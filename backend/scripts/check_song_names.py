"""
Check current song names in database to understand the naming patterns.
"""

import sys
import os
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.database import DatabaseManager

def main():
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        from app.models import Song
        songs = session.query(Song).limit(50).all()
        
        print(f"Found {len(songs)} songs (showing first 50)\n")
        print("=" * 80)
        
        for song in songs:
            print(f"ID: {song.id}")
            print(f"Title: {song.title}")
            print(f"Artist: {song.artist}")
            print("-" * 80)
            
    finally:
        session.close()

if __name__ == "__main__":
    main()
