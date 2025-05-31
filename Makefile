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
	docker-compose exec drawscape-api /bin/bash

docker-rebuild:
	docker-compose down && docker-compose build --no-cache && docker-compose up

# Utility commands
docker-clean:
	docker-compose down -v
	docker system prune -f

hotfix:
	git add . && git commit -m "Hotfix" && git push production main:master

# Convenience aliases for common commands
build: docker-build
up: docker-up
down: docker-down
logs: docker-logs
shell: docker-shell 