# VidCollector Makefile for Ubuntu 24.04 with UV

.PHONY: help install install-dev install-uv test lint format clean run-demo setup-ubuntu

# Default target
help:
	@echo "VidCollector - YouTube Farsi Video Crawler"
	@echo "Available targets:"
	@echo "  setup-ubuntu    - Install system dependencies on Ubuntu 24.04"
	@echo "  install-uv      - Install UV package manager"
	@echo "  install         - Install project dependencies with UV"
	@echo "  install-dev     - Install project with development dependencies"
	@echo "  test           - Run tests"
	@echo "  lint           - Run linting (flake8, mypy)"
	@echo "  format         - Format code (black, isort)"
	@echo "  clean          - Clean build artifacts"
	@echo "  run-demo       - Run the demo without API key"
	@echo "  crawl          - Run basic crawl (requires API key)"

# Install system dependencies for Ubuntu 24.04
setup-ubuntu:
	@echo "🔧 Setting up system dependencies for Ubuntu 24.04..."
	sudo apt update
	sudo apt install -y \
		python3 \
		python3-pip \
		python3-venv \
		python3-dev \
		build-essential \
		curl \
		wget \
		git \
		ffmpeg \
		sqlite3 \
		libsqlite3-dev \
		libxml2-dev \
		libxslt1-dev \
		zlib1g-dev \
		libjpeg-dev \
		libpng-dev \
		libffi-dev \
		libssl-dev
	@echo "✅ System dependencies installed"

# Install UV package manager
install-uv:
	@echo "📦 Installing UV package manager..."
	@if ! command -v uv >/dev/null 2>&1; then \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "✅ UV installed successfully"; \
		echo "🔄 Please restart your shell or run: source ~/.bashrc"; \
	else \
		echo "✅ UV is already installed"; \
		uv --version; \
	fi

# Install project dependencies
install:
	@echo "📦 Installing VidCollector dependencies with UV..."
	uv sync
	@echo "✅ Dependencies installed"

# Install with development dependencies
install-dev:
	@echo "📦 Installing VidCollector with development dependencies..."
	uv sync --extra dev --extra test --extra docs
	@echo "✅ Development environment ready"

# Run tests
test:
	@echo "🧪 Running tests..."
	uv run pytest tests/ -v --cov=src/vidcollector --cov-report=term-missing
	@echo "✅ Tests completed"

# Run linting
lint:
	@echo "🔍 Running linting..."
	uv run flake8 src/ tests/
	uv run mypy src/vidcollector/
	@echo "✅ Linting completed"

# Format code
format:
	@echo "🎨 Formatting code..."
	uv run black src/ tests/ *.py
	uv run isort src/ tests/ *.py
	@echo "✅ Code formatted"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -f *.db
	@echo "✅ Cleanup completed"

# Run demo
run-demo:
	@echo "🚀 Running VidCollector demo..."
	uv run python example_usage.py

# Run web scraping demo
run-scraping-demo:
	@echo "🚀 Running VidCollector web scraping demo..."
	uv run python scraping_example.py

# Run basic crawl (requires API key)
crawl:
	@echo "🚀 Running basic crawl..."
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found. Please copy .env.example to .env and add your YouTube API key"; \
		exit 1; \
	fi
	uv run python -m vidcollector crawl --max-videos 5

# Run web scraping crawl (requires YouTube URL)
scrape:
	@echo "🚀 Running web scraping crawl..."
	@echo "Usage: make scrape URL='https://www.youtube.com/watch?v=VIDEO_ID' MAX_VIDEOS=20"
	@if [ -z "$(URL)" ]; then echo "❌ Error: URL parameter is required"; exit 1; fi
	uv run python -m vidcollector.scraping_cli crawl --start-url "$(URL)" --max-videos $(or $(MAX_VIDEOS),10)

# Run scraping without downloading content
scrape-no-download:
	@echo "🚀 Running scraping without downloads..."
	@echo "Usage: make scrape-no-download URL='https://www.youtube.com/watch?v=VIDEO_ID'"
	@if [ -z "$(URL)" ]; then echo "❌ Error: URL parameter is required"; exit 1; fi
	uv run python -m vidcollector.scraping_cli crawl --start-url "$(URL)" --no-download --max-videos $(or $(MAX_VIDEOS),10)

# Initialize database
init-db:
	@echo "🗄️ Initializing database..."
	uv run python -m vidcollector db init

# Show statistics
stats:
	@echo "📊 Showing statistics..."
	uv run python -m vidcollector stats --detailed

# Show scraping statistics
scraping-stats:
	@echo "📊 Showing scraping statistics..."
	uv run python -m vidcollector.scraping_cli stats --downloads

# Show video-subtitle mappings
mapping:
	@echo "📁 Showing video-subtitle mappings..."
	uv run python -m vidcollector.scraping_cli mapping

# Development server (if needed)
dev:
	@echo "🔧 Starting development environment..."
	@echo "Use 'make run-demo' to test functionality"
	@echo "Use 'make crawl' to run actual crawling (requires API key)"

# Quick setup for new users
quick-setup: setup-ubuntu install-uv install-dev
	@echo "🎉 Quick setup completed!"
	@echo "Next steps:"
	@echo "1. Copy .env.example to .env"
	@echo "2. Add your YouTube API key to .env"
	@echo "3. Run 'make run-demo' to test"
	@echo "4. Run 'make crawl' to start crawling"