from __future__ import annotations

import json
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
SETTINGS_PATH = BACKEND_DIR / "data" / "openai_settings.json"


def _ensure_parent() -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_openai_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {
            "api_key": os.getenv("OPENAI_API_KEY", "").strip(),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini",
        }
    try:
        payload = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    return {
        "api_key": str(payload.get("api_key") or os.getenv("OPENAI_API_KEY", "")).strip(),
        "model": str(
            payload.get("model") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        ).strip()
        or "gpt-4o-mini",
    }


def apply_openai_settings_to_env(settings: dict | None = None) -> dict:
    settings = settings or load_openai_settings()
    key = (settings.get("api_key") or "").strip()
    model = (settings.get("model") or "gpt-4o-mini").strip() or "gpt-4o-mini"
    if key:
        os.environ["OPENAI_API_KEY"] = key
    elif "OPENAI_API_KEY" in os.environ and not os.environ.get("OPENAI_API_KEY"):
        os.environ.pop("OPENAI_API_KEY", None)
    os.environ["OPENAI_MODEL"] = model
    return {"api_key": key, "model": model}


def save_openai_settings(api_key: str, model: str | None = None) -> dict:
    current = load_openai_settings()
    key = (api_key or "").strip()
    chosen_model = (model or current.get("model") or "gpt-4o-mini").strip() or "gpt-4o-mini"
    payload = {"api_key": key, "model": chosen_model}
    _ensure_parent()
    SETTINGS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    apply_openai_settings_to_env(payload)
    return payload


def clear_openai_settings() -> dict:
    current = load_openai_settings()
    payload = {"api_key": "", "model": current.get("model") or "gpt-4o-mini"}
    _ensure_parent()
    SETTINGS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ["OPENAI_MODEL"] = payload["model"]
    return payload


def openai_status() -> dict:
    settings = apply_openai_settings_to_env()
    key = settings.get("api_key") or ""
    masked = ""
    if key:
        if len(key) <= 8:
            masked = "*" * len(key)
        else:
            masked = f"{key[:3]}...{key[-4:]}"
    return {
        "configured": bool(key),
        "model": settings.get("model") or "gpt-4o-mini",
        "api_key_masked": masked,
        "source": "settings_file" if SETTINGS_PATH.exists() else "environment",
    }
