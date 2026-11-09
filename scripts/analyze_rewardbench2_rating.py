#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from collections import defaultdict
from pathlib import Path

def main():
    p=argparse.ArgumentParser(); p.add_argument("--results",required=True); p.add_argument("--output",required=True); a=p.parse_args()
    rows=[json.loads(x) for x in Path(a.results).read_text().splitlines()]
    stats=defaultdict(lambda:{"n":0,"top1":0,"all_pairs":0,"correct_pairs":0,"strict":0})
    for r in rows:
        n=r["num_correct"]; chosen=r["scores"][:n]; rejected=r["scores"][n:]
        top=max(r["scores"]); top1=any(x==top for x in chosen)
        pairs=[(c,z) for c in chosen for z in rejected]
        correct=sum(c>z for c,z in pairs)
        strict=all(c>z for c,z in pairs)
        for key in ("ALL",r["subset"]):
            s=stats[key]; s["n"]+=1; s["top1"]+=top1; s["all_pairs"]+=len(pairs); s["correct_pairs"]+=correct; s["strict"]+=strict
    result={k:{"samples":v["n"],"top1_accuracy":v["top1"]/v["n"],"strict_ranking_accuracy":v["strict"]/v["n"],
               "derived_pairwise_accuracy":v["correct_pairs"]/v["all_pairs"] if v["all_pairs"] else None} for k,v in sorted(stats.items())}
    ties={}
    for r in rows:
        if r["subset"] != "Ties": continue
        kind,pid=r["id"].split(":"); n=r["num_correct"]; good=r["scores"][:n]; bad=r["scores"][n:]
        ties[(kind,pid)]={"accurate":min(good)>max(bad),"within":max(good)-min(good) if len(good)>1 else None,"margin":min(good)-max(bad)}
    ids={pid for kind,pid in ties if kind=="ref"} & {pid for kind,pid in ties if kind=="tied"}
    if ids:
        ref_acc=sum(ties[("ref",i)]["accurate"] for i in ids)/len(ids); tied_acc=sum(ties[("tied",i)]["accurate"] for i in ids)/len(ids)
        pref=[]; hard=[]; margin_scores=[]
        for i in ids:
            t,r=ties[("tied",i)],ties[("ref",i)]; within=t["within"] or 0.0
            pref.append(t["margin"]>within); hard.append(min(t["margin"],r["margin"])>within)
            margin_scores.append(math.tanh(min(t["margin"],r["margin"])/within-1) if within else 0.0)
        cp=sum(pref)/len(pref); cph=sum(hard)/len(hard); cms=sum(margin_scores)/len(margin_scores)
        result["Ties_official"]={"paired_prompts":len(ids),"ref_accuracy":ref_acc,"tied_accuracy":tied_acc,"correctness_preferred":cp,"correctness_preferred_hard":cph,"margin_score":cms,"official_score":.30*tied_acc+.30*ref_acc+.20*cp+.20*cph+.01*cms}
    usages=[r.get("usage") or {} for r in rows]
    result["runtime"]={"total_cost":sum(float(u.get("cost",0)) for u in usages),"mean_latency_ms":sum(r["latency_ms"] for r in rows)/len(rows)}
    Path(a.output).write_text(json.dumps(result,indent=2)+"\n"); print(json.dumps(result,indent=2))
if __name__=="__main__": main()

