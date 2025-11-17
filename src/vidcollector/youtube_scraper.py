"""
YouTube page scraper for extracting video information and related videos.
"""

import re
import time
import logging
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Set seed for consistent language detection
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)


class FarsiDetector:
    """Detect Farsi/Persian text in strings."""
    
    # Persian/Farsi Unicode ranges
    PERSIAN_CHARS = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
    
    @classmethod
    def has_farsi_chars(cls, text: str) -> bool:
        """Check if text contains Persian/Farsi characters."""
        if not text:
            return False
        return bool(cls.PERSIAN_CHARS.search(text))
    
    @classmethod
    def detect_farsi(cls, text: str, min_farsi_ratio: float = 0.1) -> bool:
        """
        Detect if text is primarily in Farsi.
        
        Args:
            text: Text to analyze
            min_farsi_ratio: Minimum ratio of Farsi characters required
            
        Returns:
            True if text is detected as Farsi
        """
        if not text or len(text.strip()) < 3:
            return False
        
        # First check for Persian characters
        if not cls.has_farsi_chars(text):
            return False
        
        # Calculate ratio of Persian characters
        persian_chars = len(cls.PERSIAN_CHARS.findall(text))
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return False
        
        farsi_ratio = persian_chars / total_chars
        
        # Use langdetect as secondary check
        try:
            detected_lang = detect(text)
            if detected_lang == 'fa':  # Persian language code
                return True
        except LangDetectException:
            pass
        
        return farsi_ratio >= min_farsi_ratio


