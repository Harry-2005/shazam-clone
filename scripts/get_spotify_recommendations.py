"""
Fetch music charts and download audio clips/songs.

Supports:
- Deezer API (30-second previews, no auth)
- Spotify API (30-second previews, requires auth)
- YouTube + yt-dlp (full songs, no auth) - See download_youtube_songs.py

Install: 
  pip install requests python-dotenv
  pip install yt-dlp  # For YouTube downloads
"""

import json
import os
import urllib.request
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

# ============================================================================
# DEEZER API FUNCTIONS (No authentication required!)
# ============================================================================

def get_deezer_chart(country='', limit=200):
    """
    Fetch Deezer chart tracks.
    
    Args:
        country: Country code (empty for global, 'in' for India, 'us' for USA, etc.)
        limit: Maximum tracks to fetch
    """
    try:
        # Deezer chart endpoint
        if country:
            url = f"https://api.deezer.com/chart/{country}/tracks"
        else:
            url = "https://api.deezer.com/chart/0/tracks"
        
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        tracks = []
        for track in data.get('data', [])[:limit]:
            tracks.append({
                'title': track['title'],
                'artist': track['artist']['name'],
                'album': track.get('album', {}).get('title', ''),
                'duration': track['duration'],
                'preview_url': track.get('preview'),  # 30-second preview
                'deezer_id': track['id'],
                'popularity': track.get('rank', 0)
            })
        
        return tracks
    except Exception as e:
        print(f"   Error fetching Deezer chart: {e}")
        return []

def get_deezer_playlist(playlist_id, limit=200):
    """Fetch tracks from a Deezer playlist."""
    try:
        url = f"https://api.deezer.com/playlist/{playlist_id}/tracks"
        params = {'limit': limit}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        tracks = []
        for track in data.get('data', [])[:limit]:
            tracks.append({
                'title': track['title'],
                'artist': track['artist']['name'],
                'album': track.get('album', {}).get('title', ''),
                'duration': track['duration'],
                'preview_url': track.get('preview'),
                'deezer_id': track['id'],
            })
        
        return tracks
    except Exception as e:
        print(f"   Error fetching Deezer playlist: {e}")
        return []

def get_deezer_songs():
    """
    Fetch popular songs from Deezer charts.
    No API credentials needed!
    """
    print("\n🎵 Using Deezer API (No authentication required)")
    print("=" * 60)
    
    # Define charts/playlists to fetch
    sources = {
        'Global Top 200': ('global', 200),
        'India Top 200': ('in', 200),
        'US Top 100': ('us', 100),
        'UK Top 100': ('gb', 100),
        'Canada Top 50': ('ca', 50),
        'Australia Top 50': ('au', 50),
        'Germany Top 50': ('de', 50),
        'France Top 50': ('fr', 50),
        'Brazil Top 50': ('br', 50),
        'Mexico Top 50': ('mx', 50),
        'Japan Top 50': ('jp', 50),
        'Spain Top 50': ('es', 50),
        'Italy Top 50': ('it', 50),
        'Netherlands Top 50': ('nl', 50),
        'Argentina Top 50': ('ar', 50),
    }
    
    all_songs = {}
    total_songs = 0
    
    for name, (country, limit) in sources.items():
        print(f"\nFetching {name}...")
        try:
            tracks = get_deezer_chart(country, limit)
            
            # Add region info
            region = name.split(' ')[0]
            for track in tracks:
                track['region'] = region
            
            all_songs[name] = tracks
            total_songs += len(tracks)
            print(f"   ✓ Fetched {len(tracks)} tracks")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    return all_songs, total_songs

# ============================================================================
# SPOTIFY API FUNCTIONS (Legacy - if Spotify comes back online)
# ============================================================================

def get_spotify_client():
    """Initialize Spotify API client (if credentials available)."""
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        
        client_id = os.getenv('SPOTIFY_CLIENT_ID', 'YOUR_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')
        
        if client_id == 'YOUR_CLIENT_ID' or client_secret == 'YOUR_CLIENT_SECRET':
            return None
        
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        return spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    except Exception:
        return None

def download_preview(preview_url, output_path):
    """Download a Spotify preview URL (30-second clip)."""
    try:
        urllib.request.urlretrieve(preview_url, output_path)
        return True
    except Exception as e:
        print(f"   ✗ Download failed: {e}")
        return False

