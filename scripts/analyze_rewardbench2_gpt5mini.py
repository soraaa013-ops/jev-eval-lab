"""Compare all 1,763 RB2 winner selections: Jev, GPT-5, and GPT-5 mini."""
import csv
import json
from run_rewardbench2_gpt5 import ROOT, load_rows, read_records, combine_events, payload, digest, rejected_for_budget
from analyze_rewardbench2_gpt5 import identity, summarize, paired_difference, pct, SUBSETS, NAMES

OUT = ROOT / 'artifacts/rewardbench2-gpt5mini'

def main():
    source=[r for r in load_rows() if r['subset']!='Ties']
    expected={identity(r):r for r in source}
    records={}
    records['jev']={identity(r):r for r in read_records(ROOT/'artifacts/runs/rewardbench2-jev-ranking/results.jsonl')}
    for model,folder in [('gpt5','rewardbench2-gpt5'),('gpt5mini','rewardbench2-gpt5mini')]:
        combined=combine_events(read_records(ROOT/f'artifacts/{folder}/results.jsonl'))
        records[model]={identity(r):r for r in combined.values() if r['mode']=='ranking'}
        for key,r in records[model].items():
            p=payload(expected[key],'ranking')
            p['model']='openai/gpt-5-mini' if model=='gpt5mini' else 'openai/gpt-5'
            assert r['request_sha256']==digest(p), 'Request drift'
            assert not rejected_for_budget(r), 'Unadmitted requests remain'
    for m,r in records.items():
        assert set(r)==set(expected), f'{m}: incomplete winner-selection coverage'
    metrics={m:summarize(source,'ranking',r) for m,r in records.items()}
    paired={}
    for other in ['jev','gpt5']:
        paired['gpt5mini_minus_'+other]={}
        for ss in ['ALL',*SUBSETS[:-1]]:
            rr=[r for r in source if ss=='ALL' or r['subset']==ss]
            a=[bool(records[other][identity(r)].get('correct',False)) for r in rr]
            b=[bool(records['gpt5mini'][identity(r)].get('correct',False)) for r in rr]
            d=paired_difference(a,b)
            d['difference']=d.pop('gpt5_minus_jev')
            paired['gpt5mini_minus_'+other][ss]=d
    pilot_cost=sum(r['reported_cost_all_attempts'] for r in read_records(OUT/'pilot.jsonl'))
    result={'scope':'Complete 1763-row non-Ties winner selection; no rating or Ties mini run',
            'models':metrics,'paired_differences':paired,'pilot_reported_cost_usd':pilot_cost,
            'bootstrap':{'unit':'subset/id','draws':10000,'seed':20261117},
            'failures':[{'subset':r['subset'],'id':r['id'],'attempt_errors':[a.get('error') for a in r['attempts']]} for r in records['gpt5mini'].values() if not r['success']]}
    (OUT/'metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    fields=['subset','id','gold','jev_choice','gpt5_choice','gpt5mini_choice','jev_correct','gpt5_correct','gpt5mini_correct']
    with (OUT/'paired-items.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
        for r in source:
            key=identity(r);row={'subset':r['subset'],'id':r['id'],'gold':records['jev'][key]['correct_label']}
            for m in records:
                row[m+'_choice']=records[m][key].get('choice')
                row[m+'_correct']=records[m][key].get('correct',False)
            writer.writerow(row)
    names={'jev':'Jev 1.14','gpt5':'GPT-5','gpt5mini':'GPT-5 mini'}
    a=metrics['gpt5mini']['ALL'];n=a['samples'];correct=round(a['accuracy']*n)
    lines=['# RewardBench 2 四选一：GPT-5 mini、GPT-5 与 Jev','',
        f'**GPT-5 mini 已完成全部 {n:,} 题，答对 {correct:,} 题，准确率 {pct(a["accuracy"])}。** 同一批题上，GPT-5 为 {pct(metrics["gpt5"]["ALL"]["accuracy"])}，Jev 为 {pct(metrics["jev"]["ALL"]["accuracy"])}。','',
        '## 1. 实验怎么跑？','',
        '- 使用 RewardBench 2 全部 1,763 条非 Ties 问题；每题一个标准好回答、三个较差回答。',
        '- 给模型看原问题与四个候选，让它直接选 A/B/C/D；选中标准好回答就计对。标准标签不输入模型。',
        '- GPT-5 mini 与此前 GPT-5 的候选内容、位置、提示和 JSON 输出要求完全相同，只换模型。两者均用 medium 推理，最多 16,384 个生成 token；相同 effort 名称不代表内部计算量相同。',
        '- Jev 使用已有实验结果，候选内容和轮转顺序相同；它通过类型化 Choice 选择赢家。',
        '- 按用户要求只做四选一：本轮 mini 不运行逐候选评分，也不运行 Ties。不同模型调用并非同时进行。','',
        '## 2. 各类别结果','',
        '| 类别 | 题数 | Jev | GPT-5 | GPT-5 mini |','|---|---:|---:|---:|---:|']
    for ss in [*SUBSETS[:-1],'ALL']:
        vals=[pct(metrics[m][ss]['accuracy']) for m in names]
        lines.append(f'| {"全部非 Ties" if ss=="ALL" else NAMES[ss]} | {metrics["jev"][ss]["samples"]} | '+ ' | '.join(vals)+' |')
    lines+=['','## 3. 差距有多大？','',
        '按同一题配对比较，再对题目进行 10,000 次重采样，得到准确率差值的 95% 区间。区间反映本批题的抽样波动，不涵盖提示选择、训练污染或服务变化。','',
        '| 比较 | mini 准确率差（百分点） | 95% 区间（百分点） |','|---|---:|---:|']
    for other in ['jev','gpt5']:
        d=paired['gpt5mini_minus_'+other]['ALL'];lo,hi=d['paired_item_bootstrap_95ci']
        lines.append(f'| mini − {names[other]} | {d["difference"]*100:+.2f} | [{lo*100:+.2f}, {hi*100:+.2f}] |')
    lines+=['']
    for other in ['jev','gpt5']:
        d=paired['gpt5mini_minus_'+other]['ALL'];lo,hi=d['paired_item_bootstrap_95ci']
        conclusion='区间包含零，本次不能据此认定总体有明确差异。' if lo<=0<=hi else ('区间完全高于零，mini 在本批题上更准。' if lo>0 else '区间完全低于零，mini 在本批题上较低。')
        lines.append(f'mini 对比 {names[other]}：{conclusion}')
    changes=sorted([(metrics['gpt5mini'][ss]['accuracy']-metrics['jev'][ss]['accuracy'],ss) for ss in SUBSETS[:-1]])
    lines+=['', '相对 Jev 的类别差距：'+'；'.join(f'{NAMES[ss]} {delta*100:+.2f} 个百分点' for delta,ss in changes)+'。']
    lines+=['','## 4. 费用和耗时','',
        '| 评委 | 全部 1,763 题报告费用 | 每题耗时中位数 | 每题耗时 p95 |','|---|---:|---:|---:|']
    for m,name in names.items():
        t=metrics[m]['runtime'];lines.append(f'| {name} | ${t["reported_cost_usd"]:.4f} | {t["latency_ms_p50"]/1000:.2f} 秒 | {t["latency_ms_p95"]/1000:.2f} 秒 |')
    lines+=['',f'mini 的 5 题预检费用另计 ${pilot_cost:.4f}，不混入正式成绩。费用来自服务返回记录，包含有费用记录的尝试；耗时包含请求内重试，不包括排队或暂停后的额度恢复等待，不是相同硬件下的纯推理速度。','',
        '## 5. 怎样理解结果？','',
        '这里比较的是“在四个已有回答里选最好”，不是回答生成能力，也不是 agent 过程判断。模型之间的总体差距需要结合类别结果看，不能从一个总分推出所有能力的高低。','',
        '本实验只包含非 Ties 的四选一，不把该准确率当作官方六类别宏平均排行榜分数。','',
        f'完成情况：mini 有效输出 {a["valid"]}/{n}；终止模型失败 {a["missing"]} 条，若有则按错计。没有后台任务继续运行。','',
        '[逐题结果与指标](../artifacts/rewardbench2-gpt5mini/README.md) · [此前 GPT-5 实验](rewardbench2-gpt5-comparison.md)','']
    (ROOT/'report/rewardbench2-gpt5mini-comparison.md').write_text('\n'.join(lines))
    print(json.dumps({'scores':{m:metrics[m]['ALL'] for m in names},'costs':{m:metrics[m]['runtime']['reported_cost_usd'] for m in names},'paired':{k:v['ALL'] for k,v in paired.items()}},indent=2))

if __name__=='__main__':main()
