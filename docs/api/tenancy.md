# Tenancy

Router file: `backend/app/routers/tenancy.py`  
Prefix: `/api/tenancy`  
Tag: `Tenancy`

Routes sorted by path, then method.

---

### `GET /api/tenancy/cities`

**Handler**: `app.routers.tenancy:list_cities`  
**Role required**: `executive` | `supervisor` | `sub_supervisor`  
**Scope**: `tenant`  
**Touches**: reads → `[sites]`, writes → `[]`  
**Side effects**: none

Returns all distinct city names that have active sites within the current tenant. Used to populate city filter dropdowns.

**Response** — inline `dict` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `cities` | `str[]` | distinct city names; stub returns hardcoded list |

The stub returns: `["Mumbai", "Bengaluru", "New Delhi", "Hyderabad", "Pune", "Chennai", "Ahmedabad"]`

**TODO markers** (`backend/app/routers/tenancy.py`)

- Line 37: `# TODO(db): SELECT DISTINCT city FROM sites WHERE tenant_id=tenant_id`

**Frontend caller**: no direct caller in `frontend/src/services/api/`. Not yet wired.

**Example**

```bash
curl http://localhost:8000/api/tenancy/cities \
  -H "Authorization: Bearer <token>"
```

---

### `GET /api/tenancy/tenants`

**Handler**: `app.routers.tenancy:list_tenants`  
**Role required**: `supervisor`  
**Scope**: `tenant`  
**Touches**: reads → `[tenants]`, writes → `[]`  
**Side effects**: none

Returns all tenants accessible to the current supervisor.

**Response** — inline `dict` (HTTP `200`)

| field | type | notes |
| ----- | ---- | ----- |
| `items` | `list` | tenant objects — shape TBD once DB is wired |
| `total` | `int` | — |

**Errors**

- `403` — caller role is not `supervisor`

**TODO markers** (`backend/app/routers/tenancy.py`)

- Line 22: `# TODO(db): SELECT * FROM tenants WHERE id IN (supervisor's accessible tenants)`

**Frontend caller**: no direct caller in `frontend/src/services/api/`. Not yet wired.

**Example**

```bash
curl http://localhost:8000/api/tenancy/tenants \
  -H "Authorization: Bearer <token>"
```
