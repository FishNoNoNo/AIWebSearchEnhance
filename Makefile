.PHONY: install test run lint

install:
	pip install -r requirements.txt

test:
	pytest

run:
	uvicorn src.main:app --host 0.0.0.0 --port 18080

lint:
	python -m compileall src tests
