"""
Clean song names in the database by removing video-related terms.
Applies the same cleaning logic as rename_songs_from_metadata.py
"""

import sys
import os
import re
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import DatabaseManager
from sqlalchemy import text


def remove_video_terms(text_input: str) -> str:
    """Remove common video/song-related terms from title."""
    if not text_input:
        return text_input
    
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
        text_input = re.sub(term, '', text_input, flags=re.IGNORECASE)
    
    # Remove multiple spaces and clean up
    text_input = re.sub(r'\s+', ' ', text_input)
    text_input = text_input.strip(' -_|')
    
    return text_input


def clean_database_song_names(dry_run: bool = False):
    """Clean song names in the database by removing video-related terms."""
    
    db = DatabaseManager()
    
    try:
        # Get all songs
        session = db.get_session()
        try:
            result = session.execute(text("SELECT id, title, artist FROM songs ORDER BY id"))
            songs = result.fetchall()
            
            if not songs:
                print("No songs found in database.")
                return
            
            print(f"Found {len(songs)} songs in database")
            
            if dry_run:
                print("\n=== DRY RUN MODE - No changes will be made ===\n")
            else:
                print()
            
            updated_count = 0
            unchanged_count = 0
            
            for song in songs:
                song_id, title, artist = song
                
                # Clean the title
                cleaned_title = remove_video_terms(title)
                
                if cleaned_title != title:
                    print(f"[{song_id}] {artist}")
                    print(f"  Old: {title}")
                    print(f"  New: {cleaned_title}")
                    
                    if not dry_run:
                        # Update the database
                        session.execute(
                            text("UPDATE songs SET title = :new_title WHERE id = :song_id"),
                            {"new_title": cleaned_title, "song_id": song_id}
                        )
                        session.commit()
                        print("  * Updated")
                    else:
                        print("  > Would update")
                    
                    print()
                    updated_count += 1
                else:
                    unchanged_count += 1
            
            print("=" * 60)
            print("Summary:")
            print(f"  Updated: {updated_count}")
            print(f"  Unchanged: {unchanged_count}")
            print(f"  Total: {len(songs)}")
            
            if dry_run:
                print("\nRun without --dry-run to actually update the database")
        finally:
            session.close()
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean song names in the database by removing video-related terms"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without actually updating the database"
    )
    
    args = parser.parse_args()
    
    clean_database_song_names(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
