from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crm.store import CRMStore
from tools.llm_client import LLMTool

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_store = CRMStore(str(_BACKEND_ROOT / "data" / "crm.db"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_json(text: str) -> dict[str, Any]:
    raw = str(text or "").strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {"summary": raw}
    except Exception:
        return {"summary": raw}


async def analyze_reply_intent(contact_id: str, reply_text: str, subject: str = "") -> dict[str, Any]:
    contact = _store.get_contact(contact_id)
    if not contact:
        return {"error": "contact_not_found"}
    prompt = f"""You are a B2B export sales assistant. Analyze this customer reply and return JSON only.
Customer: {json.dumps(contact, ensure_ascii=False)}
Subject: {subject}
Reply: {reply_text[:4000]}
Return fields: intent (interested|needs_info|price_request|sample_request|negotiation|not_interested|out_of_scope|unclear), sentiment (positive|neutral|negative), urgency (high|medium|low), recommended_stage, next_action, reply_subject, reply_body, risk_flags (array). Do not invent product facts, prices, certifications, MOQ or lead times. This is a draft only; never send automatically."""
    llm = LLMTool(model_type="reasoning", agent="crm_reply_intent")
    text = await llm.generate(prompt, system="Return valid JSON only. Evidence-grounded. Draft only, do not send.", temperature=0.2, max_tokens=1800, response_format={"type":"json_object"})
    result = _parse_json(text)
    _store.add_activity(contact_id, "ai_reply_analysis", "AI 已分析客户回复意图并生成回复建议", metadata={"analysis": result, "subject": subject, "reply_text": reply_text[:4000], "created_at": _now()})
    stage = str(result.get("recommended_stage") or "").strip()
    if stage in {"replied", "negotiating", "won", "lost"}:
        _store.update_sales_state(contact_id, deal_stage=stage)
    return result


def forecast_snapshot() -> dict[str, Any]:
    summary = _store.sales_operations_summary()
    stages = summary.get("stages", {}) or {}
    weighted_units = (
        stages.get("new", 0) * 0.05
        + stages.get("qualified", 0) * 0.15
        + stages.get("contacted", 0) * 0.25
        + stages.get("replied", 0) * 0.45
        + stages.get("negotiating", 0) * 0.70
        + stages.get("won", 0) * 1.0
    )
    return {
        "stage_counts": stages,
        "weighted_opportunity_units": round(float(weighted_units), 2),
        "contact_rate": summary.get("contact_rate", 0.0),
        "reply_rate": summary.get("reply_rate", 0.0),
        "win_rate": summary.get("win_rate", 0.0),
        "generated_at": _now(),
        "note": "Forecast is a weighted pipeline health indicator, not revenue guidance."
    }
