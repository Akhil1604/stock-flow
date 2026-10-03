import json
import logging
from datetime import UTC, datetime

from kafka import KafkaProducer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.infrastructure.models import OutboxEventModel

logger = logging.getLogger(__name__)


class KafkaEventPublisher:
    def __init__(self) -> None:
        self._producer: KafkaProducer | None = None
        self._disabled = False

    def _get_producer(self) -> KafkaProducer | None:
        if self._disabled:
            return None
        if self._producer:
            return self._producer
        try:
            self._producer = KafkaProducer(
                bootstrap_servers=get_settings().kafka_bootstrap_servers,
                value_serializer=lambda value: json.dumps(value).encode("utf-8"),
                retries=5,
                acks="all",
                enable_idempotence=True,
            )
            return self._producer
        except Exception as exc:  # Kafka is optional for local API-only development.
            self._disabled = True
            logger.warning("Kafka unavailable; outbox will remain pending: %s", exc)
            return None

    def publish(self, event: OutboxEventModel) -> bool:
        producer = self._get_producer()
        if not producer:
            return False
        try:
            producer.send(
                get_settings().kafka_topic,
                key=event.aggregate_id.encode("utf-8"),
                value={
                    "id": event.id,
                    "type": event.event_type,
                    "aggregate_id": event.aggregate_id,
                    "payload": event.payload,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                },
            ).get(timeout=10)
            return True
        except Exception as exc:
            logger.exception("Failed to publish outbox event %s: %s", event.id, exc)
            return False


def publish_pending_events(
    publisher: KafkaEventPublisher, db: Session, batch_size: int = 50
) -> int:
    events = db.scalars(
        select(OutboxEventModel)
        .where(OutboxEventModel.published.is_(False))
        .order_by(OutboxEventModel.created_at)
        .limit(batch_size)
    ).all()
    published_count = 0
    for event in events:
        event.attempts += 1
        if publisher.publish(event):
            event.published = True
            event.published_at = datetime.now(UTC)
            event.last_error = None
            published_count += 1
        else:
            event.last_error = "publisher unavailable or publish failed"
    if events:
        db.commit()
    return published_count
