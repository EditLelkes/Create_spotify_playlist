from bs4 import BeautifulSoup
import requests
import spotipy.oauth2
import os
from datetime import datetime
from typing import List, Optional


OLDEST_TOP100 = datetime(1958, 10, 4)
SPOTIFY_CLIENT_ID = 'SPOTIFY_CLIENT_ID'
SPOTIFY_CLIENT_SECRET = 'SPOTIFY_CLIENT_SECRET'
SPOTIFY_SCOPE = "playlist-modify-private"


def read_date() -> str:
    """
    Reads a date from standard input in format YYYY-MM-DD.
    """
    while True:
        formatted_date = try_read_date()
        if formatted_date is not None:
            return formatted_date


def try_read_date() -> Optional[str]:
    """
    Tries to read a date from standard input in format YYYY-MM-DD.
    Checks if the read date is in valid format and whether it is between 1958-10-04 and yesterday.

    :return: On success it returns the formatted date, otherwise None.
    """
    user_input = input('Date in format YYYY-MM-DD: ')
    today = datetime.today().replace(minute=0, hour=0, second=0, microsecond=0)
    try:
        date_datetime = datetime.strptime(user_input, '%Y-%m-%d')
        if date_datetime < OLDEST_TOP100 or date_datetime >= today:
            print('Date is too old or in the future. Choose a date between 1958-10-04 and yesterday. Try again.')
        else:
            return date_datetime.strftime('%Y-%m-%d')
    except ValueError:
        print('Please give a date in format YYYY-MM-DD.')
    return None


def get_top_100_songs(url_date: str) -> List[str]:
    """
    Gets the top 100 songs form a date then extracts the titles of these songs using BeautifulSoup.

    :param url_date: URL date in format YYYY-MM-DD.
    :return: List of titles of top 100 songs from a given date.
    """
    response = requests.get(url=f'https://www.billboard.com/charts/hot-100/{url_date}')
    webpage = response.text
    soup = BeautifulSoup(webpage, 'html.parser')
    music_titles = soup.find_all(class_='chart-element__information__song text--truncate color--primary')
    titles_of_songs = [title.getText() for title in music_titles]
    return titles_of_songs


def create_playlist(sp: spotipy.Spotify, song_titles: List[str], date: str) -> None:
    """
    Creates a playlist and adds songs which URIs are in the list 'song_uris'.

    :param sp: Spotify instance.
    :param song_titles: List of song titles.
    :param date: Date.
    """
    song_uris = create_list_of_spotify_song_uris(sp, song_titles, date)
    playlist = sp.user_playlist_create(user=sp.current_user()['id'], name=f"Top songs of {date}", public=False)
    sp.playlist_add_items(playlist['id'], song_uris)


def create_list_of_spotify_song_uris(sp: spotipy.Spotify, song_titles: List[str], date: str) -> List:
    """
    Creates a List of Spotify URIs (Uniform Resource Indicator) of songs by searching the titles
    of top100 songs of a given date. Prints out the songs not found in Spotify.

    :param sp: Spotify instance.
    :param song_titles: List of song titles.
    :param date: Date.
    :return: List of Spotify song URIs.
    """
    song_uris = []
    for title in song_titles:
        result = sp.search(q=f"track:{title} year:{date.split('-')[0]}", type="track")
        try:
            song_uri = result['tracks']['items'][0]['uri']
            song_uris.append(song_uri)
        except IndexError:
            print(f'Song: {title} :not found, skipped.')
    return song_uris


if __name__ == "__main__":
    # Check if Spotify-related environmental variables are defined.
    if SPOTIFY_CLIENT_ID in os.environ and SPOTIFY_CLIENT_SECRET in os.environ:
        client_id = os.environ.get(SPOTIFY_CLIENT_ID)
        client_secret = os.environ.get(SPOTIFY_CLIENT_SECRET)
        my_sp = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(scope=SPOTIFY_SCOPE, client_id=client_id,
                                                                  client_secret=client_secret,
                                                                  redirect_uri='http://example.com'))
        my_date = read_date()
        list_of_song_titles = get_top_100_songs(my_date)
        create_playlist(my_sp, list_of_song_titles, my_date)
    else:
        raise RuntimeError('Please save your spotify client ID as "SPOTIFY_CLIENT_ID" and '
                           'spotify client secret as "SPOTIFY_CLIENT_SECRET" environment variables.')
