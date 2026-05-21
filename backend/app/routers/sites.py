"""Sites router — overview list, single site, per-site tabs, and resource-style action aliases.

The action routes (POST /sites, PATCH /sites/{id}/status, etc.) are thin aliases that delegate
to the underlying domain service functions.  No business logic lives here — all logic is in
app/services/bd_service.py and app/services/loi_service.py.
"""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status as http_status

from app.core.deps import CurrentUser, DbDep, TenantId
from app.rbac.guards import require_role
from app.rbac.roles import Role
from app.domain.state_machine import SiteStatus, assert_transition, ALLOWED_TRANSITIONS
from app.domain.schemas.site import (
    CreateDraftRequest,
    SiteListResponse,
    SiteResponse,
    PatchSiteStatusRequest,
    PatchSiteDetailsRequest,
    ArchiveSiteRequest,
    AssignSiteRequest,
)
from app.domain.schemas.common import OkResponse
from app.domain.schemas.loi import LOIUploadResponse
from app.domain.schemas.audit import AuditListResponse
from app.services.bd_service import (
    svc_shortlist_draft,
    svc_submit_details,
    svc_approve_shortlist,
    svc_push_to_payments,
    svc_reject_site,
    svc_archive_site,
    svc_reassign_site,
    svc_save_details,
)
from app.services.loi_service import svc_upload_loi
from app.services.audit_service import write_audit_event
from app.services.notification_service import send as notify

router = APIRouter(prefix="/sites", tags=["Sites"])


@router.get(
    "",
    response_model=SiteListResponse,
    summary="List all sites",
    description="Returns all sites visible to the current user, scoped by role and tenant.",
)
async def list_sites(
    db: DbDep,
    current_user: CurrentUser,
    tenant_id: TenantId,
    status: Optional[str] = Query(None, description="Filter by status"),
    city: Optional[str] = Query(None, description="Filter by city"),
) -> SiteListResponse:
    """List sites (role + tenant scoped)."""
    # TODO(db): SELECT * FROM sites WHERE tenant_id=tenant_id [AND status=status] [AND city=city]
    # TODO(db): if exec, add AND created_by=current_user.sub
    return SiteListResponse(items=[], total=0)


@router.get(
    "/{site_id}",
    response_model=SiteResponse,
    summary="Get a single site",
    description="Returns full site detail for the Overview drawer tab.",
)
async def get_site(
    site_id: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant_id: TenantId,
) -> SiteResponse:
    """Get site by ID (Overview tab data)."""
    # TODO(db): SELECT * FROM sites WHERE id=site_id AND tenant_id=tenant_id
    from fastapi import HTTPException, status as http_status
    raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Site not found (stub)")


@router.get(
    "/{site_id}/activity",
    response_model=AuditListResponse,
    summary="Get site activity feed",
    description="Returns the ordered audit log for a single site (Activity tab).",
)
async def get_site_activity(
    site_id: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant_id: TenantId,
) -> AuditListResponse:
    """Get site activity / audit feed (Activity tab)."""
    # TODO(db): SELECT * FROM audit_events WHERE site_id=site_id ORDER BY created_at DESC
    return AuditListResponse(items=[], total=0)


@router.get(
    "/{site_id}/documents",
    summary="Get site documents list",
    description="Returns the list of documents attached to a site (Documents tab).",
)
async def get_site_documents(
    site_id: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant_id: TenantId,
) -> dict:
    """Get site documents (Documents tab)."""
    # TODO(db): SELECT * FROM site_documents WHERE site_id=site_id
    # TODO(storage): generate signed download URLs
    return {"site_id": site_id, "documents": []}


# ── Action aliases ─────────────────────────────────────────────────────────────
# Each route below is a 1-3 line alias that imports + calls the service function.
# No business logic lives here.

