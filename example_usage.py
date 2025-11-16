#!/usr/bin/env python3
"""
Example usage of VidCollector for testing without YouTube API key.
This demonstrates the basic functionality and structure.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vidcollector.config import Config
from vidcollector.database import DatabaseManager
from vidcollector.subtitle_extractor import SubtitleExtractor

def demo_database_operations():
    """Demonstrate database operations."""
    print("🗄️  Database Operations Demo")
    print("=" * 40)
    
    # Initialize database
    db = DatabaseManager("demo.db")
    
    # Sample video data
    sample_video = {
        'video_id': 'demo123',
        'title': 'نمونه ویدیو فارسی',
        'description': 'این یک ویدیو نمونه برای تست است',
        'channel_id': 'channel123',
        'channel_title': 'کانال نمونه',
        'duration': 300,
        'view_count': 1000,
        'like_count': 50,
        'published_at': '2023-01-01T00:00:00Z',
        'language': 'fa',
        'tags': ['فارسی', 'نمونه'],
        'thumbnail_url': 'https://example.com/thumb.jpg'
    }
    
    # Insert video
    if db.insert_video(sample_video):
        print("✅ Sample video inserted successfully")
    
    # Insert sample subtitles
    farsi_subtitle = "سلام دنیا! این یک زیرنویس فارسی است."
    english_subtitle = "Hello world! This is an English subtitle."
    
    if db.insert_subtitle('demo123', 'fa', 'manual', farsi_subtitle):
        print("✅ Farsi subtitle inserted successfully")
    
    if db.insert_subtitle('demo123', 'en', 'manual', english_subtitle):
        print("✅ English subtitle inserted successfully")
    
    # Show statistics
    print(f"\n📊 Database Statistics:")
    print(f"Videos: {db.get_video_count()}")
    print(f"Subtitles: {db.get_subtitle_count()}")
    
    # Clean up
    os.unlink("demo.db")
    print("\n🧹 Demo database cleaned up")

def demo_subtitle_processing():
    """Demonstrate subtitle processing capabilities."""
    print("\n📝 Subtitle Processing Demo")
    print("=" * 40)
    
    extractor = SubtitleExtractor()
    
    # Test Farsi character detection
    test_texts = [
        "Hello World",
        "سلام دنیا",
        "Hello سلام World",
        "This is English text",
        "این متن فارسی است"
    ]
    
    print("🔍 Farsi Character Detection:")
    for text in test_texts:
        has_farsi = extractor._contains_farsi_chars(text)
        print(f"  '{text}' -> {'✅ Has Farsi' if has_farsi else '❌ No Farsi'}")
    
    # Test text cleaning
    print("\n🧹 Text Cleaning:")
    dirty_texts = [
        "<b>Bold text</b> and <i>italic</i>",
        "[Music] Hello [Applause] World",
        "Text   with    multiple    spaces",
        "(Background noise) Clear speech"
    ]
    
    for dirty_text in dirty_texts:
        clean_text = extractor._clean_subtitle_text(dirty_text)
        print(f"  '{dirty_text}' -> '{clean_text}'")
    
    # Test subtitle statistics
    print("\n📊 Subtitle Statistics:")
    sample_content = """Line 1 of subtitle
Line 2 with more content
سلام دنیا - این خط فارسی است
Final line in English"""
    
    stats = extractor.get_subtitle_stats(sample_content)
    print(f"  Total lines: {stats['total_lines']}")
    print(f"  Total words: {stats['total_words']}")
    print(f"  Total characters: {stats['total_characters']}")
    print(f"  Has Farsi characters: {stats['has_farsi_chars']}")
    print(f"  Average line length: {stats['avg_line_length']:.1f}")

def demo_configuration():
    """Demonstrate configuration management."""
    print("\n⚙️  Configuration Demo")
    print("=" * 40)
    
    config = Config()
    
    print("📋 Default Configuration Values:")
    print(f"  Max videos per search: {config.MAX_VIDEOS_PER_SEARCH}")
    print(f"  Rate limit delay: {config.RATE_LIMIT_DELAY}s")
    print(f"  Max concurrent downloads: {config.MAX_CONCURRENT_DOWNLOADS}")
    print(f"  Database path: {config.DATABASE_PATH}")
    print(f"  Log level: {config.LOG_LEVEL}")
    print(f"  Number of Farsi keywords: {len(config.FARSI_KEYWORDS)}")
    print(f"  Sample keywords: {', '.join(config.FARSI_KEYWORDS[:5])}")

def main():
    """Run all demos."""
    print("🚀 VidCollector Demo")
    print("=" * 50)
    print("This demo shows the core functionality without requiring a YouTube API key.")
    print()
    
    try:
        demo_configuration()
        demo_database_operations()
        demo_subtitle_processing()
        
        print("\n🎉 Demo completed successfully!")
        print("\nTo use VidCollector with real YouTube data:")
        print("1. Get a YouTube Data API v3 key from Google Cloud Console")
        print("2. Copy .env.example to .env and add your API key")
        print("3. Run: python main.py crawl --max-videos 10")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())