PYTHON ?= python
RUN_DIR ?= artifacts/runs/smoke
CONFIG ?= configs/experiments/smoke.toml

.PHONY: test validate run analyze report smoke

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

validate:
	PYTHONPATH=src $(PYTHON) -m jev_eval.cli validate --config $(CONFIG)

run:
	PYTHONPATH=src $(PYTHON) -m jev_eval.cli run --config $(CONFIG)

analyze:
	PYTHONPATH=src $(PYTHON) -m jev_eval.cli analyze --run-dir $(RUN_DIR)

report:
	PYTHONPATH=src $(PYTHON) -m jev_eval.cli report --run-dir $(RUN_DIR)

smoke: test validate run analyze report

