"""
Detailed diagnostic for analyzing actual recording files
Shows exactly what's happening during fingerprinting and matching
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DatabaseManager
from app.fingerprint import AudioFingerprinter
import librosa

def diagnose_recording(recording_path: str):
    """Analyze a recording file and diagnose matching issues"""
    
    if not os.path.exists(recording_path):
        print(f"❌ File not found: {recording_path}")
        return
    
    print("="*60)
    print("RECORDING DIAGNOSTIC ANALYSIS")
    print("="*60)
    print(f"File: {recording_path}")
    
    fingerprinter = AudioFingerprinter()
    db_manager = DatabaseManager()
    
    # Step 1: Analyze audio file
    print("\n1. Audio File Analysis:")
    print("   " + "-"*56)
    try:
        # Get duration and sample rate
        duration = librosa.get_duration(path=recording_path)
        y, sr = librosa.load(recording_path, sr=None)
        
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Sample Rate: {sr} Hz")
        print(f"   Audio samples: {len(y):,}")
        
        if duration < 5:
            print(f"   ⚠️  WARNING: Recording is very short (< 5 seconds)")
            print(f"      Recommendation: Record 10-15 seconds")
        elif duration < 10:
            print(f"   ⚠️  WARNING: Recording is short (< 10 seconds)")
            print(f"      May have difficulty matching")
        else:
            print(f"   ✅ Duration is good")
        
        # Check audio levels
        max_amplitude = abs(y).max()
        rms_level = (y**2).mean()**0.5
        print(f"   Max amplitude: {max_amplitude:.4f}")
        print(f"   RMS level: {rms_level:.4f}")
        
        if max_amplitude < 0.1:
            print(f"   ⚠️  WARNING: Audio is very quiet")
            print(f"      Try recording with higher volume")
        elif rms_level < 0.01:
            print(f"   ⚠️  WARNING: Low signal level")
        else:
            print(f"   ✅ Audio levels look good")
            
    except Exception as e:
        print(f"   ❌ Error analyzing audio: {e}")
        return
    
    # Step 2: Generate fingerprints WITHOUT preprocessing
    print("\n2. Fingerprint Generation (without preprocessing):")
    print("   " + "-"*56)
    try:
        fingerprints_raw = fingerprinter.fingerprint_file(recording_path, preprocess=False)
        print(f"   Generated: {len(fingerprints_raw)} fingerprints")
        
        if len(fingerprints_raw) < 100:
            print(f"   ❌ CRITICAL: Too few fingerprints generated!")
            print(f"      This indicates audio quality issues")
        elif len(fingerprints_raw) < 300:
            print(f"   ⚠️  WARNING: Low fingerprint count")
            print(f"      Expected: ~40-50 per second")
        else:
            fps_per_second = len(fingerprints_raw) / duration
            print(f"   Rate: ~{fps_per_second:.1f} fingerprints/second")
            print(f"   ✅ Good fingerprint generation")
    except Exception as e:
        print(f"   ❌ Error generating fingerprints: {e}")
        return
    
    # Step 3: Generate fingerprints WITH preprocessing
    print("\n3. Fingerprint Generation (with preprocessing):")
    print("   " + "-"*56)
    try:
        fingerprints_preprocessed = fingerprinter.fingerprint_file(recording_path, preprocess=True)
        print(f"   Generated: {len(fingerprints_preprocessed)} fingerprints")
        
        diff = len(fingerprints_preprocessed) - len(fingerprints_raw)
        print(f"   Difference: {diff:+d} fingerprints")
        
        if abs(diff) > 100:
            print(f"   ℹ️  Preprocessing made significant difference")
    except Exception as e:
        print(f"   ❌ Error with preprocessing: {e}")
        fingerprints_preprocessed = fingerprints_raw
    
    # Step 4: Attempt matching
    print("\n4. Matching Analysis:")
    print("   " + "-"*56)
    
    # Use preprocessed fingerprints for matching
    query_fingerprints = fingerprints_preprocessed[:400]  # Use up to 400
    print(f"   Using {len(query_fingerprints)} fingerprints for matching")
    
    if len(query_fingerprints) < 50:
        print(f"   ❌ CRITICAL: Not enough fingerprints to match")
        print(f"      Need at least 50, have {len(query_fingerprints)}")
        return
    
    try:
        result = db_manager.find_matches(query_fingerprints)
        
        if result:
            print(f"\n   ✅ MATCH FOUND!")
            print(f"   Song: {result['title']}")
            print(f"   Artist: {result['artist']}")
            print(f"   Song ID: {result['song_id']}")
            print(f"   Confidence: {result['confidence']} fingerprints ({result['confidence_percentage']:.1f}%)")
            print(f"   Alignment offset: {result['alignment_offset']} frames")
            
            # Timing info
            offset_seconds = result['alignment_offset'] * fingerprinter.hop_length / fingerprinter.sample_rate
            print(f"   Time offset: ~{abs(offset_seconds):.1f} seconds into song")
        else:
            print(f"\n   ❌ NO MATCH FOUND")
            print(f"\n   Possible reasons:")
            print(f"   1. Song is not in database")
            print(f"   2. Recording quality is too poor")
            print(f"   3. Background noise is too loud")
            print(f"   4. Recording is from a different version (live/remix)")
            
    except Exception as e:
        print(f"   ❌ Error during matching: {e}")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS:")
    print("="*60)
    if duration < 10:
        print("• Record 10-15 seconds of audio")
    if len(fingerprints_preprocessed) < 300:
        print("• Improve recording quality (less noise, clearer audio)")
    print("• Make sure the song is in your database")
    print("• Record from the beginning or chorus (distinctive parts)")
    print("• Avoid recordings with talking or other sounds over music")
    print("="*60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_recording.py <path_to_recording.wav>")
        print("\nExample:")
        print("  python test_recording.py ../sample-songs/test_recording.wav")
        sys.exit(1)
    
    recording_path = sys.argv[1]
    diagnose_recording(recording_path)
