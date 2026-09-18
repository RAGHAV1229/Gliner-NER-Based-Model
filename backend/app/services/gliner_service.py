from __future__ import annotations

import os
from pathlib import Path

from gliner import GLiNER

from app.config.entity_ontology import (
    CORE_ALWAYS_ON_LABELS,
    DICTIONARY_ONLY_LABELS,
    LABEL_ALIASES,
    MAX_GLINER_LABELS,
    MODEL_LABEL_PROMPTS,
    PRODUCTION_TRAINING_LABELS as TRAINED_LABELS,
    PROMPT_TO_LABEL,
    REGEX_ONLY_LABELS,
    STRUCTURED_LABELS,
    normalize_label,
)
from app.services.confidence_service import DEFAULT_MIN_SCORE, apply_confidence_policy
from app.services.label_selector_service import select_labels
from app.services.ontology_service import extract_dictionary_entities, load_dictionary_values
from app.services.pii_extractor import extract_pii_entities

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_BASE_DIR = BASE_DIR / "checkpoints" / "best_model"

GLINER_EXCLUDED_LABELS = set(REGEX_ONLY_LABELS) | set(DICTIONARY_ONLY_LABELS)

_model = None
MODEL_PATH = None
DICTIONARY_VALUES = load_dictionary_values()


def get_latest_checkpoint(base_dir: str | Path) -> str:
    base = Path(base_dir)
    if not base.exists():
        return str(base)
    # Prefer directory itself if it looks like a model folder
    if (base / "gliner_config.json").exists() or (base / "config.json").exists():
        return str(base)
    checkpoints = sorted(
        [p for p in base.glob("checkpoint-*") if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if checkpoints:
        return str(checkpoints[0])
    return str(base)


def resolve_model_path() -> str:
    production_dir = BASE_DIR / "checkpoints" / "production_model"
    env_path = os.environ.get("GLINER_MODEL_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    if production_dir.exists():
        return get_latest_checkpoint(production_dir)
    if MODEL_BASE_DIR.exists():
        return get_latest_checkpoint(MODEL_BASE_DIR)
    return os.environ.get("GLINER_BASE_MODEL", "urchade/gliner_small-v2.1")


def get_model():
    global _model, MODEL_PATH
    if _model is not None:
        return _model
    MODEL_PATH = resolve_model_path()
    print(f"Loading GLiNER model from: {MODEL_PATH}")
    _model = GLiNER.from_pretrained(MODEL_PATH)
    print(f"Loaded dictionary labels: {len(DICTIONARY_VALUES)}")
    return _model


def create_text_chunks(text: str, chunk_size: int = 1200, overlap: int = 120):
    if not text:
        return []
    if len(text) <= chunk_size:
        return [(text, 0)]
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append((text[start:end], start))
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def predict_chunk(
    chunk_text: str,
    selected_labels: list[str],
    minimum_score: float,
    loaded_model=None,
) -> list[dict]:
    active_model = loaded_model or get_model()
    try:
        predictions = active_model.predict_entities(
            chunk_text,
            selected_labels,
            threshold=minimum_score,
        )
    except TypeError:
        predictions = active_model.predict_entities(chunk_text, selected_labels)
    return predictions


def _canonical_gliner_label(raw_label: str) -> str:
    raw = str(raw_label).strip()
    prompt_key = raw.lower()
    if prompt_key in PROMPT_TO_LABEL:
        return PROMPT_TO_LABEL[prompt_key]
    return normalize_label(raw)


def _label_batches(labels: list[str]) -> list[list[str]]:
    unique = list(dict.fromkeys(labels))
    if not unique:
        return []
    return [
        unique[index : index + MAX_GLINER_LABELS]
        for index in range(0, len(unique), MAX_GLINER_LABELS)
    ]


def extract_gliner_entities(
    text: str,
    selected_labels: list[str],
    minimum_score: float = DEFAULT_MIN_SCORE,
) -> list[dict]:
    if not selected_labels:
        return []

    gliner_labels = [
        normalize_label(label)
        for label in selected_labels
        if normalize_label(label) not in GLINER_EXCLUDED_LABELS
    ]
    gliner_labels = list(dict.fromkeys(gliner_labels))

    all_entities: list[dict] = []
    loaded_model = get_model()

    for chunk_text, chunk_start in create_text_chunks(text):
        for label_batch in _label_batches(gliner_labels):
            prompts = [
                MODEL_LABEL_PROMPTS.get(label, label.lower().replace("_", " "))
                for label in label_batch
            ]
            predictions = predict_chunk(
                chunk_text=chunk_text,
                selected_labels=prompts,
                minimum_score=minimum_score,
                loaded_model=loaded_model,
            )
            for prediction in predictions:
                score = float(prediction.get("score") or 0.0)
                if score < minimum_score:
                    continue
                local_start = prediction.get("start")
                local_end = prediction.get("end")
                if local_start is None or local_end is None:
                    continue
                global_start = int(local_start) + chunk_start
                global_end = int(local_end) + chunk_start
                if global_start < 0 or global_end > len(text):
                    continue
                label = _canonical_gliner_label(prediction.get("label", ""))
                all_entities.append(
                    {
                        "text": text[global_start:global_end],
                        "label": label,
                        "score": score,
                        "start": global_start,
                        "end": global_end,
                        "source": "gliner",
                    }
                )
    return all_entities


def extract_regex_entities(text: str) -> list[dict]:
    return extract_pii_entities(text)


def _overlap(a: dict, b: dict) -> bool:
    return not (a["end"] <= b["start"] or b["end"] <= a["start"])


def merge_entities(entities: list[dict]) -> list[dict]:
    if not entities:
        return []
    ranked = sorted(
        entities,
        key=lambda e: (
            2 if e.get("source") in {"regex", "pii"} else 1 if e.get("source") == "dictionary" else 0,
            float(e.get("score") or 0.0),
            (e.get("end", 0) - e.get("start", 0)),
        ),
        reverse=True,
    )
    accepted: list[dict] = []
    for entity in ranked:
        if any(_overlap(entity, existing) for existing in accepted):
            continue
        accepted.append(entity)
    return sorted(accepted, key=lambda e: (e.get("start", 0), e.get("end", 0)))


def extract_entities(
    text: str,
    profiles: list[str] | None = None,
    minimum_score: float = DEFAULT_MIN_SCORE,
) -> list[dict]:
    if not text or not text.strip():
        return []

    selection = select_labels(profiles)
    gliner_entities: list[dict] = []
    try:
        gliner_entities = extract_gliner_entities(text, selection["labels"], minimum_score)
    except Exception as exc:
        print(f"GLiNER extraction failed, continuing with PII/dictionary only: {exc}")

    pii_entities = extract_regex_entities(text)
    dict_entities = extract_dictionary_entities(text, DICTIONARY_VALUES)
    merged = merge_entities(gliner_entities + pii_entities + dict_entities)
    return apply_confidence_policy(merged, minimum_score=minimum_score)
