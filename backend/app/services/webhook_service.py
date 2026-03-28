"""Webhook delivery service: fires async HTTP POST to registered webhook URLs."""

import logging
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.webhook import Webhook

logger = logging.getLogger(__name__)


async def fire_webhook(event_type: str, payload: dict[str, Any]) -> None:
    """Send POST requests to all active webhooks registered for the given event type."""
    db: Session = SessionLocal()
    try:
        webhooks = (
            db.query(Webhook)
            .filter(Webhook.event_type == event_type, Webhook.is_active.is_(True))
            .all()
        )

        if not webhooks:
            return

        async with httpx.AsyncClient(timeout=10.0) as client:
            for webhook in webhooks:
                try:
                    response = await client.post(
                        webhook.url,
                        json={"event": event_type, "data": payload},
                        headers={"Content-Type": "application/json"},
                    )
                    logger.info(
                        f"Webhook delivered: id={webhook.id} url={webhook.url} "
                        f"event={event_type} status={response.status_code}"
                    )
                except Exception as e:
                    logger.error(
                        f"Webhook delivery failed: id={webhook.id} url={webhook.url} "
                        f"event={event_type} error={e}"
                    )
    finally:
        db.close()
