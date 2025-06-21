.PHONY: clean install test format lint docker dev help

help:
	@echo "Identity Circuit Factory - Development Commands"
	@echo "=============================================="
	@echo "clean      - Clean all generated files"
	@echo "install    - Clean install in development mode"
	@echo "test       - Run tests"
	@echo "format     - Format code with black"
	@echo "lint       - Lint code with flake8"
	@echo "docker     - Build and test Docker image"
	@echo "dev        - Start development server"
	@echo "deploy     - Deploy to production"

clean:
	@echo "🧹 Cleaning up..."
	rm -rf .venv __pycache__ *.egg-info
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

install: clean
	@echo "📦 Installing project..."
	chmod +x scripts/clean_install.sh
	./scripts/clean_install.sh

test:
	@echo "🧪 Running tests..."
	.venv/bin/pytest tests/ -v

format:
	@echo "🎨 Formatting code..."
	.venv/bin/black identity_factory/ sat_revsynth/ tests/
	.venv/bin/black *.py

lint:
	@echo "🔍 Linting code..."
	.venv/bin/flake8 identity_factory/ sat_revsynth/

docker:
	@echo "🐳 Building Docker image..."
	docker build -t identity-factory .
	@echo "🚀 Testing Docker image..."
	docker run --rm -p 8000:8000 -d --name identity-factory-test identity-factory
	sleep 5
	curl -f http://localhost:8000/health && echo "✅ Docker test passed"
	docker stop identity-factory-test

dev:
	@echo "🚀 Starting development server..."
	.venv/bin/python start_api.py --reload --debug --host 0.0.0.0 --port 8000

deploy:
	@echo "🚀 Preparing for deployment..."
	make test
	make docker
	@echo "✅ Ready for deployment!"
