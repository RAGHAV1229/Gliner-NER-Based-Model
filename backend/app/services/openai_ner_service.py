from __future__ import annotations

import json
import os
import re
from typing import Any

from app.config.entity_ontology import MODEL_LABEL_PROMPTS, normalize_label

OPENAI_LABELS = [
    "PERSON",
    "ORGANIZATION",
    "LOCATION",
    "ADDRESS",
    "DATE",
    "TIME",
    "EVENT",
    "PRODUCT",
    "DESIGNATION",
    "DEPARTMENT",
    "PROJECT",
    "WEAPON",
    "MILITARY_UNIT",
    "INFRASTRUCTURE",
    "THREAT_ACTOR",
    "DOCUMENT_NUMBER",
    "DOCUMENT_TYPE",
    "EMAIL",
    "PHONE",
    "MONEY",
    "QUANTITY",
]


def openai_configured() -> bool:
    from app.services.settings_service import apply_openai_settings_to_env

    settings = apply_openai_settings_to_env()
    return bool((settings.get("api_key") or "").strip())


def get_openai_model() -> str:
    from app.services.settings_service import apply_openai_settings_to_env

    settings = apply_openai_settings_to_env()
    return (settings.get("model") or "gpt-4o-mini").strip() or "gpt-4o-mini"


def _extract_json_array(raw: str) -> list[dict]:
    raw = (raw or "").strip()
    if not raw:
        return []
    try:
        payload = json.loads(raw)
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("entities"), list):
            return payload["entities"]
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[[\s\S]*\]", raw)
    if not match:
        return []
    try:
        payload = json.loads(match.group(0))
        return payload if isinstance(payload, list) else []
    except json.JSONDecodeError:
        return []


def extract_openai_entities(text: str, max_chars: int = 6000) -> list[dict[str, Any]]:
    """Extract entities with OpenAI Chat Completions. Returns empty list if unavailable."""
    if not openai_configured() or not text.strip():
        return []

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return []

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "openai package is not installed. Run: pip install openai"
        ) from exc

    model = get_openai_model()
    snippet = text[:max_chars]
    label_list = ", ".join(OPENAI_LABELS)
    prompt = (
        "Extract named entities from the document text.\n"
        f"Allowed labels only: {label_list}.\n"
        "Return ONLY a JSON array of objects with keys: text, label.\n"
        "Use exact surface forms from the text. Do not invent entities.\n\n"
        f"TEXT:\n{snippet}"
    )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are an enterprise NER extractor. Reply with JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content or ""
    entities: list[dict[str, Any]] = []
    for item in _extract_json_array(content):
        if not isinstance(item, dict):
            continue
        surface = str(item.get("text") or "").strip()
        label = normalize_label(item.get("label"))
        if not surface or label == "UNKNOWN":
            continue
        if label not in MODEL_LABEL_PROMPTS and label not in OPENAI_LABELS:
            continue
        start = snippet.find(surface)
        end = start + len(surface) if start >= 0 else None
        entities.append(
            {
                "text": surface[:1024],
                "label": label,
                "score": 0.9,
                "start": start if start >= 0 else None,
                "end": end,
                "source": "openai",
            }
        )
    return entities
