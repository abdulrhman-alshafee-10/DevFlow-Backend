.PHONY: up down build logs shell test migrate db-shell format lint

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

shell:
	docker-compose exec api /bin/bash

test:
	docker-compose exec api pytest --cov=app

migrate:
	docker-compose exec api alembic upgrade head

db-shell:
	docker-compose exec db psql -U devflow -d devflow_db

format:
	docker-compose exec api black app tests
	docker-compose exec api isort app tests

lint:
	docker-compose exec api flake8 app tests
	docker-compose exec api mypy app
