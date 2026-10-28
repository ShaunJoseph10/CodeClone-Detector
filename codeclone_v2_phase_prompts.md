# CodeClone Detector v2: Production Upgrade Plan

v1 is a working command-line engine: 26 tests pass, precision 1.0, recall 0.595.
v2 turns it into a production-grade web application that a teacher can actually use, and fixes v1's weak spots.

**v1 problems this plan fixes**

| Problem in v1 | Fix in v2 |
|---|---|
| Dead code inserted: only 2/6 caught | Dead-code normalization, plus a similarity score that tolerates gaps |
| `for` rewritten as `while`: only 1/6 caught | Canonicalize `for ... in range()` into the equivalent `while` form |
| All pairs compared, so time grows with n² | An inverted index means only file pairs that share fingerprints get compared |
| Output is only CLI + a static HTML file | REST API, database and a full web UI |

**Targets:** precision ≥ 0.95, recall ≥ 0.85, and 500 files analysed in under 10 seconds.

**Stack:** Python engine (unchanged rule: hand-written data structures) · FastAPI + SQLite (SQLModel) · React + Vite + TypeScript + Tailwind · Docker Compose

There are 4 phases. Each prompt below is self-contained. Use the master prompt at the bottom to run them all in order.

---

## Phase 1: Engine v2 (accuracy + speed)

```
Upgrade the existing CodeClone Detector engine (v1 is complete: own lexer, parser, normalizer,
post-order hasher, chained hash table, matcher, Dice scorer, merge sort, BFS clustering,
26 passing tests). Keep every v1 rule: no `ast`/`tokenize` modules, and hand-written data
structures for the core (they are graded course outcomes CO1–CO5). Only the standard library
is allowed in the engine.

Goals: recall >= 0.85 with precision >= 0.95 on the existing dataset, and better scaling.

1. Loop canonicalization (normalizer)
   - Rewrite `for VAR in range(a)`, `range(a, b)` and `range(a, b, s)` into the equivalent
     init + while + increment shape before hashing, so for and while versions hash the same.
   - Handle `continue` inside the loop correctly (the increment must still run), or skip the
     rewrite for that loop and document why.

2. Dead-code normalization (new pass: deadcode.py)
   - Remove `if False:` / `while False:` blocks and statements after `return` in a block.
   - Simple liveness: remove assignments to a variable that is never read afterwards in that
     function (with no side-effecting call on the right-hand side). Implement it with a
     backward pass over the statement list, using my own set structure built on the hash table.

3. Gap-tolerant scoring (scorer.py)
   - For each pair of matched functions, turn their bodies into sequences of statement hashes
     and compute an LCS (dynamic programming) similarity. This tolerates inserted junk lines.
   - Final score = weighted mix of: Dice on matched nodes, containment (matched / smaller file),
     and LCS similarity. Put the weights in config and tune them with evaluate.py.

4. Winnowing fingerprints (winnow.py)
   - MOSS-style: k-grams over the normalized token stream -> rolling hash -> window-minimum
     selection. Use it as a second signal in the final score and report both scores.

5. Candidate generation instead of all-pairs (index.py)
   - Build an inverted index fingerprint -> linked list of file ids (my own hash table).
   - Only score file pairs that share at least K fingerprints. Report how many pairs were
     skipped. Ignore fingerprints that appear in more than X% of files (common boilerplate).

6. Clean library API (engine/api.py)
   - analyze(files: list[(name, source)], config) -> AnalysisResult, a dataclass with: pairs
     (scores, per-signal breakdown, matched line spans for both files), clusters, per-file
     parse errors, and timing. Add to_json(). A file that fails to parse must not crash the run.
   - Keep main.py working on top of this API.

7. Tests and evaluation
   - Keep all 26 old tests passing. Add tests for each new pass.
   - Extend evaluate.py: per-disguise table, precision/recall/F1 at thresholds 0.4–0.8, and
     timing for 50 / 200 / 500 generated files. Print a v1-vs-v2 comparison.

Use python3. Run the tests with `python3 -m unittest discover -s tests` (pytest is not installed).
```

---

## Phase 2: Backend API + database

```
Phase 1 is done: the CodeClone engine exposes analyze(files, config) -> AnalysisResult with
to_json(). Now build a production backend around it in backend/. Do not modify engine logic;
import it as a library. The web layer may use external packages.

Stack: FastAPI, SQLModel on SQLite, Pydantic settings, uvicorn. Put requirements in
backend/requirements.txt and use a virtualenv.

Data model:
- Assignment(id, title, course, language="python-subset", created_at)
- Submission(id, assignment_id, student_name, filename, source, uploaded_at, parse_error)
- Analysis(id, assignment_id, status [queued/running/done/failed], config_json, started_at,
  finished_at, duration_ms, error)
- PairResult(id, analysis_id, sub_a, sub_b, score, dice, containment, lcs, winnow,
  matches_json)
- Cluster(id, analysis_id, member_ids_json, max_score)

Endpoints (under /api, OpenAPI docs on):
- POST/GET/DELETE /assignments
- POST /assignments/{id}/submissions: upload multiple .py files OR one .zip. Student name comes
  from the filename or folder. Validate the extension and size (limits in settings), and
  reject zip-slip paths.
- GET /assignments/{id}/submissions, GET /submissions/{id} (includes source)
- POST /assignments/{id}/analyses with {threshold, min_mass, weights}: runs as a background task
- GET /analyses/{id}: status + summary. GET /analyses/{id}/pairs?min_score&sort&page
- GET /analyses/{id}/pairs/{pair_id}: both sources + matched line spans, for the compare view
- GET /analyses/{id}/clusters, GET /analyses/{id}/graph (nodes + edges for visualisation)
- GET /analyses/{id}/export?format=csv|json
- GET /submissions/{id}/ast: the AST from my own parser as nested JSON (for a teaching view)
- GET /health

Quality:
- Consistent error responses, structured logging, CORS restricted to configured origins.
- Seed script: loads dataset/ as a demo assignment and runs one analysis.
- Tests with FastAPI TestClient covering upload (files + zip), the analysis lifecycle, pagination,
  export, and bad input. Keep the engine tests passing too.
```

