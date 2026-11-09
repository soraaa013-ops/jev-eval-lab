#!/usr/bin/env python3
"""Download and convert a pinned JudgeBench release to the local pairwise contract."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

COMMIT = "e2c52c284e735e139b3daa61c206ee208f36c461"
FILES = {
    "gpt": "data/dataset=judgebench,response_model=gpt-4o-2024-05-13.jsonl",
    "claude": "data/dataset=judgebench,response_model=claude-3-5-sonnet-20240620.jsonl",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=sorted(FILES), default="gpt")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    url = f"https://raw.githubusercontent.com/ScalerLab/JudgeBench/{COMMIT}/{FILES[args.split]}"
    raw = urlopen(url, timeout=60).read()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8") as handle:
        for line in raw.decode().splitlines():
            source = json.loads(line)
            label = {"A>B": "A", "B>A": "B"}[source["label"]]
            row = {
                "id": source["pair_id"], "context": source["question"],
                "response_a": source["response_A"], "response_b": source["response_B"],
                "label": label, "category": str(source["source"]).split("-")[0],
                "source": source["source"],
                "metadata": {"original_id": source["original_id"], "response_model": source["response_model"]},
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    print(json.dumps({"rows": count, "output": str(output), "source_commit": COMMIT,
                      "source_sha256": hashlib.sha256(raw).hexdigest()}, indent=2))


if __name__ == "__main__":
    main()

