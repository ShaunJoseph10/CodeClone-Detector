"""Load ../dataset as a demo assignment and run one analysis.  Run:  python -m app.seed"""

import json
import sys
from pathlib import Path

from sqlmodel import Session, select

from .db import Analysis, Assignment, Submission, engine, init_db
from .services import parse_error_of, run_analysis

DATASET = Path(__file__).resolve().parents[2] / "dataset"
TITLE = "Demo: CodeClone dataset"


def seed():
    init_db()
    with Session(engine) as db:
        if db.exec(select(Assignment).where(Assignment.title == TITLE)).first():
            print("demo assignment already exists")
            return
        a = Assignment(title=TITLE, course="DSA demo")
        db.add(a)
        db.commit()
        db.refresh(a)
        for path in sorted(DATASET.glob("*.py")):
            source = path.read_text()
            db.add(Submission(assignment_id=a.id, student_name=path.stem, filename=path.name,
                              source=source, parse_error=parse_error_of(source)))
        run = Analysis(assignment_id=a.id, config_json=json.dumps({"threshold": 0.6, "min_mass": 6, "weights": None}))
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id, assignment_id = run.id, a.id
    run_analysis(run_id)
    with Session(engine) as db:
        run = db.get(Analysis, run_id)
        print("seeded assignment %d, analysis %d: %s %s" % (assignment_id, run_id, run.status, run.summary_json))
    if run.status != "done":
        sys.exit(1)


if __name__ == "__main__":
    seed()
