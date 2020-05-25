import configparser
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


def __get_spot_client() -> Optional[spotipy.Spotify]:
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


def __add_song_to_playlist(spot_client: spotipy.Spotify, song: str) -> bool:
    song_missing = False
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
                track_id = tracks['items'][0]['id']

                # try:
                #     spot_client.current_user_saved_tracks_add(tracks=[track_id])
                #
                # except spotipy.client.SpotifyException as spot_except:
                #     print(str(spot_except))
                #     pass

                try:
                    spot_client.user_playlist_add_tracks(user=spot_client.current_user()['id'],
                                                         playlist_id=spot_playlist_id,
                                                         tracks=[track_id])

                except spotipy.client.SpotifyException as spot_except:
                    print(str(spot_except))
                    pass

            else:
                song_missing = True
        else:
            song_missing = True

    except spotipy.client.SpotifyException as spot_except:
        print(str(spot_except))
        pass

    return song_missing


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


def __update_playlist() -> None:
    all_songs = __get_gpm_songs()
    missing_songs = []

    if all_songs and len(all_songs) > 0:
        song_buckets = __get_song_buckets(all_songs)
        for song_bucket in song_buckets:

            try:
                spot_client: spotipy.Spotify = __get_spot_client()

                if not spot_client:
                    break

                for song in song_bucket:
                    print(song)
                    if __add_song_to_playlist(spot_client, song):
                        missing_songs.append(song)

            except spotipy.client.SpotifyException as spot_except:
                print(str(spot_except))

    missing_songs_rows = '\n'.join(missing_songs)
    print(f'>>>>>>\nMissing Songs:\n{missing_songs_rows}')


def main() -> None:
    try:
        spot_client: spotipy.Spotify = __get_spot_client()
        __clear_favorites(spot_client)

    except spotipy.client.SpotifyException as spot_except:
        print(str(spot_except))


if __name__ == '__main__':
    main()
