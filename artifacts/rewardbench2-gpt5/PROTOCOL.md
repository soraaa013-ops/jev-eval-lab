# RewardBench 2: GPT-5 versus the existing Jev experiment

## Fixed before the first API call

- Model: `openai/gpt-5`, OpenRouter chat completions; medium reasoning, max 16,384 generated tokens including reasoning. No temperature parameter (not supported by the model catalog).
- Data: existing `data/benchmarks/rewardbench2.jsonl`, 1,865 rows. Source revision and file SHA are recorded in the existing provenance and this run's manifest.
- Two tasks: ranking (1,763 non-Ties rows) and rating (all 1,865 rows). No correctness-based sampling.
- Identity is `(subset, id, mode)`: 40 raw IDs recur across subsets. Candidate rotation still uses the original ID, exactly as in the Jev ranking run.
- Ranking: same four candidate texts, same deterministic rotation, same correctness/relevance/safety/instruction-following criterion as Jev. GPT returns the winning candidate label.
- Rating: same candidate texts, same order (chosen first, then rejected, without exposing those names), same five quality levels as Jev. All candidates share one input. GPT emits a scalar on the corresponding 0–4 scale; fractional scores are allowed. Jev's scores are native expected rubric indices, while GPT's are generated scalar ratings. This is a task-matched comparison, not an identical internal scoring mechanism.
- Rating's chosen-first order follows the existing Jev study and may introduce position bias. Neither model receives the gold labels, subset name, chosen count, or candidate provenance as input. This study does not establish robustness to rating candidate order.
- Main metrics: ranking accuracy by subset and all non-Ties; rating top-1 (any chosen tied for maximum counts), strict chosen-over-rejected accuracy, derived pairwise accuracy. Ties uses the existing margin formula; its score is not an ordinary accuracy or an official leaderboard submission.
- Paired model differences use `(subset,id)` to match the same inputs. Non-Ties ranking and rating differences get paired item bootstrap intervals (10,000 draws, fixed seed). Ties is reported separately. The pre-existing Jev run is historical, not simultaneous.
- At most three attempts per logical request; each failed attempt and available reported cost is retained. Terminal failures count as wrong in classification metrics. Ties aggregate is withheld if any required Ties rating is missing. Failed logical requests are cached, not silently retried beyond the limit.
- Pilot: first row of each subset plus maximum-candidate row; separate from main results and costs. Pilot validates interface/schema, not prompt selection by accuracy. Same prompts and settings in main.
- No online tools, retrieval, or agent intervention. This evaluates judges on existing answer candidates, not answer generation.

Results will be summarized in plain language in `report/rewardbench2-gpt5-comparison.md` after completion.

## Transport recovery addendum (during execution)

The initial 48-worker run encountered HTTP 402 `in_flight_budget_exhausted`:
OpenRouter refused admission before running the model, with no usage returned.
These are not incorrect model predictions. After outstanding calls settle,
resubmit only such unbilled rejections with identical requests, at lower
concurrency. All original rejection events remain in the result journal;
recovery events are explicitly marked and merged by `(subset,id,mode)`.
No valid prediction or usage-bearing model attempt is rerun by this recovery.
The scheduler now drains active work and stops enqueuing on a budget rejection.
Analysis refuses to publish full model scores while admission rejections remain.

Account credit availability is lower than the API-key spending ceiling.
Prioritize all non-Ties ranking and Ties rating if funds do not cover the full
second protocol; report incomplete rating coverage instead of a partial-data
rating score. Prompt, candidate ordering, model and reasoning settings stay fixed.

## Final requested scope

After winner selection and Ties completed, the user requested winner selection
only. The 1,763-row ranking is the primary deliverable. Retain the completed
Ties supplement and 288 total rating predictions, but do not continue remaining
ratings or publish a partial full-rating aggregate. No API calls remain running.
