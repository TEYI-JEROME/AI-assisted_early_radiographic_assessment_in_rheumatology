from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def ensure_sqlite_directory(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return

    relative_path = database_url.replace("sqlite:///", "", 1)
    if relative_path.startswith("./"):
        relative_path = relative_path[2:]

    db_path = Path(__file__).resolve().parents[2] / relative_path
    db_path.parent.mkdir(parents=True, exist_ok=True)


ensure_sqlite_directory(settings.database_url)

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)