"""LOI service functions — extracted from loi router so sites alias can call them."""
from datetime import date
from typing import Optional

from app.domain.state_machine import SiteStatus
from app.domain.schemas.loi import LOIUploadResponse
from app.services.audit_service import write_audit_event
from app.services.notification_service import send as notify


async def svc_upload_loi(
    db,
    *,
    site_id: str,
    actor: str,
    file_bytes: Optional[bytes] = None,
    filename: Optional[str] = None,
) -> LOIUploadResponse:
    """Core logic for approved -> loi_uploaded.

    Called by loi.upload_loi and sites.upload_loi_alias.
    """
    # TODO(db): update sites set status=loi_uploaded, loi_uploaded_at=now() where id=site_id
    # TODO(storage): store file_bytes in S3/GCS; save URL to site_documents
    await write_audit_event(
        db,
        site_id=site_id,
        actor=actor,
        action="upload_loi",
        from_status=SiteStatus.APPROVED,
        to_status=SiteStatus.LOI_UPLOADED,
    )
    await notify(
        event="loi_uploaded",
        recipient_ids=["supervisor-in-tenant"],
        channels=["email", "slack", "in_app"],
        payload={"site_id": site_id},
    )
    return LOIUploadResponse(
        site_id=site_id,
        loi_uploaded=True,
        loi_uploaded_at=date.today(),
        days_to_loi=0,
    )
