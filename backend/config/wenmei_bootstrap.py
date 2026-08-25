from __future__ import annotations

import os
from pathlib import Path


def load_wenmei_env() -> None:
    """Load provider variables not modeled by legacy Settings.

    Pydantic reads .env into the Settings model but intentionally ignores unknown
    keys. DeepSeek is added by this fork without rewriting the legacy settings
    schema, so we expose its variables to LiteLLM through os.environ here.
    """
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    wanted = {"DEEPSEEK_API_KEY", "DEEPSEEK_API_BASE"}
    try:
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key not in wanted or os.environ.get(key):
                continue
            value = value.strip().strip('"').strip("'")
            if value:
                os.environ[key] = value
    except OSError:
        return
