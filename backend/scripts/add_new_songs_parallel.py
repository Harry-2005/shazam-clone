"""
Add songs from New songs directory with renamed files (Title - Artist format).
Uses parallel processing for faster uploads.

Usage:
    python add_new_songs_parallel.py --workers 4
    python add_new_songs_parallel.py --workers 8 --audio-dir "./youtube_songs/New songs"
"""

import sys
import os
import argparse
from pathlib import Path
import re
from multiprocessing import Pool, cpu_count, Manager
from functools import partial
import time
from datetime import datetime

# Add parent directory to path for imports
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.fingerprint import AudioFingerprinter
from app.database import DatabaseManager


def parse_renamed_filename(filename: str):
    """
    Parse title and artist from renamed filename in "Title - Artist" format.
    
    Examples:
    - "Chikni Chameli - Sony Music India.mp3" -> ("Chikni Chameli", "Sony Music India")
    - "Tum Hi Ho - Arijit Singh.mp3" -> ("Tum Hi Ho", "Arijit Singh")
    """
    base = Path(filename).stem
    
    # Split by " - " to get title and artist
    if ' - ' in base:
        parts = base.split(' - ', 1)
        title = parts[0].strip()
        artist = parts[1].strip() if len(parts) > 1 else "Unknown"
        return title or "Unknown", artist or "Unknown"
    else:
        # Fallback: use filename as title
        return base.strip() or "Unknown", "Unknown"


def process_song(filepath, counter, lock, skipped_files):
    """
    Process a single song file.
    
    Args:
        filepath: Path to audio file
        counter: Shared counter for progress tracking
        lock: Lock for thread-safe counter updates
        skipped_files: Shared list for tracking skipped files
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        fingerprinter = AudioFingerprinter()
        db = DatabaseManager()
        
        # Parse title and artist from filename
        title, artist = parse_renamed_filename(filepath.name)
        
        # Generate fingerprints
        fingerprints = fingerprinter.fingerprint_file(str(filepath))
        
        if not fingerprints:
            with lock:
                skipped_files.append((str(filepath), "No fingerprints generated"))
            return False, f"No fingerprints: {filepath.name}"
        
        # Add to database
        song_id = db.add_song(
            title=title,
            artist=artist,
            fingerprints=fingerprints,
            filepath=str(filepath)
        )
        
        # Update counter
        with lock:
            counter.value += 1
            count = counter.value
        
        db.close()
        
        return True, f"[{count}] Added: {title} - {artist}"
        
    except Exception as e:
        error_msg = f"Error processing {filepath.name}: {str(e)}"
        with lock:
            skipped_files.append((str(filepath), str(e)))
        return False, error_msg


def get_audio_files(directory: str):
    """Get all audio files from directory and subdirectories."""
    audio_dir = Path(directory)
    
    if not audio_dir.exists():
        raise ValueError(f"Directory not found: {audio_dir}")
    
    # Audio file extensions
    audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.ogg'}
    
    # Get all audio files recursively
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(audio_dir.rglob(f'*{ext}'))
    
    return sorted(audio_files)


def main():
    parser = argparse.ArgumentParser(
        description='Add songs to database in parallel (from renamed files with Title - Artist format)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )
    parser.add_argument(
        '--audio-dir',
        type=str,
        default='./youtube_songs/New songs',
        help='Directory containing audio files (default: ./youtube_songs/New songs)'
    )
    
    args = parser.parse_args()
    
    # Validate workers
    max_workers = cpu_count()
    if args.workers > max_workers:
        print(f"Warning: {args.workers} workers requested but only {max_workers} CPUs available")
        print(f"Using {max_workers} workers instead")
        args.workers = max_workers
    
    print(f"\n{'='*60}")
    print(f"Parallel Song Upload (Renamed Files - Title - Artist format)")
    print(f"{'='*60}")
    print(f"Workers: {args.workers}")
    print(f"Directory: {args.audio_dir}")
    print(f"{'='*60}\n")
    
    # Get audio files
    print("Scanning for audio files...")
    try:
        audio_files = get_audio_files(args.audio_dir)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    if not audio_files:
        print(f"No audio files found in {args.audio_dir}")
        return 1
    
    print(f"Found {len(audio_files)} audio files\n")
    
    # Ask for confirmation
    response = input(f"Upload {len(audio_files)} songs using {args.workers} workers? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return 0
    
    print(f"\nStarting parallel upload with {args.workers} workers...")
    print("This may take a while...\n")
    
    # Track progress
    manager = Manager()
    counter = manager.Value('i', 0)
    lock = manager.Lock()
    skipped_files = manager.list()
    
    # Start timing
    start_time = time.time()
    
    # Create partial function with shared objects
    process_func = partial(
        process_song,
        counter=counter,
        lock=lock,
        skipped_files=skipped_files
    )
    
    # Process in parallel
    successful = 0
    failed = 0
    
    with Pool(processes=args.workers) as pool:
        results = pool.map(process_func, audio_files)
        
        # Count results
        for success, message in results:
            if success:
                successful += 1
                print(message)
            else:
                failed += 1
                print(f"✗ {message}")
    
    # Calculate timing
    elapsed_time = time.time() - start_time
    avg_time = elapsed_time / len(audio_files) if audio_files else 0
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Upload Complete!")
    print(f"{'='*60}")
    print(f"Total files: {len(audio_files)}")
    print(f"Successfully added: {successful}")
    print(f"Failed: {failed}")
    print(f"Total time: {elapsed_time:.1f}s")
    print(f"Average time per song: {avg_time:.2f}s")
    print(f"{'='*60}")
    
    # Show skipped files
    if skipped_files:
        print(f"\nSkipped files ({len(skipped_files)}):")
        for filepath, reason in skipped_files[:10]:  # Show first 10
            print(f"  - {Path(filepath).name}: {reason}")
        if len(skipped_files) > 10:
            print(f"  ... and {len(skipped_files) - 10} more")
    
    print("\nRemember to rebuild indexes:")
    print("  python scripts/optimize_bulk_insert.py --rebuild")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
