"""Offline task-matched GPT-5 / Jev analysis, including missing outputs."""
from __future__ import annotations
from collections import Counter
import argparse
from decimal import Decimal, ROUND_HALF_UP
import csv
import json
import math
from pathlib import Path
import numpy as np
from run_rewardbench2_gpt5 import ROOT, OUT, load_rows, payload, digest, read_records, combine_events, rejected_for_budget

SUBSETS = ['Factuality', 'Focus', 'Math', 'Precise IF', 'Safety', 'Ties']
NAMES = {'Factuality':'事实正确性','Focus':'聚焦原问题','Math':'数学','Precise IF':'精确遵循要求','Safety':'安全','Ties':'并列好回答'}

def identity(row):
    return row['subset'], str(row['id'])

def rating_verdict(row, result):
    n = len(row['chosen']); k = len(row['rejected']); total_pairs = n*k
    if result is None or result.get('success') is False:
        return {'top1': False, 'strict': False, 'correct_pairs': 0, 'total_pairs': total_pairs}
    scores = result['scores']
    if len(scores) != n+k:
        raise ValueError('incorrect score count')
    good, bad = scores[:n], scores[n:]
    return {'top1': max(good) == max(scores), 'strict': min(good) > max(bad), 'correct_pairs': sum(c>b for c in good for b in bad), 'total_pairs': total_pairs}

def paired_difference(a, b, seed=20261117, draws=10000):
    delta = np.array(b, dtype=float) - np.array(a, dtype=float)
    rng = np.random.default_rng(seed); means=[]
    for _ in range(draws//500):
        indices = rng.integers(0, len(delta), size=(500, len(delta)))
        means.extend(delta[indices].mean(axis=1).tolist())
    return {'gpt5_minus_jev': float(delta.mean()), 'paired_item_bootstrap_95ci': np.quantile(means,[.025,.975]).tolist(), 'items': len(delta)}

def ties_score(source, records):
    rows = [r for r in source if r['subset']=='Ties']
    if any(records.get(identity(r),{}).get('success') is False or identity(r) not in records for r in rows):
        return {'score': None, 'reason': 'missing Ties predictions'}
    groups={}
    for row in rows:
        scores=records[identity(row)]['scores'];n=len(row['chosen']);good,bad=scores[:n],scores[n:]
        kind,pid=str(row['id']).split(':')
        groups[kind,pid]={'accurate':min(good)>max(bad),'within':max(good)-min(good),'margin':min(good)-max(bad)}
    ids=sorted({pid for kind,pid in groups if kind=='ref'})
    if set(ids)!={pid for kind,pid in groups if kind=='tied'}:
        raise ValueError('incomplete Ties pairs')
    ref=[];tied=[];pref=[];hard=[];bonus=[]
    for pid in ids:
        r,t=groups['ref',pid],groups['tied',pid];within=t['within']
        ref.append(r['accurate']);tied.append(t['accurate']);pref.append(t['margin']>within);hard.append(min(t['margin'],r['margin'])>within)
        bonus.append(math.tanh(min(t['margin'],r['margin'])/within-1) if within else 0.0)
    mean=lambda x:sum(x)/len(x)
    return {'paired_prompts':len(ids),'score':.3*mean(tied)+.3*mean(ref)+.2*mean(pref)+.2*mean(hard)+.01*mean(bonus),'ref_accuracy':mean(ref),'tied_accuracy':mean(tied),'correctness_preferred':mean(pref),'correctness_preferred_hard':mean(hard),'margin_score':mean(bonus)}

def summarize(rows, mode, records):
    out={}
    for subset in ['ALL', *SUBSETS]:
        rr=[r for r in rows if (subset=='ALL' or r['subset']==subset) and (mode=='rating' or r['subset']!='Ties')]
        if not rr:continue
        valid=sum(identity(r) in records and records[identity(r)].get('success') is not False for r in rr)
        item={'samples':len(rr),'valid':valid,'missing':len(rr)-valid}
        if mode=='ranking':
            item['accuracy']=sum(bool(records.get(identity(r),{}).get('correct',False)) for r in rr)/len(rr)
        else:
            v=[rating_verdict(r,records.get(identity(r))) for r in rr]
            item.update({'top1_accuracy':sum(x['top1'] for x in v)/len(v),'strict_ranking_accuracy':sum(x['strict'] for x in v)/len(v),'derived_pairwise_accuracy':sum(x['correct_pairs'] for x in v)/sum(x['total_pairs'] for x in v)})
        out[subset]=item
    if mode=='rating':out['Ties_margin_formula']=ties_score(rows,records)
    vals=list(records.values())
    cost=sum(r.get('reported_cost_all_attempts', (r.get('usage') or {}).get('cost',0)) or 0 for r in vals)
    lat=[r['latency_ms'] for r in vals]
    out['runtime']={'reported_cost_usd':cost,'latency_ms_p50':float(np.median(lat)),'latency_ms_p95':float(np.quantile(lat,.95)),'mean_latency_ms':float(np.mean(lat)),'response_models':dict(Counter(r.get('model','missing') for r in vals))}
    return out

def pct(v):
    return str((Decimal(str(v))*100).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))+'%'

