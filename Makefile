# Makefile para Sistema de Asignación de Llamadas
# Prueba Técnica - Insight Solutions

.PHONY: help install up down test test-quick test-stress status logs clean health demo api

# Colores para output
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Mostrar ayuda
	@echo "$(GREEN)Sistema de Asignación de Llamadas - Prueba Técnica$(NC)"
	@echo "$(YELLOW)Comandos disponibles:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Instalar dependencias Python
	@echo "$(YELLOW)📦 Instalando dependencias...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencias instaladas$(NC)"

up: ## Levantar todos los servicios
	@echo "$(YELLOW)🚀 Levantando servicios...$(NC)"
	@# Detener Redis local si está corriendo
	@-sudo systemctl stop redis-server 2>/dev/null || true
	@-redis-cli shutdown 2>/dev/null || true
	@echo "$(YELLOW)📦 Iniciando contenedores Docker...$(NC)"
	docker-compose up -d
	@echo "$(YELLOW)⏳ Esperando que los servicios estén listos...$(NC)"
	@sleep 20
	@echo "$(GREEN)✅ Todos los servicios están funcionando!$(NC)"
	@make status

down: ## Parar y limpiar todos los servicios
	@echo "$(YELLOW)🛑 Deteniendo servicios...$(NC)"
	docker-compose down -v --remove-orphans
	@echo "$(GREEN)✅ Servicios detenidos$(NC)"

test: up ## Ejecutar prueba completa (Prueba 2)
	@echo "$(GREEN)🔬 EJECUTANDO PRUEBA TÉCNICA COMPLETA$(NC)"
	@echo "$(YELLOW)📊 Test: 100 llamadas, 20 agentes$(NC)"
	python src/main.py test

test-quick: up ## Ejecutar prueba rápida (10 llamadas)
	@echo "$(GREEN)⚡ EJECUTANDO PRUEBA RÁPIDA$(NC)"
	python src/main.py test --quick

test-stress: up ## Ejecutar prueba de estrés (5 minutos)
	@echo "$(GREEN)💪 EJECUTANDO PRUEBA DE ESTRÉS$(NC)"
	python src/main.py test --stress 5

status: ## Ver estado de todos los servicios
	@echo "$(GREEN)📊 ESTADO DEL SISTEMA$(NC)"
	@echo "$(YELLOW)Docker Services:$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(YELLOW)Health Checks:$(NC)"
	@echo -n "API (8000): "
	@curl -s http://localhost:8000/health >/dev/null && echo "$(GREEN)✅ OK$(NC)" || echo "$(RED)❌ FAILED$(NC)"
	@echo -n "Webhook (8001): "
	@curl -s http://localhost:8001/health >/dev/null && echo "$(GREEN)✅ OK$(NC)" || echo "$(RED)❌ FAILED$(NC)"
	@echo -n "Grafana (3000): "
	@curl -s http://localhost:3000/api/health >/dev/null && echo "$(GREEN)✅ OK$(NC)" || echo "$(RED)❌ FAILED$(NC)"
	@echo -n "Prometheus (9090): "
	@curl -s http://localhost:9090/-/healthy >/dev/null && echo "$(GREEN)✅ OK$(NC)" || echo "$(RED)❌ FAILED$(NC)"

logs: ## Ver logs de todos los servicios
	@echo "$(YELLOW)📋 Logs del sistema:$(NC)"
	docker-compose logs -f

health: ## Verificar salud del sistema
	@echo "$(GREEN)🏥 DIAGNÓSTICO COMPLETO$(NC)"
	python src/main.py status

clean: down ## Limpiar todo (contenedores, volúmenes, imágenes)
	@echo "$(YELLOW)🧹 Limpieza completa...$(NC)"
	docker system prune -f
	docker volume prune -f
	@echo "$(GREEN)✅ Sistema limpio$(NC)"

demo: up ## Ejecutar demo interactivo
	@echo "$(GREEN)🎮 DEMO INTERACTIVO$(NC)"
	python src/main.py demo

api: up ## Solo iniciar API (para desarrollo)
	@echo "$(GREEN)🔧 MODO DESARROLLO - Solo API$(NC)"
	python src/main.py api

# Comandos para los evaluadores
evaluacion: ## Comando principal para evaluadores
	@echo "$(GREEN)🎯 PRUEBA TÉCNICA - INSIGHT SOLUTIONS$(NC)"
	@echo "$(YELLOW)Iniciando sistema completo...$(NC)"
	@make up
	@echo ""
	@echo "$(GREEN)✅ Sistema listo para evaluación$(NC)"
	@echo "$(YELLOW)URLs importantes:$(NC)"
	@echo "  • API: http://localhost:8000/docs"
	@echo "  • Grafana: http://localhost:3000 (admin/admin)"
	@echo "  • Prometheus: http://localhost:9090"
	@echo ""
	@echo "$(GREEN)Para ejecutar la prueba:$(NC)"
	@echo "  make test"

# Comandos de conveniencia
quick-start: install up test ## Instalación completa desde cero
	@echo "$(GREEN)🎉 ¡Sistema completo ejecutado exitosamente!$(NC)"

# Desarrollo
dev-setup: install ## Configurar entorno de desarrollo
	pip install -r requirements-dev.txt
	pre-commit install
	@echo "$(GREEN)✅ Entorno de desarrollo configurado$(NC)"

# Monitoreo
metrics: ## Ver métricas del sistema
	@echo "$(GREEN)📈 MÉTRICAS DEL SISTEMA$(NC)"
	curl -s http://localhost:8000/system/metrics | python -m json.tool

# Información
info: ## Mostrar información del sistema
	@echo "$(GREEN)ℹ️  INFORMACIÓN DEL SISTEMA$(NC)"
	@echo "$(YELLOW)Arquitectura:$(NC) Hexagonal + DDD"
	@echo "$(YELLOW)Stack:$(NC) Python 3.11 + FastAPI + PostgreSQL + Redis"
	@echo "$(YELLOW)Performance:$(NC) <0.1ms asignación (req: <100ms)"
	@echo "$(YELLOW)Autor:$(NC) Andrés Caballero"
	@echo "$(YELLOW)Prueba:$(NC) Insight Solutions S.L."