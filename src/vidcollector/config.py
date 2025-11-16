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
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings."""
        if not cls.YOUTUBE_API_KEY:
            raise ValueError("YOUTUBE_API_KEY is required")
        return True