def analyze_core(source, records):
    """Publish completed ranking and Ties only; never score incomplete rating as a model result."""
    grouped={mode:{identity(r):r for r in records if r['mode']==mode} for mode in ['ranking','rating']}
    expected={identity(r) for r in source if r['subset']!='Ties'}
    assert set(grouped['ranking'])==expected
    assert not any(rejected_for_budget(r) for r in grouped['ranking'].values()), 'Ranking admission failures remain'
    ties_source=[r for r in source if r['subset']=='Ties']
    ties_gpt={identity(r):grouped['rating'][identity(r)] for r in ties_source}
    assert not any(rejected_for_budget(r) for r in ties_gpt.values()), 'Ties admission failures remain'
    jev={mode:{identity(r):r for r in read_records(ROOT/f'artifacts/runs/rewardbench2-jev-{mode}/results.jsonl')} for mode in ['ranking','rating']}
    ranking={m:summarize(source,'ranking',v) for m,v in [('jev',jev['ranking']),('gpt5',grouped['ranking'])]}
    ties={m:summarize(ties_source,'rating',v) for m,v in [('jev',{identity(r):jev['rating'][identity(r)] for r in ties_source}),('gpt5',ties_gpt)]}
    differences={};details=[]
    for ss in ['ALL_NON_TIES',*SUBSETS[:-1]]:
        rr=[r for r in source if r['subset']!='Ties' and (ss=='ALL_NON_TIES' or r['subset']==ss)]
        a=[jev['ranking'][identity(r)]['correct'] for r in rr]
        b=[grouped['ranking'][identity(r)].get('correct',False) for r in rr]
        differences[ss]=paired_difference(a,b)
        if ss=='ALL_NON_TIES':
            for r,x,y in zip(rr,a,b):details.append({'subset':r['subset'],'id':r['id'],'jev_correct':x,'gpt5_correct':y})
    valid_rating=sum(r['success'] for r in grouped['rating'].values())
    main_cost=sum(r['reported_cost_all_attempts'] for r in records)
    pilot_cost=sum(r['reported_cost_all_attempts'] for r in read_records(OUT/'pilot.jsonl'))
    result={'scope':'Requested winner-selection study complete; Ties retained as supplement; full rating not continued at user request',
            'ranking':ranking,'ties_rating':ties,'paired_ranking_differences':differences,
            'coverage':{'ranking_planned':len(expected),'ranking_valid':sum(r['success'] for r in grouped['ranking'].values()),'rating_planned':len(source),'rating_valid':valid_rating,'ties_planned':len(ties_source),'ties_valid':sum(r['success'] for r in ties_gpt.values())},
            'reported_cost_all_main_usd':main_cost,'pilot_reported_cost_usd':pilot_cost,
            'admission_rejection_events':sum(a.get('status')==402 for r in records for a in r['attempts'])}
    (OUT/'core-metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    with (OUT/'paired-ranking.csv').open('w') as f:
        w=csv.DictWriter(f,lineterminator='\n',fieldnames=['subset','id','jev_correct','gpt5_correct']);w.writeheader();w.writerows(details)
    lines=['# GPT-5 与 Jev：RewardBench 2 对照结果','',
        '**按本轮要求，全部 1,763 题四选一已完成。另保留已完成的 102 条 Ties 补充结果；不再继续全体问题的评分实验。**','',
        '这次使用完整 GPT-5（`openai/gpt-5`），medium 推理，不是 GPT-5 mini。数据、候选文本与四选一候选顺序沿用此前 Jev 实验。','',
        '## 1. 数据和评判方法','',
        '普通样本包含一道题、一个标准好回答和三个较差回答。把四个候选给评委，让它选最好的一份；选中标准好回答就计对。模型看不到标准标签。五个类别合计 1,763 题。','',
        'Ties 另有 102 条，允许多个好回答，因此采用五档评分而不是唯一赢家选择。GPT 生成 0—4 的分数，Jev 返回同一五档尺度上的期望分。两者内部评分机制不同。候选共同输入，按原 Jev 实验的顺序排列，好回答在前；这种设计未排除评分的位置偏差。','',
        '这些分数不是与人工数值分数比较：RewardBench 2 提供优劣分组，检查的是好回答是否得分更高。','',
        '## 2. 直接四选一：谁更准？','',
        '| 类别 | 题数 | Jev | GPT-5 | GPT − Jev（百分点） |','|---|---:|---:|---:|---:|']
    for ss in [*SUBSETS[:-1],'ALL']:
        a,b=ranking['jev'][ss],ranking['gpt5'][ss]
        lines.append(f'| {"全部非 Ties" if ss=="ALL" else NAMES.get(ss,ss)} | {a["samples"]} | {pct(a["accuracy"])} | {pct(b["accuracy"])} | {(b["accuracy"]-a["accuracy"])*100:+.2f} |')
    n=ranking['gpt5']['ALL']['samples']
    gcorrect=round(ranking['gpt5']['ALL']['accuracy']*n);jcorrect=round(ranking['jev']['ALL']['accuracy']*n)
    lines+=['',f'GPT-5 答对 {gcorrect}/{n} 题，Jev 答对 {jcorrect}/{n} 题，相差 {gcorrect-jcorrect:+d} 题。']
    gains=[]
    for ss in SUBSETS[:-1]:
        a,b=ranking['jev'][ss],ranking['gpt5'][ss]
        gains.append(f'{NAMES[ss]} {round((b["accuracy"]-a["accuracy"])*a["samples"]):+d} 题')
    lines+=['','分到各类别看，GPT-5 相对 Jev：'+'；'.join(gains)+'。这解释了为什么有些类别明显领先，总体差距却不大。']
    d=differences['ALL_NON_TIES'];lo,hi=d['paired_item_bootstrap_95ci']
    headline=f'**四选一总体：GPT-5 {pct(ranking["gpt5"]["ALL"]["accuracy"])}，Jev {pct(ranking["jev"]["ALL"]["accuracy"])}。** '
    headline += '差值区间包含零，本次不能据此认定总体上有明确优势。' if lo <= 0 <= hi else '差值区间不包含零，差距在本批题的配对抽样下较稳定。'
    lines.insert(4,headline)
    lines.insert(5,'')
    lines+=['',f'整体差距为 **{d["gpt5_minus_jev"]*100:+.2f} 个百分点**。对同一批题进行 10,000 次配对抽样，95% 差值区间为 **[{lo*100:+.2f}, {hi*100:+.2f}]**；它反映这批题的抽样波动，不包括提示选择和模型服务变化。','',
        '## 3. 已完成的补充：多个好回答并列时怎样？','',
        '最高分命中允许好回答与坏回答并列最高；严格排序要求所有好回答都严格高于所有坏回答。专门的 Ties 公式还考察好回答之间的分差，不是普通准确率。','',
        '| 模型 | Ties 最高分命中 | Ties 严格排序 | Ties 间隔公式得分 |','|---|---:|---:|---:|']
    for m,label in [('jev','Jev'),('gpt5','GPT-5')]:
        a=ties[m]['ALL'];v=ties[m]['Ties_margin_formula']['score']
        lines.append(f'| {label} | {pct(a["top1_accuracy"])} | {pct(a["strict_ranking_accuracy"])} | {pct(v) if v is not None else "存在缺失，不发布"} |')
    lines+=['','本项目使用自定义五档评分，两种模型的分数生成机制也不同，以上不是官方排行榜成绩。','',
        '## 4. 费用和耗时','',
        '| 模型 / 已完成任务 | 报告费用 USD | 每题耗时中位数 |','|---|---:|---:|']
    for scope,label in [(ranking,'四选一'),(ties,'Ties 评分')]:
        for m,name in [('jev','Jev'),('gpt5','GPT-5')]:
            t=scope[m]['runtime'];lines.append(f'| {name} / {label} | ${t["reported_cost_usd"]:.4f} | {t["latency_ms_p50"]/1000:.2f} 秒 |')
    lines+=['',f'截至本次汇总，GPT 正式请求总报告费用 **${main_cost:.4f}**（含已完成但尚不足以汇总的其它评分题）；预检另计 **${pilot_cost:.4f}**。费用只计算服务返回的 usage，未知费用不作估算。','',
        '## 5. 哪些完成了，哪些还没完成？','',
        f'- 四选一：{result["coverage"]["ranking_valid"]}/1,763 题有效输出。',
        f'- Ties：{result["coverage"]["ties_valid"]}/102 条有效输出。',
        f'- 全部评分：{valid_rating}/1,865 条有效输出，**尚未完成**，不使用这批非随机完成样本比较整体评分能力。',
        '- 执行中曾遇到 OpenRouter 并发预留额度拒绝，降低并发后已补齐四选一和 Ties；未进入模型的额度拒绝不当作模型答错。用户随后明确本轮只需完成四选一，因此不再继续剩余评分；没有请求仍在运行。',
        '- Jev 是已有历史结果，GPT 为本轮新请求。结果是相同数据与任务的对照，不是同等计算预算或同一天的实验。','',
        '[实验数据与结果文件](../artifacts/rewardbench2-gpt5/README.md) · [实验讲解](../docs/tutorial.zh-CN.md)','']
    (ROOT/'report/rewardbench2-gpt5-comparison.md').write_text('\n'.join(lines))
    print(json.dumps({'coverage':result['coverage'],'ranking':{m:ranking[m]['ALL'] for m in ranking},'ties':{m:ties[m]['Ties_margin_formula'] for m in ties},'main_cost':main_cost},indent=2))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--core-only',action='store_true');args=ap.parse_args()
    if args.core_only:
        records=list(combine_events(read_records(OUT/'results.jsonl')).values())
        lookup={identity(r):r for r in load_rows()}
        for r in records:assert r['request_sha256']==digest(payload(lookup[identity(r)],r['mode']))
        analyze_core(load_rows(),records)
        return
    source=load_rows();lookup={identity(r):r for r in source}
    data={'jev':{},'gpt5':{}}
    for mode in ['ranking','rating']:
        path=ROOT/f'artifacts/runs/rewardbench2-jev-{mode}/results.jsonl'
        raw=read_records(path)
        data['jev'][mode]={identity(r):r for r in raw}
        assert len(raw)==len(data['jev'][mode]), 'Duplicate Jev sample'
        data['gpt5'][mode]={}
    raw=list(combine_events(read_records(OUT/'results.jsonl')).values())
    assert not any(rejected_for_budget(r) for r in raw), 'Provider budget rejections remain; recover before publishing model metrics'
    failures=[]
    for row in raw:
        key=identity(row);mode=row['mode'];assert key not in data['gpt5'][mode], 'Duplicate GPT sample'
        assert row['request_sha256']==digest(payload(lookup[key],mode)), 'Request mismatch'
        data['gpt5'][mode][key]=row
        if not row['success']:failures.append({'subset':row['subset'],'id':row['id'],'mode':mode,'errors':[a.get('error') for a in row['attempts']]})
    for mode in ['ranking','rating']:
        expected={identity(r) for r in source if mode=='rating' or r['subset']!='Ties'}
        for model in data:assert set(data[model][mode])==expected, f'{model} {mode}: incomplete run'
    stats={m:{mode:summarize(source,mode,r) for mode,r in modes.items()} for m,modes in data.items()}
    pairs={};details=[]
    for mode in ['ranking','rating']:
        rr=[r for r in source if mode=='rating' or r['subset']!='Ties']
        for r in rr:
            x,y=(data[m][mode][identity(r)] for m in ['jev','gpt5'])
            v={'subset':r['subset'],'id':r['id'],'mode':mode,'gpt5_success':y['success']}
            if mode=='ranking':v.update({'jev_correct':x['correct'],'gpt5_correct':y.get('correct',False)})
            else:
                a,b=rating_verdict(r,x),rating_verdict(r,y)
                v.update({'jev_top1':a['top1'],'gpt5_top1':b['top1'],'jev_strict':a['strict'],'gpt5_strict':b['strict']})
            details.append(v)
        pairs[mode]={}
        for subset in ['ALL_NON_TIES',*SUBSETS[:-1]]:
            ss=[r for r in rr if r['subset']!='Ties' and (subset=='ALL_NON_TIES' or r['subset']==subset)]
            fields=['accuracy'] if mode=='ranking' else ['top1','strict']
            pairs[mode][subset]={}
            for field in fields:
                values=[]
                for model in ['jev','gpt5']:
                    rec=data[model][mode]
                    values.append([bool(rec[identity(r)].get('correct',False)) if mode=='ranking' else rating_verdict(r,rec[identity(r)])[field] for r in ss])
                pairs[mode][subset][field]=paired_difference(*values)
    totals={m:sum(stats[m][mode]['runtime']['reported_cost_usd'] for mode in ['ranking','rating']) for m in stats}
    pilot_path=OUT/'pilot.jsonl'
    pilot_cost=sum(r['reported_cost_all_attempts'] for r in read_records(pilot_path)) if pilot_path.exists() else 0
    result={'models':stats,'paired_differences_non_ties':pairs,'reported_total_cost_usd':totals,'pilot_reported_cost_usd':pilot_cost,'failures':failures,'completed_logical_requests':len(raw),'valid_logical_requests':sum(r['success'] for r in raw),'bootstrap':{'unit':'subset/id','draws':10000,'seed':20261117}}
    (OUT/'metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    fields=['subset','id','mode','gpt5_success','jev_correct','gpt5_correct','jev_top1','gpt5_top1','jev_strict','gpt5_strict']
    with (OUT/'paired-items.csv').open('w') as f:
        w=csv.DictWriter(f,lineterminator='\n',fieldnames=fields);w.writeheader();w.writerows(details)
    lines=['# GPT-5 与 Jev 在 RewardBench 2 上的对照实验','',
        '这次使用完整 **GPT-5（openai/gpt-5，medium 推理）**，不是 GPT-5 mini。比较的是对已有回答的判断能力，没有重新生成候选回答。','',
        '## 1. 怎么跑的？','',
        '- 数据沿用原 Jev 实验：1,865 条问题，候选文本不变。',
        '- **直接选择**：1,763 条非 Ties 问题，每题四个候选，GPT 与 Jev 使用相同候选轮转；选中标准好回答就计对。',
        '- **打分后比较**：全部 1,865 条，每个候选使用相同五档质量标准。GPT 生成 0—4 连续分数，Jev 返回五档索引的期望分；分数生成机制不同。',
        '- 评分时所有候选共享输入，排列与此前 Jev 一致；标准好回答排在前面，模型看不到这些标签，但仍可能受到位置偏差影响。',
        '- 数据没有人工 1—5 分；比较的是分数能否把好回答排在较差回答前面。',
        '- GPT 使用本轮新请求；Jev 使用已有历史结果。因此不是同一时间或相同内部计算量的比较。','',
        f'正式评估共 **{len(raw):,}** 份，成功输出 **{sum(r["success"] for r in raw):,}** 份，终止失败 **{len(failures)}** 份。缺失输出按错计。','',
        '## 2. 直接选最好回答：谁更准？','',
        '| 类别 | 题数 | Jev | GPT-5 | GPT − Jev（百分点） |',
        '|---|---:|---:|---:|---:|']
    for ss in [*SUBSETS[:-1],'ALL']:
        a,b=stats['jev']['ranking'][ss],stats['gpt5']['ranking'][ss]
        lines.append(f'| {"全部非 Ties" if ss=="ALL" else NAMES.get(ss,ss)} | {a["samples"]} | {pct(a["accuracy"])} | {pct(b["accuracy"])} | {(b["accuracy"]-a["accuracy"])*100:+.2f} |')
    diff=pairs['ranking']['ALL_NON_TIES']['accuracy'];lo,hi=diff['paired_item_bootstrap_95ci']
    lines+=['',f'在相同 1,763 题上，GPT-5 相对 Jev 的准确率差为 **{diff["gpt5_minus_jev"]*100:+.2f} 个百分点**，配对抽样 95% 区间 **[{lo*100:+.2f}, {hi*100:+.2f}]**。区间只反映这批题的抽样波动，不包括提示设计和服务变化。','',
        '## 3. 给每份回答打分后，谁排得更好？','',
        '最高分命中：最高分里有一个好回答就算对，包括好坏回答并列最高。严格排序：所有好回答必须严格高于所有较差回答。高 top-1 但较低 strict 往往意味着打分并列，不能只看 top-1。','',
        '| 类别 | Jev 最高分命中 | GPT 最高分命中 | Jev 严格排序 | GPT 严格排序 |','|---|---:|---:|---:|---:|']
    for ss in [*SUBSETS,'ALL']:
        a,b=stats['jev']['rating'][ss],stats['gpt5']['rating'][ss]
        lines.append(f'| {"全部 1,865 题" if ss=="ALL" else NAMES.get(ss,ss)} | {pct(a["top1_accuracy"])} | {pct(b["top1_accuracy"])} | {pct(a["strict_ranking_accuracy"])} | {pct(b["strict_ranking_accuracy"])} |')
    lines+=['','Ties 的专门间隔公式另算，不是普通准确率，也不是官方排行榜成绩：']
    for m,label in [('jev','Jev'),('gpt5','GPT-5')]:
        v=stats[m]['rating']['Ties_margin_formula']['score']
        lines.append(f'- {label}：{pct(v) if v is not None else "存在缺失，不发布聚合分"}。')
    lines+=['','## 4. 费用和耗时','', '| 模型 / 方法 | 报告费用 USD | 每题耗时中位数 | 每题耗时 p95 |','|---|---:|---:|---:|']
    for mode in ['ranking','rating']:
        for m,label in [('jev','Jev'),('gpt5','GPT-5')]:
            t=stats[m][mode]['runtime'];lines.append(f'| {label} / {mode} | ${t["reported_cost_usd"]:.4f} | {t["latency_ms_p50"]/1000:.2f} 秒 | {t["latency_ms_p95"]/1000:.2f} 秒 |')
    lines+=['',f'GPT-5 正式实验合计报告费用 **${totals["gpt5"]:.4f}**，预检另计 **${pilot_cost:.4f}**。GPT 费用计入所有有费用记录的尝试；没有费用信息的失败收费未知。GPT 耗时含重试，不含线程排队。Jev 费用和耗时沿用原实验记录，不能把两者理解为硬件归一化速度。','',
        '## 5. 怎样使用这些结果？','',
        '直接选择与打分是两个任务，分别比较，不混成一个总分。特别是评分方式的并列规则会影响 top-1；应该同时看严格排序。Ties 的特殊公式也不能与普通四选一准确率混用。','',
        '这次可以比较 GPT-5 与 Jev 在相同候选和评分任务上的表现，但不应据此推断通用智能、参数效率，或直接宣称超过官方 RewardBench 2 排行榜。','',
        '[逐题结果与指标](../artifacts/rewardbench2-gpt5/README.md) · [原实验讲解](../docs/tutorial.zh-CN.md)','']
    (ROOT/'report/rewardbench2-gpt5-comparison.md').write_text('\n'.join(lines))
    print(json.dumps({'completed':len(raw),'valid':sum(r['success'] for r in raw),'cost':totals,'ranking':{m:stats[m]['ranking']['ALL'] for m in stats},'rating':{m:stats[m]['rating']['ALL'] for m in stats}},indent=2))

if __name__=='__main__':main()
