# Users

Router file: `backend/app/routers/users.py`  
Prefix: `/api/users`  
Tag: `Users`

Routes sorted by path, then method.

---

### `GET /api/users`

**Handler**: `app.routers.users:list_users`  
**Role required**: `supervisor`  
**Scope**: `tenant`  
**Touches**: reads → `[users]`, writes → `[]`  
**Side effects**: none

Returns all users in the current tenant.

**Response** — inline `dict` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `items` | `list` | user objects — shape TBD once DB is wired |
| `total` | `int` | — |

**Errors**

- `403` — caller role is not `supervisor`

**TODO markers** (`backend/app/routers/users.py`)

- Line 35: `# TODO(db): SELECT * FROM users WHERE tenant_id=tenant_id`

**Frontend caller**: `userService.js::listUsers` calls `adapter.listUsers` which in `httpAdapter.js` calls `GET /users`. Path resolves correctly given base URL.

**Example**

```bash
curl http://localhost:8000/api/users \
  -H "Authorization: Bearer <token>"
```

---

### `POST /api/users/{user_id}/assign-city`

**Handler**: `app.routers.users:assign_sub_supervisor_city`  
**Role required**: `supervisor`  
**Scope**: `tenant`  
**Touches**: reads → `[users]`, writes → `[users]`  
**State transition**: none  
**Writes audit row**: yes  
**Notifies**: none  
**Side effects**: none beyond audit

Sets the target user's role to `sub_supervisor` and assigns a city scope.

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `user_id` | `str` | ID of the user to update |

**Request body** — inline `dict`

No Pydantic model declared on the handler. Expected key:

| field | type | required | notes |
| ----- | ---- | -------- | ----- |
| `city` | `str` | yes | city to assign as the scope |

**Response** — `OkResponse` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `ok` | `bool` | `true` |
| `message` | `str` | confirmation string |

**Errors**

- `403` — caller role is not `supervisor`

**TODO markers** (`backend/app/routers/users.py`)

- Line 54: `# TODO(db): update users set role=sub_supervisor, assigned_city=city where id=user_id`

**Frontend caller**: no direct caller in `frontend/src/services/api/`. Not yet wired.

**Example**

```bash
curl -X POST http://localhost:8000/api/users/user_subsup/assign-city \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"city": "Bengaluru"}'
```

---

### `GET /api/users/me`

**Handler**: `app.routers.users:get_me`  
**Role required**: `executive` | `supervisor` | `sub_supervisor`  
**Scope**: `own`  
**Touches**: reads → `[]`, writes → `[]`  
**Side effects**: none

Derived entirely from JWT claims. No database query. The response IS the decoded token payload; the stub returns a hardcoded dict until `TODO(auth)` is resolved.

**Response** — inline `dict` (HTTP `200`)

Shape matches the hardcoded mock user in `app/core/deps.py` and `app/core/security.py`:

| field | type | notes |
| ----- | ---- | ----- |
| `sub` | `str` | user ID |
| `name` | `str` | display name |
| `role` | `str` | `executive`, `supervisor`, or `sub_supervisor` |
| `tenant_id` | `str` | — |
| `city` | `str` | city scope (relevant for `sub_supervisor`) |

The frontend `authService.js` session shape adds `email`, `cityScope`, and `token`. These are not yet returned by the backend. Alignment required — see `CONNECTING_BACKEND.md` Section D.

**Frontend caller**: `userService.js::me` calls `adapter.me` which in `httpAdapter.js` calls `GET /users/me`. Path resolves correctly.

**Example**

```bash
curl http://localhost:8000/api/users/me \
  -H "Authorization: Bearer <token>"
```
