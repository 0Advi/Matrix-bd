"""Notifications router — stub in-app feed and send endpoint."""
from typing import Annotated
from fastapi import APIRouter, Depends

from app.core.deps import CurrentUser, DbDep
from app.rbac.guards import require_role
from app.rbac.roles import Role
from app.services.notification_service import send as notify_send
from app.domain.schemas.common import OkResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    summary="List in-app notifications",
    description="Returns in-app notifications for the current user.",
)
async def list_notifications(
    db: DbDep,
    current_user: CurrentUser,
) -> dict:
    """In-app notification feed for current user."""
    # TODO(db): SELECT * FROM notifications WHERE recipient_id=current_user.sub ORDER BY created_at DESC
    return {"items": [], "total": 0}


@router.post(
    "/send",
    response_model=OkResponse,
    summary="Send a notification (system use)",
    description="Internal endpoint to trigger a notification. "
                "Called by other services; not intended for direct client use. "
                "TODO(mcp): teammate plugs real email/Slack via MCP here.",
)
async def send_notification(
    payload: dict,
    db: DbDep,
    current_user: Annotated[dict, Depends(require_role(Role.SYSTEM))],
) -> OkResponse:
    """System: send notification (stub)."""
    await notify_send(
        event=payload.get("event", "unknown"),
        recipient_ids=payload.get("recipient_ids", []),
        channels=payload.get("channels", ["in_app"]),
        payload=payload,
    )
    return OkResponse(message="Notification queued (stub)")
