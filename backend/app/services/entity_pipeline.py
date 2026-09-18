from __future__ import annotations

from app.services.gliner_service import extract_entities


def run_entity_pipeline(text: str, profiles: list[str] | None = None) -> list[dict]:
    return extract_entities(text, profiles=profiles)
