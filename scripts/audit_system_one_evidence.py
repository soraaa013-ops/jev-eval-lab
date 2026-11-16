"""Recompute a fixed external Jev/Laya comparison; never calls a model API.

Raw upstream files stay in a cache. Outputs record hashes and per-case derived
decisions, not benchmark prompts. External inference is NOT our own inference.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import urllib.request
from collections import defaultdict

REV = "e74dfb6d99ed041f5f5240af386ba5272de84cdd"
BASE = f"https://raw.githubusercontent.com/David-DL-Space/sys1-eval/{REV}/"
ROOT = Path(__file__).resolve().parents[1]


def score(case, row):
    key, gold = next(iter(case["gold"].items()))
    if not row.get("ok") or key not in row.get("answers", {}):
        return False, None
    answer = row["answers"][key]
    predicted = answer["noul"] >= .5 if isinstance(gold, bool) else answer["choice"]
    return predicted == gold, predicted


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, default=Path("/tmp/jev-external-audit"))
    args = ap.parse_args()
    out = ROOT / "artifacts/validation/system-one/external-reanalysis"
    out.mkdir(parents=True, exist_ok=True)
    provenance = []

    def read(rel):
        path = args.cache / rel
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(BASE + rel, timeout=60) as response:
                path.write_bytes(response.read())
        raw = path.read_bytes()
        provenance.append({"path": rel, "url": BASE + rel,
                           "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        return [json.loads(line) for line in raw.splitlines() if line.strip()]

    cases = read("bench/cases-large.jsonl")
    assert len(cases) == 2100 and len({c["id"] for c in cases}) == 2100
    runs = {}
    for model in ("jev", "laya"):
        raw = read(f"results/{model}-all.jsonl")
        assert len({r["id"] for r in raw}) == len(raw), "Ambiguous duplicate IDs"
        runs[model] = {r["id"]: r for r in raw}
        # Upstream corrected C after its builder omitted the user request.
        corrected = read(f"results/{model}-c-fixed.jsonl")
        assert len(corrected) == 300
        for row in corrected:
            assert row["track"] == "C_tool_guardrail"
            runs[model][row["id"]] = row
    groups = defaultdict(list)
    rows = []
    for case in cases:
        j, l = runs["jev"][case["id"]], runs["laya"][case["id"]]
        assert j["track"] == l["track"] == case["track"]
        jc, jp = score(case, j)
        lc, lp = score(case, l)
        row = {"id": case["id"], "track": case["track"],
               "gold": next(iter(case["gold"].values())),
               "jev_prediction": jp, "laya_prediction": lp,
               "jev_correct": int(jc), "laya_correct": int(lc)}
        rows.append(row)
        groups[case["track"]].append(row)
        groups["ALL"].append(row)
    summary = {}
    for group, values in sorted(groups.items()):
        n = len(values)
        summary[group] = {"n": n,
            "jev_correct": sum(r["jev_correct"] for r in values),
            "laya_correct": sum(r["laya_correct"] for r in values),
            "jev_only_correct": sum(r["jev_correct"] and not r["laya_correct"] for r in values),
            "laya_only_correct": sum(r["laya_correct"] and not r["jev_correct"] for r in values)}
        for model in ("jev", "laya"):
            summary[group][model + "_accuracy"] = summary[group][model + "_correct"] / n
    with (out / "per-case.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (out / "metrics.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "manifest.json").write_text(json.dumps({
        "evidence_type": "our_reanalysis_of_external_inference",
        "upstream_repository": "https://github.com/David-DL-Space/sys1-eval",
        "upstream_revision": REV, "sources": provenance,
        "scope": "2100-case six-track subset; not all 11 tracks; corrected C rows override all",
        "binary_threshold": .5, "invalid_output_policy": "count as wrong",
        "limitations": "Labels and inference are external; no new model calls; no claim about current checkpoints",
    }, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
