# Variable to easily switch between 'docker compose' and 'docker-compose'
DC = sudo docker-compose

.PHONY: build up down restart migrate makemigrations shell logs django-bash db-shell deploy clean help

# Default target
help:
	@echo "PathWise EC2 Management Commands:"
	@echo "  deploy           Pull code, rebuild, and migrate"
	@echo "  up               Start all containers in background"
	@echo "  down             Stop and remove containers"
	@echo "  restart          Restart all services"
	@echo "  migrate          Apply Django database migrations"
	@echo "  makemigrations   Create new migrations"
	@echo "  shell            Open Django Python shell"
	@echo "  db-shell         Access RDS PostgreSQL directly"
	@echo "  logs             View real-time logs from all containers"
	@echo "  django-bash      Open terminal inside Django container"
	@echo "  clean            Remove __pycache__ and .pyc files"

# Deployment workflow
deploy:
	git pull origin beta
	$(DC) up -d --build
	$(DC) exec django python manage.py migrate

build:
	$(DC) build

up:
	$(DC) up -d

down:
	$(DC) down

restart:
	$(DC) restart

# Django Commands
migrate:
	$(DC) exec django python manage.py migrate

makemigrations:
	$(DC) exec django python manage.py makemigrations

shell:
	$(DC) exec django python manage.py shell

django-bash:
	$(DC) exec django bash

# Database
db-shell:
	PGPASSWORD='b6489ZUBYPnTQ3r' psql -h pathwise-db.cly28megm1pn.ap-south-1.rds.amazonaws.com -U pathwise_admin -d pathwise_db

# Monitoring
logs:
	$(DC) logs -f

# Specific Service Logs (Useful for debugging Google Auth)
logs-django:
	$(DC) logs -f django

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
