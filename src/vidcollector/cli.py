"""Command-line interface for VidCollector."""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Optional

from .config import Config
from .crawler import FarsiVideoCrawler
from .database import DatabaseManager

def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="VidCollector - YouTube Farsi Video Crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic crawl with 50 videos
  python -m vidcollector crawl --max-videos 50
  
  # Crawl with custom search queries
  python -m vidcollector crawl --queries "فیلم ایرانی" "موسیقی ایرانی" --max-videos 100
  
  # Crawl specific channels
  python -m vidcollector crawl-channels --channel-ids UC123456789 UC987654321
  
  # Resume subtitle extraction
  python -m vidcollector resume-subtitles --max-videos 20
  
  # Show statistics
  python -m vidcollector stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Crawl command
    crawl_parser = subparsers.add_parser('crawl', help='Crawl Farsi videos from YouTube')
    crawl_parser.add_argument('--max-videos', type=int, default=50,
                             help='Maximum number of videos to crawl (default: 50)')
    crawl_parser.add_argument('--queries', nargs='+', 
                             help='Custom search queries (space-separated)')
    crawl_parser.add_argument('--no-subtitles', action='store_true',
                             help='Skip subtitle extraction')
    crawl_parser.add_argument('--config', type=str,
                             help='Path to custom config file')
    
    # Crawl channels command
    channels_parser = subparsers.add_parser('crawl-channels', 
                                           help='Crawl videos from specific channels')
    channels_parser.add_argument('--channel-ids', nargs='+', required=True,
                                help='YouTube channel IDs to crawl')
    channels_parser.add_argument('--max-videos-per-channel', type=int, default=50,
                                help='Maximum videos per channel (default: 50)')
    
    # Resume subtitles command
    resume_parser = subparsers.add_parser('resume-subtitles',
                                         help='Resume subtitle extraction for existing videos')
    resume_parser.add_argument('--max-videos', type=int,
                              help='Maximum number of videos to process')
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Show crawling statistics')
    stats_parser.add_argument('--detailed', action='store_true',
                             help='Show detailed statistics')
    
    # Database command
    db_parser = subparsers.add_parser('db', help='Database operations')
    db_subparsers = db_parser.add_subparsers(dest='db_command')
    
    db_subparsers.add_parser('init', help='Initialize database')
    db_subparsers.add_parser('reset', help='Reset database (WARNING: deletes all data)')
    
    export_parser = db_subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json',
                              help='Export format (default: json)')
    export_parser.add_argument('--output', type=str, required=True,
                              help='Output file path')
    export_parser.add_argument('--table', choices=['videos', 'subtitles', 'all'], 
                              default='all', help='Table to export (default: all)')
    
    return parser

def handle_crawl_command(args) -> int:
    """Handle the crawl command."""
    try:
        print("🚀 Starting VidCollector crawl...")
        
        # Initialize crawler
        crawler = FarsiVideoCrawler()
        
        # Run crawl
        stats = crawler.crawl_farsi_videos(
            max_videos=args.max_videos,
            search_queries=args.queries,
            extract_subtitles=not args.no_subtitles
        )
        
        # Print results
        print("\n✅ Crawl completed successfully!")
        print_stats(stats)
        
        return 0
        
    except Exception as e:
        print(f"❌ Crawl failed: {e}")
        return 1

def handle_crawl_channels_command(args) -> int:
    """Handle the crawl-channels command."""
    try:
        print(f"🚀 Starting channel crawl for {len(args.channel_ids)} channels...")
        
        # Initialize crawler
        crawler = FarsiVideoCrawler()
        
        # Run channel crawl
        stats = crawler.crawl_specific_channels(
            channel_ids=args.channel_ids,
            max_videos_per_channel=args.max_videos_per_channel
        )
        
        # Print results
        print("\n✅ Channel crawl completed successfully!")
        print_stats(stats)
        
        return 0
        
    except Exception as e:
        print(f"❌ Channel crawl failed: {e}")
        return 1

