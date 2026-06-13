"""Project Excellence service — budget tracking module that opens after project completion.

The module owns the 11-item budget review flow (moved from the project module).
It unlocks when sites.project_status = 'done'.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status as http_status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.db.session import transaction
from app.domain.schemas.common import OkResponse
from app.domain.schemas.project_excellence import (
    AdminBudgetReviewRequest,
    PEBudgetAdminQueueResponse,
    PEBudgetItemOut,
    PEDelegationsResponse,
    PEQueueItem,
    PEQueueResponse,
    PEStateResponse,
    ReviewRequest,
    SavePEBudgetRequest,
)
from app.services._common import fetch_site_or_404, fetch_user_name, fetch_user_names
from app.services.audit_service import write_audit_event
from app.services.delegation_service import svc_assigned_sites, svc_is_delegated


_BUDGET_LABELS = (
    "Professional Fees",
    "HVAC",
    "Furniture, Light & Planters",
    "Civil & Interiors",
    "Kitchen Equipment",
    "Branding",
    "Crockery & Small Equipments",
    "Utilities",
    "Licencing",
    "BD Cost",
    "Misc",
)


def _is_supervisor(actor: dict) -> bool:
    return (actor.get("role") or "").lower() == "supervisor"


def _is_business_admin(actor: dict) -> bool:
    return (actor.get("role") or "").lower() == "business_admin"


def _assert_pe_unlocked(site: models.Site) -> None:
    if (site.project_status or "pending") != "done":
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project Excellence is locked until the Project module is completed.",
        )


async def _active_pe_delegate(
    session: AsyncSession, *, site_id: str | UUID,
) -> Optional[tuple[UUID, str, str]]:
    row = (await session.execute(
        select(models.SiteDelegation.delegate_user_id, models.User.name, models.User.email)
        .join(models.User, models.User.id == models.SiteDelegation.delegate_user_id)
        .where(
            models.SiteDelegation.site_id == site_id,
            models.SiteDelegation.module == "project_excellence",
            models.SiteDelegation.revoked_at.is_(None),
        )
        .order_by(models.SiteDelegation.granted_at.desc())
        .limit(1)
    )).first()
    return (row[0], row[1], row[2]) if row else None


async def _fetch_review_or_none(
    session: AsyncSession, *, site_id: str | UUID,
) -> Optional[models.ProjectExcellenceReview]:
    return (await session.execute(
        select(models.ProjectExcellenceReview).where(
            models.ProjectExcellenceReview.site_id == site_id
        )
    )).scalar_one_or_none()


async def _fetch_review_or_create(
    session: AsyncSession, *, site: models.Site,
) -> models.ProjectExcellenceReview:
    review = await _fetch_review_or_none(session, site_id=site.id)
    if review is not None:
        return review
    review = models.ProjectExcellenceReview(
        tenant_id=site.tenant_id,
        site_id=site.id,
        excellence_status="pending",
        current_stage="budget",
        budget_status="draft",
    )
    session.add(review)
    await session.flush()
    return review


async def _budget_items(
    session: AsyncSession, *, site_id: str | UUID,
) -> list[models.ProjectExcellenceItem]:
    rows = (await session.execute(
        select(models.ProjectExcellenceItem)
        .where(models.ProjectExcellenceItem.site_id == site_id)
        .order_by(models.ProjectExcellenceItem.idx.asc())
    )).scalars().all()
    return list(rows)


def _budget_item_out(row: models.ProjectExcellenceItem) -> PEBudgetItemOut:
    return PEBudgetItemOut(
        id=str(row.id),
        idx=row.idx,
        label=row.label,
        amount=float(row.amount) if row.amount is not None else None,
    )


async def _batch_pe_prefetch(
    session: AsyncSession, sites: list[models.Site],
) -> tuple[dict, dict]:
    delegates: dict = {}
    names: dict = {}
    site_ids = [s.id for s in sites]
    if not site_ids:
        return delegates, names
    delegate_rows = (await session.execute(
        select(
            models.SiteDelegation.site_id,
            models.SiteDelegation.delegate_user_id,
            models.User.name,
            models.User.email,
        )
        .join(models.User, models.User.id == models.SiteDelegation.delegate_user_id)
        .where(
            models.SiteDelegation.site_id.in_(site_ids),
            models.SiteDelegation.module == "project_excellence",
            models.SiteDelegation.revoked_at.is_(None),
        )
        .order_by(models.SiteDelegation.granted_at.desc())
    )).all()
    for sid, uid, uname, uemail in delegate_rows:
        delegates.setdefault(sid, (uid, uname, uemail))
    submitter_ids = {s.submitted_by for s in sites if s.submitted_by}
    if submitter_ids:
        names = dict((await session.execute(
            select(models.User.id, models.User.name).where(models.User.id.in_(submitter_ids))
        )).all())
    return delegates, names


async def _queue_item(
    session: AsyncSession,
    site: models.Site,
    review: Optional[models.ProjectExcellenceReview],
    *,
    prefetched: Optional[dict] = None,
) -> PEQueueItem:
    if prefetched is None:
        delegate = await _active_pe_delegate(session, site_id=site.id)
        submitted_by_name = await fetch_user_name(session, site.submitted_by)
    else:
        delegate = prefetched.get("delegate")
        submitted_by_name = prefetched.get("submitted_by_name")
    return PEQueueItem(
        site_id=str(site.id),
        site_code=site.ca_code or site.code or "",
        site_name=site.name,
        city=site.city,
        project_status=site.project_status or "done",
        excellence_status=(review.excellence_status if review else "pending"),
        budget_status=(review.budget_status if review else "draft"),
        allocated_to_name=(delegate[1] if delegate else None),
        submitted_by_name=submitted_by_name,
        budget_total=float(review.budget_total) if review and review.budget_total is not None else None,
    )


async def _build_response(
    session: AsyncSession, site: models.Site, review: models.ProjectExcellenceReview,
) -> PEStateResponse:
    delegate = await _active_pe_delegate(session, site_id=site.id)
    items = await _budget_items(session, site_id=site.id)
    return PEStateResponse(
        site_id=str(site.id),
        site_code=site.ca_code or site.code or "",
        site_name=site.name,
        city=site.city,
        tenant_id=str(site.tenant_id),
        submitted_by_name=await fetch_user_name(session, site.submitted_by),
        site_status=site.status,
        project_status=site.project_status or "done",
        excellence_status=review.excellence_status,
        current_stage=review.current_stage,
        allocated_to=str(review.allocated_to) if review.allocated_to else None,
        allocated_to_name=(delegate[1] if delegate else None),
        budget_status=review.budget_status,
        budget_total=float(review.budget_total) if review.budget_total is not None else None,
        total_indoor_area_sqft=float(review.total_indoor_area_sqft) if review.total_indoor_area_sqft is not None else None,
        total_area_sqft=float(review.total_area_sqft) if review.total_area_sqft is not None else None,
        covers=int(review.covers) if review.covers is not None else None,
        budget_items=[_budget_item_out(item) for item in items],
        budget_supervisor_comments=review.budget_supervisor_comments,
        budget_admin_comments=review.budget_admin_comments,
        updated_at=review.updated_at,
    )


async def _assert_can_work_pe(
    session: AsyncSession,
    *,
    tenant_id: str | UUID,
    actor: dict,
    site_id: str | UUID,
) -> None:
    if _is_supervisor(actor):
        return
    if (actor.get("role") or "").lower() != "executive":
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Project Excellence access denied.")
    allowed = await svc_is_delegated(
        session,
        tenant_id=tenant_id,
        site_id=site_id,
        user_id=actor["sub"],
        module="project_excellence",
    )
    if not allowed:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Executive is not allocated to this Project Excellence site.",
        )


async def svc_pe_queue(
    session: AsyncSession,
    *,
    tenant_id: str | UUID,
    restrict_to_site_ids: Optional[list[str]] = None,
) -> PEQueueResponse:
    async with transaction(session):
        stmt = (
            select(models.Site, models.ProjectExcellenceReview)
            .outerjoin(
                models.ProjectExcellenceReview,
                models.ProjectExcellenceReview.site_id == models.Site.id,
            )
            .where(
                models.Site.tenant_id == tenant_id,
                models.Site.project_status == "done",
            )
        )
        if restrict_to_site_ids is not None:
            if not restrict_to_site_ids:
                return PEQueueResponse(items=[], total=0)
            stmt = stmt.where(models.Site.id.in_(restrict_to_site_ids))
        rows = (await session.execute(stmt.order_by(models.Site.updated_at.asc()))).all()

        delegates, names = await _batch_pe_prefetch(session, [site for site, _r in rows])
        items: list[PEQueueItem] = []
        for site, review in rows:
            items.append(await _queue_item(
                session, site, review,
                prefetched={
                    "delegate": delegates.get(site.id),
                    "submitted_by_name": names.get(site.submitted_by, ""),
                },
            ))
        return PEQueueResponse(items=items, total=len(items))


async def svc_get_pe(
    session: AsyncSession, *, tenant_id: str | UUID, site_id: str | UUID,
) -> PEStateResponse:
    async with transaction(session):
        site = await fetch_site_or_404(session, site_id=site_id, tenant_id=tenant_id)
        _assert_pe_unlocked(site)
        review = await _fetch_review_or_create(session, site=site)
        return await _build_response(session, site, review)


async def svc_list_pe_delegations_for_site(
    session: AsyncSession, *, tenant_id: str | UUID, site_id: str | UUID,
) -> dict:
    stmt = (
        select(models.SiteDelegation, models.User.email, models.User.name)
        .join(models.User, models.User.id == models.SiteDelegation.delegate_user_id)
        .where(
            models.SiteDelegation.site_id == site_id,
            models.SiteDelegation.tenant_id == tenant_id,
            models.SiteDelegation.module == "project_excellence",
            models.SiteDelegation.revoked_at.is_(None),
        )
        .order_by(models.SiteDelegation.granted_at.desc())
    )
    rows = (await session.execute(stmt)).all()
    return {
        "items": [
            {
                "id": str(row.id),
                "site_id": str(row.site_id),
                "module": row.module,
                "delegate_user_id": str(row.delegate_user_id),
                "delegate_email": email,
                "delegate_name": name,
                "granted_by": str(row.granted_by),
                "granted_at": row.granted_at,
                "notes": row.notes,
            }
            for (row, email, name) in rows
        ],
        "total": len(rows),
    }


async def svc_allocate_pe(
    session: AsyncSession,
    *,
    tenant_id: str | UUID,
    actor: dict,
    site_id: str | UUID,
    delegate_user_id: str | UUID,
    notes: Optional[str] = None,
) -> PEStateResponse:
    if not _is_supervisor(actor):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Only a project excellence supervisor can allocate.")
    if str(delegate_user_id) == str(actor["sub"]):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Cannot allocate to yourself.")

    async with transaction(session):
        site = await fetch_site_or_404(session, site_id=site_id, tenant_id=tenant_id)
        _assert_pe_unlocked(site)
        delegate = (await session.execute(
            select(models.User).where(
                models.User.id == delegate_user_id,
                models.User.tenant_id == tenant_id,
                models.User.is_active.is_(True),
            )
        )).scalar_one_or_none()
        if delegate is None or (delegate.role or "").lower() != "executive":
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Active executive not found.")
        existing = (await session.execute(
            select(models.SiteDelegation).where(
                models.SiteDelegation.site_id == site.id,
                models.SiteDelegation.module == "project_excellence",
                models.SiteDelegation.delegate_user_id == delegate_user_id,
                models.SiteDelegation.revoked_at.is_(None),
            )
        )).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail="Project Excellence allocation already exists.")

        row = models.SiteDelegation(
            tenant_id=tenant_id,
            site_id=site.id,
            module="project_excellence",
            delegate_user_id=delegate_user_id,
            granted_by=actor["sub"],
            notes=(notes or "").strip() or None,
        )
        session.add(row)
        review = await _fetch_review_or_create(session, site=site)
        review.allocated_to = delegate.id
        review.excellence_status = "allocated"
        review.current_stage = "budget"
        site.project_excellence_status = "allocated"
        await write_audit_event(
            session,
            tenant_id=tenant_id,
            site_id=site.id,
            actor_id=actor["sub"],
            actor_name=actor.get("name"),
            action="pe_allocated",
            detail=f"delegate={delegate.email}",
        )
        return await _build_response(session, site, review)


async def svc_revoke_pe_delegation(
    session: AsyncSession,
    *,
    tenant_id: str | UUID,
    actor: dict,
    site_id: str | UUID,
    delegate_user_id: str | UUID,
) -> OkResponse:
    if not _is_supervisor(actor):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Only a project excellence supervisor can revoke.")
    from datetime import datetime, timezone
    async with transaction(session):
        row = (await session.execute(
            select(models.SiteDelegation).where(
                models.SiteDelegation.tenant_id == tenant_id,
                models.SiteDelegation.site_id == site_id,
                models.SiteDelegation.module == "project_excellence",
                models.SiteDelegation.delegate_user_id == delegate_user_id,
                models.SiteDelegation.revoked_at.is_(None),
            )
        )).scalar_one_or_none()
        if row is None:
            return OkResponse(message="No active project excellence allocation to revoke.")
        row.revoked_at = datetime.now(timezone.utc)
        row.revoked_by = actor["sub"]
        await write_audit_event(
            session,
            tenant_id=tenant_id,
            site_id=row.site_id,
            actor_id=actor["sub"],
            actor_name=actor.get("name"),
            action="pe_allocation_revoked",
        )
    return OkResponse(message="Project Excellence allocation revoked.")


async def svc_save_pe_budget(
    session: AsyncSession,
    *,
    tenant_id: str | UUID,
    actor: dict,
    site_id: str | UUID,
    body: SavePEBudgetRequest,
) -> PEStateResponse:
    async with transaction(session):
        site = await fetch_site_or_404(session, site_id=site_id, tenant_id=tenant_id)
        _assert_pe_unlocked(site)
        await _assert_can_work_pe(session, tenant_id=tenant_id, actor=actor, site_id=site.id)
        review = await _fetch_review_or_create(session, site=site)
        if review.budget_status not in {"draft", "rejected"}:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Budget is already {review.budget_status}.",
            )

        labels = {item.idx: (item.label or _BUDGET_LABELS[item.idx - 1]) for item in body.items}
        amounts = {item.idx: item.amount for item in body.items}
        await session.execute(
            delete(models.ProjectExcellenceItem).where(models.ProjectExcellenceItem.site_id == site.id)
        )
        total = 0.0
        for idx in range(1, len(_BUDGET_LABELS) + 1):
            amount = amounts.get(idx)
            if amount is not None:
                total += float(amount)
            session.add(models.ProjectExcellenceItem(
                tenant_id=tenant_id,
                site_id=site.id,
                idx=idx,
                label=labels.get(idx, _BUDGET_LABELS[idx - 1]),
                amount=amount,
            ))
        review.budget_total = total
        review.total_indoor_area_sqft = body.total_indoor_area_sqft
        review.total_area_sqft = body.total_area_sqft
        review.covers = body.covers
        review.excellence_status = "budgeting"
        site.project_excellence_status = "budgeting"
        if body.action == "submit":
            review.budget_status = "pending_admin" if _is_supervisor(actor) else "pending_supervisor"
        else:
            review.budget_status = "draft"
        await write_audit_event(
            session,
            tenant_id=tenant_id,
            site_id=site.id,
            actor_id=actor["sub"],
            actor_name=actor.get("name"),
            action="pe_budget_saved" if body.action == "save" else "pe_budget_submitted",
            detail=f"total={total} status={review.budget_status}",
        )
        await session.flush()
        return await _build_response(session, site, review)


async def svc_review_pe_budget(
    session: AsyncSession,
    *,
    tenant_id: str | UUID,
    actor: dict,
    site_id: str | UUID,
    body: ReviewRequest,
) -> PEStateResponse:
    if not _is_supervisor(actor):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Only a project excellence supervisor can review budgets.")
    async with transaction(session):
        site = await fetch_site_or_404(session, site_id=site_id, tenant_id=tenant_id)
        review = await _fetch_review_or_create(session, site=site)
        if review.budget_status != "pending_supervisor":
            raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Budget is not awaiting supervisor.")
        if body.decision == "approve":
            review.budget_status = "pending_admin"
        else:
            review.budget_status = "rejected"
            review.budget_supervisor_comments = (body.comments or "").strip() or "Rejected by supervisor."
        await write_audit_event(
            session,
            tenant_id=tenant_id,
            site_id=site.id,
            actor_id=actor["sub"],
            actor_name=actor.get("name"),
            action="pe_budget_supervisor_reviewed",
            detail=f"decision={body.decision}",
        )
        return await _build_response(session, site, review)


async def svc_pe_budget_admin_queue(
    session: AsyncSession, *, tenant_id: str | UUID,
) -> PEBudgetAdminQueueResponse:
    rows = (await session.execute(
        select(models.Site, models.ProjectExcellenceReview)
        .join(models.ProjectExcellenceReview, models.ProjectExcellenceReview.site_id == models.Site.id)
        .where(
            models.Site.tenant_id == tenant_id,
            models.ProjectExcellenceReview.budget_status == "pending_admin",
        )
        .order_by(models.ProjectExcellenceReview.updated_at.asc())
    )).all()
    delegates, names = await _batch_pe_prefetch(session, [site for site, _r in rows])
    items = [
        await _queue_item(session, site, review, prefetched={
            "delegate": delegates.get(site.id),
            "submitted_by_name": names.get(site.submitted_by, ""),
        })
        for (site, review) in rows
    ]
    return PEBudgetAdminQueueResponse(items=items, total=len(items))


async def svc_admin_review_pe_budget(
    session: AsyncSession,
    *,
    tenant_id: str | UUID,
    actor: dict,
    site_id: str | UUID,
    body: AdminBudgetReviewRequest,
) -> PEStateResponse:
    if not _is_business_admin(actor):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Only a business admin can review project excellence budgets.")
    async with transaction(session):
        site = await fetch_site_or_404(session, site_id=site_id, tenant_id=tenant_id)
        review = await _fetch_review_or_create(session, site=site)
        if review.budget_status != "pending_admin":
            raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Budget is not awaiting admin.")
        if body.decision == "approve":
            review.budget_status = "approved"
            review.excellence_status = "approved"
            review.current_stage = "done"
            site.project_excellence_status = "approved"
        else:
            review.budget_status = "rejected"
            review.budget_admin_comments = (body.comments or "").strip() or "Rejected by business admin."
        await write_audit_event(
            session,
            tenant_id=tenant_id,
            site_id=site.id,
            actor_id=actor["sub"],
            actor_name=actor.get("name"),
            action="pe_budget_admin_reviewed",
            detail=f"decision={body.decision}",
        )
        return await _build_response(session, site, review)


async def svc_get_pe_budget_admin_detail(
    session: AsyncSession, *, tenant_id: str | UUID, site_id: str | UUID,
) -> PEStateResponse:
    site = await fetch_site_or_404(session, site_id=site_id, tenant_id=tenant_id)
    review = await _fetch_review_or_none(session, site_id=site.id)
    if review is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Project Excellence budget details are not available for this site.",
        )
    return await _build_response(session, site, review)
