from __future__ import annotations

"""
Convert enterprise classification JSON documents into GLiNER training samples.
Uses structured fields + keyword spans as high-precision weak labels aligned
to the production ontology prompts.
"""

import argparse
import json
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config.entity_ontology import MODEL_LABEL_PROMPTS

TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", flags=re.UNICODE)

# Map domain keywords / fields to ontology labels used in training prompts.
KEYWORD_LABELS = {
    "explosives": "WEAPON",
    "fighter aircraft": "WEAPON",
    "artillery": "WEAPON",
    "ballistic missile": "WEAPON",
    "cruise missile": "WEAPON",
    "uav": "WEAPON",
    "unmanned aerial vehicle": "WEAPON",
    "ammunition depot": "INFRASTRUCTURE",
    "ministry of defense": "ORGANIZATION",
    "ministry of defence": "ORGANIZATION",
    "royal saudi air force": "MILITARY_UNIT",
    "rapid action force": "MILITARY_UNIT",
    "nato": "ORGANIZATION",
    "isro": "ORGANIZATION",
    "drdo": "ORGANIZATION",
}


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text)


def find_span(tokens: list[str], value_tokens: list[str]) -> tuple[int, int] | None:
    if not value_tokens:
        return None
    n, m = len(tokens), len(value_tokens)
    for i in range(n - m + 1):
        if [t.lower() for t in tokens[i : i + m]] == [t.lower() for t in value_tokens]:
            return i, i + m - 1
    return None


def build_text_from_doc(doc: dict) -> str:
    parts = []
    for key in ("title", "documentNumber", "classification", "preparedBy", "summary", "overview"):
        value = doc.get(key)
        if value:
            parts.append(str(value))
    for key in ("keywords", "indicators"):
        values = doc.get(key) or []
        if isinstance(values, list):
            parts.extend(str(v) for v in values if v)
    for row in doc.get("register") or []:
        if isinstance(row, dict):
            parts.extend(str(v) for v in row.values() if v)
    return "\n".join(parts)


def annotate_document(doc: dict) -> dict | None:
    text = build_text_from_doc(doc)
    if len(text.strip()) < 40:
        return None

    tokens = tokenize(text)
    ner: list[list] = []
    seen_spans: set[tuple[int, int, str]] = set()

    def add_entity(raw: str, label: str) -> None:
        raw = (raw or "").strip()
        if len(raw) < 2 or label not in MODEL_LABEL_PROMPTS:
            return
        value_tokens = tokenize(raw)
        span = find_span(tokens, value_tokens)
        if not span:
            return
        start, end = span
        key = (start, end, MODEL_LABEL_PROMPTS[label])
        if key in seen_spans:
            return
        seen_spans.add(key)
        ner.append([start, end, MODEL_LABEL_PROMPTS[label]])

    title = doc.get("title")
    if title:
        add_entity(str(title), "DOCUMENT_TITLE") if "DOCUMENT_TITLE" in MODEL_LABEL_PROMPTS else None
        # Prefer EVENT/PROJECT-like titles as ORGANIZATION context is weak; keep as EVENT when military
        if any(w in str(title).lower() for w in ("brief", "report", "memo", "advisory", "bulletin")):
            add_entity(str(title), "DOCUMENT_TYPE") if "DOCUMENT_TYPE" in MODEL_LABEL_PROMPTS else None

    if doc.get("documentNumber"):
        add_entity(str(doc["documentNumber"]), "DOCUMENT_NUMBER")

    if doc.get("preparedBy"):
        add_entity(str(doc["preparedBy"]), "ORGANIZATION")

    if doc.get("date"):
        # ISO dates often appear in overview; also try raw date field text
        add_entity(str(doc["date"])[:10], "DATE")

    for bucket in (doc.get("keywords") or [], doc.get("indicators") or []):
        if not isinstance(bucket, list):
            continue
        for item in bucket:
            key = str(item).strip().lower()
            label = KEYWORD_LABELS.get(key)
            if label:
                add_entity(str(item), label)
            elif "facility" in key or "port" in key or "airport" in key or "plant" in key:
                add_entity(str(item), "INFRASTRUCTURE")
            elif "ministry" in key or "force" in key or "command" in key or "office" in key:
                add_entity(str(item), "ORGANIZATION")
            elif any(
                token in key
                for token in (
                    "missile",
                    "weapon",
                    "aircraft",
                    "artillery",
                    "explosive",
                    "ammunition",
                    "uav",
                    "rifle",
                )
            ):
                add_entity(str(item), "WEAPON")
            elif len(key.split()) <= 4 and key[0:1].isalpha():
                # Keep short indicator phrases as ORGANIZATION/LOCATION candidates
                add_entity(str(item), "ORGANIZATION")

    for row in doc.get("register") or []:
        if not isinstance(row, dict):
            continue
        for field, label in (
            ("Origin", "LOCATION"),
            ("Destination", "LOCATION"),
            ("Reference", "DOCUMENT_NUMBER"),
        ):
            if row.get(field):
                add_entity(str(row[field]), label)

    # Drop DOCUMENT_* if not in prompts
    ner = [span for span in ner if span[2] in set(MODEL_LABEL_PROMPTS.values())]
    if not ner:
        return None
    return {"tokenized_text": tokens, "ner": ner}


def convert_directory(root: Path, limit: int | None = None) -> list[dict]:
    samples: list[dict] = []
    paths = sorted(root.rglob("*.json"))
    for path in paths:
        if limit is not None and len(samples) >= limit:
            break
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        sample = annotate_document(payload)
        if sample:
            samples.append(sample)
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert domain JSON docs to GLiNER samples.")
    parser.add_argument(
        "--input",
        default=str(BACKEND_DIR / "batch_uploads"),
        help="Root folder containing classification JSON documents",
    )
    parser.add_argument(
        "--output",
        default=str(BACKEND_DIR / "training" / "domain_gliner.json"),
    )
    parser.add_argument("--limit", type=int, default=2000)
    args = parser.parse_args()

    samples = convert_directory(Path(args.input), limit=args.limit)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(samples, ensure_ascii=False), encoding="utf-8")
    print(f"Converted {len(samples)} domain documents -> {output}")


if __name__ == "__main__":
    main()
