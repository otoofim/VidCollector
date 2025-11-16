"""Main crawler engine for VidCollector."""

import time
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from .config import Config
from .database import DatabaseManager
from .youtube_api import YouTubeAPI
from .subtitle_extractor import SubtitleExtractor

class FarsiVideoCrawler:
    """Main crawler for collecting Farsi YouTube videos with subtitles."""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.config.validate()
        
        # Initialize components
        self.db = DatabaseManager(self.config.DATABASE_PATH)
        self.youtube_api = YouTubeAPI(self.config.YOUTUBE_API_KEY)
        self.subtitle_extractor = SubtitleExtractor()
        
        # Crawler state
        self.session_id = str(uuid.uuid4())
        self.processed_videos: Set[str] = set()
        self.failed_videos: Set[str] = set()
        
        # Statistics
        self.stats = {
            'videos_found': 0,
            'videos_processed': 0,
            'subtitles_extracted': 0,
            'errors': 0,
            'skipped_existing': 0
        }
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def crawl_farsi_videos(self, max_videos: int = 100, 
                          search_queries: List[str] = None,
                          extract_subtitles: bool = True) -> Dict:
        """
        Main crawling method for Farsi videos.
        
        Args:
            max_videos: Maximum number of videos to crawl
            search_queries: Custom search queries (uses default if None)
            extract_subtitles: Whether to extract subtitles
        
        Returns:
            Dict with crawling statistics
        """
        self.logger.info(f"Starting Farsi video crawl session: {self.session_id}")
        self.logger.info(f"Target: {max_videos} videos, Extract subtitles: {extract_subtitles}")
        
        # Start crawl session in database
        search_query = ', '.join(search_queries) if search_queries else 'farsi_auto_search'
        self.db.start_crawl_session(self.session_id, search_query)
        
        try:
            # Phase 1: Search and collect video metadata
            self.logger.info("Phase 1: Searching for Farsi videos...")
            videos = self._search_videos(max_videos, search_queries)
            
            # Phase 2: Process videos and extract subtitles
            if extract_subtitles and videos:
                self.logger.info("Phase 2: Extracting subtitles...")
                self._process_videos_with_subtitles(videos)
            
            # Update final statistics
            self.db.update_crawl_session(
                self.session_id,
                videos_found=self.stats['videos_found'],
                videos_processed=self.stats['videos_processed'],
                subtitles_extracted=self.stats['subtitles_extracted'],
                status='completed'
            )
            
            self.logger.info("Crawl session completed successfully")
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Crawl session failed: {e}")
            self.db.update_crawl_session(self.session_id, status='failed')
            raise
    
    def _search_videos(self, max_videos: int, search_queries: List[str] = None) -> List[Dict]:
        """Search for videos and store metadata."""
        videos = []
        
        try:
            if search_queries:
                # Use custom search queries
                videos_per_query = max(1, max_videos // len(search_queries))
                
                for query in search_queries:
                    self.logger.info(f"Searching for: {query}")
                    
                    for video in self.youtube_api.search_videos(
                        query=query,
                        max_results=videos_per_query,
                        language='fa',
                        region_code='IR'
                    ):
                        if len(videos) >= max_videos:
                            break
                        
                        if not self._should_process_video(video):
                            continue
                        
                        videos.append(video)
                        self.stats['videos_found'] += 1
                        
                        # Store video metadata
                        if self.db.insert_video(video):
                            self.logger.debug(f"Stored video: {video['video_id']} - {video['title'][:50]}...")
                        
                        # Rate limiting
                        time.sleep(self.config.RATE_LIMIT_DELAY)
            else:
                # Use automatic Farsi search
                self.logger.info("Using automatic Farsi video search")
                
                for video in self.youtube_api.search_farsi_videos(max_results=max_videos):
                    if len(videos) >= max_videos:
                        break
                    
                    if not self._should_process_video(video):
                        continue
                    
                    videos.append(video)
                    self.stats['videos_found'] += 1
                    
                    # Store video metadata
                    if self.db.insert_video(video):
                        self.logger.debug(f"Stored video: {video['video_id']} - {video['title'][:50]}...")
                    
                    # Rate limiting
                    time.sleep(self.config.RATE_LIMIT_DELAY)
            
            self.logger.info(f"Found {len(videos)} videos to process")
            return videos
            
        except Exception as e:
            self.logger.error(f"Error during video search: {e}")
            raise
    
    def _should_process_video(self, video: Dict) -> bool:
        """Determine if a video should be processed."""
        video_id = video['video_id']
        
        # Skip if already processed in this session
        if video_id in self.processed_videos:
            return False
        
        # Skip if already exists in database (optional)
        if self.db.video_exists(video_id):
            self.stats['skipped_existing'] += 1
            self.logger.debug(f"Video {video_id} already exists in database")
            return False
        
        # Check duration constraints
        duration = video.get('duration', 0)
        if duration < self.config.MIN_VIDEO_DURATION or duration > self.config.MAX_VIDEO_DURATION:
            self.logger.debug(f"Video {video_id} duration {duration}s outside constraints")
            return False
        
        # Check channel whitelist if configured
        if self.config.CHANNEL_WHITELIST:
            channel_id = video.get('channel_id', '')
            if channel_id not in self.config.CHANNEL_WHITELIST:
                self.logger.debug(f"Video {video_id} channel not in whitelist")
                return False
        
        return True
    
    def _process_videos_with_subtitles(self, videos: List[Dict]):
        """Process videos and extract subtitles with concurrent processing."""
        
        with ThreadPoolExecutor(max_workers=self.config.MAX_CONCURRENT_DOWNLOADS) as executor:
            # Submit all video processing tasks
            future_to_video = {
                executor.submit(self._process_single_video, video): video
                for video in videos
            }
            
            # Process completed tasks with progress bar
            with tqdm(total=len(videos), desc="Processing videos") as pbar:
                for future in as_completed(future_to_video):
                    video = future_to_video[future]
                    video_id = video['video_id']
                    
                    try:
                        result = future.result()
                        if result:
                            self.stats['videos_processed'] += 1
                            if result.get('subtitles_extracted', 0) > 0:
                                self.stats['subtitles_extracted'] += result['subtitles_extracted']
                        else:
                            self.failed_videos.add(video_id)
                            self.stats['errors'] += 1
                    
                    except Exception as e:
                        self.logger.error(f"Error processing video {video_id}: {e}")
                        self.failed_videos.add(video_id)
                        self.stats['errors'] += 1
                    
                    finally:
                        self.processed_videos.add(video_id)
                        pbar.update(1)
    
    def _process_single_video(self, video: Dict) -> Optional[Dict]:
        """Process a single video and extract its subtitles."""
        video_id = video['video_id']
        
        try:
            self.logger.debug(f"Processing video: {video_id}")
            
            # Extract subtitles
            subtitles_info = self.subtitle_extractor.extract_subtitles(video_id)
            
            if not subtitles_info:
                self.logger.warning(f"No subtitles found for video {video_id}")
                return {'subtitles_extracted': 0}
            
            # Store subtitles in database
            subtitles_stored = 0
            for subtitle_key, subtitle_data in subtitles_info.items():
                language = subtitle_data['language']
                subtitle_type = subtitle_data['type']
                content = subtitle_data['content']
                file_path = subtitle_data.get('file_path')
                
                if content and len(content.strip()) > 0:
                    if self.db.insert_subtitle(video_id, language, subtitle_type, content, file_path):
                        subtitles_stored += 1
                        self.logger.debug(f"Stored {language} {subtitle_type} subtitle for {video_id}")
            
            return {'subtitles_extracted': subtitles_stored}
            
        except Exception as e:
            self.logger.error(f"Error processing video {video_id}: {e}")
            return None
    
    def crawl_specific_channels(self, channel_ids: List[str], max_videos_per_channel: int = 50) -> Dict:
        """Crawl videos from specific YouTube channels."""
        self.logger.info(f"Crawling {len(channel_ids)} specific channels")
        
        all_videos = []
        
        for channel_id in channel_ids:
            self.logger.info(f"Crawling channel: {channel_id}")
            
            try:
                channel_videos = list(self.youtube_api.get_channel_videos(
                    channel_id, max_videos_per_channel
                ))
                
                for video in channel_videos:
                    if self._should_process_video(video):
                        all_videos.append(video)
                        self.stats['videos_found'] += 1
                        
                        # Store video metadata
                        self.db.insert_video(video)
                
                self.logger.info(f"Found {len(channel_videos)} videos from channel {channel_id}")
                
            except Exception as e:
                self.logger.error(f"Error crawling channel {channel_id}: {e}")
                continue
        
        # Process videos with subtitles
        if all_videos:
            self._process_videos_with_subtitles(all_videos)
        
        return self.stats
    
    def resume_subtitle_extraction(self, max_videos: int = None) -> Dict:
        """Resume subtitle extraction for videos without subtitles."""
        self.logger.info("Resuming subtitle extraction for existing videos")
        
        # Get videos without Farsi subtitles
        videos_without_farsi = self.db.get_videos_without_subtitles('fa')
        videos_without_english = self.db.get_videos_without_subtitles('en')
        
        # Combine and deduplicate
        videos_to_process = list(set(videos_without_farsi + videos_without_english))
        
        if max_videos:
            videos_to_process = videos_to_process[:max_videos]
        
        self.logger.info(f"Found {len(videos_to_process)} videos needing subtitle extraction")
        
        # Create video objects for processing
        videos = [{'video_id': vid_id} for vid_id in videos_to_process]
        
        # Process videos
        self._process_videos_with_subtitles(videos)
        
        return self.stats
    
    def get_crawl_statistics(self) -> Dict:
        """Get comprehensive crawling statistics."""
        db_stats = {
            'total_videos_in_db': self.db.get_video_count(),
            'total_subtitles_in_db': self.db.get_subtitle_count(),
        }
        
        return {
            **self.stats,
            **db_stats,
            'session_id': self.session_id,
            'youtube_api_quota_used': self.youtube_api.get_quota_usage(),
            'processed_videos_count': len(self.processed_videos),
            'failed_videos_count': len(self.failed_videos)
        }