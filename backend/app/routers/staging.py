"""Staging router.

Exec staging: all approved sites for this exec.
Supervisor staging: only loi_uploaded sites.
push_to_payments: supervisor activates Payments module (stub).
"""
from typing import Annotated
from fastapi import APIRouter, Depends, status

from app.core.deps import CurrentUser, DbDep, TenantId
from app.rbac.guards import require_role
from app.rbac.roles import Role
from app.domain.state_machine import SiteStatus, assert_transition
from app.domain.schemas.site import SiteListResponse, SiteResponse
from app.domain.schemas.common import OkResponse
from app.services.bd_service import svc_push_to_payments
from app.services.audit_service import write_audit_event
from app.services.notification_service import send as notify

router = APIRouter(prefix="/staging", tags=["Staging"])


@router.get(
    "/exec",
    response_model=SiteListResponse,
    summary="List exec staging sites",
    description="Returns all approved sites for the current exec, regardless of LOI upload state.",
)
async def list_exec_staging(
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.EXECUTIVE))],
    tenant_id: TenantId,
) -> SiteListResponse:
    """Exec: all approved sites for current user (own scope)."""
    # TODO(db): SELECT * FROM sites WHERE status=approved AND created_by=current_user.sub AND tenant_id=tenant_id
    return SiteListResponse(items=[], total=0)


@router.get(
    "/supervisor",
    response_model=SiteListResponse,
    summary="List supervisor staging sites",
    description="Returns only sites where LOI has been uploaded "
                "(status=loi_uploaded). Supervisor sees all; sub-supervisor sees city scope.",
)
async def list_supervisor_staging(
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR, Role.SUB_SUPERVISOR))],
    tenant_id: TenantId,
) -> SiteListResponse:
    """Supervisor: loi_uploaded sites, tenant (or city) scoped."""
    # TODO(db): SELECT * FROM sites WHERE status=loi_uploaded AND tenant_id=tenant_id
    # TODO(db): if sub_supervisor, add AND city=current_user.city
    return SiteListResponse(items=[], total=0)


@router.post(
    "/{site_id}/push",
    response_model=OkResponse,
    status_code=status.HTTP_200_OK,
    summary="Push site to Payments module (stub)",
    description="Supervisor pushes a site from staging to the Payments module. "
                "Status: loi_uploaded -> pushed_to_payments. "
                "This is a stub route — Payments module activation is out of scope.",
)
async def push_to_payments(
    site_id: str,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR, Role.SUB_SUPERVISOR))],
    tenant_id: TenantId,
) -> OkResponse:
    """Supervisor pushes site to Payments module (loi_uploaded -> pushed_to_payments)."""
    assert_transition(SiteStatus.LOI_UPLOADED, SiteStatus.PUSHED_TO_PAYMENTS)
    return await svc_push_to_payments(db, site_id=site_id, actor=current_user["name"])
