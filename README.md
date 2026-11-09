# Jev Eval Lab

Jev Eval Lab is a provider-neutral, reproducible testbed for studying typed
decision models—especially Jev—in model-evaluation settings. It compares typed
judges, generative LLM judges, and deterministic baselines on the same pairwise
tasks while preserving raw responses, resolved configuration, request hashes,
latency, probabilities, and model versions.

The research focus is evaluation, not a claim that Jev should replace an LLM.
The report separately surveys existing Jev applications so that benchmark
results can be interpreted in the wider decision-model landscape.

## Results

Choose the [research report](report/report.md) for a concise research account or the
[detailed experiment report](report/experiment-report.md) for a complete explanation of how every experiment was run.
The [experiment-results index](artifacts/README.md) links every detail. The repository commits every
per-judgment result, not just aggregate scores. Current experiments contain
5,728 real API judgments across JudgeBench and RewardBench 2.

## What works now

- OpenRouter Decisions API adapter for Jev and compatible decision models
- OpenRouter chat-completions adapter for generative judges
- deterministic mock judge for offline end-to-end verification
- pairwise evaluation with automatic A/B order reversal
- resumable JSONL result logs keyed by canonical request hashes
- accuracy, strict swapped-order accuracy, consistency, Brier score, ECE,
  latency, token use, and reported cost
- generated Markdown result report
- configuration-only model replacement using TOML

## Quick start (no API key)

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .

jev-eval validate --config configs/experiments/smoke.toml
jev-eval run --config configs/experiments/smoke.toml
jev-eval analyze --run-dir artifacts/runs/smoke
jev-eval report --run-dir artifacts/runs/smoke
```

Or, without installation:

```bash
PYTHONPATH=src python -m jev_eval.cli run --config configs/experiments/smoke.toml
```

The whole offline verification can also be run with `make smoke` or
`scripts/run_smoke.sh`.

## Run Jev through OpenRouter

Set `OPENROUTER_API_KEY` in the environment; do not place it in TOML or commit
it. Then run:

```bash
jev-eval validate --config configs/experiments/jev_sample.toml
jev-eval run --config configs/experiments/jev_sample.toml
jev-eval analyze --run-dir artifacts/runs/jev-sample
jev-eval report --run-dir artifacts/runs/jev-sample
```

Change only `model.id` to pin another decision-model release. The Decisions API
and chat-completions API use different adapters intentionally.

For JudgeBench, prepare the pinned official data and run the full 350-pair,
double-order protocol:

```bash
python scripts/prepare_judgebench.py --split gpt --output data/benchmarks/judgebench-gpt.jsonl
jev-eval run --config configs/experiments/judgebench_jev.toml
```

RewardBench 2 has separate reproducible scripts because its native structure is
multi-candidate and its Ties subset has a special metric. The repository includes
full Jev rating and task-compatible winner-selection results under
`artifacts/runs/rewardbench2-*`. They use the official dataset but a custom Jev
adapter, so they are not official leaderboard reproductions; see the main report
for protocol definitions.

## Dataset contract

Each JSONL row contains an ID, context, two candidate responses, and the gold
winner (`"A"` or `"B"`). Optional `category`, `source`, and `metadata` fields are
preserved.

```json
{"id":"example-1","context":"Question or rubric","response_a":"...","response_b":"...","label":"A","category":"reasoning"}
```

Benchmark downloaders will be added only after dataset licenses and canonical
revisions are pinned. The committed sample is synthetic and is not a scientific
benchmark.

## Reproducibility model

Two levels are distinguished:

1. **Analysis reproducibility:** committed raw results can be re-analysed without
   another paid request.
2. **API rerun reproducibility:** a pinned request can be sent again, but hosted
   model weights and provider infrastructure may change.

Every run stores the resolved configuration and run manifest. Raw provider
responses remain in `results.jsonl`; review them before publishing because a
benchmark row may contain sensitive text.

See [the research report](report/report.md), [experiment protocol](docs/protocol.md),
and [adding a model](docs/adding-models.md).

