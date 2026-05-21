# Connecting the Backend — Wiring Runbook

For the teammate replacing stub adapters with real SQLAlchemy/SQLModel persistence.  
Work top-to-bottom. Each section is a dependency for the next.

---

## Table of Contents

- [Section A — Prerequisites](#section-a--prerequisites)
- [Section B — Database layer](#section-b--database-layer)
- [Section C — Wire each domain in order](#section-c--wire-each-domain-in-order)
- [Section D — Auth wiring](#section-d--auth-wiring)
- [Section E — Switch the frontend to live mode](#section-e--switch-the-frontend-to-live-mode)
- [Section F — File storage](#section-f--file-storage)
- [Section G — Notifications](#section-g--notifications)
- [Section H — Audit log](#section-h--audit-log)
- [Section I — Definition of done](#section-i--definition-of-done)
- [Section J — Known gaps to address before prod](#section-j--known-gaps-to-address-before-prod)

---

## Section A — Prerequisites

### Python version

Requires Python >= 3.11 (declared in `backend/pyproject.toml`). Python 3.12 is recommended for `asyncio` stability with SQLAlchemy 2.x.

```bash
python --version   # must be >= 3.11
```

### Virtual environment setup

```bash
cd /Users/adityashandilya/Desktop/Matrix/backend

python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# or: .venv\Scripts\activate       # Windows

pip install -e ".[dev]"
```

This installs: `fastapi>=0.111`, `uvicorn[standard]>=0.30`, `pydantic>=2.7`, `pytest>=8`, `httpx>=0.27`.

You will also need to add database and auth dependencies. Add them to `pyproject.toml` under `[project.dependencies]` before installing:

```toml
"sqlalchemy[asyncio]>=2.0",
"sqlmodel>=0.0.18",
"asyncpg>=0.29",           # PostgreSQL async driver (or aiosqlite for SQLite dev)
"alembic>=1.13",
"python-jose[cryptography]>=3.3",
"passlib[bcrypt]>=1.7",
"python-multipart>=0.0.9", # required for UploadFile support
```

Re-run `pip install -e ".[dev]"` after updating.

### Launch backend dev server

```bash
cd /Users/adityashandilya/Desktop/Matrix/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Expected: server starts at `http://localhost:8000`. Verify:

```bash
curl http://localhost:8000/api/health
# Expected: {"status": "ok", "version": "0.1.0"}
```

The health endpoint is at `GET /api/health` (defined in `backend/app/main.py` line 28).  
Note: there is no `/healthz` alias. If you need one for load-balancer probes, add it to `main.py`.

### Launch frontend dev server

```bash
cd /Users/adityashandilya/Desktop/Matrix/frontend
npm install
npm run dev
```

Expected: frontend starts at `http://localhost:5173`.

### Verify the two are talking

With the backend running and `VITE_USE_MOCK=false` set (see Section E), open `http://localhost:5173` and check the browser Network tab. All API calls should appear directed at `http://localhost:8000`.

CORS is pre-configured in `backend/app/core/config.py`:

```python
cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
```

If you serve the frontend on a different port, add it to `cors_origins` in `config.py`.

---

## Section B — Database layer

### Step B-1: Replace the stub session factory

File: `backend/app/db/session.py`

Current state: `get_db()` yields `None`. Replace with:

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import os

DATABASE_URL = os.environ["DATABASE_URL"]
# Example: "postgresql+asyncpg://user:pass@localhost:5432/zmatrix"
# For SQLite dev:  "sqlite+aiosqlite:///./zmatrix.db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

Update `backend/app/core/deps.py` to change the type annotation:

```python
from sqlalchemy.ext.asyncio import AsyncSession
DbDep = Annotated[AsyncSession, Depends(get_db)]
```

Add `DATABASE_URL` to `frontend/.env` (backend reads it directly via `os.environ`, not Vite).  
Create `backend/.env` or set the env var in your shell:

```bash
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/zmatrix"
```

### Step B-2: ORM models

Each Pydantic schema in `backend/app/domain/schemas/` needs a corresponding SQLModel table. The canonical column list is derived from `frontend/src/services/api/mock/mockSites.js` — the mock schema is the contract.

Create `backend/app/db/models.py`:

#### `sites` table

Derived from the mock site shape in `mockSites.js`:

```python
from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON


class Site(SQLModel, table=True):
    __tablename__ = "sites"

    id: str = Field(primary_key=True)            # UUID string
    code: str = Field(index=True)                # e.g. "BT-MUM-0144"
    name: str
    city: str = Field(index=True)
    tenant_id: str = Field(index=True, foreign_key="tenants.id")
    status: str = Field(index=True)              # SiteStatus snake_case value
    created_by: str                              # user id of originating exec
    assigned_to: Optional[str] = None           # user id of currently assigned exec
    visit_date: Optional[date] = None
    expected_loi_days: Optional[int] = None
    loi_url: Optional[str] = None
    details_completion: Optional[str] = None    # null | "partial"
    rejection_reasons: Optional[list] = Field(default=None, sa_column=Column(JSON))
    archive_note: Optional[str] = None
    score: Optional[float] = None
    est_sales: Optional[float] = None
    carpet: Optional[float] = None
    rent: Optional[float] = None
    rent_type: Optional[str] = None
    total_op_cost: Optional[float] = None
    hue: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

#### `site_details` table

The 17-field detail form from `SaveDetailsRequest` (`backend/app/domain/schemas/site.py:26`):

```python
class SiteDetails(SQLModel, table=True):
    __tablename__ = "site_details"

    id: str = Field(primary_key=True)
    site_id: str = Field(foreign_key="sites.id", index=True)
    model: Optional[str] = None
    spoc_name: Optional[str] = None
    google_pin: Optional[str] = None
    score: Optional[float] = None
    est_sales: Optional[float] = None
    nearest_starbucks: Optional[float] = None
    nearest_twc: Optional[float] = None
    carpet: Optional[float] = None
    cam: Optional[float] = None
    rent_type: Optional[str] = None
    rent: Optional[float] = None
    escalation: Optional[float] = None
    rent_free_days: Optional[int] = None
    cadex: Optional[float] = None
    deposit: Optional[float] = None
    brokerage: Optional[float] = None
    lockin: Optional[int] = None
    tenure: Optional[int] = None
    total_op_cost: Optional[float] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

#### `site_documents` table

```python
class SiteDocument(SQLModel, table=True):
    __tablename__ = "site_documents"

    id: str = Field(primary_key=True)
    site_id: str = Field(foreign_key="sites.id", index=True)
    tenant_id: str = Field(foreign_key="tenants.id")
    file_url: str                                # S3/GCS URL or local path
    uploaded_by: str                             # user id
    uploaded_at: date
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

#### `notifications` table

```python
class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: str = Field(primary_key=True)
    recipient_id: str = Field(index=True)
    tenant_id: str = Field(foreign_key="tenants.id")
    event: str
    channel: str                                 # "in_app" | "email" | "slack"
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

#### `users` table

```python
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    role: str                                    # executive | supervisor | sub_supervisor
    tenant_id: str = Field(foreign_key="tenants.id")
    assigned_city: Optional[str] = None         # for sub_supervisor
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

#### `tenants` table

```python
class Tenant(SQLModel, table=True):
    __tablename__ = "tenants"

    id: str = Field(primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

### Step B-3: audit_trail persistence — two options

The `auditTrail` field in the mock is a list embedded in the site object. For the real DB, choose one:

**Option 1 — JSON column on `sites`**

Add `audit_trail: list = Field(default_factory=list, sa_column=Column(JSON))` to the `Site` model. Reads are fast (single query). Writes append to the JSON blob. Drawback: no individual row indexing; difficult to query by actor or action.

**Option 2 — Separate `audit_events` table (recommended)**

```python
class AuditEvent(SQLModel, table=True):
    __tablename__ = "audit_events"

    id: str = Field(primary_key=True)
    site_id: str = Field(foreign_key="sites.id", index=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    actor: str
    action: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    detail: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

Recommendation: use Option 2. The audit feed (`GET /api/audit`, `GET /api/audit/site/:id`, `GET /api/sites/:id/activity`) all query audit events independently. A separate table keeps audit immutable, allows pagination, and supports future filtering by action type or actor. The existing `audit_service.write_audit_event` signature already matches this shape exactly.

### Step B-4: Multi-tenancy mixin

Every table above needs `tenant_id`. To enforce this without repeating the column, use a mixin:

```python
from sqlmodel import SQLModel, Field


class TenantMixin(SQLModel):
    """Add to every table that must be tenant-scoped."""
    tenant_id: str = Field(index=True, foreign_key="tenants.id")
```

Apply: `class Site(TenantMixin, SQLModel, table=True): ...`

Every query in every router must include `WHERE tenant_id = :tenant_id` derived from the JWT claim via `TenantId = Annotated[str, Depends(get_tenant)]` (already wired in `app/core/deps.py`).

### Step B-5: Run Alembic migrations

```bash
cd /Users/adityashandilya/Desktop/Matrix/backend
alembic init alembic
# Edit alembic/env.py to import your models and set target_metadata = SQLModel.metadata
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

---

## Section C — Wire each domain in order

Work in this order: `tenancy` → `users` → `bd` → `loi` → `staging` → `sites` → `audit` → `notifications`. Tenancy and users have no dependencies on other domains.

### Canonical patterns

**List route pattern** (copy to all list handlers):

```python
from sqlmodel import select

@router.get("/drafts", response_model=SiteListResponse)
async def list_drafts(db: DbDep, current_user: CurrentUser, tenant_id: TenantId):
    stmt = select(Site).where(
        Site.tenant_id == tenant_id,
        Site.status == SiteStatus.DRAFT_SUBMITTED,
    )
    # Role scope: if executive, restrict to own sites
    if current_user["role"] == Role.EXECUTIVE.value:
        stmt = stmt.where(Site.created_by == current_user["sub"])
    # Role scope: if sub_supervisor, restrict to city
    elif current_user["role"] == Role.SUB_SUPERVISOR.value:
        stmt = stmt.where(Site.city == current_user["city"])

    result = await db.execute(stmt)
    rows = result.scalars().all()
    return SiteListResponse(items=rows, total=len(rows))
```

**Transition route pattern** (copy to all mutating handlers):

```python
from sqlmodel import select
from datetime import datetime, timezone

@router.post("/drafts/{site_id}/shortlist", response_model=SiteResponse)
async def shortlist_draft(site_id: str, db: DbDep, current_user: ..., tenant_id: TenantId):
    # 1. Fetch and verify ownership
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.tenant_id == tenant_id)
    )
    site = result.scalar_one_or_none()
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    # 2. Assert transition (raises 422 on invalid)
    assert_transition(SiteStatus(site.status), SiteStatus.SHORTLISTED)

    # 3. Apply transition
    site.status = SiteStatus.SHORTLISTED.value
    site.updated_at = datetime.now(timezone.utc)
    db.add(site)
    await db.commit()
    await db.refresh(site)

    # 4. Write audit
    await write_audit_event(
        db,
        site_id=site_id,
        actor=current_user["name"],
        action="shortlist",
        from_status=SiteStatus.DRAFT_SUBMITTED.value,
        to_status=SiteStatus.SHORTLISTED.value,
    )

    # 5. Notify
    await notify(
        event="draft_shortlisted",
        recipient_ids=[site.created_by],   # real exec ID from DB
        channels=["email", "in_app"],
        payload={"site_id": site_id},
    )
    return site
```

### Domain checklist

For each domain, the steps are:

1. Open `backend/app/routers/<domain>.py`.
2. Add `from app.db.models import <relevant models>` at the top.
3. For each route, locate the `# TODO(db):` markers (listed in the domain doc files).
4. Replace each stub block with the canonical pattern above.
5. After wiring, run: `pytest backend/tests/` (add tests as you go).
6. Flip the frontend to HTTP mode (Section E) and manually click through the relevant page.

**tenancy** (`backend/app/routers/tenancy.py`)
- [ ] `list_tenants`: line 22 — `SELECT * FROM tenants WHERE id IN (...)`
- [ ] `list_cities`: line 37 — `SELECT DISTINCT city FROM sites WHERE tenant_id=:tenant_id`

**users** (`backend/app/routers/users.py`)
- [ ] `list_users`: line 35 — `SELECT * FROM users WHERE tenant_id=:tenant_id`
- [ ] `assign_sub_supervisor_city`: line 54 — `UPDATE users SET role=sub_supervisor, assigned_city=:city WHERE id=:user_id`

**bd** (`backend/app/routers/bd.py`)
- [ ] `create_draft`: line 58 — INSERT into `sites`
- [ ] `create_draft`: line 83 — resolve real supervisor IDs from `users` table
- [ ] `list_drafts`: line 101 — SELECT with role scope
- [ ] `shortlist_draft`: lines 119, 121, 133 — fetch site, UPDATE status, resolve exec ID
- [ ] `reject_draft`: lines 158–159 — fetch site, UPDATE status + rejection_reasons
- [ ] `archive_draft`: line 190 — UPDATE status=archived
- [ ] `list_shortlist`: line 215 — SELECT where status IN (shortlisted, details_submitted)
- [ ] `save_draft_details`: line 234 — UPSERT site_details, set details_completion='partial'
- [ ] `submit_details_for_review`: line 254 — UPDATE sites + UPSERT site_details
- [ ] `approve_shortlist`: line 291 — UPDATE status=approved, expected_loi_days
- [ ] `reassign_site`: line 328 — UPDATE created_by
- [ ] `assign_sub_supervisor`: line 352 — UPDATE users (role + city)

**loi** (`backend/app/routers/loi.py`)
- [ ] `upload_loi`: line 35 — UPDATE status=loi_uploaded; line 36 — save document URL (needs Section F first)
- [ ] `view_loi`: lines 74–75 — fetch site_documents; generate signed URL (needs Section F first)
- [ ] `set_loi_timeline`: line 99 — UPDATE expected_loi_days

**staging** (`backend/app/routers/staging.py`)
- [ ] `list_exec_staging`: line 34 — SELECT approved sites for exec
- [ ] `list_supervisor_staging`: lines 51–52 — SELECT loi_uploaded sites with city scope
- [ ] `push_to_payments`: line 73 — UPDATE status=pushed_to_payments; line 74 — payments stub remains

**sites** (`backend/app/routers/sites.py`)
- [ ] `list_sites`: lines 26–27 — SELECT with status + city filters + role scope
- [ ] `get_site`: line 44 — SELECT single site (remove 404 stub)
- [ ] `get_site_activity`: line 62 — SELECT audit_events for site
- [ ] `get_site_documents`: lines 78–79 — SELECT site_documents (signed URLs in Section F)

**audit** (`backend/app/routers/audit.py`)
- [ ] `list_audit_events`: line 28 — paginated SELECT from audit_events
- [ ] `get_site_audit`: line 46 — SELECT audit_events by site_id

**notifications** (`backend/app/routers/notifications.py`)
- [ ] `list_notifications`: line 24 — SELECT notifications WHERE recipient_id=current_user.sub
- [ ] `send_notification`: plug MCP transport (Section G)

---

## Section D — Auth wiring

### Step D-1: Replace `decode_token`

File: `backend/app/core/security.py`

Install `python-jose[cryptography]`. Then replace the stub:

```python
from jose import JWTError, jwt
from fastapi import HTTPException, status
import os

JWT_SECRET = os.environ["JWT_SECRET"]          # at least 32 random bytes
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "zmatrix"


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": True},
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
```

### Step D-2: Replace `get_current_user`

File: `backend/app/core/deps.py`

The current stub already calls `decode_token`; once `decode_token` is real, `get_current_user` works correctly. The only change needed is removing the hardcoded fallback:

```python
async def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or malformed",
        )
    token = authorization.split(" ", 1)[1]
    return decode_token(token)
```

### Expected JWT claim shape

The backend expects — and the frontend must send — tokens with these claims:

| claim | type | notes |
| ----- | ---- | ----- |
| `sub` | `str` | user ID, e.g. `"user_riya"` |
| `name` | `str` | display name |
| `role` | `str` | `executive` \| `supervisor` \| `sub_supervisor` |
| `tenant_id` | `str` | tenant ID |
| `city` | `str` | relevant for `sub_supervisor` city scope |
| `exp` | `int` | Unix timestamp expiry (standard JWT claim) |

### Step D-3: Frontend auth alignment

File: `frontend/src/services/api/authService.js`

The `DEFAULT_SESSION` in `frontend/src/services/api/mock/mockAuth.js` has:

```js
{ id, name, email, role, cityScope, tenantId, token }
```

The backend `/users/me` currently returns:

```json
{ "sub": "...", "name": "...", "role": "...", "tenant_id": "...", "city": "..." }
```

These shapes do not yet match. Before switching to HTTP mode:

1. Update `GET /api/users/me` to return `id` (not `sub`), `email`, `cityScope` (not `city`), `tenantId` (camelCase, not `tenant_id`), and `token` fields — or update the frontend to accept the backend shape. Pick one canonical shape and apply it everywhere.
2. The frontend stores the token in `window.__zm_token` (see `httpAdapter.js` line 13). The login endpoint returns the token in the response body so the frontend can store it. See [`auth.md`](./auth.md) for the live endpoints; the JWT issuance is still stubbed (`TODO(auth)`).

---

## Section E — Switch the frontend to live mode

### Step E-1: Edit the env file

File: `frontend/.env`

Change:
```
VITE_USE_MOCK=true
```
To:
```
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000
```

Restart: `npm run dev`

### Step E-2: Adapter selection line

The adapter switch is in `frontend/src/services/api/adapters/index.js`. The key line to verify is:

```js
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === true;
```

Grep for it:

```bash
grep -n "USE_MOCK" /Users/adityashandilya/Desktop/Matrix/frontend/src/services/api/adapters/index.js
```

When `VITE_USE_MOCK=false`, `USE_MOCK` evaluates to `false` and `export const adapter = http`.

The console will log: `[adapter] Using HTTP adapter. Set VITE_USE_MOCK to switch.`

### Step E-3: Verify in browser

1. Open `http://localhost:5173`.
2. Open DevTools > Network tab.
3. Navigate to Pipeline (BD drafts), Shortlist, and Staging views.
4. Each page load should show XHR/Fetch requests to `http://localhost:8000/api/...`.
5. Check the response status. Most routes will return empty `items: []` arrays until DB data exists — that is correct.

### Common failures and what to check

| Symptom | Check |
| ------- | ----- |
| `Network Error` on all requests | Backend not running. Run `uvicorn app.main:app --reload`. |
| `CORS error` in console | Frontend port not in `cors_origins` in `backend/app/core/config.py`. |
| `401 Unauthorized` | JWT header not being sent. Check `window.__zm_token` is set after login. |
| `403 Forbidden` | Role mismatch. The token's `role` claim does not match `require_role(...)` in the router. |
| `422 Unprocessable Entity` on a transition | State machine rejected the transition. The site is not in the expected `from` status. |
| Trailing slash 404 | FastAPI is strict about trailing slashes. `GET /api/sites/` (with slash) does not match `GET /api/sites`. Ensure `httpAdapter.js` paths have no trailing slashes. |
| `POST /sites` returns 404 | `httpAdapter.js` calls non-existent routes. See README.md "Needs review" for the full list of path mismatches. |

---

## Section F — File storage

### Step F-1: Add multipart support to `upload_loi`

File: `backend/app/routers/loi.py`

The current handler signature does not accept a file. Add `python-multipart` to dependencies (see Section A), then update:

```python
from fastapi import UploadFile, File

@router.post("/{site_id}/upload", response_model=LOIUploadResponse)
async def upload_loi(
    site_id: str,
    file: UploadFile = File(...),           # add this parameter
    db: DbDep = ...,
    current_user: ... = ...,
    tenant_id: TenantId = ...,
) -> LOIUploadResponse:
    file_bytes = await file.read()
    # TODO(storage): persist file_bytes to storage backend
    # file.filename, file.content_type are available
    ...
```

### Step F-2: Storage backend

Recommended approach: start with local disk for dev, switch to S3 for prod via an env flag.

Add to `backend/.env`:

```
STORAGE_BACKEND=local           # or "s3"
STORAGE_LOCAL_PATH=./uploads    # for local mode
AWS_BUCKET_NAME=zmatrix-loi     # for s3 mode
AWS_REGION=ap-south-1
```

Create `backend/app/services/storage_service.py`:

```python
import os, uuid
from pathlib import Path

BACKEND = os.environ.get("STORAGE_BACKEND", "local")
LOCAL_PATH = Path(os.environ.get("STORAGE_LOCAL_PATH", "./uploads"))


async def store_file(file_bytes: bytes, filename: str, site_id: str) -> str:
    """Persist file and return the URL/path to store in site_documents."""
    key = f"loi/{site_id}/{uuid.uuid4()}-{filename}"

    if BACKEND == "local":
        dest = LOCAL_PATH / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(file_bytes)
        return f"/uploads/{key}"         # serve via a static mount

    elif BACKEND == "s3":
        import boto3
        s3 = boto3.client("s3")
        bucket = os.environ["AWS_BUCKET_NAME"]
        s3.put_object(Bucket=bucket, Key=key, Body=file_bytes)
        return f"https://{bucket}.s3.amazonaws.com/{key}"

    raise ValueError(f"Unknown STORAGE_BACKEND: {BACKEND}")


async def signed_url(file_url: str) -> str:
    """Generate a time-limited signed URL for download."""
    if BACKEND == "local":
        return file_url                  # static mount — no signing needed in dev

    elif BACKEND == "s3":
        import boto3
        s3 = boto3.client("s3")
        key = file_url.split(".amazonaws.com/", 1)[-1]
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": os.environ["AWS_BUCKET_NAME"], "Key": key},
            ExpiresIn=3600,
        )
```

### Step F-3: Replace `TODO(storage)` markers

After creating `storage_service.py`, replace the markers in these files:

- `backend/app/routers/loi.py` line 36 — call `storage_service.store_file`, save returned URL to `site_documents`
- `backend/app/routers/loi.py` line 75 — call `storage_service.signed_url` for `view_loi`
- `backend/app/routers/sites.py` line 79 — call `storage_service.signed_url` for each document in `get_site_documents`

---

## Section G — Notifications

### Step G-1: Wiring order

1. Sandbox SMTP email first — fastest feedback loop.
2. Slack webhook second.
3. MCP integration last (replaces the raw HTTP calls with the MCP client).

### Step G-2: Replace the stub in `notification_service.py`

File: `backend/app/services/notification_service.py`

The `TODO(mcp)` marker is at line 29. The current stub calls `print(...)`. Replace the body of `send()`:

```python
import httpx, os

SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))   # MailHog default for dev
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")


async def send(*, event, recipient_ids, channels=["in_app"], payload=None):
    payload = payload or {}

    if "in_app" in channels:
        # Persist to notifications table — see Section H for the write pattern
        await _write_in_app(event=event, recipient_ids=recipient_ids, payload=payload)

    if "email" in channels:
        await _send_email(event=event, recipient_ids=recipient_ids, payload=payload)

    if "slack" in channels and SLACK_WEBHOOK_URL:
        await _send_slack(event=event, payload=payload)


async def _write_in_app(event, recipient_ids, payload):
    # TODO(db): INSERT INTO notifications for each recipient_id
    print(f"[in_app] {event} -> {recipient_ids}")


async def _send_email(event, recipient_ids, payload):
    # Use aiosmtplib for async SMTP
    # For dev: point SMTP_HOST to MailHog (docker run -p 1025:1025 mailhog/mailhog)
    print(f"[email] {event} -> {recipient_ids}")


async def _send_slack(event, payload):
    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json={"text": f"[{event}] {payload}"})
```

---

## Section H — Audit log

### Persist via the `audit_events` table

File: `backend/app/services/audit_service.py`

Current state: prints to stdout (line 35). Replace:

```python
from app.db.models import AuditEvent
import uuid
from datetime import datetime, timezone


async def write_audit_event(db, *, site_id, actor, action,
                             from_status=None, to_status=None, detail=None) -> dict:
    event = AuditEvent(
        id=str(uuid.uuid4()),
        site_id=site_id,
        tenant_id=...,   # pass tenant_id as a parameter — add it to the signature
        actor=actor,
        action=action,
        from_status=str(from_status) if from_status else None,
        to_status=str(to_status) if to_status else None,
        detail=detail,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.flush()    # flush within the same transaction as the status update
    # Do NOT commit here — let the router commit after both the site update and audit row
    return event.dict()
```

Note: add `tenant_id` to the `write_audit_event` signature, and pass it from every router call. The routers already have `tenant_id: TenantId` available.

All 9 routers that call `write_audit_event` (bd, loi, staging, users) need a `tenant_id` argument added to each call site.

---

## Section I — Definition of done

- [ ] `VITE_USE_MOCK=false` and the frontend boots at `http://localhost:5173` without console errors.
- [ ] All 8 domains' routes return `200` / appropriate status on the happy path (verify with curl or the Network tab).
- [ ] Creating a draft from the frontend (`POST /api/bd/drafts`) persists to the DB and the site appears after a page refresh / backend restart.
- [ ] Approving a shortlist item (`POST /api/bd/shortlist/:id/approve`) writes an audit row visible in `GET /api/audit/site/:id`.
- [ ] Uploading an LOI (`POST /api/loi/:id/upload`) persists the file to the storage backend and stores a non-null URL in `site_documents`.
- [ ] Reject (`POST /api/bd/drafts/:id/reject`) and archive (`POST /api/bd/drafts/:id/archive`) routes work and the site transitions to the terminal status.
- [ ] Invalid transitions (e.g. calling `POST /api/bd/drafts/:id/shortlist` on a `shortlisted` site) return `422` with the state machine error message.
- [ ] JWT verification rejects expired or tampered tokens with `401 Unauthorized`.

---

## Section J — Known gaps to address before prod

1. **`LOITimelinePage` is a stub** re-exporting `AddDetailsPage`. A dedicated LOI timeline view needs to be built and wired to `GET /api/loi/:id` and `POST /api/loi/:id/set-timeline`.

2. **`PATCH /sites/:id/details` route does not exist** in any router. `httpAdapter.js::patchSiteDetails` (line 45) and `siteService.js::saveDraftDetails` call it. The manifest covers this via `POST /api/bd/shortlist/:id/details/save`. Options:
   - Add a `PATCH /api/sites/{site_id}/details` route to `backend/app/routers/sites.py` that delegates to the same logic.
   - Update `httpAdapter.js` to call `POST /api/bd/shortlist/:id/details/save` directly.
   Update the manifest after whichever change is made.

3. **`httpAdapter.js` path mismatches** — the frontend HTTP adapter calls several paths that do not match the manifest. The full list is in `docs/api/README.md` under "Needs review". These must be resolved before `VITE_USE_MOCK=false` can be used end-to-end.

4. **`POST /auth/login` and `POST /auth/logout` are stubs.** `backend/app/routers/auth.py` exists and the frontend's `httpAdapter.js` calls succeed against the mock user list, but JWT issuance, credential validation against the DB, and token deny-list/invalidation are all `TODO(auth)`. See [`auth.md`](./auth.md).

5. **`api-contracts.md` location** — the signed contract lives at `frontend/.claude/artifacts/api-contracts.md` rather than the project-root `.claude/artifacts/`. Consolidate to `Matrix/.claude/artifacts/api-contracts.md` so all agents share the same source of truth.

6. **Scope enforcement is a stub** — `app/rbac/guards.py::require_scope` (line 32) is a pass-through with `TODO(auth)`. City and tenant scope checks must be implemented before going to prod. Until then, a `sub_supervisor` in Mumbai can read data for Chennai.

7. **Pre-existing cosmetic warning** — duplicate `marginTop` prop in `SiteDrawer.jsx`. Does not affect functionality; fix when convenient.

8. **`recipient_ids` are hardcoded placeholders** — every notification call in the routers uses `"supervisor-in-tenant"` or `"site-owner"` as placeholder IDs. After the `users` table is wired, replace with real queries: e.g. `SELECT id FROM users WHERE tenant_id=:tenant_id AND role='supervisor'` for supervisor notifications, and `SELECT created_by FROM sites WHERE id=:site_id` for exec notifications.
