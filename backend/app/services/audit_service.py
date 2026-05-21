"""Audit service — writes an audit row on every state transition.

TODO(db): replace stub with real DB insert via SQLAlchemy/SQLModel session.
"""
from datetime import datetime, timezone
import uuid


async def write_audit_event(
    db,  # TODO(db): type as AsyncSession once SQLModel is wired
    *,
    site_id: str,
    actor: str,
    action: str,
    from_status: str | None = None,
    to_status: str | None = None,
    detail: str | None = None,
) -> dict:
    """Write an audit row and return it.

    Currently a stub that prints to stdout.
    When DB is wired, insert into the audit_events table.
    """
    event = {
        "id": str(uuid.uuid4()),
        "site_id": site_id,
        "actor": actor,
        "action": action,
        "from_status": from_status,
        "to_status": to_status,
        "detail": detail,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # TODO(db): await db.execute(insert(AuditEvent).values(**event))
    print(f"[AUDIT] {event}")
    return event
