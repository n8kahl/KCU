.PHONY: dev lint test fmt migrate upgrade worker beat

PYTHON?=python
POETRY?=poetry

venv:
	@if [ ! -d .venv ]; then $(PYTHON) -m venv .venv; fi

install: venv
	. .venv/bin/activate && pip install -U pip && pip install -e .

fmt:
	. .venv/bin/activate && black app

lint:
	. .venv/bin/activate && ruff check app

migrate:
	. .venv/bin/activate && alembic revision --autogenerate -m "manual"

upgrade:
	. .venv/bin/activate && alembic upgrade head

worker:
	. .venv/bin/activate && celery -A app.workers.celery_app.app worker -l INFO

beat:
	. .venv/bin/activate && celery -A app.workers.celery_app.app beat -l INFO

dev:
	. .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload

test:
	. .venv/bin/activate && pytest --cov=app/domain --cov=app/services
