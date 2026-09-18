from __future__ import annotations

from app.config.entity_ontology import (
    CORE_ALWAYS_ON_LABELS,
    ENTITY_PROFILES,
    MODEL_LABEL_PROMPTS,
    REGEX_ONLY_LABELS,
    normalize_label,
)


def select_labels(profiles: list[str] | None = None) -> dict:
    profiles = profiles or ["general", "pii", "security", "finance", "medical"]
    labels = list(CORE_ALWAYS_ON_LABELS)

    for profile in profiles:
        for label in ENTITY_PROFILES.get(profile, []):
            label = normalize_label(label)
            if label in REGEX_ONLY_LABELS:
                continue
            if label not in MODEL_LABEL_PROMPTS:
                continue
            if label not in labels:
                labels.append(label)

    return {
        "profiles": profiles,
        "labels": labels,
        "model_prompts": [
            MODEL_LABEL_PROMPTS[x]
            for x in labels
            if x in MODEL_LABEL_PROMPTS
        ],
    }
