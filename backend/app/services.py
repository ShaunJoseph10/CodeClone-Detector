"""Glue between the HTTP layer and the CodeClone engine: uploads, analysis runs, AST export.
Uploaded code is only parsed by the engine, never executed."""

import io
import json
import logging
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from sqlmodel import Session, select

from .db import Analysis, Cluster, PairResult, Submission, engine, now
from .settings import settings

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root: the engine

from codeclone.api import Config, analyze  # noqa: E402
from codeclone.deadcode import remove_dead_code  # noqa: E402
from codeclone.lexer import LexerError  # noqa: E402
from codeclone.normalizer import canonicalize, normalize  # noqa: E402
from codeclone.parser import ParseError, parse  # noqa: E402

log = logging.getLogger("codeclone")


class UploadError(ValueError):
    """The whole upload is rejected (bad zip, zip-slip, too many files)."""


@dataclass
class IncomingFile:
    student: str
    filename: str
    source: str


def parse_error_of(source):
    try:
        parse(source)
        return None
    except (LexerError, ParseError) as e:
        return str(e)
    except RecursionError:
        return "file is nested too deeply to parse"


def _decode(data, name):
    if len(data) > settings.max_file_bytes:
        raise ValueError("%s is larger than %d bytes" % (name, settings.max_file_bytes))
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("%s is not UTF-8 text" % name)


def _safe_member(name):
    """Zip entry path -> parts, or UploadError for absolute / '..' paths (zip-slip)."""
    path = PurePosixPath(name.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or (path.parts and ":" in path.parts[0]):
        raise UploadError("unsafe path in zip: %s" % name)
    return path.parts


def read_upload(filename, data):
    """One uploaded file -> (IncomingFile list, per-file error list).
    .py: student = file name without extension. .zip: student = top folder, else file stem."""
    files, errors = [], []
    lower = filename.lower()
    if lower.endswith(".py"):
        try:
            name = PurePosixPath(filename.replace("\\", "/")).name
            files.append(IncomingFile(name[:-3], name, _decode(data, name)))
        except ValueError as e:
            errors.append({"filename": filename, "error": str(e)})
    elif lower.endswith(".zip"):
        if len(data) > settings.max_zip_bytes:
            raise UploadError("%s is larger than %d bytes" % (filename, settings.max_zip_bytes))
        try:
            archive = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile:
            raise UploadError("%s is not a valid zip file" % filename)
        with archive:
            infos = [i for i in archive.infolist() if not i.is_dir()]
            for info in infos:
                _safe_member(info.filename)  # reject the whole zip before reading anything
            for info in infos:
                parts = _safe_member(info.filename)
                if parts[0] == "__MACOSX" or parts[-1].startswith("."):
                    continue
                if not parts[-1].lower().endswith(".py"):
                    errors.append({"filename": info.filename, "error": "only .py files are accepted"})
                    continue
                if info.file_size > settings.max_file_bytes:
                    errors.append({"filename": info.filename,
                                   "error": "larger than %d bytes" % settings.max_file_bytes})
                    continue
                student = parts[-2] if len(parts) >= 2 else parts[-1][:-3]
                try:
                    files.append(IncomingFile(student, parts[-1], _decode(archive.read(info), info.filename)))
                except ValueError as e:
                    errors.append({"filename": info.filename, "error": str(e)})
    else:
        errors.append({"filename": filename, "error": "only .py or .zip files are accepted"})
    return files, errors


# ---------------- analysis ----------------

def run_analysis(analysis_id):
    """Background task: run the engine over the assignment's submissions and store results."""
    with Session(engine) as db:
        analysis = db.get(Analysis, analysis_id)
        if analysis is None:
            return
        analysis.status, analysis.started_at = "running", now()
        db.add(analysis)
        db.commit()
        start = time.perf_counter()
        try:
            cfg = json.loads(analysis.config_json)
            subs = db.exec(select(Submission).where(Submission.assignment_id == analysis.assignment_id)
                           .where(Submission.parse_error == None)).all()  # noqa: E711
            config = Config(threshold=cfg["threshold"], min_mass=cfg["min_mass"],
                            **({"weights": cfg["weights"]} if cfg.get("weights") else {}))
            result = analyze([(str(s.id), s.source) for s in subs], config)

            for p in result.pairs:
                db.add(PairResult(analysis_id=analysis_id, sub_a=int(p.a), sub_b=int(p.b), score=p.score,
                                  dice=p.signals["dice"], containment=p.signals["containment"],
                                  lcs=p.signals["lcs"], winnow=p.signals["winnow"],
                                  matches_json=json.dumps([m.__dict__ for m in p.matches])))
            best = {}
            for p in result.flagged_pairs():
                for side in (p.a, p.b):
                    best[side] = max(best.get(side, 0), p.score)
            for group in result.clusters:
                db.add(Cluster(analysis_id=analysis_id, member_ids_json=json.dumps([int(x) for x in group]),
                               max_score=max(best.get(x, 0) for x in group)))
            analysis.summary_json = json.dumps({
                **result.stats,
                "flagged": result.flagged,
                "clusters": len(result.clusters),
                "max_score": result.pairs[0].score if result.pairs else 0.0,
                "engine_errors": result.errors,
                "timing": result.timing,
            })
            analysis.status = "done"
        except Exception as e:  # a failed run is recorded, never crashes the worker
            log.exception("analysis %s failed", analysis_id)
            db.rollback()
            analysis = db.get(Analysis, analysis_id)
            analysis.status, analysis.error = "failed", "%s: %s" % (type(e).__name__, e)
        analysis.finished_at = now()
        analysis.duration_ms = int((time.perf_counter() - start) * 1000)
        db.add(analysis)
        db.commit()
        log.info("analysis %s %s in %d ms", analysis_id, analysis.status, analysis.duration_ms)


# ---------------- AST export (teaching view) ----------------

def ast_json(source, normalized=False):
    """The engine's own AST as nested dicts. normalized=True shows the tree the matcher sees:
    dead code removed, loops canonicalized, names replaced by VAR/FUNC/NUM/STR."""
    root = parse(source)
    if normalized:
        root = normalize(canonicalize(remove_dead_code(root)))

    def node(n):
        return {"label": n.label, "value": None if n.value is None else str(n.value),
                "start_line": n.start_line, "end_line": n.end_line,
                "children": [node(c) for c in n.children]}
    return node(root)
