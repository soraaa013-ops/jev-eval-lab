# Run report: judgebench-qwen3-30b-a3b

Generated from immutable raw result rows. This report is descriptive; the
synthetic smoke dataset must not be used to claim model quality.

## Run identity

- Model requested: `qwen/qwen3-30b-a3b-instruct-2507`
- Adapter: `openrouter_chat`
- Dataset SHA-256: `e93afb67adad4fa12d1f6f34cb07e82f760682497efe7c4fd6f6c3147d4a3851`
- Created: 2026-11-09T01:48:51.371908+00:00

## Aggregate metrics

| Metric | Value |
|---|---:|
| Items | 350 |
| Judgments | 700 |
| Per-orientation accuracy | 0.6429 |
| Strict swapped-order accuracy | 0.4000 |
| Swap consistency | 0.5143 |
| Brier score | 0.2952 |
| Expected calibration error | 0.2590 |
| Latency p50 (ms) | 1191.2211 |
| Latency p95 (ms) | 8725.6472 |
| Reported total cost | 0.1128 |

## Accuracy by category

| Category | Accuracy |
|---|---:|
| livebench | 0.6494 |
| livecodebench | 0.7857 |
| mmlu | 0.5974 |

## Interpretation guardrails

- Compare confidence intervals on the full benchmark before ranking models.
- Treat conflicting A/B and B/A verdicts as failures in the strict metric.
- Hosted-model reruns may change even when request configuration is pinned.
- Calibration is dataset-specific; do not transfer a threshold without validation.
