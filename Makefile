.PHONY: dev format test test-unit test-int

dev: env
	fastapi dev src\main.py

format:
	ruff format

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit -v

test-int:
	pytest tests/integration -v

