"""Notification service stub.

Interface is defined here; a teammate plugs the MCP transport in.
Wire email + Slack via the MCP integration by implementing the
send() function body below.

TODO(mcp): teammate plugs MCP email + Slack here.
"""
from typing import Literal

NotificationChannel = Literal["email", "slack", "in_app"]


async def send(
    *,
    event: str,
    recipient_ids: list[str],
    channels: list[NotificationChannel] = ["in_app"],
    payload: dict | None = None,
) -> None:
    """Send a notification via one or more channels.

    Args:
        event: machine-readable event name, e.g. "draft_shortlisted".
        recipient_ids: list of user IDs to notify.
        channels: which channels to use.
        payload: arbitrary extra data for the notification template.

    TODO(mcp): implement real email/Slack dispatch via MCP integration.
    """
    print(
        f"[NOTIFICATION stub] event={event!r} recipients={recipient_ids} "
        f"channels={channels} payload={payload}"
    )
