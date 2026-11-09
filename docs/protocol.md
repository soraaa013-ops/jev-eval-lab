# Experimental protocol

## Primary question

When can a typed decision model serve as a reliable evaluator, and how does its
quality–calibration–robustness–cost frontier compare with generative judges and
specialized reward models?

## Comparisons executed in v1.0

1. Pairwise objective correctness with A/B order reversal on JudgeBench.
2. Multi-candidate winner selection on RewardBench 2.
3. Ordered rubric scoring, analysed separately from winner selection.
4. Pinned Jev 1.14 versus two generative judges and one open reward model.

Binary atomic criteria, holistic-versus-atomic ablations, and moving-alias drift
are separate future studies. They are not silently pooled into this release.

## Bias controls

- Run every pair in both A/B orders.
- Keep candidate identity hidden.
- Freeze prompts before the test split is run.
- Record invalid outputs and API failures rather than silently retrying forever.
- Use paired bootstrap confidence intervals for model differences.
- Report category results; a pooled average can hide important failures.

## Calibration

Accuracy is not evidence of calibrated probabilities. This release reports
Brier score, log loss, 10-bin ECE, reliability plots, and descriptive
risk–coverage curves. Deployment thresholds are deliberately not selected on
the test set; they require a separate in-domain validation split.

## Reproducibility

Pin dataset revision and hash, model ID, prompt, request body, software version,
and raw response. Hosted APIs are not bit-reproducible; publish raw responses so
all tables can be regenerated without calling the API.

