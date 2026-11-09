from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import os
import sys
import tomllib
from typing import Any

from . import __version__
from .adapters import make_adapter
from .core import PairwiseItem, file_sha256, load_jsonl, read_jsonl, stable_hash
from .metrics import compute_metrics


def load_config(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        config = tomllib.load(handle)
    for section in ("experiment", "model"):
        if section not in config:
            raise ValueError(f"missing [{section}] section")
    for key in ("name", "dataset", "output_dir"):
        if key not in config["experiment"]:
            raise ValueError(f"missing experiment.{key}")
    for key in ("adapter", "id"):
        if key not in config["model"]:
            raise ValueError(f"missing model.{key}")
    make_adapter(config["model"])
    secret_path = config["model"].get("secrets_file")
    if secret_path:
        root = find_project_root(path.parent)
        resolved = resolve(root, str(secret_path))
        if not resolved.exists():
            raise ValueError(f"secrets file does not exist: {resolved}")
        with resolved.open("rb") as handle:
            secrets = tomllib.load(handle)
        env_name = str(config["model"].get("api_key_env", "OPENROUTER_API_KEY"))
        value = secrets.get("openrouter", {}).get("api_key")
        if value and not os.environ.get(env_name):
            os.environ[env_name] = str(value)
    return config


def resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def validate(config_path: Path) -> tuple[dict[str, Any], Path, list[PairwiseItem]]:
    config_path = config_path.resolve()
    config = load_config(config_path)
    root = find_project_root(config_path.parent)
    dataset = resolve(root, str(config["experiment"]["dataset"]))
    items = load_jsonl(dataset)
    if not items:
        raise ValueError("dataset is empty")
    return config, root, items


def find_project_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    raise ValueError("could not find project root containing pyproject.toml")


def command_validate(args: argparse.Namespace) -> None:
    config, root, items = validate(Path(args.config))
    dataset = resolve(root, config["experiment"]["dataset"])
    print(json.dumps({
        "valid": True, "items": len(items), "dataset": str(dataset),
        "dataset_sha256": file_sha256(dataset), "adapter": config["model"]["adapter"],
        "model": config["model"]["id"],
    }, indent=2))


def command_run(args: argparse.Namespace) -> None:
    config_path = Path(args.config).resolve()
    config, root, items = validate(config_path)
    experiment, model = config["experiment"], config["model"]
    output = resolve(root, str(experiment["output_dir"]))
    output.mkdir(parents=True, exist_ok=True)
    result_path = output / "results.jsonl"
    completed = {str(row["request_id"]) for row in read_jsonl(result_path)}
    adapter = make_adapter(model)
    limit = int(experiment.get("limit", 0))
    if limit > 0:
        items = items[:limit]
    jobs: list[tuple[PairwiseItem, str]] = []
    for item in items:
        jobs.append((item, "original"))
        if bool(experiment.get("swap_positions", True)):
            jobs.append((item.swapped(), "swapped"))
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(), "tool_version": __version__,
        "python": platform.python_version(), "config_path": str(config_path), "config": config,
        "dataset_sha256": file_sha256(resolve(root, str(experiment["dataset"]))),
        "planned_judgments": len(jobs),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending: list[tuple[int, PairwiseItem, str, str]] = []
    for index, (item, orientation) in enumerate(jobs, 1):
        request_id = stable_hash({"item": asdict(item), "orientation": orientation, "model": model})
        if request_id in completed:
            print(f"[{index}/{len(jobs)}] cached {item.id} {orientation}")
        else:
            pending.append((index, item, orientation, request_id))

    concurrency = max(1, int(experiment.get("concurrency", 1)))
    with result_path.open("a", encoding="utf-8") as handle, ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(adapter.judge, item): (index, item, orientation, request_id)
                   for index, item, orientation, request_id in pending}
        for future in as_completed(futures):
            index, item, orientation, request_id = futures[future]
            try:
                judgment = future.result()
            except Exception as exc:
                for other in futures:
                    other.cancel()
                raise RuntimeError(f"{item.id} {orientation} failed: {exc}") from exc
            row = {
                "request_id": request_id, "item_id": item.id, "orientation": orientation,
                "label": item.label, "category": item.category, "source": item.source,
                "choice": judgment.choice, "probability_a": judgment.probability_a,
                "probability_b": judgment.probability_b, "model": judgment.model,
                "latency_ms": judgment.latency_ms, "usage": judgment.usage,
                "cost": judgment.cost, "raw": judgment.raw,
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            completed.add(request_id)
            print(f"[{index}/{len(jobs)}] {item.id} {orientation}: {judgment.choice}")
    print(f"results: {result_path}")


def command_analyze(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir).resolve()
    rows = list(read_jsonl(run_dir / "results.jsonl"))
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    bins = int(manifest["config"].get("metrics", {}).get("ece_bins", 10))
    metrics = compute_metrics(rows, bins)
    path = run_dir / "metrics.json"
    path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


def command_report(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir).resolve()
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    def fmt(value: Any) -> str:
        return "n/a" if value is None else f"{value:.4f}" if isinstance(value, float) else str(value)
    categories = "\n".join(f"| {k} | {fmt(v)} |" for k, v in metrics["category_accuracy"].items())
    text = f"""# Run report: {manifest['config']['experiment']['name']}

Generated from immutable raw result rows. This report is descriptive; the
synthetic smoke dataset must not be used to claim model quality.

## Run identity

- Model requested: `{manifest['config']['model']['id']}`
- Adapter: `{manifest['config']['model']['adapter']}`
- Dataset SHA-256: `{manifest['dataset_sha256']}`
- Created: {manifest['created_at']}

## Aggregate metrics

| Metric | Value |
|---|---:|
| Items | {metrics['items']} |
| Judgments | {metrics['judgments']} |
| Per-orientation accuracy | {fmt(metrics['accuracy'])} |
| Strict swapped-order accuracy | {fmt(metrics['strict_swap_accuracy'])} |
| Swap consistency | {fmt(metrics['swap_consistency'])} |
| Brier score | {fmt(metrics['brier_score'])} |
| Expected calibration error | {fmt(metrics['ece'])} |
| Latency p50 (ms) | {fmt(metrics['latency_ms_p50'])} |
| Latency p95 (ms) | {fmt(metrics['latency_ms_p95'])} |
| Reported total cost | {fmt(metrics['reported_total_cost'])} |

## Accuracy by category

| Category | Accuracy |
|---|---:|
{categories}

## Interpretation guardrails

- Compare confidence intervals on the full benchmark before ranking models.
- Treat conflicting A/B and B/A verdicts as failures in the strict metric.
- Hosted-model reruns may change even when request configuration is pinned.
- Calibration is dataset-specific; do not transfer a threshold without validation.
"""
    path = run_dir / "report.md"
    path.write_text(text, encoding="utf-8")
    print(f"report: {path}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="jev-eval")
    result.add_argument("--version", action="version", version=__version__)
    commands = result.add_subparsers(dest="command", required=True)
    validate_parser = commands.add_parser("validate")
    validate_parser.add_argument("--config", required=True)
    validate_parser.set_defaults(func=command_validate)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--config", required=True)
    run_parser.set_defaults(func=command_run)
    analyze_parser = commands.add_parser("analyze")
    analyze_parser.add_argument("--run-dir", required=True)
    analyze_parser.set_defaults(func=command_analyze)
    report_parser = commands.add_parser("report")
    report_parser.add_argument("--run-dir", required=True)
    report_parser.set_defaults(func=command_report)
    return result


def main() -> None:
    try:
        args = parser().parse_args()
        args.func(args)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()

