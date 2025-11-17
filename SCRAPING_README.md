# VidCollector - Web Scraping Approach

This document describes the web scraping version of VidCollector that collects Farsi YouTube videos and subtitles without using the YouTube API.

## 🌟 Features

- **Web Scraping**: Direct scraping of YouTube pages using Selenium and BeautifulSoup
- **Farsi Detection**: Advanced Persian/Farsi text detection in video titles and descriptions
- **Related Video Discovery**: Automatically finds related Farsi videos from current page
- **External Downloads**: Uses ytdown.to for video downloads and downsub.com for subtitles
- **Mapping Files**: Creates text files mapping videos, subtitles, and URLs
- **Database Storage**: Stores metadata and subtitle content in SQLite database

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### 2. Install Chrome Browser

The scraper requires Chrome/Chromium browser:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y chromium-browser

# Or install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable
```

### 3. Run Demo

```bash
# Run the scraping demo (no actual scraping)
make run-scraping-demo

# Or directly
uv run python scraping_example.py
```

### 4. Start Scraping

```bash
# Scrape from a YouTube video URL
make scrape URL='https://www.youtube.com/watch?v=VIDEO_ID' MAX_VIDEOS=20

# Or use the CLI directly
uv run python -m vidcollector.scraping_cli crawl --start-url "https://www.youtube.com/watch?v=VIDEO_ID" --max-videos 20
```

## 📋 Usage Examples

### Basic Scraping

```bash
# Scrape 10 videos starting from a Farsi video
uv run python -m vidcollector.scraping_cli crawl \
    --start-url "https://www.youtube.com/watch?v=FARSI_VIDEO_ID" \
    --max-videos 10
```

### Metadata Only (No Downloads)

```bash
# Collect metadata without downloading videos/subtitles
uv run python -m vidcollector.scraping_cli crawl \
    --start-url "https://www.youtube.com/watch?v=VIDEO_ID" \
    --no-download \
    --max-videos 20
```

### Multiple Starting URLs

```bash
# Scrape from multiple starting points
uv run python -m vidcollector.scraping_cli crawl \
    --start-url "URL1,URL2,URL3" \
    --multiple-urls \
    --max-videos 30
```

### View Statistics

```bash
# Show database statistics
uv run python -m vidcollector.scraping_cli stats --downloads

# Show video-subtitle mappings
uv run python -m vidcollector.scraping_cli mapping --output mappings.txt
```

### Export Data

```bash
# Export to CSV
uv run python -m vidcollector.scraping_cli export --output data.csv --format csv

# Export to JSON
uv run python -m vidcollector.scraping_cli export --output data.json --format json
```

## 🏗️ Architecture

### Components

1. **YouTubeScraper**: Scrapes YouTube pages for video metadata and related videos
2. **FarsiDetector**: Detects Persian/Farsi text using Unicode ranges and langdetect
3. **YTDownService**: Interfaces with ytdown.to for video downloads
4. **DownSubService**: Interfaces with downsub.com for subtitle downloads
5. **DownloadManager**: Manages downloads and creates mapping files
6. **FarsiVideoCrawler**: Main crawler that orchestrates the entire process

### Workflow

```
Start URL → Scrape Page → Extract Metadata → Detect Farsi Content
    ↓
Find Related Videos → Filter Farsi Videos → Store in Database
    ↓
Download Video (ytdown.to) → Download Subtitles (downsub.com)
    ↓
Update Mapping File → Continue with Related Videos
```

### File Structure

```
downloads/
├── videos/                    # Downloaded video files
│   ├── VIDEO_ID_720p.mp4
│   └── ...
├── subtitles/                 # Downloaded subtitle files
│   ├── VIDEO_ID_fa.srt       # Farsi subtitles
│   ├── VIDEO_ID_en.srt       # English subtitles
│   └── ...
└── video_subtitle_mapping.txt # URL to file mappings
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file (optional):

