"""FastAPI dependencies: get_db, get_current_user, get_tenant."""
from typing import Annotated, Optional
from fastapi import Depends, Header, HTTPException, status
from app.db.session import get_db
from app.core.security import decode_token


# Re-export get_db so routers import from a single place
DbDep = Annotated[None, Depends(get_db)]


async def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
) -> dict:
    """Stub: extract user from Bearer token.

    TODO(auth): validate real JWT.  For now returns mock user so routes
    can be developed without an identity service running.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        return decode_token(token)
    # Default mock user for local dev without auth header
    return {
        "sub": "user-riya-sharma-001",
        "name": "Riya Sharma",
        "role": "executive",
        "tenant_id": "bt-tenant-001",
        "city": "Mumbai",
    }


CurrentUser = Annotated[dict, Depends(get_current_user)]


async def get_tenant(current_user: CurrentUser) -> str:
    """Extract tenant_id from the current user's claims."""
    return current_user["tenant_id"]


TenantId = Annotated[str, Depends(get_tenant)]
