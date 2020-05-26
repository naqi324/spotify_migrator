from pathlib import Path

from gmusicapi import Mobileclient

gpm_playlists_root = Path('gpm_playlists')


def __get_all_playlists(gpm_client: Mobileclient) -> None:
    playlists = gpm_client.get_all_playlists()
    playlist_dict = {}
    for playlist in playlists:
        playlist_dict.update({playlist['name']: playlist['id']})

    pass


def __get_top_songs(gpm_client: Mobileclient) -> list:
    response = gpm_client.get_top_songs()
    top_songs = []

    for song in response:
        top_songs.append(f"{song['artist']} {song['title']}")

    return top_songs


def __save_playlist_locally(playlist_name: str, playlist_tracks: list) -> None:
    try:
        playlist_fn = f"{playlist_name}.txt"
        playlist = Path(gpm_playlists_root / playlist_fn)

        with open(playlist, 'w') as pl_fh:
            pl_fh.write('\n'.join(playlist_tracks))

    except (FileNotFoundError, IOError) as file_error:
        print(file_error)


def main() -> None:
    gpm_client = Mobileclient()

    if not gpm_client.oauth_login(gpm_client.FROM_MAC_ADDRESS):
        gpm_client.perform_oauth()

    if gpm_client:
        # Save thumbs up songs from GPM to local playlist file
        # top_songs = __get_top_songs(gpm_client)
        # if len(top_songs) > 0:
        #     __save_playlist_locally('gpm_thumbs_up', top_songs)
        pass


if __name__ == '__main__':
    main()
