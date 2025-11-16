"""Basic tests for VidCollector components."""

import unittest
import tempfile
import os
from pathlib import Path

from src.vidcollector.config import Config
from src.vidcollector.database import DatabaseManager

class TestConfig(unittest.TestCase):
    """Test configuration management."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = Config()
        self.assertIsInstance(config.MAX_VIDEOS_PER_SEARCH, int)
        self.assertIsInstance(config.RATE_LIMIT_DELAY, float)
        self.assertIsInstance(config.FARSI_KEYWORDS, list)
        self.assertTrue(len(config.FARSI_KEYWORDS) > 0)
    
    def test_config_validation_without_api_key(self):
        """Test config validation fails without API key."""
        # Temporarily remove API key
        original_key = Config.YOUTUBE_API_KEY
        Config.YOUTUBE_API_KEY = ''
        
        with self.assertRaises(ValueError):
            Config.validate()
        
        # Restore original key
        Config.YOUTUBE_API_KEY = original_key

class TestDatabase(unittest.TestCase):
    """Test database operations."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_database_initialization(self):
        """Test database tables are created."""
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check if we can get counts (tables exist)
        video_count = self.db.get_video_count()
        subtitle_count = self.db.get_subtitle_count()
        
        self.assertEqual(video_count, 0)
        self.assertEqual(subtitle_count, 0)
    
    def test_video_insertion(self):
        """Test video data insertion."""
        video_data = {
            'video_id': 'test123',
            'title': 'Test Video',
            'description': 'Test Description',
            'channel_id': 'channel123',
            'channel_title': 'Test Channel',
            'duration': 300,
            'view_count': 1000,
            'like_count': 50,
            'published_at': '2023-01-01T00:00:00Z',
            'language': 'fa',
            'tags': ['test', 'farsi'],
            'thumbnail_url': 'https://example.com/thumb.jpg'
        }
        
        # Insert video
        result = self.db.insert_video(video_data)
        self.assertTrue(result)
        
        # Check if video exists
        self.assertTrue(self.db.video_exists('test123'))
        
        # Check count
        self.assertEqual(self.db.get_video_count(), 1)
    
    def test_subtitle_insertion(self):
        """Test subtitle data insertion."""
        # First insert a video
        video_data = {
            'video_id': 'test123',
            'title': 'Test Video'
        }
        self.db.insert_video(video_data)
        
        # Insert subtitle
        result = self.db.insert_subtitle(
            video_id='test123',
            language='fa',
            subtitle_type='manual',
            content='سلام دنیا',
            file_path='/path/to/subtitle.vtt'
        )
        
        self.assertTrue(result)
        self.assertEqual(self.db.get_subtitle_count(), 1)
    
    def test_videos_without_subtitles(self):
        """Test finding videos without subtitles."""
        # Insert video without subtitles
        video_data = {
            'video_id': 'test123',
            'title': 'Test Video'
        }
        self.db.insert_video(video_data)
        
        # Should find the video
        videos_without_fa = self.db.get_videos_without_subtitles('fa')
        self.assertIn('test123', videos_without_fa)
        
        # Add Farsi subtitle
        self.db.insert_subtitle('test123', 'fa', 'manual', 'سلام')
        
        # Should not find the video anymore
        videos_without_fa = self.db.get_videos_without_subtitles('fa')
        self.assertNotIn('test123', videos_without_fa)

class TestSubtitleExtractor(unittest.TestCase):
    """Test subtitle extraction functionality."""
    
    def test_farsi_character_detection(self):
        """Test Farsi character detection."""
        from src.vidcollector.subtitle_extractor import SubtitleExtractor
        
        extractor = SubtitleExtractor()
        
        # Test with Farsi text
        farsi_text = "سلام دنیا"
        self.assertTrue(extractor._contains_farsi_chars(farsi_text))
        
        # Test with English text
        english_text = "Hello World"
        self.assertFalse(extractor._contains_farsi_chars(english_text))
        
        # Test with mixed text
        mixed_text = "Hello سلام World"
        self.assertTrue(extractor._contains_farsi_chars(mixed_text))
    
    def test_subtitle_text_cleaning(self):
        """Test subtitle text cleaning."""
        from src.vidcollector.subtitle_extractor import SubtitleExtractor
        
        extractor = SubtitleExtractor()
        
        # Test HTML tag removal
        html_text = "<b>Bold text</b> and <i>italic</i>"
        cleaned = extractor._clean_subtitle_text(html_text)
        self.assertEqual(cleaned, "Bold text and italic")
        
        # Test bracket removal
        bracket_text = "[Music] Hello [Applause] World"
        cleaned = extractor._clean_subtitle_text(bracket_text)
        self.assertEqual(cleaned, "Hello World")
    
    def test_subtitle_stats(self):
        """Test subtitle statistics calculation."""
        from src.vidcollector.subtitle_extractor import SubtitleExtractor
        
        extractor = SubtitleExtractor()
        
        test_content = "Line 1\nLine 2\nسلام دنیا\n"
        stats = extractor.get_subtitle_stats(test_content)
        
        self.assertEqual(stats['total_lines'], 3)
        self.assertTrue(stats['has_farsi_chars'])
        self.assertGreater(stats['total_words'], 0)
        self.assertGreater(stats['total_characters'], 0)

if __name__ == '__main__':
    unittest.main()