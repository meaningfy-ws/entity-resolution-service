import json
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


def serialize_to_json(data: dict[str, Any]) -> str:
    """Serialize a dictionary to a JSON string."""
    return json.dumps(data)
