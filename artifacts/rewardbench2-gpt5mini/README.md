# GPT-5 mini: RewardBench 2 winner selection

Model: `openai/gpt-5-mini`, medium reasoning. Scope: exactly 1,763 non-Ties
winner-selection questions; no candidate-rating or Ties run.

**Completed:** 1,763/1,763 valid predictions, 1,438 correct (81.57%), zero terminal failures. Main reported cost: $2.7800; pilot: $0.0109. No requests remain running.

Read
[the Chinese results report](../../report/rewardbench2-gpt5mini-comparison.md).

- `PROTOCOL.md`: task, input, scoring and comparison design.
- `manifest.json`: every planned request and frozen configuration.
- `results.jsonl.gz`: complete request/response event log, compressed for Git.
- `metrics.json`: Jev / GPT-5 / GPT-5 mini category metrics and paired intervals.
- `paired-items.csv`: all 1,763 choices and correctness comparisons.
- `pilot.jsonl`, `pilot-manifest.json`: five format checks, separate from main results/cost.
- `completion.json`: final coverage and archive checksum.

```bash
python scripts/run_rewardbench2_gpt5mini.py --pilot --concurrency 5
python scripts/run_rewardbench2_gpt5mini.py --concurrency 32
python scripts/analyze_rewardbench2_gpt5mini.py
```

Use the existing `.[agent-eval]` dependencies. Exact prompts, candidate ordering,
JSON schema, medium effort and token limit match the GPT-5 run; the model field
is the only request change. Results are paired by `(subset,id)`, not raw ID.
Jev uses the historical typed-Choice results on those same candidate orders.

Analysis accepts compressed archives and refuses incomplete coverage. The
runner restores a local JSONL from its archive on resume. Valid predictions
are cached; provider-rejected unbilled 402 requests can be resumed unchanged
with `--recover-rejected` after outstanding requests settle or credit is added.
No partial-data accuracy is presented as a complete benchmark score.
