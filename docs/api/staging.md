# Staging

Router file: `backend/app/routers/staging.py`  
Prefix: `/api/staging`  
Tag: `Staging`

Routes sorted by path, then method.

---

### `GET /api/staging/exec`

**Handler**: `app.routers.staging:list_exec_staging`  
**Role required**: `executive`  
**Scope**: `own`  
**Touches**: reads → `[sites]`, writes → `[]`  
**Side effects**: none

Returns all sites with status `approved` (and beyond) for the currently authenticated executive, regardless of whether an LOI has been uploaded.

**Response** — `SiteListResponse` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `items` | `SiteResponse[]` | see SiteResponse shape in `bd.md` |
| `total` | `int` | — |

**TODO markers** (`backend/app/routers/staging.py`)

- Line 34: `# TODO(db): SELECT * FROM sites WHERE status=approved AND created_by=current_user.sub AND tenant_id=tenant_id`

**Frontend caller**: `frontend/src/services/api/staging.js::listExecStaging` (has `TODO(db)` stub — throws `Error('listExecStaging: not yet implemented')`).

**Example**

```bash
curl http://localhost:8000/api/staging/exec \
  -H "Authorization: Bearer <token>"
```

---

### `GET /api/staging/supervisor`

**Handler**: `app.routers.staging:list_supervisor_staging`  
**Role required**: `supervisor` | `sub_supervisor`  
**Scope**: `tenant` (supervisor) | `city` (sub_supervisor)  
**Touches**: reads → `[sites]`, writes → `[]`  
**Side effects**: none

Returns only sites with status `loi_uploaded`. Sub-supervisor results are additionally filtered to their assigned city.

**Response** — `SiteListResponse` (HTTP `200`)

See `SiteListResponse` / `SiteResponse` shape in `bd.md`.

**Errors**

- `403` — caller role not allowed

**TODO markers** (`backend/app/routers/staging.py`)

- Line 51: `# TODO(db): SELECT * FROM sites WHERE status=loi_uploaded AND tenant_id=tenant_id`
- Line 52: `# TODO(db): if sub_supervisor, add AND city=current_user.city`

**Frontend caller**: `frontend/src/services/api/staging.js::listSupervisorStaging` (has `TODO(db)` stub — throws `Error('listSupervisorStaging: not yet implemented')`).

**Example**

```bash
curl http://localhost:8000/api/staging/supervisor \
  -H "Authorization: Bearer <token>"
```

---

### `POST /api/staging/{site_id}/push`

**Handler**: `app.routers.staging:push_to_payments`  
**Role required**: `supervisor` | `sub_supervisor`  
**Scope**: `tenant` | `city`  
**Touches**: reads → `[sites]`, writes → `[sites]`  
**State transition**: `loi_uploaded` → `pushed_to_payments`  
**Writes audit row**: yes  
**Notifies**: `executive` (site owner) and `finance-team` via `email`, `slack`, `in_app`  
**Side effects**:
- Calls `notification_service.send` (stdout stub — `TODO(mcp)`)
- Calls `assert_transition(LOI_UPLOADED, PUSHED_TO_PAYMENTS)` — raises `422` on invalid transition
- Payments module activation is a stub; `TODO(payments)` marker

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Response** — `OkResponse` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `ok` | `bool` | `true` |
| `message` | `str` | confirmation |

**Errors**

- `403` — caller role not allowed
- `422` — invalid state transition (e.g. site not in `loi_uploaded`)

**TODO markers** (`backend/app/routers/staging.py`)

- Line 73: `# TODO(db): update sites set status=pushed_to_payments where id=site_id`
- Line 74: `# TODO(payments): activate Payments module for this site`

**Frontend caller**: `frontend/src/services/api/staging.js::pushToPayments` (has `TODO(db)` stub — throws `Error('pushToPayments: not yet implemented')`). `siteService.js::pushToPayments` calls `adapter.patchSiteStatus` with `PUSHED_TO_PAYMENTS` — **adapter path mismatch**.

**Example**

```bash
curl -X POST http://localhost:8000/api/staging/site_q9m20i39/push \
  -H "Authorization: Bearer <token>"
```
