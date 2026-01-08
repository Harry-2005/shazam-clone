import sys
sys.path.append('..')

from app.database import DatabaseManager
from app.fingerprint import AudioFingerprinter
import os

def test_database():
    """Test database operations."""
    
    print("=== Database System Test ===\n")
    
    # Initialize
    db = DatabaseManager()
    fp = AudioFingerprinter()
    print("✓ Database and Fingerprinter initialized")
    
    # Check database stats
    stats = db.get_database_stats()
    print(f"\nCurrent database stats:")
    print(f"  Songs: {stats['total_songs']}")
    print(f"  Fingerprints: {stats['total_fingerprints']}")
    
    # Test adding a song
    test_file = "../../sample-songs/test_song.mp3"
    
    if not os.path.exists(test_file):
        print(f"\n✗ Test file not found: {test_file}")
        print("  Please place a test MP3 file at that location")
        return
    
    print(f"\n✓ Test file found: {test_file}")
    
    # Fingerprint the audio
    print("\nFingerprinting audio...")
    hashes = fp.fingerprint_file(test_file)
    print(f"✓ Generated {len(hashes)} fingerprints")
    
    # Add to database
    print("\nAdding song to database...")
    song_id = db.add_song(
        title="Dhurandhar - Title Track",
        artist="Shashwat Sachdev",
        album="Dhurandhar",
        fingerprints=hashes,
        filepath=test_file
    )
    print(f"✓ Song added with ID: {song_id}")
    
    # Verify it was added
    song = db.get_song(song_id)
    print(f"\nRetrieved song:")
    print(f"  Title: {song.title}")
    print(f"  Artist: {song.artist}")
    print(f"  Album: {song.album}")
    
    # Test matching (match against itself)
    print("\n--- Testing Matching ---")
    print("Attempting to match the same song...")
    
    # Use first 5 seconds of fingerprints as query
    query_prints = hashes[:200]  # Subset of fingerprints
    print(f"Query fingerprints: {len(query_prints)}")
    
    match_result = db.find_matches(query_prints)
    
    if match_result:
        print("\n✓ Match found!")
        print(f"  Song: {match_result['title']} by {match_result['artist']}")
        print(f"  Confidence: {match_result['confidence']} matching fingerprints")
        print(f"  Match rate: {match_result['confidence']/len(query_prints)*100:.1f}%")
    else:
        print("\n✗ No match found")
    
    # Show updated stats
    stats = db.get_database_stats()
    print(f"\nUpdated database stats:")
    print(f"  Songs: {stats['total_songs']}")
    print(f"  Fingerprints: {stats['total_fingerprints']}")
    print(f"  Avg fingerprints per song: {stats['avg_fingerprints_per_song']:.0f}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_database()