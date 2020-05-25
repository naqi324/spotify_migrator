import configparser
from pathlib import Path
from typing import Optional

import spotipy
import spotipy.util as util
from yaspin import yaspin

config = configparser.ConfigParser()
config.read('config.ini')

spot_username = config['spotify']['username']
spot_client_id = config['spotify']['client_id']
spot_client_secret = config['spotify']['client_secret']
spot_playlist_id = config['spotify']['playlist_id']
spot_max_requests = config['spotify'].getint('max_requests')

spot_scope = 'user-library-read user-library-modify playlist-modify-private playlist-modify-public'
spot_redirect_uri = 'http://localhost:8080/'

gpm_playlists_root = Path('gpm_playlists')


def __get_song_buckets(song_list: list) -> list:
    song_buckets = [song_list[i * spot_max_requests:(i + 1) * spot_max_requests]
                    for i in range((len(song_list) + spot_max_requests - 1) // spot_max_requests)]

    return song_buckets


def __get_gpm_songs() -> Optional[list]:
    try:
        with open('gpm_songs.txt', 'r') as gpm_fh:
            songs = gpm_fh.readlines()

        return songs

    except (FileNotFoundError, IOError) as file_error:
        print(file_error)
        return None


def get_spot_client() -> Optional[spotipy.Spotify]:
    try:
        token = util.prompt_for_user_token(username=spot_username,
                                           scope=spot_scope,
                                           client_id=spot_client_id,
                                           client_secret=spot_client_secret,
                                           redirect_uri=spot_redirect_uri)
        sp = spotipy.Spotify(auth=token,
                             # requests_timeout=20,
                             # status_forcelist=[500, 502],
                             # retries=2,
                             # status_retries=2,
                             # backoff_factor=0.5
                             )
        return sp

    except spotipy.client.SpotifyException as spot_except:
        print(str(spot_except))
        return None


def __clear_favorites(spot_client: spotipy.Spotify):
    with yaspin(text='Removing favorites...', color='yellow') as spinner:
        while True:
            response = spot_client.current_user_saved_tracks(limit=50)
            if not response:
                break

            favorites = []
            for item in response['items']:
                favorites.append(item['track']['id'])
            if len(favorites) > 0:
                spot_client.current_user_saved_tracks_delete(favorites)
            else:
                break
        spinner.ok('✅ ')


def add_track_to_favorites(spot_client: spotipy.Spotify, track_id: str) -> bool:
    try:
        spot_client.current_user_saved_tracks_add(tracks=[track_id])
        return True

    except spotipy.client.SpotifyException as spot_except:
        print(f"Error adding track {track_id} as favorite.\nMore info:\n{str(spot_except)}")
        return False


def add_track_to_playlist(spot_client: spotipy.Spotify, track_id: str, playlist_id: str) -> None:
    try:
        spot_client.user_playlist_add_tracks(user=spot_client.current_user()['id'],
                                             playlist_id=playlist_id,
                                             tracks=[track_id])

    except spotipy.client.SpotifyException as spot_except:
        print(f"Error adding track {track_id} to playlist {playlist_id}.\nMore info:\n{str(spot_except)}")


def get_spotify_track_id(spot_client: spotipy.Spotify, song: str) -> Optional[str]:
    try:
        response = spot_client.search(q=song,
                                      type='track',
                                      limit=1)
        if response and len(response) > 0 and 'tracks' in response and response['tracks'] \
                and len(response['tracks']) > 0:
            tracks = response['tracks']

            if 'items' in tracks and tracks['items'] and len(tracks['items']) > 0 and tracks['items'][0] \
                    and 'id' in tracks['items'][0] and tracks['items'][0]['id'] \
                    and len(tracks['items'][0]['id']) > 0:
                return tracks['items'][0]['id']

    except spotipy.client.SpotifyException as spot_except:
        print(f"Error in looking up {song}.\nMore info:\n{str(spot_except)}")
        return None


def __get_playlist_track_ids(spot_client: spotipy.Spotify, playlist_name: str) -> Optional[list]:
    track_ids = []
    try:
        playlist_fn = f"{playlist_name}.txt"
        playlist = Path(gpm_playlists_root / playlist_fn)

        with open(playlist, 'r') as pl_fh:
            tracks = pl_fh.readlines()

        if len(tracks) > 9999:
            tracks = tracks[:9999]

        for track in tracks:
            track_id = get_spotify_track_id(spot_client, track)
            if track_id:
                track_ids.append(track_id)

        return track_ids

    except (FileNotFoundError, IOError) as file_error:
        print(f"Error opening {playlist_name}.\nMore info:\n{str(file_error)}")
        return None


def __add_gpm_thumbs_up_to_spotify(spot_client: spotipy.Spotify) -> None:
    with yaspin(text='Getting Spotify track IDs...', color='yellow') as spinner:
        fave_track_ids = __get_playlist_track_ids(spot_client, 'gpm_thumbs_up')
        spinner.ok('✅ ')

    with yaspin(text='Adding favorites...', color='yellow') as spinner:
        for track_id in fave_track_ids:
            fave_added = add_track_to_favorites(spot_client, track_id)
            retries = 0
            while not fave_added and retries < 3:
                spot_client: spotipy.Spotify = get_spot_client()
                fave_added = add_track_to_favorites(spot_client, track_id)
                retries += 1
            if retries == 3:
                break
        spinner.ok('✅ ')


def main() -> None:
    try:
        spot_client: spotipy.Spotify = get_spot_client()

    except spotipy.client.SpotifyException as spot_except:
        print(f"Error in creating spotipy client.\nMore info:\n{str(spot_except)}")

    print(f"All done!")


if __name__ == '__main__':
    main()
