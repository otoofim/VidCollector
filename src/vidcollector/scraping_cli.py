"""
Command-line interface for the web scraping version of VidCollector.
"""

import argparse
import logging
import sys
from typing import List

from .config import Config
from .scraping_crawler import FarsiVideoCrawler


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/vidcollector.log')
        ]
    )


def crawl_command(args):
    """Handle crawl command."""
    config = Config()
    
    if not args.start_url:
        print("Error: --start-url is required for crawling")
        return 1
    
    crawler = FarsiVideoCrawler(config)
    
    try:
        if args.multiple_urls:
            # Parse multiple URLs
            urls = [url.strip() for url in args.start_url.split(',')]
            stats = crawler.crawl_multiple_urls(
                start_urls=urls,
                max_videos_per_url=args.max_videos // len(urls) if args.max_videos else 10,
                download_content=args.download
            )
        else:
            stats = crawler.crawl_from_url(
                start_url=args.start_url,
                max_videos=args.max_videos,
                download_content=args.download
            )
        
        # Print results
        print("\n🎉 Crawling Results:")
        print(f"Videos found: {stats.get('videos_found', 0)}")
        print(f"Videos processed: {stats.get('videos_processed', 0)}")
        if args.download:
            print(f"Videos downloaded: {stats.get('videos_downloaded', 0)}")
            print(f"Subtitles extracted: {stats.get('subtitles_extracted', 0)}")
        print(f"Errors: {stats.get('errors', 0)}")
        print(f"Duration: {stats.get('duration', 0):.2f} seconds")
        
        return 0
        
    except Exception as e:
        print(f"Error during crawling: {e}")
        return 1
    finally:
        crawler.cleanup()


def stats_command(args):
    """Handle stats command."""
    config = Config()
    crawler = FarsiVideoCrawler(config)
    
    try:
        stats = crawler.get_stats()
        
        print("\n📊 Database Statistics:")
        print(f"Total videos: {stats.get('videos', 0)}")
        print(f"Total subtitles: {stats.get('subtitles', 0)}")
        print(f"Farsi subtitles: {stats.get('farsi_subtitles', 0)}")
        print(f"English subtitles: {stats.get('english_subtitles', 0)}")
        
        if args.downloads:
            print(f"Downloaded videos: {stats.get('downloaded_videos', 0)}")
            print(f"Downloaded Farsi subtitles: {stats.get('downloaded_farsi_subtitles', 0)}")
            print(f"Downloaded English subtitles: {stats.get('downloaded_english_subtitles', 0)}")
        
        return 0
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        return 1


def export_command(args):
    """Handle export command."""
    config = Config()
    crawler = FarsiVideoCrawler(config)
    
    try:
        success = crawler.export_data(args.output, args.format)
        
        if success:
            print(f"✅ Data exported to: {args.output}")
            return 0
        else:
            print(f"❌ Export failed")
            return 1
            
    except Exception as e:
        print(f"Error during export: {e}")
        return 1


def mapping_command(args):
    """Handle mapping command to show video-subtitle mappings."""
    config = Config()
    crawler = FarsiVideoCrawler(config)
    
    try:
        mappings = crawler.get_download_mapping()
        
        if not mappings:
            print("No download mappings found.")
            return 0
        
        print("\n📁 Video-Subtitle Mappings:")
        print("=" * 80)
        
        for i, mapping in enumerate(mappings, 1):
            print(f"\n{i}. URL: {mapping['url']}")
            print(f"   Video: {mapping['video_file'] or 'Not downloaded'}")
            print(f"   Farsi Subtitle: {mapping['farsi_subtitle'] or 'Not available'}")
            print(f"   English Subtitle: {mapping['english_subtitle'] or 'Not available'}")
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write("URL | Video File | Farsi Subtitle | English Subtitle\n")
                f.write("=" * 80 + "\n")
                for mapping in mappings:
                    f.write(f"{mapping['url']} | {mapping['video_file'] or 'N/A'} | "
                           f"{mapping['farsi_subtitle'] or 'N/A'} | {mapping['english_subtitle'] or 'N/A'}\n")
            print(f"\n💾 Mappings saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        print(f"Error getting mappings: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="VidCollector - YouTube Farsi Video Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl from a single video URL
  python -m vidcollector.scraping_cli crawl --start-url "https://www.youtube.com/watch?v=VIDEO_ID" --max-videos 20

  # Crawl from multiple URLs without downloading
  python -m vidcollector.scraping_cli crawl --start-url "URL1,URL2,URL3" --multiple-urls --no-download

  # Show statistics
  python -m vidcollector.scraping_cli stats --downloads

  # Export data
  python -m vidcollector.scraping_cli export --output data.csv --format csv

  # Show download mappings
  python -m vidcollector.scraping_cli mapping --output mappings.txt
        """
    )
    
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Set logging level')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Crawl command
    crawl_parser = subparsers.add_parser('crawl', help='Start crawling from YouTube URL(s)')
    crawl_parser.add_argument('--start-url', required=True,
                             help='Starting YouTube video URL (or comma-separated URLs for multiple)')
    crawl_parser.add_argument('--max-videos', type=int, default=50,
                             help='Maximum number of videos to process (default: 50)')
    crawl_parser.add_argument('--multiple-urls', action='store_true',
                             help='Treat start-url as comma-separated list of URLs')
    crawl_parser.add_argument('--download', action='store_true', default=True,
                             help='Download videos and subtitles (default: True)')
    crawl_parser.add_argument('--no-download', dest='download', action='store_false',
                             help='Only collect metadata, do not download content')
    crawl_parser.set_defaults(func=crawl_command)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.add_argument('--downloads', action='store_true',
                             help='Include download statistics')
    stats_parser.set_defaults(func=stats_command)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export collected data')
    export_parser.add_argument('--output', required=True,
                              help='Output file path')
    export_parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                              help='Export format (default: csv)')
    export_parser.set_defaults(func=export_command)
    
    # Mapping command
    mapping_parser = subparsers.add_parser('mapping', help='Show video-subtitle mappings')
    mapping_parser.add_argument('--output', 
                               help='Save mappings to file')
    mapping_parser.set_defaults(func=mapping_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Run command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())