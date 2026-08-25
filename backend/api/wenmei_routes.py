from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.security import require_api_access
from config.settings import get_settings
from tools.llm_client import LLMTool

router = APIRouter(prefix="/api/v1/wenmei", tags=["Wenmei"], dependencies=[Depends(require_api_access)])
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class DeepSeekConfig(BaseModel):
    api_key: str = ""
    default_model: str = "deepseek/deepseek-chat"
    reasoning_model: str = "deepseek/deepseek-reasoner"


def _mask(value: str) -> str:
    value = str(value or "")
    if not value:
        return ""
    if len(value) <= 8:
        return "********"
    return value[:4] + "…" + value[-4:]


def _replace_env_values(updates: dict[str, str]) -> None:
    lines = []
    if _ENV_FILE.exists():
        lines = _ENV_FILE.read_text(encoding="utf-8").splitlines()
    used: set[str] = set()
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in line:
            key = line.split("=", 1)[0].strip()
            if key in updates:
                output.append(f"{key}={updates[key]}")
                used.add(key)
                continue
        output.append(line)
    if output and output[-1].strip():
        output.append("")
    for key, value in updates.items():
        if key not in used:
            output.append(f"{key}={value}")
    _ENV_FILE.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


@router.get("/deepseek")
def get_deepseek_config() -> dict[str, object]:
    settings = get_settings()
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    return {
        "configured": bool(key),
        "api_key_masked": _mask(key),
        "default_model": settings.llm_model,
        "reasoning_model": settings.reasoning_model,
        "recommended_default_model": "deepseek/deepseek-chat",
        "recommended_reasoning_model": "deepseek/deepseek-reasoner",
    }


@router.post("/deepseek")
def save_deepseek_config(payload: DeepSeekConfig) -> dict[str, object]:
    key = payload.api_key.strip()
    if key:
        os.environ["DEEPSEEK_API_KEY"] = key
    elif not os.environ.get("DEEPSEEK_API_KEY"):
        raise HTTPException(status_code=400, detail="DeepSeek API Key is required")

    settings = get_settings()
    settings.llm_model = payload.default_model.strip() or "deepseek/deepseek-chat"
    settings.reasoning_model = payload.reasoning_model.strip() or "deepseek/deepseek-reasoner"

    updates = {
        "LLM_MODEL": settings.llm_model,
        "REASONING_MODEL": settings.reasoning_model,
        "DEEPSEEK_API_BASE": "https://api.deepseek.com",
    }
    if key:
        updates["DEEPSEEK_API_KEY"] = key
    _replace_env_values(updates)
    return {
        "saved": True,
        "configured": bool(os.environ.get("DEEPSEEK_API_KEY")),
        "default_model": settings.llm_model,
        "reasoning_model": settings.reasoning_model,
    }


@router.post("/deepseek/test")
async def test_deepseek() -> dict[str, object]:
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise HTTPException(status_code=400, detail="DeepSeek API Key is not configured")
    try:
        tool = LLMTool(model_type="default", settings=get_settings(), agent="deepseek_test")
        text = await tool.generate("Reply with exactly: OK", max_tokens=8, temperature=0)
        return {"ok": True, "response": str(text or "").strip()[:100], "model": tool.model}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def register_wenmei_routes(target_router: APIRouter) -> None:
    target_router.include_router(router)
