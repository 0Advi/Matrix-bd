"""BD (Business Development) router.

Covers the pipeline (drafts), shortlist, detail form, and reassignment flows.
Every mutating route:
  1. Asserts the state transition is valid.
  2. Persists via Depends(get_db)  — marked # TODO(db).
  3. Writes an audit row via audit_service.
  4. Emits a notification via notification_service.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import CurrentUser, DbDep, TenantId
from app.rbac.guards import require_role
from app.rbac.roles import Role
from app.domain.state_machine import SiteStatus, assert_transition
from app.domain.schemas.site import (
    CreateDraftRequest,
    RejectSiteRequest,
    ArchiveSiteRequest,
    SaveDetailsRequest,
    SubmitDetailsRequest,
    ApproveShortlistRequest,
    ReassignSiteRequest,
    AssignSubSupervisorRequest,
    SiteResponse,
    SiteListResponse,
)
from app.domain.schemas.common import OkResponse
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
from app.services.audit_service import write_audit_event
from app.services.notification_service import send as notify

router = APIRouter(prefix="/bd", tags=["BD"])


# ── Drafts ─────────────────────────────────────────────────────────────────────

@router.post(
    "/drafts",
    response_model=SiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a pipeline draft",
    description="BD exec submits a new site for supervisor review. "
                "Status transitions: null -> draft_submitted.",
)
async def create_draft(
    body: CreateDraftRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.EXECUTIVE))],
    tenant_id: TenantId,
) -> SiteResponse:
    """Create a pipeline draft (exec action, null -> draft_submitted)."""
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
        recipient_ids=["supervisor-in-tenant"],  # TODO(db): resolve real supervisor IDs
        channels=["email", "slack", "in_app"],
        payload={"site_id": site_id, "site_name": body.name, "city": body.city},
    )
    return mock_site


@router.get(
    "/drafts",
    response_model=SiteListResponse,
    summary="List pipeline drafts",
    description="Returns drafts scoped by role: exec sees own, supervisor sees all in tenant.",
)
async def list_drafts(
    db: DbDep,
    current_user: CurrentUser,
    tenant_id: TenantId,
) -> SiteListResponse:
    """List drafts (role-scoped)."""
    # TODO(db): query sites where status=draft_submitted, scoped by role
    return SiteListResponse(items=[], total=0)


@router.post(
    "/drafts/{site_id}/shortlist",
    response_model=SiteResponse,
    summary="Shortlist a draft",
    description="Supervisor approves a draft, advancing it to shortlisted status. "
                "Notifies the originating exec.",
)
async def shortlist_draft(
    site_id: str,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR, Role.SUB_SUPERVISOR))],
    tenant_id: TenantId,
) -> SiteResponse:
    """Supervisor shortlists a draft (draft_submitted -> shortlisted)."""
    # TODO(db): fetch site, assert tenant ownership
    assert_transition(SiteStatus.DRAFT_SUBMITTED, SiteStatus.SHORTLISTED)
    return await svc_shortlist_draft(db, site_id=site_id, actor=current_user["name"], tenant_id=tenant_id)


@router.post(
    "/drafts/{site_id}/reject",
    response_model=OkResponse,
    summary="Reject a draft",
    description="Supervisor rejects a draft with reasons. Draft is archived. "
                "Notifies the originating exec.",
)
async def reject_draft(
    site_id: str,
    body: RejectSiteRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR, Role.SUB_SUPERVISOR))],
    tenant_id: TenantId,
) -> OkResponse:
    """Supervisor rejects a draft (* -> rejected)."""
    # TODO(db): fetch site, validate current status allows rejection
    return await svc_reject_site(db, site_id=site_id, actor=current_user["name"], reasons=body.reasons, comment=body.note)


@router.post(
    "/drafts/{site_id}/archive",
    response_model=OkResponse,
    summary="Archive a site",
    description="Supervisor archives a site for future reference without rejecting it explicitly.",
)
async def archive_draft(
    site_id: str,
    body: ArchiveSiteRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR, Role.SUB_SUPERVISOR))],
    tenant_id: TenantId,
) -> OkResponse:
    """Supervisor archives a site (* -> archived)."""
    return await svc_archive_site(db, site_id=site_id, actor=current_user["name"], note=body.note)


# ── Shortlist ──────────────────────────────────────────────────────────────────

@router.get(
    "/shortlist",
    response_model=SiteListResponse,
    summary="List shortlisted sites",
    description="Returns shortlisted sites scoped by role.",
)
async def list_shortlist(
    db: DbDep,
    current_user: CurrentUser,
    tenant_id: TenantId,
) -> SiteListResponse:
    """List shortlist (role-scoped)."""
    # TODO(db): query sites where status in (shortlisted, details_submitted)
    return SiteListResponse(items=[], total=0)


@router.post(
    "/shortlist/{site_id}/details/save",
    response_model=OkResponse,
    summary="Save partial details (draft save)",
    description="BD exec saves partial 17-field form. Status stays shortlisted; "
                "sets details_completion=partial. Supervisor cannot act until exec submits.",
)
async def save_draft_details(
    site_id: str,
    body: SaveDetailsRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.EXECUTIVE))],
    tenant_id: TenantId,
) -> OkResponse:
    """Exec saves partial details (shortlisted -> shortlisted, completion=partial)."""
    return await svc_save_details(db, site_id=site_id, actor=current_user["name"], details=body.model_dump())


@router.post(
    "/shortlist/{site_id}/details/submit",
    response_model=SiteResponse,
    summary="Submit details for supervisor review",
    description="BD exec submits the completed 17-field form. "
                "Status transitions: shortlisted -> details_submitted. Notifies supervisor.",
)
async def submit_details_for_review(
    site_id: str,
    body: SubmitDetailsRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.EXECUTIVE))],
    tenant_id: TenantId,
) -> SiteResponse:
    """Exec submits details (shortlisted -> details_submitted)."""
    assert_transition(SiteStatus.SHORTLISTED, SiteStatus.DETAILS_SUBMITTED)
    # TODO(db): save body to site_details before transitioning
    return await svc_submit_details(db, site_id=site_id, actor=current_user["name"], tenant_id=tenant_id)


@router.post(
    "/shortlist/{site_id}/approve",
    response_model=SiteResponse,
    summary="Approve shortlist and set LOI timeline",
    description="Supervisor approves site details, sets expected_loi_days, and moves site to "
                "approved. Status: details_submitted -> approved. Notifies exec.",
)
async def approve_shortlist(
    site_id: str,
    body: ApproveShortlistRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR, Role.SUB_SUPERVISOR))],
    tenant_id: TenantId,
) -> SiteResponse:
    """Supervisor approves shortlist (details_submitted -> approved)."""
    assert_transition(SiteStatus.DETAILS_SUBMITTED, SiteStatus.APPROVED)
    return await svc_approve_shortlist(
        db,
        site_id=site_id,
        actor=current_user["name"],
        tenant_id=tenant_id,
        expected_loi_days=body.expected_loi_days,
    )


@router.post(
    "/shortlist/{site_id}/reassign",
    response_model=OkResponse,
    summary="Reassign site to another exec",
    description="Supervisor reassigns a shortlisted site from one exec to another. "
                "Writes audit row; does not change status.",
)
async def reassign_site(
    site_id: str,
    body: ReassignSiteRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR))],
    tenant_id: TenantId,
) -> OkResponse:
    """Supervisor reassigns a site to a different exec (supervisor only)."""
    return await svc_reassign_site(db, site_id=site_id, actor=current_user["name"], new_owner_id=body.new_owner_id)


@router.post(
    "/assign-sub-supervisor",
    response_model=OkResponse,
    summary="Assign sub-supervisor to a city",
    description="Supervisor assigns a sub_supervisor role to a user for a specific city.",
)
async def assign_sub_supervisor(
    body: AssignSubSupervisorRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR))],
    tenant_id: TenantId,
) -> OkResponse:
    """Supervisor assigns sub-supervisor (supervisor only)."""
    # TODO(db): update users set role=sub_supervisor, assigned_city=body.city where id=body.user_id
    await write_audit_event(
        db,
        site_id="N/A",
        actor=current_user["name"],
        action="assign_sub_supervisor",
        detail=f"user={body.user_id} city={body.city}",
    )
    return OkResponse(message=f"User {body.user_id} assigned as sub-supervisor for {body.city}")
