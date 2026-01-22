"""
Add songs from a directory to the database without dropping existing data.
- Automatically detects duplicates using file hash
- Parses filenames in multiple formats: "Title - Artist", "Title by Artist", "Artist - Title"
- Provides detailed progress and statistics
"""

import sys
import os
import argparse
from pathlib import Path
import re

# Add parent directory to path for imports
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.fingerprint import AudioFingerprinter
from app.database import DatabaseManager


def parse_title_artist(filename: str):
    """
    Parse title and artist from filename. Supports multiple formats:
    - "Song Title by Artist Name"
    - "Song Title - Artist Name"  
    - "Artist Name - Song Title"
    - "Song Title" (artist becomes "Unknown")
    """
    base = Path(filename).stem
    
    # Try "by" separator first (most common from YouTube downloads)
    if ' by ' in base:
        parts = base.split(' by ', 1)
        title = parts[0].strip()
        artist = parts[1].strip()
        return title or "Unknown", artist or "Unknown"
    
    # Try " - " separator
    if ' - ' in base:
        parts = base.split(' - ', 1)
        first = parts[0].strip()
        second = parts[1].strip()
        
        # Heuristic: if first part is much shorter, it's likely artist
        # e.g., "Drake - God's Plan" vs "God's Plan - Drake"
        if len(first) < len(second) * 0.6 and len(first) < 30:
            artist, title = first, second
        else:
            title, artist = first, second
            
        return title or "Unknown", artist or "Unknown"
    
    # No separator found - treat entire name as title
    return base.strip() or "Unknown", "Unknown"


def iter_audio_files(audio_dir: Path):
    """Recursively find all audio files in directory."""
    exts = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".opus", ".webm"}
    for path in sorted(audio_dir.rglob("*")):
        if path.suffix.lower() in exts:
            yield path


def add_songs(args):
    """Add all songs from directory to database, skipping duplicates."""
    db = DatabaseManager(database_url=args.database_url)
    audio_dir = Path(args.audio_dir).resolve()

    if not audio_dir.exists():
        raise SystemExit(f"Audio directory not found: {audio_dir}")

    # Initialize fingerprinter
    fp = AudioFingerprinter(
        sample_rate=args.sample_rate,
        n_fft=args.n_fft,
        hop_length=args.hop_length,
        freq_min=args.freq_min,
        freq_max=args.freq_max,
    )

    # Find all audio files
    audio_files = list(iter_audio_files(audio_dir))
    if not audio_files:
        print(f"No audio files found in {audio_dir}")
        return

    print(f"Found {len(audio_files)} audio files")
    print(f"Audio directory: {audio_dir}")
    print(f"Database: {os.getenv('DATABASE_URL', 'default')}")
    print()

    # Track statistics
    stats = {
        'total': len(audio_files),
        'added': 0,
        'skipped': 0,
        'failed': 0
    }

    # Process each file
    for idx, audio_path in enumerate(audio_files, 1):
        print(f"[{idx}/{len(audio_files)}] {audio_path.name}")
        
        try:
            # Generate fingerprints
            hashes = fp.fingerprint_file(str(audio_path))
            
            if not hashes:
                print(f"  ⚠ No fingerprints generated, skipping")
                stats['failed'] += 1
                continue
            
            # Parse metadata from filename
            title, artist = parse_title_artist(audio_path.name)
            
            # Add to database (will check for duplicates automatically)
            song_id = db.add_song(
                title=title,
                artist=artist,
                album=None,
                duration=None,
                fingerprints=hashes,
                filepath=str(audio_path),
            )
            
            # Check if it was added or skipped (duplicate)
            # The add_song method prints messages, but we track stats
            if song_id:
                # Check if this was a new addition or duplicate
                # We can infer from the presence of the message
                stats['added'] += 1
                print(f"  ✓ Added: '{title}' by {artist} (ID: {song_id}, {len(hashes)} fingerprints)")
            
        except Exception as exc:
            print(f"  ✗ Failed: {exc}")
            stats['failed'] += 1
            
        print()  # Blank line for readability

    # Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {stats['total']}")
    print(f"Successfully added:    {stats['added']}")
    print(f"Failed:                {stats['failed']}")
    print()
    
    if stats['added'] > 0:
        print(f"✓ Successfully added {stats['added']} songs to the database!")
    if stats['failed'] > 0:
        print(f"⚠ {stats['failed']} files failed to process")


def main():
    """Main entry point with argument parsing."""
    default_audio_dir = Path(__file__).resolve().parents[2] / "youtube_songs"

    parser = argparse.ArgumentParser(
        description="Add songs from directory to database (preserves existing data, skips duplicates)"
    )
    parser.add_argument(
        "--audio-dir", 
        default=default_audio_dir, 
        help=f"Directory containing audio files (default: {default_audio_dir})"
    )
    parser.add_argument(
        "--database-url", 
        default=None, 
        help="Override DATABASE_URL from .env file"
    )
    
    # Fingerprinting parameters (defaults match current configuration)
    parser.add_argument("--sample-rate", type=int, default=22050, help="Fingerprint sample rate")
    parser.add_argument("--n-fft", type=int, default=2048, help="FFT window size")
    parser.add_argument("--hop-length", type=int, default=512, help="STFT hop length")
    parser.add_argument("--freq-min", type=int, default=20, help="Min frequency considered")
    parser.add_argument("--freq-max", type=int, default=8000, help="Max frequency considered")

    args = parser.parse_args()
    add_songs(args)


if __name__ == "__main__":
    main()
