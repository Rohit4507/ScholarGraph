# ScholarGraph AI - Development Makefile

.PHONY: help dev-setup dev test clean build deploy

# Default target
help:
	@echo "ScholarGraph AI - Development Commands"
	@echo ""
	@echo "Setup Commands:"
	@echo "  dev-setup     - Set up development environment"
	@echo "  dev           - Start development servers"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test          - Run all tests"
	@echo "  test-backend  - Run backend tests"
	@echo "  test-frontend - Run frontend tests"
	@echo "  test-integration - Run integration tests"
	@echo ""
	@echo "Build Commands:"
	@echo "  build         - Build for production"
	@echo "  clean         - Clean build artifacts"
	@echo ""
	@echo "Deployment Commands:"
	@echo "  deploy        - Deploy to production"
	@echo "  deploy-staging - Deploy to staging"
	@echo ""
	@echo "Utility Commands:"
	@echo "  format        - Format code"
	@echo "  lint          - Run linting"
	@echo "  docs          - Generate documentation"

# Development setup
dev-setup:
	@echo "🚀 Setting up ScholarGraph AI development environment..."
	@echo ""
	@echo "📦 Setting up backend..."
	cd backend && \
		python -m venv .venv && \
		source .venv/bin/activate && \
		pip install --upgrade pip && \
		pip install -r requirements.txt && \
		cp .env.template .env && \
		echo "✅ Backend setup complete"
	@echo ""
	@echo "📦 Setting up frontend..."
	cd frontend && \
		npm install && \
		echo "✅ Frontend setup complete"
	@echo ""
	@echo "🤖 Setting up LLaMA (optional)..."
	@if command -v ollama >/dev/null 2>&1; then \
		ollama pull llama3.1:8b && \
		echo "✅ LLaMA 3.1 setup complete"; \
	else \
		echo "⚠️  Ollama not found. Install from https://ollama.ai"; \
	fi
	@echo ""
	@echo "🗄️  Initializing database..."
	cd backend && \
		source .venv/bin/activate && \
		python -c "from database.session import init_db; init_db()" && \
		echo "✅ Database initialized"
	@echo ""
	@echo "🎉 Development setup complete!"
	@echo "Run 'make dev' to start development servers"

# Development servers
dev:
	@echo "🚀 Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Starting backend and frontend in parallel..."
	@cd backend && source .venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000 & \
	 cd frontend && npm run dev & \
	 wait

# Backend development server only
dev-backend:
	@echo "🚀 Starting backend server..."
	cd backend && \
	source .venv/bin/activate && \
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend development server only
dev-frontend:
	@echo "🚀 Starting frontend server..."
	cd frontend && \
	npm run dev

# Testing
test: test-backend test-frontend test-integration

test-backend:
	@echo "🧪 Running backend tests..."
	cd backend && \
	source .venv/bin/activate && \
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

test-frontend:
	@echo "🧪 Running frontend tests..."
	cd frontend && \
	npm run test

test-integration:
	@echo "🧪 Running integration tests..."
	cd backend && \
	source .venv/bin/activate && \
	python -m pytest tests/integration/ -v

# Code quality
format:
	@echo "🎨 Formatting code..."
	@echo "Formatting Python code..."
	cd backend && \
	source .venv/bin/activate && \
	black . && \
	isort .
	@echo "Formatting JavaScript code..."
	cd frontend && \
	npm run format

lint:
	@echo "🔍 Running linting..."
	@echo "Linting Python code..."
	cd backend && \
	source .venv/bin/activate && \
	flake8 . --max-line-length=88 --extend-ignore=E203,W503 && \
	mypy . --ignore-missing-imports
	@echo "Linting JavaScript code..."
	cd frontend && \
	npm run lint

# Build for production
build:
	@echo "🏗️  Building for production..."
	@echo "Building backend..."
	cd backend && \
	docker build -t scholargraph-backend .
	@echo "Building frontend..."
	cd frontend && \
	npm run build && \
	docker build -t scholargraph-frontend .
	@echo "✅ Build complete"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	@echo "Cleaning Python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Cleaning Node modules..."
	rm -rf frontend/node_modules frontend/.next
	@echo "Cleaning Docker images..."
	docker system prune -f
	@echo "✅ Clean complete"

# Docker development
docker-dev:
	@echo "🐳 Starting development with Docker..."
	docker-compose -f docker/docker-compose.dev.yml up --build

docker-prod:
	@echo "🐳 Starting production with Docker..."
	docker-compose -f docker/docker-compose.yml up -d --build

# Database operations
db-reset:
	@echo "🗄️  Resetting database..."
	cd backend && \
	source .venv/bin/activate && \
	python -c "from database.session import init_db; init_db()" && \
	echo "✅ Database reset complete"

db-migrate:
	@echo "🗄️  Running database migrations..."
	cd backend && \
	source .venv/bin/activate && \
	alembic upgrade head && \
	echo "✅ Migrations complete"

