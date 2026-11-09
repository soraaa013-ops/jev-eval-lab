# Run report: judgebench-jev-1.14

Generated from immutable raw result rows. This report is descriptive; the
synthetic smoke dataset must not be used to claim model quality.

## Run identity

- Model requested: `typesafe/jev-1.14`
- Adapter: `openrouter_decisions`
- Dataset SHA-256: `e93afb67adad4fa12d1f6f34cb07e82f760682497efe7c4fd6f6c3147d4a3851`
- Created: 2026-11-09T01:47:23.526329+00:00

## Aggregate metrics

| Metric | Value |
|---|---:|
| Items | 350 |
| Judgments | 700 |
| Per-orientation accuracy | 0.7814 |
| Strict swapped-order accuracy | 0.7057 |
| Swap consistency | 0.8486 |
| Brier score | 0.1439 |
| Log loss | 0.4427 |
| Expected calibration error | 0.0410 |
| Latency p50 (ms) | 435.5043 |
| Latency p95 (ms) | 522.8261 |
| Reported total cost | 0.0543 |

## Accuracy by category

| Category | Accuracy |
|---|---:|
| livebench | 0.7403 |
| livecodebench | 0.8452 |
| mmlu | 0.8052 |

## Interpretation guardrails

- Compare confidence intervals on the full benchmark before ranking models.
- Treat conflicting A/B and B/A verdicts as failures in the strict metric.
- Hosted-model reruns may change even when request configuration is pinned.
- Calibration is dataset-specific; do not transfer a threshold without validation.
