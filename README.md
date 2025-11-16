# VidCollector

A powerful YouTube crawler specifically designed to collect Farsi-spoken videos along with their Farsi and English subtitles. This tool is perfect for building datasets for Text-to-Video (TTV) Farsi applications.

## Features

- 🎯 **Targeted Farsi Content**: Intelligent search for Farsi-spoken YouTube videos
- 📝 **Dual Subtitle Extraction**: Extracts both Farsi and English subtitles (manual and auto-generated)
- 🗄️ **Robust Data Storage**: SQLite database for organized storage of video metadata and subtitles
- 🚀 **Concurrent Processing**: Multi-threaded subtitle extraction for efficiency
- 📊 **Progress Monitoring**: Real-time progress tracking and comprehensive statistics
- 🔧 **Configurable**: Flexible configuration for search parameters and crawler behavior
- 🛡️ **Rate Limiting**: Built-in YouTube API rate limiting and quota management
- 📋 **CLI Interface**: Easy-to-use command-line interface

## Installation

### Prerequisites (Ubuntu 24.04)

VidCollector is optimized for Ubuntu 24.04 and uses UV as the package manager for fast, reliable dependency management.

📖 **For detailed Ubuntu 24.04 setup instructions, see [UBUNTU_SETUP.md](UBUNTU_SETUP.md)**

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/otoofim/VidCollector.git
cd VidCollector

# Quick setup (installs system deps, UV, and project deps)
make quick-setup

# Set up your YouTube API key
cp .env.example .env
# Edit .env and add your YouTube Data API v3 key
```

### Manual Setup

1. **Install system dependencies:**
```bash
make setup-ubuntu
```

2. **Install UV package manager:**
```bash
make install-uv
# Restart your shell or run: source ~/.bashrc
```

3. **Install project dependencies:**
```bash
# For regular use
make install

# For development (includes testing, linting tools)
make install-dev
```

4. **Set up configuration:**
```bash
cp .env.example .env
# Edit .env and add your YouTube Data API v3 key
```

## Quick Start

### 1. Get YouTube API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Add the API key to your `.env` file

### 2. Basic Usage

```bash
# Test the installation (no API key required)
make run-demo

# Initialize the database
uv run python -m vidcollector db init

# Start crawling (basic)
make crawl
# or manually:
uv run python -m vidcollector crawl --max-videos 50

# Crawl with custom search terms
uv run python -m vidcollector crawl --queries "فیلم ایرانی" "موسیقی ایرانی" --max-videos 100

# Crawl specific YouTube channels
uv run python -m vidcollector crawl-channels --channel-ids UC123456789 UC987654321

# Resume subtitle extraction for existing videos
uv run python -m vidcollector resume-subtitles --max-videos 20

# Show statistics
make stats
# or manually:
uv run python -m vidcollector stats --detailed
```

## Configuration

Edit the `.env` file to customize crawler behavior:

```env
# YouTube Data API v3 Key
YOUTUBE_API_KEY=your_youtube_api_key_here

# Database Configuration
DATABASE_PATH=data/farsi_videos.db

# Crawler Settings
MAX_VIDEOS_PER_SEARCH=50
RATE_LIMIT_DELAY=1.0
MAX_CONCURRENT_DOWNLOADS=3

