# Makefile perAnatema Docker

.PHONY: help build up down logs restart clean backup rebuild

# Colori per l'output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

# Configurazione di default
COMPOSE_FILE=docker-compose.yml
COMPOSE_FILE_PROD=docker-compose.prod.yml
CONTAINER_NAME=anatema-2

help: ## Mostra questo messaggio di aiuto
	@echo "$(GREEN)Comandi disponibili perAnatema:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build dell'immagine Docker
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker-compose build --no-cache

rebuild: ## Rebuild completo (down, build, up)
	@echo "$(BLUE)Rebuilding sistema completo...$(NC)"
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "$(GREEN)Sistema riavviato con successo!$(NC)"
	docker build -t anatema .

build-no-cache: ## Build dell'immagine Docker senza cache
	@echo "$(GREEN)Building Docker image without cache...$(NC)"
	docker build --no-cache -t anatema .

up: ## Avvia i servizi (sviluppo)
	@echo "$(GREEN)Starting development services...$(NC)"
	docker-compose -f $(COMPOSE_FILE) up -d

up-prod: ## Avvia i servizi (produzione)
	@echo "$(GREEN)Starting production services...$(NC)"
	docker-compose -f $(COMPOSE_FILE_PROD) up -d

down: ## Ferma i servizi
	@echo "$(YELLOW)Stopping services...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down

down-prod: ## Ferma i servizi (produzione)
	@echo "$(YELLOW)Stopping production services...$(NC)"
	docker-compose -f $(COMPOSE_FILE_PROD) down

logs: ## Visualizza i log
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-prod: ## Visualizza i log (produzione)
	docker-compose -f $(COMPOSE_FILE_PROD) logs -f

restart: ## Riavvia i servizi
	@echo "$(YELLOW)Restarting services...$(NC)"
	docker-compose -f $(COMPOSE_FILE) restart

restart-prod: ## Riavvia i servizi (produzione)
	@echo "$(YELLOW)Restarting production services...$(NC)"
	docker-compose -f $(COMPOSE_FILE_PROD) restart

ps: ## Mostra lo stato dei servizi
	docker-compose -f $(COMPOSE_FILE) ps

ps-prod: ## Mostra lo stato dei servizi (produzione)
	docker-compose -f $(COMPOSE_FILE_PROD) ps

shell: ## Accedi al container
	docker-compose -f $(COMPOSE_FILE) exec web bash

shell-prod: ## Accedi al container (produzione)
	docker-compose -f $(COMPOSE_FILE_PROD) exec web bash

backup: ## Crea un backup del database
	@echo "$(GREEN)Creating database backup...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec web python -c "\
import shutil; \
import datetime; \
import os; \
os.makedirs('/app/backups', exist_ok=True); \
shutil.copy2('/app/instance/analisi_mu.db', f'/app/backups/analisi_mu_backup_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.db'); \
print('Backup created successfully')"

backup-prod: ## Crea un backup del database (produzione)
	@echo "$(GREEN)Creating database backup (production)...$(NC)"
	docker-compose -f $(COMPOSE_FILE_PROD) exec web python -c "\
import shutil; \
import datetime; \
import os; \
os.makedirs('/app/backups', exist_ok=True); \
shutil.copy2('/app/instance/analisi_mu.db', f'/app/backups/analisi_mu_backup_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.db'); \
print('Backup created successfully')"

clean: ## Pulisci container, immagini e volumi non utilizzati
	@echo "$(RED)Cleaning up Docker resources...$(NC)"
	docker system prune -a --volumes

clean-all: ## Pulisci tutto (ATTENZIONE: rimuove anche i volumi)
	@echo "$(RED)WARNING: This will remove all volumes and data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose -f $(COMPOSE_FILE) down -v
	docker system prune -a --volumes

dev: up logs ## Avvia in sviluppo e mostra i log

prod: up-prod logs-prod ## Avvia in produzione e mostra i log

status: ## Mostra lo stato completo del sistema
	@echo "$(GREEN)=== Docker System Info ===$(NC)"
	docker system df
	@echo "\n$(GREEN)=== Development Services ===$(NC)"
	docker-compose -f $(COMPOSE_FILE) ps
	@echo "\n$(GREEN)=== Production Services ===$(NC)"
	docker-compose -f $(COMPOSE_FILE_PROD) ps || true

init: ## Inizializza il progetto (prima volta)
	@echo "$(GREEN)Initializing project...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env file from template...$(NC)"; \
		cp .env.production .env; \
		echo "$(YELLOW)Please edit .env file with your configuration$(NC)"; \
	fi
	@make build
	@make up
	@echo "$(GREEN)Project initialized! Access at http://localhost:5016$(NC)"

# Comandi per la sincronizzazione etichette
sync-colors: ## Sincronizza i colori delle etichette (esegue nel container)
	@echo "$(GREEN)Sincronizzando i colori delle etichette...$(NC)"
	docker exec $(CONTAINER_NAME) python sync_all_label_colors.py --verbose

sync-colors-force: ## Forza la sincronizzazione dei colori (ATTENZIONE: sovrascrive colori personalizzati)
	@echo "$(RED)ATTENZIONE: Questa operazione sovrascriverà tutti i colori personalizzati!$(NC)"
	@read -p "Sei sicuro di voler continuare? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "$(GREEN)Forzando la sincronizzazione dei colori...$(NC)"
	docker exec $(CONTAINER_NAME) python sync_all_label_colors.py --force --verbose

sync-colors-dry: ## Simula la sincronizzazione senza salvare (test)
	@echo "$(BLUE)Simulando la sincronizzazione dei colori (dry-run)...$(NC)"
	docker exec $(CONTAINER_NAME) python sync_all_label_colors.py --dry-run --verbose
