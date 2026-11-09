from __future__ import annotations

from collections import defaultdict
import math
from statistics import median
from typing import Any


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def compute_metrics(rows: list[dict[str, Any]], bins: int = 10) -> dict[str, Any]:
    if not rows:
        raise ValueError("no result rows")
    by_item: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    correct: list[float] = []
    brier: list[float] = []
    confidence_correct: list[tuple[float, float]] = []
    latencies: list[float] = []
    costs: list[float] = []
    categories: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        orientation = str(row["orientation"])
        by_item[str(row["item_id"])][orientation] = row
        ok = float(row["choice"] == row["label"])
        correct.append(ok)
        categories[str(row.get("category", "uncategorized"))].append(ok)
        latencies.append(float(row.get("latency_ms", 0)))
        if row.get("cost") is not None:
            costs.append(float(row["cost"]))
        pa = row.get("probability_a")
        if pa is not None:
            pa = float(pa)
            target_a = float(row["label"] == "A")
            brier.append((pa - target_a) ** 2)
            predicted_confidence = pa if row["choice"] == "A" else 1 - pa
            confidence_correct.append((predicted_confidence, ok))

    consistent: list[float] = []
    strict: list[float] = []
    for pair in by_item.values():
        if "original" not in pair or "swapped" not in pair:
            continue
        original, swapped = pair["original"], pair["swapped"]
        agrees = original["choice"] != swapped["choice"]
        consistent.append(float(agrees))
        strict.append(float(agrees and original["choice"] == original["label"] and swapped["choice"] == swapped["label"]))

    metrics = {
        "judgments": len(rows), "items": len(by_item), "accuracy": _mean(correct),
        "strict_swap_accuracy": _mean(strict), "swap_consistency": _mean(consistent),
        "brier_score": _mean(brier), "ece": expected_calibration_error(confidence_correct, bins),
        "latency_ms_p50": median(latencies), "latency_ms_p95": percentile(latencies, 0.95),
        "reported_total_cost": sum(costs) if costs else None,
        "category_accuracy": {key: _mean(value) for key, value in sorted(categories.items())},
    }
    return metrics


def expected_calibration_error(values: list[tuple[float, float]], bins: int) -> float | None:
    if not values:
        return None
    buckets: list[list[tuple[float, float]]] = [[] for _ in range(bins)]
    for confidence, correct in values:
        index = min(int(max(0.0, min(1.0, confidence)) * bins), bins - 1)
        buckets[index].append((confidence, correct))
    total = len(values)
    return sum(
        len(bucket) / total * abs(sum(x for x, _ in bucket) / len(bucket) - sum(y for _, y in bucket) / len(bucket))
        for bucket in buckets if bucket
    )


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * quantile
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

