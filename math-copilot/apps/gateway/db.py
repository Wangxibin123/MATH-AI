from sqlmodel import Session, SQLModel, create_engine
from apps.gateway.settings import settings

# ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # math-copilot/
# DB_FILE = ROOT / "dev.db"
# DB_URL = os.getenv("DB_URL", f"sqlite:///{DB_FILE}")

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False},
    echo=False,
)


def init_db() -> None:
    """
    Create tables in the database. Idempotent.
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """
    Usage:
        with get_session() as session:
            ...
    """
    return Session(engine)
