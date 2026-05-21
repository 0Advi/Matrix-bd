"""Canonical site state machine.

Mirrors frontend src/lib/stateMachine.js exactly.
Every state transition must pass through `assert_transition` before
being persisted; audit_service is called by the router after a successful transition.
"""
from enum import Enum
from fastapi import HTTPException, status


class SiteStatus(str, Enum):
    DRAFT_SUBMITTED    = "draft_submitted"
    SHORTLISTED        = "shortlisted"
    DETAILS_SUBMITTED  = "details_submitted"
    APPROVED           = "approved"
    LOI_UPLOADED       = "loi_uploaded"
    PUSHED_TO_PAYMENTS = "pushed_to_payments"
    REJECTED           = "rejected"
    ARCHIVED           = "archived"


# Allowed transitions: from_status -> [to_status, ...]
ALLOWED_TRANSITIONS: dict[SiteStatus, list[SiteStatus]] = {
    SiteStatus.DRAFT_SUBMITTED:    [SiteStatus.SHORTLISTED,        SiteStatus.REJECTED, SiteStatus.ARCHIVED],
    SiteStatus.SHORTLISTED:        [SiteStatus.DETAILS_SUBMITTED,  SiteStatus.REJECTED, SiteStatus.ARCHIVED],
    SiteStatus.DETAILS_SUBMITTED:  [SiteStatus.APPROVED,           SiteStatus.REJECTED, SiteStatus.ARCHIVED],
    SiteStatus.APPROVED:           [SiteStatus.LOI_UPLOADED,       SiteStatus.REJECTED, SiteStatus.ARCHIVED],
    SiteStatus.LOI_UPLOADED:       [SiteStatus.PUSHED_TO_PAYMENTS, SiteStatus.REJECTED, SiteStatus.ARCHIVED],
    SiteStatus.PUSHED_TO_PAYMENTS: [],  # terminal
    SiteStatus.REJECTED:           [],  # terminal
    SiteStatus.ARCHIVED:           [],  # terminal
}


def can_transition(from_status: SiteStatus, to_status: SiteStatus) -> bool:
    return to_status in ALLOWED_TRANSITIONS.get(from_status, [])


def assert_transition(from_status: SiteStatus, to_status: SiteStatus) -> None:
    """Raise HTTP 422 if the transition is not allowed."""
    if not can_transition(from_status, to_status):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid state transition: {from_status} -> {to_status}",
        )
