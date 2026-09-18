from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def run_step(script: str, extra: list[str]) -> None:
    command = [sys.executable, str(BACKEND_DIR / "training" / script), *extra]
    print("\n>>>", " ".join(command))
    completed = subprocess.run(command, cwd=str(BACKEND_DIR), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def merge_datasets(paths: list[Path]) -> list[dict]:
    merged = []
    seen = set()
    for path in paths:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = [payload]
        for sample in payload:
            tokens = sample.get("tokenized_text") or []
            key = " ".join(tokens)
            if not tokens or key in seen:
                continue
            seen.add(key)
            merged.append(sample)
    return merged


def split_samples(samples: list[dict], seed: int = 42) -> dict[str, list]:
    rng = random.Random(seed)
    rng.shuffle(samples)
    total = len(samples)
    train_end = int(total * 0.80)
    val_end = train_end + int(total * 0.10)
    return {
        "train": samples[:train_end],
        "val": samples[train_end:val_end],
        "test": samples[val_end:],
    }


def counts(samples: list[dict]) -> dict:
    counter: Counter[str] = Counter()
    for sample in samples:
        for _, _, label in sample.get("ner", []):
            counter[label] += 1
    return dict(counter)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate data, split, and optionally fine-tune GLiNER."
    )
    parser.add_argument("--samples", type=int, default=12000)
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--base-model", default="urchade/gliner_medium-v2.1")
    parser.add_argument("--max-steps", type=int, default=4000)
    args = parser.parse_args()

    run_step(
        "generate_enterprise_dataset.py",
        ["--samples", str(args.samples)],
    )
    run_step(
        "convert_domain_json.py",
        [
            "--input",
            str(BACKEND_DIR / "batch_uploads"),
            "--output",
            str(BACKEND_DIR / "training" / "domain_gliner.json"),
            "--limit",
            "2000",
        ],
    )

    generated = BACKEND_DIR / "training" / "enterprise_gliner.json"
    domain = BACKEND_DIR / "training" / "domain_gliner.json"
    existing = BACKEND_DIR / "training" / "datasets" / "train.json"
    val_existing = BACKEND_DIR / "training" / "datasets" / "val.json"
    test_existing = BACKEND_DIR / "training" / "datasets" / "test.json"

    merged = merge_datasets([generated, domain, existing, val_existing, test_existing])
    splits = split_samples(merged)
    output_dir = BACKEND_DIR / "training" / "datasets"
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, split in splits.items():
        path = output_dir / f"{name}.json"
        path.write_text(json.dumps(split, ensure_ascii=False), encoding="utf-8")
        print(f"{name}: {len(split)} documents")
        print(counts(split))

    all_path = BACKEND_DIR / "training" / "all_gliner.json"
    all_path.write_text(json.dumps(merged, ensure_ascii=False), encoding="utf-8")
    print(f"Merged corpus: {len(merged)} -> {all_path}")

    if args.skip_train:
        print("Skipping training (--skip-train).")
        return

    run_step(
        "train_enterprise.py",
        [
            "--base-model",
            args.base_model,
            "--train",
            str(output_dir / "train.json"),
            "--val",
            str(output_dir / "val.json"),
            "--output",
            str(BACKEND_DIR / "checkpoints" / "best_model"),
            "--max-steps",
            str(args.max_steps),
        ],
    )


if __name__ == "__main__":
    main()
