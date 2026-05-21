"""Users router — current user info and user management."""
from typing import Annotated
from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, DbDep, TenantId
from app.rbac.guards import require_role
from app.rbac.roles import Role
from app.domain.schemas.common import OkResponse
from app.services.audit_service import write_audit_event

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    summary="Get current user",
    description="Returns the current user's profile, role, and tenant information.",
)
async def get_me(current_user: CurrentUser) -> dict:
    """Current user + role + tenant (no DB needed — from JWT claims)."""
    return current_user


@router.get(
    "",
    summary="List users in tenant",
    description="Returns all users in the current tenant. Supervisor only.",
)
async def list_users(
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR))],
    tenant_id: TenantId,
) -> dict:
    """List users in tenant (supervisor only)."""
    # TODO(db): SELECT * FROM users WHERE tenant_id=tenant_id
    return {"items": [], "total": 0}


@router.post(
    "/{user_id}/assign-city",
    response_model=OkResponse,
    summary="Assign sub-supervisor city scope",
    description="Supervisor assigns a city to a sub-supervisor, scoping their visibility.",
)
async def assign_sub_supervisor_city(
    user_id: str,
    body: dict,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SUPERVISOR))],
    tenant_id: TenantId,
) -> OkResponse:
    """Assign city scope to sub-supervisor (supervisor only)."""
    city = body.get("city")
    # TODO(db): update users set role=sub_supervisor, assigned_city=city where id=user_id
    await write_audit_event(
        db,
        site_id="N/A",
        actor=current_user["name"],
        action="assign_sub_supervisor_city",
        detail=f"user={user_id} city={city}",
    )
    return OkResponse(message=f"User {user_id} assigned to city {city}")
