import sqlite3
import configparser
import typing
import collections
import os
from typing import Literal

import spotipy
import sqlparse

import listen_time
import date_range

config = configparser.ConfigParser()
config.read("config.ini")

CLIENT_ID = config["SPOTIFY"]["CLIENT_ID"]
CLIENT_SECRET = config["SPOTIFY"]["CLIENT_SECRET"]
REDIRECT_URI = config["SPOTIFY"]["REDIRECT_URI"]

os.environ["SPOTIPY_CLIENT_ID"] = CLIENT_ID
os.environ["SPOTIPY_CLIENT_SECRET"] = CLIENT_SECRET
os.environ["SPOTIPY_REDIRECT_URI"] = REDIRECT_URI

spotify = spotipy.Spotify(client_credentials_manager=spotipy.oauth2.SpotifyClientCredentials())

DATABASE = config['PATHES']['DATABASE']
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
SQL_DIR = "./sql/data/"

QUERIES = {}

# Get SQL Files
for sql_file in os.listdir(SQL_DIR):
    file_name = sql_file.split('.')[0]

    with open(SQL_DIR + sql_file, 'r') as f:
        raw_data = f.read()

    # SQLparse is used because there are multiple queries in each file + comments
    statements = sqlparse.split(raw_data)
    if len(statements) == 1:
        QUERIES[file_name] = statements[0]
    else:
        QUERIES[file_name] = sqlparse.split(raw_data)


class Opener():
    def __init__(self):
        self.con = sqlite3.connect(DATABASE)

    def __enter__(self):
        return self.con, self.con.cursor()

    def __exit__(self, type, value, traceback):
        self.con.commit()
        self.con.close()


def get_spotify_artist_image_url(id: str) -> str | None:
    spotify_response = spotify.artist(id)

    if spotify_response["images"]:
        image_url = spotify_response["images"][0]["url"]
    else:
        image_url = None

    return image_url

def get_spotify_album_image_url(id: str) -> str | None:

    spotify_response = spotify.album(id)

    if spotify_response["images"]:
        image_url = spotify_response["images"][0]["url"]
    else:
        image_url = None

    if image_url:
        with Opener() as (con, cur):
            cur.execute(QUERIES["insert_cover_art"], [image_url, id])

    return image_url




def get_top_artists(user_id : int, range : date_range.DateRange | None = None, top : typing.Optional[int] = None) -> dict:
    dated = False
    args = [user_id]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)


    with Opener() as (con, cur):
        cur.execute(QUERIES["top_artists"][dated], args)

        results = cur.fetchall()

    if top:
        results = results[:top]

    # Format results
    top = []
    for artist in results:
        artist_name: str = artist[0].replace('-', ' ').title()
        artist_id: str = artist[1]
        time: tuple[int, float] = listen_time.ListenTime(artist[2]).to_hour_and_seconds()

        top.append((artist_name, artist_id, time))

    return top



def get_top_albums(user_id : int, range : date_range.DateRange | None = None, top : typing.Optional[int] = None) -> list[dict]:
    dated = False
    args = [user_id]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)

    with Opener() as (con, cur):
        cur.execute(QUERIES["top_albums"][dated], args)

        results = cur.fetchall()

    if top:
        results = results[:top]

    # Format results
    top = []
    for album in results:
        artist_name: str = album[0].replace('-', ' ').title()
        artist_id: int = album[1]
        album_name: str = album[2]
        cover_art_url: str = album[3]
        time: tuple[int, float] = listen_time.ListenTime(album[4]).to_hour_and_seconds()

        if not cover_art_url:
            album_spotify_id: str = album[5]
            cover_art_url = get_spotify_album_image_url(album_spotify_id)

        top.append({
            "artist_name" : artist_name,
            "artist_id" : artist_id,
            "title" : album_name,
            "cover_art_url" : cover_art_url,
            "time" : time
        })

    return top



