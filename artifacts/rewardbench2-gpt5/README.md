# GPT-5 on RewardBench 2

This experiment adds full GPT-5 (`openai/gpt-5`, medium reasoning) to the
existing Jev comparison. It is not GPT-5 mini and is not an official leaderboard submission.

**Status:** all 1,763 ranking rows and all 102 Ties rows completed. The user requested winner selection only; full rating (288/1,865 valid) is not being continued. No requests remain running.

Read the [Chinese experiment results](../../report/rewardbench2-gpt5-comparison.md)
for data, methods, scores, and interpretation.

- `PROTOCOL.md`: data, prompts, scoring, failure policy and comparison limits.
- `manifest.json`: all 3,628 planned logical requests (1,763 ranking + 1,865 rating).
- `results.jsonl.gz`: each main-run prediction, exact request, all attempts and available usage.
- `core-metrics.json`: completed ranking/Ties scores and paired ranking intervals.
- `completion.json`: completed scope, remaining rating count and archive checksum.
- `metrics.json`: generated only after full rating completes.
- `paired-ranking.csv`: completed winner-selection comparisons.
- `paired-items.csv`: generated after both full protocols complete.
- `pilot.jsonl` / `pilot-manifest.json`: 12 format-pilot requests, separate from main costs and scores.

Both models see the same candidate content and order for each mode. Rating
uses the same five-level rubric, but Jev returns a distribution-derived score
and GPT generates a scalar on the corresponding 0–4 scale. Rating candidates
are ordered chosen first, following the original Jev study; gold field names
are hidden, but this does not rule out order bias.

Raw IDs are not unique across subsets. Use `(subset,id)` when matching
predictions. Ties has its own margin metric and is not a winner-selection task.
The main classification denominators retain failed requests as incorrect.

The runner requires the existing `.[agent-eval]` dependencies (`requests` and
`numpy` for the analyzer). Credentials come from the environment or ignored
local configuration; neither is copied into artifacts. Main results cache
terminal failures as well as successes, preventing unbounded retries.

```bash
python scripts/run_rewardbench2_gpt5.py --pilot --concurrency 8
python scripts/run_rewardbench2_gpt5.py --concurrency 48
python scripts/analyze_rewardbench2_gpt5.py
```

Raw main results are compressed for Git; readers accept the compressed archive and the runner restores a local JSONL file on resume.

Analysis is offline and refuses an incomplete set of logical requests. A
terminal failure is a completed request but not a valid prediction. Cost
counts all usage-bearing attempts once; unavailable charges remain unknown.

The requested winner-selection scope is complete. Its analysis command (including
the already-completed Ties supplement) is:

```bash
python scripts/analyze_rewardbench2_gpt5.py --core-only
```

`core-metrics.json` and `paired-ranking.csv` describe that completed scope.
No all-candidate rating total is claimed until every rating request has been
admitted. Only if a future full-rating run is requested, sufficient credit is available,
and the protocol is retained, resume unbilled admission rejections with
`--recover-rejected --concurrency 8`.
The event journal preserves original refusals and subsequent recovery.
