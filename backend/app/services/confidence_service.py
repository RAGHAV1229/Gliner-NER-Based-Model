from __future__ import annotations

from app.config.entity_ontology import REGEX_ONLY_LABELS

DEFAULT_MIN_SCORE = 0.45
REGEX_MIN_SCORE = 0.95


def apply_confidence_policy(entities: list[dict], minimum_score: float = DEFAULT_MIN_SCORE) -> list[dict]:
    filtered = []
    for entity in entities:
        label = entity.get("label", "")
        score = float(entity.get("score") or 0.0)
        source = entity.get("source", "gliner")

        if source in {"regex", "pii"} or label in REGEX_ONLY_LABELS:
            entity["score"] = max(score, REGEX_MIN_SCORE)
            filtered.append(entity)
            continue

        # Do not inflate weak GLiNER scores.
        if score < minimum_score:
            continue
        filtered.append(entity)
    return filtered
