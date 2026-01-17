.PHONY: install lint test run report api publish-pages

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

publish-pages:
	mkdir -p docs
	cp out/report.html docs/index.html
	cp out/index.png docs/index.png
	cp out/components.png docs/components.png
