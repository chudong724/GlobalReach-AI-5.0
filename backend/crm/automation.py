from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from crm.store import CRMStore


def _pick_first(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0] if value else "").strip()
    return str(value or "").strip()


def lead_to_contact(lead: dict[str, Any], *, source: str = "AI Hunt") -> dict[str, Any]:
    emails = lead.get("emails") or lead.get("email") or []
    phones = lead.get("phones") or lead.get("phone") or []
    contact = {
        "company_name": lead.get("company_name") or lead.get("name") or "",
        "contact_name": lead.get("contact_name") or lead.get("decision_maker") or "",
        "job_title": lead.get("job_title") or lead.get("title") or "",
        "email": _pick_first(emails),
        "phone": _pick_first(phones),
        "website": lead.get("website") or lead.get("url") or "",
        "country": lead.get("country") or "",
        "city": lead.get("city") or "",
        "linkedin": lead.get("linkedin") or lead.get("linkedin_url") or "",
        "source": source,
        "status": "new",
        "priority": "normal",
        "notes": str(lead.get("summary") or lead.get("evidence") or "")[:1500],
        "deal_stage": "new",
        "email_verification": "unknown",
    }
    fit = lead.get("fit_score") or lead.get("score")
    if isinstance(fit, (int, float)):
        contact["priority"] = "high" if float(fit) >= 0.75 else "normal"
    return contact


def sync_hunt_leads(store: CRMStore, leads: list[dict[str, Any]], *, hunt_id: str = "") -> dict[str, int]:
    imported = skipped = 0
    source = f"AI Hunt {hunt_id[:8]}" if hunt_id else "AI Hunt"
    for lead in leads or []:
        if not isinstance(lead, dict):
            skipped += 1
            continue
        contact = lead_to_contact(lead, source=source)
        if not (contact["company_name"] or contact["email"] or contact["website"]):
            skipped += 1
            continue
        saved = store.upsert_contact(contact)
        store.add_activity(saved["id"], "lead_discovered", f"获客任务自动入库：{source}", metadata={"hunt_id": hunt_id})
        imported += 1
    return {"imported": imported, "skipped": skipped}


def suggested_follow_up_date(days: int = 3) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=max(1, days))).isoformat()