---

## Phase 3: Frontend UI

```
Phases 1–2 are done: the FastAPI backend at /api serves assignments, submissions, analyses,
pairs, clusters, graph, export and AST endpoints (see the OpenAPI docs at /docs). Build the
frontend in frontend/ with React + Vite + TypeScript + Tailwind, React Router, and TanStack
Query for data fetching. Make it clean, modern and responsive, with a light/dark theme and a
consistent design system (one accent colour, a clear type scale, no clutter).

Pages:
1. Dashboard: list of assignments with submission count, last analysis status, highest
   similarity, and a "New assignment" button.
2. Assignment page:
   - Drag-and-drop upload for .py files or a .zip, with progress and per-file errors.
   - Submissions table (student, file, lines, parse status).
   - "Run analysis" panel with a threshold slider, min-mass input and an advanced weights section.
   - Live status while the analysis runs (poll the analysis status).
3. Results page:
   - Summary cards: files, pairs checked, pairs skipped by the index, flagged pairs, clusters,
     duration.
   - Ranked pairs table: score bar, per-signal breakdown (Dice / containment / LCS / winnowing),
     filter by min score, search by student, sort, pagination.
   - Cluster graph: an interactive network (use cytoscape.js or react-force-graph). Node = student,
     edge thickness = score, clicking an edge opens the compare view.
   - Export CSV / JSON buttons.
4. Compare view: side-by-side code with line numbers. Matched regions are highlighted in matching
   colours on both sides, and clicking a match on one side scrolls to it on the other. Show
   the score breakdown at the top.
5. AST viewer (teaching mode): a collapsible tree of the submission's AST, with a toggle between
   raw and normalized trees, to demonstrate the data structures in the viva.

Also: loading skeletons, empty states, error toasts, a 404 page, accessible colours and
keyboard focus. Configure the API base URL via env, and set up a Vite proxy to the backend
in dev. Add a few component tests with Vitest + Testing Library.
```

---

## Phase 4: Production hardening + delivery

```
Phases 1–3 are done (engine, FastAPI backend, React frontend). Make the project production-ready
and demo-ready.

1. Docker: Dockerfiles for the backend (python slim) and frontend (build, then serve with nginx,
   proxying /api to the backend), plus a docker-compose.yml with a volume for the SQLite DB and
   uploads. `docker compose up` must bring up the whole app with demo data seeded.
2. Config & security: all settings via env (.env.example). Upload size/count limits, rate
   limiting on upload and analysis, and a simple single-teacher login (hashed password from
   env, session or JWT). Never execute uploaded code; it is only parsed.
3. Reliability: an analysis timeout, failed analyses shown clearly in the UI, the DB created
   automatically on startup, and request logging.
4. Quality gates: a Makefile (or scripts) with `test`, `lint`, `format`, `run`. Use ruff for the
   backend and eslint + prettier for the frontend. Add a GitHub Actions workflow file that runs
   all tests. (Do not push; I will push myself.)
5. Docs:
   - README: features, screenshots placeholders, architecture diagram (Mermaid), the
     CO-to-data-structure mapping table, an algorithm summary, v1 vs v2 evaluation results,
     complexity per stage, setup (Docker and manual), API overview, and limitations.
   - docs/DEMO.md: a 5-minute demo script for the viva (upload -> analyse -> graph -> compare
     -> AST view).
6. Final check: fresh `docker compose up`, run the seeded analysis, and confirm that all
   engine, backend and frontend tests pass. Report the final metrics.
```

---

## Master prompt (paste this with the file attached)

```
You are upgrading my DSA project "CodeClone Detector" from v1 (a working CLI engine) to a
production-level web application. The attached file `codeclone_v2_phase_prompts.md` is the full
specification, with 4 phases.

How to work:
1. Read the whole file first, then inspect the existing v1 code and tests before changing anything.
2. Do the phases strictly in order: 1 -> 2 -> 3 -> 4. Treat each phase prompt as its requirements.
3. After each phase: run all tests (engine: `python3 -m unittest discover -s tests`), fix every
   failure, show me the outputs and key metrics, give a short summary of what changed, and
   commit with a clear message. Then continue to the next phase automatically.
4. Stop and ask me only if a requirement is genuinely unclear, or if a change would break v1 behaviour.

Hard rules:
- The engine keeps hand-written data structures (stack, queue, linked-list hash table, trees,
  merge sort, binary search, BFS, LCS DP). No `ast`/`tokenize`, and no external packages in the
  engine. Mark CO usage in comments, e.g. `# CO4: chained hash table`.
- Use python3, not python. pytest is not installed; use unittest for the engine.
- Never execute uploaded code.
- Git: commit locally per phase, but NEVER add a co-author line and NEVER push. I push myself.

Final deliverable: `docker compose up` runs the full app with demo data, all tests pass, the README
and docs/DEMO.md are complete, and you give me a final summary with v1 vs v2 metrics, how to run,
and the remaining limitations.

Start with Phase 1.
```

---

## Done checklist
- [ ] Phase 1: recall ≥ 0.85, precision ≥ 0.95, 500 files < 10 s, old tests still pass
- [ ] Phase 2: API works end to end, uploads are validated, backend tests pass
- [ ] Phase 3: upload → analyse → results → graph → compare → AST view all work in the browser
- [ ] Phase 4: `docker compose up` works from scratch, CI file is added, README and demo script are written
