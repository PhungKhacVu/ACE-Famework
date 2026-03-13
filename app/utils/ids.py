"""ID generation utilities (stdlib only)."""
import uuid


def new_id() -> str:
    """Return a new UUID4 hex string (32 hex chars, no dashes)."""
    return uuid.uuid4().hex
