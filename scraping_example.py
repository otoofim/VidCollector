#!/usr/bin/env python3
"""
Example usage of VidCollector with web scraping approach.
This example shows how to use the scraper to collect Farsi videos and subtitles.
"""

import logging
import os
from src.vidcollector.config import Config
from src.vidcollector.scraping_crawler import FarsiVideoCrawler
from src.vidcollector.youtube_scraper import YouTubeScraper, FarsiDetector
from src.vidcollector.download_services import DownloadManager

def demo_farsi_detection():
    """Demonstrate Farsi text detection."""
    print("🔍 Farsi Detection Demo")
    print("=" * 40)
    
    detector = FarsiDetector()
    
    test_texts = [
        "Hello World",
        "سلام دنیا",
        "Hello سلام World",
        "This is English text",
        "این متن فارسی است",
        "فیلم جدید ایرانی",
        "Persian music video",
        "موزیک ویدیو فارسی جدید",
        "English with some فارسی words",
        "123 numbers only"
    ]
    
    for text in test_texts:
        has_farsi = detector.has_farsi_chars(text)
        is_farsi = detector.detect_farsi(text)
        print(f"'{text}' -> Farsi chars: {has_farsi}, Is Farsi: {is_farsi}")


def demo_youtube_scraping():
    """Demonstrate YouTube page scraping (without actual scraping)."""
    print("\n🌐 YouTube Scraping Demo")
    print("=" * 40)
    
    # Note: This is a demo without actual scraping to avoid hitting YouTube
    print("YouTube scraper would:")
    print("1. Navigate to a YouTube video page")
    print("2. Extract video metadata (title, description, channel)")
    print("3. Find related videos in the sidebar")
    print("4. Detect Farsi content in titles and descriptions")
    print("5. Follow links to related Farsi videos")
    print("6. Build a collection of Farsi video URLs")
    
    # Simulate some results
    sample_results = [
        {
            'video_id': 'sample123',
            'title': 'نمونه ویدیو فارسی',
            'description': 'این یک ویدیو نمونه فارسی است',
            'channel': 'کانال فارسی',
            'url': 'https://www.youtube.com/watch?v=sample123',
            'is_farsi': True,
            'farsi_score': 0.95
        },
        {
            'video_id': 'sample456',
            'title': 'Another Persian Video',
            'description': 'ویدیو دیگری با محتوای فارسی',
            'channel': 'Persian Channel',
            'url': 'https://www.youtube.com/watch?v=sample456',
            'is_farsi': True,
            'farsi_score': 0.78
        }
    ]
    
    print(f"\nFound {len(sample_results)} Farsi videos:")
    for video in sample_results:
        print(f"- {video['title']} (Score: {video['farsi_score']:.2f})")


def demo_download_services():
    """Demonstrate download services integration."""
    print("\n📥 Download Services Demo")
    print("=" * 40)
    
    print("Download services would:")
    print("1. Submit YouTube URLs to ytdown.to for video download")
    print("2. Extract available quality options (720p, 480p, etc.)")
    print("3. Download videos in preferred quality")
    print("4. Submit URLs to downsub.com for subtitle extraction")
    print("5. Download Farsi and English subtitles if available")
    print("6. Create mapping file: URL | Video File | Farsi Sub | English Sub")
    
    # Simulate mapping file content
    sample_mapping = [
        "https://www.youtube.com/watch?v=sample123 | downloads/videos/sample123_720p.mp4 | downloads/subtitles/sample123_fa.srt | downloads/subtitles/sample123_en.srt",
        "https://www.youtube.com/watch?v=sample456 | downloads/videos/sample456_720p.mp4 | downloads/subtitles/sample456_fa.srt | N/A"
    ]
    
    print("\nSample mapping file content:")
    for line in sample_mapping:
        print(f"  {line}")


def demo_database_operations():
    """Demonstrate database operations."""
    print("\n🗄️ Database Operations Demo")
    print("=" * 40)
    
    # Create a temporary config for demo
    config = Config()
    # Override the database path by setting the class attribute temporarily
    original_db_path = config.DATABASE_PATH
    config.DATABASE_PATH = "demo_farsi_videos.db"
    
    try:
        # Initialize crawler (this creates the database)
        crawler = FarsiVideoCrawler(config)
        
        print("✅ Database initialized successfully")
        
        # Get initial stats
        stats = crawler.get_stats()
        print(f"Initial stats: {stats}")
        
        # Clean up demo database
        if os.path.exists(config.database_path):
            os.remove(config.database_path)
            print("🧹 Demo database cleaned up")
        
    except Exception as e:
        print(f"❌ Database demo error: {e}")
    finally:
        # Restore original database path
        config.DATABASE_PATH = original_db_path


def demo_full_pipeline():
    """Demonstrate the complete pipeline (simulation)."""
    print("\n🚀 Complete Pipeline Demo")
    print("=" * 40)
    
    print("Complete pipeline would:")
    print("1. Start from a given YouTube video URL")
    print("2. Scrape the video page for metadata")
    print("3. Extract related videos from the sidebar")
    print("4. Filter for videos with Farsi content")
    print("5. For each Farsi video:")
    print("   - Store metadata in database")
    print("   - Download video using ytdown.to")
    print("   - Download subtitles using downsub.com")
    print("   - Update mapping file")
    print("6. Continue with related videos until max limit reached")
    print("7. Generate final statistics and export data")
    
    # Simulate final results
    print("\n📊 Simulated Results:")
    print("Videos found: 25")
    print("Videos processed: 23")
    print("Videos downloaded: 20")
    print("Farsi subtitles: 18")
    print("English subtitles: 15")
    print("Errors: 2")
    print("Duration: 45.6 seconds")


def main():
    """Run all demos."""
    print("🎬 VidCollector Web Scraping Demo")
    print("=" * 50)
    print("This demo shows the web scraping approach for collecting Farsi YouTube videos.")
    print("Note: No actual scraping is performed to avoid hitting external services.")
    print()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run demos
    demo_farsi_detection()
    demo_youtube_scraping()
    demo_download_services()
    demo_database_operations()
    demo_full_pipeline()
    
    print("\n🎉 Demo completed!")
    print("\nTo use VidCollector with real scraping:")
    print("1. Install Chrome/Chromium browser")
    print("2. Run: python -m vidcollector.scraping_cli crawl --start-url 'YOUTUBE_URL' --max-videos 10")
    print("3. Check downloads/ directory for videos and subtitles")
    print("4. View mapping file: downloads/video_subtitle_mapping.txt")


if __name__ == "__main__":
    main()