install:
	uv sync

dev:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	uv run pytest -q

lint:
	uv run ruff check .
