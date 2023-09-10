import sqlite3 as sql
from datetime import datetime
from configparser import ConfigParser
from typing import Optional








config = ConfigParser()
config.read("config.ini")


DATABASE = config['PATHES']['DATABASE']
artist_name = str
time = int



class Opener():
    def __init__(self):
        self.con = sql.connect(DATABASE)

    def __enter__(self):
        return self.con, self.con.cursor()

    def __exit__(self, type, value, traceback):
        self.con.commit()
        self.con.close()



def get_top_artists(start : Optional[datetime] = None, end : Optional[datetime] = None) -> list[tuple[artist_name, time]]:
    dated = False
    if start and end:
        dated = True
        start = start.strftime("%Y-%m-%d")
        end = end.strftime("%Y-%m-%d")

    with Opener() as (con, cur):
        if dated:
            cur.execute("SELECT artist_name, SUM(total_time) FROM (SELECT artists.name artist_name, songs.name song_name, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id WHERE DATE(dated.date) BETWEEN '?' AND '?' GROUP BY dated.song, songs.artist) GROUP BY artist_name ORDER BY SUM(total_time) DESC", [start, end])
        else:
            cur.execute("SELECT artist_name, SUM(total_time) FROM (SELECT artists.name artist_name, songs.name song_name, songs.length * COUNT(songs.name) total_time, COUNT(songs.name) cnt FROM dated INNER JOIN songs ON dated.song=songs.id INNER JOIN artists ON songs.artist=artists.id GROUP BY dated.song, songs.artist) GROUP BY artist_name ORDER BY SUM(total_time) DESC")
        results = cur.fetchall()

    return results

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



