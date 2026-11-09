# Adding a model

Implement `JudgeAdapter.judge()` in `src/jev_eval/adapters.py` and register it in
`make_adapter`. An adapter must return the winning label, probabilities when the
provider exposes them, the actual model version, latency, raw request/response,
usage, and provider-reported cost.

Do not route a Decisions model through chat completions. Do not convert prose
confidence into a probability unless the experiment explicitly studies that
conversion. Parsers must fail loudly on malformed output.

Add a TOML file under `configs/experiments/`; credentials must be referenced by
environment-variable name, never embedded in configuration.

