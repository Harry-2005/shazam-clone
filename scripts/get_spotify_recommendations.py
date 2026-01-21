import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import os
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def download_preview(preview_url, output_path):
    """Download a Spotify preview URL (30-second clip)."""
    try:
        urllib.request.urlretrieve(preview_url, output_path)
        return True
    except Exception as e:
        print(f"   ✗ Download failed: {e}")
        return False

def download_previews_from_json(json_file='spotify_songs_list.json', output_dir='spotify_previews'):
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


def get_playlist_tracks(sp, playlist_id, limit=200):
    """Fetch tracks from a Spotify playlist with pagination."""
    tracks = []
    offset = 0
    
    while len(tracks) < limit:
        try:
            results = sp.playlist_tracks(playlist_id, offset=offset, limit=100)
            if not results['items']:
                break
                
            for item in results['items']:
                if item['track']:
                    track = item['track']
                    tracks.append({
                        'title': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'album': track['album']['name'],
                        'popularity': track['popularity'],
                        'duration_ms': track['duration_ms'],
                        'preview_url': track.get('preview_url'),
                        'spotify_id': track['id'],
                    })
            
            if not results['next'] or len(tracks) >= limit:
                break
            offset += 100
        except Exception as e:
            print(f"   Error fetching tracks: {e}")
            break
    
    return tracks[:limit]

def get_popular_songs():
    """
    Get popular songs from Spotify charts worldwide.
    Fetches Top 200 Global, Top 200 India, and Top 50 from various countries.
    """
    
    # Setup Spotify API - Get from environment variables
    client_id = os.getenv('SPOTIFY_CLIENT_ID', 'YOUR_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')
    
    if client_id == 'YOUR_CLIENT_ID' or client_secret == 'YOUR_CLIENT_SECRET':
        print("\n❌ ERROR: Spotify credentials not configured!")
        print("\nSetup Instructions:")
        print("1. Go to https://developer.spotify.com/dashboard")
        print("2. Create an app and get your Client ID and Secret")
        print("3. Create a .env file in the project root with:")
        print("   SPOTIFY_CLIENT_ID=your_client_id")
        print("   SPOTIFY_CLIENT_SECRET=your_client_secret")
        print("\nOr edit this script and replace YOUR_CLIENT_ID and YOUR_CLIENT_SECRET")
        return []
    
    client_credentials_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    # Spotify Chart Playlists (official "Top 50" playlists)
    # Note: Spotify doesn't have official "Top 200" playlists, so we use Top 50 + Viral 50
    playlists = {
        'Global Top 50': ('37i9dQZEVXbMDoHDwVN2tF', 200),
        'Global Viral 50': ('37i9dQZEVXbLiRPT6q49JJ', 50),
        'India Top 50': ('37i9dQZEVXbLZ52XmnySJg', 200),
        'India Viral 50': ('37i9dQZEVXbMWDif5SCBJq', 50),
        'US Top 50': ('37i9dQZEVXbLRQDuF5jeBp', 50),
        'UK Top 50': ('37i9dQZEVXbLnolsZ8PSNw', 50),
        'Canada Top 50': ('37i9dQZEVXbKj23U1GF4IR', 50),
        'Australia Top 50': ('37i9dQZEVXbJPcfkRz0wJ0', 50),
        'Germany Top 50': ('37i9dQZEVXbJiZcmkrIHGU', 50),
        'France Top 50': ('37i9dQZEVXbIPWwFssbupI', 50),
        'Brazil Top 50': ('37i9dQZEVXbMXbN3EUUhlg', 50),
        'Mexico Top 50': ('37i9dQZEVXbO3qyFxbkOE1', 50),
        'Japan Top 50': ('37i9dQZEVXbKXQ4mDTEBXq', 50),
        'South Korea Top 50': ('37i9dQZEVXbNxXF4SkHj9F', 50),
        'Spain Top 50': ('37i9dQZEVXbNFJfN1Vw8d9', 50),
        'Italy Top 50': ('37i9dQZEVXbIQnj7RRhdSX', 50),
        'Netherlands Top 50': ('37i9dQZEVXbKCF6dqVpDkS', 50),
        'Sweden Top 50': ('37i9dQZEVXbLoATJ81JYXz', 50),
        'Argentina Top 50': ('37i9dQZEVXbMMy2roB9myp', 50),
        'Philippines Top 50': ('37i9dQZEVXbNBz9cRCSFkY', 50),
    }
    
    all_songs = {}
    total_songs = 0
    
    for name, (playlist_id, limit) in playlists.items():
        print(f"\nFetching {name}...")
        try:
            tracks = get_playlist_tracks(sp, playlist_id, limit)
            # Add region info
            region = name.replace(' Top 50', '').replace(' Viral 50', '').replace(' Top 200', '')
            for track in tracks:
                track['region'] = region
            
            all_songs[name] = tracks
            total_songs += len(tracks)
            print(f"   ✓ Fetched {len(tracks)} tracks")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    # Save to JSON
    output_json = 'spotify_songs_list.json'
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
        output_csv = 'spotify_songs_list.csv'
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_tracks[0].keys())
            writer.writeheader()
            writer.writerows(all_tracks)
        
        print(f"\n✅ Saved {total_songs} songs to:")
        print(f"   - {output_json}")
        print(f"   - {output_csv}")
        
        # Stats
        with_preview = sum(1 for s in all_tracks if s.get('preview_url'))
        unique_songs = len(set(s['spotify_id'] for s in all_tracks))
        
        print(f"\n📊 Stats:")
        print(f"   Total songs: {total_songs}")
        print(f"   Unique songs: {unique_songs}")
        print(f"   Songs with preview URLs: {with_preview}/{total_songs}")
        print(f"   Playlists fetched: {len(all_songs)}")
        
        print(f"\n⚠️  Note: Spotify API doesn't provide full audio downloads.")
        print(f"   - preview_url gives 30-second clips (if available)")
        print(f"   - You'll need to source full audio files separately")
    
    return all_songs

if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 60)
    print("SPOTIFY SONG FETCHER")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'fetch':
            # Fetch song metadata from Spotify
            songs = get_popular_songs()
            
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
        print("1. Fetch song metadata from Spotify charts")
        print("2. Download preview clips (30-second)")
        print("3. Both (fetch then download)")
        
        choice = input("\nEnter choice (1/2/3): ").strip()
        
        if choice == '1':
            songs = get_popular_songs()
            if songs:
                print("\n✅ Done! Check spotify_songs_list.json and .csv")
        
        elif choice == '2':
            download_previews_from_json()
        
        elif choice == '3':
            songs = get_popular_songs()
            if songs:
                print("\n" + "=" * 60)
                download_previews_from_json()
        
        else:
            print("❌ Invalid choice")