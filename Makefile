.PHONY: build up down restart migrate makemigrations test shell logs django-bash ai-up ai-logs ai-bash clean help venv-run

# Default target
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build            Build or rebuild services"
	@echo "  up               Create and start containers"
	@echo "  down             Stop and remove containers, networks"
	@echo "  restart          Restart all services"
	@echo "  migrate          Apply all migrations"
	@echo "  makemigrations   Create new migrations for all apps"
	@echo "  test             Run all tests"
	@echo "  shell            Open Django Python shell"
	@echo "  django-bash      Open bash shell in the Django container"
	@echo "  logs             View output from containers"
	@echo "  ai-setup         Setup local venv for AI service"
	@echo "  ai-run           Run AI service locally (FastAPI)"
	@echo "  ai-ingest        Run AI ingestion script locally"
	@echo "  ai-logs          View AI service logs"
	@echo "  ai-bash          Open bash shell in the AI container"
	@echo "  clean            Remove python cache files"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

migrate:
	docker compose exec django python manage.py migrate

makemigrations:
	docker compose exec django python manage.py makemigrations

test:
	docker compose exec django python manage.py test

shell:
	docker compose exec django python manage.py shell

django-bash:
	docker compose exec django bash

logs:
	docker compose logs -f

ai-setup:
	cd ai-service && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt

ai-run:
	cd ai-service && ./venv/bin/uvicorn main:app --reload --port 8002

ai-ingest:
	cd ai-service && ./venv/bin/python scripts/ingest.py

# ai-up:
# 	docker compose up -d ai-service

# ai-logs:
# 	docker compose logs -f ai-service

# ai-bash:
# 	docker compose exec ai-service bash

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete




