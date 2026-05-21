# BD — Business Development

Router file: `backend/app/routers/bd.py`  
Prefix: `/api/bd`  
Tag: `BD`

Routes sorted by path, then method.

---

### `POST /api/bd/assign-sub-supervisor`

**Handler**: `app.routers.bd:assign_sub_supervisor`  
**Role required**: `supervisor`  
**Scope**: `tenant`  
**Touches**: reads → `[users]`, writes → `[users]`  
**Side effects**:
- Writes audit row via `audit_service.write_audit_event` (currently prints to stdout — `TODO(db)`)

**Request body** — `AssignSubSupervisorRequest` (`backend/app/domain/schemas/site.py:62`)

| field | type | required | constraints |
| ----- | ---- | -------- | ----------- |
| `user_id` | `str` | yes | — |
| `city` | `str` | yes | — |

**Response** — `OkResponse` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `ok` | `bool` | always `true` |
| `message` | `str` | confirmation string |

**Errors**

- `403` — caller role is not `supervisor`

**TODO markers** (`backend/app/routers/bd.py`)

- Line 352: `# TODO(db): update users set role=sub_supervisor, assigned_city=body.city where id=body.user_id`

**Frontend caller**: no caller in `frontend/src/services/api/`. Not yet wired.

**Example**

```bash
curl -X POST http://localhost:8000/api/bd/assign-sub-supervisor \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_subsup", "city": "Mumbai"}'
```

---

### `GET /api/bd/drafts`

**Handler**: `app.routers.bd:list_drafts`  
**Role required**: `executive` | `supervisor` | `sub_supervisor`  
**Scope**: `own` (executive) | `city` (sub_supervisor) | `tenant` (supervisor)  
**Touches**: reads → `[sites]`, writes → `[]`  
**Side effects**: none

**Query params**

No query params defined in the handler signature. Filtering is applied internally based on role scope.

**Response** — `SiteListResponse` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `items` | `SiteResponse[]` | see SiteResponse shape below |
| `total` | `int` | total matching count |

**SiteResponse shape** (`backend/app/domain/schemas/site.py:69`)

| field | type | notes |
| ----- | ---- | ----- |
| `id` | `str` | UUID |
| `code` | `str` | e.g. `BT-MUM-0144` |
| `name` | `str` | — |
| `city` | `str` | — |
| `tenant_id` | `str` | — |
| `status` | `SiteStatus` | snake_case enum value |
| `created_by` | `str` | user name |
| `visit_date` | `date \| null` | YYYY-MM-DD |
| `days` | `int \| null` | computed age |
| `stage` | `str \| null` | — |
| `details_completion` | `str \| null` | `partial` or `null` |

**TODO markers** (`backend/app/routers/bd.py`)

- Line 101: `# TODO(db): query sites where status=draft_submitted, scoped by role`

**Frontend caller**: `frontend/src/services/api/sites.js::listSites` (has its own `TODO(db)` stub; not yet calling this endpoint)

**Example**

```bash
curl http://localhost:8000/api/bd/drafts \
  -H "Authorization: Bearer <token>"
```

---

### `POST /api/bd/drafts`

**Handler**: `app.routers.bd:create_draft`  
**Role required**: `executive`  
**Scope**: `own`  
**Touches**: reads → `[]`, writes → `[sites]`  
**State transition**: `null` → `draft_submitted`  
**Writes audit row**: yes  
**Notifies**: `supervisor` via `email`, `slack`, `in_app`  
**Side effects**:
- Calls `notification_service.send` (currently prints to stdout — `TODO(mcp)`)
- Supervisor recipient ID is a hardcoded placeholder: `"supervisor-in-tenant"` — `TODO(db): resolve real supervisor IDs`

**Request body** — `CreateDraftRequest` (`backend/app/domain/schemas/site.py:11`)

| field | type | required | constraints |
| ----- | ---- | -------- | ----------- |
| `name` | `str` | yes | — |
| `city` | `str` | yes | first 3 chars used for site code prefix |
| `visit_date` | `date` | yes | YYYY-MM-DD |

**Response** — `SiteResponse` (HTTP `201`)

See `SiteResponse` shape under `GET /api/bd/drafts` above.

**Errors**

- `403` — caller role is not `executive`

**TODO markers** (`backend/app/routers/bd.py`)

- Line 58: `# TODO(db): insert into sites table`
- Line 83: `# TODO(db): resolve real supervisor IDs`

