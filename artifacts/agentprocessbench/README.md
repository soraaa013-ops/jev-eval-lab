# AgentProcessBench: real agent-trajectory judges

Read the [Chinese explanation and results](../../report/agent-judge-benchmark.md).

This run judges the complete **BFCL and tau2** subsets: 500 existing trajectories,
6,147 human-labeled steps, 100 underlying queries. Models: Jev 1.14, Clef-flash,
GPT-5 mini. The agents themselves were not rerun. This is a subset study, not the
full APB leaderboard, and not an online intervention experiment.

- [PROTOCOL.md](PROTOCOL.md): selection, blind evidence, shared rubric, metrics, statistical unit, limitations; locked before the main run.
- [manifest.json](manifest.json): pinned source revision, source file hashes, all evidence / logical request hashes.
- [results.jsonl](results.jsonl): every main-run result, raw responses, attempts, model versions, usage/cost, latency; `parts` contains individual HTTP requests' hashes / question keys / responses. The outer response combines decision batches when needed.
- [completion.json](completion.json): final counts, code/data/result hashes and verification checks.
- [cases.json](cases.json): traceable post-hoc directory-location example.
- [metrics.json](metrics.json): coverage, primary metrics, per-subset confusion matrices, cost/latency, paired query-bootstrap intervals.
- [per-step.csv](per-step.csv): every gold/prediction pair, plus the always-positive baseline. Gold is joined **after** inference.
- [smoke.jsonl](smoke.jsonl): format pilot, separate from main scoring. Initially Clef rejected 96 questions (HTTP 422, max 64). The successful replacement uses batches and retains full evidence. The failed pilot and successful rerun are both kept. The longest Jev pilot used one batch, whereas main decision-model calls cap batches at 64.
- [Source data and provenance](../../data/agentprocessbench/).

Request bodies can be reconstructed exactly using `payload(row, model)` in
`run_agentprocessbench.py`. For decision requests with >64 questions, retain the
same state and slice questions in insertion order into batches of at most 64;
compare each part's SHA-256. Gold fields are never serialized into requests.

Run offline:

```bash
pip install -e '.[agent-eval]'
python scripts/analyze_agentprocessbench.py
```

Main output and pilot costs are kept separate. The completed main run has 1,497
valid trajectory outputs and three terminal Clef token-limit failures; primary
metrics retain their 264 missing step predictions as wrong. The auxiliary final
binary metric uses 480 non-neutral gold outcomes; see the protocol addendum.
Failed terminal main records are cached, so resume does not exceed the attempt limit. Do not sum the combined outer
response usage and the per-part usage together: those duplicate the same charges.