@router.post(
    "",
    response_model=SiteResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create a draft site (alias for POST /api/bd/drafts)",
    description="Creates a new site in draft_submitted state. "
                "Delegates to the same logic as POST /api/bd/drafts.",
)
async def create_site(
    body: CreateDraftRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.EXECUTIVE))],
    tenant_id: TenantId,
) -> SiteResponse:
    """Alias: create_draft. Delegates to bd create_draft logic."""
    import uuid
    site_id = str(uuid.uuid4())
    city_code = body.city[:3].upper()
    site_code = f"BT-{city_code}-{str(uuid.uuid4())[:4].upper()}"

    # TODO(db): insert into sites table
    mock_site = SiteResponse(
        id=site_id,
        code=site_code,
        name=body.name,
        city=body.city,
        tenant_id=tenant_id,
        status=SiteStatus.DRAFT_SUBMITTED,
        created_by=current_user["name"],
        visit_date=body.visit_date,
        days=0,
        stage="draft",
    )
    await write_audit_event(
        db,
        site_id=site_id,
        actor=current_user["name"],
        action="create_draft",
        from_status=None,
        to_status=SiteStatus.DRAFT_SUBMITTED,
    )
    await notify(
        event="draft_submitted",
        recipient_ids=["supervisor-in-tenant"],
        channels=["email", "slack", "in_app"],
        payload={"site_id": site_id, "site_name": body.name, "city": body.city},
    )
    return mock_site


@router.patch(
    "/{site_id}/status",
    summary="Universal status-transition dispatcher (alias)",
    description="Routes to the correct domain handler based on (currentStatus → newStatus). "
                "LOI upload is rejected (must use POST /sites/{id}/loi for multipart).",
)
async def patch_site_status(
    site_id: str,
    body: PatchSiteStatusRequest,
    db: DbDep,
    current_user: CurrentUser,
    tenant_id: TenantId,
):
    """Dispatcher: validates transition then delegates to the appropriate service function.

    Covered transitions (from ALLOWED_TRANSITIONS):
      DRAFT_SUBMITTED   → SHORTLISTED        → svc_shortlist_draft
      SHORTLISTED       → DETAILS_SUBMITTED  → svc_submit_details
      DETAILS_SUBMITTED → APPROVED           → svc_approve_shortlist (payload.expectedLoiDays)
      APPROVED          → LOI_UPLOADED       → 400 (use POST /sites/{id}/loi for multipart)
      LOI_UPLOADED      → PUSHED_TO_PAYMENTS → svc_push_to_payments
      *                 → REJECTED           → svc_reject_site (payload.reasons, payload.comment)
      *                 → ARCHIVED           → svc_archive_site (payload.note)
    """
    new_status = body.status
    payload = body.payload or {}

    # TODO(db): fetch current status from DB — using DRAFT_SUBMITTED as stub
    current_status = SiteStatus.DRAFT_SUBMITTED  # TODO(db): replace with real DB fetch

    assert_transition(current_status, new_status)

    # Terminal catch: LOI upload must go through multipart endpoint
    if new_status == SiteStatus.LOI_UPLOADED:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="LOI upload requires multipart. Use POST /sites/{id}/loi instead.",
        )

    if new_status == SiteStatus.REJECTED:
        reasons = payload.get("reasons", [])
        comment = payload.get("comment")
        return await svc_reject_site(db, site_id=site_id, actor=current_user["name"], reasons=reasons, comment=comment)

    if new_status == SiteStatus.ARCHIVED:
        note = payload.get("note")
        return await svc_archive_site(db, site_id=site_id, actor=current_user["name"], note=note)

    if new_status == SiteStatus.SHORTLISTED:
        return await svc_shortlist_draft(db, site_id=site_id, actor=current_user["name"], tenant_id=tenant_id)

    if new_status == SiteStatus.DETAILS_SUBMITTED:
        return await svc_submit_details(db, site_id=site_id, actor=current_user["name"], tenant_id=tenant_id)

    if new_status == SiteStatus.APPROVED:
        expected_loi_days = payload.get("expectedLoiDays", 30)
        return await svc_approve_shortlist(
            db,
            site_id=site_id,
            actor=current_user["name"],
            tenant_id=tenant_id,
            expected_loi_days=expected_loi_days,
        )

    if new_status == SiteStatus.PUSHED_TO_PAYMENTS:
        return await svc_push_to_payments(db, site_id=site_id, actor=current_user["name"])

    raise HTTPException(
        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"No handler registered for transition to {new_status}",
    )


