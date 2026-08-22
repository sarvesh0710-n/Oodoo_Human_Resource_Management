.PHONY: help venv install test db-migrate db-upgrade db-downgrade db-status db-history clean

PYTHON = .venv/bin/python
ALEMBIC = .venv/bin/alembic
PIP = .venv/bin/pip

help:
	@echo "Dayflow HRMS Database Management Commands:"
	@echo "  make venv         - Create Python virtual environment (.venv) and install dependencies"
	@echo "  make install      - Install/update dependencies from requirements.txt"
	@echo "  make test         - Run database unit tests"
	@echo "  make db-migrate   - Generate a new migration revision (usage: make db-migrate msg=\"title\")"
	@echo "  make db-upgrade   - Apply pending database migrations (alembic upgrade head)"
	@echo "  make db-downgrade - Rollback the last migration revision (alembic downgrade -1)"
	@echo "  make db-status    - Show current migration revision status"
	@echo "  make db-history   - Display migration revision history log"
	@echo "  make clean        - Clean __pycache__ folders and temporary files"

venv:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install:
	$(PIP) install -r requirements.txt

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"

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
