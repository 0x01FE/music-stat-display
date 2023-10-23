import sqlite3
import configparser
import typing
import collections
import os

import sqlparse

import listen_time
import date_range

config = configparser.ConfigParser()
config.read("config.ini")


DATABASE = config['PATHES']['DATABASE']
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
SQL_DIR = "./sql/"

QUERIES = {}

# Get SQL Files
for sql_file in os.listdir(SQL_DIR):
    file_name = sql_file.split('.')[0]

    with open(SQL_DIR + sql_file, 'r') as f:
        raw_data = f.read()

    # SQLparse is used because there are multiple queries in each file + comments
    QUERIES[file_name] = sqlparse.split(raw_data)


class Opener():
    def __init__(self):
        self.con = sqlite3.connect(DATABASE)

    def __enter__(self):
        return self.con, self.con.cursor()

    def __exit__(self, type, value, traceback):
        self.con.commit()
        self.con.close()




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
    top = collections.OrderedDict()
    for artist in results:
        top[artist[0].replace('-', ' ').title()] = (listen_time.ListenTime(artist[1]).to_hour_and_seconds(), artist[0])

    return top



def get_top_albums(user_id : int, range : date_range.DateRange | None = None, top : typing.Optional[int] = None) -> dict:
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
    top = collections.OrderedDict()
    for album in results:
        top[album[1]] = (listen_time.ListenTime(album[2]).to_hour_and_seconds(), album[0].replace('-', ' ').title(), album[0])

    return top



def get_top_songs(user_id : int, range : date_range.DateRange | None = None, top : typing.Optional[int] = None) -> dict:
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
    top = collections.OrderedDict()
    for song in results:
        top[song[1]] = (listen_time.ListenTime(song[2]).to_hour_and_seconds(), song[0].replace('-', ' ').title(), song[0])

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



def get_artist_top_albums(user_id : int, artist : str, range : date_range.DateRange | None = None) -> dict:
    dated = False
    args = [user_id]
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


def get_artist_top_songs(user_id : int, artist : str, range : date_range.DateRange | None = None) -> dict:
    dated = False
    args = [user_id]
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


def get_artist_total(user_id : int, artist : str, range : date_range.DateRange | None = None) -> listen_time.ListenTime | None:
    dated = False
    args = [user_id]
    if range:
        dated = True
        for date in range.to_str():
            args.append(date)

    with Opener() as (con, cur):
        cur.execute(QUERIES["artist_total_time"][dated], args)

        results = cur.fetchall()

    if results[0][0]:
        return listen_time.ListenTime(results[0][0])
    else:
        return None


