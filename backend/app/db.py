"""Database models (SQLModel on SQLite) and session helpers."""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine

from .settings import settings


def now():
    return datetime.now(timezone.utc)


class Assignment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    course: str = ""
    language: str = "python-subset"
    created_at: datetime = Field(default_factory=now)


class Submission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    assignment_id: int = Field(foreign_key="assignment.id", index=True)
    student_name: str
    filename: str
    source: str
    uploaded_at: datetime = Field(default_factory=now)
    parse_error: Optional[str] = None


class Analysis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    assignment_id: int = Field(foreign_key="assignment.id", index=True)
    status: str = "queued"  # queued / running / done / failed
    config_json: str = "{}"
    summary_json: str = "{}"  # stats + timing + counts, filled when done
    created_at: datetime = Field(default_factory=now)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class PairResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    analysis_id: int = Field(foreign_key="analysis.id", index=True)
    sub_a: int = Field(foreign_key="submission.id")
    sub_b: int = Field(foreign_key="submission.id")
    score: float = Field(index=True)
    dice: float
    containment: float
    lcs: float
    winnow: float
    matches_json: str = "[]"


class Cluster(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    analysis_id: int = Field(foreign_key="analysis.id", index=True)
    member_ids_json: str
    max_score: float


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
