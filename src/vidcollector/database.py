"""Database management for VidCollector."""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class DatabaseManager:
    """Manages SQLite database for storing video metadata and subtitles."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Videos table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    channel_id TEXT,
                    channel_title TEXT,
                    duration INTEGER,
                    view_count INTEGER,
                    like_count INTEGER,
                    published_at TEXT,
                    language TEXT,
                    tags TEXT,
                    thumbnail_url TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Subtitles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subtitles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    language TEXT NOT NULL,
                    subtitle_type TEXT NOT NULL,  -- 'auto' or 'manual'
                    content TEXT NOT NULL,
                    file_path TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id),
                    UNIQUE(video_id, language, subtitle_type)
                )
            ''')
            
            # Crawl sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crawl_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    search_query TEXT,
                    videos_found INTEGER DEFAULT 0,
                    videos_processed INTEGER DEFAULT 0,
                    subtitles_extracted INTEGER DEFAULT 0,
                    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    status TEXT DEFAULT 'running'
                )
            ''')
            
            conn.commit()
    
    def insert_video(self, video_data: Dict) -> bool:
        """Insert or update video metadata."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO videos (
                        video_id, title, description, channel_id, channel_title,
                        duration, view_count, like_count, published_at, language,
                        tags, thumbnail_url, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video_data['video_id'],
                    video_data['title'],
                    video_data.get('description', ''),
                    video_data.get('channel_id', ''),
                    video_data.get('channel_title', ''),
                    video_data.get('duration', 0),
                    video_data.get('view_count', 0),
                    video_data.get('like_count', 0),
                    video_data.get('published_at', ''),
                    video_data.get('language', ''),
                    json.dumps(video_data.get('tags', [])),
                    video_data.get('thumbnail_url', ''),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error inserting video {video_data.get('video_id', 'unknown')}: {e}")
            return False
    
    def insert_subtitle(self, video_id: str, language: str, subtitle_type: str, 
                       content: str, file_path: Optional[str] = None) -> bool:
        """Insert subtitle data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO subtitles (
                        video_id, language, subtitle_type, content, file_path
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (video_id, language, subtitle_type, content, file_path))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error inserting subtitle for {video_id}: {e}")
            return False
    
    def video_exists(self, video_id: str) -> bool:
        """Check if video already exists in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM videos WHERE video_id = ?', (video_id,))
            return cursor.fetchone() is not None
    
    def get_video_count(self) -> int:
        """Get total number of videos in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM videos')
            return cursor.fetchone()[0]
    
    def get_subtitle_count(self) -> int:
        """Get total number of subtitles in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM subtitles')
            return cursor.fetchone()[0]
    
    def get_videos_without_subtitles(self, language: str = None) -> List[str]:
        """Get video IDs that don't have subtitles for specified language."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if language:
                cursor.execute('''
                    SELECT v.video_id FROM videos v
                    LEFT JOIN subtitles s ON v.video_id = s.video_id AND s.language = ?
                    WHERE s.video_id IS NULL
                ''', (language,))
            else:
                cursor.execute('''
                    SELECT v.video_id FROM videos v
                    LEFT JOIN subtitles s ON v.video_id = s.video_id
                    WHERE s.video_id IS NULL
                ''')
            
            return [row[0] for row in cursor.fetchall()]
    
    def start_crawl_session(self, session_id: str, search_query: str) -> bool:
        """Start a new crawl session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO crawl_sessions (session_id, search_query)
                    VALUES (?, ?)
                ''', (session_id, search_query))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error starting crawl session: {e}")
            return False
    
    def update_crawl_session(self, session_id: str, **kwargs) -> bool:
        """Update crawl session statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                set_clauses = []
                values = []
                
                for key, value in kwargs.items():
                    if key in ['videos_found', 'videos_processed', 'subtitles_extracted', 'status']:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                
                if 'status' in kwargs and kwargs['status'] == 'completed':
                    set_clauses.append("completed_at = ?")
                    values.append(datetime.now().isoformat())
                
                if set_clauses:
                    query = f"UPDATE crawl_sessions SET {', '.join(set_clauses)} WHERE session_id = ?"
                    values.append(session_id)
                    cursor.execute(query, values)
                    conn.commit()
                
                return True
        except Exception as e:
            print(f"Error updating crawl session: {e}")
            return False


class VideoDatabase:
    """Simplified database interface for web scraping crawler."""
    
    def __init__(self, db_path: str):
        """Initialize database connection."""
        self.db_path = db_path
        self.db_manager = DatabaseManager(db_path)
    
    def video_exists(self, video_id: str) -> bool:
        """Check if video exists in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM videos WHERE video_id = ?", (video_id,))
                return cursor.fetchone() is not None
        except Exception:
            return False
    
    def insert_video(self, video_id: str, title: str, description: str = '', 
                    channel_title: str = '', published_at: str = '', duration: str = '',
                    view_count: int = 0, like_count: int = 0, language: str = 'fa',
                    url: str = '', farsi_score: float = 0.0) -> bool:
        """Insert video metadata."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO videos 
                    (video_id, title, description, channel_title, published_at, 
                     duration, view_count, like_count, language, tags, thumbnail_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (video_id, title, description, channel_title, published_at,
                      duration, view_count, like_count, language, 
                      json.dumps({'url': url, 'farsi_score': farsi_score}), ''))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error inserting video: {e}")
            return False
    
    def insert_subtitle(self, video_id: str, language: str, content: str,
                       format_type: str = 'srt', source: str = 'downsub.com',
                       file_path: str = '') -> bool:
        """Insert subtitle data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO subtitles 
                    (video_id, language, content, format, source, file_path, word_count, char_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (video_id, language, content, format_type, source, file_path,
                      len(content.split()), len(content)))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error inserting subtitle: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Video count
                cursor.execute("SELECT COUNT(*) FROM videos")
                video_count = cursor.fetchone()[0]
                
                # Subtitle count
                cursor.execute("SELECT COUNT(*) FROM subtitles")
                subtitle_count = cursor.fetchone()[0]
                
                # Farsi subtitle count
                cursor.execute("SELECT COUNT(*) FROM subtitles WHERE language = 'fa'")
                farsi_subtitle_count = cursor.fetchone()[0]
                
                # English subtitle count
                cursor.execute("SELECT COUNT(*) FROM subtitles WHERE language = 'en'")
                english_subtitle_count = cursor.fetchone()[0]
                
                return {
                    'videos': video_count,
                    'subtitles': subtitle_count,
                    'farsi_subtitles': farsi_subtitle_count,
                    'english_subtitles': english_subtitle_count
                }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {'videos': 0, 'subtitles': 0, 'farsi_subtitles': 0, 'english_subtitles': 0}
    
    def export_data(self, output_file: str, format_type: str = 'csv') -> bool:
        """Export data to file."""
        return self.db_manager.export_videos(output_file, format_type)