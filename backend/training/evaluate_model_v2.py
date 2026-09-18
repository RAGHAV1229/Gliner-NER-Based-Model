from __future__ import annotations

"""Evaluate GLiNER checkpoint with token-span Precision / Recall / F1."""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from gliner import GLiNER

from app.config.entity_ontology import (
    MODEL_LABEL_PROMPTS,
    PRODUCTION_TRAINING_LABELS,
    PROMPT_TO_LABEL,
    normalize_label,
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def detokenize(tokens: list[str]) -> tuple[str, list[tuple[int, int]]]:
    """Rebuild text and char spans for each token."""
    pieces = []
    spans = []
    cursor = 0
    for index, token in enumerate(tokens):
        if index > 0 and token.isalnum() and pieces and pieces[-1][-1:].isalnum():
            pieces.append(" ")
            cursor += 1
        start = cursor
        pieces.append(token)
        cursor += len(token)
        spans.append((start, cursor))
    return "".join(pieces), spans


def gold_entities(sample: dict) -> set[tuple[str, str]]:
    tokens = sample.get("tokenized_text") or []
    text, spans = detokenize(tokens)
    gold = set()
    for start_tok, end_tok, label in sample.get("ner") or []:
        if start_tok >= len(spans) or end_tok >= len(spans):
            continue
        char_start = spans[start_tok][0]
        char_end = spans[end_tok][1]
        surface = text[char_start:char_end].strip()
        canonical = PROMPT_TO_LABEL.get(str(label).lower(), normalize_label(label))
        if surface:
            gold.add((surface.lower(), canonical))
    return gold


def predict_entities(model: GLiNER, sample: dict, threshold: float) -> set[tuple[str, str]]:
    tokens = sample.get("tokenized_text") or []
    text, _ = detokenize(tokens)
    labels = [
        MODEL_LABEL_PROMPTS[label]
        for label in PRODUCTION_TRAINING_LABELS
        if label in MODEL_LABEL_PROMPTS
    ]
    labels = list(dict.fromkeys(labels))
    predicted = set()
    batch = 12
    for i in range(0, len(labels), batch):
        chunk = labels[i : i + batch]
        try:
            preds = model.predict_entities(text, chunk, threshold=threshold)
        except TypeError:
            preds = model.predict_entities(text, chunk)
        for pred in preds:
            surface = str(pred.get("text") or "").strip()
            label = PROMPT_TO_LABEL.get(
                str(pred.get("label") or "").lower(),
                normalize_label(pred.get("label")),
            )
            if surface:
                predicted.add((surface.lower(), label))
    return predicted


def score(gold: set, pred: set) -> tuple[float, float, float, int, int, int]:
    tp = len(gold & pred)
    fp = len(pred - gold)
    fn = len(gold - pred)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return precision, recall, f1, tp, fp, fn


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="checkpoints/best_model")
    parser.add_argument("--test", default="training/datasets/test.json")
    parser.add_argument("--threshold", type=float, default=0.45)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--output", default="reports/evaluation_report.json")
    args = parser.parse_args()

    test_data = [s for s in load_json(Path(args.test)) if s.get("ner")][: args.limit]
    model = GLiNER.from_pretrained(args.model)

    micro_gold: set = set()
    micro_pred: set = set()
    per_label = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    for sample in test_data:
        gold = gold_entities(sample)
        pred = predict_entities(model, sample, args.threshold)
        # Use sample-local matching for micro by pairing sets
        tp_set = gold & pred
        fp_set = pred - gold
        fn_set = gold - pred
        micro_gold |= {(id(sample), g) for g in gold}
        micro_pred |= {(id(sample), p) for p in pred}

        for _, label in tp_set:
            per_label[label]["tp"] += 1
        for _, label in fp_set:
            per_label[label]["fp"] += 1
        for _, label in fn_set:
            per_label[label]["fn"] += 1

    # Recompute micro properly
    tp = fp = fn = 0
    for sample in test_data:
        gold = gold_entities(sample)
        pred = predict_entities(model, sample, args.threshold)
        tp += len(gold & pred)
        fp += len(pred - gold)
        fn += len(gold - pred)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    label_metrics = {}
    for label, counts in sorted(per_label.items()):
        p, r, f, *_ = score(
            set(range(counts["tp"] + counts["fn"])),  # placeholder unused
            set(),
        )
        tpc, fpc, fnc = counts["tp"], counts["fp"], counts["fn"]
        p = tpc / (tpc + fpc) if (tpc + fpc) else 0.0
        r = tpc / (tpc + fnc) if (tpc + fnc) else 0.0
        f = 2 * p * r / (p + r) if (p + r) else 0.0
        label_metrics[label] = {
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": round(f, 4),
            "tp": tpc,
            "fp": fpc,
            "fn": fnc,
        }

    report = {
        "model": args.model,
        "samples": len(test_data),
        "threshold": args.threshold,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "per_label": label_metrics,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("samples", "precision", "recall", "f1", "tp", "fp", "fn")}, indent=2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
