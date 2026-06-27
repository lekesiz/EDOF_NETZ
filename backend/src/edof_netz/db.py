from __future__ import annotations

from typing import Any

from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

settings = get_settings()
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Any:
    with Session(engine) as session:
        yield session
