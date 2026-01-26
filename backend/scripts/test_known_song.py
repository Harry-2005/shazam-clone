"""
Test matching with a known song from the database
This verifies that the matching logic works correctly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DatabaseManager
from app.fingerprint import AudioFingerprinter
from app.models import Song, Fingerprint
import random

def test_known_song_matching():
    """Test matching using fingerprints from a song already in database"""
    
    db_manager = DatabaseManager()
    fingerprinter = AudioFingerprinter()
    session = db_manager.get_session()
    
    print("="*60)
    print("TESTING MATCHING LOGIC WITH KNOWN SONG")
    print("="*60)
    
    # Get a random song from database
    songs = session.query(Song).limit(50).all()
    if not songs:
        print("❌ No songs in database!")
        session.close()
        return
    
    test_song = random.choice(songs)
    print(f"\n1. Selected test song:")
    print(f"   ID: {test_song.id}")
    print(f"   Title: {test_song.title}")
    print(f"   Artist: {test_song.artist}")
    
    # Get fingerprints for this song
    song_fingerprints = session.query(
        Fingerprint.hash_value,
        Fingerprint.time_offset
    ).filter(
        Fingerprint.song_id == test_song.id
    ).limit(1000).all()  # Get 1000 fingerprints
    
    print(f"\n2. Retrieved {len(song_fingerprints)} fingerprints from database")
    
    if len(song_fingerprints) < 400:
        print(f"⚠️  Warning: Song only has {len(song_fingerprints)} fingerprints (need 400+ for good matching)")
    
    # Convert to query format
    query_fingerprints = [(fp.hash_value, fp.time_offset) for fp in song_fingerprints]
    
    # Test 1: Full fingerprints (should definitely match)
    print(f"\n3. Test 1: Using all {len(query_fingerprints)} fingerprints")
    print("   " + "-"*56)
    result = db_manager.find_matches(query_fingerprints)
    
    if result:
        print(f"   ✅ MATCHED: {result['title']} by {result['artist']}")
        print(f"   Song ID: {result['song_id']}")
        print(f"   Confidence: {result['confidence']} fingerprints ({result['confidence_percentage']:.1f}%)")
        print(f"   Alignment: {result['alignment_offset']}")
        
        if result['song_id'] == test_song.id:
            print(f"   ✅ CORRECT - Matched the right song!")
        else:
            print(f"   ❌ WRONG - Expected song {test_song.id}, got {result['song_id']}")
    else:
        print(f"   ❌ NO MATCH FOUND")
        print(f"   This indicates a problem with the matching logic!")
    
    # Test 2: Subset of fingerprints (simulate real recording)
    subset_size = 400
    if len(query_fingerprints) >= subset_size:
        # Take fingerprints from different parts of the song
        step = len(query_fingerprints) // subset_size
        subset_fingerprints = query_fingerprints[::step][:subset_size]
        
        print(f"\n4. Test 2: Using {len(subset_fingerprints)} sampled fingerprints (simulates recording)")
        print("   " + "-"*56)
        result = db_manager.find_matches(subset_fingerprints)
        
        if result:
            print(f"   ✅ MATCHED: {result['title']} by {result['artist']}")
            print(f"   Song ID: {result['song_id']}")
            print(f"   Confidence: {result['confidence']} fingerprints ({result['confidence_percentage']:.1f}%)")
            
            if result['song_id'] == test_song.id:
                print(f"   ✅ CORRECT - Matched the right song!")
            else:
                print(f"   ❌ WRONG - Expected song {test_song.id}, got {result['song_id']}")
        else:
            print(f"   ❌ NO MATCH FOUND")
            print(f"   This might indicate threshold is too high")
    
    # Test 3: Very small subset (stress test)
    small_subset = query_fingerprints[:100]
    print(f"\n5. Test 3: Using only {len(small_subset)} fingerprints (stress test)")
    print("   " + "-"*56)
    result = db_manager.find_matches(small_subset)
    
    if result:
        print(f"   ✅ MATCHED: {result['title']} by {result['artist']}")
        print(f"   Confidence: {result['confidence']} fingerprints ({result['confidence_percentage']:.1f}%)")
        if result['song_id'] == test_song.id:
            print(f"   ✅ CORRECT")
        else:
            print(f"   ❌ WRONG MATCH")
    else:
        print(f"   ❌ NO MATCH (expected - too few fingerprints)")
    
    session.close()
    
    print("\n" + "="*60)
    print("DIAGNOSIS:")
    print("="*60)
    print("If Test 1 passes: Matching logic works correctly")
    print("If Test 2 passes: Your recordings need 10+ seconds")
    print("If Test 1 fails: Check if fingerprint settings changed")
    print("="*60)

if __name__ == "__main__":
    test_known_song_matching()
