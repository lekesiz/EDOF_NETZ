from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Header, HTTPException, Request, status

from ..config import get_settings
from ..services.wedof import store_webhook_event
from ..tasks import process_wedof_webhook_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/wedof")
async def wedof_webhook(
    request: Request,
    x_wedof_event: str | None = Header(None, alias="X-WEDOF-EVENT"),
    x_wedof_secret: str | None = Header(None, alias="X-WEDOF-SECRET"),
) -> dict[str, str]:
    """Receive Wedof webhook events and queue them for processing."""
    settings = get_settings()
    if settings.wedof_webhook_secret and x_wedof_secret != settings.wedof_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )

    body = await request.body()
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Invalid Wedof webhook body: %s", exc)
        return {"status": "ignored", "reason": "invalid json"}

    event_type = x_wedof_event or payload.get("event") or payload.get("eventType")
    event = store_webhook_event(event_type, payload)
    process_wedof_webhook_task.delay(event.id)
    logger.info("Stored Wedof webhook event %s (%s)", event.id, event_type)
    return {"status": "accepted", "event_id": event.id}
