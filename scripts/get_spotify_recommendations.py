import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json

def get_popular_songs():
    """
    Get popular songs from Spotify to use as a reference list.
    You'll need to source the actual audio files separately.
    """
    
    # Setup Spotify API
    # Get credentials from: https://developer.spotify.com/dashboard
    client_id = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"
    
    client_credentials_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    # Get Top Global 50 playlist
    # Playlist URI: spotify:playlist:37i9dQZEVXbMDoHDwVN2tF
    print("Fetching Spotify Top 50 Global...")
    global_playlist = sp.playlist('37i9dQZEVXbMDoHDwVN2tF')
    
    # Get Top India 50 playlist
    # Playlist URI: spotify:playlist:37i9dQZEVXbLZ52XmnySJg
    print("Fetching Spotify Top 50 India...")
    india_playlist = sp.playlist('37i9dQZEVXbLZ52XmnySJg')
    
    songs = []
    
    # Process Global playlist
    for item in global_playlist['tracks']['items']:
        track = item['track']
        songs.append({
            'title': track['name'],
            'artist': ', '.join([artist['name'] for artist in track['artists']]),
            'album': track['album']['name'],
            'popularity': track['popularity'],
            'duration_ms': track['duration_ms'],
            'preview_url': track.get('preview_url'),  # May be None
            'spotify_id': track['id'],
            'region': 'Global'
        })
    
    # Process India playlist
    for item in india_playlist['tracks']['items']:
        track = item['track']
        songs.append({
            'title': track['name'],
            'artist': ', '.join([artist['name'] for artist in track['artists']]),
            'album': track['album']['name'],
            'popularity': track['popularity'],
            'duration_ms': track['duration_ms'],
            'preview_url': track.get('preview_url'),
            'spotify_id': track['id'],
            'region': 'India'
        })
    
    # Save to JSON
    with open('spotify_songs_list.json', 'w', encoding='utf-8') as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)
    
    # Save to CSV for easy viewing
    import csv
    with open('spotify_songs_list.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=songs[0].keys())
        writer.writeheader()
        writer.writerows(songs)
    
    print(f"\n✅ Saved {len(songs)} songs to:")
    print("   - spotify_songs_list.json")
    print("   - spotify_songs_list.csv")
    
    # Show preview URL availability
    with_preview = sum(1 for s in songs if s['preview_url'])
    print(f"\n📊 Stats:")
    print(f"   Songs with preview URLs: {with_preview}/{len(songs)}")
    print(f"   Songs without previews: {len(songs) - with_preview}/{len(songs)}")
    
    return songs

if __name__ == "__main__":
    songs = get_popular_songs()
    
    print("\n📝 Sample songs:")
    for song in songs[:5]:
        print(f"   • {song['title']} - {song['artist']}")