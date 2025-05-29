import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import json
import pandas as pd # Optional: Useful for transforming data later
from datetime import datetime # Optional: For timestamping extracts

# --- Configuration ---
# Ensure your environment variables are set:
# SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI

# Define the SCOPES required for the data you want to extract
# Find available scopes here: https://developer.spotify.com/documentation/web-api/concepts/scopes
# Example scopes:
SCOPE = "user-read-private user-read-email user-library-read user-top-read user-read-recently-played playlist-read-private playlist-read-collaborative"

# Directory to save extracted data
DATA_DIR = "spotify_data"
os.makedirs(DATA_DIR, exist_ok=True)

# --- Authentication ---
try:
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))
    print("Authentication successful.")
    user_info = sp.current_user()
    print(f"Authenticated as: {user_info['display_name']} ({user_info['id']})")
except Exception as e:
    print(f"Error during authentication: {e}")
    print("Ensure your environment variables (SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI) are set correctly.")
    exit()

# --- Data Extraction Functions ---

def save_data(data, filename_prefix):
    """Saves data to a JSON file with a timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(DATA_DIR, f"{filename_prefix}_{timestamp}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Data saved to {filename}")

def get_all_paginated_items(spotify_func, *args, **kwargs):
    """Helper function to retrieve all items from a paginated Spotify endpoint."""
    results = spotify_func(*args, **kwargs)
    all_items = results['items']
    while results['next']:
        results = sp.next(results) # Fetches the next page
        all_items.extend(results['items'])
    return all_items

# --- Example Extraction Tasks ---

# 1. Get User's Saved Tracks (Library)
try:
    print("\nFetching saved tracks...")
    saved_tracks = get_all_paginated_items(sp.current_user_saved_tracks, limit=50)
    # Process track data if needed (e.g., simplify structure)
    processed_tracks = []
    for item in saved_tracks:
        track = item['track']
        processed_tracks.append({
            'added_at': item['added_at'],
            'track_id': track['id'],
            'track_name': track['name'],
            'artist_ids': [artist['id'] for artist in track['artists']],
            'artist_names': [artist['name'] for artist in track['artists']],
            'album_id': track['album']['id'],
            'album_name': track['album']['name'],
            'duration_ms': track['duration_ms'],
            'popularity': track['popularity'],
            'external_url': track['external_urls']['spotify'],
            'preview_url': track['preview_url'],
            'is_local': track['is_local']
        })
    save_data(processed_tracks, "saved_tracks")
    print(f"Fetched {len(processed_tracks)} saved tracks.")
except Exception as e:
    print(f"Error fetching saved tracks: {e}")

# 2. Get User's Playlists
try:
    print("\nFetching user playlists...")
    playlists = get_all_paginated_items(sp.current_user_playlists, limit=50)
    processed_playlists = []
    for playlist in playlists:
         processed_playlists.append({
            'playlist_id': playlist['id'],
            'playlist_name': playlist['name'],
            'owner_id': playlist['owner']['id'],
            'owner_name': playlist['owner']['display_name'],
            'description': playlist['description'],
            'public': playlist['public'],
            'collaborative': playlist['collaborative'],
            'track_count': playlist['tracks']['total'],
            'snapshot_id': playlist['snapshot_id'],
            'external_url': playlist['external_urls']['spotify']
        })
    save_data(processed_playlists, "user_playlists")
    print(f"Fetched {len(processed_playlists)} playlists.")
except Exception as e:
    print(f"Error fetching playlists: {e}")

# 3. Get Tracks from a Specific Playlist (Example: first playlist found)
#    In a real ETL, you'd likely iterate through all playlist IDs from the previous step.
if processed_playlists:
    try:
        first_playlist_id = processed_playlists[0]['playlist_id']
        first_playlist_name = processed_playlists[0]['playlist_name']
        print(f"\nFetching tracks for playlist: '{first_playlist_name}' ({first_playlist_id})...")
        # Note: Playlist items endpoint has a slightly different structure
        playlist_items_results = sp.playlist_items(first_playlist_id, limit=100) # Max limit is 100 here
        playlist_tracks = playlist_items_results['items']
        while playlist_items_results['next']:
             playlist_items_results = sp.next(playlist_items_results)
             playlist_tracks.extend(playlist_items_results['items'])

        processed_playlist_tracks = []
        for item in playlist_tracks:
             # Skip if track is None (can happen with local files, etc.)
             if not item or not item['track']:
                 continue
             track = item['track']
             processed_playlist_tracks.append({
                'playlist_id': first_playlist_id, # Add playlist ID for context
                'added_at': item['added_at'],
                'added_by_id': item['added_by']['id'] if item.get('added_by') else None,
                'track_id': track.get('id'), # Use .get() as ID might be missing for local tracks
                'track_name': track.get('name'),
                'artist_ids': [artist['id'] for artist in track.get('artists', [])],
                'artist_names': [artist['name'] for artist in track.get('artists', [])],
                'album_id': track.get('album', {}).get('id'),
                'album_name': track.get('album', {}).get('name'),
                'duration_ms': track.get('duration_ms'),
                'popularity': track.get('popularity'),
                'external_url': track.get('external_urls', {}).get('spotify'),
                'preview_url': track.get('preview_url'),
                'is_local': track.get('is_local', False)
            })

        save_data(processed_playlist_tracks, f"playlist_{first_playlist_id}_tracks")
        print(f"Fetched {len(processed_playlist_tracks)} tracks from playlist '{first_playlist_name}'.")
    except Exception as e:
        print(f"Error fetching tracks for playlist {first_playlist_id}: {e}")


# 4. Get Audio Features for Tracks (Example: for saved tracks)
#    Note: API limit of 100 track IDs per call
track_ids_for_features = [track['track_id'] for track in processed_tracks if track['track_id'] and not track['is_local']] # Ensure ID exists and not local
if track_ids_for_features:
    try:
        print(f"\nFetching audio features for {len(track_ids_for_features)} saved tracks...")
        all_audio_features = []
        # Process in batches of 100
        for i in range(0, len(track_ids_for_features), 100):
            batch_ids = track_ids_for_features[i:i + 100]
            batch_features = sp.audio_features(batch_ids)
            # Filter out None results (can happen if a track ID is invalid)
            all_audio_features.extend([f for f in batch_features if f])

        save_data(all_audio_features, "saved_tracks_audio_features")
        print(f"Fetched audio features for {len(all_audio_features)} tracks.")

    except Exception as e:
        print(f"Error fetching audio features: {e}")

# 5. Get User's Recently Played Tracks
try:
    print("\nFetching recently played tracks...")
    # Note: Recently played endpoint has a slightly different structure and limit (max 50)
    # It uses cursors for pagination ('before' or 'after' timestamps), not 'offset'.
    # Spotipy's `current_user_recently_played` handles this.
    # We might not need the helper function here if we only want the last 50.
    # For full history, you'd need cursor-based pagination logic.
    recently_played = sp.current_user_recently_played(limit=50)
    processed_recent = []
    for item in recently_played.get('items', []):
        track = item['track']
        processed_recent.append({
            'played_at': item['played_at'],
            'track_id': track['id'],
            'track_name': track['name'],
            'artist_ids': [artist['id'] for artist in track['artists']],
            'artist_names': [artist['name'] for artist in track['artists']],
            'album_id': track['album']['id'],
            'album_name': track['album']['name'],
            'context_type': item['context']['type'] if item.get('context') else None, # e.g., 'playlist', 'album', 'artist'
            'context_uri': item['context']['uri'] if item.get('context') else None,
        })

    save_data(processed_recent, "recently_played")
    print(f"Fetched {len(processed_recent)} recently played tracks.")
except Exception as e:
    print(f"Error fetching recently played tracks: {e}")


print("\n--- Extraction Complete ---")
print(f"Data saved in '{DATA_DIR}' directory.")

# --- Next Steps (ETL) ---
# Now you have the raw data (JSON files).
# The next steps in your ETL process would be:
# 1. Transform:
#    - Load the JSON files (e.g., using pandas: df = pd.read_json(filepath))
#    - Clean the data (handle missing values, duplicates)
#    - Normalize/Structure the data (e.g., create separate tables for tracks, artists, albums, plays)
#    - Add timestamps for ETL processing
# 2. Load:
#    - Connect to your data warehouse (PostgreSQL, BigQuery, Snowflake, etc.)
#    - Load the transformed data into the appropriate tables.