def get_top_songs(user_id : int, range : date_range.DateRange | None = None, top : int | None = None) -> dict:
    dated = False
    args = [user_id]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)

    with Opener() as (con, cur):
        cur.execute(QUERIES["top_songs"][dated], args)

        results = cur.fetchall()

    if top:
        results = results[:top]

    # Format results
    top: list[tuple[tuple[int, float], str, str]] = []
    for song in results:
        artist_name: str = song[0].replace('-', ' ').title()
        artist_id: int = song[1]
        song_name: str = song[2]
        time: tuple[int, float] = listen_time.ListenTime(song[3]).to_hour_and_seconds()

        top.append((artist_name, artist_id, song_name, time))

    return top



def get_total_time(user_id : int, range : date_range.DateRange | None = None) -> listen_time.ListenTime | None:
    dated = False
    args = [user_id]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)

    with Opener() as (con, cur):
        cur.execute(QUERIES["total_time"][dated], args)

        results = cur.fetchall()

    if results[0][0]:
        return listen_time.ListenTime(results[0][0])
    else:
        return None



def get_artist_count(user_id : int, range : date_range.DateRange | None = None) -> int:
    dated = False
    args = [user_id]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)

    with Opener() as (con, cur):
        cur.execute(QUERIES["artist_count"][dated], args)

        results = cur.fetchall()

    return results[0][0]



def get_album_count(user_id : int, range : date_range.DateRange | None = None) -> int:
    dated = False
    args = [user_id]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)

    with Opener() as (con, cur):
        cur.execute(QUERIES["album_count"][dated], args)

        results = cur.fetchall()

    return results[0][0]



def get_song_count(user_id : int, range : date_range.DateRange | None = None) -> int:
    dated = False
    args = [user_id]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)

    with Opener() as (con, cur):
        cur.execute(QUERIES["song_count"][dated], args)

        results = cur.fetchall()

    return results[0][0]



def get_artist_top_albums(user_id : int, artist : int, range : date_range.DateRange | None = None) -> dict:
    dated = False
    args = [user_id, artist]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)

    with Opener() as (con, cur):
        cur.execute(QUERIES["top_artist_albums"][dated], args)

        results = cur.fetchall()

    # Format results
    top = collections.OrderedDict()
    for album in results:
        top[album[1]] = listen_time.ListenTime(album[2]).to_hour_and_seconds()

    return top


def get_artist_top_songs(user_id : int, artist : int, range : date_range.DateRange | None = None) -> dict:
    dated = False
    args = [user_id, artist]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)

    with Opener() as (con, cur):
        cur.execute(QUERIES["top_artist_songs"][dated], args)

        results = cur.fetchall()

    # Format results
    top = collections.OrderedDict()
    for song in results:
        top[song[1]] = listen_time.ListenTime(song[2]).to_hour_and_seconds()

    return top

'''
Get the amount of time a user has listened to an artist for a time range.

Parameters:
    user_id : int (user id)
    artist : int (artist database id)
    range : date_range.DateRange | None (if desired, the range to query)

Returns:
    ListenTime | None
'''
def get_artist_total(user_id : int, artist : int, range : date_range.DateRange | None = None) -> listen_time.ListenTime | None:
    dated = False
    args = [user_id, artist]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)

    with Opener() as (con, cur):
        cur.execute(QUERIES["artist_total_time"][dated], args)

        results = cur.fetchall()

    if results[0][0]:
        return listen_time.ListenTime(results[0][0])
    return None

def get_artist_name(artist : int) -> str | None:
    with Opener() as (con, cur):
        cur.execute(QUERIES["get_artist_name"], [artist,])

        results = cur.fetchall()

    if results:
        return results[0][0].replace('-', ' ').title()
    return None


def get_top_skipped_songs(user_id : int, range : date_range.DateRange | None = None, top : int | None = None) -> list:
    dated = False
    args = [user_id]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)

    with Opener() as (con, cur):
        cur.execute(QUERIES["top_skipped_songs"][dated], args)

        results = cur.fetchall()

    if top:
        results = results[:top]

    # Format results
    top: list = []
    for song in results:
        artist_name: str = song[1].replace('-', ' ').title()
        artist_id: int = song[0]
        song_name: str = song[2]
        skips: int = song[3]

        top.append((artist_id, artist_name, song_name, skips))

    return top


