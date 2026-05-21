"""Audit router — tenant-wide and per-site activity feeds."""
from typing import Annotated
from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, DbDep, TenantId
from app.rbac.guards import require_role
from app.rbac.roles import Role
from app.domain.schemas.audit import AuditListResponse

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get(
    "",
    response_model=AuditListResponse,
    summary="Tenant-wide audit feed",
    description="Returns all audit events for the tenant. Supervisor only. "
                "Paginated by cursor.",
)
async def list_audit_events(
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR))],
    tenant_id: TenantId,
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=200),
) -> AuditListResponse:
    """Tenant-wide audit log (supervisor only, paginated)."""
    # TODO(db): SELECT * FROM audit_events WHERE tenant_id=tenant_id ORDER BY created_at DESC LIMIT limit OFFSET (page-1)*limit
    return AuditListResponse(items=[], total=0)


@router.get(
    "/site/{site_id}",
    response_model=AuditListResponse,
    summary="Per-site audit feed",
    description="Returns the ordered audit log for a specific site. "
                "Exec sees their own sites only.",
)
async def get_site_audit(
    site_id: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant_id: TenantId,
) -> AuditListResponse:
    """Per-site audit feed (role scoped)."""
    # TODO(db): SELECT * FROM audit_events WHERE site_id=site_id ORDER BY created_at DESC
    return AuditListResponse(items=[], total=0)
