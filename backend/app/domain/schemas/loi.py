"""Pydantic schemas for LOI resources."""
from __future__ import annotations
from datetime import date
from typing import Optional
from pydantic import BaseModel


class SetLOITimelineRequest(BaseModel):
    expected_loi_days: int


class LOIUploadResponse(BaseModel):
    site_id: str
    loi_uploaded: bool
    loi_uploaded_at: Optional[date] = None
    days_to_loi: Optional[int] = None


class LOIViewResponse(BaseModel):
    site_id: str
    file_url: Optional[str] = None  # TODO(storage): real signed URL
    uploaded_at: Optional[date] = None
    uploaded_by: Optional[str] = None
