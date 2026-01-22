#!/usr/bin/env python3
"""
Download songs from YouTube using yt-dlp.

Supports:
- Downloading from song list JSON (from Deezer/Spotify charts)
- Searching and downloading by song name
- Downloading from YouTube playlist URLs
- Renaming audio files to standard format

Install: pip install yt-dlp
"""

import json
import os
import subprocess
import re
from pathlib import Path

def clean_filename(text):
    """Clean text for use in filenames."""
    # Remove invalid characters
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_filename(filename):
    """
    Parse various filename formats to extract title and artist.
    
    Supports formats:
    - "Artist - Title.mp3"
    - "Title by Artist.mp3"
    - "Artist-Title.mp3"
    - "Title_Artist.mp3"
    """
    name = Path(filename).stem  # Remove extension
    
    # Try different patterns
    patterns = [
        r'^(.+?)\s*-\s*(.+)$',      # Artist - Title
        r'^(.+?)\s+by\s+(.+)$',     # Title by Artist
        r'^(.+?)_(.+)$',            # Title_Artist
    ]
    
    for pattern in patterns:
        match = re.match(pattern, name)
        if match:
            part1, part2 = match.groups()
            # Heuristic: assume first part is artist if it's shorter or if pattern is "by"
            if 'by' in pattern:
                return part1.strip(), part2.strip()  # Title, Artist
            else:
                return part2.strip(), part1.strip()  # Title, Artist
    
    # Fallback: use entire name as title
    return name.strip(), "Unknown Artist"