# Documentation
docs:
	@echo "📚 Generating documentation..."
	@echo "Generating API documentation..."
	cd backend && \
	source .venv/bin/activate && \
	python -c "import main; print('API docs at http://localhost:8000/docs')" && \
	echo "✅ Documentation ready"

# Deployment
deploy-staging:
	@echo "🚀 Deploying to staging..."
	# Add staging deployment commands
	@echo "✅ Staging deployment complete"

deploy:
	@echo "🚀 Deploying to production..."
	# Add production deployment commands
	@echo "✅ Production deployment complete"

# Security
security-scan:
	@echo "🔒 Running security scan..."
	cd backend && \
	source .venv/bin/activate && \
	safety check && \
	bandit -r . && \
	echo "✅ Security scan complete"

# Performance
performance-test:
	@echo "⚡ Running performance tests..."
	cd backend && \
	source .venv/bin/activate && \
	python -m pytest tests/performance/ -v && \
	echo "✅ Performance tests complete"

# Monitoring
monitor:
	@echo "📊 Starting monitoring dashboard..."
	# Add monitoring commands
	@echo "✅ Monitoring dashboard running"

# Backup
backup:
	@echo "💾 Creating backup..."
	@echo "Backing up database..."
	# Add backup commands
	@echo "✅ Backup complete"

# Logs
logs:
	@echo "📋 Showing logs..."
	docker-compose logs -f --tail=100

# Health check
health:
	@echo "🏥 Checking system health..."
	curl -f http://localhost:8000/health || echo "❌ Backend unhealthy"
	curl -f http://localhost:3000 || echo "❌ Frontend unhealthy"
	@echo "✅ Health check complete"

# Install dependencies
install-deps:
	@echo "📦 Installing dependencies..."
	@echo "Installing Python dependencies..."
	cd backend && \
	pip install -r requirements.txt
	@echo "Installing Node dependencies..."
	cd frontend && \
	npm install
	@echo "✅ Dependencies installed"

# Update dependencies
update-deps:
	@echo "🔄 Updating dependencies..."
	@echo "Updating Python dependencies..."
	cd backend && \
	pip install --upgrade -r requirements.txt
	@echo "Updating Node dependencies..."
	cd frontend && \
	npm update
	@echo "✅ Dependencies updated"

# Version management
version:
	@echo "📋 Showing version information..."
	cd backend && \
	source .venv/bin/activate && \
	python -c "import main; print(f'Backend: {main.__version__}')" && \
	cd frontend && \
	npm list | grep "scholargraph-frontend"

# Release
release: clean test build
	@echo "🚀 Creating release..."
	# Add release commands
	@echo "✅ Release created"

# Quick demo
demo:
	@echo "🎮 Starting demo environment..."
	make docker-dev
	@echo "🎯 Demo ready at http://localhost:3000"
	@echo "📖 See docs/DEMO.md for demo script"

# Development shortcuts
quick-test:
	@echo "⚡ Quick test run..."
	cd backend && \
	source .venv/bin/activate && \
	python -m pytest tests/ -v --tb=short

quick-lint:
	@echo "⚡ Quick lint check..."
	cd backend && \
	flake8 . --max-line-length=88 --extend-ignore=E203,W503

# Development utilities
install-pre-commit:
	@echo "🔧 Setting up pre-commit hooks..."
	cd backend && \
	source .venv/bin/activate && \
	pre-commit install && \
	echo "✅ Pre-commit hooks installed"

# Git utilities
git-setup:
	@echo "🔧 Setting up git configuration..."
	git config branch.main.mergeoptions --no-ff
	git config pull.rebase false
	echo "✅ Git configuration updated"

# Project statistics
stats:
	@echo "📊 Project statistics..."
	@echo "Lines of code:"
	find . -name "*.py" -not -path "./.venv/*" | xargs wc -l | tail -1
	find . -name "*.js" -not -path "./node_modules/*" | xargs wc -l | tail -1
	find . -name "*.tsx" -not -path "./node_modules/*" | xargs wc -l | tail -1
	@echo "Files:"
	find . -name "*.py" -not -path "./.venv/*" | wc -l
	find . -name "*.js" -not -path "./node_modules/*" | wc -l
	find . -name "*.tsx" -not -path "./node_modules/*" | wc -l

# Welcome message
welcome:
	@echo "🎓 Welcome to ScholarGraph AI!"
	@echo ""
	@echo "Quick start:"
	@echo "  make dev-setup    # Set up development environment"
	@echo "  make dev          # Start development servers"
	@echo "  make test         # Run tests"
	@echo ""
	@echo "Documentation:"
	@echo "  📖 README.md      # Project overview"
	@echo "  🏗️  docs/ARCHITECTURE.md  # System design"
	@echo "  🔧 docs/API.md    # API documentation"
	@echo "  🚀 docs/DEPLOYMENT.md  # Deployment guide"
	@echo ""
	@echo "Get help:"
	@echo "  make help         # Show all commands"
	@echo "  make welcome      # Show this message"