class YouTubeScraper:
    """Scrape YouTube pages for video information and related videos."""
    
    def __init__(self, headless: bool = True, delay: float = 2.0):
        """
        Initialize YouTube scraper.
        
        Args:
            headless: Run browser in headless mode
            delay: Delay between requests in seconds
        """
        self.headless = headless
        self.delay = delay
        self.ua = UserAgent()
        self.session = requests.Session()
        self.driver = None
        self.farsi_detector = FarsiDetector()
        
        # Set up session headers
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver."""
        if self.driver:
            return self.driver
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={self.ua.random}')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(
                service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return self.driver
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            raise
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def scrape_video_page(self, video_url: str) -> Dict:
        """
        Scrape a YouTube video page for metadata and related videos.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Dictionary containing video information
        """
        video_id = self.extract_video_id(video_url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {video_url}")
        
        logger.info(f"Scraping video: {video_id}")
        
        try:
            driver = self._setup_driver()
            driver.get(video_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "title"))
            )
            
            # Wait a bit more for dynamic content
            time.sleep(3)
            
            # Extract video information
            video_info = self._extract_video_info(driver, video_id, video_url)
            
            # Extract related videos
            related_videos = self._extract_related_videos(driver)
            
            video_info['related_videos'] = related_videos
            
            return video_info
            
        except Exception as e:
            logger.error(f"Error scraping video {video_id}: {e}")
            return {
                'video_id': video_id,
                'url': video_url,
                'error': str(e),
                'related_videos': []
            }
        finally:
            time.sleep(self.delay)
    
    def _extract_video_info(self, driver: webdriver.Chrome, video_id: str, video_url: str) -> Dict:
        """Extract video metadata from the page."""
        info = {
            'video_id': video_id,
            'url': video_url,
            'title': '',
            'description': '',
            'channel': '',
            'channel_url': '',
            'views': '',
            'duration': '',
            'upload_date': '',
            'is_farsi': False,
            'farsi_score': 0.0
        }
        
        try:
            # Title
            title_element = driver.find_element(By.CSS_SELECTOR, "h1.ytd-video-primary-info-renderer")
            info['title'] = title_element.text.strip()
            
            # Channel name and URL
            try:
                channel_element = driver.find_element(By.CSS_SELECTOR, "#owner-name a")
                info['channel'] = channel_element.text.strip()
                info['channel_url'] = channel_element.get_attribute('href')
            except:
                pass
            
            # Description (click "Show more" if needed)
            try:
                show_more_button = driver.find_element(By.CSS_SELECTOR, "#description-inline-expander tp-yt-paper-button")
                if show_more_button.is_displayed():
                    driver.execute_script("arguments[0].click();", show_more_button)
                    time.sleep(1)
            except:
                pass
            
            try:
                description_element = driver.find_element(By.CSS_SELECTOR, "#description-text")
                info['description'] = description_element.text.strip()
            except:
                pass
            
            # Views
            try:
                views_element = driver.find_element(By.CSS_SELECTOR, "#info-text")
                info['views'] = views_element.text.strip()
            except:
                pass
            
            # Check if content is Farsi
            text_to_check = f"{info['title']} {info['description']}"
            info['is_farsi'] = self.farsi_detector.detect_farsi(text_to_check)
            
            # Calculate Farsi score
            if text_to_check:
                farsi_chars = len(self.farsi_detector.PERSIAN_CHARS.findall(text_to_check))
                total_chars = len([c for c in text_to_check if c.isalpha()])
                info['farsi_score'] = farsi_chars / total_chars if total_chars > 0 else 0.0
            
            logger.info(f"Extracted info for {video_id}: {info['title'][:50]}... (Farsi: {info['is_farsi']})")
            
        except Exception as e:
            logger.error(f"Error extracting video info: {e}")
        
        return info
    
    def _extract_related_videos(self, driver: webdriver.Chrome) -> List[Dict]:
        """Extract related videos from the sidebar."""
        related_videos = []
        
        try:
            # Scroll to load more related videos
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            
            # Find related video elements
            video_elements = driver.find_elements(By.CSS_SELECTOR, "#related #dismissible")
            
            for element in video_elements[:20]:  # Limit to first 20
                try:
                    # Extract video URL
                    link_element = element.find_element(By.CSS_SELECTOR, "a#thumbnail")
                    video_url = link_element.get_attribute('href')
                    
                    if not video_url or 'watch?v=' not in video_url:
                        continue
                    
                    video_id = self.extract_video_id(video_url)
                    if not video_id:
                        continue
                    
                    # Extract title
                    title_element = element.find_element(By.CSS_SELECTOR, "#video-title")
                    title = title_element.text.strip()
                    
                    # Extract channel
                    channel = ""
                    try:
                        channel_element = element.find_element(By.CSS_SELECTOR, "#channel-name a")
                        channel = channel_element.text.strip()
                    except:
                        pass
                    
                    # Check if title/channel suggests Farsi content
                    text_to_check = f"{title} {channel}"
                    is_farsi = self.farsi_detector.detect_farsi(text_to_check)
                    
                    related_video = {
                        'video_id': video_id,
                        'url': video_url,
                        'title': title,
                        'channel': channel,
                        'is_farsi': is_farsi
                    }
                    
                    related_videos.append(related_video)
                    
                except Exception as e:
                    logger.debug(f"Error extracting related video: {e}")
                    continue
            
            logger.info(f"Found {len(related_videos)} related videos")
            
        except Exception as e:
            logger.error(f"Error extracting related videos: {e}")
        
        return related_videos
    
    def find_farsi_videos(self, start_url: str, max_videos: int = 50) -> List[Dict]:
        """
        Find Farsi videos starting from a given URL.
        
        Args:
            start_url: Starting YouTube video URL
            max_videos: Maximum number of videos to collect
            
        Returns:
            List of Farsi video information
        """
        farsi_videos = []
        visited_urls = set()
        urls_to_visit = [start_url]
        
        logger.info(f"Starting Farsi video discovery from: {start_url}")
        
        while urls_to_visit and len(farsi_videos) < max_videos:
            current_url = urls_to_visit.pop(0)
            
            if current_url in visited_urls:
                continue
            
            visited_urls.add(current_url)
            
            try:
                video_info = self.scrape_video_page(current_url)
                
                if video_info.get('is_farsi', False):
                    farsi_videos.append(video_info)
                    logger.info(f"Found Farsi video {len(farsi_videos)}: {video_info.get('title', '')[:50]}...")
                
                # Add related Farsi videos to queue
                for related in video_info.get('related_videos', []):
                    if related.get('is_farsi', False) and related['url'] not in visited_urls:
                        urls_to_visit.append(related['url'])
                
                # Limit queue size
                urls_to_visit = urls_to_visit[:100]
                
            except Exception as e:
                logger.error(f"Error processing {current_url}: {e}")
                continue
        
        logger.info(f"Discovery complete. Found {len(farsi_videos)} Farsi videos.")
        return farsi_videos
    
    def close(self):
        """Close the browser driver."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)
    
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Replace with actual Farsi video
    
    with YouTubeScraper(headless=True) as scraper:
        video_info = scraper.scrape_video_page(test_url)
        print(f"Video info: {video_info}")