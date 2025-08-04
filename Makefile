# Call Assignment System - Makefile
# Comandos útiles para desarrollo y operación del sistema

.PHONY: help install dev test clean docker-build docker-up docker-down logs demo

# Variables
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker-compose
PROJECT_NAME := call-assignment-system

# Colores para output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Mostrar ayuda de comandos disponibles
	@echo "$(GREEN)Call Assignment System - Comandos Disponibles$(NC)"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# INSTALACIÓN Y CONFIGURACIÓN
# =============================================================================

install: ## Instalar dependencias del proyecto
	@echo "$(GREEN)Instalando dependencias...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Dependencias instaladas correctamente$(NC)"

install-dev: install ## Instalar dependencias de desarrollo
	@echo "$(GREEN)Instalando dependencias de desarrollo...$(NC)"
	$(PIP) install pytest pytest-asyncio pytest-cov black flake8 mypy pre-commit
	pre-commit install
	@echo "$(GREEN)✅ Entorno de desarrollo configurado$(NC)"

setup-env: ## Crear archivo .env desde template
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✅ Archivo .env creado desde template$(NC)"; \
		echo "$(YELLOW)⚠️  Revisa y ajusta las variables en .env$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  El archivo .env ya existe$(NC)"; \
	fi

# =============================================================================
# DESARROLLO
# =============================================================================

dev: ## Iniciar servidor en modo desarrollo
	@echo "$(GREEN)Iniciando servidor en modo desarrollo...$(NC)"
	$(PYTHON) src/main.py api --reload

format: ## Formatear código con Black
	@echo "$(GREEN)Formateando código...$(NC)"
	black src/ tests/
	@echo "$(GREEN)✅ Código formateado$(NC)"

lint: ## Ejecutar linters (flake8, mypy)
	@echo "$(GREEN)Ejecutando linters...$(NC)"
	flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503
	mypy src/ --ignore-missing-imports
	@echo "$(GREEN)✅ Linting completado$(NC)"

check: format lint ## Ejecutar formateo y linting

# =============================================================================
# TESTING
# =============================================================================

test: ## Ejecutar tests unitarios
	@echo "$(GREEN)Ejecutando tests unitarios...$(NC)"
	$(PYTHON) -m pytest tests/ -v

test-cov: ## Ejecutar tests con cobertura
	@echo "$(GREEN)Ejecutando tests con cobertura...$(NC)"
	$(PYTHON) -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-integration: ## Ejecutar test de integración completo
	@echo "$(GREEN)Ejecutando test de integración...$(NC)"
	$(PYTHON) src/main.py test

test-quick: ## Ejecutar test rápido de validación
	@echo "$(GREEN)Ejecutando test rápido...$(NC)"
	$(PYTHON) src/main.py test --quick

test-stress: ## Ejecutar test de estrés (5 minutos)
	@echo "$(GREEN)Ejecutando test de estrés...$(NC)"
	$(PYTHON) src/main.py test --stress 5

# =============================================================================
# DOCKER
# =============================================================================

docker-build: ## Construir imágenes Docker
	@echo "$(GREEN)Construyendo imágenes Docker...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✅ Imágenes construidas$(NC)"

docker-up: ## Levantar servicios con Docker Compose
	@echo "$(GREEN)Levantando servicios...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Servicios iniciados$(NC)"
	@echo "$(YELLOW)API disponible en: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Grafana disponible en: http://localhost:3000 (admin/admin)$(NC)"
	@echo "$(YELLOW)Webhook receiver en: http://localhost:8001$(NC)"

docker-down: ## Detener servicios Docker
	@echo "$(GREEN)Deteniendo servicios...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Servicios detenidos$(NC)"

docker-logs: ## Ver logs de servicios Docker
	$(DOCKER_COMPOSE) logs -f

docker-clean: ## Limpiar contenedores e imágenes Docker
	@echo "$(GREEN)Limpiando Docker...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans
	docker system prune -f
	@echo "$(GREEN)✅ Limpieza completada$(NC)"

# =============================================================================
# OPERACIÓN
# =============================================================================

status: ## Mostrar estado del sistema
	@echo "$(GREEN)Estado del sistema:$(NC)"
	$(PYTHON) src/main.py status

demo: ## Ejecutar demostración del sistema
	@echo "$(GREEN)Iniciando demostración...$(NC)"
	$(PYTHON) src/main.py demo