**Frontend caller**: `frontend/src/services/api/sites.js::createDraft` (has `TODO(db)` stub; not yet calling this endpoint). Also `siteService.js::createSite` calls `adapter.createSite` which in `httpAdapter.js` calls `POST /sites` — **path mismatch, needs update**.

**Example**

```bash
curl -X POST http://localhost:8000/api/bd/drafts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "BKC One East Wing", "city": "Mumbai", "visit_date": "2026-05-18"}'
```

---

### `POST /api/bd/drafts/{site_id}/archive`

**Handler**: `app.routers.bd:archive_draft`  
**Role required**: `supervisor` | `sub_supervisor`  
**Scope**: `tenant` | `city`  
**Touches**: reads → `[sites]`, writes → `[sites]`  
**State transition**: `*` → `archived`  
**Writes audit row**: yes  
**Notifies**: none  
**Side effects**: none beyond audit

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

- `403` — caller role is not `supervisor` or `sub_supervisor`

**TODO markers** (`backend/app/routers/bd.py`)

- Line 190: `# TODO(db): update sites set status=archived where id=site_id`

**Frontend caller**: `siteService.js::archiveSite` calls `adapter.archiveSite` which in `httpAdapter.js` calls `POST /sites/:id/archive` — **path mismatch, needs update to `/api/bd/drafts/:id/archive`**.

**Example**

```bash
curl -X POST http://localhost:8000/api/bd/drafts/site_h9d31a40/archive \
  -H "Authorization: Bearer <token>"
```

---

### `POST /api/bd/drafts/{site_id}/reject`

**Handler**: `app.routers.bd:reject_draft`  
**Role required**: `supervisor` | `sub_supervisor`  
**Scope**: `tenant` | `city`  
**Touches**: reads → `[sites]`, writes → `[sites]`  
**State transition**: `*` → `rejected`  
**Writes audit row**: yes  
**Notifies**: `executive` (originating exec) via `email`, `in_app`  
**Side effects**:
- Calls `notification_service.send` (stdout stub — `TODO(mcp)`)
- Recipient is hardcoded `"site-owner"` placeholder — `TODO(db): resolve exec user ID`

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Request body** — `RejectSiteRequest` (`backend/app/domain/schemas/site.py:21`)

| field | type | required | constraints |
| ----- | ---- | -------- | ----------- |
| `reasons` | `list[str]` | yes | at least one reason |
| `note` | `str \| null` | no | optional freeform note |

**Response** — `OkResponse` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `ok` | `bool` | `true` |
| `message` | `str` | confirmation |

**Errors**

- `403` — caller role not allowed

**TODO markers** (`backend/app/routers/bd.py`)

- Line 158: `# TODO(db): fetch site, validate current status allows rejection`
- Line 159: `# TODO(db): update sites set status=rejected, rejection_reasons=body.reasons`

**Frontend caller**: `siteService.js::rejectSite` calls `adapter.rejectSite` which in `httpAdapter.js` calls `POST /sites/:id/reject` — **path mismatch, needs update**.

**Example**

```bash
curl -X POST http://localhost:8000/api/bd/drafts/site_h9d31a40/reject \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"reasons": ["High rent", "Poor footfall"], "note": "Revisit in Q3"}'
```

---

### `POST /api/bd/drafts/{site_id}/shortlist`

**Handler**: `app.routers.bd:shortlist_draft`  
**Role required**: `supervisor` | `sub_supervisor`  
**Scope**: `tenant` | `city`  
**Touches**: reads → `[sites]`, writes → `[sites]`  
**State transition**: `draft_submitted` → `shortlisted`  
**Writes audit row**: yes  
**Notifies**: `executive` (originating exec) via `email`, `in_app`  
**Side effects**:
- Calls `notification_service.send` (stdout stub — `TODO(mcp)`)
- Recipient is hardcoded `"site-owner"` placeholder — `TODO(db): resolve exec user ID`
- Calls `assert_transition(DRAFT_SUBMITTED, SHORTLISTED)` — raises `422` on invalid transition

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Response** — `SiteResponse` (HTTP `200`)

See `SiteResponse` shape under `GET /api/bd/drafts`. Returns a stub site object until DB is wired.

**Errors**

- `403` — caller role not allowed
- `422` — invalid state transition

**TODO markers** (`backend/app/routers/bd.py`)

