#!/usr/bin/env python3
"""Download a pinned RewardBench 2 parquet revision and convert to JSONL."""
from __future__ import annotations
import argparse, hashlib, json, tempfile
from pathlib import Path
from urllib.request import urlopen

DATASET = "allenai/reward-bench-2"
REVISION = "7ff08853b0d5686e79b13fda8677024f566a104a"

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--output", required=True); args = p.parse_args()
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise SystemExit("Install the dataset extra: pip install -e '.[datasets]'") from exc
    url = f"https://huggingface.co/datasets/{DATASET}/resolve/{REVISION}/data/test-00000-of-00001.parquet"
    raw = urlopen(url, timeout=120).read()
    with tempfile.NamedTemporaryFile(suffix=".parquet") as handle:
        handle.write(raw); handle.flush()
        rows = parquet.read_table(handle.name).to_pylist()
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows)
    output.write_text(payload, encoding="utf-8")
    print(json.dumps({"rows": len(rows), "sha256": hashlib.sha256(payload.encode()).hexdigest(),
                      "output": str(output), "source_revision": REVISION,
                      "source_parquet_sha256": hashlib.sha256(raw).hexdigest()}, indent=2))

if __name__ == "__main__": main()

