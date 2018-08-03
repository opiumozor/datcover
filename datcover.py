import requests
import os
import argparse
import sys
from urlparse import urlparse
from instabot import Bot

SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""
DOWNLOAD_DIR = "./covers"
INSTA_USERNAME = ""
INSTA_PASSWORD = ""


def get_access_token(client_id, client_secret):
    """
    Get the access token from Spotify
    """
    body_params = {'grant_type': "client_credentials"}
    url = 'https://accounts.spotify.com/api/token'

    response = requests.post(url, data=body_params, auth=(client_id, client_secret))
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        sys.exit("Failed to get access token. Is your client_id and client_secret correct?")


def get_api_url(url):
    """
    Get the api url from the song link or the Spotify URI

    Example:
    - https://open.spotify.com/track/7H9sqtNVPp6eoxnJRMUmm4?si=jtQGu_1MQGOF-2WscCvbnA
    - spotify:track:7H9sqtNVPp6eoxnJRMUmm4
    """
    parsed_url = urlparse(url)

    type = None
    spotify_id = None

    if parsed_url.scheme == 'http' or parsed_url.scheme == 'https':
        type = parsed_url.path.split('/')[1]
        spotify_id = parsed_url.path.split('/')[2]
    elif parsed_url.scheme == 'spotify':
        type = parsed_url.path.split(':')[0]
        spotify_id = parsed_url.path.split(':')[1]
    else:
        sys.exit("Failed to build api url.")

    return "https://api.spotify.com/v1/%ss/%s" % (type, spotify_id)  # add an 's' after the type


def download_spotify_cover(url, client_id, client_secret, directory):
    """
    Download an album cover from Spotify
    Get the name, artist and album for default caption
    """
    headers = {"Authorization": "Bearer %s" % get_access_token(client_id, client_secret)}
    url = get_api_url(url)

    response = requests.get(url, headers=headers).json()

    cover_url = response['album']['images'][0]['url']
    file_name = response['id'] + '.jpeg'
    if directory:
        file_name = os.path.join(directory, file_name)

    img_data = requests.get(cover_url).content
    with open(file_name, 'wb') as handler:
        handler.write(img_data)

    song_info = {
        "title": response['name'],
        "artist": response['album']['artists'][0]['name'],
        "album": response['album']['name'],
        "cover_path": file_name
    }

    return song_info


def upload_cover(song_infos, caption):
    """
    Upload the cover to instagram
    """
    bot = Bot()
    bot.login(username=INSTA_USERNAME, password=INSTA_PASSWORD)

    if not caption:
        caption = "%s by %s, %s" % (song_infos['title'], song_infos['artist'], song_infos['album'])

    caption += " #datcover #music #%s" % song_infos['artist'].lower().replace(" ", "")

    bot.upload_photo(song_infos['cover_path'], caption=caption)

    if bot.api.last_response.status_code != 200:
        print(bot.api.last_response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download album cover from Spotify.')
    parser.add_argument("url", help="Song or album url")
    parser.add_argument("--caption", help="Custom caption")
    args = parser.parse_args()

    client_id = SPOTIFY_CLIENT_ID
    client_secret = SPOTIFY_CLIENT_SECRET
    directory = DOWNLOAD_DIR

    song_infos = download_spotify_cover(args.url, client_id, client_secret, directory)
    upload_cover(song_infos, args.caption)
