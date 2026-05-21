# Audit

Router file: `backend/app/routers/audit.py`  
Prefix: `/api/audit`  
Tag: `Audit`

Routes sorted by path, then method.

---

### `GET /api/audit`

**Handler**: `app.routers.audit:list_audit_events`  
**Role required**: `supervisor`  
**Scope**: `tenant`  
**Touches**: reads → `[audit_events]`, writes → `[]`  
**Side effects**: none

Tenant-wide audit feed. Returns all audit events for the tenant, newest first, paginated.

**Query params**

| name | type | required | default | notes |
| ---- | ---- | -------- | ------- | ----- |
| `page` | `int` | no | `1` | minimum 1 |
| `limit` | `int` | no | `50` | maximum 200 |

**Response** — `AuditListResponse` (HTTP `200`) (`backend/app/domain/schemas/audit.py:19`)

| field | type | notes |
| ----- | ---- | ----- |
| `items` | `AuditEvent[]` | ordered by `created_at DESC` |
| `total` | `int` | total events in tenant |

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

**Errors**

- `403` — caller role is not `supervisor`

**TODO markers** (`backend/app/routers/audit.py`)

- Line 28: `# TODO(db): SELECT * FROM audit_events WHERE tenant_id=tenant_id ORDER BY created_at DESC LIMIT limit OFFSET (page-1)*limit`

**Frontend caller**: `frontend/src/services/api/audit.js::listAuditEvents` (has `TODO(db)` stub — throws `Error('listAuditEvents: not yet implemented')`).

**Example**

```bash
curl "http://localhost:8000/api/audit?page=1&limit=50" \
  -H "Authorization: Bearer <token>"
```

---

### `GET /api/audit/site/{site_id}`

**Handler**: `app.routers.audit:get_site_audit`  
**Role required**: `executive` | `supervisor` | `sub_supervisor`  
**Scope**: `own` (executive) | `city` (sub_supervisor) | `tenant` (supervisor)  
**Touches**: reads → `[audit_events]`, writes → `[]`  
**Side effects**: none

Per-site audit feed ordered by `created_at DESC`. Exec can only access their own sites.

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Response** — `AuditListResponse` (HTTP `200`)

See `AuditListResponse` / `AuditEvent` shape above.

**Errors**

- `403` — exec requesting audit for a site they don't own (scope enforcement `TODO(auth)`)

**TODO markers** (`backend/app/routers/audit.py`)

- Line 46: `# TODO(db): SELECT * FROM audit_events WHERE site_id=site_id ORDER BY created_at DESC`

**Frontend caller**: `frontend/src/services/api/audit.js::getSiteAudit` (has `TODO(db)` stub — throws `Error('getSiteAudit: not yet implemented')`).

**Example**

```bash
curl http://localhost:8000/api/audit/site/site_a8f3c129 \
  -H "Authorization: Bearer <token>"
```
