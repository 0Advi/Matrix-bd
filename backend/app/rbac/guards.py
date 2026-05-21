"""Role and scope guards for FastAPI routes."""
from typing import Callable
from fastapi import Depends, HTTPException, status
from app.core.deps import get_current_user
from app.rbac.roles import Role


def require_role(*roles: Role) -> Callable:
    """Dependency factory: raises 403 if the current user's role is not in *roles*.

    Usage::

        @router.post("/bd/drafts")
        async def create_draft(
            _: Annotated[None, Depends(require_role(Role.EXECUTIVE))],
            ...
        ):
            ...
    """
    async def guard(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        if user_role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' not allowed. Required: {[r.value for r in roles]}",
            )
        return current_user

    return guard


def require_scope(kind: str) -> Callable:
    """Dependency factory: validates scope access.

    TODO(auth): implement real scope checks from JWT claims.
    Currently a pass-through.
    """
    async def guard(current_user: dict = Depends(get_current_user)) -> dict:
        # TODO(auth): enforce scope from session claims
        return current_user

    return guard