- Line 119: `# TODO(db): fetch site, assert tenant ownership`
- Line 121: `# TODO(db): update sites set status=shortlisted where id=site_id`
- Line 133: `# TODO(db): resolve exec user ID from site`

**Frontend caller**: `frontend/src/services/api/sites.js::shortlistDraft` (has `TODO(db)` stub). `siteService.js::shortlistSite` calls `adapter.patchSiteStatus` with `SHORTLISTED` — **adapter path mismatch**.

**Example**

```bash
curl -X POST http://localhost:8000/api/bd/drafts/site_h9d31a40/shortlist \
  -H "Authorization: Bearer <token>"
```

---

### `GET /api/bd/shortlist`

**Handler**: `app.routers.bd:list_shortlist`  
**Role required**: `executive` | `supervisor` | `sub_supervisor`  
**Scope**: `own` (executive) | `city` (sub_supervisor) | `tenant` (supervisor)  
**Touches**: reads → `[sites]`, writes → `[]`  
**Side effects**: none

**Response** — `SiteListResponse` (HTTP `200`)

Returns sites with status `shortlisted` or `details_submitted`. See `SiteListResponse` shape above.

**TODO markers** (`backend/app/routers/bd.py`)

- Line 215: `# TODO(db): query sites where status in (shortlisted, details_submitted)`

**Frontend caller**: no direct caller. `siteService.js::listSites` with a status filter would cover this via `GET /api/sites?status=...`. Dedicated shortlist view not yet wired.

**Example**

```bash
curl http://localhost:8000/api/bd/shortlist \
  -H "Authorization: Bearer <token>"
```

---

### `POST /api/bd/shortlist/{site_id}/approve`

**Handler**: `app.routers.bd:approve_shortlist`  
**Role required**: `supervisor` | `sub_supervisor`  
**Scope**: `tenant` | `city`  
**Touches**: reads → `[sites]`, writes → `[sites]`  
**State transition**: `details_submitted` → `approved`  
**Writes audit row**: yes  
**Notifies**: `executive` (originating exec) via `email`, `in_app`  
**Side effects**:
- Calls `notification_service.send` (stdout stub — `TODO(mcp)`)
- Calls `assert_transition(DETAILS_SUBMITTED, APPROVED)` — raises `422` on invalid transition

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Request body** — `ApproveShortlistRequest` (`backend/app/domain/schemas/site.py:54`)

| field | type | required | constraints |
| ----- | ---- | -------- | ----------- |
| `expected_loi_days` | `int` | yes | number of days exec has to upload LOI |

**Response** — `SiteResponse` (HTTP `200`)

Returns stub `SiteResponse` with `status=approved` until DB is wired.

**Errors**

- `403` — caller role not allowed
- `422` — invalid state transition

**TODO markers** (`backend/app/routers/bd.py`)

- Line 291: `# TODO(db): update sites set status=approved, expected_loi_days=body.expected_loi_days`

**Frontend caller**: `frontend/src/services/api/sites.js::approveShortlist` (has `TODO(db)` stub). `siteService.js::approveSite` calls `adapter.patchSiteStatus` with `APPROVED` — **adapter path mismatch**.

**Example**

```bash
curl -X POST http://localhost:8000/api/bd/shortlist/site_sl_mum143/approve \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"expected_loi_days": 14}'
```

---

### `POST /api/bd/shortlist/{site_id}/details/save`

**Handler**: `app.routers.bd:save_draft_details`  
**Role required**: `executive`  
**Scope**: `own`  
**Touches**: reads → `[sites]`, writes → `[site_details]`  
**State transition**: `shortlisted` → `shortlisted` (no status change; sets `details_completion=partial`)  
**Writes audit row**: no  
**Notifies**: none  
**Side effects**: none

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Request body** — `SaveDetailsRequest` (`backend/app/domain/schemas/site.py:26`)

All fields optional (incremental save). The 17-field detail form:

| field | type | required | constraints |
| ----- | ---- | -------- | ----------- |
| `model` | `str \| null` | no | — |
| `spoc_name` | `str \| null` | no | — |
| `google_pin` | `str \| null` | no | — |
| `score` | `float \| null` | no | — |
| `est_sales` | `float \| null` | no | — |
| `nearest_starbucks` | `float \| null` | no | distance in km |
| `nearest_twc` | `float \| null` | no | distance in km |
| `carpet` | `float \| null` | no | sq ft |
| `cam` | `float \| null` | no | — |
| `rent_type` | `str \| null` | no | e.g. `"fixed"` |
| `rent` | `float \| null` | no | per sq ft |
| `escalation` | `float \| null` | no | % |
| `rent_free_days` | `int \| null` | no | — |
| `cadex` | `float \| null` | no | — |
| `deposit` | `float \| null` | no | — |
| `brokerage` | `float \| null` | no | — |
| `lockin` | `int \| null` | no | months |
| `tenure` | `int \| null` | no | months |
| `total_op_cost` | `float \| null` | no | — |

