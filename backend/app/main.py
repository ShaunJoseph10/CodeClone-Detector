"""CodeClone REST API. Run:  uvicorn app.main:app --reload   (docs at /docs)"""

import csv
import io
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, or_
from sqlalchemy.orm import aliased
from sqlmodel import Session, delete, select
from starlette.exceptions import HTTPException as StarletteHTTPException

from .db import Analysis, Assignment, Cluster, PairResult, Submission, get_session, init_db
from .services import UploadError, ast_json, parse_error_of, read_upload, run_analysis
from .settings import settings


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {"ts": self.formatTime(record), "level": record.levelname, "logger": record.name,
                 "msg": record.getMessage()}
        entry.update(getattr(record, "fields", {}))
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
log = logging.getLogger("codeclone")
log.handlers[:] = [handler]
log.setLevel(settings.log_level)
log.propagate = False


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="CodeClone Detector API", version="2.0.0", lifespan=lifespan,
              docs_url="/docs", openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    log.info("request", extra={"fields": {
        "method": request.method, "path": request.url.path, "status": response.status_code,
        "ms": round((time.perf_counter() - start) * 1000, 1)}})
    return response


# ---------- consistent error shape: {"error": {"code": ..., "message": ..., "details"?: ...}} ----------

def error(status, code, message, details=None):
    body = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(body, status_code=status)


