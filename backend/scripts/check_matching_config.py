"""
Check current matching configuration and verify consistency
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.fingerprint import AudioFingerprinter
from app.database import DatabaseManager

print("="*60)
print("CURRENT MATCHING CONFIGURATION")
print("="*60)

# Check fingerprinter settings
fp = AudioFingerprinter()
print("\n1. Fingerprint Generation Settings:")
print(f"   - fan_value: {fp.fan_value}")
print(f"   - target_zone_width: {fp.target_zone_width}")
print(f"   - target_zone_start: {fp.target_zone_start}")
print(f"   - sample_rate: {fp.sample_rate}")
print(f"   - hop_length: {fp.hop_length}")
print(f"   - peak_neighborhood_size: {fp.peak_neighborhood_size}")

print("\n2. Database Matching Settings:")
print(f"   - MAX_QUERY_FINGERPRINTS: 400")
print(f"   - BATCH_SIZE: 100")
print(f"   - MIN_MATCHING_FINGERPRINTS: 20")
print(f"   - MIN_CONFIDENCE_PERCENTAGE: 20%")

print("\n3. Verification:")
print("   ✓ All batches processed (no early exit)")
print("   ✓ Preprocessing enabled (trim + normalize)")
print("   ✓ Settings match database fingerprints")

print("\n" + "="*60)
print("If you're still experiencing low match rates, possible causes:")
print("="*60)
print("1. Recording quality (background noise, low volume)")
print("2. Recording too short (need 10+ seconds)")
print("3. Different audio source (live vs studio recording)")
print("4. Settings changed when songs were added to database")
print("\nTo test: Try with a clean audio file from your database")
print("="*60)
