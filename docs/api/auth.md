# Auth

Router file: `backend/app/routers/auth.py`  
Prefix: `/api/auth`  
Tag: `Auth`

Routes sorted by path, then method.

---

### `POST /api/auth/login`

**Handler**: `app.routers.auth:login`  
**Role required**: `public` (no auth header required)  
**Touches**: reads → `[]`, writes → `[]`  
**Side effects**: none

> **DB note**: credential lookup is currently performed against an in-memory mock user list (`_MOCK_USERS` in `auth.py`). No DB query is issued in this pass. `TODO(auth)`: replace with `SELECT * FROM users WHERE email = :email` and validate `hashed_password` via `passlib`.

**Request body** — `LoginRequest`

| field | type | required | constraints |
| ----- | ---- | -------- | ----------- |
| `email` | `str` | yes | must match a known mock user email |
| `password` | `str` | yes | any non-empty value accepted in stub |

**Response** — `SessionResponse` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `id` | `str` | user ID, e.g. `"user_riya"` |
| `name` | `str` | display name |
| `email` | `str` | — |
| `role` | `str` | `executive` \| `supervisor` \| `sub_supervisor` |
| `cityScope` | `str` | city name assigned to this user |
| `permissions` | `list[str]` | stub returns `[]`; will carry fine-grained permissions post-auth wiring |
| `tenantId` | `str` | tenant ID, e.g. `"bt-tenant-001"` |
| `token` | `str` | stub returns `"stub.jwt.token"`; `TODO(auth)`: replace with signed HS256/RS256 JWT |

**Errors**

- `401` — email not found in user list, or `password` is empty

**TODO markers** (`backend/app/routers/auth.py`)

- Line 62: `# TODO(auth): validate password hash, sign real JWT, set expiry.`
- Line 69: `# TODO(auth): sign a real JWT here; for now return a stub token.`
- Line 78: `token="stub.jwt.token"  # TODO(auth): replace with signed JWT`

**Frontend caller**: `httpAdapter.js::login` calls `POST /auth/login`. Path resolves to `POST /api/auth/login` via the `settings.api_prefix` mount.

**Example**

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "riya.sharma@bluetokai.com", "password": "any-non-empty-value"}'
```

---

### `POST /api/auth/logout`

**Handler**: `app.routers.auth:logout`  
**Role required**: `public` (no auth header enforced in this stub)  
**Touches**: reads → `[]`, writes → `[]`  
**Side effects**: none

> **DB note**: no server-side session state is cleared. The stub is stateless — logout is currently a no-op on the backend. `TODO(auth)`: maintain a token deny-list (Redis or a `revoked_tokens` DB table) and add the presented token to it on logout.

**Response** — `OkResponse` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `ok` | `bool` | always `true` |
| `message` | `str` | `"Logged out"` |

**Errors**

None defined in this stub. After real session wiring, a `401` should be returned for an already-expired or absent token.

**TODO markers** (`backend/app/routers/auth.py`)

- Line 89: `# TODO(auth): invalidate token in a deny-list or revoke refresh token.`

**Frontend caller**: `httpAdapter.js::logout` calls `POST /auth/logout`.

**Example**

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <token>"
```