cleanup: ## Limpiar datos de prueba
	@echo "$(GREEN)Limpiando datos de prueba...$(NC)"
	$(PYTHON) src/main.py cleanup
	@echo "$(GREEN)✅ Datos limpiados$(NC)"

load-test: ## Ejecutar test de carga (1 minuto, 200 llamadas/min)
	@echo "$(GREEN)Ejecutando test de carga...$(NC)"
	$(PYTHON) src/main.py load --duration 60 --calls-per-minute 200

# =============================================================================
# BASE DE DATOS
# =============================================================================

db-init: ## Inicializar base de datos
	@echo "$(GREEN)Inicializando base de datos...$(NC)"
	@if command -v psql >/dev/null 2>&1; then \
		psql $(DATABASE_URL) -f init-db.sql; \
		echo "$(GREEN)✅ Base de datos inicializada$(NC)"; \
	else \
		echo "$(RED)❌ psql no encontrado. Usa Docker o instala PostgreSQL client$(NC)"; \
	fi

db-reset: ## Resetear base de datos (¡PELIGROSO!)
	@echo "$(RED)⚠️  ADVERTENCIA: Esto eliminará TODOS los datos$(NC)"
	@read -p "¿Estás seguro? (y/N): " confirm && [ "$$confirm" = "y" ]
	@echo "$(GREEN)Reseteando base de datos...$(NC)"
	@if command -v psql >/dev/null 2>&1; then \
		psql $(DATABASE_URL) -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"; \
		psql $(DATABASE_URL) -f init-db.sql; \
		echo "$(GREEN)✅ Base de datos reseteada$(NC)"; \
	else \
		echo "$(RED)❌ psql no encontrado$(NC)"; \
	fi

# =============================================================================
# MONITOREO
# =============================================================================

metrics: ## Mostrar métricas del sistema
	@echo "$(GREEN)Métricas del sistema:$(NC)"
	@curl -s http://localhost:8000/system/metrics | python -m json.tool || echo "Sistema no disponible"

health: ## Verificar salud del sistema
	@echo "$(GREEN)Verificando salud del sistema...$(NC)"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "API no disponible"
	@curl -s http://localhost:8001/health | python -m json.tool || echo "Webhook receiver no disponible"

logs: ## Ver logs del sistema (Docker)
	$(DOCKER_COMPOSE) logs -f api

# =============================================================================
# UTILIDADES
# =============================================================================

clean: ## Limpiar archivos temporales
	@echo "$(GREEN)Limpiando archivos temporales...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@echo "$(GREEN)✅ Limpieza completada$(NC)"

requirements: ## Generar requirements.txt actualizado
	@echo "$(GREEN)Generando requirements.txt...$(NC)"
	$(PIP) freeze > requirements.txt
	@echo "$(GREEN)✅ requirements.txt actualizado$(NC)"

backup: ## Crear backup de la base de datos
	@echo "$(GREEN)Creando backup...$(NC)"
	@mkdir -p backups
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	docker-compose exec -T postgres pg_dump -U user call_assignment > backups/backup_$$timestamp.sql; \
	echo "$(GREEN)✅ Backup creado: backups/backup_$$timestamp.sql$(NC)"

# =============================================================================
# INFORMACIÓN
# =============================================================================

info: ## Mostrar información del proyecto
	@echo "$(GREEN)Call Assignment System$(NC)"
	@echo "======================"
	@echo "$(YELLOW)Versión:$(NC) 1.0.0"
	@echo "$(YELLOW)Autor:$(NC) Andrés Caballero"
	@echo "$(YELLOW)Descripción:$(NC) Sistema multi-tenant de asignación de llamadas"
	@echo ""
	@echo "$(YELLOW)URLs importantes:$(NC)"
	@echo "  API: http://localhost:8000"
	@echo "  Docs: http://localhost:8000/docs"
	@echo "  Health: http://localhost:8000/health"
	@echo "  Grafana: http://localhost:3000"
	@echo "  Webhook: http://localhost:8001"
	@echo ""
	@echo "$(YELLOW)Comandos principales:$(NC)"
	@echo "  make docker-up    # Levantar todo el stack"
	@echo "  make test         # Ejecutar tests"
	@echo "  make demo         # Demostración"
	@echo "  make status       # Estado del sistema"

# Comando por defecto
.DEFAULT_GOAL := help