@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    codes = {400: "bad_request", 404: "not_found", 409: "conflict", 413: "too_large", 422: "invalid"}
    return error(exc.status_code, codes.get(exc.status_code, "error"), str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    details = [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
    return error(422, "invalid", "request validation failed", details)


@app.exception_handler(Exception)
async def unhandled(request, exc):
    log.exception("unhandled error on %s", request.url.path)
    return error(500, "internal", "internal server error")


def get_or_404(db, model, id_):
    obj = db.get(model, id_)
    if obj is None:
        raise HTTPException(404, "%s %d not found" % (model.__name__.lower(), id_))
    return obj


# ---------- schemas ----------

class AssignmentIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    course: str = Field(default="", max_length=100)


class AnalysisIn(BaseModel):
    threshold: float = Field(default=0.6, ge=0, le=1)
    min_mass: int = Field(default=6, ge=1, le=200)
    weights: Optional[dict[str, float]] = None

    @field_validator("weights")
    @classmethod
    def check_weights(cls, w):
        if w is None:
            return w
        allowed = {"dice", "containment", "lcs", "winnow"}
        if not w or set(w) - allowed:
            raise ValueError("weights must use only the keys %s" % sorted(allowed))
        if any(v < 0 for v in w.values()) or sum(w.values()) <= 0:
            raise ValueError("weights must be non-negative with a positive sum")
        return w


# ---------- serializers ----------

def submission_out(s, with_source=False):
    out = {"id": s.id, "assignment_id": s.assignment_id, "student_name": s.student_name, "filename": s.filename,
           "lines": s.source.count("\n") + (0 if s.source.endswith("\n") or not s.source else 1),
           "uploaded_at": s.uploaded_at, "parse_error": s.parse_error}
    if with_source:
        out["source"] = s.source
    return out


def analysis_out(a):
    return {"id": a.id, "assignment_id": a.assignment_id, "status": a.status, "config": json.loads(a.config_json),
            "summary": json.loads(a.summary_json), "created_at": a.created_at, "started_at": a.started_at,
            "finished_at": a.finished_at, "duration_ms": a.duration_ms, "error": a.error}


def pair_out(p, a, b):
    return {"id": p.id, "score": p.score,
            "signals": {"dice": p.dice, "containment": p.containment, "lcs": p.lcs, "winnow": p.winnow},
            "a": {"id": a.id, "student_name": a.student_name, "filename": a.filename},
            "b": {"id": b.id, "student_name": b.student_name, "filename": b.filename},
            "match_count": len(json.loads(p.matches_json))}


def assignment_out(db, a):
    count = db.exec(select(func.count()).select_from(Submission).where(Submission.assignment_id == a.id)).one()
    last = db.exec(select(Analysis).where(Analysis.assignment_id == a.id).order_by(Analysis.id.desc())).first()
    return {"id": a.id, "title": a.title, "course": a.course, "language": a.language, "created_at": a.created_at,
            "submission_count": count,
            "last_analysis": None if last is None else {
                "id": last.id, "status": last.status,
                "max_score": json.loads(last.summary_json).get("max_score")}}


# ---------- assignments ----------

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/assignments", status_code=201)
def create_assignment(body: AssignmentIn, db: Session = Depends(get_session)):
    a = Assignment(title=body.title.strip(), course=body.course.strip())
    db.add(a)
    db.commit()
    db.refresh(a)
    return assignment_out(db, a)


@app.get("/api/assignments")
def list_assignments(db: Session = Depends(get_session)):
    return [assignment_out(db, a) for a in db.exec(select(Assignment).order_by(Assignment.id.desc())).all()]


@app.get("/api/assignments/{assignment_id}")
def get_assignment(assignment_id: int, db: Session = Depends(get_session)):
    return assignment_out(db, get_or_404(db, Assignment, assignment_id))


@app.delete("/api/assignments/{assignment_id}", status_code=204)
def delete_assignment(assignment_id: int, db: Session = Depends(get_session)):
    a = get_or_404(db, Assignment, assignment_id)
    analysis_ids = select(Analysis.id).where(Analysis.assignment_id == assignment_id)
    db.exec(delete(PairResult).where(PairResult.analysis_id.in_(analysis_ids)))
    db.exec(delete(Cluster).where(Cluster.analysis_id.in_(analysis_ids)))
    db.exec(delete(Analysis).where(Analysis.assignment_id == assignment_id))
    db.exec(delete(Submission).where(Submission.assignment_id == assignment_id))
    db.delete(a)
    db.commit()
    return Response(status_code=204)


# ---------- submissions ----------

@app.post("/api/assignments/{assignment_id}/submissions", status_code=201)
async def upload_submissions(assignment_id: int, files: list[UploadFile] = File(...),
                             db: Session = Depends(get_session)):
    """Upload several .py files and/or .zip archives. Per-file problems are returned in
    `errors`; an unsafe or broken zip rejects the whole request."""
    get_or_404(db, Assignment, assignment_id)
    incoming, errors = [], []
    for upload in files:
        data = await upload.read(settings.max_zip_bytes + 1)
        try:
            got, errs = read_upload(upload.filename or "", data)
        except UploadError as e:
            raise HTTPException(400, str(e))
        incoming += got
        errors += errs
    if len(incoming) > settings.max_files_per_upload:
        raise HTTPException(413, "too many files: %d (limit %d)" % (len(incoming), settings.max_files_per_upload))
    created = []
    for f in incoming:
        s = Submission(assignment_id=assignment_id, student_name=f.student, filename=f.filename,
                       source=f.source, parse_error=parse_error_of(f.source))
        db.add(s)
        created.append(s)
    db.commit()
    return {"created": [submission_out(s) for s in created], "errors": errors}


@app.get("/api/assignments/{assignment_id}/submissions")
def list_submissions(assignment_id: int, db: Session = Depends(get_session)):
    get_or_404(db, Assignment, assignment_id)
    subs = db.exec(select(Submission).where(Submission.assignment_id == assignment_id).order_by(Submission.id))
    return [submission_out(s) for s in subs.all()]


@app.get("/api/submissions/{submission_id}")
def get_submission(submission_id: int, db: Session = Depends(get_session)):
    return submission_out(get_or_404(db, Submission, submission_id), with_source=True)


@app.get("/api/submissions/{submission_id}/ast")
def get_ast(submission_id: int, normalized: bool = False, db: Session = Depends(get_session)):
    s = get_or_404(db, Submission, submission_id)
    if s.parse_error:
        raise HTTPException(422, "submission does not parse: %s" % s.parse_error)
    return {"submission_id": s.id, "normalized": normalized, "tree": ast_json(s.source, normalized)}


# ---------- analyses ----------

@app.post("/api/assignments/{assignment_id}/analyses", status_code=202)
def start_analysis(assignment_id: int, body: AnalysisIn, tasks: BackgroundTasks,
                   db: Session = Depends(get_session)):
    get_or_404(db, Assignment, assignment_id)
    a = Analysis(assignment_id=assignment_id, config_json=body.model_dump_json())
    db.add(a)
    db.commit()
    db.refresh(a)
    tasks.add_task(run_analysis, a.id)
    return analysis_out(a)


@app.get("/api/assignments/{assignment_id}/analyses")
def list_analyses(assignment_id: int, db: Session = Depends(get_session)):
    get_or_404(db, Assignment, assignment_id)
    rows = db.exec(select(Analysis).where(Analysis.assignment_id == assignment_id).order_by(Analysis.id.desc()))
    return [analysis_out(a) for a in rows.all()]


@app.get("/api/analyses/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_session)):
    return analysis_out(get_or_404(db, Analysis, analysis_id))


SORTABLE = {"score", "dice", "containment", "lcs", "winnow"}


def _pairs_query(analysis_id, min_score, student):
    A, B = aliased(Submission), aliased(Submission)
    q = (select(PairResult, A, B).join(A, PairResult.sub_a == A.id).join(B, PairResult.sub_b == B.id)
         .where(PairResult.analysis_id == analysis_id).where(PairResult.score >= min_score))
    if student:
        like = "%" + student.lower() + "%"
        q = q.where(or_(func.lower(A.student_name).like(like), func.lower(B.student_name).like(like)))
    return q


@app.get("/api/analyses/{analysis_id}/pairs")
def list_pairs(analysis_id: int, min_score: float = Query(0.0, ge=0, le=1), student: str = "",
               sort: str = Query("-score", description="score|dice|containment|lcs|winnow, prefix '-' for descending"),
               page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500),
               db: Session = Depends(get_session)):
    get_or_404(db, Analysis, analysis_id)
    field = sort.lstrip("-")
    if field not in SORTABLE:
        raise HTTPException(422, "sort must be one of %s" % sorted(SORTABLE))
    column = getattr(PairResult, field)
    q = _pairs_query(analysis_id, min_score, student)
    total = db.exec(select(func.count()).select_from(q.subquery())).one()
    q = q.order_by(column.desc() if sort.startswith("-") else column.asc(), PairResult.id)
    rows = db.exec(q.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [pair_out(p, a, b) for p, a, b in rows], "total": total, "page": page, "page_size": page_size}


@app.get("/api/analyses/{analysis_id}/pairs/{pair_id}")
def get_pair(analysis_id: int, pair_id: int, db: Session = Depends(get_session)):
    p = get_or_404(db, PairResult, pair_id)
    if p.analysis_id != analysis_id:
        raise HTTPException(404, "pair %d not found in analysis %d" % (pair_id, analysis_id))
    a, b = db.get(Submission, p.sub_a), db.get(Submission, p.sub_b)
    out = pair_out(p, a, b)
    out["a"], out["b"] = submission_out(a, True), submission_out(b, True)
    out["matches"] = json.loads(p.matches_json)
    return out


@app.get("/api/analyses/{analysis_id}/clusters")
def list_clusters(analysis_id: int, db: Session = Depends(get_session)):
    get_or_404(db, Analysis, analysis_id)
    out = []
    for c in db.exec(select(Cluster).where(Cluster.analysis_id == analysis_id).order_by(Cluster.id)).all():
        members = [db.get(Submission, i) for i in json.loads(c.member_ids_json)]
        out.append({"id": c.id, "max_score": c.max_score,
                    "members": [{"id": s.id, "student_name": s.student_name, "filename": s.filename}
                                for s in members]})
    return out


@app.get("/api/analyses/{analysis_id}/graph")
def get_graph(analysis_id: int, min_score: Optional[float] = Query(None, ge=0, le=1),
              db: Session = Depends(get_session)):
    """Nodes: every parsed submission. Edges: pairs at or above min_score (default: the threshold)."""
    a = get_or_404(db, Analysis, analysis_id)
    cut = json.loads(a.config_json)["threshold"] if min_score is None else min_score
    subs = db.exec(select(Submission).where(Submission.assignment_id == a.assignment_id)
                   .where(Submission.parse_error == None)).all()  # noqa: E711
    pairs = db.exec(select(PairResult).where(PairResult.analysis_id == analysis_id)
                    .where(PairResult.score >= cut)).all()
    degree = {}
    for p in pairs:
        degree[p.sub_a] = degree.get(p.sub_a, 0) + 1
        degree[p.sub_b] = degree.get(p.sub_b, 0) + 1
    return {"min_score": cut,
            "nodes": [{"id": s.id, "label": s.student_name, "filename": s.filename, "degree": degree.get(s.id, 0)}
                      for s in subs],
            "edges": [{"id": p.id, "source": p.sub_a, "target": p.sub_b, "score": p.score} for p in pairs]}


@app.get("/api/analyses/{analysis_id}/export")
def export(analysis_id: int, format: Literal["csv", "json"] = "csv", db: Session = Depends(get_session)):
    a = get_or_404(db, Analysis, analysis_id)
    rows = db.exec(_pairs_query(analysis_id, 0.0, "").order_by(PairResult.score.desc(), PairResult.id)).all()
    name = "analysis-%d.%s" % (analysis_id, format)
    headers = {"Content-Disposition": 'attachment; filename="%s"' % name}
    if format == "json":
        body = {"analysis": analysis_out(a), "pairs": [pair_out(p, x, y) for p, x, y in rows]}
        return Response(json.dumps(body, default=str, indent=1), media_type="application/json", headers=headers)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["student_a", "file_a", "student_b", "file_b", "score", "dice", "containment", "lcs", "winnow"])
    for p, x, y in rows:
        w.writerow([x.student_name, x.filename, y.student_name, y.filename, p.score, p.dice, p.containment,
                    p.lcs, p.winnow])
    return Response(buf.getvalue(), media_type="text/csv", headers=headers)
