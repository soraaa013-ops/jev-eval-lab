#!/usr/bin/env python3
"""Download RewardBench 2 through the Hugging Face datasets server."""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

DATASET = "allenai/reward-bench-2"

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--output", required=True); args = p.parse_args()
    rows = []
    for offset in range(0, 1865, 100):
        query = urlencode({"dataset": DATASET, "config": "default", "split": "test", "offset": offset, "length": 100})
        for attempt in range(5):
            try:
                with urlopen("https://datasets-server.huggingface.co/rows?" + query, timeout=60) as response:
                    page = json.load(response)["rows"]
                break
            except Exception:
                if attempt == 4: raise
                time.sleep(2 ** attempt)
        rows.extend(entry["row"] for entry in page)
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows)
    output.write_text(payload, encoding="utf-8")
    print(json.dumps({"rows": len(rows), "sha256": hashlib.sha256(payload.encode()).hexdigest(), "output": str(output)}, indent=2))

if __name__ == "__main__": main()

