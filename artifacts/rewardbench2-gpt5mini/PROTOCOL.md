# GPT-5 mini: RewardBench 2 winner selection

The user requested GPT-5 mini and restricted this work to winner selection.

- Model: `openai/gpt-5-mini`, medium reasoning, 16,384 maximum generated tokens including reasoning.
- Scope: all 1,763 non-Ties rows; no candidate-rating experiment or Ties calls.
- Data, prompts, candidate rotation, output schema and scoring are identical to the completed GPT-5 ranking study. Only the model field changes.
- Jev is compared on the same candidates and rotation using the historical Jev ranking results.
- Each row presents the prompt and four candidates; GPT selects A/B/C/D. Gold fields are excluded.
- Primary score: proportion of correct choices, by category and all non-Ties combined. Pair model results by `(subset,id)` because raw IDs recur across subsets.
- Paired item bootstrap: 10,000 draws, seed 20261117. Report differences against both Jev and GPT-5.
- Pilot: first row from each of the five non-Ties categories; separate from main results and cost. No accuracy-based prompt tuning.
- At most three attempts per model request. Unbilled HTTP 402 admission rejections stop new scheduling and can be resumed unchanged; they are not model errors. Other terminal model failures count as incorrect. Do not publish incomplete coverage as a full benchmark score.
- Preserve raw requests, responses, attempts, reported costs and latency. Do not expose credentials or provider account IDs.
- This is a controlled task comparison, not an official leaderboard submission or a claim of equal internal computation. Both GPT variants use the medium effort setting, which does not imply equal compute.
