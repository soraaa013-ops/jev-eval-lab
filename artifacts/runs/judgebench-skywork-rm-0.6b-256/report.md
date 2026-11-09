# Run report: judgebench-skywork-rm-0.6b-256

Generated from immutable raw result rows. This report is descriptive; the
synthetic smoke dataset must not be used to claim model quality.

## Run identity

- Model requested: `Skywork/Skywork-Reward-V2-Qwen3-0.6B`
- Adapter: `local_bradley_terry_reward_model`
- Dataset SHA-256: `e93afb67adad4fa12d1f6f34cb07e82f760682497efe7c4fd6f6c3147d4a3851`
- Created: 2026-11-09T08:15:55.786341+00:00

## Aggregate metrics

| Metric | Value |
|---|---:|
| Items | 350 |
| Judgments | 700 |
| Per-orientation accuracy | 0.6029 |
| Strict swapped-order accuracy | 0.6029 |
| Swap consistency | 1.0000 |
| Brier score | 0.3040 |
| Log loss | 0.9609 |
| Expected calibration error | 0.2457 |
| Latency p50 (ms) | 10282.6344 |
| Latency p95 (ms) | 11210.0861 |
| Reported total cost | 0.0000 |

## Accuracy by category

| Category | Accuracy |
|---|---:|
| livebench | 0.6104 |
| livecodebench | 0.6905 |
| mmlu | 0.5714 |

## Interpretation guardrails

- Compare confidence intervals on the full benchmark before ranking models.
- Treat conflicting A/B and B/A verdicts as failures in the strict metric.
- Hosted-model reruns may change even when request configuration is pinned.
- Calibration is dataset-specific; do not transfer a threshold without validation.
