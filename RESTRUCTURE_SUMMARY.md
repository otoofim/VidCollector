# VidCollector Restructure Summary

## 🎯 Project Transformation

VidCollector has been successfully restructured from a YouTube API-based approach to a comprehensive web scraping pipeline for collecting Farsi YouTube videos and subtitles.

## 🔄 Key Changes

### 1. Dependencies Migration
**Before**: YouTube Data API v3 dependencies
```toml
"google-api-python-client>=2.100.0"
"google-auth-httplib2>=0.1.0" 
"google-auth-oauthlib>=1.0.0"
"yt-dlp>=2023.10.0"
```

**After**: Web scraping and automation dependencies
```toml
"requests>=2.31.0"
"beautifulsoup4>=4.12.0"
"selenium>=4.15.0"
"langdetect>=1.0.9"
"fake-useragent>=1.4.0"
"webdriver-manager>=4.0.0"
```

### 2. New Core Components

#### 🕷️ YouTube Scraper (`youtube_scraper.py`)
- **FarsiDetector**: Advanced Persian text detection using Unicode ranges and langdetect
- **YouTubeScraper**: Selenium-based scraper for YouTube pages
- Features:
  - Video metadata extraction (title, description, channel)
  - Related video discovery from sidebar
  - Farsi content detection and scoring
  - Headless browser support with anti-detection measures

#### 📥 Download Services (`download_services.py`)
- **YTDownService**: Integration with ytdown.to for video downloads
- **DownSubService**: Integration with downsub.com for subtitle downloads
- **DownloadManager**: Orchestrates downloads and creates mapping files
- Features:
  - Multiple quality options for videos
  - Farsi and English subtitle extraction
  - Automatic mapping file generation
  - Error handling and retry logic

#### 🚀 Scraping Crawler (`scraping_crawler.py`)
- **FarsiVideoCrawler**: Main crawler orchestrating the entire pipeline
- Features:
  - Single URL or multiple URL crawling
  - Configurable video limits per URL
  - Optional content downloading
  - Database integration for metadata storage
  - Progress tracking with tqdm

#### 💻 CLI Interface (`scraping_cli.py`)
- Comprehensive command-line interface
- Commands:
  - `crawl`: Start scraping from YouTube URLs
  - `stats`: Show database and download statistics
  - `export`: Export collected data to CSV/JSON
  - `mapping`: Display video-subtitle mappings

### 3. Enhanced Database Schema

Extended the existing database with new fields:
- `farsi_score`: Quantitative measure of Farsi content
- `file_path`: Local paths to downloaded subtitle files
- `source`: Track subtitle source (downsub.com, etc.)

### 4. Configuration Updates

Added new configuration options:
```python
# Web Scraping Configuration
HEADLESS_BROWSER: bool = True
VIDEO_DOWNLOAD_DIR: str = 'downloads/videos'
SUBTITLE_DOWNLOAD_DIR: str = 'downloads/subtitles'
```

## 🎯 New Workflow

### Traditional API Approach (Old)
```
YouTube API → Search Videos → Extract Metadata → yt-dlp Download
```

### Web Scraping Approach (New)
```
Start URL → Scrape Page → Extract Metadata → Detect Farsi Content
    ↓
Find Related Videos → Filter Farsi Videos → Store in Database
    ↓
Download Video (ytdown.to) → Download Subtitles (downsub.com)
    ↓
Update Mapping File → Continue with Related Videos
```

## 📁 File Structure

### New Files Added
```
src/vidcollector/
├── youtube_scraper.py      # YouTube page scraping
├── download_services.py    # External download services
├── scraping_crawler.py     # Main scraping crawler
└── scraping_cli.py         # Command-line interface

scraping_example.py         # Demo script
SCRAPING_README.md         # Comprehensive documentation
RESTRUCTURE_SUMMARY.md     # This summary
```

### Updated Files
```
pyproject.toml             # Updated dependencies
Makefile                   # Added scraping commands
src/vidcollector/config.py # Added scraping configuration
src/vidcollector/database.py # Added VideoDatabase class
```

## 🚀 Usage Examples

### Quick Start
```bash
# Run demo (no actual scraping)
make run-scraping-demo

# Scrape from a YouTube video
make scrape URL='https://www.youtube.com/watch?v=VIDEO_ID' MAX_VIDEOS=20

# Metadata only (no downloads)
make scrape-no-download URL='https://www.youtube.com/watch?v=VIDEO_ID'
```

### CLI Usage
```bash
# Basic crawling
uv run python -m vidcollector.scraping_cli crawl \
    --start-url "https://www.youtube.com/watch?v=VIDEO_ID" \
    --max-videos 10

# Multiple URLs
uv run python -m vidcollector.scraping_cli crawl \
    --start-url "URL1,URL2,URL3" \
    --multiple-urls \
    --max-videos 30

# Show statistics
uv run python -m vidcollector.scraping_cli stats --downloads

# Export data
uv run python -m vidcollector.scraping_cli export \
    --output data.csv --format csv
```

