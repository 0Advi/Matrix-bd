# Blue Tokai Ops Platform — API Reference

Generated: 2026-05-21T00:00:00Z  
Source manifest: `.claude/artifacts/routes-manifest.json` (verified against router source)

---

## Counts

| Domain | Routes |
| ------ | ------ |
| auth | 2 |
| bd | 11 |
| loi | 3 |
| staging | 3 | 
| sites | 11 |
| audit | 2 |
| notifications | 2 |
| tenancy | 2 |
| users | 3 |
| **Total** | **39** |

All 39 routes in the manifest have corresponding handlers in the router source files.

---

## Auth / Role legend

| Role | Who | Scope |
| ---- | --- | ----- |
| `executive` | BD field executive | own — sees and acts on sites they created |
| `sub_supervisor` | City-level supervisor | city — scoped to their assigned city |
| `supervisor` | Tenant-level supervisor | tenant — sees all sites / users in the tenant |
| `system` | Internal service calls | tenant — not for direct client use |
| `public` | Login and logout endpoints | — |

Scope enforcement is currently stubbed in `app/rbac/guards.py::require_scope`. Role enforcement via `require_role(...)` is active.

---

## Conventions

Derived from the router source and mock schema — not invented.

**Base URL**: `http://localhost:8000` (dev). All routes are under the `/api` prefix, registered via `settings.api_prefix`.

**Auth header**: `Authorization: Bearer <token>`. Token is read from `window.__zm_token` by `httpAdapter.js`. If the header is absent, the backend falls back to a hardcoded mock user (`TODO(auth)`).

**Status enum values** (UPPER_SNAKE_CASE in frontend, `snake_case` in backend `SiteStatus` enum):

```
draft_submitted  /  DRAFT_SUBMITTED
shortlisted      /  SHORTLISTED
details_submitted / DETAILS_SUBMITTED
approved         /  APPROVED
loi_uploaded     /  LOI_UPLOADED
pushed_to_payments / PUSHED_TO_PAYMENTS
rejected         /  REJECTED
archived         /  ARCHIVED
```

**Pagination** (audit domain): `?page=<int>&?limit=<int>` query params. Response shape: `{ items: [...], total: int }`.

**OK response shape** (common): `{ "ok": true, "message": "..." }` — defined in `app/domain/schemas/common.py`.

**Error shape** (from guards): `{ "detail": "<message>" }`. State-machine violations return HTTP `422`.

**Timestamps**: ISO-8601 UTC strings (e.g. `2026-05-17T10:00:00Z`). Dates in `YYYY-MM-DD`.

**Tenant isolation**: every route that touches the DB passes a `tenant_id` extracted from the JWT claim via `app/core/deps.py::get_tenant`. The DB layer (once wired) must add `WHERE tenant_id = :tenant_id` to every query.

---

## State machine

Defined in `backend/app/domain/state_machine.py`. Every mutating route calls `assert_transition(from, to)` before writing; invalid transitions raise HTTP `422`.

```
null ──► DRAFT_SUBMITTED ──► SHORTLISTED ──► DETAILS_SUBMITTED ──► APPROVED ──► LOI_UPLOADED ──► PUSHED_TO_PAYMENTS (terminal)
                     │              │                   │              │              │
                     └──────────────┴───────────────────┴──────────────┴──────────────┴──► REJECTED (terminal)
                                                                                      └──► ARCHIVED (terminal)
```

---

## Table of contents

- [Auth](./auth.md)
- [BD (Business Development)](./bd.md)
- [LOI (Letter of Intent)](./loi.md)
- [Staging](./staging.md)
- [Sites](./sites.md)
- [Audit](./audit.md)
- [Notifications](./notifications.md)
- [Tenancy](./tenancy.md)
- [Users](./users.md)

---

## Needs review

### Routes in manifest but missing from router source
None. All 39 manifest routes have verified handler implementations.

### Routes in router source but missing from manifest
None.

### Routes called by frontend but absent from the manifest / router source

1. **`PATCH /sites/:id/status`** — called by `httpAdapter.js::patchSiteStatus` and transitively by every `siteService.js` convenience wrapper (`shortlistSite`, `submitDetails`, `approveSite`, `pushToPayments`). No matching route exists in any router file. The manifest routes these transitions through domain-specific POST endpoints (`/bd/drafts/:id/shortlist`, `/bd/shortlist/:id/approve`, etc.). **Action required**: either add a unified `PATCH /api/sites/{site_id}/status` dispatcher route, or update `httpAdapter.js` to call the correct per-domain endpoints.

2. **`PATCH /sites/:id/details`** — called by `httpAdapter.js::patchSiteDetails` and by `siteService.js::saveDraftDetails`. No matching route in any router file. The manifest covers partial save via `POST /api/bd/shortlist/{site_id}/details/save`. **Action required**: update `httpAdapter.js` to call `POST /api/bd/shortlist/:id/details/save`, or add the PATCH route.

3. **`POST /sites`** — called by `httpAdapter.js::createSite` and `siteService.js::createSite`. No matching route in the `sites.py` router. The manifest covers site creation via `POST /api/bd/drafts`. **Action required**: update `httpAdapter.js::createSite` to call `POST /api/bd/drafts`.

4. **`POST /sites/:id/archive`** — called by `httpAdapter.js::archiveSite`. Maps to `POST /api/bd/drafts/{site_id}/archive` in the manifest. **Action required**: update path in `httpAdapter.js`.

5. **`POST /sites/:id/reject`** — called by `httpAdapter.js::rejectSite`. Maps to `POST /api/bd/drafts/{site_id}/reject`. **Action required**: update path in `httpAdapter.js`.

6. **`POST /sites/:id/assign`** — called by `httpAdapter.js::assignSite`. Maps to `POST /api/bd/shortlist/{site_id}/reassign` or `POST /api/bd/assign-sub-supervisor`. Semantics differ; needs clarification.

7. **`POST /sites/:id/loi`** — called by `httpAdapter.js::uploadLoi`. Maps to `POST /api/loi/{site_id}/upload`. **Action required**: update path in `httpAdapter.js`.

### Routes partially implemented (TODO markers present)
All 39 routes have `# TODO(db):` or `# TODO(auth):` markers. See individual domain files for verbatim locations. See `CONNECTING_BACKEND.md` for the wiring runbook.
