.PHONY: install run migrate makemigrations seed test lint format typecheck precommit up down logs

install:
	pip install -r requirements-dev.txt
	pre-commit install

run:
	PYTHONPATH=backend uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload

migrate:
	alembic upgrade head

makemigrations:
	alembic revision --autogenerate -m "$(m)"

seed:
	PYTHONPATH=backend python scripts/seed.py

test:
	PYTHONPATH=backend pytest -v --cov=backend/app --cov-report=term-missing

lint:
	ruff check backend

format:
	black backend
	ruff check --fix backend

typecheck:
	mypy backend

precommit:
	pre-commit run --all-files

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f api
