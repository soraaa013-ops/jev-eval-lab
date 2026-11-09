# Run report: judgebench-gpt-5-mini

Generated from immutable raw result rows. This report is descriptive; the
synthetic smoke dataset must not be used to claim model quality.

## Run identity

- Model requested: `openai/gpt-5-mini`
- Adapter: `openrouter_chat`
- Dataset SHA-256: `e93afb67adad4fa12d1f6f34cb07e82f760682497efe7c4fd6f6c3147d4a3851`
- Created: 2026-11-09T01:56:15.589995+00:00

## Aggregate metrics

| Metric | Value |
|---|---:|
| Items | 350 |
| Judgments | 700 |
| Per-orientation accuracy | 0.8571 |
| Strict swapped-order accuracy | 0.8057 |
| Swap consistency | 0.8971 |
| Brier score | 0.1055 |
| Expected calibration error | 0.0715 |
| Latency p50 (ms) | 14160.5034 |
| Latency p95 (ms) | 46978.0862 |
| Reported total cost | 2.3001 |

## Accuracy by category

| Category | Accuracy |
|---|---:|
| livebench | 0.9123 |
| livecodebench | 0.9643 |
| mmlu | 0.7727 |

## Interpretation guardrails

- Compare confidence intervals on the full benchmark before ranking models.
- Treat conflicting A/B and B/A verdicts as failures in the strict metric.
- Hosted-model reruns may change even when request configuration is pinned.
- Calibration is dataset-specific; do not transfer a threshold without validation.
