from __future__ import annotations

from pathlib import Path

from crm.store import CRMStore

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_store = CRMStore(str(_BACKEND_ROOT / "data" / "crm.db"))


def record_email_sent(email: str, *, subject: str = "", sent_at: str = "", step_number: int = 1) -> None:
    contact = _store.find_contact_by_email(email)
    if not contact:
        return
    stage = str(contact.get("deal_stage") or "new")
    next_stage = "contacted" if stage in {"new", "qualified"} else stage
    _store.update_sales_state(contact["id"], deal_stage=next_stage, mark_contacted=True)
    _store.add_activity(
        contact["id"],
        "email_sent",
        f"已发送第 {step_number} 封邮件" + (f"：{subject}" if subject else ""),
        metadata={"sent_at": sent_at, "step_number": step_number},
    )


def record_email_reply(email: str, *, subject: str = "", snippet: str = "", received_at: str = "") -> None:
    contact = _store.find_contact_by_email(email)
    if not contact:
        return
    stage = str(contact.get("deal_stage") or "new")
    next_stage = "replied" if stage not in {"won", "lost", "negotiating"} else stage
    _store.update_sales_state(contact["id"], deal_stage=next_stage, next_follow_up_at="")
    content = "客户邮件回复"
    if subject:
        content += f"：{subject}"
    _store.add_activity(
        contact["id"],
        "email_reply",
        content,
        metadata={"received_at": received_at, "snippet": snippet[:1000]},
    )
