# LOI — Letter of Intent

Router file: `backend/app/routers/loi.py`  
Prefix: `/api/loi`  
Tag: `LOI`

Routes sorted by path, then method.

---

### `GET /api/loi/{site_id}`

**Handler**: `app.routers.loi:view_loi`  
**Role required**: `executive` | `supervisor` | `sub_supervisor`  
**Scope**: `own` (executive) | `city` (sub_supervisor) | `tenant` (supervisor)  
**Touches**: reads → `[site_documents]`, writes → `[]`  
**Side effects**: none (signed URL generation is a `TODO(storage)`)

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Response** — `LOIViewResponse` (HTTP `200`) (`backend/app/domain/schemas/loi.py:19`)

| field | type | notes |
| ----- | ---- | ----- |
| `site_id` | `str` | — |
| `file_url` | `str \| null` | signed URL — `null` until `TODO(storage)` resolved |
| `uploaded_at` | `date \| null` | YYYY-MM-DD |
| `uploaded_by` | `str \| null` | user name |

**Errors**

- `403` — caller is exec attempting to view another exec's site (scope enforcement is `TODO(auth)`)

**TODO markers** (`backend/app/routers/loi.py`)

- Line 74: `# TODO(db): fetch site, check ownership if exec, return document URL`
- Line 75: `# TODO(storage): generate signed URL for the stored document`
- Line 78: `# TODO(storage): real signed URL`

**Frontend caller**: `frontend/src/services/api/loi.js::viewLOI` (has `TODO(db)` stub — not yet calling this endpoint).

**Example**

```bash
curl http://localhost:8000/api/loi/site_q9m20i39 \
  -H "Authorization: Bearer <token>"
```

---

### `POST /api/loi/{site_id}/set-timeline`

**Handler**: `app.routers.loi:set_loi_timeline`  
**Role required**: `supervisor` | `sub_supervisor`  
**Scope**: `tenant` | `city`  
**Touches**: reads → `[sites]`, writes → `[sites]`  
**State transition**: none (no status change)  
**Writes audit row**: yes  
**Notifies**: none  
**Side effects**: none beyond audit

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Request body** — `SetLOITimelineRequest` (`backend/app/domain/schemas/loi.py:8`)

| field | type | required | constraints |
| ----- | ---- | -------- | ----------- |
| `expected_loi_days` | `int` | yes | number of days |

**Response** — `OkResponse` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `ok` | `bool` | `true` |
| `message` | `str` | confirmation |

**Errors**

- `403` — caller role not allowed

**TODO markers** (`backend/app/routers/loi.py`)

- Line 99: `# TODO(db): update sites set expected_loi_days=body.expected_loi_days where id=site_id`

**Frontend caller**: `frontend/src/services/api/loi.js::setLOITimeline` (has `TODO(db)` stub — not yet calling this endpoint).

**Example**

```bash
curl -X POST http://localhost:8000/api/loi/site_q9m20i39/set-timeline \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"expected_loi_days": 21}'
```

---

### `POST /api/loi/{site_id}/upload`

**Handler**: `app.routers.loi:upload_loi`  
**Role required**: `executive`  
**Scope**: `own`  
**Touches**: reads → `[sites]`, writes → `[sites, site_documents]`  
**State transition**: `approved` → `loi_uploaded`  
**Writes audit row**: yes  
**Notifies**: `supervisor` via `email`, `slack`, `in_app`  
**Side effects**:
- Calls `notification_service.send` (stdout stub — `TODO(mcp)`)
- Calls `assert_transition(APPROVED, LOI_UPLOADED)` — raises `422` on invalid transition
- File upload is NOT yet accepted: multipart body is not wired (`TODO(storage)`)

**Path params**

| name | type | notes |
| ---- | ---- | ----- |
| `site_id` | `str` | UUID of the site |

**Request body**: `multipart/form-data` with field `file: File`

The handler signature does not yet declare `file: UploadFile = File(...)`. This must be added as part of `TODO(storage)` wiring. See `CONNECTING_BACKEND.md` Section F.

**Response** — `LOIUploadResponse` (HTTP `200`) (`backend/app/domain/schemas/loi.py:12`)

| field | type | notes |
| ----- | ---- | ----- |
| `site_id` | `str` | — |
| `loi_uploaded` | `bool` | `true` on success |
| `loi_uploaded_at` | `date \| null` | YYYY-MM-DD; currently `date.today()` stub |
| `days_to_loi` | `int \| null` | computed from approval date; currently `0` stub |

**Errors**

- `403` — caller role is not `executive`
- `422` — invalid state transition (e.g. site is not `approved`)

**TODO markers** (`backend/app/routers/loi.py`)

- Line 35: `# TODO(db): update sites set status=loi_uploaded, loi_uploaded_at=now() where id=site_id`
- Line 36: `# TODO(storage): accept multipart file upload; store in S3/GCS; save URL to site_documents`

**Frontend caller**: `frontend/src/services/api/loi.js::uploadLOI` (has `TODO(db)` stub). `loiService.js::uploadLoi` calls `adapter.uploadLoi` which in `httpAdapter.js` calls `POST /sites/:id/loi` — **path mismatch, needs update to `/api/loi/:id/upload`**.

**Example**

```bash
# Once multipart is wired:
curl -X POST http://localhost:8000/api/loi/site_a8f3c129/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@signed-loi.pdf"
```
