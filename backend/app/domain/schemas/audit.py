"""Pydantic schemas for audit events."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AuditEvent(BaseModel):
    id: str
    site_id: str
    actor: str
    action: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    detail: Optional[str] = None
    created_at: datetime


class AuditListResponse(BaseModel):
    items: list[AuditEvent]
    total: int
