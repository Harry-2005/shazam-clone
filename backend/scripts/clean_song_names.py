"""
Smart song name cleaner for database.
Handles inconsistent YouTube naming patterns and fixes reversed title/artist entries.

Patterns handled:
- "Artist - Song Title Official Video" -> "Song Title" by "Artist"
- "Song Title ft. Artist 1, Artist 2" -> "Song Title" by "Artist 1, Artist 2"
- Removes: Official Video, Official Music Video, Lyric Video, Audio, etc.
- Cleans underscores to spaces
- Extracts featured artists (ft., feat., featuring)
"""

import sys
import os
import re
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager
from app.models import Song


def clean_text(text):
    """Basic text cleaning: underscores to spaces, strip extra spaces."""
    text = text.replace('_', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def remove_common_suffixes(text):
    """Remove common YouTube video suffixes."""
    suffixes = [
        r'\s*[-|]\s*Official\s*(Music\s*)?Video.*$',
        r'\s*[-|]\s*Official\s*Audio.*$',
        r'\s*[-|]\s*Lyric(al)?\s*Video.*$',
        r'\s*[-|]\s*Official\s*Lyric(al)?.*$',
        r'\s*\(Official\s*(Music\s*)?Video\).*$',
        r'\s*\(Official\s*Audio\).*$',
        r'\s*\(Lyric(al)?\s*Video\).*$',
        r'\s*\[Official.*\].*$',
        r'\s*[-|]\s*Full\s*Video.*$',
        r'\s*[-|]\s*Full\s*Song.*$',
        r'\s*\(Full\s*Video\).*$',
        r'\s*\(Full\s*Song\).*$',
        r'\s*[-|]\s*4K.*$',
        r'\s*[-|]\s*HD.*$',
    ]
    
    for pattern in suffixes:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()


def extract_featured_artists(text):
    """
    Extract featured artists from text like "Song ft. Artist1, Artist2".
    Returns (main_text, featured_artists)
    """
    # Patterns for featured artists
    patterns = [
        r'\s+ft\.?\s+(.+)$',
        r'\s+feat\.?\s+(.+)$',
        r'\s+featuring\s+(.+)$',
        r'\s+ft\s+(.+)$',
        r'\s+feat\s+(.+)$',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            featured = match.group(1).strip()
            main_text = text[:match.start()].strip()
            return main_text, featured
    
    return text, None


def parse_youtube_title(raw_text):
    """
    Parse YouTube title to extract song name and artists.
    Returns (song_title, artist_string)
    
    Examples:
    "Artist - Song Title Official Video" -> ("Song Title", "Artist")
    "Song ft. Artist1, Artist2" -> ("Song", "Artist1, Artist2")
    "Artist1, Artist2 - Song Title" -> ("Song Title", "Artist1, Artist2")
    """
    # Clean the text
    text = clean_text(raw_text)
    text = remove_common_suffixes(text)
    
    # Try to split by " - " or similar separators
    separators = [' - ', ' – ', ' — ', '|']
    parts = None
    
    for sep in separators:
        if sep in text:
            parts = [p.strip() for p in text.split(sep, 1)]
            break
    
    if not parts or len(parts) < 2:
        # No separator found, try to extract featured artists
        main_text, featured = extract_featured_artists(text)
        if featured:
            return main_text, featured
        # Return as-is
        return text, "Unknown"
    
    first_part, second_part = parts[0], parts[1]
    
    # Remove common suffixes from second part
    second_part = remove_common_suffixes(second_part)
    
    # Check for featured artists in second part
    second_part, featured = extract_featured_artists(second_part)
    
    # Heuristics to determine which is song and which is artist:
    # 1. If first part has commas or multiple names, it's likely artists
    # 2. If first part is shorter and second is longer, first is likely artist
    # 3. If second part has commas, those are likely multiple artists
    
    # Count indicators
    first_has_commas = ',' in first_part
    second_has_commas = ',' in second_part
    first_word_count = len(first_part.split())
    second_word_count = len(second_part.split())
    
    # Decision logic
    if first_has_commas and not second_has_commas:
        # "Artist1, Artist2 - Song" pattern
        song_title = second_part
        artists = first_part
    elif first_word_count <= 3 and second_word_count > 3:
        # "Artist - Long Song Title" pattern
        song_title = second_part
        artists = first_part
    elif second_has_commas:
        # "Song - Artist1, Artist2" pattern
        song_title = first_part
        artists = second_part
    elif len(first_part) < len(second_part) * 0.6:
        # First part is much shorter - likely artist
        song_title = second_part
        artists = first_part
    else:
        # Default: assume "Song - Artist" pattern
        song_title = first_part
        artists = second_part
    
    # Add featured artists if found
    if featured:
        if artists and artists != "Unknown":
            artists = f"{artists}, {featured}"
        else:
            artists = featured
    
    return song_title, artists if artists else "Unknown"


def preview_changes(dry_run=True):
    """Preview or apply song name cleaning."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        songs = session.query(Song).all()
        
        print(f"Processing {len(songs)} songs...")
        print("=" * 80)
        
        changes = []
        
        for song in songs:
            # Try parsing both title and artist to see which one has the messy YouTube text
            title_raw = song.title
            artist_raw = song.artist
            
            # Check if title or artist looks like a YouTube title (has underscores, long, etc)
            title_is_messy = '_' in title_raw or len(title_raw) > 50
            artist_is_messy = '_' in artist_raw or len(artist_raw) > 50
            
            # Parse the messy field
            if title_is_messy or artist_is_messy:
                # Use the messier field as the source
                if title_is_messy and len(title_raw) >= len(artist_raw):
                    source = title_raw
                elif artist_is_messy and len(artist_raw) >= len(title_raw):
                    source = artist_raw
                else:
                    source = title_raw
                
                new_title, new_artist = parse_youtube_title(source)
            else:
                # Both fields look clean, just clean them up slightly
                new_title = clean_text(title_raw)
                new_artist = clean_text(artist_raw) if artist_raw != "Unknown" else artist_raw
            
            # Check if changes are needed
            if new_title != title_raw or new_artist != artist_raw:
                changes.append({
                    'id': song.id,
                    'old_title': title_raw,
                    'old_artist': artist_raw,
                    'new_title': new_title,
                    'new_artist': new_artist
                })
        
        # Display changes
        print(f"\nFound {len(changes)} songs that need cleaning:\n")
        
        for change in changes[:50]:  # Show first 50
            print(f"ID {change['id']}:")
            print(f"  Old: \"{change['old_title']}\" by {change['old_artist']}")
            print(f"  New: \"{change['new_title']}\" by {change['new_artist']}")
            print()
        
        if len(changes) > 50:
            print(f"... and {len(changes) - 50} more\n")
        
        # Apply changes if not dry run
        if not dry_run:
            print("\nApplying changes...")
            for change in changes:
                song = session.query(Song).filter(Song.id == change['id']).first()
                if song:
                    song.title = change['new_title']
                    song.artist = change['new_artist']
            
            session.commit()
            print(f"✓ Updated {len(changes)} songs in database!")
        else:
            print(f"\n{'=' * 80}")
            print("DRY RUN - No changes made to database")
            print(f"Run with --execute flag to apply these changes")
            print(f"{'=' * 80}")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Clean song names in database')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually apply changes (default is dry-run)')
    args = parser.parse_args()
    
    preview_changes(dry_run=not args.execute)


if __name__ == "__main__":
    main()
