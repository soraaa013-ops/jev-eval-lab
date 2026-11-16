"""Offline paired analysis; cluster bootstrap at query level, not independent steps."""
import csv, json, sys
from collections import Counter
from pathlib import Path
import numpy as np
from run_agentprocessbench import ROOT, OUT, MODELS, rows, payload, dump, sha

def scores(cm):
    cm=np.asarray(cm,dtype=float);n=cm.sum();tp=np.diag(cm[:,:3]);gold=cm.sum(axis=1);pred=cm[:,:3].sum(axis=0)
    f1=np.divide(2*tp,gold+pred,out=np.zeros(3),where=gold+pred>0)
    return {'n_steps':int(n),'accuracy':float(tp.sum()/n) if n else 0,'macro_f1':float(f1.mean()),'f1_by_label':dict(zip(['-1','0','1'],f1.tolist())),'error_recall':float(tp[0]/gold[0]) if gold[0] else 0,'error_false_positive_rate':float(cm[1:,0].sum()/gold[1:].sum()) if gold[1:].sum() else 0,'confusion_gold_rows_pred_columns_-1_0_1_missing':cm.astype(int).tolist()}

def main():
    rr=rows();lookup={r['_id']:r for r in rr};records={};attempt_records=[]
    for line in (OUT/'results.jsonl').read_text().splitlines():
        x=json.loads(line);assert x['id'] in lookup
        assert x['request_sha256']==sha(dump(payload(lookup[x['id']],x['model']))),'Request drift'
        attempt_records.append(x)
        if (x['id'],x['model']) not in records or 'prediction'in x:records[x['id'],x['model']]=x
    assert len(records)==len(rr)*len(MODELS), 'Main run not finished; refusing to publish partial metrics'
    groups=sorted({(r['_dataset'],r['query_index']) for r in rr});gi={k:i for i,k in enumerate(groups)}
    cms={m:np.zeros((len(groups),3,4),dtype=int) for m in [*MODELS,'always_positive']};details=[];metrics={};coverage={}
    for m in cms:
        final=[];lat=[];cost=0;versions=Counter();high=[];nvalid=0;calls=0;retries=0
        for r in rr:
            x=records.get((r['_id'],m),{});p=x.get('prediction',{});g=gi[r['_dataset'],r['query_index']]
            if m=='always_positive':p={'step_labels':{i:1 for i in r['step_labels']},'final_label':1}
            if p:nvalid+=1
            for idx,y in r['step_labels'].items():
                yp=p.get('step_labels',{}).get(idx);col=yp+1 if yp in [-1,0,1] else 3;cms[m][g,y+1,col]+=1
                row={'id':r['_id'],'dataset':r['_dataset'],'query_index':r['query_index'],'sample_index':r['sample_index'],'message_index':idx,'model':m,'gold':y,'prediction':yp}
                if m in ['jev','clef'] and p:
                    probs=x['attempts'][-1]['response']['answers'][f'step_{idx}']['probabilities'];confidence=max(probs.values());row['max_probability']=confidence
                    if confidence>=.9:high.append(y==yp)
                details.append(row)
            final.append((r['final_label'],p.get('final_label')))
            if 'elapsed_ms'in x:lat.append(x['elapsed_ms']/1000)
            if p and m!='always_positive':versions[x['attempts'][-1]['response'].get('model','unknown')]+=1
        for x in attempt_records:
            if x['model']!=m:continue
            retries+=max(0,len(x['attempts'])-1)
            for a in x['attempts']:
                parts=a.get('parts') or [{'response':a.get('response',{})}]
                calls+=len(parts)
                for part in parts:cost+=part['response'].get('usage',{}).get('cost',0) or 0
        combined=scores(cms[m].sum(axis=0));combined.update({'complete_trajectories':nvalid,'requested_trajectories':len(rr),'final_accuracy_all_500_exact_match':sum(y==p for y,p in final)/len(final),'final_accuracy':sum(y==p for y,p in final if y in [-1,1])/sum(y in [-1,1] for y,p in final),'final_binary_gold_count':sum(y in [-1,1] for y,p in final),'final_neutral_gold_excluded':sum(y==0 for y,p in final),'final_failure_recall':sum(y==-1 and p==-1 for y,p in final)/sum(y==-1 for y,p in final),'cost_usd_reported':cost,'http_calls_recorded':calls,'retries':retries,'latency_seconds_p50':float(np.median(lat)) if lat else None,'latency_seconds_p95':float(np.quantile(lat,.95)) if lat else None,'model_versions':dict(versions),'probability_ge_0.9_steps':len(high),'probability_ge_0.9_error_rate':1-sum(high)/len(high) if high else None})
        combined['subsets']={ds:scores(cms[m][[i for i,g in enumerate(groups) if g[0]==ds]].sum(axis=0)) for ds in ['bfcl','tau2']}
        metrics[m]=combined
    rng=np.random.default_rng(20261116);draws=rng.integers(0,len(groups),(2000,len(groups)));boots={}
    for m,cm in cms.items():
        boots[m]={k:[] for k in ['accuracy','macro_f1']}
        for draw in draws:
            s=scores(cm[draw].sum(axis=0))
            for k in boots[m]:boots[m][k].append(s[k])
        for k,b in boots[m].items():metrics[m][k+'_95ci']=np.quantile(b,[.025,.975]).tolist()
    diffs={}
    for a,b in [('jev','gpt5mini'),('clef','gpt5mini'),('jev','clef')]:
        diffs[a+' minus '+b]={k:{'difference':metrics[a][k]-metrics[b][k],'paired_query_bootstrap_95ci':np.quantile(np.array(boots[a][k])-np.array(boots[b][k]),[.025,.975]).tolist()} for k in ['accuracy','macro_f1']}
    common_ids={r['_id'] for r in rr if all('prediction' in records.get((r['_id'],m),{}) for m in MODELS)}
    common={}
    for m in MODELS:
        cm=np.zeros((3,4),dtype=int)
        for r in rr:
            if r['_id'] not in common_ids:continue
            pred=records[r['_id'],m]['prediction']['step_labels']
            for idx,y in r['step_labels'].items():cm[y+1,pred[idx]+1]+=1
        common[m]=scores(cm)
    result={'dataset_revision':'cd81f326aece8b0a3f6359e20df370690d3a98bf','n_trajectories':len(rr),'n_queries':len(groups),'n_steps':sum(len(r['step_labels']) for r in rr),'gold_step_counts':dict(Counter(str(y) for r in rr for y in r['step_labels'].values())),'gold_final_counts':dict(Counter(str(r['final_label']) for r in rr)),'models':metrics,'common_complete_trajectories':len(common_ids),'common_complete_metrics':common,'paired_differences':diffs,'bootstrap':{'unit':'dataset/query_index (five trajectories per query)','seed':20261116,'draws':2000},'main_run_errors':[{'id':x['id'],'model':x['model'],'errors':[a.get('error') for a in x['attempts'] if a.get('error')]} for x in attempt_records if any('error'in a for a in x['attempts'])]}
    (OUT/'metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    with (OUT/'per-step.csv').open('w') as f:
        writer=csv.DictWriter(f,lineterminator='\n',fieldnames=['id','dataset','query_index','sample_index','message_index','model','gold','prediction','max_probability']);writer.writeheader();writer.writerows(details)
    for m,s in metrics.items():print(m,'complete',s['complete_trajectories'],'accuracy',round(s['accuracy'],4),'macroF1',round(s['macro_f1'],4),'error_recall',round(s['error_recall'],4),'final_acc',round(s['final_accuracy'],4),'cost',round(s['cost_usd_reported'],4))
    print('Paired differences',json.dumps(diffs))
if __name__=='__main__':main()
