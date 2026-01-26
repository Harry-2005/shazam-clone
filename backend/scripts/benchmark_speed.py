"""
Quick benchmark to measure identification speed improvements
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DatabaseManager
from app.fingerprint import AudioFingerprinter
import time
import random

def benchmark_identification():
    """Test identification speed with current optimizations"""
    
    db_manager = DatabaseManager()
    fingerprinter = AudioFingerprinter()
    
    # Get a random song to test against
    session = db_manager.get_session()
    from app.models import Song
    songs = session.query(Song).limit(10).all()
    
    if not songs:
        print("No songs in database to test!")
        return
    
    test_song = random.choice(songs)
    print(f"Testing with: {test_song.title} by {test_song.artist}")
    print(f"Song ID: {test_song.id}")
    
    # Get fingerprints for this song from database
    from app.models import Fingerprint
    song_fingerprints = session.query(
        Fingerprint.hash_value, 
        Fingerprint.time_offset
    ).filter(
        Fingerprint.song_id == test_song.id
    ).limit(500).all()  # Simulate 500 fps from recording
    
    session.close()
    
    if not song_fingerprints:
        print("No fingerprints found!")
        return
    
    # Convert to list of tuples
    query_fingerprints = [(fp.hash_value, fp.time_offset) for fp in song_fingerprints]
    
    print(f"\n{'='*60}")
    print(f"SPEED BENCHMARK")
    print(f"{'='*60}")
    print(f"Query fingerprints: {len(query_fingerprints)}")
    
    # Test 1: Full matching
    print(f"\nTest 1: Full matching algorithm")
    start = time.time()
    result = db_manager.find_matches(query_fingerprints)
    duration = time.time() - start
    
    if result:
        print(f"✅ Match found: {result['title']} by {result['artist']}")
        print(f"⏱️  Time taken: {duration:.2f}s")
        print(f"🎯 Confidence: {result['confidence']} fingerprints ({result['confidence_percentage']:.1f}%)")
    else:
        print(f"❌ No match found")
        print(f"⏱️  Time taken: {duration:.2f}s")
    
    # Speed targets
    print(f"\n{'='*60}")
    print(f"PERFORMANCE TARGETS")
    print(f"{'='*60}")
    print(f"🎯 Target: < 5s for web app (includes fingerprint generation)")
    print(f"🎯 Target: < 2s for matching only")
    
    if duration < 2:
        print(f"✅ EXCELLENT: {duration:.2f}s - Faster than target!")
    elif duration < 5:
        print(f"✅ GOOD: {duration:.2f}s - Within target")
    else:
        print(f"⚠️  SLOW: {duration:.2f}s - Needs optimization")
    
    print(f"\n{'='*60}")
    print(f"OPTIMIZATIONS APPLIED")
    print(f"{'='*60}")
    print(f"✅ Reduced query fingerprints: 400 → 300")
    print(f"✅ Disabled audio preprocessing (skip trim/normalize)")
    print(f"✅ Faster resampling: kaiser_fast method")
    print(f"✅ Early exit on strong match (>150 fingerprints)")
    print(f"✅ Reduced target zone: 75 → 50 frames")
    print(f"✅ Optimized peak sorting (in-place)")
    print(f"✅ Frontend: Auto-stop at 15 seconds")

if __name__ == "__main__":
    benchmark_identification()
