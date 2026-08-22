.PHONY: help venv install install-frontend build-frontend dev-frontend run run-port test db-migrate db-upgrade db-downgrade db-status db-history clean

PYTHON = .venv/bin/python
UVICORN = .venv/bin/uvicorn
ALEMBIC = .venv/bin/alembic
PYTEST = .venv/bin/pytest
PIP = .venv/bin/pip

PORT ?= 8000
HOST ?= 0.0.0.0

help:
	@echo "Dayflow HRMS Commands:"
	@echo "  make run            - Build frontend & start Dayflow HRMS backend server (port 8000)"
	@echo "  make run-port       - Build frontend & start server on custom port (usage: make run-port PORT=8001)"
	@echo "  make build-frontend - Install npm dependencies & build React SPA production bundle (frontend/dist)"
	@echo "  make dev-frontend   - Start Vite frontend development server (http://localhost:5173)"
	@echo "  make install        - Install backend Python dependencies & frontend npm dependencies"
	@echo "  make venv           - Create Python virtual environment (.venv) and install dependencies"
	@echo "  make test           - Execute backend Pytest suite & verify frontend build"
	@echo "  make db-migrate     - Generate a new migration revision (usage: make db-migrate msg=\"title\")"
	@echo "  make db-upgrade     - Apply pending database migrations (alembic upgrade head)"
	@echo "  make db-downgrade   - Rollback the last migration revision (alembic downgrade -1)"
	@echo "  make db-status      - Show current migration revision status"
	@echo "  make db-history     - Display migration revision history log"
	@echo "  make clean          - Clean __pycache__, node_modules build artifacts, and temporary files"

build-frontend:
	@echo "Building React SPA frontend..."
	npm --prefix frontend install
	npm --prefix frontend run build

dev-frontend:
	@echo "Starting Vite frontend dev server..."
	npm --prefix frontend run dev

install-frontend:
	npm --prefix frontend install

install:
	$(PIP) install -r requirements.txt
	npm --prefix frontend install

run: build-frontend
	$(UVICORN) main:app --reload --host $(HOST) --port $(PORT)

run-port: build-frontend
	$(UVICORN) main:app --reload --host $(HOST) --port $(PORT)

venv:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	npm --prefix frontend install

test:
	$(PYTEST) -v
	npm --prefix frontend run build

db-migrate:
	@if [ -z "$(msg)" ]; then \
		echo "Error: Please specify a migration message, e.g., make db-migrate msg=\"migration title\""; \
		exit 1; \
	fi
	$(ALEMBIC) revision --autogenerate -m "$(msg)"

db-upgrade:
	$(ALEMBIC) upgrade head

db-downgrade:
	$(ALEMBIC) downgrade -1

db-status:
	$(ALEMBIC) current
	$(ALEMBIC) heads

db-history:
	$(ALEMBIC) history --verbose

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
