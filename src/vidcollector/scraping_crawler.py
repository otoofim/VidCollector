"""
Main crawler engine for collecting Farsi YouTube videos and subtitles using web scraping.
"""

import time
import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from .config import Config
from .database import VideoDatabase
from .youtube_scraper import YouTubeScraper
from .download_services import DownloadManager

logger = logging.getLogger(__name__)


class FarsiVideoCrawler:
    """Main crawler for collecting Farsi YouTube videos and subtitles via web scraping."""
    
    def __init__(self, config: Config):
        """Initialize the crawler with configuration."""
        self.config = config
        self.db = VideoDatabase(config.database_path)
        self.scraper = YouTubeScraper(headless=True, delay=config.rate_limit_delay)
        self.download_manager = DownloadManager()
        
        logger.info(f"Initialized crawler with database: {config.database_path}")
    
    def crawl_from_url(self, start_url: str, max_videos: int = None, download_content: bool = True) -> Dict:
        """
        Run the main crawling process starting from a YouTube URL.
        
        Args:
            start_url: Starting YouTube video URL
            max_videos: Maximum number of videos to process
            download_content: Whether to download videos and subtitles
            
        Returns:
            Dictionary with crawling statistics
        """
        max_videos = max_videos or self.config.max_videos_per_search
        
        logger.info(f"Starting crawl from: {start_url}")
        logger.info(f"Max videos: {max_videos}, Download content: {download_content}")
        
        stats = {
            'videos_found': 0,
            'videos_processed': 0,
            'videos_downloaded': 0,
            'subtitles_extracted': 0,
            'errors': 0,
            'start_time': time.time(),
            'start_url': start_url
        }
        
        try:
            # Find Farsi videos starting from the given URL
            farsi_videos = self.scraper.find_farsi_videos(start_url, max_videos)
            stats['videos_found'] = len(farsi_videos)
            
            if not farsi_videos:
                logger.warning("No Farsi videos found")
                return stats
            
            logger.info(f"Found {len(farsi_videos)} Farsi videos")
            
            # Process each video
            with tqdm(total=len(farsi_videos), desc="Processing videos") as pbar:
                for video_info in farsi_videos:
                    try:
                        result = self._process_video(video_info, download_content)
                        
                        if result['success']:
                            stats['videos_processed'] += 1
                            if result.get('downloaded', False):
                                stats['videos_downloaded'] += 1
                            stats['subtitles_extracted'] += result.get('subtitles_count', 0)
                        else:
                            stats['errors'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing video {video_info.get('video_id', 'unknown')}: {e}")
                        stats['errors'] += 1
                    
                    pbar.update(1)
                    time.sleep(self.config.rate_limit_delay)
            
            stats['duration'] = time.time() - stats['start_time']
            logger.info(f"Crawling completed: {stats}")
            
        except Exception as e:
            logger.error(f"Crawling failed: {e}")
            stats['error'] = str(e)
        finally:
            self.scraper.close()
        
        return stats
    
    def crawl_multiple_urls(self, start_urls: List[str], max_videos_per_url: int = 10, 
                          download_content: bool = True) -> Dict:
        """
        Crawl multiple starting URLs.
        
        Args:
            start_urls: List of starting YouTube URLs
            max_videos_per_url: Maximum videos to find from each URL
            download_content: Whether to download videos and subtitles
            
        Returns:
            Combined crawling statistics
        """
        combined_stats = {
            'videos_found': 0,
            'videos_processed': 0,
            'videos_downloaded': 0,
            'subtitles_extracted': 0,
            'errors': 0,
            'start_time': time.time(),
            'urls_processed': 0,
            'start_urls': start_urls
        }
        
        for url in start_urls:
            logger.info(f"Processing URL {combined_stats['urls_processed'] + 1}/{len(start_urls)}: {url}")
            
            try:
                stats = self.crawl_from_url(url, max_videos_per_url, download_content)
                
                # Combine statistics
                combined_stats['videos_found'] += stats.get('videos_found', 0)
                combined_stats['videos_processed'] += stats.get('videos_processed', 0)
                combined_stats['videos_downloaded'] += stats.get('videos_downloaded', 0)
                combined_stats['subtitles_extracted'] += stats.get('subtitles_extracted', 0)
                combined_stats['errors'] += stats.get('errors', 0)
                combined_stats['urls_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                combined_stats['errors'] += 1
        
        combined_stats['duration'] = time.time() - combined_stats['start_time']
        logger.info(f"Multi-URL crawling completed: {combined_stats}")
        
        return combined_stats
    
    def _process_video(self, video_info: Dict, download_content: bool = True) -> Dict:
        """Process a single video: store metadata and optionally download content."""
        result = {
            'video_id': video_info.get('video_id'),
            'success': False,
            'subtitles_count': 0,
            'downloaded': False,
            'error': None
        }
        
        try:
            video_id = video_info.get('video_id')
            if not video_id:
                result['error'] = "No video ID found"
                return result
            
            # Check if video already processed
            if self.db.video_exists(video_id):
                logger.debug(f"Video {video_id} already processed")
                result['success'] = True
                return result
            
            # Store video metadata in database
            self.db.insert_video(
                video_id=video_id,
                title=video_info.get('title', ''),
                description=video_info.get('description', ''),
                channel_title=video_info.get('channel', ''),
                published_at='',  # Not available from scraping
                duration=video_info.get('duration', ''),
                view_count=0,  # Parse from views string if needed
                like_count=0,  # Not available from scraping
                language='fa',  # Detected as Farsi
                url=video_info.get('url', ''),
                farsi_score=video_info.get('farsi_score', 0.0)
            )
            
            # Download video and subtitles if requested
            if download_content:
                try:
                    download_result = self.download_manager.download_video_with_subtitles(
                        video_info.get('url', ''),
                        video_quality="720p",
                        subtitle_languages=['fa', 'en']
                    )
                    
                    if download_result.get('success', False):
                        result['downloaded'] = True
                        
                        # Store subtitle information in database
                        for lang, subtitle_file in download_result.get('subtitle_files', {}).items():
                            if subtitle_file:
                                # Read subtitle content
                                try:
                                    with open(subtitle_file, 'r', encoding='utf-8') as f:
                                        subtitle_content = f.read()
                                    
                                    self.db.insert_subtitle(
                                        video_id=video_id,
                                        language=lang,
                                        content=subtitle_content,
                                        format_type='srt' if subtitle_file.endswith('.srt') else 'vtt',
                                        source='downsub.com',
                                        file_path=subtitle_file
                                    )
                                    result['subtitles_count'] += 1
                                    
                                except Exception as e:
                                    logger.error(f"Error reading subtitle file {subtitle_file}: {e}")
                    
                except Exception as e:
                    logger.error(f"Error downloading content for {video_id}: {e}")
                    # Continue processing even if download fails
            
            result['success'] = True
            logger.debug(f"Successfully processed video {video_id}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error processing video {video_info.get('video_id', 'unknown')}: {e}")
        
        return result
    
    def get_stats(self) -> Dict:
        """Get crawler statistics."""
        db_stats = self.db.get_stats()
        
        # Add download mapping statistics
        mapping_summary = self.download_manager.get_mapping_summary()
        db_stats['downloaded_videos'] = len([item for item in mapping_summary if item['video_file']])
        db_stats['downloaded_farsi_subtitles'] = len([item for item in mapping_summary if item['farsi_subtitle']])
        db_stats['downloaded_english_subtitles'] = len([item for item in mapping_summary if item['english_subtitle']])
        
        return db_stats
    
    def export_data(self, output_file: str, format_type: str = 'csv') -> bool:
        """Export collected data to file."""
        try:
            return self.db.export_data(output_file, format_type)
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def get_download_mapping(self) -> List[Dict]:
        """Get the video-subtitle download mapping."""
        return self.download_manager.get_mapping_summary()
    
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'scraper'):
            self.scraper.close()