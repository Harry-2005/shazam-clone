"""
Fix reversed title/artist fields in database.
Many songs have artist in title field and song name in artist field due to YouTube parsing issues.
"""

import sys
import os
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager
from app.models import Song


def clean_text(text):
    """Clean underscores and extra spaces."""
    text = text.replace('_', ' ')
    import re
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_youtube_title(title):
    """
    Parse YouTube-style title to extract song name and artist.
    
    Handles patterns like:
    - "Artist - Song Name Official Video" -> ("Song Name", "Artist")
    - "Artist feat. Artist2 - Song Name" -> ("Song Name", "Artist, Artist2")
    - "Song Name Official Video" -> ("Song Name", "Unknown")
    """
    import re
    
    # Clean first
    text = clean_text(title)
    
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
    
    # Try to split by " - " (most common pattern)
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
    
    # No separator found - return as-is with Unknown artist
    return (text, "Unknown")


def fix_database(dry_run=True):
    """Fix reversed title/artist and clean up names."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        songs = session.query(Song).all()
        
        print(f"Analyzing {len(songs)} songs...")
        print("=" * 80)
        
        changes = []
        
        for song in songs:
            title_raw = song.title
            artist_raw = song.artist
            
            # Skip songs that are already clean (first 11 IDs)
            if song.id <= 11:
                continue
            
            # Special handling for "NA" artist - parse the YouTube title
            if artist_raw == "NA" or artist_raw == "Unknown":
                # Title contains the full YouTube title, parse it
                parsed_song, parsed_artist = parse_youtube_title(title_raw)
                new_title = parsed_song
                new_artist = parsed_artist
            else:
                # Clean underscores from both fields
                title_clean = clean_text(title_raw)
                artist_clean = clean_text(artist_raw)
                
                # Check if fields are likely reversed:
                # - Title field has underscores or multiple names (looks like artist)
                # - Artist field is short and looks like a song title
                title_has_underscores = '_' in title_raw
                title_looks_like_artists = ',' in title_clean or len(title_clean.split()) >= 3
                artist_is_short = len(artist_clean.split()) <= 4
                
                # Decision: Should we swap?
                should_swap = False
                
                if title_has_underscores and artist_is_short:
                    # Very likely reversed: "Anuv_Jain" (title) vs "Husn" (artist)
                    should_swap = True
                elif title_looks_like_artists and artist_is_short and ',' not in artist_clean:
                    # Title looks like multiple artists, artist looks like a song name
                    should_swap = True
                
                if should_swap:
                    # Swap and clean
                    new_title = artist_clean
                    new_artist = title_clean
                else:
                    # Just clean
                    new_title = title_clean
                    new_artist = artist_clean
            
            # Track changes
            if new_title != title_raw or new_artist != artist_raw:
                changes.append({
                    'id': song.id,
                    'old_title': title_raw,
                    'old_artist': artist_raw,
                    'new_title': new_title,
                    'new_artist': new_artist,
                    'swapped': artist_raw != "NA" and artist_raw != "Unknown"
                })
        
        # Display changes
        print(f"\nFound {len(changes)} songs that need fixing:\n")
        
        for change in changes[:100]:  # Show first 100
            swap_marker = "[SWAPPED]" if change['swapped'] else "[CLEANED]"
            print(f"ID {change['id']} {swap_marker}:")
            print(f"  Old: \"{change['old_title']}\" by {change['old_artist']}")
            print(f"  New: \"{change['new_title']}\" by {change['new_artist']}")
            print()
        
        if len(changes) > 100:
            print(f"... and {len(changes) - 100} more\n")
        
        # Statistics
        swapped = sum(1 for c in changes if c['swapped'])
        cleaned = len(changes) - swapped
        print(f"\nStatistics:")
        print(f"  Swapped (title <-> artist): {swapped}")
        print(f"  Cleaned (underscores):      {cleaned}")
        print(f"  Total changes:              {len(changes)}")
        
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
    parser = argparse.ArgumentParser(description='Fix reversed title/artist in database')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually apply changes (default is dry-run)')
    args = parser.parse_args()
    
    fix_database(dry_run=not args.execute)


if __name__ == "__main__":
    main()
