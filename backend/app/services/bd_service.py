"""BD service functions — extracted from bd router so sites aliases can call them.

Extracting the business logic here keeps both the original /api/bd/* routes and
the /sites/* alias routes pointing at the same implementation, with no duplication.
"""
from typing import Optional

from app.domain.state_machine import SiteStatus
from app.domain.schemas.site import SiteResponse
from app.domain.schemas.common import OkResponse
from app.services.audit_service import write_audit_event
from app.services.notification_service import send as notify


# ── Shortlist ──────────────────────────────────────────────────────────────────

async def svc_shortlist_draft(
    db,
    *,
    site_id: str,
    actor: str,
    tenant_id: str,
) -> SiteResponse:
    """Core logic for draft_submitted -> shortlisted.

    Called by bd.shortlist_draft and sites.patch_site_status alias.
    """
    # TODO(db): update sites set status=shortlisted where id=site_id
    await write_audit_event(
        db,
        site_id=site_id,
        actor=actor,
        action="shortlist",
        from_status=SiteStatus.DRAFT_SUBMITTED,
        to_status=SiteStatus.SHORTLISTED,
    )
    await notify(
        event="draft_shortlisted",
        recipient_ids=["site-owner"],  # TODO(db): resolve exec user ID from site
        channels=["email", "in_app"],
        payload={"site_id": site_id},
    )
    return SiteResponse(
        id=site_id, code="STUB", name="stub", city="stub",
        tenant_id=tenant_id, status=SiteStatus.SHORTLISTED, created_by="stub",
    )


# ── Submit details ─────────────────────────────────────────────────────────────

async def svc_submit_details(
    db,
    *,
    site_id: str,
    actor: str,
    tenant_id: str,
) -> SiteResponse:
    """Core logic for shortlisted -> details_submitted.

    Called by bd.submit_details_for_review and sites.patch_site_status alias.
    """
    # TODO(db): update sites set status=details_submitted, save body to site_details
    await write_audit_event(
        db,
        site_id=site_id,
        actor=actor,
        action="submit_details_for_review",
        from_status=SiteStatus.SHORTLISTED,
        to_status=SiteStatus.DETAILS_SUBMITTED,
    )
    await notify(
        event="details_submitted_for_review",
        recipient_ids=["supervisor-in-tenant"],
        channels=["email", "slack", "in_app"],
        payload={"site_id": site_id},
    )
    return SiteResponse(
        id=site_id, code="STUB", name="stub", city="stub",
        tenant_id=tenant_id, status=SiteStatus.DETAILS_SUBMITTED, created_by=actor,
    )


# ── Approve ────────────────────────────────────────────────────────────────────

async def svc_approve_shortlist(
    db,
    *,
    site_id: str,
    actor: str,
    tenant_id: str,
    expected_loi_days: int,
) -> SiteResponse:
    """Core logic for details_submitted -> approved.

    Called by bd.approve_shortlist and sites.patch_site_status alias.
    """
    # TODO(db): update sites set status=approved, expected_loi_days=expected_loi_days
    await write_audit_event(
        db,
        site_id=site_id,
        actor=actor,
        action="approve_details",
        from_status=SiteStatus.DETAILS_SUBMITTED,
        to_status=SiteStatus.APPROVED,
        detail=f"expected_loi_days={expected_loi_days}",
    )
    await notify(
        event="site_approved",
        recipient_ids=["site-owner"],
        channels=["email", "in_app"],
        payload={"site_id": site_id, "expected_loi_days": expected_loi_days},
    )
    return SiteResponse(
        id=site_id, code="STUB", name="stub", city="stub",
        tenant_id=tenant_id, status=SiteStatus.APPROVED, created_by="stub",
    )


# ── Push to payments ───────────────────────────────────────────────────────────

async def svc_push_to_payments(
    db,
    *,
    site_id: str,
    actor: str,
) -> OkResponse:
    """Core logic for loi_uploaded -> pushed_to_payments.

    Called by staging.push_to_payments and sites.patch_site_status alias.
    """
    # TODO(db): update sites set status=pushed_to_payments where id=site_id
    # TODO(payments): activate Payments module for this site
    await write_audit_event(
        db,
        site_id=site_id,
        actor=actor,
        action="push_to_payments",
        from_status=SiteStatus.LOI_UPLOADED,
        to_status=SiteStatus.PUSHED_TO_PAYMENTS,
    )
    await notify(
        event="site_pushed_to_payments",
        recipient_ids=["site-owner", "finance-team"],
        channels=["email", "slack", "in_app"],
        payload={"site_id": site_id},
    )
    return OkResponse(message=f"Site {site_id} pushed to Payments module (stub)")


# ── Reject ─────────────────────────────────────────────────────────────────────

async def svc_reject_site(
    db,
    *,
    site_id: str,
    actor: str,
    reasons: list[str],
    comment: Optional[str] = None,
) -> OkResponse:
    """Core logic for * -> rejected.

    Called by bd.reject_draft and sites.reject_site / sites.patch_site_status alias.
    """
    # TODO(db): update sites set status=rejected, rejection_reasons=reasons where id=site_id
    await write_audit_event(
        db,
        site_id=site_id,
        actor=actor,
        action="reject",
        to_status=SiteStatus.REJECTED,
        detail=f"Reasons: {reasons}" + (f" | {comment}" if comment else ""),
    )
    await notify(
        event="draft_rejected",
        recipient_ids=["site-owner"],
        channels=["email", "in_app"],
        payload={"site_id": site_id, "reasons": reasons},
    )
    return OkResponse(message=f"Site {site_id} rejected")


# ── Archive ────────────────────────────────────────────────────────────────────

async def svc_archive_site(
    db,
    *,
    site_id: str,
    actor: str,
    note: Optional[str] = None,
) -> OkResponse:
    """Core logic for * -> archived.

    Called by bd.archive_draft and sites.archive_site / sites.patch_site_status alias.
    """
    # TODO(db): update sites set status=archived, archive_note=note where id=site_id
    await write_audit_event(
        db,
        site_id=site_id,
        actor=actor,
        action="archive",
        to_status=SiteStatus.ARCHIVED,
        detail=note,
    )
    return OkResponse(message=f"Site {site_id} archived")


# ── Reassign ───────────────────────────────────────────────────────────────────

async def svc_reassign_site(
    db,
    *,
    site_id: str,
    actor: str,
    new_owner_id: str,
) -> OkResponse:
    """Core logic for site reassignment (no status change).

    Called by bd.reassign_site and sites.assign_site alias.
    """
    # TODO(db): update sites set created_by=new_owner_id where id=site_id
    await write_audit_event(
        db,
        site_id=site_id,
        actor=actor,
        action="reassign_site",
        detail=f"reassigned to {new_owner_id}",
    )
    return OkResponse(message=f"Site {site_id} reassigned to {new_owner_id}")


# ── Save details ───────────────────────────────────────────────────────────────

async def svc_save_details(
    db,
    *,
    site_id: str,
    actor: str,
    details: dict,
) -> OkResponse:
    """Core logic for saving partial details without transitioning status.

    Called by bd.save_draft_details and sites.patch_site_details alias.
    """
    # TODO(db): upsert site_details where site_id=site_id, set details_completion='partial'
    return OkResponse(message=f"Details draft saved for site {site_id}")
