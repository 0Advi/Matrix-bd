"""Shared Pydantic models."""
from pydantic import BaseModel


class OkResponse(BaseModel):
    ok: bool = True
    message: str = "success"


class ErrorResponse(BaseModel):
    detail: str
