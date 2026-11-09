#!/usr/bin/env python3
"""Bootstrap confidence intervals, paired differences, reliability, and errors."""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

from jev_eval.metrics import compute_metrics


def load(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def item_groups(rows: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[str(row["item_id"])].append(row)
    return groups


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * q)]


def bootstrap(groups: dict[str, list[dict]], seed: int, samples: int) -> dict:
    rng, ids = random.Random(seed), sorted(groups)
    item_accuracy = {key: mean(float(x["choice"] == x["label"]) for x in value) for key, value in groups.items()}
    item_strict = {}
    for key, value in groups.items():
        orientations = {x["orientation"]: x for x in value}
        original, swapped = orientations.get("original"), orientations.get("swapped")
        item_strict[key] = float(bool(original and swapped and original["choice"] != swapped["choice"]
                                      and original["choice"] == original["label"]
                                      and swapped["choice"] == swapped["label"]))
    accuracy, strict = [], []
    for _ in range(samples):
        chosen = [rng.choice(ids) for _ in ids]
        accuracy.append(mean(item_accuracy[x] for x in chosen))
        strict.append(mean(item_strict[x] for x in chosen))
    point = compute_metrics([r for rows in groups.values() for r in rows])
    return {
        "accuracy": {"estimate": point["accuracy"], "ci95": [percentile(accuracy, .025), percentile(accuracy, .975)]},
        "strict_swap_accuracy": {"estimate": point["strict_swap_accuracy"], "ci95": [percentile(strict, .025), percentile(strict, .975)]},
    }


def paired(a: dict[str, list[dict]], b: dict[str, list[dict]], seed: int, samples: int) -> dict:
    rng, ids = random.Random(seed), sorted(set(a) & set(b))
    def item_accuracy(group: list[dict]) -> float:
        return mean(float(x["choice"] == x["label"]) for x in group)
    item_delta = {x: item_accuracy(a[x]) - item_accuracy(b[x]) for x in ids}
    deltas = []
    for _ in range(samples):
        sample = [rng.choice(ids) for _ in ids]
        deltas.append(mean(item_delta[x] for x in sample))
    point = mean(item_delta.values())
    return {"accuracy_difference": point, "ci95": [percentile(deltas, .025), percentile(deltas, .975)],
            "probability_a_better": mean(float(x > 0) for x in deltas)}


def reliability(rows: list[dict], bins: int = 10) -> list[dict]:
    bucketed: list[list[tuple[float, float]]] = [[] for _ in range(bins)]
    for row in rows:
        pa = row.get("probability_a")
        if pa is None:
            continue
        confidence = float(pa) if row["choice"] == "A" else 1 - float(pa)
        bucketed[min(int(confidence * bins), bins - 1)].append((confidence, float(row["choice"] == row["label"])))
    return [{"bin": i, "count": len(v), "mean_confidence": mean(x for x, _ in v),
             "accuracy": mean(y for _, y in v)} for i, v in enumerate(bucketed) if v]


def risk_coverage(rows: list[dict]) -> list[dict]:
    ranked = []
    for row in rows:
        pa = row.get("probability_a")
        if pa is None:
            continue
        confidence = float(pa) if row["choice"] == "A" else 1 - float(pa)
        ranked.append((confidence, float(row["choice"] == row["label"])))
    ranked.sort(reverse=True)
    points = []
    for step in range(1, 11):
        target_count = max(1, round(len(ranked) * step / 10))
        threshold = ranked[target_count - 1][0]
        selected = [value for value in ranked if value[0] >= threshold]
        count = len(selected)
        points.append({"coverage": count / len(ranked), "risk": 1 - mean(x[1] for x in selected),
                       "min_confidence": threshold, "count": count})
    return points