## 📊 Output Files

### 1. Video-Subtitle Mapping File
Location: `downloads/video_subtitle_mapping.txt`
Format:
```
URL | Video File | Farsi Subtitle | English Subtitle
https://www.youtube.com/watch?v=VIDEO_ID | downloads/videos/VIDEO_ID_720p.mp4 | downloads/subtitles/VIDEO_ID_fa.srt | downloads/subtitles/VIDEO_ID_en.srt
```

### 2. Downloaded Content
```
downloads/
├── videos/
│   ├── VIDEO_ID1_720p.mp4
│   └── VIDEO_ID2_480p.mp4
└── subtitles/
    ├── VIDEO_ID1_fa.srt
    ├── VIDEO_ID1_en.srt
    └── VIDEO_ID2_fa.srt
```

### 3. Database Storage
- Video metadata with Farsi scoring
- Subtitle content and file paths
- Source tracking and timestamps

## 🔍 Key Features

### 1. Advanced Farsi Detection
- Unicode range analysis for Persian characters
- Language detection with langdetect
- Configurable Farsi content thresholds
- Quantitative scoring (0.0 - 1.0)

### 2. Related Video Discovery
- Automatic sidebar scraping
- Farsi content filtering
- Recursive video discovery
- Duplicate prevention

### 3. External Service Integration
- ytdown.to for video downloads
- downsub.com for subtitle extraction
- Quality selection and format preferences
- Robust error handling

### 4. Anti-Detection Measures
- Rotating user agents
- Configurable delays
- Headless browser support
- Request session management

## 🛠️ Technical Improvements

### 1. Scalability
- Configurable rate limiting
- Memory-efficient processing
- Batch operations support
- Progress tracking

### 2. Reliability
- Comprehensive error handling
- Service availability checks
- Retry mechanisms
- Graceful degradation

### 3. Maintainability
- Modular architecture
- Clear separation of concerns
- Comprehensive logging
- Configuration management

## 🎉 Benefits of New Approach

### 1. No API Limitations
- No quota restrictions
- No API key requirements
- Access to all public content
- Real-time data access

### 2. Enhanced Discovery
- Related video traversal
- Organic content discovery
- Community-driven recommendations
- Broader content coverage

### 3. Complete Pipeline
- End-to-end automation
- Integrated download management
- Comprehensive mapping files
- Database persistence

### 4. Flexibility
- Multiple starting points
- Configurable crawl depth
- Optional content downloading
- Various export formats

## 🚨 Important Considerations

### 1. Legal Compliance
- Respects robots.txt
- Rate limiting implementation
- Personal/research use only
- User responsibility for compliance

### 2. Service Dependencies
- External service availability
- Interface changes monitoring
- Fallback mechanisms
- Error handling

### 3. Resource Requirements
- Chrome browser dependency
- Storage space for downloads
- Network bandwidth usage
- Processing time considerations

## 🔮 Future Enhancements

### Potential Improvements
1. **Multi-threaded Processing**: Parallel video processing
2. **Advanced Filtering**: Content quality assessment
3. **Resume Capability**: Interrupted crawl recovery
4. **Cloud Storage**: S3/GCS integration
5. **API Endpoints**: REST API for remote access
6. **Web Interface**: Browser-based management
7. **Analytics Dashboard**: Real-time statistics
8. **Content Analysis**: Advanced NLP features

### Service Integrations
1. **Additional Download Services**: More video/subtitle sources
2. **Cloud Transcription**: Google/AWS speech-to-text
3. **Translation Services**: Automatic subtitle translation
4. **Content Moderation**: Inappropriate content filtering

## 📋 Migration Guide

### For Existing Users
1. **Backup Data**: Export existing database
2. **Update Dependencies**: Run `uv sync`
3. **Install Browser**: Chrome/Chromium required
4. **Test Setup**: Run `make run-scraping-demo`
5. **Start Scraping**: Use new CLI commands

### Configuration Migration
- No YouTube API key required
- Update `.env` file with new options
- Adjust rate limiting as needed
- Configure download directories

## 🎯 Success Metrics

The restructure successfully achieves:
- ✅ Complete YouTube API independence
- ✅ Advanced Farsi content detection
- ✅ Automated video and subtitle downloads
- ✅ Comprehensive mapping file generation
- ✅ Database integration and persistence
- ✅ User-friendly CLI interface
- ✅ Extensive documentation and examples
- ✅ Robust error handling and logging
- ✅ Configurable and extensible architecture

## 🏁 Conclusion

VidCollector has been successfully transformed into a powerful web scraping pipeline that provides:

1. **Complete autonomy** from YouTube API limitations
2. **Advanced Farsi detection** capabilities
3. **Integrated download management** with external services
4. **Comprehensive data mapping** and persistence
5. **User-friendly interface** with extensive CLI options
6. **Robust architecture** with proper error handling
7. **Extensive documentation** for easy adoption

The new approach enables researchers and developers to build comprehensive Farsi video datasets without API restrictions, while maintaining high code quality and user experience standards.