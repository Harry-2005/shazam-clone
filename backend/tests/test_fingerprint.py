import sys
sys.path.append('..')

from app.fingerprint import AudioFingerprinter
import os

def test_fingerprinting():
    """Test basic fingerprinting functionality."""
    
    print("=== Audio Fingerprinting Test ===\n")
    
    # Initialize fingerprinter
    fp = AudioFingerprinter()
    print("[OK] Fingerprinter initialized")
    
    # Test with a sample audio file
    # You'll need to place a test audio file in sample-songs/
    test_file = "../../sample-songs/test_song.mp3"
    
    if not os.path.exists(test_file):
        print("[ERROR] Test file not found: " + test_file)
        print("  Please place a test MP3 file at that location")
        return
    
    print("[OK] Test file found: " + test_file)
    
    # Load audio
    print("\nLoading audio...")
    audio = fp.load_audio(test_file)
    print("[OK] Audio loaded: {} samples, {:.2f} seconds".format(len(audio), len(audio)/fp.sample_rate))
    
    # Compute spectrogram
    print("\nComputing spectrogram...")
    spectrogram = fp.compute_spectrogram(audio)
    print("[OK] Spectrogram shape: {}".format(spectrogram.shape))
    print("  Time frames: {}".format(spectrogram.shape[1]))
    print("  Frequency bins: {}".format(spectrogram.shape[0]))
    
    # Find peaks
    print("\nFinding peaks...")
    peaks = fp.find_peaks(spectrogram)
    print("[OK] Found {} peaks".format(len(peaks)))
    
    # Generate hashes
    print("\nGenerating fingerprint hashes...")
    hashes = fp.generate_hashes(peaks)
    print("[OK] Generated {} hashes".format(len(hashes)))
    
    # Show sample hashes
    print("\nSample hashes:")
    for i, (hash_val, time_offset) in enumerate(hashes[:5]):
        time_sec = fp.frames_to_time(time_offset)
        print("  {}. Hash: {}... at {:.2f}s".format(i+1, hash_val[:16], time_sec))
    
    print("\n=== Test Complete ===")
    print("Fingerprinting successful! Generated {} unique fingerprints.".format(len(hashes)))

if __name__ == "__main__":
    test_fingerprinting()