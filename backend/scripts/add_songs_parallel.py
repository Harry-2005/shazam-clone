"""
Parallel version of add_songs_to_database.py using multiprocessing.
Significantly faster by processing multiple songs simultaneously.

Usage:
    python add_songs_parallel.py --workers 4
    python add_songs_parallel.py --workers 8 --audio-dir ./youtube_songs
"""

import sys
import os
import argparse
from pathlib import Path
import re
from multiprocessing import Pool, cpu_count, Manager, current_process
from functools import partial
import time
import logging
from datetime import datetime

# Add parent directory to path for imports
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.fingerprint import AudioFingerprinter
from app.database import DatabaseManager


def clean_text(text):
    """Clean underscores and extra spaces."""
    text = text.replace('_', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_title_artist(filename: str):
    """
    Parse title and artist from filename using smart YouTube title parsing.
    
    Handles patterns like:
    - "Artist - Song Name Official Video" -> ("Song Name", "Artist")
    - "Artist feat. Artist2 - Song Name" -> ("Song Name", "Artist, Artist2")
    - "03. Artist - Song Name" -> ("Song Name", "Artist")
    - "Song Name by Artist" -> ("Song Name", "Artist")
    """
    base = Path(filename).stem
    text = clean_text(base)
    
    # Remove common YouTube suffixes
    patterns_to_remove = [
        r'\s*-?\s*Official\s+(Music\s+)?Video.*$',
        r'\s*-?\s*Official\s+Audio.*$',
        r'\s*-?\s*Lyric(al)?\s+Video.*$',
        r'\s*\(Official.*\).*$',
        r'\s*\[Official.*\].*$',
        r'\s*-?\s*Full\s+Video.*$',
        r'\s*-?\s*Full\s+Song.*$',
        r'\s*-?\s*4K.*$',
        r'\s*-?\s*HD.*$',
        r'\s*-?\s*New\s+Song.*$',
        r'\s*-?\s*Latest\s+Song.*$',
        r'\s*\d{4}.*$',  # Remove years at the end
    ]
    
    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    text = text.strip()
    
    # Remove leading numbers and dots (like "03. " or "1. ")
    text = re.sub(r'^\d+\.\s*', '', text)
    
    # Try "by" separator first
    if ' by ' in text:
        parts = text.split(' by ', 1)
        title = parts[0].strip()
        artist = parts[1].strip()
        return title or "Unknown", artist or "Unknown"
    
    # Try " - " separator (most common pattern)
    if ' - ' in text:
        parts = text.split(' - ', 1)
        first_part = parts[0].strip()
        second_part = parts[1].strip() if len(parts) > 1 else ""
        
        # Check for featured artists in first part
        feat_match = re.search(r'\s+(ft\.?|feat\.?|featuring)\s+(.+)', first_part, re.IGNORECASE)
        if feat_match:
            main_artist = first_part[:feat_match.start()].strip()
            featured = feat_match.group(2).strip()
            artist = f"{main_artist}, {featured}"
        else:
            artist = first_part
        
        song_name = second_part
        
        # If second part is empty or very short, might be wrong direction
        if not song_name or len(song_name) < 3:
            return (first_part, "Unknown")
        
        return (song_name, artist)
    
    # No separator found - treat entire name as title
    return text or "Unknown", "Unknown"


def iter_audio_files(audio_dir: Path):
    """Recursively find all audio files in directory."""
    exts = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".opus", ".webm"}
    for path in sorted(audio_dir.rglob("*")):
        if path.suffix.lower() in exts:
            yield path


