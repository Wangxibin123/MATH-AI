import os
import pathlib

from sqlmodel import Session, SQLModel, create_engine

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # math-copilot/
DB_FILE = ROOT / "dev.db"
DB_URL = os.getenv("DB_URL", f"sqlite:///{DB_FILE}")

engine = create_engine(DB_URL, echo=False)


def init_db() -> None:
    """
    Create tables in SQLite file.  Idempotent.
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """
    Usage:
        with get_session() as session:
            ...
    """
    return Session(engine)