def get_top_played_artists(user_id : int, range : date_range.DateRange | None = None, top : int | None = None) -> list:
    dated = False
    args = [user_id]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)

    with Opener() as (con, cur):
        cur.execute(QUERIES["top_played_artists"][dated], args)

        results = cur.fetchall()

    if top:
        results = results[:top]

    top: list = []
    # Format Artist Name
    for artist in results:
        artist_name: str = artist[1].replace('-', ' ').title()
        artist_id: int = artist[0]
        count: int = artist[2]

        top.append((artist_name, artist_id, count))

    return top


def get_top_played_songs(user_id : int, range : date_range.DateRange | None = None, top : int | None = None) -> list:
    dated = False
    args = [user_id]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)

    with Opener() as (con, cur):
        cur.execute(QUERIES["top_played_songs"][dated], args)

        results = cur.fetchall()

    if top:
        results = results[:top]

    top: list = []
    # Format Artist Name
    for song in results:
        artist_name: str = song[0].replace('-', ' ').title()
        artist_id: int = song[1]
        song_name : str = song[2]
        count: int = song[4]

        top.append((artist_name, artist_id, song_name, count))

    return top


def add_user(display_name : str, user_spotify_id : str) -> None:
    with open('./sql/user/add_user.sql', 'r') as f:
        query = f.read()

    with Opener() as (con, cur):
        cur.execute(query, [display_name, user_spotify_id, 1])


def user_exists(user_spotify_id : str) -> bool:
    with open('./sql/user/user_exists.sql', 'r') as f:
        query = f.read()

    with Opener() as (con, cur):
        cur.execute(query, [user_spotify_id,])

        results = cur.fetchall()

    return bool(results)

def get_user_id(user_spotify_id : str) -> int | None:
    with open('./sql/user/user_exists.sql', 'r') as f:
        query = f.read()

    with Opener() as (con, cur):
        cur.execute(query, [user_spotify_id,])

        results = cur.fetchall()

    return results[0][0]

def is_user_public(user_id : int) -> bool | None:
    with open('./sql/user/get_user_by_id.sql', 'r') as f:
        query = f.read()

    with Opener() as (con, cur):
        cur.execute(query, [user_id,])

        results = cur.fetchall()

    return bool(results[0][3])

def update_public(spotify_id : str, public : bool) -> None:
    with open('./sql/user/update_public.sql', 'r') as f:
        query = f.read()

    with Opener() as (con, cur):
        cur.execute(query, [int(public), spotify_id])

def get_last_n(user_id : int, limit: int | None = 50) -> list | None:
    with Opener() as (con, cur):
        cur.execute(QUERIES["get_last_n"], [user_id, limit])

        results = cur.fetchall()

    return results

def get_songs_artists(song_id : int) -> list[str] | None:
    with Opener() as (con, cur):
        cur.execute(QUERIES["get_songs_artists"], [song_id,])

        results = cur.fetchall()

    if not results:
        return None

    artists: list[str] = []
    for result in results[0]:
        artists.append(result.replace("-", " "))

    return artists

def get_song_name_by_id(song_id : int) -> str | None:
    with Opener() as (con, cur):
        cur.execute(QUERIES["get_song_name_by_id"], [song_id,])

        results = cur.fetchall()

    return results[0][0]

"""
Get the id of some artist, album, or user.

Parameters:
    table (str) : Name of the table the item is in
    name (str) : Name of the item you're looking for

Returns:
    id (int | None) : Id if found, otherwise None.
"""
def get_id(table : Literal["artists", "albums", "users"], name : str) -> int | None:
    with Opener() as (con, cur):
        cur.execute("SELECT * FROM '{}' WHERE name = ?".format(table), [name])
        results = cur.fetchall()

    if results:
        return results[0][0]
    return None