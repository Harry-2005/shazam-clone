"""
Rename audio files based on their embedded metadata.
Extracts artist and title from MP3 tags and renames files to: "Artist - Title.mp3"
"""

import sys
import os
from pathlib import Path
import re

# Set UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')

# Try to import mutagen for metadata reading
try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3
except ImportError:
    print("Error: mutagen library not found. Install it with: pip install mutagen")
    sys.exit(1)


def remove_video_terms(text: str) -> str:
    """Remove common video/song-related terms from title."""
    if not text:
        return text
    
    # Terms to remove (case insensitive)
    terms_to_remove = [
        r'\bofficial\s+video\b',
        r'\bofficial\s+music\s+video\b',
        r'\bfull\s+video\b',
        r'\bfull\s+song\b',
        r'\bfull\s+audio\b',
        r'\bvideo\s+song\b',
        r'\baudio\s+song\b',
        r'\blyric\s+video\b',
        r'\blyrical\s+video\b',
        r'\blyrical\s+song\b',
        r'\bbest\s+video\b',
        r'\bbest\s+audio\b',
        r'\bbest\s+song\b',
        r'\bmusic\s+video\b',
        r'\btitle\s+track\b',
        r'\btitle\s+song\b',
        r'\bwith\s+lyrics\b',
        r'\bfeat\.\b',
        r'\bfeaturing\b',
        r'\bft\.\b',
    ]
    
    for term in terms_to_remove:
        text = re.sub(term, '', text, flags=re.IGNORECASE)
    
    # Remove multiple spaces and clean up
    text = re.sub(r'\s+', ' ', text)
    text = text.strip(' -_|')
    
    return text


def clean_filename(text: str) -> str:
    """Clean text to be filesystem-safe."""
    if not text:
        return "Unknown"
    
    # Replace problematic characters
    replacements = {
        '/': '_',
        '\\': '_',
        ':': '_',
        '*': '_',
        '?': '_',
        '"': '_',
        '<': '_',
        '>': '_',
        '|': '_',
        '\n': ' ',
        '\r': ' ',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing spaces and dots
    text = text.strip('. ')
    
    return text or "Unknown"


def get_metadata(file_path: Path):
    """Extract artist and title from MP3 metadata."""
    try:
        audio = MP3(file_path, ID3=ID3)
        
        # Try to get artist
        artist = None
        if 'TPE1' in audio.tags:  # Lead artist
            artist = str(audio.tags['TPE1'])
        elif 'TPE2' in audio.tags:  # Album artist
            artist = str(audio.tags['TPE2'])
        
        # Try to get title
        title = None
        if 'TIT2' in audio.tags:  # Title
            title = str(audio.tags['TIT2'])
        
        return artist, title
        
    except Exception as e:
        print(f"  Error reading metadata: {e}")
        return None, None


def rename_songs(directory: str, dry_run: bool = False):
    """Rename all audio files in directory based on metadata."""
    
    directory = Path(directory).resolve()
    
    if not directory.exists():
        print(f"Error: Directory not found: {directory}")
        return
    
    # Supported audio extensions
    audio_extensions = {'.mp3', '.m4a', '.flac', '.wav', '.ogg'}
    
    files = [f for f in directory.iterdir() 
             if f.is_file() and f.suffix.lower() in audio_extensions]
    
    if not files:
        print(f"No audio files found in: {directory}")
        return
    
    print(f"Found {len(files)} audio files")
    print(f"Directory: {directory}")
    
    if dry_run:
        print("\n=== DRY RUN MODE - No files will be renamed ===\n")
    else:
        print()
    
    renamed_count = 0
    skipped_count = 0
    
    for file_path in files:
        print(f"Processing: {file_path.name}")
        
        # Get metadata
        artist, title = get_metadata(file_path)
        
        if not artist or not title:
            print(f"  ⚠ Skipped: Missing metadata (artist: {artist}, title: {title})")
            skipped_count += 1
            continue
        
        # Remove video terms from title
        title = remove_video_terms(title)
        
        # Clean the metadata
        artist_clean = clean_filename(artist)
        title_clean = clean_filename(title)
        
        # Create new filename
        new_name = f"{title_clean} - {artist_clean}{file_path.suffix}"
        new_path = file_path.parent / new_name
        
        # Check if file already has the correct name
        if file_path.name == new_name:
            print(f"  ✓ Already correctly named")
            continue
        
        # Check if target file already exists
        if new_path.exists():
            print(f"  ⚠ Skipped: Target file already exists: {new_name}")
            skipped_count += 1
            continue
        
        # Rename the file
        if dry_run:
            print(f"  → Would rename to: {new_name}")
            renamed_count += 1
        else:
            try:
                file_path.rename(new_path)
                print(f"  ✓ Renamed to: {new_name}")
                renamed_count += 1
            except Exception as e:
                print(f"  ✗ Error renaming: {e}")
                skipped_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  Renamed: {renamed_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total: {len(files)}")
    
    if dry_run:
        print(f"\nRun without --dry-run to actually rename files")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Rename audio files based on their metadata"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default="youtube_songs/New songs",
        help="Directory containing audio files (default: youtube_songs/New songs)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without actually renaming"
    )
    
    args = parser.parse_args()
    
    rename_songs(args.directory, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