```bash
# Database configuration
DATABASE_PATH=farsi_videos.db

# Scraping configuration
RATE_LIMIT_DELAY=2.0
MAX_VIDEOS_PER_SEARCH=50

# Download directories
VIDEO_DOWNLOAD_DIR=downloads/videos
SUBTITLE_DOWNLOAD_DIR=downloads/subtitles

# Browser configuration
HEADLESS_BROWSER=true
```

### Farsi Detection Settings

The Farsi detector uses:
- Unicode ranges for Persian characters (U+0600-U+06FF, etc.)
- Language detection with langdetect library
- Configurable minimum Farsi character ratio (default: 10%)

## 📊 Output Files

### Mapping File Format

The `video_subtitle_mapping.txt` file contains:

```
URL | Video File | Farsi Subtitle | English Subtitle
https://www.youtube.com/watch?v=VIDEO_ID1 | downloads/videos/VIDEO_ID1_720p.mp4 | downloads/subtitles/VIDEO_ID1_fa.srt | downloads/subtitles/VIDEO_ID1_en.srt
https://www.youtube.com/watch?v=VIDEO_ID2 | downloads/videos/VIDEO_ID2_720p.mp4 | downloads/subtitles/VIDEO_ID2_fa.srt | N/A
```

### Database Schema

Videos and subtitles are stored in SQLite database:

```sql
-- Videos table
CREATE TABLE videos (
    video_id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    channel_title TEXT,
    language TEXT,
    farsi_score REAL,
    url TEXT,
    created_at TIMESTAMP
);

-- Subtitles table
CREATE TABLE subtitles (
    id INTEGER PRIMARY KEY,
    video_id TEXT,
    language TEXT,
    content TEXT,
    format TEXT,
    source TEXT,
    file_path TEXT,
    FOREIGN KEY (video_id) REFERENCES videos (video_id)
);
```

## 🛠️ Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage
```

### Code Quality

```bash
# Lint code
make lint

# Format code
make format
```

### Adding New Download Services

To add support for new download services:

1. Create a new service class in `download_services.py`
2. Implement `get_download_links()` and `download_video()` methods
3. Update `DownloadManager` to use the new service
4. Add configuration options as needed

## 🚨 Important Notes

### Rate Limiting

- Default delay between requests: 2 seconds
- Respects robots.txt and website terms of service
- Uses rotating user agents to avoid detection

### Legal Considerations

- Only scrapes publicly available information
- Respects website terms of service
- Downloads are for personal/research use only
- Users are responsible for compliance with local laws

### Browser Requirements

- Requires Chrome/Chromium browser
- Uses webdriver-manager for automatic driver management
- Supports headless mode for server environments

## 🔍 Troubleshooting

### Common Issues

1. **Chrome driver not found**
   ```bash
   # Install Chrome browser first, then run:
   uv run python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
   ```

2. **Download services not working**
   - External services (ytdown.to, downsub.com) may change their interfaces
   - Check service availability and update scraping logic if needed

3. **Farsi detection issues**
   - Adjust `min_farsi_ratio` parameter in FarsiDetector
   - Check Unicode ranges for Persian characters

4. **Memory issues with large crawls**
   - Reduce `max_videos` parameter
   - Use `--no-download` for metadata-only collection

### Debug Mode

```bash
# Run with debug logging
uv run python -m vidcollector.scraping_cli crawl \
    --start-url "URL" \
    --log-level DEBUG
```

## 📈 Performance Tips

1. **Optimize for Speed**
   - Use headless browser mode
   - Adjust rate limiting based on your needs
   - Process videos in batches

2. **Reduce Resource Usage**
   - Use `--no-download` for metadata collection
   - Limit concurrent operations
   - Clean up temporary files regularly

3. **Improve Accuracy**
   - Start with high-quality Farsi content URLs
   - Adjust Farsi detection thresholds
   - Manually verify results for important datasets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes. Users are responsible for:
- Complying with YouTube's Terms of Service
- Respecting copyright and intellectual property rights
- Following local laws and regulations
- Using downloaded content appropriately

The developers are not responsible for any misuse of this tool.