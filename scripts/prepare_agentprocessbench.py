"""Fetch the two selected APB subsets at a frozen revision (dataset card: MIT)."""
from pathlib import Path
import hashlib, json, urllib.request
ROOT=Path(__file__).resolve().parents[1]
REV='cd81f326aece8b0a3f6359e20df370690d3a98bf'
EXPECTED={'bfcl':'6aee0b71eff7feb872c6b54d962f8831b56f7bebf770cba9cb657f219afb6fe5','tau2':'6f22818ff88822512767fe735f56e7b78bed4b9aaf26959144feb92f127e1e95'}
def main():
    dest=ROOT/'data/agentprocessbench';dest.mkdir(parents=True,exist_ok=True)
    sources=[]
    for subset in ['bfcl','tau2']:
        url=f'https://huggingface.co/datasets/LulaCola/AgentProcessBench/resolve/{REV}/{subset}/test.jsonl'
        path=dest/f'{subset}.jsonl'
        if not path.exists():
            with urllib.request.urlopen(url,timeout=120) as r:path.write_bytes(r.read())
        raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED[subset], 'Source checksum mismatch'
        sources.append({'subset':subset,'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'trajectories':len(raw.splitlines())})
    (dest/'sources.json').write_text(json.dumps({'revision':REV,'dataset_card_license':'mit','sources':sources},indent=2)+'\n')
    print(json.dumps(sources,indent=2))
if __name__=='__main__':main()
