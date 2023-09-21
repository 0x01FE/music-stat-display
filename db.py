import sqlite3 as sql
from configparser import ConfigParser
from typing import Optional
from collections import OrderedDict


import listen_time
import date_range

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




def get_top_artists(user_id : int, range : date_range.DateRange | None = None, top : Optional[int] = None) -> dict:
    dated = False
    if range:
        dated = True
        start, end = range.to_str()


    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT artist_name, SUM(total_time) FROM (SELECT artists.name artist_name, songs.name song_name, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id WHERE dated.user = ? AND DATE(dated.date) BETWEEN ? AND ? GROUP BY dated.song, songs.artist) GROUP BY artist_name ORDER BY SUM(total_time) DESC", [user_id, start, end])
        else:
            cur.execute("SELECT artist_name, SUM(total_time) FROM (SELECT artists.name artist_name, songs.name song_name, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id WHERE dated.user = ? GROUP BY dated.song, songs.artist) GROUP BY artist_name ORDER BY SUM(total_time) DESC", [user_id])
        results = cur.fetchall()

    if top:
        results = results[:top]

    # Format results
    top = OrderedDict()
    for artist in results:
        top[artist[0].replace('-', ' ').title()] = (listen_time.ListenTime(artist[1]).to_hour_and_seconds(), artist[0])

    return top



def get_top_albums(user_id : int, range : date_range.DateRange | None = None, top : Optional[int] = None) -> dict:
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
    top = OrderedDict()
    for album in results:
        top[album[1]] = (listen_time.ListenTime(album[2]).to_hour_and_seconds(), album[0].replace('-', ' ').title(), album[0])

    return top



def get_top_songs(user_id : int, range : date_range.DateRange | None = None, top : Optional[int] = None) -> dict:
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
    top = OrderedDict()
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
    top = OrderedDict()
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
    top = OrderedDict()
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


