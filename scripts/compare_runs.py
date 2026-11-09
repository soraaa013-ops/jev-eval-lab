#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", required=True, help="name=run-directory")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    runs: dict[str, Path] = {}
    for value in args.run:
        name, path = value.split("=", 1)
        runs[name] = Path(path)

    records: dict[tuple[str, str], dict[str, object]] = {}
    for name, directory in runs.items():
        for line in (directory / "results.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            key = (row["item_id"], row["orientation"])
            record = records.setdefault(key, {
                "item_id": row["item_id"], "orientation": row["orientation"],
                "label": row["label"], "category": row["category"], "source": row["source"],
            })
            record[f"{name}_choice"] = row["choice"]
            record[f"{name}_probability_a"] = row["probability_a"]
            record[f"{name}_correct"] = row["choice"] == row["label"]
            record[f"{name}_latency_ms"] = row["latency_ms"]
            record[f"{name}_cost"] = row["cost"]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(records.values(), key=lambda x: (str(x["item_id"]), str(x["orientation"])))
    fields = list(rows[0])
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} judgments to {output}")


if __name__ == "__main__":
    main()

