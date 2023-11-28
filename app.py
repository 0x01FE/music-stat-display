import dateutil.relativedelta
import datetime
import configparser
import calendar
import os

import flask
import flask_wtf.csrf
import waitress

import db
import date_range
import graphs

app = flask.Flask(__name__, static_url_path='', static_folder='static')

csrf = flask_wtf.csrf.CSRFProtect()
csrf.init_app(app)

config = configparser.ConfigParser()
config.read("config.ini")

templates_path = config['PATHES']['templates']
DATABASE = config['PATHES']['DATABASE']
PORT = config['NETWORK']['PORT']


@app.route('/<int:user>/')
def overview(user : int):

    graphs.generate_daily_graph(user)
    graphs.generate_weekly_graph(user)
    graphs.generate_monthly_graph(user)

    today = datetime.datetime.today()

    top_artists = db.get_top_artists(user, top=5)
    top_albums = db.get_top_albums(user, top=5)
    top_songs = db.get_top_songs(user, top=5)

    total_time = db.get_total_time(user).to_hour_and_seconds()

    artist_count = db.get_artist_count(user)
    album_count = db.get_album_count(user)
    song_count = db.get_song_count(user)


    return flask.render_template('overall.html', top_albums=top_albums, top_songs=top_songs, top_artists=top_artists, year=today.year, month=today.month, artist_count=artist_count, total_time=total_time, album_count=album_count, song_count=song_count)

@app.route('/<int:user>/artists/')
def artists_overview(user: int):

    top_artists = db.get_top_artists(user)

    return flask.render_template('artists_overview.html', top_artists=top_artists)

@app.route('/<int:user>/artists/<artist>/')
def artist_overview(user: int, artist : int):

    total_time = db.get_artist_total(user, artist).to_hour_and_seconds()
    top_albums = db.get_artist_top_albums(user, artist)
    top_songs = db.get_artist_top_songs(user, artist)

    artist_name = db.get_artist_name(artist)

    graphs.generate_artist_graph(user, artist, date_range.daily_ranges(30), 'd')
    graphs.generate_artist_graph(user, artist, date_range.weekly_ranges(4), 'w')
    graphs.generate_artist_graph(user, artist, date_range.monthly_ranges(12), 'm')

    return flask.render_template('artist.html', artist_name=artist_name, artist_listen_time=total_time, top_albums=top_albums, top_songs=top_songs, artist_id=artist)

@app.route('/<int:user>/albums/')
def albums_overview(user : int):
    top_albums = db.get_top_albums(user)

    return flask.render_template('albums_overview.html', top_albums=top_albums)

@app.route('/<int:user>/songs/')
def songs_overview(user : int):
    top_songs = db.get_top_songs(user)

    return flask.render_template('songs_overview.html', top_songs=top_songs)



@app.route('/<int:user>/month/<int:year>/<int:month>/')
def month_overview(user : int, year : int, month : int):

    period = date_range.DateRange()

    if not period.get_range(year, month):
        return "Invalid month or year."

    top_artists = db.get_top_artists(user, period, top=5)
    top_albums = db.get_top_albums(user, period, top=5)
    top_songs = db.get_top_songs(user, period, top=5)

    if not (total_time := db.get_total_time(user, period)):
        return "No data for this month."
    total_time = total_time.to_hour_and_seconds()

    artist_count = db.get_artist_count(user, period)
    album_count = db.get_album_count(user, period)
    song_count = db.get_song_count(user, period)


    links = (f"../../{year}/{month - 1}", f"../../{year}/{month + 1}")

    return flask.render_template('month_overview.html', month_name=calendar.month_name[month], year=year, top_artists=top_artists, top_albums=top_albums, top_songs=top_songs, artist_count=artist_count, total_time=total_time, album_count=album_count, song_count=song_count)


@app.route('/<int:user>/month/<int:year>/<int:month>/artists/<artist>/')
def artist_month_overview(user : int, year : int, month : int, artist : int):

    period = date_range.DateRange()

    if not period.get_range(year, month):
        return "Invalid month or year."

    total_time = db.get_artist_total(user, artist, period).to_hour_and_seconds()
    top_albums = db.get_artist_top_albums(user, artist, period)
    top_songs = db.get_artist_top_songs(user, artist, period)

    artist_name = db.get_artist_name(artist)

    return flask.render_template('artist_month_overview.html', artist_name=artist_name, month_name=calendar.month_name[month], year=year, artist_listen_time=total_time, top_albums=top_albums, top_songs=top_songs)

@app.route('/<int:user>/month/<int:year>/<int:month>/artists/')
def artists_month_overview(user : int, year : int, month : int):

    period = date_range.DateRange()

    if not period.get_range(year, month):
        return "Invalid month or year."

    top_artists = db.get_top_artists(user, period)

    return flask.render_template('artists_month_overview.html', top_artists=top_artists, month_name=calendar.month_name[month], year=year)

@app.route('/<int:user>/month/<int:year>/<int:month>/albums/')
def albums_month_overview(user : int, year : int, month : int):

    period = date_range.DateRange()

    if not period.get_range(year, month):
        return "Invalid month or year."

    top_albums = db.get_top_albums(user, period)

    return flask.render_template('albums_month_overview.html', top_albums=top_albums, month_name=calendar.month_name[month], year=year)

@app.route('/<int:user>/month/<int:year>/<int:month>/songs/')
def songs_month_overview(user : int, year : int, month : int):

    period = date_range.DateRange()

    if not period.get_range(year, month):
        return "Invalid month or year."

    top_songs = db.get_top_songs(user, period)

    return flask.render_template('songs_month_overview.html', top_songs=top_songs, month_name=calendar.month_name[month], year=year)

@app.route('/<int:user>/biggraph/<int:artist>/')
def big_artist_graph(user : int, artist : int):

    graphs.generate_artist_graph(user, artist, date_range.daily_ranges(365), 'yd')

    return flask.send_file(f"static/{artist}-yd.png")

@app.route('/')
def root():
    return 'home'

if __name__ == '__main__':
    if os.environ['env'] == 'DEV':
        app.run()
    else:
        waitress.serve(app, host='0.0.0.0', port=PORT)
