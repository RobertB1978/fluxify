SHELL := /bin/bash
PYTHON ?= python3
VENV ?= .venv
BACKEND_DIR := apps/backend
PYTHONPATH := $(BACKEND_DIR)
UVICORN ?= uvicorn

.PHONY: setup migrate health smoke test clean run lint

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r $(BACKEND_DIR)/requirements.txt

migrate:
	PYTHONPATH=$(PYTHONPATH) $(VENV)/bin/alembic -c $(BACKEND_DIR)/alembic.ini upgrade head

health:
	PYTHONPATH=$(PYTHONPATH) $(VENV)/bin/python $(BACKEND_DIR)/scripts/health_check.py

smoke:
	PYTHONPATH=$(PYTHONPATH) $(VENV)/bin/python $(BACKEND_DIR)/scripts/smoke_test.py

lint:
	PYTHONPATH=$(PYTHONPATH) $(VENV)/bin/python -m compileall $(BACKEND_DIR)/app

test:
	PYTHONPATH=$(PYTHONPATH) $(VENV)/bin/pytest --cov=$(BACKEND_DIR)/app --cov-report=term-missing

clean:
	rm -rf $(VENV)
	rm -rf $(BACKEND_DIR)/__pycache__ $(BACKEND_DIR)/app/__pycache__
	rm -f test_stage1.sqlite3
	rm -rf test_data

run:
	PYTHONPATH=$(PYTHONPATH) $(VENV)/bin/$(UVICORN) app.main:app --app-dir $(BACKEND_DIR)/app --host 0.0.0.0 --port 8000
