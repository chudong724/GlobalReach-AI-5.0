from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.security import require_api_access
from crm.store import CRMStore
from tools.contact_intelligence import discover_contact_emails

router = APIRouter(prefix="/api/v1/contact-intelligence", tags=["Contact Intelligence"], dependencies=[Depends(require_api_access)])
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
crm_store = CRMStore(str(_BACKEND_ROOT / "data" / "crm.db"))


class DiscoverPayload(BaseModel):
    website: str
    contact_name: str = ""
    company_name: str = ""
    contact_id: str = ""


class ApplyPayload(BaseModel):
    contact_id: str
    email: str
    confidence: int = 0
    source_type: str = ""
    status: str = ""


@router.post("/discover")
async def discover(payload: DiscoverPayload) -> dict[str, Any]:
    website = payload.website.strip()
    contact_name = payload.contact_name.strip()
    company_name = payload.company_name.strip()
    if payload.contact_id.strip():
        contact = crm_store.get_contact(payload.contact_id.strip())
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        website = website or str(contact.get("website") or "")
        contact_name = contact_name or str(contact.get("contact_name") or "")
        company_name = company_name or str(contact.get("company_name") or "")
    if not website:
        raise HTTPException(status_code=400, detail="website is required")
    result = await discover_contact_emails(website, contact_name=contact_name, company_name=company_name)
    if payload.contact_id.strip():
        crm_store.add_activity(payload.contact_id.strip(), "contact_intelligence", "已运行联系人邮箱情报瀑布流", metadata={"candidate_count": len(result.get("candidates") or []), "domain": result.get("domain")})
    return result


@router.post("/apply")
def apply_candidate(payload: ApplyPayload) -> dict[str, Any]:
    contact = crm_store.get_contact(payload.contact_id.strip())
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="valid email is required")
    updated = dict(contact)
    updated["email"] = email
    updated["email_verification"] = "valid" if payload.status in {"public+mx", "hunter-fallback"} else "unknown"
    saved = crm_store.upsert_contact(updated)
    crm_store.add_activity(saved["id"], "email_selected", f"联系人邮箱已确认：{email}", metadata={"confidence": payload.confidence, "source_type": payload.source_type, "status": payload.status})
    return saved


def register_contact_intelligence_routes(target_router: APIRouter) -> None:
    target_router.include_router(router)
