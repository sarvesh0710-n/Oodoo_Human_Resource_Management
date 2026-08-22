.PHONY: help venv install run run-port test seed-db populate-db create-admin create-user reset-db db-migrate db-upgrade db-downgrade db-status db-history clean

PYTHON = .venv/bin/python
UVICORN = .venv/bin/uvicorn
ALEMBIC = .venv/bin/alembic
PYTEST = .venv/bin/pytest
PIP = .venv/bin/pip

PORT ?= 8000
HOST ?= 0.0.0.0

help:
	@echo "Dayflow HRMS Commands:"
	@echo "  make run          - Start Dayflow HRMS Jinja2 web application & API server (port 8000)"
	@echo "  make run-port     - Start app server on custom port (usage: make run-port PORT=8001)"
	@echo "  make seed-db      - Seed initial database data (Admin HR, Employee, Departments, Leave Types)"
	@echo "  make populate-db  - Populate full sample data (Multiple departments, HRs, employees, attendance, leaves)"
	@echo "  make create-admin - Create or promote an Admin HR user (usage: make create-admin EMAIL=... PASS=...)"
	@echo "  make create-user  - Create a user (usage: make create-user EMAIL=... PASS=... ROLE=employee)"
	@echo "  make reset-db     - Reset and re-seed the entire database"
	@echo "  make install      - Install backend Python dependencies"
	@echo "  make venv         - Create Python virtual environment (.venv) and install dependencies"
	@echo "  make test         - Execute backend Pytest suite"
	@echo "  make db-migrate   - Generate a new migration revision (usage: make db-migrate msg=\"title\")"
	@echo "  make db-upgrade   - Apply pending database migrations (alembic upgrade head)"
	@echo "  make db-downgrade - Rollback the last migration revision (alembic downgrade -1)"
	@echo "  make db-status    - Show current migration revision status"
	@echo "  make db-history   - Display migration revision history log"
	@echo "  make clean        - Clean __pycache__ and temporary files"

install:
	$(PIP) install -r requirements.txt

run:
	$(UVICORN) main:app --reload --host $(HOST) --port $(PORT)

run-port:
	$(UVICORN) main:app --reload --host $(HOST) --port $(PORT)

seed-db:
	$(PYTHON) -m scripts.seed_db

populate-db:
	$(PYTHON) -m scripts.populate_sample_data

create-admin:
	@if [ -n "$(EMAIL)" ] && [ -n "$(PASS)" ]; then \
		$(PYTHON) -m scripts.create_admin --email $(EMAIL) --password $(PASS); \
	else \
		$(PYTHON) -m scripts.create_admin; \
	fi

create-user:
	@if [ -z "$(EMAIL)" ] || [ -z "$(PASS)" ]; then \
		echo "Usage: make create-user EMAIL=emp@company.com PASS=secret [ROLE=employee]"; \
		exit 1; \
	fi
	$(PYTHON) -m scripts.create_user --email $(EMAIL) --password $(PASS) --role $(or $(ROLE),employee)

reset-db:
	$(PYTHON) -m scripts.reset_db

venv:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

test:
	$(PYTEST) -v

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
