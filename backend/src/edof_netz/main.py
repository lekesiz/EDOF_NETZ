from __future__ import annotations

import redis
from fastapi import Depends, FastAPI
from sqlmodel import Session, select

from .auth import get_password_hash, require_role
from .config import get_settings
from .db import create_db_and_tables, engine
from .models import HealthCheck, Organization, User, UserRole
from .routers import auth, dashboard, folders, invoices, pennylane, sync, webhooks

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(folders.router)
app.include_router(invoices.router)
app.include_router(pennylane.router)
app.include_router(sync.router)
app.include_router(webhooks.router)


def _ensure_admin_user() -> None:
    """Create or update the bootstrap admin user from environment variables."""
    if not settings.admin_email or not settings.admin_password:
        return
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == settings.admin_email)).first()
        if user is None:
            user = User(
                email=settings.admin_email,
                role=UserRole.SUPERUSER,
                is_active=True,
            )
            session.add(user)
        user.hashed_password = get_password_hash(settings.admin_password)
        session.commit()


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()
    _ensure_admin_user()


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
def demo_settings(
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPERUSER)),
) -> dict[str, str | bool | None]:
    return {
        "app_name": settings.app_name,
        "wedof_configured": bool(settings.wedof_api_key),
        "pennylane_configured": bool(settings.pennylane_api_token),
        "user_email": current_user.email,
    }