@router.patch(
    "/{site_id}/details",
    response_model=OkResponse,
    summary="Save partial details without transitioning (alias for POST /api/bd/shortlist/{id}/details/save)",
    description="Saves partial 17-field form. Status unchanged. "
                "Delegates to svc_save_details.",
)
async def patch_site_details(
    site_id: str,
    body: PatchSiteDetailsRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.EXECUTIVE))],
    tenant_id: TenantId,
) -> OkResponse:
    """Alias: save_draft_details."""
    return await svc_save_details(db, site_id=site_id, actor=current_user["name"], details=body.details.model_dump())


@router.post(
    "/{site_id}/archive",
    response_model=OkResponse,
    summary="Archive a site (alias for POST /api/bd/drafts/{id}/archive)",
    description="Soft-archives a site. Delegates to svc_archive_site.",
)
async def archive_site(
    site_id: str,
    body: ArchiveSiteRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR, Role.SUB_SUPERVISOR))],
    tenant_id: TenantId,
) -> OkResponse:
    """Alias: archive_draft."""
    return await svc_archive_site(db, site_id=site_id, actor=current_user["name"], note=body.note)


@router.post(
    "/{site_id}/reject",
    response_model=OkResponse,
    summary="Reject a site (alias for POST /api/bd/drafts/{id}/reject)",
    description="Rejects a site with reasons. Delegates to svc_reject_site.",
)
async def reject_site(
    site_id: str,
    body: "RejectSiteBody",
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR, Role.SUB_SUPERVISOR))],
    tenant_id: TenantId,
) -> OkResponse:
    """Alias: reject_draft."""
    return await svc_reject_site(db, site_id=site_id, actor=current_user["name"], reasons=body.reasons, comment=body.comment)


@router.post(
    "/{site_id}/assign",
    response_model=OkResponse,
    summary="Reassign site to an exec (alias for POST /api/bd/shortlist/{id}/reassign)",
    description="Reassigns a site to a different exec. Body: {exec_id}. "
                "Delegates to svc_reassign_site.",
)
async def assign_site(
    site_id: str,
    body: AssignSiteRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR))],
    tenant_id: TenantId,
) -> OkResponse:
    """Alias: reassign_site."""
    return await svc_reassign_site(db, site_id=site_id, actor=current_user["name"], new_owner_id=body.exec_id)


@router.post(
    "/{site_id}/loi",
    response_model=LOIUploadResponse,
    summary="Upload LOI document (alias for POST /api/loi/{id}/upload)",
    description="Accepts multipart file upload. "
                "Delegates to svc_upload_loi. Transitions approved -> loi_uploaded.",
)
async def upload_loi_alias(
    site_id: str,
    file: Annotated[UploadFile, File(description="Signed LOI document (PDF or image)")],
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.EXECUTIVE))],
    tenant_id: TenantId,
) -> LOIUploadResponse:
    """Alias: upload_loi. Reads file bytes and delegates to svc_upload_loi."""
    file_bytes = await file.read()
    # TODO(storage): pass file_bytes + file.filename to svc_upload_loi once storage is wired
    return await svc_upload_loi(db, site_id=site_id, actor=current_user["name"], file_bytes=file_bytes, filename=file.filename)


# ── Inline schema for reject body (avoids import cycle from site.py for comment field) ──
from pydantic import BaseModel  # noqa: E402

class RejectSiteBody(BaseModel):
    reasons: list[str]
    comment: Optional[str] = None
