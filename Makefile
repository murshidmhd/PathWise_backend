# Variables
DC = sudo docker-compose
DCP = sudo docker-compose -f docker-compose.prod.yml

.PHONY: build up down restart migrate makemigrations shell logs django-bash db-shell deploy clean help ps prune prod-up prod-logs

# Default target
help:
	@echo "PathWise Management Commands:"
	@echo "  ps               Show running containers status"
	@echo "  up               Start containers (Development)"
	@echo "  prod-up          Start containers (Production - GHCR Images)"
	@echo "  down             Stop all containers"
	@echo "  restart          Restart all services"
	@echo "  migrate          Apply Django database migrations"
	@echo "  makemigrations   Create new migrations"
	@echo "  shell            Open Django Python shell"
	@echo "  db-shell         Access local PostgreSQL (db1) directly"
	@echo "  logs             View real-time logs (Development)"
	@echo "  prod-logs        View real-time logs (Production)"
	@echo "  prune            Clean up unused Docker images and space"
	@echo "  clean            Remove __pycache__ and .pyc files"

# Monitoring
ps:
	$(DC) ps

# Standard Commands
up:
	$(DC) up -d

prod-up:
	$(DCP) pull
	$(DCP) up -d

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

# Database (Local db1)
db-shell:
	$(DC) exec db1 psql -U pathwise_admin -d pathwise-db

# Monitoring
logs:
	$(DC) logs -f

prod-logs:
	$(DCP) logs -f

# Specific Service Logs
logs-django:
	$(DC) logs -f django

# Cleanup
prune:
	sudo docker system prune -a -f
	sudo docker image prune -f

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
