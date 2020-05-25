from gmusicapi import Mobileclient


def __get_thumbs_up_songs(gpm_client: Mobileclient) -> None:
    playlists = gpm_client.get_all_playlists()
    pass


def main() -> None:
    gpm_client = Mobileclient()

    if not gpm_client.oauth_login(gpm_client.FROM_MAC_ADDRESS):
        gpm_client.perform_oauth()

    if gpm_client:
        __get_thumbs_up_songs(gpm_client)


if __name__ == '__main__':
    main()
