# Locked protocol: APB agent trajectory judges

Locked before the main run, 2026-11-16. Pilot tests only validate API/schema handling, not tune labels.

- Source: [AgentProcessBench](https://huggingface.co/datasets/LulaCola/AgentProcessBench), revision `cd81f326aece8b0a3f6359e20df370690d3a98bf` (dataset card: MIT). Complete BFCL (250) and tau2 (250) subsets, 6,147 human step labels and 500 final labels. 100 underlying queries, five traces each. This is NOT the full 1,000-trajectory APB leaderboard and NOT a rerun of BFCL/tau2 agents.
- Why these subsets: direct tool-use / multi-turn business workflows; these match the question of judging agent actions. GAIA and HotpotQA are excluded by task scope before inference, not by results. No filtering within the two selected subsets.
- Same blind evidence: task/question, task description, tools, all indexed messages, assistant indices. Exclude `ground_truth`, `answer_text`, `tool_metrics`, and human step/final labels. No content truncation. Full-trace retrospective evaluation; not an online prefix-only experiment. User goals in APB question are visible to the evaluator, as in the official blind protocol.
- Adapted English rubric shared across models: progress +1, neutral 0, error -1; cumulative error propagation unless corrected/independent recovery; final task success +1/failure -1. Based on official `eval/llm_annotation.py` at `0a42606b178a8c69d40c5765dc05c342f921e578`. All assistant steps are predicted, not just selected failure cases. This adaptation is not an exact reproduction of their prompt/leaderboard.
- Judges: `typesafe/jev-1.14`, `cloudflare/clef-flash`, `openai/gpt-5-mini`. System One: categorical choices and probabilities via Decisions. LLM: JSON labels plus concise evidence explanations, temperature 0, reasoning effort low, max output 12,000. This compares usable judge configurations, not isolated architecture under equal compute. Generation is still generation when constrained to JSON.
- Pilot revealed Clef's maximum of 64 question fields per request (HTTP 422). Main run splits **both decision models** at 64 questions, repeats full evidence, and combines predictions. GPT generates the complete judgment in one call. No trajectory is shortened. Report per-trajectory latency/cost, including all chunks/retries; batching differences remain a confound. Pilot data separate, not scored.
- Main run 1,500 trajectory judgments / 18,441 step predictions. Concurrency 12 total. Maximum three attempts per trajectory; retain failures and retry response metadata. Missing/invalid outputs count as wrong in all-request primary metrics; additionally report coverage. All output schema must validate before a trajectory counts as complete. Resumption preserves completed requests by hash.
- Primary: step macro-F1 (three classes), step accuracy, error recall (-1), error false-positive rate on non-errors; final accuracy and final-failure recall. Include majority-label baseline (+1), per-subset breakdown, confusion matrices. All metrics computed against held-out published labels; no training or prompt optimization on their values.
- Uncertainty: paired bootstrap over the 100 underlying queries (all five traces retained together), 2,000 draws, fixed seed 20261116, for step macro-F1 and accuracy differences. Labels are not independent samples; 6,147 steps must not be treated as 6,147 independent tasks.
- Cost is provider-reported USD, includes failed/retried responses when usage is supplied; unavailable failure charges are unknown. Latency is observed client wall time per complete trace, includes retries; shared API load and concurrency limit deployment generalizability. Do not interpret these as hardware-normalized throughput.
- Preserve source hashes, request/evidence hashes, raw responses, model identifiers, per-step predictions, failures, and analysis scripts. Read human labels for scoring only; examples selected after the run are explanatory, not independent validation.
- Scope of inference: agreement with public human annotations. It does not prove agent success improves, agent training benefits, generalization to unseen proprietary domains, or absence of training contamination. Human labels can be disputable; audit examples rather than treating every disagreement as certain model error.

## Post-run accounting notes (no inference or primary metric changes)

The auxiliary final-result prompt, like the official APB prompt, requests only
+1 or -1, but the downloaded gold data actually has 20 `final_label=0` records.
This mismatch was identified during analysis. Final binary accuracy is therefore
reported on the 480 non-neutral gold outcomes; all-500 exact-match accuracy is
also retained explicitly. No neutral gold was relabeled. All 6,147 step labels
remain in the primary metrics. This is a post-run denominator clarification,
not a preregistered exclusion or a full APB outcome metric.

The main run finished all 1,500 planned trajectory submissions. Three Clef
trajectories remained incomplete after the maximum three attempts due to
provider token-limit HTTP 422 errors (264 step labels unavailable); these remain
in all-request primary scoring as wrong. A secondary common-completion table
uses the same 497 traces / 5,883 steps across all three models, to separate
availability from classification quality. Its selection and metrics are labeled
post-run sensitivity analysis, not a replacement primary score. Failed terminal
records are cached on resume so rerunning --run does not silently retry beyond
the fixed attempt limit.
