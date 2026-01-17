.PHONY: install lint test run report api

install:
	python -m pip install -e .[dev]

lint:
	ruff check src tests
	mypy src

test:
	pytest -q

run:
	fragility monitor --refresh --report out/

report:
	fragility monitor --report out/

api:
	fragility serve
