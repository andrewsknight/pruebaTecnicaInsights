.PHONY: up down test clean logs status

up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 15
	@echo "✅ All services are up!"

down:
	docker-compose down -v --remove-orphans

test: up
	@echo "🔬 Running full test suite..."
	python src/main.py test

clean: down
	docker system prune -f
	docker volume prune -f

logs:
	docker-compose logs -f

status:
	docker-compose ps
	@echo "\n📊 Service Health:"
	@curl -s http://localhost:8000/health || echo "API not ready"