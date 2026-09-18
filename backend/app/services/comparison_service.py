from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from app.batch_models import ExtractedEntity
from app.services.openai_ner_service import extract_openai_entities, openai_configured
from app.services.parser_service import extract_text_from_file


def _norm_key(text: str, label: str) -> tuple[str, str]:
    return (str(text or "").strip().lower(), str(label or "").strip().upper())


def _surface_key(text: str) -> str:
    return str(text or "").strip().lower()


def entity_filename(path: str | None) -> str:
    if not path:
        return "unknown"
    return Path(str(path).replace("\\", "/")).name


def build_entity_file_map(entities: list[ExtractedEntity]) -> dict[tuple[str, str], list[str]]:
    mapping: dict[tuple[str, str], set[str]] = defaultdict(set)
    for entity in entities:
        key = _norm_key(entity.text, entity.label)
        mapping[key].add(entity_filename(entity.file_path))
    return {key: sorted(files) for key, files in mapping.items()}


def compare_gliner_openai(
    gliner_entities: list[ExtractedEntity],
    openai_entities: list[dict],
) -> dict:
    gliner_by_pair: dict[tuple[str, str], dict] = {}
    openai_by_pair: dict[tuple[str, str], dict] = {}
    gliner_by_surface: dict[str, set[str]] = defaultdict(set)
    openai_by_surface: dict[str, set[str]] = defaultdict(set)

    for entity in gliner_entities:
        if str(entity.source).lower() == "openai":
            continue
        key = _norm_key(entity.text, entity.label)
        gliner_by_pair[key] = {
            "text": entity.text,
            "label": entity.label,
            "score": entity.score,
            "source": entity.source,
            "file_path": entity_filename(entity.file_path),
        }
        gliner_by_surface[_surface_key(entity.text)].add(entity.label)

    for entity in openai_entities:
        key = _norm_key(entity.get("text"), entity.get("label"))
        openai_by_pair[key] = {
            "text": entity.get("text"),
            "label": entity.get("label"),
            "score": entity.get("score", 0.9),
            "source": "openai",
            "file_path": entity_filename(entity.get("file_path")),
        }
        openai_by_surface[_surface_key(entity.get("text"))].add(
            str(entity.get("label") or "").upper()
        )

    both_keys = set(gliner_by_pair) & set(openai_by_pair)
    gliner_only_keys = set(gliner_by_pair) - set(openai_by_pair)
    openai_only_keys = set(openai_by_pair) - set(gliner_by_pair)

    type_differences = []
    for surface in sorted(set(gliner_by_surface) & set(openai_by_surface)):
        g_labels = gliner_by_surface[surface]
        o_labels = openai_by_surface[surface]
        if g_labels != o_labels:
            type_differences.append(
                {
                    "text": surface,
                    "gliner_labels": sorted(g_labels),
                    "openai_labels": sorted(o_labels),
                }
            )

    return {
        "counts": {
            "gliner_total": len(gliner_by_pair),
            "openai_total": len(openai_by_pair),
            "both": len(both_keys),
            "gliner_only": len(gliner_only_keys),
            "openai_only": len(openai_only_keys),
            "type_differences": len(type_differences),
        },
        "both": [gliner_by_pair[k] for k in sorted(both_keys)],
        "gliner_only": [gliner_by_pair[k] for k in sorted(gliner_only_keys)],
        "openai_only": [openai_by_pair[k] for k in sorted(openai_only_keys)],
        "type_differences": type_differences,
    }


def run_openai_on_files(files: list) -> list[dict]:
    """files: iterable of objects with stored_path and relative_path."""
    if not openai_configured():
        return []
    results: list[dict] = []
    for batch_file in files:
        text = extract_text_from_file(Path(batch_file.stored_path))
        if not text.strip():
            continue
        for entity in extract_openai_entities(text):
            entity["file_path"] = batch_file.relative_path
            results.append(entity)
    return results
