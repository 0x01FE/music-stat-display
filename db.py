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

    with open(sql_file, 'r') as f:
        raw_data = f.read()

    # SQLparse is used because there are multiple queries in each file + comments
    QUERIES[file_name] = sqlparse.parse(raw_data)


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
    if range:
        dated = True
        start, end = range.to_str()

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT artist_name, album_name, SUM(total_time) total_time FROM (SELECT artists.name artist_name, albums.name album_name, songs.name song_name, COUNT(songs.name) * songs.length total_time FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? AND DATE(dated.date) BETWEEN ? AND ? GROUP BY songs.name) GROUP BY album_name ORDER BY total_time DESC", [user_id, start, end])
        else:
            cur.execute("SELECT artist_name, album_name, SUM(total_time) total_time FROM (SELECT artists.name artist_name, albums.name album_name, songs.name song_name, COUNT(songs.name) * songs.length total_time FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? GROUP BY songs.name) GROUP BY album_name ORDER BY total_time DESC", [user_id])
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
    if range:
        dated = True
        start, end = range.to_str()

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT artists.name artist_name, songs.name song_name, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? AND DATE(dated.date) BETWEEN ? AND ? GROUP BY dated.song, songs.artist ORDER BY total_time DESC", [user_id, start, end])
        else:
            cur.execute("SELECT artists.name artist_name, songs.name song_name, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? GROUP BY dated.song, songs.artist ORDER BY total_time DESC", [user_id])
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
    if range:
        dated = True
        start, end = range.to_str()

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT SUM(total_time) total_time FROM (SELECT artists.name artist_name, songs.name song_name, dated.song song_id, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? AND DATE(dated.date) BETWEEN ? AND ? GROUP BY dated.song, songs.artist)", [user_id, start, end])
        else:
            cur.execute("SELECT SUM(total_time) total_time FROM (SELECT artists.name artist_name, songs.name song_name, dated.song song_id, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? GROUP BY dated.song, songs.artist)", [user_id])
        results = cur.fetchall()

    if results[0][0]:
        return listen_time.ListenTime(results[0][0])
    else:
        return None



def get_artist_count(user_id : int, range : date_range.DateRange | None = None) -> int:
    dated = False
    if range:
        dated = True
        start, end = range.to_str()

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT COUNT(DISTINCT songs.artist) artist_count FROM dated INNER JOIN songs ON dated.song=songs.id WHERE dated.user = ? AND DATE(dated.date) BETWEEN ? AND ?", [user_id, start, end])
        else:
            cur.execute("SELECT COUNT(DISTINCT songs.artist) artist_count FROM dated INNER JOIN songs ON dated.song=songs.id WHERE dated.user = ?", [user_id])
        results = cur.fetchall()

    return results[0][0]



def get_album_count(user_id : int, range : date_range.DateRange | None = None) -> int:
    dated = False
    if range:
        dated = True
        start, end = range.to_str()

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT COUNT(DISTINCT dated.song) song_count FROM dated WHERE dated.user = ? AND DATE(dated.date) BETWEEN ? AND ?", [user_id, start, end])
        else:
            cur.execute("SELECT COUNT(DISTINCT dated.song) song_count FROM dated WHERE dated.user = ?", [user_id])
        results = cur.fetchall()

    return results[0][0]



def get_song_count(user_id : int, range : date_range.DateRange | None = None) -> int:
    dated = False
    if range:
        dated = True
        start, end = range.to_str()

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT COUNT(DISTINCT dated.song) song_count FROM dated WHERE dated.user = ? AND DATE(dated.date) BETWEEN ? AND ?", [user_id, start, end])
        else:
            cur.execute("SELECT COUNT(DISTINCT dated.song) song_count FROM dated WHERE dated.user = ?", [user_id])
        results = cur.fetchall()

    return results[0][0]



def get_artist_top_albums(user_id : int, artist : str, range : date_range.DateRange | None = None) -> dict:
    dated = False
    if range:
        dated = True
        start, end = range.to_str()

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT artist_name, album_name, SUM(total_time) total_time FROM (SELECT artists.name artist_name, albums.name album_name, songs.name song_name, COUNT(songs.name) * songs.length total_time FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? AND artists.name = ? AND DATE(dated.date) BETWEEN ? AND ? GROUP BY songs.name) GROUP BY album_name ORDER BY total_time DESC", [user_id, artist, start, end])
        else:
            cur.execute("SELECT artist_name, album_name, SUM(total_time) total_time FROM (SELECT artists.name artist_name, albums.name album_name, songs.name song_name, COUNT(songs.name) * songs.length total_time FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? AND artists.name = ? GROUP BY songs.name) GROUP BY album_name ORDER BY total_time DESC", [user_id, artist])
        results = cur.fetchall()

    # Format results
    top = collections.OrderedDict()
    for album in results:
        top[album[1]] = listen_time.ListenTime(album[2]).to_hour_and_seconds()

    return top


def get_artist_top_songs(user_id : int, artist : str, range : date_range.DateRange | None = None) -> dict:
    dated = False
    if range:
        dated = True
        start, end = range.to_str()

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT artists.name artist_name, songs.name song_name, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? AND artists.name = ? AND DATE(dated.date) BETWEEN ? AND ? GROUP BY dated.song, songs.artist ORDER BY total_time DESC", [user_id, artist, start, end])
        else:
            cur.execute("SELECT artists.name artist_name, songs.name song_name, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? AND artists.name = ? GROUP BY dated.song, songs.artist ORDER BY total_time DESC", [user_id, artist])
        results = cur.fetchall()

    # Format results
    top = collections.OrderedDict()
    for song in results:
        top[song[1]] = listen_time.ListenTime(song[2]).to_hour_and_seconds()

    return top


def get_artist_total(user_id : int, artist : str, range : date_range.DateRange | None = None) -> listen_time.ListenTime | None:
    dated = False
    if range:
        dated = True
        start, end = range.to_str()

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT SUM(total_time) total_time FROM (SELECT artists.name artist_name, songs.name song_name, dated.song song_id, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id WHERE dated.user = ? AND artists.name = ? AND DATE(dated.date) BETWEEN ? AND ? GROUP BY dated.song, songs.artist)", [user_id, artist, start, end])
        else:
            cur.execute("SELECT SUM(total_time) total_time FROM (SELECT artists.name artist_name, songs.name song_name, dated.song song_id, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id WHERE dated.user = ? AND artists.name = ? GROUP BY dated.song, songs.artist)", [user_id, artist])
        results = cur.fetchall()

    if results[0][0]:
        return listen_time.ListenTime(results[0][0])
    else:
        return None


