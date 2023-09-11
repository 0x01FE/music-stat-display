import sqlite3 as sql
from datetime import datetime
from configparser import ConfigParser
from typing import Optional
from math import floor
from collections import OrderedDict

from song import Song








config = ConfigParser()
config.read("config.ini")


DATABASE = config['PATHES']['DATABASE']



class Opener():
    def __init__(self):
        self.con = sql.connect(DATABASE)

    def __enter__(self):
        return self.con, self.con.cursor()

    def __exit__(self, type, value, traceback):
        self.con.commit()
        self.con.close()


def listenTimeFormat(mili : int) -> tuple:

    minutes = mili/1000/60
    hours = floor(minutes/60)

    return (hours, round(minutes % 60, 2))



def get_top_artists(user_id : int, start : Optional[datetime] = None, end : Optional[datetime] = None, top : Optional[int] = None) -> dict:
    if start and end:
        dated = True
        start = start.strftime("%Y-%m-%d")
        end = end.strftime("%Y-%m-%d")
    else:
        dated = False

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT artist_name, SUM(total_time) FROM (SELECT artists.name artist_name, songs.name song_name, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id WHERE dated.user = ? AND DATE(dated.date) BETWEEN '?' AND '?' GROUP BY dated.song, songs.artist) GROUP BY artist_name ORDER BY SUM(total_time) DESC", [user_id, start, end])
        else:
            cur.execute("SELECT artist_name, SUM(total_time) FROM (SELECT artists.name artist_name, songs.name song_name, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id WHERE dated.user = ? GROUP BY dated.song, songs.artist) GROUP BY artist_name ORDER BY SUM(total_time) DESC", [user_id])
        results = cur.fetchall()

    if top:
        results = results[:top]

    # Format results
    top = OrderedDict()
    for artist in results:
        top[artist[0].replace('-', ' ').title()] = (listenTimeFormat(artist[1]), artist[0])

    return top



def get_top_albums(user_id : int, start : Optional[datetime] = None, end : Optional[datetime] = None, top : Optional[int] = None) -> dict:
    if start and end:
        dated = True
        start = start.strftime("%Y-%m-%d")
        end = end.strftime("%Y-%m-%d")
    else:
        dated = False

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT artist_name, album_name, SUM(total_time) total_time FROM (SELECT artists.name artist_name, albums.name album_name, songs.name song_name, COUNT(songs.name) * songs.length total_time FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? AND DATE(dated.date) BETWEEN '?' AND '?' GROUP BY songs.name) GROUP BY album_name ORDER BY total_time DESC", [user_id, start, end])
        else:
            cur.execute("SELECT artist_name, album_name, SUM(total_time) total_time FROM (SELECT artists.name artist_name, albums.name album_name, songs.name song_name, COUNT(songs.name) * songs.length total_time FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? GROUP BY songs.name) GROUP BY album_name ORDER BY total_time DESC", [user_id])
        results = cur.fetchall()

    if top:
        results = results[:top]

    # Format results
    top = OrderedDict()
    for album in results:
        top[album[1]] = (listenTimeFormat(album[2]), album[0].replace('-', ' ').title(), album[0])

    return top



def get_top_songs(user_id : int, start : Optional[datetime] = None, end : Optional[datetime] = None, top : Optional[int] = None) -> dict:
    if start and end:
        dated = True
        start = start.strftime("%Y-%m-%d")
        end = end.strftime("%Y-%m-%d")
    else:
        dated = False

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT artists.name artist_name, songs.name song_name, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? AND WHERE DATE(dated.date) BETWEEN '?' AND '?' GROUP BY dated.song, songs.artist ORDER BY total_time DESC", [user_id, start, end])
        else:
            cur.execute("SELECT artists.name artist_name, songs.name song_name, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? GROUP BY dated.song, songs.artist ORDER BY total_time DESC", [user_id])
        results = cur.fetchall()

    if top:
        results = results[:top]

    # Format results
    top = OrderedDict()
    for song in results:
        top[song[1]] = (listenTimeFormat(song[2]), song[0].replace('-', ' ').title(), song[0])

    return top



def get_total_time(user_id : int, start : Optional[datetime] = None, end : Optional[datetime] = None) -> int:
    if start and end:
        dated = True
        start = start.strftime("%Y-%m-%d")
        end = end.strftime("%Y-%m-%d")
    else:
        dated = False

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT SUM(total_time) total_time FROM (SELECT artists.name artist_name, songs.name song_name, dated.song song_id, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? AND DATE(dated.date) BETWEEN ? AND ? GROUP BY dated.song, songs.artist ORDER BY total_time DESC)", [user_id, start, end])
        else:
            cur.execute("SELECT SUM(total_time) total_time FROM (SELECT artists.name artist_name, songs.name song_name, dated.song song_id, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id INNER JOIN albums on songs.album=albums.id WHERE dated.user = ? GROUP BY dated.song, songs.artist ORDER BY total_time DESC)", [user_id])
        results = cur.fetchall()

    return results[0][0]



def get_artist_count(user_id : int) -> int:
    with Opener() as (con, cur):
        cur.execute("SELECT COUNT(DISTINCT songs.artist) artist_count FROM dated INNER JOIN songs ON dated.song=songs.id WHERE dated.user = ?", [user_id])
        results = cur.fetchall()

    return results[0][0]



def get_album_count(user_id : int) -> int:
    with Opener() as (con, cur):
        cur.execute("SELECT COUNT(DISTINCT songs.album) album_count FROM dated INNER JOIN songs ON dated.song=songs.id WHERE dated.user = ?", [user_id])
        results = cur.fetchall()

    return results[0][0]



def get_song_count(user_id : int) -> int:
    with Opener() as (con, cur):
        cur.execute("SELECT COUNT(DISTINCT dated.song) song_count FROM dated WHERE dated.user = ?", [user_id])
        results = cur.fetchall()

    return results[0][0]


### Getters


## Artist

# return is (id, name, spotify_id) or None if not found
def get_artist_by_id(id : int) -> list[int, str, str] | None:
    with Opener() as (con, cur):
        cur.execute("SELECT * FROM artists WHERE id = ?", [id])

    results = cur.fetchall()
    if results:
        return results[0]
    return None

def get_artist_by_name(name : str) -> list[int, str, str] | None:
    with Opener() as (con, cur):
        cur.execute("SELECT * FROM artists WHERE name = ?", [name])

    results = cur.fetchall()
    if results:
        return results[0]
    return None


## Album

def get_album_by_id(id : int) -> list[int, str, str] | None:
    with Opener() as (con, cur):
        cur.execute("SELECT * FROM albums WHERE id = ?", [id])

    results = cur.fetchall()
    if results:
        return results[0]
    return None

def get_album_by_name(name : int) -> list[int, str, str] | None:
    with Opener() as (con, cur):
        cur.execute("SELECT * FROM albums WHERE name = ?", [name])

    results = cur.fetchall()
    if results:
        return results[0]
    return None


## Song

def get_song_by_id(id : int) -> list[int, str, str] | None:
    with Opener() as (con, cur):
        cur.execute("SELECT * FROM songs WHERE id = ?", [id])

    results = cur.fetchall()
    if results:
        return results[0]
    return None

def get_song_by_name(name : int) -> list[int, str, str] | None:
    with Opener() as (con, cur):
        cur.execute("SELECT * FROM songs WHERE name = ?", [name])

    results = cur.fetchall()
    if results:
        return results[0]
    return None