def handle_resume_subtitles_command(args) -> int:
    """Handle the resume-subtitles command."""
    try:
        print("🚀 Resuming subtitle extraction...")
        
        # Initialize crawler
        crawler = FarsiVideoCrawler()
        
        # Resume subtitle extraction
        stats = crawler.resume_subtitle_extraction(max_videos=args.max_videos)
        
        # Print results
        print("\n✅ Subtitle extraction completed!")
        print_stats(stats)
        
        return 0
        
    except Exception as e:
        print(f"❌ Subtitle extraction failed: {e}")
        return 1

def handle_stats_command(args) -> int:
    """Handle the stats command."""
    try:
        # Initialize database
        db = DatabaseManager(Config.DATABASE_PATH)
        
        # Get basic stats
        video_count = db.get_video_count()
        subtitle_count = db.get_subtitle_count()
        
        print("📊 VidCollector Statistics")
        print("=" * 30)
        print(f"Total videos in database: {video_count}")
        print(f"Total subtitles in database: {subtitle_count}")
        
        if args.detailed:
            # Get more detailed statistics
            print("\n📈 Detailed Statistics")
            print("-" * 20)
            
            # Videos without subtitles
            videos_without_farsi = len(db.get_videos_without_subtitles('fa'))
            videos_without_english = len(db.get_videos_without_subtitles('en'))
            
            print(f"Videos without Farsi subtitles: {videos_without_farsi}")
            print(f"Videos without English subtitles: {videos_without_english}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")
        return 1

def handle_db_command(args) -> int:
    """Handle database commands."""
    try:
        db = DatabaseManager(Config.DATABASE_PATH)
        
        if args.db_command == 'init':
            print("🔧 Initializing database...")
            # Database is automatically initialized in constructor
            print("✅ Database initialized successfully!")
            
        elif args.db_command == 'reset':
            print("⚠️  WARNING: This will delete all data!")
            confirm = input("Type 'yes' to confirm: ")
            if confirm.lower() == 'yes':
                # Delete database file
                db_path = Path(Config.DATABASE_PATH)
                if db_path.exists():
                    db_path.unlink()
                print("✅ Database reset successfully!")
            else:
                print("❌ Database reset cancelled.")
                
        elif args.db_command == 'export':
            print(f"📤 Exporting data to {args.output}...")
            export_data(db, args.format, args.output, args.table)
            print("✅ Data exported successfully!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        return 1

def export_data(db: DatabaseManager, format_type: str, output_path: str, table: str):
    """Export database data to file."""
    import sqlite3
    import csv
    
    data = {}
    
    with sqlite3.connect(db.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if table in ['videos', 'all']:
            cursor.execute('SELECT * FROM videos')
            data['videos'] = [dict(row) for row in cursor.fetchall()]
        
        if table in ['subtitles', 'all']:
            cursor.execute('SELECT * FROM subtitles')
            data['subtitles'] = [dict(row) for row in cursor.fetchall()]
    
    if format_type == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    elif format_type == 'csv':
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for table_name, rows in data.items():
            if rows:
                csv_path = output_dir / f"{Path(output_path).stem}_{table_name}.csv"
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)

def print_stats(stats: dict):
    """Print crawling statistics in a formatted way."""
    print("\n📊 Crawling Statistics")
    print("=" * 25)
    print(f"Videos found: {stats.get('videos_found', 0)}")
    print(f"Videos processed: {stats.get('videos_processed', 0)}")
    print(f"Subtitles extracted: {stats.get('subtitles_extracted', 0)}")
    print(f"Errors: {stats.get('errors', 0)}")
    print(f"Skipped (existing): {stats.get('skipped_existing', 0)}")
    
    if 'youtube_api_quota_used' in stats:
        print(f"YouTube API quota used: {stats['youtube_api_quota_used']}")
    
    if 'total_videos_in_db' in stats:
        print(f"Total videos in database: {stats['total_videos_in_db']}")
        print(f"Total subtitles in database: {stats['total_subtitles_in_db']}")

def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file or environment variables.")
        return 1
    
    # Route to appropriate handler
    if args.command == 'crawl':
        return handle_crawl_command(args)
    elif args.command == 'crawl-channels':
        return handle_crawl_channels_command(args)
    elif args.command == 'resume-subtitles':
        return handle_resume_subtitles_command(args)
    elif args.command == 'stats':
        return handle_stats_command(args)
    elif args.command == 'db':
        return handle_db_command(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())