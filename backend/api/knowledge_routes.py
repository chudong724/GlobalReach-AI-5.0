from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.security import require_api_access
from knowledge.store import KnowledgeStore

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge"], dependencies=[Depends(require_api_access)])
_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge.db"
store = KnowledgeStore(str(_DB_PATH))


class KnowledgePayload(BaseModel):
    id: str | None = None
    title: str = ""
    category: str = "general"
    content: str = ""
    tags: str = ""
    active: bool = True


class DeletePayload(BaseModel):
    ids: list[str] = Field(default_factory=list)


@router.get("")
def list_items(search: str = "", limit: int = 500) -> dict[str, Any]:
    items = store.list_items(search=search, limit=limit)
    return {"items": items, "count": len(items)}


@router.post("")
def save_item(payload: KnowledgePayload) -> dict[str, Any]:
    if not payload.title.strip() or not payload.content.strip():
        raise HTTPException(status_code=400, detail="title and content are required")
    return store.save_item(payload.model_dump())


@router.post("/delete-many")
def delete_many(payload: DeletePayload) -> dict[str, int]:
    return {"deleted": store.delete_many(payload.ids)}


def register_knowledge_routes(target_router: APIRouter) -> None:
    target_router.include_router(router)
