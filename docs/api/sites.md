# Sites

Router file: `backend/app/routers/sites.py`  
Prefix: `/api/sites`  
Tag: `Sites`

This router handles read-only site access — overview list, single-site lookup, and per-site tab data (activity, documents). All mutating operations (transitions, details, LOI) live in domain-specific routers (`bd`, `loi`, `staging`).

Routes sorted by path, then method.

---

### `GET /api/sites`

**Handler**: `app.routers.sites:list_sites`  
**Role required**: `executive` | `supervisor` | `sub_supervisor`  
**Scope**: `own` (executive) | `city` (sub_supervisor) | `tenant` (supervisor)  
**Touches**: reads → `[sites]`, writes → `[]`  
**Side effects**: none

**Query params**

| name | type | required | default | notes |
| ---- | ---- | -------- | ------- | ----- |
| `status` | `str` | no | — | filter by `SiteStatus` snake_case value |
| `city` | `str` | no | — | filter by city name |

**Response** — `SiteListResponse` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `items` | `SiteResponse[]` | see SiteResponse shape in `bd.md` |
| `total` | `int` | — |

**TODO markers** (`backend/app/routers/sites.py`)

- Line 26: `# TODO(db): SELECT * FROM sites WHERE tenant_id=tenant_id [AND status=status] [AND city=city]`
- Line 27: `# TODO(db): if exec, add AND created_by=current_user.sub`

**Frontend caller**: `siteService.js::listSites` calls `adapter.listSites` which in `httpAdapter.js` calls `GET /sites` — **path should be `/api/sites`** (base URL already `http://localhost:8000`, path resolves correctly). Also `frontend/src/services/api/sites.js::listSites` has a `TODO(db)` stub.

**Example**

```bash
curl "http://localhost:8000/api/sites?status=draft_submitted&city=Mumbai" \
  -H "Authorization: Bearer <token>"
```

---

### `GET /api/sites/{site_id}`

**Handler**: `app.routers.sites:get_site`  
**Role required**: `executive` | `supervisor` | `sub_supervisor`  
**Scope**: `own` (executive) | `city` (sub_supervisor) | `tenant` (supervisor)  
**Touches**: reads → `[sites, site_details]`, writes → `[]`  
**Side effects**: none

Currently raises `HTTP 404` unconditionally (stub) until DB is wired.

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Response** — `SiteResponse` (HTTP `200`)

See `SiteResponse` shape in `bd.md`.

**Errors**

- `404` — site not found (currently always raised — stub)
- `403` — exec requesting a site they don't own (scope enforcement `TODO(auth)`)

**TODO markers** (`backend/app/routers/sites.py`)

- Line 44: `# TODO(db): SELECT * FROM sites WHERE id=site_id AND tenant_id=tenant_id`

**Frontend caller**: `siteService.js::getSite` calls `adapter.getSite` which in `httpAdapter.js` calls `GET /sites/:id`. Also `frontend/src/services/api/sites.js::getSite` has a `TODO(db)` stub.

**Example**

```bash
curl http://localhost:8000/api/sites/site_a8f3c129 \
  -H "Authorization: Bearer <token>"
```

---

### `GET /api/sites/{site_id}/activity`

**Handler**: `app.routers.sites:get_site_activity`  
**Role required**: `executive` | `supervisor` | `sub_supervisor`  
**Scope**: `own` (executive) | `city` (sub_supervisor) | `tenant` (supervisor)  
**Touches**: reads → `[audit_events]`, writes → `[]`  
**Side effects**: none

Returns the ordered audit feed for a single site. Used by the Activity drawer tab.

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Response** — `AuditListResponse` (HTTP `200`) (`backend/app/domain/schemas/audit.py:19`)

| field | type | notes |
| ----- | ---- | ----- |
| `items` | `AuditEvent[]` | ordered by `created_at DESC` |
| `total` | `int` | — |

**AuditEvent shape** (`backend/app/domain/schemas/audit.py:8`)

| field | type | notes |
| ----- | ---- | ----- |
| `id` | `str` | UUID |
| `site_id` | `str` | — |
| `actor` | `str` | user name |
| `action` | `str` | machine-readable action key |
| `from_status` | `str \| null` | snake_case status or `null` |
| `to_status` | `str \| null` | snake_case status or `null` |
| `detail` | `str \| null` | freeform detail string |
| `created_at` | `datetime` | ISO-8601 UTC |

**TODO markers** (`backend/app/routers/sites.py`)

- Line 62: `# TODO(db): SELECT * FROM audit_events WHERE site_id=site_id ORDER BY created_at DESC`

**Frontend caller**: `frontend/src/services/api/audit.js::getSiteAudit` (has `TODO(db)` stub — throws `Error('getSiteAudit: not yet implemented')`).

**Example**

```bash
curl http://localhost:8000/api/sites/site_a8f3c129/activity \
  -H "Authorization: Bearer <token>"
```

---

### `GET /api/sites/{site_id}/documents`

**Handler**: `app.routers.sites:get_site_documents`  
**Role required**: `executive` | `supervisor` | `sub_supervisor`  
**Scope**: `own` (executive) | `city` (sub_supervisor) | `tenant` (supervisor)  
**Touches**: reads → `[site_documents]`, writes → `[]`  
**Side effects**: signed URL generation is `TODO(storage)`

Returns the list of documents attached to a site. Used by the Documents drawer tab.

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Response** — inline `dict` (HTTP `200`)

No `response_model` declared. The handler returns:

| field | type | notes |
| ----- | ---- | ----- |
| `site_id` | `str` | — |
| `documents` | `list` | empty stub; shape TBD once storage is wired |

**Errors**

- `403` — exec requesting documents for a site they don't own (scope enforcement `TODO(auth)`)

**TODO markers** (`backend/app/routers/sites.py`)

- Line 78: `# TODO(db): SELECT * FROM site_documents WHERE site_id=site_id`
- Line 79: `# TODO(storage): generate signed download URLs`

**Frontend caller**: no caller in `frontend/src/services/api/`. Not yet wired.

**Example**

```bash
curl http://localhost:8000/api/sites/site_q9m20i39/documents \
  -H "Authorization: Bearer <token>"
```
