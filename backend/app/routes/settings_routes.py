from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.models import User
from app.services.settings_service import (
    clear_openai_settings,
    openai_status,
    save_openai_settings,
)
from app.utils.auth_utils import get_current_user, require_admin

router = APIRouter(prefix="/api/settings", tags=["Settings"])


class OpenAISettingsRequest(BaseModel):
    api_key: str = Field(min_length=1)
    model: str | None = "gpt-4o-mini"


@router.get("/openai")
def get_openai_settings(current_user: User = Depends(get_current_user)):
    status = openai_status()
    status["can_edit"] = current_user.role == "admin"
    return status


@router.post("/openai")
def set_openai_settings(
    payload: OpenAISettingsRequest,
    _: User = Depends(require_admin),
):
    key = payload.api_key.strip()
    if not key.startswith("sk-") and not key.startswith("sk-proj-"):
        # Allow other key formats but warn via soft validation length
        if len(key) < 20:
            raise HTTPException(status_code=400, detail="API key looks too short")
    saved = save_openai_settings(key, payload.model)
    status = openai_status()
    status["message"] = "OpenAI API key saved. Comparison is now enabled."
    status["model"] = saved["model"]
    return status


@router.delete("/openai")
def delete_openai_settings(_: User = Depends(require_admin)):
    clear_openai_settings()
    status = openai_status()
    status["message"] = "OpenAI API key cleared."
    return status