def rename_audio_files(directory, format_pattern="{title} by {artist}", dry_run=False):
    """
    Rename audio files in a directory to a standard format.
    
    Args:
        directory: Directory containing audio files
        format_pattern: Format string with {title} and {artist} placeholders
        dry_run: If True, only show what would be renamed without actually renaming
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"❌ Directory not found: {directory}")
        return
    
    # Find audio files
    audio_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(dir_path.glob(f'*{ext}'))
    
    if not audio_files:
        print(f"❌ No audio files found in {directory}")
        return
    
    print(f"\n📝 {'DRY RUN - ' if dry_run else ''}Renaming files in: {dir_path.absolute()}")
    print(f"   Format: {format_pattern}")
    print("=" * 60)
    
    renamed = 0
    skipped = 0
    errors = 0
    
    for file_path in sorted(audio_files):
        try:
            # Parse current filename
            title, artist = parse_filename(file_path.name)
            
            # Generate new filename
            new_name = format_pattern.format(title=title, artist=artist)
            new_name = clean_filename(new_name)
            new_path = file_path.parent / f"{new_name}{file_path.suffix}"
            
            # Check if already in correct format
            if file_path.name == new_path.name:
                print(f"⏭️  {file_path.name} (already correct)")
                skipped += 1
                continue
            
            # Check if target exists
            if new_path.exists() and new_path != file_path:
                print(f"⚠️  {file_path.name} → {new_path.name} (target exists)")
                skipped += 1
                continue
            
            print(f"✏️  {file_path.name}")
            print(f"   → {new_path.name}")
            
            if not dry_run:
                file_path.rename(new_path)
            
            renamed += 1
            
        except Exception as e:
            print(f"✗ Error renaming {file_path.name}: {e}")
            errors += 1
    
    print("\n" + "=" * 60)
    print(f"{'DRY RUN - ' if dry_run else ''}Rename Summary:")
    print(f"   Renamed: {renamed}")
    print(f"   Skipped: {skipped}")
    print(f"   Errors: {errors}")
    
    if dry_run:
        print(f"\n💡 This was a dry run. Use --execute to actually rename files.")


def download_youtube_audio(query, output_dir='youtube_songs', max_results=1):
    """
    Search YouTube and download audio for a song.
    
    Args:
        query: Search query (e.g., "Artist - Song Title")
        output_dir: Directory to save audio files
        max_results: Number of results to download (usually 1)
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # yt-dlp command to search and download best audio
    cmd = [
        'yt-dlp',
        f'ytsearch{max_results}:{query}',  # Search YouTube
        '--extract-audio',                  # Extract audio only
        '--audio-format', 'mp3',            # Convert to MP3
        '--audio-quality', '0',             # Best quality
        '--output', str(output_path / '%(artist)s - %(title)s.%(ext)s'),
        '--restrict-filenames',             # Clean filenames
        '--no-playlist',                    # Don't download playlists
        '--max-downloads', str(max_results),
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return True
        else:
            print(f"   ✗ Error: {result.stderr[:100]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ✗ Timeout")
        return False
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

def download_from_playlist(playlist_url, output_dir='youtube_songs', max_songs=50):
    """Download songs from a YouTube playlist."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"\n📥 Downloading from playlist: {playlist_url}")
    print(f"   Output: {output_path.absolute()}")
    print(f"   Max songs: {max_songs}")
    print("=" * 60)
    
    cmd = [
        'yt-dlp',
        playlist_url,
        '--extract-audio',
        '--audio-format', 'mp3',
        '--audio-quality', '0',
        '--output', str(output_path / '%(artist)s - %(title)s.%(ext)s'),
        '--restrict-filenames',
        '--max-downloads', str(max_songs),
        '--no-warnings',
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Playlist download complete!")
    except Exception as e:
        print(f"\n✗ Error: {e}")

def download_from_json(json_file='music_songs_list.json', output_dir='youtube_songs', limit=50):
    """
    Download songs from the JSON chart file using YouTube.
    
    This fetches FULL songs instead of 30-second previews!
    """
    if not os.path.exists(json_file):
        print(f"❌ {json_file} not found. Run get_spotify_recommendations.py first.")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        all_songs = json.load(f)
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"\n📥 Downloading songs from {json_file} via YouTube")
    print(f"   Output: {output_path.absolute()}")
    print(f"   Limit: {limit} songs")
    print("=" * 60)
    
    downloaded = 0
    failed = 0
    skipped = 0
    
    # Flatten all tracks
    all_tracks = []
    for playlist_name, tracks in all_songs.items():
        for track in tracks:
            track['source_playlist'] = playlist_name
            all_tracks.append(track)
    
    # Limit total downloads
    all_tracks = all_tracks[:limit]
    
    for idx, track in enumerate(all_tracks, 1):
        title = track['title']
        artist = track['artist']
        query = f"{artist} - {title}"
        
        # Clean filename for checking
        safe_filename = f"{artist} - {title}".replace('/', '-').replace('\\', '-')
        safe_filename = safe_filename.replace(':', '-').replace('?', '').replace('*', '')
        
        # Check if file already exists (rough check)
        existing_files = list(output_path.glob(f"*{title[:20]}*.mp3"))
        if existing_files:
            print(f"[{idx}/{len(all_tracks)}] ⏭️  {query[:60]}... (exists)")
            skipped += 1
            continue
        
        print(f"[{idx}/{len(all_tracks)}] 📥 {query[:60]}...")
        
        if download_youtube_audio(query, output_dir):
            downloaded += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print("✅ Download complete!")
    print(f"   Downloaded: {downloaded}")
    print(f"   Skipped (exists): {skipped}")
    print(f"   Failed: {failed}")
    print(f"\n📁 Audio files: {output_path.absolute()}")
    print(f"\n💡 Next step: Upload to database")
    print(f"   cd backend")
    print(f"   python scripts/reindex_databse.py --audio-dir ../{output_dir} --force")

def search_and_download(query, output_dir='youtube_songs'):
    """Search and download a single song."""
    print(f"\n🔍 Searching YouTube: {query}")
    if download_youtube_audio(query, output_dir):
        print("✅ Downloaded!")
    else:
        print("✗ Failed")

if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 60)
    print("YOUTUBE SONG DOWNLOADER (yt-dlp)")
    print("=" * 60)
    print("\n🎵 Downloads FULL songs from YouTube (not 30s previews!)")
    
    # Check if yt-dlp is installed
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    except:
        print("\n❌ ERROR: yt-dlp not installed!")
        print("\nInstall with:")
        print("  pip install yt-dlp")
        print("\nOr:")
        print("  Windows: winget install yt-dlp")
        print("  Mac: brew install yt-dlp")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'json':
            # Download from JSON chart file
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            download_from_json(limit=limit)
        
        elif command == 'playlist':
            # Download from YouTube playlist
            if len(sys.argv) < 3:
                print("Usage: python download_youtube_songs.py playlist <URL> [max_songs]")
                sys.exit(1)
            url = sys.argv[2]
            max_songs = int(sys.argv[3]) if len(sys.argv) > 3 else 50
            download_from_playlist(url, max_songs=max_songs)
        
        elif command == 'search':
            # Search and download single song
            if len(sys.argv) < 3:
                print("Usage: python download_youtube_songs.py search '<Artist> - <Title>'")
                sys.exit(1)
            query = ' '.join(sys.argv[2:])
            search_and_download(query)
        
        elif command == 'rename':
            # Rename audio files in a directory
            if len(sys.argv) < 3:
                print("Usage: python download_youtube_songs.py rename <directory> [--execute]")
                print("\nExamples:")
                print("  python download_youtube_songs.py rename youtube_songs          # Dry run")
                print("  python download_youtube_songs.py rename youtube_songs --execute # Actually rename")
                sys.exit(1)
            
            directory = sys.argv[2]
            dry_run = '--execute' not in sys.argv
            rename_audio_files(directory, format_pattern="{title} by {artist}", dry_run=dry_run)
        
        else:
            print(f"❌ Unknown command: {command}")
            print("\nUsage:")
            print("  python download_youtube_songs.py json [limit]           - Download from chart JSON")
            print("  python download_youtube_songs.py playlist <URL> [max]   - Download from YouTube playlist")
            print("  python download_youtube_songs.py search '<query>'       - Search and download one song")
            print("  python download_youtube_songs.py rename <dir> [--execute] - Rename files to 'Title by Artist'")
    
    else:
        # Interactive mode
        print("\nWhat would you like to do?")
        print("1. Download from chart JSON (music_songs_list.json)")
        print("2. Download from YouTube playlist URL")
        print("3. Search and download a specific song")
        print("4. Rename audio files in a directory")
        
        choice = input("\nEnter choice (1/2/3/4): ").strip()
        
        if choice == '1':
            limit = input("How many songs to download? [50]: ").strip() or "50"
            download_from_json(limit=int(limit))
        
        elif choice == '2':
            url = input("Enter YouTube playlist URL: ").strip()
            max_songs = input("Max songs to download? [50]: ").strip() or "50"
            download_from_playlist(url, max_songs=int(max_songs))
        
        elif choice == '3':
            query = input("Enter song search (Artist - Title): ").strip()
            search_and_download(query)
        
        elif choice == '4':
            directory = input("Enter directory path [youtube_songs]: ").strip() or "youtube_songs"
            dry_run_choice = input("Dry run first? (y/n) [y]: ").strip().lower() or 'y'
            dry_run = dry_run_choice == 'y'
            rename_audio_files(directory, format_pattern="{title} by {artist}", dry_run=dry_run)
            
            if dry_run:
                execute = input("\nExecute rename? (y/n) [n]: ").strip().lower()
                if execute == 'y':
                    rename_audio_files(directory, format_pattern="{title} by {artist}", dry_run=False)
        
        else:
            print("❌ Invalid choice")