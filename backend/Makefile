install:
	uv sync --extra dev --extra agentic

dev:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	uv run --extra dev pytest -q

lint:
	uv run --extra dev ruff check .

format:
	uv run --extra dev ruff format .

.PHONY: install dev test lint format
