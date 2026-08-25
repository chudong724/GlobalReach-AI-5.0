from __future__ import annotations

import re
from typing import Any

ROLE_WEIGHTS = {
    "owner": 100,
    "procurement": 96,
    "sourcing": 94,
    "product": 88,
    "business_development": 84,
    "engineering": 82,
    "rd": 82,
    "operations": 76,
    "sales": 68,
    "marketing": 58,
    "other": 40,
}

ROLE_PATTERNS = [
    ("owner", r"\b(founder|co-founder|owner|chief executive officer|ceo|president|managing director|general manager)\b"),
    ("procurement", r"\b(procurement|purchasing|buyer|buying|purchase manager|procurement manager|purchasing manager|category manager)\b"),
    ("sourcing", r"\b(sourcing|strategic sourcing|supply chain|vendor manager|supplier manager)\b"),
    ("product", r"\b(product manager|head of product|product director|product development|merchandising)\b"),
    ("business_development", r"\b(business development|bd manager|partnerships|commercial director|commercial manager)\b"),
    ("engineering", r"\b(engineering|engineer|technical director|technical manager|hardware manager)\b"),
    ("rd", r"\b(r&d|research and development|research development|innovation director|innovation manager)\b"),
    ("operations", r"\b(operations|operation manager|factory manager|project manager|program manager)\b"),
    ("sales", r"\b(sales director|sales manager|account manager|key account)\b"),
    ("marketing", r"\b(marketing|brand manager|brand director|ecommerce|e-commerce)\b"),
]


def normalize_role(title: str) -> str:
    text = " ".join(str(title or "").lower().replace("/", " ").split())
    for role, pattern in ROLE_PATTERNS:
        if re.search(pattern, text):
            return role
    return "other"


def role_score(title: str, *, target_motion: str = "oem_odm") -> int:
    role = normalize_role(title)
    score = ROLE_WEIGHTS.get(role, 40)
    text = str(title or "").lower()
    if any(x in text for x in ["chief", "head", "director", "vp", "vice president"]):
        score += 4
    if any(x in text for x in ["assistant", "intern", "junior", "coordinator"]):
        score -= 12
    if target_motion == "technical" and role in {"engineering", "rd", "product"}:
        score += 8
    if target_motion == "commercial" and role in {"procurement", "sourcing", "business_development", "owner"}:
        score += 8
    return max(0, min(100, score))


def rank_decision_makers(candidates: list[dict[str, Any]], *, target_motion: str = "oem_odm") -> list[dict[str, Any]]:
    ranked = []
    for raw in candidates:
        item = dict(raw)
        title = str(item.get("job_title") or item.get("title") or "")
        item["normalized_role"] = normalize_role(title)
        item["role_match_score"] = role_score(title, target_motion=target_motion)
        evidence = int(item.get("evidence_score") or item.get("confidence") or 0)
        item["decision_score"] = min(100, round(item["role_match_score"] * 0.75 + evidence * 0.25))
        ranked.append(item)
    ranked.sort(key=lambda x: (-int(x.get("decision_score", 0)), -int(x.get("role_match_score", 0))))
    for index, item in enumerate(ranked, 1):
        item["rank"] = index
        item["recommended"] = index <= 3 and int(item.get("decision_score", 0)) >= 65
    return ranked
