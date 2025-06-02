# Docker-based development
docker-build:
	docker-compose build

docker-up:
	docker-compose up

docker-up-detached:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-shell:
	docker-compose exec web /bin/bash

docker-rebuild:
	docker-compose down && docker-compose build --no-cache && docker-compose up

# Utility commands
docker-clean:
	docker-compose down -v
	docker system prune -f

hotfix:
	@echo "Enter commit message for hotfix:"
	@read -p "> " commit_msg; \
	git add . && git commit -m "$$commit_msg" && git push production main:master

# Convenience aliases for common commands
build: docker-build
up: docker-up
down: docker-down
logs: docker-logs
shell: docker-shell

# Development commands
# Run with Docker (matching Node.js pattern)
dev:
	docker-compose up

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests (SVG builder tests only - Redis tests need Docker)
test:
	pytest tests/test_svg_builder.py

# Run all tests including Redis (requires Docker)
test-all:
	docker-compose exec web python -m pytest tests/ -v

# Run tests in Docker container
docker-test:
	docker-compose exec web python -m pytest tests/ -v

# Run worker only
worker:
	rq worker --url redis://localhost:6379 svg-generation

# Run web server only
web:
	gunicorn app:app --bind 0.0.0.0:5000 --reload 