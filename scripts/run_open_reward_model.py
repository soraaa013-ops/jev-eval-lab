#!/usr/bin/env python3
"""Run an open Bradley-Terry reward model on the pairwise dataset.

Each response is scored once.  The swapped row is derived from the same two
scores, making the reward-model baseline exactly order invariant by design.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import platform
import time
from pathlib import Path

from jev_eval.core import file_sha256, load_jsonl


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/benchmarks/judgebench-gpt.jsonl")
    parser.add_argument("--output", default="artifacts/runs/judgebench-skywork-rm/results.jsonl")
    parser.add_argument("--model", default="Skywork/Skywork-Reward-V2-Qwen3-0.6B")
    parser.add_argument("--revision", default="8c14a4e9e6321deaf572544339b16b8d6bbe8886")
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    output = Path(args.output)
    prior_manifest = output.parent / "manifest.json"
    if output.exists() and prior_manifest.exists():
        prior = json.loads(prior_manifest.read_text(encoding="utf-8"))
        expected = {"model": args.model, "requested_revision": args.revision,
                    "max_length": args.max_length, "data": args.data}
        mismatches = {key: (prior.get(key), value) for key, value in expected.items()
                      if prior.get(key) != value}
        if mismatches:
            raise SystemExit(f"refusing to resume with changed settings: {mismatches}")

    try:
        import torch
        import transformers
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as exc:
        raise SystemExit("Install the local-model extra: pip install -e '.[local-models]'") from exc

    items = load_jsonl(Path(args.data))
    if args.limit:
        items = items[: args.limit]
    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=args.revision)
    # Preserve the assistant answer and the end of long prompts when a CPU run
    # explicitly chooses a short context window.
    tokenizer.truncation_side = "left"
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, revision=args.revision, dtype=torch.float32
    ).eval()

    def score_pair(context: str, answers: list[str]) -> tuple[list[float], float]:
        texts = []
        for answer in answers:
            messages = [{"role": "user", "content": context}, {"role": "assistant", "content": answer}]
            texts.append(tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False))
        inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=args.max_length)
        started = time.perf_counter()
        with torch.inference_mode():
            values = [float(x) for x in model(**inputs).logits.squeeze(-1).tolist()]
        return values, (time.perf_counter() - started) * 1000

    output.parent.mkdir(parents=True, exist_ok=True)
    completed: set[str] = set()
    if output.exists():
        for line in output.read_text(encoding="utf-8").splitlines():
            if line.strip():
                completed.add(str(json.loads(line)["item_id"]))
    with output.open("a", encoding="utf-8") as handle:
        for index, item in enumerate(items, 1):
            if item.id in completed:
                continue
            (score_a, score_b), latency = score_pair(item.context, [item.response_a, item.response_b])
            probability_a = sigmoid(score_a - score_b)
            base = {
                "item_id": item.id, "category": item.category, "source": item.source,
                "model": args.model, "model_revision": args.revision,
                "latency_ms": latency, "cost": 0.0,
                "raw": {"score_a": score_a, "score_b": score_b, "max_length": args.max_length},
            }
            rows = [
                {**base, "orientation": "original", "label": item.label,
                 "choice": "A" if score_a >= score_b else "B",
                 "probability_a": probability_a, "probability_b": 1 - probability_a},
                {**base, "orientation": "swapped", "label": "B" if item.label == "A" else "A",
                 "choice": "B" if score_a >= score_b else "A",
                 "probability_a": 1 - probability_a, "probability_b": probability_a},
            ]
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            print(f"[{index}/{len(items)}] {item.id}", flush=True)

    resolved_revision = getattr(model.config, "_commit_hash", None) or args.revision
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "adapter": "local_bradley_terry_reward_model", "model": args.model,
        "requested_revision": args.revision, "resolved_revision": resolved_revision,
        "data": args.data, "data_sha256": file_sha256(Path(args.data)),
        "dataset_sha256": file_sha256(Path(args.data)),
        "items": len(items), "judgments": len(items) * 2, "max_length": args.max_length,
        "python": platform.python_version(), "torch": torch.__version__,
        "transformers": transformers.__version__,
        "config": {
            "experiment": {"name": output.parent.name, "dataset": args.data,
                           "output_dir": str(output.parent), "swap_positions": True},
            "model": {"adapter": "local_bradley_terry_reward_model", "id": args.model},
            "metrics": {"ece_bins": 10},
        },
    }
    (output.parent / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
