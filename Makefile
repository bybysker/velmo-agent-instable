.PHONY: install up down chat test fmt lint typecheck

install:
	uv sync

up:
	docker compose up -d

down:
	docker compose down

chat:
	uv run python -m velmo.chat

chat_ex_agent:
	docker compose exec agent uv run python -m velmo.chat

test:
	uv run pytest -v

fmt:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .

typecheck:
	uv run mypy src
