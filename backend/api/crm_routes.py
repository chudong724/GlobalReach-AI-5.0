from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api.security import require_api_access
from crm.store import CRMStore, csv_template
from tools.email_verifier import EmailVerifierTool

router = APIRouter(prefix="/api/v1/crm", tags=["CRM"], dependencies=[Depends(require_api_access)])
_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "crm.db"
store = CRMStore(str(_DB_PATH))


class ContactPayload(BaseModel):
    id: str | None = None
    company_name: str = ""
    contact_name: str = ""
    job_title: str = ""
    email: str = ""
    phone: str = ""
    website: str = ""
    country: str = ""
    city: str = ""
    linkedin: str = ""
    source: str = ""
    status: str = "new"
    priority: str = "normal"
    notes: str = ""
    deal_stage: str = "new"
    lead_score: int | None = None
    email_verification: str = "unknown"
    last_contacted_at: str = ""
    next_follow_up_at: str = ""


class IdsPayload(BaseModel):
    ids: list[str] = Field(default_factory=list)


@router.get("/contacts")
def list_contacts(search: str = "", limit: int = 1000, stage: str = "") -> dict[str, Any]:
    contacts = store.list_contacts(search=search, limit=limit, stage=stage)
    return {"items": contacts, "count": len(contacts)}


@router.post("/contacts")
def save_contact(payload: ContactPayload) -> dict[str, Any]:
    if not (payload.company_name.strip() or payload.email.strip() or payload.website.strip()):
        raise HTTPException(status_code=400, detail="company_name, email or website is required")
    return store.upsert_contact(payload.model_dump())


@router.post("/contacts/delete-many")
def delete_many(payload: IdsPayload) -> dict[str, int]:
    return {"deleted": store.delete_many(payload.ids)}


@router.post("/contacts/rescore")
def rescore(payload: IdsPayload) -> dict[str, int]:
    return {"rescored": store.rescore(payload.ids or None)}


@router.post("/contacts/verify-email")
async def verify_email(payload: IdsPayload) -> dict[str, Any]:
    contacts = store.get_contacts(payload.ids)
    targets = [(c["id"], str(c.get("email") or "").strip()) for c in contacts if str(c.get("email") or "").strip()]
    verifier = EmailVerifierTool()
    results = await verifier.verify_batch([email for _, email in targets]) if targets else []
    verified = 0
    details = []
    for (contact_id, email), result in zip(targets, results):
        status = "valid" if result.get("is_deliverable") else "invalid"
        store.update_email_verification(contact_id, status)
        verified += 1
        details.append({"id": contact_id, "email": email, "status": status, "mx_records": result.get("mx_records", [])})
    return {"verified": verified, "items": details}


@router.get("/pipeline")
def pipeline_summary() -> dict[str, Any]:
    return store.pipeline_summary()


@router.post("/import")
async def import_csv(file: UploadFile = File(...)) -> dict[str, int]:
    if not str(file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV file required")
    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV file too large")
    return store.import_csv(raw)


@router.get("/export")
def export_csv() -> Response:
    data = store.export_csv().encode("utf-8")
    return Response(content=data, media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=wenmei-crm-export.csv"})


@router.get("/template")
def download_template() -> Response:
    data = csv_template().encode("utf-8")
    return Response(content=data, media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=wenmei-crm-import-template.csv"})


def register_crm_routes(target_router: APIRouter) -> None:
    target_router.include_router(router)
