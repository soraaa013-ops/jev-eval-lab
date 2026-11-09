# Experiment results index

This directory contains the committed, per-judgment results. None of the numbers
below are reconstructed from screenshots: every aggregate can be recomputed from
the JSONL files linked here.

## Experiment ledger

| Experiment | Dataset units | API judgments | Model | Complete details | Aggregate metrics |
|---|---:|---:|---|---|---|
| JudgeBench pairwise | 350 pairs | 700 | Jev 1.14 | [`results.jsonl`](runs/judgebench-jev-1.14/results.jsonl) | [`metrics.json`](runs/judgebench-jev-1.14/metrics.json) |
| JudgeBench pairwise | 350 pairs | 700 | GPT-5 mini | [`results.jsonl`](runs/judgebench-gpt-5-mini/results.jsonl) | [`metrics.json`](runs/judgebench-gpt-5-mini/metrics.json) |
| JudgeBench pairwise | 350 pairs | 700 | Qwen3-30B-A3B | [`results.jsonl`](runs/judgebench-qwen3-30b-a3b-v2/results.jsonl) | [`metrics.json`](runs/judgebench-qwen3-30b-a3b-v2/metrics.json) |
| JudgeBench pairwise, 256-token local baseline | 350 pairs | 700 derived orientations | Skywork Reward V2 Qwen3 0.6B | [`results.jsonl`](runs/judgebench-skywork-rm-0.6b-256/results.jsonl) | [`metrics.json`](runs/judgebench-skywork-rm-0.6b-256/metrics.json) |
| RewardBench 2 rating | 1,865 prompts | 1,865 | Jev 1.14 | [`results.jsonl`](runs/rewardbench2-jev-rating/results.jsonl) | [`metrics.json`](runs/rewardbench2-jev-rating/metrics.json) |
| RewardBench 2 winner selection | 1,763 non-Ties prompts | 1,763 | Jev 1.14 | [`results.jsonl`](runs/rewardbench2-jev-ranking/results.jsonl) | [`metrics.json`](runs/rewardbench2-jev-ranking/metrics.json) |

The cross-model JudgeBench table is
[`comparisons/judgebench.csv`](comparisons/judgebench.csv). It has one row for
each item/orientation and columns for every model's choice, probability,
correctness, latency, and cost.

Statistical and qualitative outputs are committed under [`analysis/`](analysis/):
10,000-sample clustered bootstrap intervals, paired model differences, raw
reliability and risk–coverage points, both SVG diagrams, and the high-confidence
error audit.

## How to read a JudgeBench result row

Each JSON object records:

- `item_id`, `source`, and `category`: identity and provenance;
- `orientation`: `original` or `swapped`;
- `label` and `choice`: expected and predicted candidate label;
- `probability_a`, `probability_b`: judge-reported distribution;
- `model`: actual model version returned by the provider;
- `latency_ms`, `usage`, and `cost`: request-level engineering measurements;
- `raw.request` and `raw.response`: full auditable API exchange.

For a pair to count as correct under `strict_swap_accuracy`, both orientations
must be correct and the semantic winner must remain the same after swapping.

## How to read a RewardBench 2 rating row

`scores` lists candidates in the same order as the dataset: all `chosen`
candidates first, then all `rejected` candidates. `num_correct` identifies the
boundary. `answers` contains Jev's complete probability distribution over the
five rubric levels for every candidate.

## How to read a RewardBench 2 ranking row

`shuffle` records the deterministic rotation applied to prevent the correct
answer from always occupying the first position. `correct_label`, `choice`, and
`probabilities` preserve the expected winner, selected winner, and full
four-choice distribution.

## Important scope note

JudgeBench compares four models. RewardBench 2 currently evaluates Jev only;
it compares protocols, not models. These two kinds of result must not be merged
into a single leaderboard.