def download_previews_from_json(json_file='music_songs_list.json', output_dir='music_previews'):
    """
    Download preview clips for all songs in the JSON file.
    Creates output_dir and downloads all available previews.
    """
    # Load JSON
    if not os.path.exists(json_file):
        # Try old filename
        json_file = 'spotify_songs_list.json'
        if not os.path.exists(json_file):
            print(f"❌ {json_file} not found. Run get_popular_songs() first.")
            return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        all_songs = json.load(f)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"\n📥 Downloading preview clips to {output_dir}/")
    print("=" * 60)
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    for playlist_name, tracks in all_songs.items():
        print(f"\n{playlist_name}:")
        
        for track in tracks:
            preview_url = track.get('preview_url')
            if not preview_url:
                skipped += 1
                continue
            
            # Clean filename
            title = track['title'].replace('/', '-').replace('\\', '-').replace(':', '-')
            artist = track['artist'].replace('/', '-').replace('\\', '-').replace(':', '-')
            filename = f"{artist} - {title}.mp3"
            
            # Limit filename length
            if len(filename) > 200:
                filename = filename[:200] + '.mp3'
            
            file_path = output_path / filename
            
            # Skip if already exists
            if file_path.exists():
                print(f"   ⏭️  {filename[:60]}... (already exists)")
                continue
            
            print(f"   📥 {filename[:60]}...")
            if download_preview(preview_url, file_path):
                downloaded += 1
            else:
                failed += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Download complete!")
    print(f"   Downloaded: {downloaded}")
    print(f"   Skipped (no preview): {skipped}")
    print(f"   Failed: {failed}")
    print(f"\n📁 Audio files saved to: {output_path.absolute()}")
    print(f"\n⚠️  Note: These are 30-second preview clips only.")
    print(f"   For full songs, you'll need to source audio from legal services.")
    """
    Download preview clips for all songs in the JSON file.
    Creates output_dir and downloads all available previews.
    """
    # Load JSON
    if not os.path.exists(json_file):
        print(f"❌ {json_file} not found. Run get_popular_songs() first.")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        all_songs = json.load(f)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"\n📥 Downloading preview clips to {output_dir}/")
    print("=" * 60)
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    for playlist_name, tracks in all_songs.items():
        print(f"\n{playlist_name}:")
        
        for track in tracks:
            preview_url = track.get('preview_url')
            if not preview_url:
                skipped += 1
                continue
            
            # Clean filename
            title = track['title'].replace('/', '-').replace('\\', '-')
            artist = track['artist'].replace('/', '-').replace('\\', '-')
            filename = f"{artist} - {title}.mp3"
            
            # Limit filename length
            if len(filename) > 200:
                filename = filename[:200] + '.mp3'
            
            file_path = output_path / filename
            
            # Skip if already exists
            if file_path.exists():
                print(f"   ⏭️  {filename[:60]}... (already exists)")
                continue
            
            print(f"   📥 {filename[:60]}...")
            if download_preview(preview_url, file_path):
                downloaded += 1
            else:
                failed += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Download complete!")
    print(f"   Downloaded: {downloaded}")
    print(f"   Skipped (no preview): {skipped}")
    print(f"   Failed: {failed}")
    print(f"\n📁 Audio files saved to: {output_path.absolute()}")
    print(f"\n⚠️  Note: These are 30-second preview clips only.")
    print(f"   For full songs, you'll need to source audio from legal services.")


def get_popular_songs(use_deezer=True):
    """
    Get popular songs from music charts.
    
    Args:
        use_deezer: If True, use Deezer API. If False, try Spotify.
    """
    
    if use_deezer:
        # Use Deezer API (no credentials needed)
        all_songs, total_songs = get_deezer_songs()
    else:
        # Try Spotify API
        sp = get_spotify_client()
        if not sp:
            print("\n❌ Spotify API not configured. Falling back to Deezer...")
            all_songs, total_songs = get_deezer_songs()
        else:
            print("\n🎵 Using Spotify API")
            # ... existing Spotify code would go here ...
            all_songs, total_songs = {}, 0
    
    if not all_songs:
        return {}
    
    # Save to JSON
    output_json = 'music_songs_list.json'
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(all_songs, f, indent=2, ensure_ascii=False)
    
    # Flatten and save to CSV
    import csv
    all_tracks = []
    for playlist_name, tracks in all_songs.items():
        for track in tracks:
            track['playlist'] = playlist_name
            all_tracks.append(track)
    
    if all_tracks:
        output_csv = 'music_songs_list.csv'
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_tracks[0].keys())
            writer.writeheader()
            writer.writerows(all_tracks)
        
        print(f"\n✅ Saved {total_songs} songs to:")
        print(f"   - {output_json}")
        print(f"   - {output_csv}")
        
        # Stats
        with_preview = sum(1 for s in all_tracks if s.get('preview_url'))
        unique_songs = len(set(s.get('deezer_id') or s.get('spotify_id') for s in all_tracks))
        
        print(f"\n📊 Stats:")
        print(f"   Total songs: {total_songs}")
        print(f"   Unique songs: {unique_songs}")
        print(f"   Songs with preview URLs: {with_preview}/{total_songs}")
        print(f"   Charts fetched: {len(all_songs)}")
        
        print(f"\n⚠️  Note: Preview clips are 30-seconds only.")
    
    return all_songs

if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 60)
    print("MUSIC CHART FETCHER")
    print("=" * 60)
    print("\n🎵 Using Deezer API (Spotify is currently down)")
    print("   - No authentication required")
    print("   - 30-second preview clips available")
    print("   - Charts from 15+ countries")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'fetch':
            # Fetch song metadata
            songs = get_popular_songs(use_deezer=True)
            
            if songs:
                print("\n📝 Sample songs:")
                for playlist_name, tracks in list(songs.items())[:3]:
                    print(f"\n{playlist_name}:")
                    for song in tracks[:3]:
                        print(f"   • {song['title']} - {song['artist']}")
        
        elif command == 'download':
            # Download preview clips
            download_previews_from_json()
        
        else:
            print(f"❌ Unknown command: {command}")
            print("\nUsage:")
            print("  python get_spotify_recommendations.py fetch     - Fetch song lists")
            print("  python get_spotify_recommendations.py download  - Download preview clips")
    else:
        # Interactive mode
        print("\nWhat would you like to do?")
        print("1. Fetch song metadata from Deezer charts")
        print("2. Download preview clips (30-second)")
        print("3. Both (fetch then download)")
        
        choice = input("\nEnter choice (1/2/3): ").strip()
        
        if choice == '1':
            songs = get_popular_songs(use_deezer=True)
            if songs:
                print("\n✅ Done! Check music_songs_list.json and .csv")
        
        elif choice == '2':
            download_previews_from_json()
        
        elif choice == '3':
            songs = get_popular_songs(use_deezer=True)
            if songs:
                print("\n" + "=" * 60)
                download_previews_from_json()
        
        else:
            print("❌ Invalid choice")