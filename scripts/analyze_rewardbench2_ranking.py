#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from collections import defaultdict
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--results",required=True);p.add_argument("--output",required=True);a=p.parse_args()
 rows=[json.loads(x) for x in Path(a.results).read_text().splitlines()]; stats=defaultdict(list)
 for r in rows:stats[r["subset"]].append(r["correct"]);stats["ALL_NON_TIES"].append(r["correct"])
 result={k:{"samples":len(v),"accuracy":sum(v)/len(v)} for k,v in sorted(stats.items())}
 result["runtime"]={"total_cost":sum(float((r.get("usage") or {}).get("cost",0)) for r in rows),"mean_latency_ms":sum(r["latency_ms"] for r in rows)/len(rows)}
 Path(a.output).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
if __name__=="__main__":main()
