"""
Quick test - upload a recording file and get detailed diagnostics
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DatabaseManager
from app.fingerprint import AudioFingerprinter
import glob

def find_latest_recording():
    """Find the most recent recording file in temp directory"""
    import tempfile
    temp_dir = tempfile.gettempdir()
    
    # Look for common patterns
    patterns = [
        os.path.join(temp_dir, "recording*.wav"),
        os.path.join(temp_dir, "tmp*.wav"),
        os.path.join(temp_dir, "audio*.wav"),
    ]
    
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    
    if files:
        # Get most recent
        latest = max(files, key=os.path.getmtime)
        return latest
    return None

def quick_test():
    """Quick test of recording quality"""
    print("="*60)
    print("QUICK RECORDING TEST")
    print("="*60)
    
    # Ask user for file
    print("\nOptions:")
    print("1. Enter path to recording file")
    print("2. Auto-detect latest recording from temp folder")
    
    choice = input("\nChoose (1 or 2): ").strip()
    
    if choice == "2":
        recording_path = find_latest_recording()
        if not recording_path:
            print("❌ No recording files found in temp directory")
            return
        print(f"\nFound: {recording_path}")
    else:
        recording_path = input("\nEnter path to recording file: ").strip()
        recording_path = recording_path.strip('"')  # Remove quotes if present
    
    if not os.path.exists(recording_path):
        print(f"❌ File not found: {recording_path}")
        return
    
    # Run diagnostic
    from test_recording import diagnose_recording
    diagnose_recording(recording_path)

if __name__ == "__main__":
    quick_test()
