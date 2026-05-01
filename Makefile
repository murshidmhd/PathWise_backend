# Variables
DC = sudo docker-compose
DCP = sudo docker-compose -f docker-compose.prod.yml

.PHONY: build up down restart migrate makemigrations shell logs django-bash db-shell deploy clean help ps prod-ps prune prod-up prod-logs prod-migrate prod-shell prod-bash prod-db-shell

# Default target
help:
	@echo "PathWise Management Commands:"
	@echo "--- MONITORING ---"
	@echo "  ps               Show running containers status (Development)"
	@echo "  prod-ps          Show running containers status (Production)"
	@echo "  logs             View real-time logs (Development)"
	@echo "  prod-logs        View real-time logs (Production)"
	@echo ""
	@echo "--- DEVELOPMENT (Local) ---"
	@echo "  up               Start containers"
	@echo "  down             Stop containers"
	@echo "  restart          Restart services"
	@echo "  migrate          Apply Django migrations (Main API)"
	@echo "  ws-migrate       Apply Django migrations (Websocket)"
	@echo "  makemigrations   Create new migrations"
	@echo "  shell            Open Django shell (Main API)"
	@echo "  ws-shell         Open Django shell (Websocket)"
	@echo "  django-bash      Open terminal inside Django container"
	@echo "  db-shell         Access local PostgreSQL (db1) directly"
	@echo "  db-restore       Restore database from backup.sql (Local)"
	@echo "  db-backup        Create a new backup.sql (Local)"
	@echo ""
	@echo "--- PRODUCTION (EC2) ---"
	@echo "  prod-up          Start containers (Uses GHCR Images)"
	@echo "  prod-migrate     Run migrations (Main API) on EC2"
	@echo "  prod-ws-migrate  Run migrations (Websocket) on EC2"
	@echo "  prod-shell       Open Django shell (Main API) on EC2"
	@echo "  prod-ws-shell    Open Django shell (Websocket) on EC2"
	@echo "  prod-db-restore  Restore database from backup.sql (EC2)"
	@echo ""
	@echo "--- CLEANUP ---"
	@echo "  prune            Clean up unused Docker images and space"
	@echo "  clean            Remove __pycache__ and .pyc files"

# Monitoring
ps:
	$(DC) ps

prod-ps:
	$(DCP) ps

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

# Django Commands (Development)
migrate:
	$(DC) exec django python manage.py migrate

ws-migrate:
	$(DC) exec websocket python manage.py migrate

makemigrations:
	$(DC) exec django python manage.py makemigrations

shell:
	$(DC) exec django python manage.py shell

ws-shell:
	$(DC) exec websocket python manage.py shell

django-bash:
	$(DC) exec django bash

db-shell:
	$(DC) exec db1 psql -U pathwise_admin -d pathwise-db

db-restore:
	cat backup.sql | $(DC) exec -i db1 psql -U pathwise_admin -d pathwise-db

db-backup:
	$(DC) exec db1 pg_dump -U pathwise_admin pathwise-db > backup.sql

# Django Commands (Production)
prod-migrate:
	$(DCP) exec django python manage.py migrate

prod-ws-migrate:
	$(DCP) exec websocket python manage.py migrate

prod-shell:
	$(DCP) exec django python manage.py shell

prod-ws-shell:
	$(DCP) exec websocket python manage.py shell

prod-bash:
	$(DCP) exec django bash

prod-db-shell:
	$(DCP) exec db1 psql -U pathwise_admin -d pathwise-db

prod-db-restore:
	cat backup.sql | $(DCP) exec -i db1 psql -U pathwise_admin -d pathwise-db

# Monitoring Logs
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
