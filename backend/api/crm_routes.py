from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api.security import require_api_access
from crm.automation import suggested_follow_up_date
from crm.store import CRMStore, csv_template
from tools.email_verifier import EmailVerifierTool
from tools.llm_client import LLMTool

router = APIRouter(prefix="/api/v1/crm", tags=["CRM"], dependencies=[Depends(require_api_access)])
_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "crm.db"
store = CRMStore(str(_DB_PATH))


class ContactPayload(BaseModel):
    id: str | None = None
    company_name: str = ""; contact_name: str = ""; job_title: str = ""; email: str = ""; phone: str = ""; website: str = ""; country: str = ""; city: str = ""; linkedin: str = ""; source: str = ""; status: str = "new"; priority: str = "normal"; notes: str = ""; deal_stage: str = "new"; lead_score: int | None = None; email_verification: str = "unknown"; last_contacted_at: str = ""; next_follow_up_at: str = ""


class IdsPayload(BaseModel):
    ids: list[str] = Field(default_factory=list)


class SalesStatePayload(BaseModel):
    deal_stage: str | None = None
    next_follow_up_at: str | None = None
    mark_contacted: bool = False
    note: str = ""


class ActivityPayload(BaseModel):
    activity_type: str = "note"
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


def _clean_json(text: str) -> dict[str, Any]:
    raw = str(text or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {"summary": raw}
    except Exception:
        return {"summary": raw}


@router.get("/contacts")
def list_contacts(search: str = "", limit: int = 1000, stage: str = "") -> dict[str, Any]:
    contacts = store.list_contacts(search=search, limit=limit, stage=stage)
    return {"items": contacts, "count": len(contacts)}


@router.get("/contacts/{contact_id}")
def get_contact(contact_id: str) -> dict[str, Any]:
    item = store.get_contact(contact_id)
    if not item: raise HTTPException(status_code=404, detail="Contact not found")
    return {"contact": item, "activities": store.list_activities(contact_id)}


@router.post("/contacts")
def save_contact(payload: ContactPayload) -> dict[str, Any]:
    if not (payload.company_name.strip() or payload.email.strip() or payload.website.strip()):
        raise HTTPException(status_code=400, detail="company_name, email or website is required")
    item = store.upsert_contact(payload.model_dump())
    store.add_activity(item["id"], "contact_updated", "客户资料已保存")
    return item


@router.post("/contacts/{contact_id}/sales-state")
def update_sales_state(contact_id: str, payload: SalesStatePayload) -> dict[str, Any]:
    current = store.get_contact(contact_id)
    if not current: raise HTTPException(status_code=404, detail="Contact not found")
    item = store.update_sales_state(contact_id, deal_stage=payload.deal_stage, next_follow_up_at=payload.next_follow_up_at, mark_contacted=payload.mark_contacted)
    if payload.deal_stage and payload.deal_stage != current.get("deal_stage"):
        store.add_activity(contact_id, "stage_changed", f"销售阶段：{current.get('deal_stage','new')} → {payload.deal_stage}")
    if payload.next_follow_up_at:
        store.add_activity(contact_id, "follow_up_scheduled", f"下次跟进：{payload.next_follow_up_at}")
    if payload.mark_contacted:
        store.add_activity(contact_id, "contacted", payload.note or "已联系客户")
    elif payload.note:
        store.add_activity(contact_id, "note", payload.note)
    return item or {}


@router.get("/contacts/{contact_id}/activities")
def activities(contact_id: str) -> dict[str, Any]:
    return {"items": store.list_activities(contact_id)}


@router.post("/contacts/{contact_id}/activities")
def add_activity(contact_id: str, payload: ActivityPayload) -> dict[str, Any]:
    if not store.get_contact(contact_id): raise HTTPException(status_code=404, detail="Contact not found")
    return store.add_activity(contact_id, payload.activity_type, payload.content, payload.metadata)


@router.post("/contacts/{contact_id}/ai-sales-plan")
async def ai_sales_plan(contact_id: str) -> dict[str, Any]:
    contact = store.get_contact(contact_id)
    if not contact: raise HTTPException(status_code=404, detail="Contact not found")
    prompt = f"""你是资深B2B外贸销售顾问。请基于以下客户资料，为销售人员生成可立即执行的销售计划。\n客户资料：{json.dumps(contact, ensure_ascii=False)}\n请只返回JSON对象，字段必须包括：rating_reason（为什么值得/不值得跟进，中文，80字内）、buyer_hypothesis（客户可能采购需求）、next_action（下一步动作）、negotiation_strategy（谈判策略，3点以内）、email_subject（英文开发信主题）、email_body（英文开发信正文，120-180词，专业、非垃圾邮件风格）、follow_up_days（建议几天后跟进，整数1-14）、risk_flags（字符串数组）。不要虚构未提供的认证、价格、产能或客户事实。"""
    llm = LLMTool(model_type="reasoning", agent="crm_sales_advisor")
    text = await llm.generate(prompt, system="Return valid JSON only. Be evidence-grounded and concise.", temperature=0.2, max_tokens=1800, response_format={"type":"json_object"})
    plan = _clean_json(text)
    try: days = max(1, min(14, int(plan.get("follow_up_days", 3))))
    except Exception: days = 3
    follow_up_at = suggested_follow_up_date(days)
    store.update_sales_state(contact_id, next_follow_up_at=follow_up_at)
    store.add_activity(contact_id, "ai_sales_plan", "AI 已生成客户评级、开发信与谈判/跟进策略", metadata={"plan": plan, "next_follow_up_at": follow_up_at})
    return {"plan": plan, "next_follow_up_at": follow_up_at}


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
    verifier = EmailVerifierTool(); results = await verifier.verify_batch([email for _, email in targets]) if targets else []
    details=[]
    for (contact_id,email), result in zip(targets,results):
        status = "valid" if result.get("is_deliverable") else "invalid"; store.update_email_verification(contact_id,status); store.add_activity(contact_id,"email_verified",f"邮箱验证：{email} → {status}",metadata={"mx_records":result.get("mx_records",[])}); details.append({"id":contact_id,"email":email,"status":status,"mx_records":result.get("mx_records",[])})
    return {"verified":len(details),"items":details}


@router.get("/pipeline")
def pipeline_summary() -> dict[str, Any]: return store.pipeline_summary()


@router.get("/follow-ups/due")
def due_follow_ups(limit: int = 100) -> dict[str, Any]:
    items=store.due_follow_ups(limit); return {"items":items,"count":len(items)}


@router.post("/import")
async def import_csv(file: UploadFile = File(...)) -> dict[str, int]:
    if not str(file.filename or "").lower().endswith(".csv"): raise HTTPException(status_code=400,detail="CSV file required")
    raw=await file.read()
    if len(raw)>10*1024*1024: raise HTTPException(status_code=413,detail="CSV file too large")
    return store.import_csv(raw)


@router.get("/export")
def export_csv() -> Response:
    return Response(content=store.export_csv().encode("utf-8"),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":"attachment; filename=wenmei-crm-export.csv"})


@router.get("/template")
def download_template() -> Response:
    return Response(content=csv_template().encode("utf-8"),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":"attachment; filename=wenmei-crm-import-template.csv"})


def register_crm_routes(target_router: APIRouter) -> None: target_router.include_router(router)
