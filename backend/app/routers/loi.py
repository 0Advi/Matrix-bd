"""LOI (Letter of Intent) router.

Covers LOI upload by exec, LOI view, and timeline setting by supervisor.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, status

from app.core.deps import CurrentUser, DbDep, TenantId
from app.rbac.guards import require_role
from app.rbac.roles import Role
from app.domain.state_machine import SiteStatus, assert_transition
from app.domain.schemas.loi import SetLOITimelineRequest, LOIUploadResponse, LOIViewResponse
from app.domain.schemas.common import OkResponse
from app.services.loi_service import svc_upload_loi
from app.services.audit_service import write_audit_event
from app.services.notification_service import send as notify

router = APIRouter(prefix="/loi", tags=["LOI"])


@router.post(
    "/{site_id}/upload",
    response_model=LOIUploadResponse,
    summary="Upload signed LOI",
    description="BD exec uploads the signed LOI document. "
                "Status transitions: approved -> loi_uploaded. Notifies supervisor.",
)
async def upload_loi(
    site_id: str,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.EXECUTIVE))],
    tenant_id: TenantId,
) -> LOIUploadResponse:
    """Exec uploads LOI (approved -> loi_uploaded).

    NOTE: This route accepts no file yet; multipart is handled via POST /sites/{id}/loi.
    TODO(storage): add UploadFile param once storage is wired.
    """
    assert_transition(SiteStatus.APPROVED, SiteStatus.LOI_UPLOADED)
    return await svc_upload_loi(db, site_id=site_id, actor=current_user["name"])


@router.get(
    "/{site_id}",
    response_model=LOIViewResponse,
    summary="View LOI document",
    description="Returns a (stub) signed URL to the LOI document. "
                "Exec can only view LOIs for their own sites; supervisor sees all.",
)
async def view_loi(
    site_id: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant_id: TenantId,
) -> LOIViewResponse:
    """View LOI (exec: own sites; supervisor: all)."""
    # TODO(db): fetch site, check ownership if exec, return document URL
    # TODO(storage): generate signed URL for the stored document
    return LOIViewResponse(
        site_id=site_id,
        file_url=None,  # TODO(storage): real signed URL
        uploaded_at=None,
        uploaded_by=None,
    )


@router.post(
    "/{site_id}/set-timeline",
    response_model=OkResponse,
    summary="Set expected LOI timeline",
    description="Supervisor sets or updates the expected number of days for LOI upload. "
                "Writes audit row.",
)
async def set_loi_timeline(
    site_id: str,
    body: SetLOITimelineRequest,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR, Role.SUB_SUPERVISOR))],
    tenant_id: TenantId,
) -> OkResponse:
    """Supervisor sets LOI timeline (no status change, audit only)."""
    # TODO(db): update sites set expected_loi_days=body.expected_loi_days where id=site_id
    await write_audit_event(
        db,
        site_id=site_id,
        actor=current_user["name"],
        action="set_loi_timeline",
        detail=f"expected_loi_days={body.expected_loi_days}",
    )
    return OkResponse(message=f"LOI timeline set to {body.expected_loi_days} days for site {site_id}")
