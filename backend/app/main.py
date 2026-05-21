"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, bd, loi, staging, sites, audit, notifications, tenancy, users

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all domain routers under /api prefix
for router_module in [auth, bd, loi, staging, sites, audit, notifications, tenancy, users]:
    app.include_router(router_module.router, prefix=settings.api_prefix)


@app.get("/api/health")
async def health() -> dict:
    """Health check."""
    return {"status": "ok", "version": "0.1.0"}
