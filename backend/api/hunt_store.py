"""Hunt persistence — JSON file-based storage for hunt metadata and results."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import get_settings

logger = logging.getLogger(__name__)


def _hunts_dir() -> Path:
    settings = get_settings()
    p = Path(settings.hunts_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _sync_completed_hunt_to_crm(hunt_id: str, hunt_data: dict[str, Any]) -> None:
    if hunt_data.get("status") != "completed" or hunt_data.get("crm_synced_at"):
        return
    result = hunt_data.get("result") or {}
    leads = result.get("leads") if isinstance(result, dict) else []
    if not isinstance(leads, list) or not leads:
        return
    try:
        from crm.automation import sync_hunt_leads
        from crm.store import CRMStore

        db_path = Path(__file__).resolve().parent.parent / "data" / "crm.db"
        sync_result = sync_hunt_leads(CRMStore(str(db_path)), leads, hunt_id=hunt_id)
        hunt_data["crm_sync"] = sync_result
        hunt_data["crm_synced_at"] = now_iso()
        logger.info("[HuntStore] Synced hunt %s to CRM: %s", hunt_id[:8], sync_result)
    except Exception as exc:
        logger.warning("[HuntStore] CRM sync failed for hunt %s: %s", hunt_id[:8], exc)


def save_hunt(hunt_id: str, hunt_data: dict[str, Any]) -> None:
    """Persist a hunt and automatically sync completed leads into CRM once."""
    try:
        _sync_completed_hunt_to_crm(hunt_id, hunt_data)
        path = _hunts_dir() / f"{hunt_id}.json"
        payload = {"hunt_id": hunt_id, **hunt_data}
        path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
    except Exception as e:
        logger.warning("[HuntStore] Failed to save hunt %s: %s", hunt_id[:8], e)


def load_all_hunts(*, mark_interrupted: bool = False) -> dict[str, dict[str, Any]]:
    hunts: dict[str, dict[str, Any]] = {}
    hunts_path = _hunts_dir()
    for path in hunts_path.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            hid = data.pop("hunt_id", path.stem)
            if mark_interrupted and data.get("status") in ("running", "pending"):
                data["status"] = "failed"
                data["error"] = "Process was interrupted (server restarted)"
                data["completed_at"] = now_iso()
                payload = {"hunt_id": hid, **data}
                path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
                logger.info("[HuntStore] Marked interrupted hunt %s as failed", hid[:8])
            hunts[hid] = data
            logger.debug("[HuntStore] Loaded hunt %s (status=%s)", hid[:8], data.get("status"))
        except Exception as e:
            logger.warning("[HuntStore] Failed to load %s: %s", path.name, e)
    if hunts:
        logger.info("[HuntStore] Loaded %d historical hunts from %s", len(hunts), hunts_path)
    return hunts


def delete_hunt(hunt_id: str) -> None:
    try:
        path = _hunts_dir() / f"{hunt_id}.json"
        if path.exists(): path.unlink()
    except Exception as e:
        logger.warning("[HuntStore] Failed to delete hunt %s: %s", hunt_id[:8], e)


def load_hunt(hunt_id: str) -> dict[str, Any] | None:
    try:
        path = _hunts_dir() / f"{hunt_id}.json"
        if not path.exists(): return None
        data = json.loads(path.read_text(encoding="utf-8")); data.pop("hunt_id", None); return data
    except Exception as e:
        logger.warning("[HuntStore] Failed to load hunt %s: %s", hunt_id[:8], e); return None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
