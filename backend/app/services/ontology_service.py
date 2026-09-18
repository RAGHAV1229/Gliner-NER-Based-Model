from __future__ import annotations

from pathlib import Path

from app.config.entity_ontology import DICTIONARY_ONLY_LABELS, normalize_label

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENTITIES_DIR = BACKEND_DIR / "entities"


def load_dictionary_values() -> dict[str, set[str]]:
    values: dict[str, set[str]] = {}
    ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
    for label in DICTIONARY_ONLY_LABELS:
        path = ENTITIES_DIR / f"{label}.txt"
        if not path.exists():
            continue
        entries = {
            line.strip()
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        if entries:
            values[label] = {entry.lower() for entry in entries}
    return values


def extract_dictionary_entities(text: str, dictionary_values: dict[str, set[str]]) -> list[dict]:
    if not text or not dictionary_values:
        return []
    lowered = text.lower()
    entities: list[dict] = []
    for label, entries in dictionary_values.items():
        for entry in entries:
            start = 0
            while True:
                index = lowered.find(entry, start)
                if index < 0:
                    break
                end = index + len(entry)
                # crude word-boundary check
                before = lowered[index - 1] if index > 0 else " "
                after = lowered[end] if end < len(lowered) else " "
                if before.isalnum() or after.isalnum():
                    start = index + 1
                    continue
                entities.append(
                    {
                        "text": text[index:end],
                        "label": normalize_label(label),
                        "score": 0.92,
                        "start": index,
                        "end": end,
                        "source": "dictionary",
                    }
                )
                start = end
    return entities
