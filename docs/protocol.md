# Experimental protocol

## Primary question

When can a typed decision model serve as a reliable evaluator, and how does its
quality–calibration–robustness–cost frontier compare with generative judges and
specialized reward models?

## Required comparisons

1. Pairwise preference on objective and human-preference datasets.
2. Binary criteria such as factuality, groundedness, and policy compliance.
3. Ordered rubric scoring, analysed separately from binary judgment.
4. Atomic criteria versus one holistic rubric.
5. Pinned Jev releases versus a moving `jev-latest` alias.

## Bias controls

- Run every pair in both A/B orders.
- Keep candidate identity hidden.
- Freeze prompts before the test split is run.
- Record invalid outputs and API failures rather than silently retrying forever.
- Use paired bootstrap confidence intervals for model differences.
- Report category results; a pooled average can hide important failures.

## Calibration

Accuracy is not evidence of calibrated probabilities. Report Brier score, log
loss, ECE with sensitivity to bin count, reliability plots, and risk–coverage
curves. Thresholds must be selected on a validation split and evaluated once on
the held-out test split.

## Reproducibility

Pin dataset revision and hash, model ID, prompt, request body, software version,
and raw response. Hosted APIs are not bit-reproducible; publish raw responses so
all tables can be regenerated without calling the API.

