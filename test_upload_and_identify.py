#!/usr/bin/env python3
"""
Quick test to verify:
1. Song upload is now FAST (no preprocessing)
2. Song identification still works (preprocessing applied)
"""

import requests
import time
import os
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

# Find a test audio file
sample_songs_dir = Path("./sample-songs")
audio_files = list(sample_songs_dir.glob("*.mp3")) + list(sample_songs_dir.glob("*.wav"))

if not audio_files:
    print("ERROR: No audio files found in sample-songs/")
    exit(1)

test_file = audio_files[0]
print(f"Test file: {test_file}")

# Extract title and artist from filename
filename = test_file.stem
if " - " in filename:
    artist, title = filename.split(" - ", 1)
else:
    title = filename
    artist = "Unknown"

print(f"Title: {title}")
print(f"Artist: {artist}\n")

# TEST 1: Upload song (should be FAST now - no preprocessing)
print("=" * 60)
print("TEST 1: Upload song (should be FAST - no preprocessing)")
print("=" * 60)

start_time = time.time()

with open(test_file, 'rb') as f:
    files = {'file': f}
    data = {'title': title, 'artist': artist}
    response = requests.post(f"{BASE_URL}/songs/upload", files=files, data=data)

upload_time = time.time() - start_time

print(f"Status: {response.status_code}")
print(f"Time taken: {upload_time:.2f} seconds")

if response.status_code == 200:
    result = response.json()
    print(f"Song ID: {result['song_id']}")
    print(f"Fingerprints: {result['fingerprints_generated']}")
    if upload_time > 30:
        print("⚠️  WARNING: Upload took too long (>30s), preprocessing might still be active")
    else:
        print("✓ Upload time is good!")
else:
    print(f"ERROR: {response.text}")
    exit(1)

# TEST 2: Identify song (should use preprocessing for better matching)
print("\n" + "=" * 60)
print("TEST 2: Identify song (uses preprocessing internally)")
print("=" * 60)

start_time = time.time()

with open(test_file, 'rb') as f:
    files = {'file': f}
    response = requests.post(f"{BASE_URL}/identify", files=files)

identify_time = time.time() - start_time

print(f"Status: {response.status_code}")
print(f"Time taken: {identify_time:.2f} seconds")

if response.status_code == 200:
    result = response.json()
    if result['matched']:
        print(f"✓ Matched: {result['song']['title']} - {result['song']['artist']}")
        print(f"Confidence: {result['confidence_percentage']:.1f}%")
    else:
        print("✗ No match found")
else:
    print(f"ERROR: {response.text}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Upload time: {upload_time:.2f}s (should be <10s)")
print(f"Identify time: {identify_time:.2f}s (preprocessing applied)")
