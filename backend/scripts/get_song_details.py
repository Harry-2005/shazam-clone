import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DatabaseManager

def get_song_details(song_id: int):
    db = DatabaseManager()
    song = db.get_song(song_id)
    
    if not song:
        print(f"\n❌ Song ID {song_id} not found in database")
        return
    
    print(f"\n{'='*60}")
    print(f"Song Details - ID {song.id}")
    print(f"{'='*60}")
    print(f"Title:       {song.title}")
    print(f"Artist:      {song.artist}")
    print(f"Album:       {song.album or 'N/A'}")
    print(f"Duration:    {song.duration:.2f}s" if song.duration else "Duration:    N/A")
    print(f"File Hash:   {song.file_hash[:32]}..." if song.file_hash else "File Hash:   N/A")
    print(f"Fingerprints: {len(song.fingerprints)}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    song_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    get_song_details(song_id)
