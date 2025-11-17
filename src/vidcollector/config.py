"""Configuration management for VidCollector."""

import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for VidCollector."""
    
    # YouTube API Configuration
    YOUTUBE_API_KEY: str = os.getenv('YOUTUBE_API_KEY', '')
    
    # Database Configuration
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'data/farsi_videos.db')
    
    # Crawler Settings
    MAX_VIDEOS_PER_SEARCH: int = int(os.getenv('MAX_VIDEOS_PER_SEARCH', '50'))
    RATE_LIMIT_DELAY: float = float(os.getenv('RATE_LIMIT_DELAY', '1.0'))
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv('MAX_CONCURRENT_DOWNLOADS', '3'))
    
    # Search Configuration
    FARSI_KEYWORDS: List[str] = os.getenv('FARSI_KEYWORDS', 'فارسی,پارسی,ایرانی,تهران,اصفهان,شیراز,مشهد').split(',')
    CHANNEL_WHITELIST: List[str] = [ch.strip() for ch in os.getenv('CHANNEL_WHITELIST', '').split(',') if ch.strip()]
    MAX_VIDEO_DURATION: int = int(os.getenv('MAX_VIDEO_DURATION', '3600'))  # 1 hour
    MIN_VIDEO_DURATION: int = int(os.getenv('MIN_VIDEO_DURATION', '60'))    # 1 minute
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'logs/vidcollector.log')
    
    # Web Scraping Configuration
    HEADLESS_BROWSER: bool = os.getenv('HEADLESS_BROWSER', 'true').lower() == 'true'
    VIDEO_DOWNLOAD_DIR: str = os.getenv('VIDEO_DOWNLOAD_DIR', 'downloads/videos')
    SUBTITLE_DOWNLOAD_DIR: str = os.getenv('SUBTITLE_DOWNLOAD_DIR', 'downloads/subtitles')
    
    # Compatibility properties for scraping crawler
    @property
    def database_path(self) -> str:
        return self.DATABASE_PATH
    
    @property
    def rate_limit_delay(self) -> float:
        return self.RATE_LIMIT_DELAY
    
    @property
    def max_videos_per_search(self) -> int:
        return self.MAX_VIDEOS_PER_SEARCH
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings."""
        if not cls.YOUTUBE_API_KEY:
            raise ValueError("YOUTUBE_API_KEY is required")
        return True