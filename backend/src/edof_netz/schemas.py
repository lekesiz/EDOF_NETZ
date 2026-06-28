from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr

from .models import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    role: UserRole = UserRole.VIEWER


class UserRead(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: UserRole
    is_active: bool


class UserLogin(BaseModel):
    email: str
    password: str


class RegistrationFolderListItem(BaseModel):
    id: str
    external_id: str
    attendee_id: str | None = None
    state: str | None = None
    billing_state: str | None = None
    amount_ttc: float | None = None
    created_on: str | None = None
    updated_on: str | None = None
    is_reconciled: bool = False
    pennylane_invoice_number: str | None = None
    pennylane_paid_date: str | None = None
    wedof_paid_date: str | None = None


class AttendeeListItem(BaseModel):
    id: str
    wedof_id: float | None = None
    pennylane_customer_id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None


class CertificationFolderListItem(BaseModel):
    id: str
    external_id: str
    state: str | None = None
    registration_folder_external_id: str | None = None
    amount_ttc: float | None = None
    created_on: str | None = None
    updated_on: str | None = None


class InvoiceListItem(BaseModel):
    id: str
    external_id: str | None = None
    state: str | None = None
    amount_ttc: float | None = None
    amount_ht: float | None = None
    due_date: str | None = None
    registration_folder_external_id: str | None = None
    pennylane_customer_id: str | None = None
    pennylane_invoice_id: str | None = None


class InvoiceableCandidateItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    external_id: str
    state: str | None = None
    billing_state: str | None = None
    amount_ttc: float | None = None
    amount_ht: float | None = None
    created_on: str | None = None
    training_action_external_id: str | None = None
    attendee: AttendeeListItem | None = None


class DashboardStats(BaseModel):
    target_amount: float
    realized: float
    remaining: float
    kasa: float
    alacak: float
    kayip: float
    total_dossiers: int
    reconciled_count: int


class MonthlyData(BaseModel):
    month: str
    kasa: float
    alacak: float
    kayip: float


class DashboardResponse(BaseModel):
    year: int
    stats: DashboardStats
    monthly_data: list[MonthlyData]
    last_sync: dict[str, str | None]
