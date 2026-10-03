from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    aggregate_id: str
    occurred_at: datetime
    payload: dict[str, Any]
