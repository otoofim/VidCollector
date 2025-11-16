"""YouTube API integration for VidCollector."""

import time
from typing import Dict, List, Optional, Iterator
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import isodate
from .config import Config

class YouTubeAPI:
    """YouTube Data API v3 wrapper for searching and retrieving video information."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.YOUTUBE_API_KEY
        if not self.api_key:
            raise ValueError("YouTube API key is required")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.quota_used = 0
    
    def search_videos(self, query: str, max_results: int = 50, 
                     language: str = 'fa', region_code: str = 'IR',
                     published_after: str = None, published_before: str = None,
                     duration: str = 'medium') -> Iterator[Dict]:
        """
        Search for videos using YouTube Data API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            language: Language code (fa for Farsi)
            region_code: Region code (IR for Iran)
            published_after: RFC 3339 formatted date-time value
            published_before: RFC 3339 formatted date-time value
            duration: Video duration (short, medium, long)
        
        Yields:
            Dict: Video information
        """
        try:
            search_params = {
                'part': 'id,snippet',
                'q': query,
                'type': 'video',
                'maxResults': min(max_results, 50),  # API limit is 50 per request
                'relevanceLanguage': language,
                'regionCode': region_code,
                'videoDuration': duration,
                'videoCaption': 'any',  # Include videos with captions
                'order': 'relevance'
            }
            
            if published_after:
                search_params['publishedAfter'] = published_after
            if published_before:
                search_params['publishedBefore'] = published_before
            
            next_page_token = None
            videos_found = 0
            
            while videos_found < max_results:
                if next_page_token:
                    search_params['pageToken'] = next_page_token
                
                # Make API request
                search_response = self.youtube.search().list(**search_params).execute()
                self.quota_used += 100  # Search costs 100 quota units
                
                video_ids = [item['id']['videoId'] for item in search_response['items']]
                
                if not video_ids:
                    break
                
                # Get detailed video information
                videos_response = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails,status',
                    id=','.join(video_ids)
                ).execute()
                self.quota_used += 1  # Videos.list costs 1 quota unit per video
                
                for video in videos_response['items']:
                    if videos_found >= max_results:
                        break
                    
                    video_info = self._parse_video_info(video)
                    if video_info:
                        yield video_info
                        videos_found += 1
                
                # Check if there are more pages
                next_page_token = search_response.get('nextPageToken')
                if not next_page_token:
                    break
                
                # Rate limiting
                time.sleep(Config.RATE_LIMIT_DELAY)
                
        except HttpError as e:
            print(f"YouTube API error: {e}")
            if e.resp.status == 403:
                print("Quota exceeded or API key invalid")
            raise
    
    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """Get detailed information for a specific video."""
        try:
            response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails,status',
                id=video_id
            ).execute()
            self.quota_used += 1
            
            if response['items']:
                return self._parse_video_info(response['items'][0])
            return None
            
        except HttpError as e:
            print(f"Error getting video details for {video_id}: {e}")
            return None
    
    def get_channel_videos(self, channel_id: str, max_results: int = 50) -> Iterator[Dict]:
        """Get videos from a specific channel."""
        try:
            # Get channel's uploads playlist
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            self.quota_used += 1
            
            if not channel_response['items']:
                return
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from uploads playlist
            next_page_token = None
            videos_found = 0
            
            while videos_found < max_results:
                playlist_params = {
                    'part': 'snippet',
                    'playlistId': uploads_playlist_id,
                    'maxResults': min(50, max_results - videos_found)
                }
                
                if next_page_token:
                    playlist_params['pageToken'] = next_page_token
                
                playlist_response = self.youtube.playlistItems().list(**playlist_params).execute()
                self.quota_used += 1
                
                video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_response['items']]
                
                if not video_ids:
                    break
                
                # Get detailed video information
                videos_response = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails,status',
                    id=','.join(video_ids)
                ).execute()
                self.quota_used += 1
                
                for video in videos_response['items']:
                    if videos_found >= max_results:
                        break
                    
                    video_info = self._parse_video_info(video)
                    if video_info:
                        yield video_info
                        videos_found += 1
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break
                
                time.sleep(Config.RATE_LIMIT_DELAY)
                
        except HttpError as e:
            print(f"Error getting channel videos for {channel_id}: {e}")
    
    def _parse_video_info(self, video_data: Dict) -> Optional[Dict]:
        """Parse video data from YouTube API response."""
        try:
            snippet = video_data['snippet']
            statistics = video_data.get('statistics', {})
            content_details = video_data.get('contentDetails', {})
            
            # Parse duration
            duration_iso = content_details.get('duration', 'PT0S')
            duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())
            
            # Filter by duration constraints
            if duration_seconds < Config.MIN_VIDEO_DURATION or duration_seconds > Config.MAX_VIDEO_DURATION:
                return None
            
            video_info = {
                'video_id': video_data['id'],
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'channel_id': snippet.get('channelId', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', ''),
                'duration': duration_seconds,
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'tags': snippet.get('tags', []),
                'language': snippet.get('defaultLanguage', ''),
                'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', '')
            }
            
            return video_info
            
        except Exception as e:
            print(f"Error parsing video info: {e}")
            return None
    
    def search_farsi_videos(self, max_results: int = 100) -> Iterator[Dict]:
        """Search for Farsi videos using predefined keywords and strategies."""
        
        # Search strategies for Farsi content
        search_queries = [
            # Direct Farsi keywords
            *Config.FARSI_KEYWORDS,
            
            # Popular Iranian topics
            'ایران Iran',
            'تهران Tehran',
            'فارسی زبان',
            'پارسی Persian',
            'ایرانی Iranian',
            
            # Content categories in Farsi
            'فیلم ایرانی',
            'موسیقی ایرانی',
            'اخبار ایران',
            'آموزش فارسی',
            'کمدی ایرانی',
            'مستند ایرانی'
        ]
        
        videos_per_query = max(1, max_results // len(search_queries))
        total_found = 0
        
        for query in search_queries:
            if total_found >= max_results:
                break
                
            try:
                for video in self.search_videos(
                    query=query,
                    max_results=videos_per_query,
                    language='fa',
                    region_code='IR'
                ):
                    if total_found >= max_results:
                        break
                    
                    yield video
                    total_found += 1
                    
            except Exception as e:
                print(f"Error searching for query '{query}': {e}")
                continue
    
    def get_quota_usage(self) -> int:
        """Get current quota usage."""
        return self.quota_used