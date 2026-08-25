from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from api.security import require_api_access
from crm.commercial_ops import analyze_reply_intent, forecast_snapshot

router = APIRouter(prefix="/api/v1/commercial-ops", tags=["Commercial Operations"], dependencies=[Depends(require_api_access)])
_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class ReplyAnalysisPayload(BaseModel):
    contact_id: str
    subject: str = ""
    reply_text: str = ""


@router.post("/reply-analysis")
async def reply_analysis(payload: ReplyAnalysisPayload) -> dict[str, Any]:
    if not payload.contact_id.strip() or not payload.reply_text.strip():
        raise HTTPException(status_code=400, detail="contact_id and reply_text are required")
    result = await analyze_reply_intent(payload.contact_id.strip(), payload.reply_text, payload.subject)
    if result.get("error") == "contact_not_found":
        raise HTTPException(status_code=404, detail="Contact not found")
    return result


@router.get("/forecast")
def forecast() -> dict[str, Any]:
    return forecast_snapshot()


@router.get("/backup")
def backup() -> Response:
    files = [
        _BACKEND_ROOT / "data" / "crm.db",
        _BACKEND_ROOT / "data" / "knowledge.db",
        _BACKEND_ROOT / "data" / "email.db",
        _BACKEND_ROOT / "hunt_sessions.db",
    ]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        added = 0
        for path in files:
            if path.exists() and path.is_file():
                archive.write(path, arcname=path.name)
                added += 1
        archive.writestr("README.txt", f"Wenmei Global AI Customer System database backup. Files included: {added}. Restore only while services are stopped.\n")
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=wenmei-global-ai-backup.zip"},
    )


def register_commercial_ops_routes(target_router: APIRouter) -> None:
    target_router.include_router(router)
