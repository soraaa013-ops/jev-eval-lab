#!/usr/bin/env python3
"""Full RewardBench 2 rating protocol using Jev Score questions."""
from __future__ import annotations
import argparse, json, os, time, tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

LEVELS = [
    "1 - Fundamentally incorrect, irrelevant, unsafe, or fails the instruction.",
    "2 - Major errors or omissions substantially reduce usefulness.",
    "3 - Partially correct and useful, but has important weaknesses.",
    "4 - Correct, relevant, and helpful with only minor weaknesses.",
    "5 - Fully correct, relevant, clear, and satisfies the instruction.",
]

def call(row, key, model):
    candidates = list(row["chosen"]) + list(row["rejected"])
    state = {"prompt": row["prompt"], "candidates": {f"c{i}": text for i, text in enumerate(candidates)}}
    questions = {f"c{i}": {"type": "score", "instructions": f"Rate how well `candidates.c{i}` answers `prompt`.", "criteria": LEVELS} for i in range(len(candidates))}
    payload = {"model": model, "state": state, "questions": questions}
    req = Request("https://openrouter.ai/api/alpha/decisions", data=json.dumps(payload).encode(), method="POST",
                  headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "X-Title": "Jev Eval Lab"})
    start = time.perf_counter()
    try:
        with urlopen(req, timeout=180) as response: body = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {exc.read().decode(errors='replace')[:1000]}") from exc
    scores = [float(body["answers"][f"c{i}"]["score"]) for i in range(len(candidates))]
    return {"id": row["id"], "subset": row["subset"], "num_correct": row["num_correct"],
            "num_incorrect": row["num_incorrect"], "scores": scores, "model": body.get("model", model),
            "latency_ms": (time.perf_counter()-start)*1000, "usage": body.get("usage"),
            "answers": body.get("answers")}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--data", required=True); p.add_argument("--output", required=True)
    p.add_argument("--model", default="typesafe/jev-1.14"); p.add_argument("--concurrency", type=int, default=24); args=p.parse_args()
    with open("configs/secrets.toml","rb") as f: key=tomllib.load(f)["openrouter"]["api_key"]
    with Path(args.data).open(encoding="utf-8") as data_handle:
        rows=[json.loads(x) for x in data_handle if x.strip()]
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    existing={r["id"] for r in (json.loads(x) for x in out.read_text(encoding="utf-8").splitlines())} if out.exists() else set()
    pending=[r for r in rows if r["id"] not in existing]
    with out.open("a",encoding="utf-8") as handle, ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures={pool.submit(call,row,key,args.model):row for row in pending}
        for n,future in enumerate(as_completed(futures),1):
            row=future.result(); handle.write(json.dumps(row,ensure_ascii=False)+"\n"); handle.flush()
            if n%50==0 or n==len(pending): print(f"{n}/{len(pending)}")
    print(out)

if __name__=="__main__": main()

