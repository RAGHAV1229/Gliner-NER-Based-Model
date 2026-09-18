from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path

import torch
from gliner import GLiNER


def filtered_kwargs(function, kwargs: dict) -> dict:
    signature = inspect.signature(function)
    if any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    ):
        return kwargs
    return {
        key: value
        for key, value in kwargs.items()
        if key in signature.parameters
    }


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Production fine-tune for enterprise GLiNER NER."
    )
    parser.add_argument("--base-model", default="urchade/gliner_medium-v2.1")
    parser.add_argument("--train", default="training/datasets/train.json")
    parser.add_argument("--val", default="training/datasets/val.json")
    parser.add_argument("--output", default="checkpoints/best_model")
    parser.add_argument("--max-steps", type=int, default=4000)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--gradient-accumulation", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=5e-6)
    parser.add_argument("--save-steps", type=int, default=250)
    parser.add_argument("--warmup-ratio", type=float, default=0.08)
    args = parser.parse_args()

    train_data = [item for item in load_json(Path(args.train)) if item.get("ner")]
    val_data = [item for item in load_json(Path(args.val)) if item.get("ner")]
    if not train_data:
        raise ValueError("Training dataset is empty.")

    print(f"Training samples: {len(train_data)}")
    print(f"Validation samples: {len(val_data)}")
    print(f"Base model: {args.base_model}")

    model = GLiNER.from_pretrained(args.base_model)
    cuda_available = torch.cuda.is_available()
    bf16_available = (
        cuda_available
        and hasattr(torch.cuda, "is_bf16_supported")
        and torch.cuda.is_bf16_supported()
    )

    if not cuda_available:
        print("CUDA not detected. Training on CPU with a smaller batch.")
        args.batch_size = min(args.batch_size, 2)
        args.gradient_accumulation = max(args.gradient_accumulation, 8)

    train_kwargs = {
        "train_dataset": train_data,
        "eval_dataset": val_data,
        "output_dir": args.output,
        "max_steps": args.max_steps,
        "per_device_train_batch_size": args.batch_size,
        "per_device_eval_batch_size": args.batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation,
        "learning_rate": args.learning_rate,
        "others_lr": args.learning_rate * 2,
        "weight_decay": 0.01,
        "others_weight_decay": 0.01,
        "warmup_ratio": args.warmup_ratio,
        "save_steps": args.save_steps,
        "eval_steps": args.save_steps,
        "logging_steps": 25,
        "save_total_limit": 4,
        "max_grad_norm": 1.0,
        "bf16": bool(bf16_available),
        "fp16": bool(cuda_available and not bf16_available),
    }
    accepted = filtered_kwargs(model.train_model, train_kwargs)
    print(json.dumps({k: v for k, v in accepted.items() if k not in {"train_dataset", "eval_dataset"}}, indent=2))
    model.train_model(**accepted)
    print(f"Training finished. Checkpoints: {args.output}")


if __name__ == "__main__":
    main()
