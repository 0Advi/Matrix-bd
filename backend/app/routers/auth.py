"""Auth router.

POST /auth/login  — body {email, password} — returns session matching mockAuth.js shape.
POST /auth/logout — returns {ok: true}.

# TODO(auth): teammate replaces stub login with real JWT issuance (sign HS256/RS256,
#             set expiry, validate against users table). decode_token in security.py
#             is the companion stub.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.domain.schemas.common import OkResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

# Mock user store — mirrors frontend/src/services/api/mock/mockUsers.js exactly.
# TODO(auth): replace with real DB lookup.
_MOCK_USERS = [
    {"id": "user_riya",   "name": "Riya Sharma",    "email": "riya.sharma@bluetokai.com",    "role": "executive",      "city": "Mumbai",    "tenantId": "bt-tenant-001"},
    {"id": "user_aman",   "name": "Aman Verma",     "email": "aman.verma@bluetokai.com",     "role": "executive",      "city": "New Delhi", "tenantId": "bt-tenant-001"},
    {"id": "user_nikhil", "name": "Nikhil Iyer",    "email": "nikhil.iyer@bluetokai.com",    "role": "executive",      "city": "Pune",      "tenantId": "bt-tenant-001"},
    {"id": "user_aisha",  "name": "Aisha Sengupta", "email": "aisha.sengupta@bluetokai.com", "role": "executive",      "city": "Bengaluru", "tenantId": "bt-tenant-001"},
    {"id": "user_sup1",   "name": "Nisha Kapoor",   "email": "nisha.kapoor@bluetokai.com",   "role": "supervisor",     "city": "Mumbai",    "tenantId": "bt-tenant-001"},
    {"id": "user_subsup", "name": "Dev Malhotra",   "email": "dev.malhotra@bluetokai.com",   "role": "sub_supervisor", "city": "Mumbai",    "tenantId": "bt-tenant-001"},
]


# ── Schemas ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class SessionResponse(BaseModel):
    """Matches the shape returned by mockAuth.mockLogin and expected by the frontend."""
    id: str
    name: str
    email: str
    role: str
    cityScope: str
    permissions: list[str]
    tenantId: str
    token: str


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=SessionResponse,
    summary="Log in and obtain a session token",
    description="Accepts email + password. Any non-empty credentials against a known "
                "mock user succeed in this pass. Teammate replaces with real JWT issuance.",
)
async def login(body: LoginRequest) -> SessionResponse:
    """Stub login — any known email + non-empty password succeeds.

    # TODO(auth): validate password hash, sign real JWT, set expiry.
    """
    user = next((u for u in _MOCK_USERS if u["email"] == body.email), None)
    if not user or not body.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    # TODO(auth): sign a real JWT here; for now return a stub token.
    return SessionResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        role=user["role"],
        cityScope=user["city"],
        permissions=[],
        tenantId=user["tenantId"],
        token="stub.jwt.token",  # TODO(auth): replace with signed JWT
    )


@router.post(
    "/logout",
    response_model=OkResponse,
    summary="Invalidate the current session",
    description="Clears the server-side session. Client should discard the token on its end.",
)
async def logout() -> OkResponse:
    """Stub logout — no server state to clear until real sessions are wired.

    # TODO(auth): invalidate token in a deny-list or revoke refresh token.
    """
    return OkResponse(ok=True, message="Logged out")
