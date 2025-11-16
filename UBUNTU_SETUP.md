# VidCollector Setup Guide for Ubuntu 24.04

This guide provides detailed instructions for setting up VidCollector on Ubuntu 24.04 with UV package manager.

## Prerequisites

- Ubuntu 24.04 LTS (recommended)
- Internet connection
- sudo privileges

## Quick Setup (Recommended)

### Option 1: Automated Installation

```bash
# Clone the repository
git clone https://github.com/otoofim/VidCollector.git
cd VidCollector

# Run the automated installer
./install.sh --dev --demo

# Or for production use only
./install.sh
```

### Option 2: Using Makefile

```bash
# Clone the repository
git clone https://github.com/otoofim/VidCollector.git
cd VidCollector

# Quick setup (installs everything)
make quick-setup

# Test the installation
make run-demo
```

## Manual Setup

### Step 1: System Dependencies

Install required system packages:

```bash
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
    libssl-dev \
    make
```

### Step 2: Install UV Package Manager

UV is a fast Python package installer and resolver:

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your shell or source the profile
source ~/.bashrc

# Verify installation
uv --version
```

### Step 3: Clone and Setup Project

```bash
# Clone the repository
git clone https://github.com/otoofim/VidCollector.git
cd VidCollector

# Install project dependencies
uv sync

# For development (includes testing, linting tools)
uv sync --extra dev --extra test --extra docs
```

### Step 4: Configuration

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration (add your YouTube API key)
nano .env
```

### Step 5: Test Installation

```bash
# Run demo (no API key required)
uv run python example_usage.py

# Or using make
make run-demo

# Run tests
uv run pytest tests/ -v

# Or using make
make test
```

## YouTube API Setup

### Getting a YouTube Data API v3 Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable YouTube Data API v3:
   - Go to "APIs & Services" > "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy the generated API key
5. Add the API key to your `.env` file:
   ```env
   YOUTUBE_API_KEY=your_api_key_here
   ```

## Usage

### Basic Commands

```bash
# Initialize database
uv run python -m vidcollector db init

# Start crawling
uv run python -m vidcollector crawl --max-videos 50

# Show statistics
uv run python -m vidcollector stats

# Export data
uv run python -m vidcollector db export --format csv --output data.csv
```

### Using Make Commands

```bash
# Show all available commands
make help

# Run basic crawl
make crawl

# Show statistics
make stats

# Run tests
make test

# Format code
make format

# Run linting
make lint

# Clean build artifacts
make clean
```

## Development Setup

### Installing Development Dependencies

```bash
# Install all development dependencies
uv sync --extra dev --extra test --extra docs

# Or using make
make install-dev
```

### Code Quality Tools

```bash
# Format code with black and isort
make format

# Run linting (flake8, mypy)
make lint

# Run tests with coverage
make test

# Install pre-commit hooks
uv run pre-commit install
```

### Project Structure

```
VidCollector/
├── src/vidcollector/          # Main package
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── database.py            # Database operations
│   ├── youtube_api.py         # YouTube API integration
│   ├── subtitle_extractor.py  # Subtitle extraction
│   ├── crawler.py             # Main crawler engine
│   ├── cli.py                 # Command-line interface
│   └── __main__.py            # Package entry point
├── tests/                     # Test suite
├── .github/workflows/         # CI/CD workflows
├── pyproject.toml             # Project configuration
├── Makefile                   # Build automation
├── install.sh                 # Installation script
└── README.md                  # Documentation
```

## Troubleshooting

### Common Issues

#### UV Not Found
```bash
# Ensure UV is in PATH
export PATH="$HOME/.cargo/bin:$PATH"
source ~/.bashrc
```

#### Permission Errors
```bash
# Fix ownership if needed
sudo chown -R $USER:$USER ~/.cargo
```

#### FFmpeg Issues
```bash
# Reinstall FFmpeg
sudo apt remove ffmpeg
sudo apt install ffmpeg
```

#### Python Version Issues
```bash
# Check Python version
python3 --version

# Install specific Python version with UV
uv python install 3.12
```

### Performance Optimization

#### For Large Scale Crawling

1. **Increase concurrent downloads:**
   ```env
   MAX_CONCURRENT_DOWNLOADS=5
   ```

2. **Adjust rate limiting:**
   ```env
   RATE_LIMIT_DELAY=0.5
   ```

3. **Use SSD storage for database:**
   ```env
   DATABASE_PATH=/path/to/ssd/farsi_videos.db
   ```

4. **Monitor system resources:**
   ```bash
   # Monitor CPU and memory usage
   htop

   # Monitor disk I/O
   iotop
   ```

### Database Optimization

```bash
# Vacuum database to optimize
sqlite3 data/farsi_videos.db "VACUUM;"

# Analyze database statistics
sqlite3 data/farsi_videos.db "ANALYZE;"
```

## Security Considerations

### API Key Security

- Never commit `.env` files to version control
- Use environment variables in production
- Rotate API keys regularly
- Monitor API usage in Google Cloud Console

### System Security

```bash
# Keep system updated
sudo apt update && sudo apt upgrade

# Install security updates
sudo unattended-upgrades

# Monitor logs
sudo journalctl -f
```

## Production Deployment

### Systemd Service

Create a systemd service for continuous crawling:

```bash
# Create service file
sudo nano /etc/systemd/system/vidcollector.service
```

```ini
[Unit]
Description=VidCollector YouTube Crawler
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/VidCollector
Environment=PATH=/home/your_username/.cargo/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/home/your_username/.cargo/bin/uv run python -m vidcollector crawl --max-videos 100
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable vidcollector
sudo systemctl start vidcollector

# Check status
sudo systemctl status vidcollector
```

### Monitoring

```bash
# View logs
sudo journalctl -u vidcollector -f

# Monitor database growth
watch -n 60 'ls -lh data/farsi_videos.db'
```

## Support

For issues and questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the [GitHub Issues](https://github.com/otoofim/VidCollector/issues)
3. Create a new issue with detailed information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `make install-dev`
4. Make your changes
5. Run tests: `make test`
6. Format code: `make format`
7. Submit a pull request