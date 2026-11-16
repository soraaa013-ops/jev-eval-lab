# Pinned AgentProcessBench subsets

Source: https://huggingface.co/datasets/LulaCola/AgentProcessBench
Revision: `cd81f326aece8b0a3f6359e20df370690d3a98bf`.
Source dataset card declares MIT. Original authors: Shengda Fan et al.,
*AgentProcessBench: Diagnosing Step-Level Process Quality in Tool-Using Agents*,
https://arxiv.org/abs/2603.14465 (2026).

Unmodified `bfcl/test.jsonl` and `tau2/test.jsonl`, stored as `bfcl.jsonl` and
`tau2.jsonl`. Each contains 250 existing agent trajectories. Source URLs and
SHA-256 values are in [sources.json](sources.json). The remaining two subsets
were not selected for this tool-use/business-workflow study.

The files contain published task and reference fields. The inference runner
uses an explicit field whitelist and excludes ground_truth, answer_text,
tool_metrics, step_labels and final_label. Gold labels are used only for scoring.
