from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(StrEnum):
    SUPERUSER = "superuser"
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    INSTRUCTOR = "instructor"
    VIEWER = "viewer"


class Organization(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str
    siret: str | None = None
    wedof_api_key: str | None = None
    pennylane_api_token: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: str | None = None
    role: UserRole = Field(default=UserRole.VIEWER)
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class Attendee(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    wedof_id: float | None = Field(default=None, index=True)
    pennylane_customer_id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    date_of_birth: datetime | None = None
    raw_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Training(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    external_id: str | None = Field(default=None, index=True, unique=True)
    title: str | None = None
    certif_info: str | None = None
    raw_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class TrainingAction(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    external_id: str | None = Field(default=None, index=True, unique=True)
    title: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    training_external_id: str | None = None
    raw_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class RegistrationFolder(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    external_id: str = Field(index=True, unique=True)
    state: str | None = None
    billing_state: str | None = None
    attendee_id: str | None = Field(default=None, foreign_key="attendee.id")
    training_action_external_id: str | None = None
    amount_ttc: float | None = None
    amount_ht: float | None = None
    created_on: datetime | None = None
    updated_on: datetime | None = None
    raw_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CertificationFolder(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    external_id: str = Field(index=True, unique=True)
    state: str | None = None
    registration_folder_external_id: str | None = None
    attendee_id: str | None = Field(default=None, foreign_key="attendee.id")
    amount_ttc: float | None = None
    created_on: datetime | None = None
    updated_on: datetime | None = None
    raw_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Invoice(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    external_id: str | None = Field(default=None, index=True, unique=True)
    state: str | None = None
    amount_ttc: float | None = None
    amount_ht: float | None = None
    due_date: datetime | None = None
    registration_folder_external_id: str | None = None
    pennylane_customer_id: str | None = None
    pennylane_invoice_id: str | None = None
    raw_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class WedofSyncState(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    entity_type: str = Field(index=True, unique=True)
    last_sync_at: datetime | None = None
    last_value: str | None = None  # page, cursor or external_id


class WedofWebhookEvent(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    event_type: str | None = None
    payload: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    processed: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class HealthCheck(SQLModel):
    status: str
    version: str
    database: str
    redis: str