def process_single_song(audio_path, args, counter, lock):
    """
    Process a single song (fingerprint and add to database).
    This function is called by multiple processes in parallel.
    
    Args:
        audio_path: Path to audio file
        args: Arguments containing database URL and fingerprinting params
        counter: Shared counter for progress tracking
        lock: Lock for thread-safe counter updates
        
    Returns:
        Tuple: (status, message) where status is 'added', 'skipped', or 'failed'
    """
    # Get worker ID for tracking
    worker_name = current_process().name
    worker_id = worker_name.split('-')[-1] if '-' in worker_name else '0'
    
    # Setup worker-specific logging
    log_file = Path(args.audio_dir).parent / f"worker_{worker_id}.log"
    
    def log_worker(msg):
        """Log to both worker file and return message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {msg}\n")
        return msg
    
    try:
        # Initialize fingerprinter (each process needs its own)
        fp = AudioFingerprinter(
            sample_rate=args.sample_rate,
            n_fft=args.n_fft,
            hop_length=args.hop_length,
            freq_min=args.freq_min,
            freq_max=args.freq_max,
        )
        
        # Initialize database connection (each process needs its own)
        db = DatabaseManager(database_url=args.database_url)
        
        try:
            # Generate fingerprints
            hashes = fp.fingerprint_file(str(audio_path))
            
            if not hashes:
                with lock:
                    counter.value += 1
                    current = counter.value
                return ('failed', f"[Worker-{worker_id}] [{current}/{counter.total}] {audio_path.name}: No fingerprints generated")
            
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
            
            with lock:
                counter.value += 1
                current = counter.value
            
            if song_id:
                msg = f"[Worker-{worker_id}] [{current}/{counter.total}] ✓ '{title}' by {artist} (ID: {song_id}, {len(hashes)} fps)"
                return ('added', log_worker(msg))
            else:
                msg = f"[Worker-{worker_id}] [{current}/{counter.total}] Already exists: {title}"
                return ('skipped', log_worker(msg))
        finally:
            # Always close database connection to avoid "too many clients" error
            db.close()
            
    except Exception as exc:
        with lock:
            counter.value += 1
            current = counter.value
        return ('failed', f"[Worker-{worker_id}] [{current}/{counter.total}] ✗ Error: {str(exc)[:100]}")


def add_songs_parallel(args):
    """Add all songs from directory to database using parallel processing."""
    audio_dir = Path(args.audio_dir).resolve()

    if not audio_dir.exists():
        raise SystemExit(f"Audio directory not found: {audio_dir}")

    # Find all audio files
    audio_files = list(iter_audio_files(audio_dir))
    if not audio_files:
        print(f"No audio files found in {audio_dir}")
        return

    print(f"Found {len(audio_files)} audio files")
    print(f"Audio directory: {audio_dir}")
    print(f"Database: {os.getenv('DATABASE_URL', 'default')}")
    print(f"Workers: {args.workers}")
    print(f"Processing songs in parallel...")
    print("=" * 60)

    # Track statistics
    stats = {
        'total': len(audio_files),
        'added': 0,
        'skipped': 0,
        'failed': 0
    }

    # Create shared counter for progress tracking
    manager = Manager()
    counter = manager.Namespace()
    counter.value = 0
    counter.total = len(audio_files)
    lock = manager.Lock()

    # Create partial function with fixed args
    process_func = partial(process_single_song, args=args, counter=counter, lock=lock)

    # Process songs in parallel with real-time progress
    start_time = time.time()
    
    print()
    
    with Pool(processes=args.workers) as pool:
        # Use imap_unordered for real-time results
        for status, message in pool.imap_unordered(process_func, audio_files, chunksize=1):
            print(message)
            stats[status] += 1
    
    elapsed_time = time.time() - start_time

    # Print separator after results
    print()
    print("=" * 60)

    # Print summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {stats['total']}")
    print(f"Successfully added:    {stats['added']}")
    print(f"Skipped (duplicates):  {stats['skipped']}")
    print(f"Failed:                {stats['failed']}")
    print(f"Total time:            {elapsed_time:.1f}s ({elapsed_time/60:.1f} minutes)")
    print(f"Average per song:      {elapsed_time/len(audio_files):.2f}s")
    print()
    
    if stats['added'] > 0:
        print(f"✓ Successfully added {stats['added']} songs to the database!")
    if stats['skipped'] > 0:
        print(f"⏭️  Skipped {stats['skipped']} duplicates")
    if stats['failed'] > 0:
        print(f"⚠ {stats['failed']} files failed to process")


def main():
    """Main entry point with argument parsing."""
    default_audio_dir = Path(__file__).resolve().parents[2] / "youtube_songs"
    default_workers = 3  # Reduced to avoid PostgreSQL connection limit

    parser = argparse.ArgumentParser(
        description="Add songs from directory to database in parallel (FAST version)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use 4 workers (recommended for most systems)
  python add_songs_parallel.py --workers 4
  
  # Use 8 workers for faster processing (if you have enough CPU cores)
  python add_songs_parallel.py --workers 8
  
  # Process specific directory
  python add_songs_parallel.py --workers 6 --audio-dir ./youtube_songs
  
  # Use auto-detected CPU count (capped at 8)
  python add_songs_parallel.py --workers auto
        """
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
    parser.add_argument(
        "--workers",
        type=str,
        default=str(default_workers),
        help=f"Number of parallel workers (default: {default_workers}, use 'auto' for CPU count)"
    )
    
    # Fingerprinting parameters (defaults match current configuration)
    parser.add_argument("--sample-rate", type=int, default=22050, help="Fingerprint sample rate")
    parser.add_argument("--n-fft", type=int, default=2048, help="FFT window size")
    parser.add_argument("--hop-length", type=int, default=512, help="STFT hop length")
    parser.add_argument("--freq-min", type=int, default=20, help="Min frequency considered")
    parser.add_argument("--freq-max", type=int, default=8000, help="Max frequency considered")

    args = parser.parse_args()
    
    # Parse workers argument
    if args.workers.lower() == 'auto':
        args.workers = default_workers
    else:
        args.workers = int(args.workers)
        if args.workers < 1:
            parser.error("Number of workers must be at least 1")
        if args.workers > 16:
            print(f"⚠️  Warning: {args.workers} workers is very high and may overwhelm the database")
    
    add_songs_parallel(args)


if __name__ == "__main__":
    main()
