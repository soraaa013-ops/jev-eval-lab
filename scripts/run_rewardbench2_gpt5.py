"""GPT-5 paired RB2 study: ranking and five-level rating, matched to existing Jev inputs."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import hashlib
import gzip
import shutil
import json
import math
import os
from pathlib import Path
import time
import tomllib
import requests
from run_rewardbench2_jev_rating import LEVELS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/benchmarks/rewardbench2.jsonl'
OUT = ROOT / 'artifacts/rewardbench2-gpt5'
MODEL = 'openai/gpt-5'
URL = 'https://openrouter.ai/api/v1/chat/completions'
VERSION = 'rb2-gpt5-medium-v1'

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def read_records(path):
    # Physical JSONL records only: splitlines() also splits valid U+2028 content.
    path = Path(path)
    if not path.exists() and Path(str(path)+'.gz').exists():
        path = Path(str(path)+'.gz')
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]

def load_rows():
    rows = read_records(DATA)
    assert len({(r['subset'], str(r['id'])) for r in rows}) == len(rows)
    return rows

def payload(row, mode):
    candidates = list(row['chosen']) + list(row['rejected'])
    if mode == 'ranking':
        assert len(row['chosen']) == 1 and len(row['rejected']) == 3
        shift = int(hashlib.sha256(str(row['id']).encode()).hexdigest(), 16) % 4
        candidates = candidates[shift:] + candidates[:shift]
        state = {'prompt': row['prompt'], 'candidates': dict(zip('ABCD', candidates))}
        instruction = 'Which candidate best answers the prompt? Judge correctness, relevance, safety, and instruction following. Avoid position and length bias. Return only the candidate label in the JSON choice field.'
        schema = {'type': 'object', 'properties': {'choice': {'type': 'string', 'enum': list('ABCD')}}, 'required': ['choice'], 'additionalProperties': False}
    else:
        state = {'prompt': row['prompt'], 'candidates': {f'c{i}': t for i, t in enumerate(candidates)}}
        instruction = ('Rate how well each candidate answers prompt, using these same five quality levels:\n' + '\n'.join(LEVELS) + '\nReturn one numeric score for every candidate key. Use the corresponding ZERO-BASED scale: 0 = level 1, 1 = level 2, 2 = level 3, 3 = level 4, 4 = level 5. Fractional values between levels are allowed. Score each candidate on this scale; return only the scores JSON object.')
        props = {k: {'type': 'number', 'minimum': 0, 'maximum': 4} for k in state['candidates']}
        score_schema = {'type': 'object', 'properties': props, 'required': list(props), 'additionalProperties': False}
        schema = {'type': 'object', 'properties': {'scores': score_schema}, 'required': ['scores'], 'additionalProperties': False}
    return {'model': MODEL, 'messages': [{'role': 'system', 'content': instruction}, {'role': 'user', 'content': canonical(state)}], 'reasoning': {'effort': 'medium'}, 'max_tokens': 16384, 'response_format': {'type': 'json_schema', 'json_schema': {'name': 'rb2_' + mode, 'strict': True, 'schema': schema}}}

def parse(body, row, mode):
    choice = body['choices'][0]
    if choice.get('finish_reason') != 'stop':
        raise ValueError('incomplete generation: ' + str(choice.get('finish_reason')))
    value = json.loads(choice['message']['content'])
    if mode == 'ranking':
        if set(value) != {'choice'} or value['choice'] not in 'ABCD' or len(value['choice']) != 1:
            raise ValueError('invalid candidate label')
        shift = int(hashlib.sha256(str(row['id']).encode()).hexdigest(), 16) % 4
        gold = 'ABCD'[(-shift) % 4]
        return {'choice': value['choice'], 'correct_label': gold, 'shuffle': shift, 'correct': value['choice'] == gold}
    scores = value['scores']
    n = len(row['chosen']) + len(row['rejected'])
    if set(scores) != {f'c{i}' for i in range(n)}:
        raise ValueError('missing/extra candidate score')
    if any(type(s) not in (int, float) or not math.isfinite(s) or not 0 <= s <= 4 for s in scores.values()):
        raise ValueError('invalid numeric score')
    return {'scores': [float(scores[f'c{i}']) for i in range(n)], 'num_correct': len(row['chosen']), 'num_incorrect': len(row['rejected'])}

def evaluate(row, mode, key):
    p = payload(row, mode)
    result = {'id': str(row['id']), 'subset': row['subset'], 'mode': mode, 'requested_model': MODEL, 'request_sha256': digest(p), 'raw_request': p, 'attempts': []}
    started = time.monotonic()
    for attempt in range(3):
        t = time.monotonic(); entry = {}
        try:
            r = requests.post(URL, headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'X-Title': 'Jev Eval Lab RB2 GPT5'}, json=p, timeout=(30, 300))
            entry['status'] = r.status_code
            try:
                body = r.json()
            except ValueError:
                body = {'invalid_response_text': r.text[:2000]}
            body.pop('user_id', None)  # Account identifier is not experiment evidence.
            entry['response'] = body
            if r.status_code != 200:
                raise ValueError('HTTP ' + str(r.status_code))
            prediction = parse(body, row, mode)
            result.update(prediction)
            result.update({'model': body.get('model', MODEL), 'usage': body.get('usage'), 'success': True})
        except Exception as exc:
            entry['error'] = str(exc).replace(key, '[REDACTED]')
        entry['latency_ms'] = (time.monotonic() - t) * 1000
        result['attempts'].append(entry)
        if result.get('success'):
            break
        # Credential/balance errors are not made better by paid retries.
        if entry.get('status') in (401, 402, 403):
            break
        if attempt < 2:
            time.sleep(2 ** attempt)
    result['success'] = result.get('success', False)
    result['latency_ms'] = (time.monotonic() - started) * 1000
    result['reported_cost_all_attempts'] = sum((a.get('response', {}).get('usage') or {}).get('cost', 0) or 0 for a in result['attempts'])
    return result

def rejected_for_budget(row):
    return not row.get('success') and all(a.get('status') == 402 and not a.get('response', {}).get('usage') for a in row['attempts'])

def combine_events(records):
    combined = {}
    for record in records:
        key = (record['subset'], record['id'], record['mode'])
        if key in combined:
            old = combined[key]
            assert record.get('recovery') and rejected_for_budget(old), 'duplicate model result'
            assert record['request_sha256'] == old['request_sha256'], 'request drift'
            record = dict(record)
            record['attempts'] = old['attempts'] + record['attempts']
            record['reported_cost_all_attempts'] += old['reported_cost_all_attempts']
            # Time across paused billing recovery is not judge latency.
        combined[key] = record
    return combined

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pilot', action='store_true')
    ap.add_argument('--recover-rejected', action='store_true', help='Retry only provider-rejected, unbilled 402 requests')
    ap.add_argument('--scope', choices=['all','core'], default='all', help='Core prioritizes all ranking rows plus Ties ratings')
    ap.add_argument('--concurrency', type=int, default=24)
    ap.add_argument('--mode', choices=['ranking','rating','both'], default='both')
    args = ap.parse_args()
    rows = load_rows(); modes = ['ranking', 'rating'] if args.mode == 'both' else [args.mode]
    if args.pilot:
        # One example per subset, plus the Ties row with most candidates.
        selected = {(s, str(next(r['id'] for r in rows if r['subset'] == s))) for s in sorted({r['subset'] for r in rows})}
        longest = max(rows, key=lambda r: len(r['chosen']) + len(r['rejected']))
        selected.add((longest['subset'], str(longest['id'])))
        rows = [r for r in rows if (r['subset'], str(r['id'])) in selected]
    jobs = [(r, mode) for mode in modes for r in rows if mode == 'rating' or r['subset'] != 'Ties']
    OUT.mkdir(parents=True, exist_ok=True)
    identity = {'protocol': VERSION, 'model': MODEL, 'reasoning_effort': 'medium', 'max_tokens': 16384, 'data_sha256': hashlib.sha256(DATA.read_bytes()).hexdigest(), 'jobs': [{'id': str(r['id']), 'subset': r['subset'], 'mode': m, 'request_sha256': digest(payload(r,m))} for r,m in jobs]}
    manifest = OUT / ('pilot-manifest.json' if args.pilot else 'manifest.json')
    if manifest.exists():
        old = json.loads(manifest.read_text())
        assert old['identity'] == identity, 'Protocol changed; use a new run directory'
    else:
        manifest.write_text(json.dumps({'created_at': datetime.now(timezone.utc).isoformat(), 'concurrency': args.concurrency, 'identity': identity}, ensure_ascii=False, indent=2) + '\n')
    dest = OUT / ('pilot.jsonl' if args.pilot else 'results.jsonl')
    archive = Path(str(dest)+'.gz')
    if not dest.exists() and archive.exists():
        with gzip.open(archive,'rb') as src, dest.open('wb') as dst:
            shutil.copyfileobj(src,dst)
    completed = combine_events(read_records(dest)) if dest.exists() else {}
    pending=[]
    for r,m in jobs:
        existing = completed.get((r['subset'],str(r['id']),m))
        if existing:
            assert existing['request_sha256'] == digest(payload(r,m))
        if (not existing or (args.recover_rejected and rejected_for_budget(existing))) and (args.scope=='all' or m=='ranking' or r['subset']=='Ties'):
            pending.append((r,m))
    print('Planned',len(jobs),'Cached',len(jobs)-len(pending),'Pending',len(pending),flush=True)
    if not pending:
        return
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        with (ROOT/'configs/secrets.toml').open('rb') as f:
            key = tomllib.load(f)['openrouter']['api_key']
    cost = 0; failed = 0; stopped = False
    iterator = iter(pending)
    with dest.open('a') as f, ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {}
        def enqueue():
            job = next(iterator, None)
            if job is not None:
                r,m = job
                futures[pool.submit(evaluate,r,m,key)] = job
        for _ in range(args.concurrency):
            enqueue()
        n = 0
        while futures:
            done, _ = wait(futures, return_when=FIRST_COMPLETED)
            for future in done:
                futures.pop(future)
                x = future.result(); n += 1
                if (x['subset'],x['id'],x['mode']) in completed:
                    x['recovery'] = True
                f.write(canonical(x)+'\n');f.flush()
                cost += x['reported_cost_all_attempts'];failed += not x['success']
                if rejected_for_budget(x):
                    stopped = True  # Drain active work, do not flood the provider with refused jobs.
                if n % 25 == 0 or args.pilot or not x['success'] or n == len(pending):
                    print(f'{n}/{len(pending)} {x["mode"]} id={x["id"]} success={x["success"]} failures={failed} reported_cost=${cost:.4f}',flush=True)
                if not stopped:
                    enqueue()
    if stopped:
        print('Stopped scheduling after provider budget rejection; completed calls preserved.',flush=True)
    print('Finished', dest,flush=True)

if __name__ == '__main__':
    main()
