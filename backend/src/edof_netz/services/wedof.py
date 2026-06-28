from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select
from wedof_sdk import WedofClient  # type: ignore[import-untyped]

from ..config import get_settings
from ..db import engine
from ..models import (
    Attendee,
    CertificationFolder,
    RegistrationFolder,
    Training,
    TrainingAction,
    WedofSyncState,
    WedofWebhookEvent,
)

logger = logging.getLogger(__name__)


class WedofNotConfiguredError(RuntimeError):
    """Raised when the Wedof API key is missing."""


def get_wedof_client() -> WedofClient:
    """Return a configured Wedof SDK client."""
    settings = get_settings()
    if not settings.wedof_api_key:
        raise WedofNotConfiguredError("WEDOF_API_KEY is not configured")
    return WedofClient(api_key=settings.wedof_api_key)


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        text = value.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    return None


def _str_value(raw: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = raw.get(key)
        if value is not None:
            return str(value)
    return None


def _float_value(raw: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = raw.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _attendee_raw_id(raw: dict[str, Any]) -> float | None:
    """Extract the Wedof attendee technical id from a folder payload."""
    attendee = raw.get("attendee")
    if isinstance(attendee, dict):
        return _float_value(attendee, "id")
    if attendee is not None:
        return _float_value({"id": attendee}, "id")
    return _float_value(raw, "attendeeId", "attendee_id")


def _upsert_attendee(session: Session, raw: dict[str, Any]) -> Attendee | None:
    wedof_id = _float_value(raw, "id")
    if wedof_id is None:
        return None

    attendee = session.exec(select(Attendee).where(Attendee.wedof_id == wedof_id)).first()
    if attendee is None:
        attendee = Attendee(wedof_id=wedof_id)
        session.add(attendee)

    attendee.email = _str_value(raw, "email") or attendee.email
    attendee.first_name = _str_value(raw, "firstName") or attendee.first_name
    attendee.last_name = _str_value(raw, "lastName") or attendee.last_name
    attendee.phone_number = _str_value(raw, "phoneNumber") or attendee.phone_number
    attendee.date_of_birth = _parse_datetime(raw.get("dateOfBirth")) or attendee.date_of_birth
    attendee.raw_data = raw
    attendee.updated_at = datetime.now(timezone.utc)
    session.flush()
    return attendee


def _touch_sync_state(session: Session, entity_type: str) -> None:
    state = session.exec(
        select(WedofSyncState).where(WedofSyncState.entity_type == entity_type)
    ).first()
    if state is None:
        state = WedofSyncState(entity_type=entity_type)
        session.add(state)
    state.last_sync_at = datetime.now(timezone.utc)


def sync_attendees(limit: int = 100) -> dict[str, int]:
    """Fetch all attendees from Wedof and upsert them locally."""
    with get_wedof_client() as client, Session(engine) as session:
        count = 0
        for raw in client.paginate(client.attendees.get_app_api_attendee_list, limit=limit):
            _upsert_attendee(session, raw)
            count += 1
        _touch_sync_state(session, "attendees")
        session.commit()
    logger.info("Synced %s attendees from Wedof", count)
    return {"attendees": count}


def sync_trainings(limit: int = 100) -> dict[str, int]:
    """Fetch all trainings from Wedof and upsert them locally."""
    with get_wedof_client() as client, Session(engine) as session:
        count = 0
        for raw in client.paginate(client.trainings.get_app_api_training_list, limit=limit):
            external_id = _str_value(raw, "externalId", "id")
            if not external_id:
                continue
            training = session.exec(
                select(Training).where(Training.external_id == external_id)
            ).first()
            if training is None:
                training = Training(external_id=external_id)
                session.add(training)
            training.title = _str_value(raw, "title", "name") or training.title
            training.certif_info = _str_value(raw, "certifInfo") or training.certif_info
            training.raw_data = raw
            training.updated_at = datetime.now(timezone.utc)
            count += 1
        _touch_sync_state(session, "trainings")
        session.commit()
    logger.info("Synced %s trainings from Wedof", count)
    return {"trainings": count}


def sync_training_actions(limit: int = 100) -> dict[str, int]:
    """Fetch all training actions from Wedof and upsert them locally."""
    with get_wedof_client() as client, Session(engine) as session:
        count = 0
        for raw in client.paginate(
            client.training_actions.get_app_api_trainingaction_list, limit=limit
        ):
            external_id = _str_value(raw, "externalId", "id")
            if not external_id:
                continue
            action = session.exec(
                select(TrainingAction).where(TrainingAction.external_id == external_id)
            ).first()
            if action is None:
                action = TrainingAction(external_id=external_id)
                session.add(action)
            action.title = _str_value(raw, "title", "name") or action.title
            action.start_date = (
                _parse_datetime(raw.get("startDate") or raw.get("sessionStartDate"))
                or action.start_date
            )
            action.end_date = (
                _parse_datetime(raw.get("endDate") or raw.get("sessionEndDate"))
                or action.end_date
            )
            action.training_external_id = (
                _str_value(raw, "trainingExternalId", "trainingId") or action.training_external_id
            )
            action.raw_data = raw
            action.updated_at = datetime.now(timezone.utc)
            count += 1
        _touch_sync_state(session, "training_actions")
        session.commit()
    logger.info("Synced %s training actions from Wedof", count)
    return {"training_actions": count}


def _parse_wedof_paid_date(raw: dict[str, Any]) -> datetime | None:
    """Extract paid date from WEDOF folder raw data."""
    history = raw.get("history") or {}
    if isinstance(history, dict):
        return _parse_datetime(
            history.get("paidDate") or history.get("paymentDate") or raw.get("paymentDate")
        )
    return _parse_datetime(raw.get("paymentDate"))


def sync_registration_folders(limit: int = 100) -> dict[str, int]:
    """Fetch all registration folders from Wedof and upsert them locally."""
    with get_wedof_client() as client, Session(engine) as session:
        count = 0
        for raw in client.paginate(
            client.registration_folders.get_app_api_registrationfolder_list, limit=limit
        ):
            external_id = _str_value(raw, "externalId")
            if not external_id:
                continue

            folder = session.exec(
                select(RegistrationFolder).where(RegistrationFolder.external_id == external_id)
            ).first()
            if folder is None:
                folder = RegistrationFolder(external_id=external_id)
                session.add(folder)

            # Ensure the linked attendee exists before assigning the FK.
            attendee_id = _attendee_raw_id(raw)
            if attendee_id is not None:
                attendee = session.exec(
                    select(Attendee).where(Attendee.wedof_id == attendee_id)
                ).first()
                if attendee is None:
                    attendee_raw = raw.get("attendee")
                    if isinstance(attendee_raw, dict):
                        attendee = _upsert_attendee(session, attendee_raw)
                folder.attendee_id = attendee.id if attendee else folder.attendee_id

            folder.state = _str_value(raw, "state") or folder.state
            folder.billing_state = _str_value(raw, "billingState") or folder.billing_state
            folder.amount_ttc = _float_value(raw, "amountTtc", "totalTTC") or folder.amount_ttc
            folder.amount_ht = _float_value(raw, "amountHt", "totalHT") or folder.amount_ht
            folder.created_on = _parse_datetime(raw.get("createdOn")) or folder.created_on
            folder.updated_on = _parse_datetime(raw.get("updatedOn")) or folder.updated_on
            folder.wedof_paid_date = _parse_wedof_paid_date(raw) or folder.wedof_paid_date
            folder.training_action_external_id = (
                _str_value(raw, "trainingActionExternalId") or folder.training_action_external_id
            )
            folder.raw_data = raw
            folder.updated_at = datetime.now(timezone.utc)
            count += 1
        _touch_sync_state(session, "registration_folders")
        session.commit()
    logger.info("Synced %s registration folders from Wedof", count)
    return {"registration_folders": count}


def sync_certification_folders(limit: int = 100) -> dict[str, int]:
    """Fetch all certification folders from Wedof and upsert them locally."""
    with get_wedof_client() as client, Session(engine) as session:
        count = 0
        for raw in client.paginate(
            client.certification_folders.get_list, limit=limit
        ):
            external_id = _str_value(raw, "externalId")
            if not external_id:
                continue

            folder = session.exec(
                select(CertificationFolder).where(CertificationFolder.external_id == external_id)
            ).first()
            if folder is None:
                folder = CertificationFolder(external_id=external_id)
                session.add(folder)

            attendee_id = _attendee_raw_id(raw)
            if attendee_id is not None:
                attendee = session.exec(
                    select(Attendee).where(Attendee.wedof_id == attendee_id)
                ).first()
                if attendee is None:
                    attendee_raw = raw.get("attendee")
                    if isinstance(attendee_raw, dict):
                        attendee = _upsert_attendee(session, attendee_raw)
                folder.attendee_id = attendee.id if attendee else folder.attendee_id

            folder.state = _str_value(raw, "state") or folder.state
            folder.amount_ttc = _float_value(raw, "amountTtc", "totalTTC") or folder.amount_ttc
            folder.created_on = _parse_datetime(raw.get("createdOn")) or folder.created_on
            folder.updated_on = _parse_datetime(raw.get("updatedOn")) or folder.updated_on
            folder.registration_folder_external_id = (
                _str_value(raw, "registrationFolderExternalId")
                or folder.registration_folder_external_id
            )
            folder.raw_data = raw
            folder.updated_at = datetime.now(timezone.utc)
            count += 1
        _touch_sync_state(session, "certification_folders")
        session.commit()
    logger.info("Synced %s certification folders from Wedof", count)
    return {"certification_folders": count}


def sync_all(limit: int = 100) -> dict[str, Any]:
    """Run a full Wedof synchronisation."""
    results: dict[str, Any] = {}
    results.update(sync_attendees(limit=limit))
    results.update(sync_trainings(limit=limit))
    results.update(sync_training_actions(limit=limit))
    results.update(sync_registration_folders(limit=limit))
    results.update(sync_certification_folders(limit=limit))
    return results


def refresh_registration_folder(external_id: str) -> dict[str, Any]:
    """Fetch a single registration folder by external id and upsert it."""
    with get_wedof_client() as client, Session(engine) as session:
        raw = client.registration_folders.get_app_api_registrationfolder_show(external_id)
        if not raw:
            return {"status": "not_found", "external_id": external_id}

        folder = session.exec(
            select(RegistrationFolder).where(RegistrationFolder.external_id == external_id)
        ).first()
        if folder is None:
            folder = RegistrationFolder(external_id=external_id)
            session.add(folder)

        attendee_id = _attendee_raw_id(raw)
        if attendee_id is not None:
            attendee = session.exec(
                select(Attendee).where(Attendee.wedof_id == attendee_id)
            ).first()
            if attendee is None and isinstance(raw.get("attendee"), dict):
                attendee = _upsert_attendee(session, raw["attendee"])
            folder.attendee_id = attendee.id if attendee else folder.attendee_id

        folder.state = _str_value(raw, "state") or folder.state
        folder.billing_state = _str_value(raw, "billingState") or folder.billing_state
        folder.amount_ttc = _float_value(raw, "amountTtc", "totalTTC") or folder.amount_ttc
        folder.amount_ht = _float_value(raw, "amountHt", "totalHT") or folder.amount_ht
        folder.created_on = _parse_datetime(raw.get("createdOn")) or folder.created_on
        folder.updated_on = _parse_datetime(raw.get("updatedOn")) or folder.updated_on
        folder.wedof_paid_date = _parse_wedof_paid_date(raw) or folder.wedof_paid_date
        folder.training_action_external_id = (
            _str_value(raw, "trainingActionExternalId") or folder.training_action_external_id
        )
        folder.raw_data = raw
        folder.updated_at = datetime.now(timezone.utc)
        session.commit()
    return {"status": "synced", "external_id": external_id}


def refresh_certification_folder(external_id: str) -> dict[str, Any]:
    """Fetch a single certification folder by external id and upsert it."""
    with get_wedof_client() as client, Session(engine) as session:
        raw = client.certification_folders.get_id_show(external_id)
        if not raw:
            return {"status": "not_found", "external_id": external_id}

        folder = session.exec(
            select(CertificationFolder).where(CertificationFolder.external_id == external_id)
        ).first()
        if folder is None:
            folder = CertificationFolder(external_id=external_id)
            session.add(folder)

        attendee_id = _attendee_raw_id(raw)
        if attendee_id is not None:
            attendee = session.exec(
                select(Attendee).where(Attendee.wedof_id == attendee_id)
            ).first()
            if attendee is None and isinstance(raw.get("attendee"), dict):
                attendee = _upsert_attendee(session, raw["attendee"])
            folder.attendee_id = attendee.id if attendee else folder.attendee_id

        folder.state = _str_value(raw, "state") or folder.state
        folder.amount_ttc = _float_value(raw, "amountTtc", "totalTTC") or folder.amount_ttc
        folder.created_on = _parse_datetime(raw.get("createdOn")) or folder.created_on
        folder.updated_on = _parse_datetime(raw.get("updatedOn")) or folder.updated_on
        folder.registration_folder_external_id = (
            _str_value(raw, "registrationFolderExternalId")
            or folder.registration_folder_external_id
        )
        folder.raw_data = raw
        folder.updated_at = datetime.now(timezone.utc)
        session.commit()
    return {"status": "synced", "external_id": external_id}


def store_webhook_event(event_type: str | None, payload: dict[str, Any]) -> WedofWebhookEvent:
    """Persist a Wedof webhook payload for asynchronous processing."""
    with Session(engine) as session:
        event = WedofWebhookEvent(event_type=event_type, payload=payload)
        session.add(event)
        session.commit()
        session.refresh(event)
        return event


def process_webhook_event(event_id: str) -> dict[str, Any]:
    """Process a stored webhook: refresh impacted entities and mark as processed."""
    with Session(engine) as session:
        event = session.get(WedofWebhookEvent, event_id)
        if event is None:
            return {"status": "not_found", "event_id": event_id}

        payload = event.payload or {}
        event_type = event.event_type or ""
        triggered: list[dict[str, str]] = []

        def maybe_trigger(entity: dict[str, Any] | None, task_name: str) -> None:
            if not entity:
                return
            external_id = _str_value(entity, "externalId")
            if external_id:
                triggered.append({"task": task_name, "external_id": external_id})

        # Webhook payloads usually contain a nested entity.
        maybe_trigger(payload.get("registrationFolder"), "refresh_registration_folder")
        maybe_trigger(payload.get("certificationFolder"), "refresh_certification_folder")
        maybe_trigger(payload.get("attendee"), "refresh_attendee")

        # Fallback: look for direct external ids in the payload root.
        if not triggered:
            reg_ext = _str_value(payload, "registrationFolderExternalId", "externalId")
            cert_ext = _str_value(payload, "certificationFolderExternalId")
            if reg_ext:
                triggered.append({"task": "refresh_registration_folder", "external_id": reg_ext})
            if cert_ext:
                triggered.append(
                    {"task": "refresh_certification_folder", "external_id": cert_ext}
                )

        event.processed = True
        session.commit()

    # Schedule refresh tasks outside of the DB transaction.
    from ..tasks import (
        refresh_certification_folder_task,
        refresh_registration_folder_task,
        sync_attendees_task,
    )

    for item in triggered:
        if item["task"] == "refresh_registration_folder":
            refresh_registration_folder_task.delay(item["external_id"])
        elif item["task"] == "refresh_certification_folder":
            refresh_certification_folder_task.delay(item["external_id"])
        elif item["task"] == "refresh_attendee":
            # Attendee refresh is implemented as a partial attendees sync.
            sync_attendees_task.delay()

    return {
        "status": "processed",
        "event_id": event_id,
        "event_type": event_type,
        "triggered": triggered,
    }
