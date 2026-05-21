# Notifications

Router file: `backend/app/routers/notifications.py`  
Prefix: `/api/notifications`  
Tag: `Notifications`

Routes sorted by path, then method.

---

### `GET /api/notifications`

**Handler**: `app.routers.notifications:list_notifications`  
**Role required**: `executive` | `supervisor` | `sub_supervisor`  
**Scope**: `own` (current user's inbox only)  
**Touches**: reads → `[notifications]`, writes → `[]`  
**Side effects**: none

Returns the in-app notification feed for the currently authenticated user.

**Response** — inline `dict` (HTTP `200`)

No `response_model` declared on the handler. Returns:

| field | type | notes |
| ----- | ---- | ----- |
| `items` | `list` | notification objects — shape TBD once DB is wired |
| `total` | `int` | — |

**TODO markers** (`backend/app/routers/notifications.py`)

- Line 24: `# TODO(db): SELECT * FROM notifications WHERE recipient_id=current_user.sub ORDER BY created_at DESC`

**Frontend caller**: `frontend/src/services/api/notifications.js::listNotifications` (has `TODO(db)` stub — throws `Error('listNotifications: not yet implemented')`).

**Example**

```bash
curl http://localhost:8000/api/notifications \
  -H "Authorization: Bearer <token>"
```

---

### `POST /api/notifications/send`

**Handler**: `app.routers.notifications:send_notification`  
**Role required**: `system`  
**Scope**: `tenant`  
**Touches**: reads → `[]`, writes → `[notifications]`  
**Side effects**:
- Calls `notification_service.send` (currently prints to stdout — `TODO(mcp)`)

Internal system endpoint. Not intended for direct client use. Called by other domain services to trigger multi-channel notifications.

**Request body** — inline `dict`

No Pydantic model declared; the handler reads keys from the raw `payload: dict` argument:

| field | type | required | notes |
| ----- | ---- | -------- | ----- |
| `event` | `str` | yes | machine-readable event name e.g. `"draft_submitted"` |
| `recipient_ids` | `str[]` | yes | list of user IDs to notify |
| `channels` | `str[]` | yes | `"email"`, `"slack"`, `"in_app"` |
| `payload` | `dict` | no | arbitrary data for notification template |

**Response** — `OkResponse` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `ok` | `bool` | `true` |
| `message` | `str` | `"Notification queued (stub)"` |

**Errors**

- `403` — caller role is not `system`

**TODO markers** (`backend/app/routers/notifications.py`)

- Line 34 (docstring): `TODO(mcp): teammate plugs real email/Slack via MCP here`

**Frontend caller**: `frontend/src/services/api/notifications.js::sendNotification` (has `TODO(db)` stub — logs a warning, does not yet call this endpoint).

**Example**

```bash
curl -X POST http://localhost:8000/api/notifications/send \
  -H "Authorization: Bearer <system-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "draft_submitted",
    "recipient_ids": ["user_sup1"],
    "channels": ["email", "in_app"],
    "payload": {"site_id": "site_h9d31a40", "site_name": "BKC One East Wing"}
  }'
```