**Response** — `OkResponse` (HTTP `200`)

**Errors**

- `403` — caller role is not `executive`

**TODO markers** (`backend/app/routers/bd.py`)

- Line 234: `# TODO(db): upsert site_details where site_id=site_id, set details_completion='partial'`

**Frontend caller**: `frontend/src/services/api/sites.js::saveDraftDetails` (has `TODO(db)` stub). `siteService.js::saveDraftDetails` calls `adapter.patchSiteDetails` which in `httpAdapter.js` calls `PATCH /sites/:id/details` — **path and method mismatch**.

**Example**

```bash
curl -X POST http://localhost:8000/api/bd/shortlist/site_sl_mum146/details/save \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"score": 78.0, "rent": 112.0, "carpet": 1120.0}'
```

---

### `POST /api/bd/shortlist/{site_id}/details/submit`

**Handler**: `app.routers.bd:submit_details_for_review`  
**Role required**: `executive`  
**Scope**: `own`  
**Touches**: reads → `[sites]`, writes → `[sites, site_details]`  
**State transition**: `shortlisted` → `details_submitted`  
**Writes audit row**: yes  
**Notifies**: `supervisor` via `email`, `slack`, `in_app`  
**Side effects**:
- Calls `notification_service.send` (stdout stub — `TODO(mcp)`)
- Calls `assert_transition(SHORTLISTED, DETAILS_SUBMITTED)` — raises `422` on invalid transition

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Request body** — `SubmitDetailsRequest` extends `SaveDetailsRequest` (`backend/app/domain/schemas/site.py:49`)

Same 17 fields as `SaveDetailsRequest`. Semantically all required fields should be populated before submitting.

**Response** — `SiteResponse` (HTTP `200`)

Returns stub `SiteResponse` with `status=details_submitted` until DB is wired.

**Errors**

- `403` — caller role is not `executive`
- `422` — invalid state transition

**TODO markers** (`backend/app/routers/bd.py`)

- Line 254: `# TODO(db): update sites set status=details_submitted, save body to site_details`

**Frontend caller**: `frontend/src/services/api/sites.js::submitDetailsForReview` (has `TODO(db)` stub). `siteService.js::submitDetails` calls `adapter.patchSiteStatus` with `DETAILS_SUBMITTED` — **adapter path mismatch**.

**Example**

```bash
curl -X POST http://localhost:8000/api/bd/shortlist/site_sl_mum146/details/submit \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"score": 78.0, "est_sales": 19.8, "carpet": 1120.0, "rent": 112.0, "rent_type": "fixed", "total_op_cost": 165000}'
```

---

### `POST /api/bd/shortlist/{site_id}/reassign`

**Handler**: `app.routers.bd:reassign_site`  
**Role required**: `supervisor`  
**Scope**: `tenant`  
**Touches**: reads → `[sites]`, writes → `[sites]`  
**State transition**: none (no status change)  
**Writes audit row**: yes  
**Notifies**: none  
**Side effects**: none beyond audit

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Request body** — `ReassignSiteRequest` (`backend/app/domain/schemas/site.py:58`)

| field | type | required | constraints |
| ----- | ---- | -------- | ----------- |
| `new_owner_id` | `str` | yes | user ID of the new exec owner |

**Response** — `OkResponse` (HTTP `200`)

**Errors**

- `403` — caller role is not `supervisor`

**TODO markers** (`backend/app/routers/bd.py`)

- Line 328: `# TODO(db): update sites set created_by=body.new_owner_id where id=site_id`

**Frontend caller**: no direct caller in `frontend/src/services/api/`. The `httpAdapter.js::assignSite` calls `POST /sites/:id/assign` — **different semantics; needs routing clarification**.

**Example**

```bash
curl -X POST http://localhost:8000/api/bd/shortlist/site_sl_mum146/reassign \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"new_owner_id": "user_aman"}'
```
