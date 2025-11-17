"""
Integration with external download services (ytdown.to and downsub.com).
"""

import os
import re
import time
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class YTDownService:
    """Interface with ytdown.to for video downloads."""
    
    def __init__(self, download_dir: str = "downloads"):
        """
        Initialize YTDown service.
        
        Args:
            download_dir: Directory to save downloaded videos
        """
        self.base_url = "https://ytdown.to/en2/"
        self.download_dir = download_dir
        self.ua = UserAgent()
        self.session = requests.Session()
        
        # Create download directory
        os.makedirs(download_dir, exist_ok=True)
        
        # Set up session headers
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def get_download_links(self, youtube_url: str) -> Dict[str, str]:
        """
        Get download links for a YouTube video.
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            Dictionary with quality options and download URLs
        """
        logger.info(f"Getting download links for: {youtube_url}")
        
        try:
            # Submit URL to ytdown.to
            response = self.session.get(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the form and submit the YouTube URL
            form_data = {
                'url': youtube_url,
                'submit': 'Download'
            }
            
            # Post the form
            response = self.session.post(self.base_url, data=form_data)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract download links
            download_links = {}
            
            # Look for download buttons/links
            download_elements = soup.find_all('a', href=True)
            
            for element in download_elements:
                href = element.get('href')
                text = element.get_text().strip()
                
                # Check if this looks like a download link
                if href and ('download' in href.lower() or 'mp4' in href.lower()):
                    # Extract quality information
                    quality_match = re.search(r'(\d+p)', text)
                    quality = quality_match.group(1) if quality_match else 'unknown'
                    
                    download_links[quality] = href
            
            logger.info(f"Found {len(download_links)} download options")
            return download_links
            
        except Exception as e:
            logger.error(f"Error getting download links: {e}")
            return {}
    
    def download_video(self, youtube_url: str, quality: str = "720p") -> Optional[str]:
        """
        Download a video from YouTube.
        
        Args:
            youtube_url: YouTube video URL
            quality: Preferred video quality
            
        Returns:
            Path to downloaded video file, or None if failed
        """
        try:
            download_links = self.get_download_links(youtube_url)
            
            if not download_links:
                logger.error("No download links found")
                return None
            
            # Choose best available quality
            preferred_qualities = [quality, "720p", "480p", "360p"]
            download_url = None
            
            for pref_quality in preferred_qualities:
                if pref_quality in download_links:
                    download_url = download_links[pref_quality]
                    break
            
            if not download_url:
                # Use first available option
                download_url = list(download_links.values())[0]
            
            # Extract video ID for filename
            video_id_match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', youtube_url)
            video_id = video_id_match.group(1) if video_id_match else "unknown"
            
            filename = f"{video_id}_{quality}.mp4"
            filepath = os.path.join(self.download_dir, filename)
            
            # Download the video
            logger.info(f"Downloading video to: {filepath}")
            
            response = self.session.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Video downloaded successfully: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None


class DownSubService:
    """Interface with downsub.com for subtitle downloads."""
    
    def __init__(self, download_dir: str = "subtitles"):
        """
        Initialize DownSub service.
        
        Args:
            download_dir: Directory to save downloaded subtitles
        """
        self.base_url = "https://downsub.com/"
        self.download_dir = download_dir
        self.ua = UserAgent()
        self.session = requests.Session()
        
        # Create download directory
        os.makedirs(download_dir, exist_ok=True)
        
        # Set up session headers
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def get_subtitle_links(self, youtube_url: str) -> Dict[str, Dict[str, str]]:
        """
        Get available subtitle download links.
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            Dictionary with language codes and download URLs
        """
        logger.info(f"Getting subtitle links for: {youtube_url}")
        
        try:
            # Submit URL to downsub.com
            response = self.session.get(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the form and submit the YouTube URL
            form_data = {
                'url': youtube_url
            }
            
            # Post the form
            response = self.session.post(self.base_url, data=form_data)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract subtitle links
            subtitle_links = {}
            
            # Look for subtitle download links
            subtitle_elements = soup.find_all('a', href=True)
            
            for element in subtitle_elements:
                href = element.get('href')
                text = element.get_text().strip()
                
                # Check if this looks like a subtitle download link
                if href and ('subtitle' in href.lower() or '.srt' in href.lower() or '.vtt' in href.lower()):
                    # Extract language information
                    lang_match = re.search(r'(english|farsi|persian|fa|en)', text.lower())
                    
                    if lang_match:
                        lang = lang_match.group(1)
                        if lang in ['farsi', 'persian']:
                            lang = 'fa'
                        elif lang == 'english':
                            lang = 'en'
                        
                        # Determine format
                        format_type = 'srt' if '.srt' in href.lower() else 'vtt'
                        
                        if lang not in subtitle_links:
                            subtitle_links[lang] = {}
                        
                        subtitle_links[lang][format_type] = href
            
            logger.info(f"Found subtitles for languages: {list(subtitle_links.keys())}")
            return subtitle_links
            
        except Exception as e:
            logger.error(f"Error getting subtitle links: {e}")
            return {}
    
    def download_subtitles(self, youtube_url: str, languages: List[str] = ['fa', 'en']) -> Dict[str, str]:
        """
        Download subtitles for specified languages.
        
        Args:
            youtube_url: YouTube video URL
            languages: List of language codes to download
            
        Returns:
            Dictionary mapping language codes to downloaded file paths
        """
        try:
            subtitle_links = self.get_subtitle_links(youtube_url)
            downloaded_files = {}
            
            # Extract video ID for filename
            video_id_match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', youtube_url)
            video_id = video_id_match.group(1) if video_id_match else "unknown"
            
            for lang in languages:
                if lang in subtitle_links:
                    # Prefer SRT format over VTT
                    format_type = 'srt' if 'srt' in subtitle_links[lang] else 'vtt'
                    download_url = subtitle_links[lang][format_type]
                    
                    filename = f"{video_id}_{lang}.{format_type}"
                    filepath = os.path.join(self.download_dir, filename)
                    
                    # Download the subtitle file
                    logger.info(f"Downloading {lang} subtitles to: {filepath}")
                    
                    response = self.session.get(download_url)
                    response.raise_for_status()
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    
                    downloaded_files[lang] = filepath
                    logger.info(f"Subtitles downloaded: {filepath}")
                else:
                    logger.warning(f"No subtitles found for language: {lang}")
            
            return downloaded_files
            
        except Exception as e:
            logger.error(f"Error downloading subtitles: {e}")
            return {}


class DownloadManager:
    """Manage video and subtitle downloads."""
    
    def __init__(self, video_dir: str = "downloads/videos", subtitle_dir: str = "downloads/subtitles"):
        """
        Initialize download manager.
        
        Args:
            video_dir: Directory for video downloads
            subtitle_dir: Directory for subtitle downloads
        """
        self.video_service = YTDownService(video_dir)
        self.subtitle_service = DownSubService(subtitle_dir)
        self.mapping_file = "downloads/video_subtitle_mapping.txt"
        
        # Create mapping file directory
        os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
    
    def download_video_with_subtitles(self, youtube_url: str, video_quality: str = "720p", 
                                    subtitle_languages: List[str] = ['fa', 'en']) -> Dict:
        """
        Download video and subtitles, then update mapping file.
        
        Args:
            youtube_url: YouTube video URL
            video_quality: Preferred video quality
            subtitle_languages: Languages to download subtitles for
            
        Returns:
            Dictionary with download results
        """
        logger.info(f"Starting download for: {youtube_url}")
        
        result = {
            'url': youtube_url,
            'video_file': None,
            'subtitle_files': {},
            'success': False,
            'error': None
        }
        
        try:
            # Download video
            video_file = self.video_service.download_video(youtube_url, video_quality)
            result['video_file'] = video_file
            
            # Download subtitles
            subtitle_files = self.subtitle_service.download_subtitles(youtube_url, subtitle_languages)
            result['subtitle_files'] = subtitle_files
            
            # Update mapping file
            self._update_mapping_file(youtube_url, video_file, subtitle_files)
            
            result['success'] = True
            logger.info(f"Download completed successfully for: {youtube_url}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Download failed for {youtube_url}: {e}")
        
        return result
    
    def _update_mapping_file(self, youtube_url: str, video_file: Optional[str], 
                           subtitle_files: Dict[str, str]):
        """Update the video-subtitle mapping file."""
        try:
            with open(self.mapping_file, 'a', encoding='utf-8') as f:
                # Format: URL | Video File | Farsi Subtitle | English Subtitle
                farsi_sub = subtitle_files.get('fa', 'N/A')
                english_sub = subtitle_files.get('en', 'N/A')
                video_path = video_file if video_file else 'N/A'
                
                line = f"{youtube_url} | {video_path} | {farsi_sub} | {english_sub}\n"
                f.write(line)
                
            logger.info(f"Updated mapping file: {self.mapping_file}")
            
        except Exception as e:
            logger.error(f"Error updating mapping file: {e}")
    
    def get_mapping_summary(self) -> List[Dict]:
        """Get summary of all downloaded content."""
        summary = []
        
        try:
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split(' | ')
                        if len(parts) >= 4:
                            summary.append({
                                'url': parts[0],
                                'video_file': parts[1] if parts[1] != 'N/A' else None,
                                'farsi_subtitle': parts[2] if parts[2] != 'N/A' else None,
                                'english_subtitle': parts[3] if parts[3] != 'N/A' else None
                            })
        except Exception as e:
            logger.error(f"Error reading mapping file: {e}")
        
        return summary


if __name__ == "__main__":
    # Test the download services
    logging.basicConfig(level=logging.INFO)
    
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Replace with actual video
    
    manager = DownloadManager()
    result = manager.download_video_with_subtitles(test_url)
    print(f"Download result: {result}")
    
    summary = manager.get_mapping_summary()
    print(f"Mapping summary: {summary}")