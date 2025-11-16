"""Subtitle extraction using yt-dlp."""

import os
import json
import tempfile
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import yt_dlp
import webvtt
import pysrt
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

class SubtitleExtractor:
    """Extract subtitles from YouTube videos using yt-dlp."""
    
    def __init__(self, output_dir: str = "subtitles"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # yt-dlp options for subtitle extraction
        self.ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['fa', 'en', 'fa-orig', 'en-orig'],
            'subtitlesformat': 'vtt',
            'skip_download': True,
            'outtmpl': str(self.output_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True
        }
    
    def extract_subtitles(self, video_id: str, video_url: str = None) -> Dict[str, Dict]:
        """
        Extract subtitles for a video.
        
        Args:
            video_id: YouTube video ID
            video_url: Full YouTube URL (optional, will be constructed if not provided)
        
        Returns:
            Dict with subtitle information for each language
        """
        if not video_url:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        subtitles_info = {}
        
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract info to see available subtitles
                info = ydl.extract_info(video_url, download=False)
                
                available_subs = info.get('subtitles', {})
                auto_subs = info.get('automatic_captions', {})
                
                # Process manual subtitles
                for lang, sub_list in available_subs.items():
                    if lang in ['fa', 'en']:
                        subtitle_data = self._download_and_process_subtitle(
                            video_id, lang, sub_list, 'manual'
                        )
                        if subtitle_data:
                            subtitles_info[f"{lang}_manual"] = subtitle_data
                
                # Process automatic subtitles
                for lang, sub_list in auto_subs.items():
                    if lang in ['fa', 'en']:
                        subtitle_data = self._download_and_process_subtitle(
                            video_id, lang, sub_list, 'auto'
                        )
                        if subtitle_data:
                            subtitles_info[f"{lang}_auto"] = subtitle_data
                
                # If no Farsi subtitles found, try to detect Farsi in English auto-captions
                if not any('fa' in key for key in subtitles_info.keys()):
                    if 'en_auto' in subtitles_info:
                        farsi_content = self._detect_farsi_in_subtitles(
                            subtitles_info['en_auto']['content']
                        )
                        if farsi_content:
                            subtitles_info['fa_detected'] = {
                                'content': farsi_content,
                                'type': 'detected',
                                'language': 'fa',
                                'file_path': None
                            }
        
        except Exception as e:
            print(f"Error extracting subtitles for {video_id}: {e}")
        
        return subtitles_info
    
    def _download_and_process_subtitle(self, video_id: str, lang: str, 
                                     sub_list: List[Dict], sub_type: str) -> Optional[Dict]:
        """Download and process a subtitle file."""
        try:
            # Find VTT format subtitle
            vtt_sub = None
            for sub in sub_list:
                if sub.get('ext') == 'vtt':
                    vtt_sub = sub
                    break
            
            if not vtt_sub:
                return None
            
            # Download subtitle
            subtitle_url = vtt_sub['url']
            subtitle_filename = f"{video_id}_{lang}_{sub_type}.vtt"
            subtitle_path = self.output_dir / subtitle_filename
            
            # Use yt-dlp to download the subtitle
            ydl_opts = {
                'writesubtitles': True,
                'subtitleslangs': [lang],
                'subtitlesformat': 'vtt',
                'skip_download': True,
                'outtmpl': str(self.output_dir / f'{video_id}.%(ext)s'),
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            
            # Find the downloaded subtitle file
            possible_files = [
                self.output_dir / f"{video_id}.{lang}.vtt",
                self.output_dir / f"{video_id}.{lang}-orig.vtt",
                self.output_dir / f"{video_id}.{lang}.{sub_type}.vtt"
            ]
            
            subtitle_file = None
            for file_path in possible_files:
                if file_path.exists():
                    subtitle_file = file_path
                    break
            
            if not subtitle_file:
                return None
            
            # Parse subtitle content
            content = self._parse_vtt_file(subtitle_file)
            
            return {
                'content': content,
                'type': sub_type,
                'language': lang,
                'file_path': str(subtitle_file)
            }
            
        except Exception as e:
            print(f"Error processing subtitle {lang}_{sub_type} for {video_id}: {e}")
            return None
    
    def _parse_vtt_file(self, file_path: Path) -> str:
        """Parse VTT subtitle file and extract text content."""
        try:
            captions = webvtt.read(str(file_path))
            text_content = []
            
            for caption in captions:
                # Clean up the text (remove HTML tags, extra whitespace)
                text = caption.text.strip()
                text = self._clean_subtitle_text(text)
                if text:
                    text_content.append(text)
            
            return '\n'.join(text_content)
            
        except Exception as e:
            print(f"Error parsing VTT file {file_path}: {e}")
            return ""
    
    def _clean_subtitle_text(self, text: str) -> str:
        """Clean subtitle text by removing HTML tags and formatting."""
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove common subtitle artifacts
        text = re.sub(r'\[.*?\]', '', text)  # Remove [Music], [Applause], etc.
        text = re.sub(r'\(.*?\)', '', text)  # Remove (Music), (Applause), etc.
        
        # Remove multiple whitespaces (after removing other elements)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _detect_farsi_in_subtitles(self, subtitle_content: str) -> Optional[str]:
        """Detect Farsi content in subtitle text."""
        try:
            # Split content into sentences
            sentences = subtitle_content.split('\n')
            farsi_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                try:
                    # Check if sentence contains Farsi characters
                    if self._contains_farsi_chars(sentence):
                        farsi_sentences.append(sentence)
                    else:
                        # Try language detection
                        detected_lang = detect(sentence)
                        if detected_lang == 'fa':
                            farsi_sentences.append(sentence)
                except LangDetectException:
                    # If language detection fails, check for Farsi characters
                    if self._contains_farsi_chars(sentence):
                        farsi_sentences.append(sentence)
            
            if farsi_sentences:
                return '\n'.join(farsi_sentences)
            
        except Exception as e:
            print(f"Error detecting Farsi content: {e}")
        
        return None
    
    def _contains_farsi_chars(self, text: str) -> bool:
        """Check if text contains Farsi/Persian characters."""
        farsi_range = range(0x0600, 0x06FF + 1)  # Arabic/Persian Unicode range
        return any(ord(char) in farsi_range for char in text)
    
    def get_subtitle_stats(self, subtitle_content: str) -> Dict:
        """Get statistics about subtitle content."""
        lines = [line.strip() for line in subtitle_content.split('\n') if line.strip()]
        
        return {
            'total_lines': len(lines),
            'total_characters': len(subtitle_content),
            'total_words': len(subtitle_content.split()),
            'has_farsi_chars': self._contains_farsi_chars(subtitle_content),
            'avg_line_length': sum(len(line) for line in lines) / len(lines) if lines else 0
        }
    
    def cleanup_temp_files(self, video_id: str):
        """Clean up temporary subtitle files for a video."""
        try:
            pattern = f"{video_id}*"
            for file_path in self.output_dir.glob(pattern):
                if file_path.is_file():
                    file_path.unlink()
        except Exception as e:
            print(f"Error cleaning up files for {video_id}: {e}")
    
    def batch_extract_subtitles(self, video_ids: List[str]) -> Dict[str, Dict]:
        """Extract subtitles for multiple videos."""
        results = {}
        
        for video_id in video_ids:
            print(f"Extracting subtitles for {video_id}...")
            subtitles = self.extract_subtitles(video_id)
            results[video_id] = subtitles
            
            # Optional: Clean up temporary files after processing
            # self.cleanup_temp_files(video_id)
        
        return results