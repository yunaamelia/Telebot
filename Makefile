# Makefile for Telegram Cash Flow Bot
# Common development commands

.PHONY: help install install-dev install-hooks test coverage lint format clean run migrate build deploy preflight

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt

install-hooks: install-dev ## Install pre-commit hooks
	pre-commit install --install-hooks
	pre-commit install --hook-type pre-commit
	pre-commit install --hook-type pre-push
	pre-commit install --hook-type commit-msg
	@echo "✅ Git hooks installed"

test: ## Run test suite
	pytest tests/ -v

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

coverage: ## Run tests with coverage report
	pytest --cov=src --cov-report=html --cov-report=term-missing

coverage-ci: ## Run coverage for CI (fail if < 80%)
	pytest --cov=src --cov-report=term-missing --cov-fail-under=80

lint: ## Run all linters
	@echo "Running flake8..."
	flake8 src/ tests/
	@echo "Running bandit..."
	bandit -r src/ -c .bandit.yml
	@echo "Running mypy..."
	mypy src/ --ignore-missing-imports
	@echo "✅ All linting passed"

format: ## Format code with black and isort
	black src/ tests/
	isort src/ tests/
	@echo "✅ Code formatted"

format-check: ## Check if code is formatted
	black --check src/ tests/
	isort --check-only src/ tests/

security: ## Run security checks
	bandit -r src/ -c .bandit.yml
	detect-secrets scan --baseline .secrets.baseline
	safety check

clean: ## Clean up cache and temporary files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

run: ## Run the bot locally
	python -m src.main

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create a new migration
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

migrate-downgrade: ## Downgrade one migration
	alembic downgrade -1

build: ## Build Docker image
	./scripts/pre-build.sh
	docker build -t cashflow-bot:latest .

build-no-cache: ## Build Docker image without cache
	docker build --no-cache -t cashflow-bot:latest .

docker-up: ## Start Docker Compose services
	docker-compose up -d

docker-down: ## Stop Docker Compose services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f bot

preflight: ## Run pre-deployment checks
	./scripts/preflight.sh

deploy: preflight ## Deploy to production (after preflight checks)
	@echo "🚀 Deploying to production..."
	@echo "This is a placeholder - implement your deployment strategy"

pre-commit-all: ## Run all pre-commit hooks
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	pre-commit autoupdate

init-db: ## Initialize database with schema
	docker-compose up -d db
	sleep 3
	alembic upgrade head
	@echo "✅ Database initialized"

setup: install-dev install-hooks init-db ## Complete project setup
	@echo ""
	@echo "✅ Project setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Copy .env.example to .env and configure"
	@echo "  2. Run 'make test' to verify installation"
	@echo "  3. Run 'make run' to start the bot"

venv: ## Create virtual environment
	python3 -m venv venv
	@echo "✅ Virtual environment created"
	@echo "Activate with: source venv/bin/activate"

.DEFAULT_GOAL := help