def svg(curves: dict[str, list[dict]], output: Path, x_key: str = "mean_confidence",
        y_key: str = "accuracy", title: str = "JudgeBench reliability diagram",
        x_label: str = "Mean confidence", y_label: str = "Observed accuracy", diagonal: bool = True) -> None:
    colors = ["#2563eb", "#dc2626", "#059669", "#7c3aed"]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="760" height="520" viewBox="0 0 760 520">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="380" y="28" text-anchor="middle" font-family="sans-serif" font-size="19">{title}</text>']
    if diagonal:
        parts.append('<line x1="70" y1="450" x2="700" y2="70" stroke="#aaa" stroke-dasharray="5 5"/>')
    for tick in range(6):
        x, y = 70 + tick * 126, 450 - tick * 76
        parts += [f'<text x="{x}" y="475" text-anchor="middle" font-family="sans-serif" font-size="12">{tick/5:.1f}</text>',
                  f'<text x="52" y="{y+4}" text-anchor="end" font-family="sans-serif" font-size="12">{tick/5:.1f}</text>']
    parts += [f'<text x="385" y="505" text-anchor="middle" font-family="sans-serif">{x_label}</text>',
              f'<text x="18" y="265" transform="rotate(-90 18 265)" text-anchor="middle" font-family="sans-serif">{y_label}</text>']
    for idx, (name, points) in enumerate(curves.items()):
        color = colors[idx % len(colors)]
        coords = " ".join(f'{70+p[x_key]*630:.1f},{450-p[y_key]*380:.1f}' for p in points)
        parts.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2"/>')
        for p in points:
            parts.append(f'<circle cx="{70+p[x_key]*630:.1f}" cy="{450-p[y_key]*380:.1f}" r="4" fill="{color}"/>')
        parts.append(f'<text x="550" y="{55+idx*20}" font-family="sans-serif" font-size="13" fill="{color}">{name}</text>')
    parts.append('</svg>')
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", required=True, help="name=run-directory")
    parser.add_argument("--output-dir", default="artifacts/analysis")
    parser.add_argument("--samples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20261109)
    args = parser.parse_args()
    runs = {x.split("=", 1)[0]: Path(x.split("=", 1)[1]) for x in args.run}
    rows = {name: load(path / "results.jsonl") for name, path in runs.items()}
    groups = {name: item_groups(value) for name, value in rows.items()}
    statistics = {"seed": args.seed, "bootstrap_samples": args.samples,
                  "models": {name: bootstrap(value, args.seed, args.samples) for name, value in groups.items()},
                  "paired": {}}
    names = list(runs)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            statistics["paired"][f"{left}_minus_{right}"] = paired(groups[left], groups[right], args.seed, args.samples)
    curves = {name: reliability(value) for name, value in rows.items()}
    risk_curves = {name: risk_coverage(value) for name, value in rows.items()}
    output = Path(args.output_dir); output.mkdir(parents=True, exist_ok=True)
    (output / "statistics.json").write_text(json.dumps(statistics, indent=2) + "\n", encoding="utf-8")
    (output / "reliability.json").write_text(json.dumps(curves, indent=2) + "\n", encoding="utf-8")
    svg(curves, output / "reliability.svg")
    (output / "risk-coverage.json").write_text(json.dumps(risk_curves, indent=2) + "\n", encoding="utf-8")
    svg(risk_curves, output / "risk-coverage.svg", "coverage", "risk",
        "JudgeBench risk–coverage", "Coverage", "Selective risk", False)

    lines = ["# JudgeBench qualitative error audit", "", "High-confidence errors are ranked by the probability assigned to the selected answer.", ""]
    for name, values in rows.items():
        errors = []
        for row in values:
            if row["choice"] == row["label"] or row.get("probability_a") is None:
                continue
            confidence = float(row["probability_a"]) if row["choice"] == "A" else 1 - float(row["probability_a"])
            errors.append((confidence, row))
        lines += [f"## {name}", "", f"Errors: {len(errors)}/{len(values)}. Top 15 high-confidence failures:", "",
                  "| item | orientation | source | gold | choice | confidence |", "|---|---|---|---:|---:|---:|"]
        for confidence, row in sorted(errors, reverse=True, key=lambda x: x[0])[:15]:
            lines.append(f'| {row["item_id"]} | {row["orientation"]} | {row.get("source", "")} | {row["label"]} | {row["choice"]} | {confidence:.3f} |')
        lines.append("")
    (output / "error-audit.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
