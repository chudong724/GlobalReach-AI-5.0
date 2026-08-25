from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.security import require_api_access
from tools.decision_maker_intelligence import rank_decision_makers

router = APIRouter(prefix="/api/v1/decision-makers", tags=["Decision Maker Intelligence"], dependencies=[Depends(require_api_access)])


class Candidate(BaseModel):
    name: str = ""
    job_title: str = ""
    email: str = ""
    linkedin: str = ""
    confidence: int = 0
    evidence_score: int = 0
    source: str = ""


class RankPayload(BaseModel):
    candidates: list[Candidate] = Field(default_factory=list)
    target_motion: str = "oem_odm"


@router.post("/rank")
def rank(payload: RankPayload) -> dict[str, Any]:
    if not payload.candidates:
        raise HTTPException(status_code=400, detail="candidates are required")
    items = rank_decision_makers([x.model_dump() for x in payload.candidates], target_motion=payload.target_motion)
    return {
        "items": items,
        "recommended": [x for x in items if x.get("recommended")],
        "target_motion": payload.target_motion,
    }


def register_decision_maker_routes(target_router: APIRouter) -> None:
    target_router.include_router(router)
