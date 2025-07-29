COMPOSE_FILE := docker-compose.yml

stop:
	docker compose -f $(COMPOSE_FILE) down
	docker compose -f $(COMPOSE_FILE) rm -f

restart:
	docker compose -f $(COMPOSE_FILE) down
	docker compose -f $(COMPOSE_FILE) rm -f
	docker compose -f $(COMPOSE_FILE) up -d
	docker compose -f $(COMPOSE_FILE) logs -f

start:
	docker compose -f $(COMPOSE_FILE) up -d

rebuild:
	docker compose -f $(COMPOSE_FILE) build

logs:
	docker compose -f $(COMPOSE_FILE) logs -f
