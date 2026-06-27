from __future__ import annotations

import redis
from fastapi import Depends, FastAPI
from sqlmodel import Session, select

from .config import get_settings
from .db import create_db_and_tables, engine, get_session
from .models import HealthCheck, Organization
from .tasks import celery_app

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/health", response_model=HealthCheck)
def health_check() -> HealthCheck:
    # Database check
    try:
        with Session(engine) as session:
            session.exec(select(Organization)).first()
        db_status = "ok"
    except Exception as exc:  # noqa: BLE001
        db_status = f"error: {exc}"

    # Redis check
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        redis_status = "ok"
    except Exception as exc:  # noqa: BLE001
        redis_status = f"error: {exc}"

    return HealthCheck(
        status="ok",
        version="0.1.0",
        database=db_status,
        redis=redis_status,
    )


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "EDOF-NETZ API"}


@app.get("/settings/demo")
def demo_settings() -> dict[str, str | None]:
    return {
        "app_name": settings.app_name,
        "wedof_configured": bool(settings.wedof_api_key),
        "pennylane_configured": bool(settings.pennylane_api_token),
    }
