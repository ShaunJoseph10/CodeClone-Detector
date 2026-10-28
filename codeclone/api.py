"""Library entry point: analyze(files, config) -> AnalysisResult.

Pipeline per file:  parse -> remove_dead_code -> canonicalize -> normalize -> hash -> fingerprints
Then:  inverted index (candidate pairs) -> clone matching -> 4 signals -> weighted score
       -> merge sort (CO5) -> binary search threshold (CO5) -> BFS clusters (CO5)
"""

import json
import time
from dataclasses import asdict, dataclass, field

from .deadcode import remove_dead_code
from .graph import build_graph, clusters
from .hashtable import HashMap, HashSet
from .index import candidate_pairs
from .lexer import LexerError
from .matcher import MIN_MASS, SourceFile, find_clones
from .normalizer import canonicalize
from .parser import ParseError
from .ranking import above_threshold, merge_sort
from .scorer import combine, signals
from .winnow import K, WINDOW, fingerprint_set, fingerprints

DEFAULT_WEIGHTS = {"dice": 0.3, "containment": 0.2, "lcs": 0.3, "winnow": 0.2}


@dataclass
class Config:
    threshold: float = 0.6
    min_mass: int = MIN_MASS
    weights: dict = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    k: int = K                      # winnowing k-gram length
    window: int = WINDOW            # winnowing window size
    min_shared: int = 3             # fingerprints a pair must share to be scored
    max_df: float = 0.5             # ignore fingerprints present in more than this share of files
    deadcode: bool = True
    canonical_loops: bool = True
    use_index: bool = True

    @classmethod
    def v1(cls, **overrides):
        """The v1 engine: no new passes, Dice only, all pairs."""
        base = dict(deadcode=False, canonical_loops=False, use_index=False, weights={"dice": 1.0})
        base.update(overrides)
        return cls(**base)


@dataclass
class Match:
    a_start: int
    a_end: int
    b_start: int
    b_end: int
    size: int


@dataclass
class PairResult:
    a: str
    b: str
    score: float
    signals: dict
    matches: list


@dataclass
class AnalysisResult:
    files: list          # names of files that parsed
    pairs: list          # PairResult, ranked by score (descending)
    flagged: int         # how many of `pairs` are >= threshold (they come first)
    clusters: list       # lists of file names
    errors: dict         # file name -> parse error message
    stats: dict
    timing: dict         # stage -> seconds
    threshold: float

    def flagged_pairs(self):
        return self.pairs[:self.flagged]

    def to_dict(self):
        return asdict(self)

    def to_json(self, **kw):
        return json.dumps(self.to_dict(), **kw)


def prepare(files, config):
    """Parse every (name, source). Returns (SourceFile list, errors). A bad file never stops the run."""
    passes = []
    if config.deadcode:
        passes.append(remove_dead_code)
    if config.canonical_loops:
        passes.append(canonicalize)
    parsed, errors = [], {}
    for name, source in files:
        try:
            parsed.append(SourceFile(len(parsed), name, source, passes))
        except (LexerError, ParseError) as e:
            errors[name] = str(e)
        except RecursionError:
            errors[name] = "file is nested too deeply to parse"
    return parsed, errors


def analyze(files, config=None):
    """files: list of (name, source). Returns an AnalysisResult."""
    config = config or Config()
    timing = {}
    t0 = time.perf_counter()
    parsed, errors = prepare(files, config)
    t1 = time.perf_counter()
    timing["parse"] = t1 - t0

    fps = [fingerprint_set(fingerprints(f.root, config.k, config.window)) for f in parsed]
    n = len(parsed)
    total_pairs = n * (n - 1) // 2
    ignored = 0
    if config.use_index:
        cand, ignored = candidate_pairs(fps, config.min_shared, config.max_df)
    else:
        cand = [(i, j) for i in range(n) for j in range(i + 1, n)]
    t2 = time.perf_counter()
    timing["index"] = t2 - t1

    clones = find_clones(parsed, config.min_mass, HashSet(cand) if config.use_index else None)
    by_pair = {}
    for c in clones:
        by_pair.setdefault((c.file_a.id, c.file_b.id), []).append(c)
    t3 = time.perf_counter()
    timing["match"] = t3 - t2

    pairs = []
    lcs_cache = HashMap()
    for i, j in cand:
        a, b = parsed[i], parsed[j]
        mine = by_pair.get((i, j), [])
        sig = signals(a, b, mine, fps[i], fps[j], lcs_cache)
        matches = [Match(c.node_a.start_line, c.node_a.end_line, c.node_b.start_line, c.node_b.end_line,
                         c.node_a.size) for c in mine]
        pairs.append(PairResult(a.name, b.name, round(combine(sig, config.weights), 4),
                                {k: round(v, 4) for k, v in sig.items()}, matches))
    ranked = merge_sort(pairs, key=lambda p: p.score)                         # CO5
    flagged = above_threshold(ranked, config.threshold, key=lambda p: p.score)  # CO5
    ids = {f.name: f.id for f in parsed}
    groups = clusters(build_graph(n, [(ids[p.a], ids[p.b]) for p in flagged]))  # CO5: BFS
    timing["score"] = time.perf_counter() - t3
    timing["total"] = time.perf_counter() - t0

    return AnalysisResult(
        files=[f.name for f in parsed],
        pairs=ranked,
        flagged=len(flagged),
        clusters=[[parsed[i].name for i in g] for g in groups],
        errors=errors,
        stats={"files": n, "total_pairs": total_pairs, "pairs_scored": len(cand),
               "pairs_skipped": total_pairs - len(cand), "ignored_fingerprints": ignored},
        timing={k: round(v, 4) for k, v in timing.items()},
        threshold=config.threshold,
    )