# Search Configuration
FARSI_KEYWORDS=فارسی,پارسی,ایرانی,تهران,اصفهان,شیراز,مشهد
MAX_VIDEO_DURATION=3600
MIN_VIDEO_DURATION=60
```

## Project Structure

```
VidCollector/
├── src/vidcollector/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── database.py        # Database operations
│   ├── youtube_api.py     # YouTube API integration
│   ├── subtitle_extractor.py  # Subtitle extraction
│   ├── crawler.py         # Main crawler engine
│   ├── cli.py            # Command-line interface
│   └── __main__.py       # Module entry point
├── tests/
│   └── test_basic.py     # Unit tests
├── data/                 # Database storage
├── logs/                 # Log files
├── subtitles/           # Downloaded subtitle files
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── main.py             # Main entry point
└── README.md
```

## Database Schema

### Videos Table
- `video_id`: YouTube video ID
- `title`: Video title
- `description`: Video description
- `channel_id`: Channel ID
- `channel_title`: Channel name
- `duration`: Video duration in seconds
- `view_count`: Number of views
- `like_count`: Number of likes
- `published_at`: Publication date
- `language`: Detected language
- `tags`: Video tags (JSON)
- `thumbnail_url`: Thumbnail URL

### Subtitles Table
- `video_id`: Associated video ID
- `language`: Subtitle language (fa/en)
- `subtitle_type`: Type (manual/auto/detected)
- `content`: Full subtitle text
- `file_path`: Path to subtitle file

## Advanced Usage

### Custom Search Strategies

The crawler uses multiple strategies to find Farsi content:

1. **Direct Farsi Keywords**: Uses predefined Farsi terms
2. **Geographic Targeting**: Searches for Iranian cities and regions
3. **Content Categories**: Targets specific content types (films, music, news)
4. **Channel Whitelisting**: Focus on specific trusted channels

### Subtitle Extraction Features

- **Manual Subtitles**: Extracts human-created subtitles when available
- **Auto-Generated**: Falls back to YouTube's automatic captions
- **Language Detection**: Identifies Farsi content in mixed-language subtitles
- **Text Cleaning**: Removes HTML tags, timestamps, and artifacts
- **Character Detection**: Uses Unicode ranges to identify Farsi text

### Data Export

```bash
# Export all data as JSON
python main.py db export --format json --output data_export.json

# Export only videos as CSV
python main.py db export --format csv --table videos --output videos_export.csv
```

## API Usage

You can also use VidCollector programmatically:

```python
from vidcollector.crawler import FarsiVideoCrawler
from vidcollector.config import Config

# Initialize crawler
crawler = FarsiVideoCrawler()

# Crawl videos
stats = crawler.crawl_farsi_videos(
    max_videos=100,
    search_queries=["فیلم ایرانی", "موسیقی سنتی"],
    extract_subtitles=True
)

print(f"Found {stats['videos_found']} videos")
print(f"Extracted {stats['subtitles_extracted']} subtitles")
```

## Development

### Testing

Run the test suite with UV:

```bash
# Run all tests
make test

# Or manually with UV
uv run pytest tests/ -v --cov=src/vidcollector

# Run specific tests
uv run python -m unittest tests.test_basic.TestDatabase
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Clean build artifacts
make clean
```

### Available Make Commands

```bash
make help              # Show all available commands
make setup-ubuntu      # Install Ubuntu 24.04 system dependencies
make install-uv        # Install UV package manager
make install           # Install project dependencies
make install-dev       # Install with development dependencies
make test             # Run tests with coverage
make lint             # Run linting (flake8, mypy)
make format           # Format code (black, isort)
make run-demo         # Run demo without API key
make crawl            # Run basic crawl (requires API key)
make stats            # Show database statistics
make clean            # Clean build artifacts
```

## Troubleshooting

### Common Issues

1. **YouTube API Quota Exceeded**
   - Wait for quota reset (daily)
   - Use multiple API keys with rotation
   - Reduce `MAX_VIDEOS_PER_SEARCH`

2. **No Subtitles Found**
   - Many videos don't have subtitles
   - Try different search queries
   - Use `resume-subtitles` command for retry

3. **Rate Limiting**
   - Increase `RATE_LIMIT_DELAY` in config
   - Reduce `MAX_CONCURRENT_DOWNLOADS`

### Logging

Check logs for detailed information:

```bash
tail -f logs/vidcollector.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes. Please respect YouTube's Terms of Service and API usage policies. Ensure you have proper rights to use any downloaded content.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details