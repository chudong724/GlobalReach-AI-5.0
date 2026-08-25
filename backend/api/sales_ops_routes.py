from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends

from api.security import require_api_access
from config.settings import get_settings
from crm.store import CRMStore
from emailing.store import EmailStore

router = APIRouter(prefix="/api/v1/sales-ops", tags=["Sales Operations"], dependencies=[Depends(require_api_access)])
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
crm_store = CRMStore(str(_BACKEND_ROOT / "data" / "crm.db"))


def _email_store() -> EmailStore:
    settings = get_settings()
    store = EmailStore(str(settings.email_db_path))
    store.init_db()
    return store


@router.get("/summary")
def summary() -> dict[str, Any]:
    crm = crm_store.sales_operations_summary()
    email = _email_store()
    email_summary = {
        "pending_messages": email.count_messages_by_status("pending"),
        "sent_messages": email.count_messages_by_status("sent"),
        "failed_messages": email.count_messages_by_status("failed"),
        "running_sequences": email.count_sequences_by_status("running", "active", "pending"),
        "replied_sequences": email.count_sequences_by_status("replied"),
        "stopped_sequences": email.count_sequences_by_status("stopped"),
    }
    return {"crm": crm, "email": email_summary}


@router.get("/daily-worklist")
def daily_worklist(limit: int = 100) -> dict[str, Any]:
    contacts = crm_store.list_contacts(limit=5000)
    due = crm_store.due_follow_ups(limit=limit)
    due_ids = {x["id"] for x in due}
    high_priority_new = [
        x for x in contacts
        if x.get("id") not in due_ids
        and str(x.get("deal_stage") or "new") in {"new", "qualified"}
        and int(x.get("lead_score") or 0) >= 70
    ][: max(0, limit - len(due))]
    replied = [
        x for x in contacts
        if str(x.get("deal_stage") or "") == "replied" and x.get("id") not in due_ids
    ][:20]
    tasks = []
    for item in due:
        tasks.append({"type":"follow_up_due","priority":"high","contact":item,"reason":"已到计划跟进时间"})
    for item in replied:
        tasks.append({"type":"reply_review","priority":"high","contact":item,"reason":"客户已回复，建议人工查看并推进谈判"})
    for item in high_priority_new:
        tasks.append({"type":"high_score_new","priority":"normal","contact":item,"reason":"高评分新客户，建议优先生成销售计划并联系"})
    return {"items": tasks[:limit], "count": min(len(tasks), limit)}


def register_sales_ops_routes(target_router: APIRouter) -> None:
    target_router.include_router(router)
