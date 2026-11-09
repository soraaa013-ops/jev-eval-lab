# Dataset provenance and redistribution status

Frozen on 2026-11-09. Hashes refer to the exact converted files committed in
this repository.

| Dataset | Upstream revision | Local file SHA-256 | Upstream license/status |
|---|---|---|---|
| JudgeBench GPT-4o split | `ScalerLab/JudgeBench@e2c52c284e735e139b3daa61c206ee208f36c461` | `e93afb67adad4fa12d1f6f34cb07e82f760682497efe7c4fd6f6c3147d4a3851` | No repository-level license was present at the frozen revision. The paper and repository make the benchmark public, but absence of a license is not permission for unrestricted redistribution. Review before external redistribution. |
| RewardBench 2 test | `allenai/reward-bench-2@7ff08853b0d5686e79b13fda8677024f566a104a` | `6999c797b2fdb9ed2a1aeb1fec481ee64640bcaaea69fb3116f7c740e9c10895` | ODC-BY; dataset card also requires following third-party model-output terms and Ai2 Responsible Use Guidelines. |

The transformation scripts preserve the upstream data content while converting
field names. `prepare_judgebench.py` pins the Git commit. `prepare_rewardbench2.py`
pins the dataset revision below so a future upstream update cannot silently alter
the experiment.

This document records provenance; it is not legal advice. In particular,
RewardBench 2 contains outputs from models with several different licenses and
terms. Internal or commercial reuse must be reviewed against the dataset card.

## Open model provenance

The local baseline uses `Skywork/Skywork-Reward-V2-Qwen3-0.6B` revision
`8c14a4e9e6321deaf572544339b16b8d6bbe8886`, licensed Apache-2.0 according to
the upstream model card. The run manifest additionally records the revision
resolved by Transformers, library version, context limit, and local data hash.
