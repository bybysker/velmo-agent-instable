.PHONY: install up down chat replay replay-offline test fmt lint typecheck

install:
	uv sync

up:
	docker compose up -d

down:
	docker compose down

chat:
	uv run python -m velmo.chat

replay:
	uv run python -m velmo.regression

replay-offline:
	uv run python -m velmo.regression --offline

test:
	uv run pytest -v

fmt:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .

typecheck:
	uv run mypy src
