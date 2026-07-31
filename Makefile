.PHONY: dev format lint test test-unit test-int

dev:
	fastapi dev src\main.py

format:
	ruff format

lint: format
	ruff check --fix .

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit -v

test-int:
	pytest tests/integration -v

