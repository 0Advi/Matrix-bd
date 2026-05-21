"""Tenancy router — tenants and cities."""
from typing import Annotated
from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, DbDep, TenantId
from app.rbac.guards import require_role
from app.rbac.roles import Role

router = APIRouter(prefix="/tenancy", tags=["Tenancy"])


@router.get(
    "/tenants",
    summary="List tenants (supervisor only)",
    description="Returns all tenants the current supervisor can manage.",
)
async def list_tenants(
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR))],
) -> dict:
    """List tenants (supervisor only)."""
    # TODO(db): SELECT * FROM tenants WHERE id IN (supervisor's accessible tenants)
    return {"items": [], "total": 0}


@router.get(
    "/cities",
    summary="List cities within tenant",
    description="Returns all cities that have active sites in the current tenant.",
)
async def list_cities(
    db: DbDep,
    current_user: CurrentUser,
    tenant_id: TenantId,
) -> dict:
    """List cities scoped to tenant."""
    # TODO(db): SELECT DISTINCT city FROM sites WHERE tenant_id=tenant_id
    return {"cities": ["Mumbai", "Bengaluru", "New Delhi", "Hyderabad", "Pune", "Chennai", "Ahmedabad"]}
