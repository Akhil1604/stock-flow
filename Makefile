.PHONY: install dev test lint seed infra-up compose-up compose-down

install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -e "backend[dev]"
	cd frontend && npm install

dev:
	@echo "Start dependencies with: make compose-up"
	@echo "API:    cd backend && ../.venv/bin/uvicorn app.main:app --reload"
	@echo "Web:    cd frontend && npm run dev"

test:
	. .venv/bin/activate && pytest -q backend/tests

lint:
	. .venv/bin/activate && ruff check backend

seed:
	. .venv/bin/activate && PYTHONPATH=backend python -m app.infrastructure.seed

compose-up:
	docker compose -f infra/docker-compose.yml up --build

infra-up:
	docker compose -f infra/docker-compose.yml up postgres redis kafka

compose-down:
	docker compose -f infra/docker-compose.yml down
