import configparser
import logging
import calendar
import os

import flask

import db
import daterange

# Logger Setup
logger = logging.getLogger(__name__)

# Config Setup
config = configparser.ConfigParser()

dev = False
if 'env' in os.environ:
    dev: bool = os.environ['env'] == 'DEV'

if dev:
    config.read("config-dev.ini")
else:
    config.read("config.ini")

TEMPLATE_PATH = config["FLASK"]["TEMPLATES"]

# Flask Blueprint Setup
month = flask.Blueprint(name='usermonth',
                       import_name=__name__,
                       template_folder=TEMPLATE_PATH,
                       url_prefix='/month/<int:year>/<int:month>/')

@month.url_value_preprocessor
def get_period(endpoint, values):

    period = daterange.DateRange()

    if not period.get_range(values['year'], values['month']):
        return "Invalid month or year."

    flask.g.period = period

@month.route('/')
def overview(user_id: int, year: int, month: int):

    TOP_N = 10

    top = {}

    top["artists"] = db.get_top_artists(user_id, flask.g.period, top=TOP_N)
    top["albums"] = db.get_top_albums(user_id, flask.g.period, top=TOP_N)
    top["songs"] = db.get_top_songs(user_id, flask.g.period, top=TOP_N)

    if not (total_time := db.get_total_time(user_id, flask.g.period)):
        return "No data for this month"
    total_time = total_time.to_hour_and_seconds()

    info = {}

    info["artist_count"] = db.get_artist_count(user_id, flask.g.period)
    info["album_count"] = db.get_album_count(user_id, flask.g.period)
    info["song_count"] = db.get_song_count(user_id, flask.g.period)

    return flask.render_template("user_home_month.html",
                                 month_name=calendar.month_name[month],
                                 year=year,
                                 top=top,
                                 info=info,
                                 times=total_time,
                                 user_info=flask.g.current_user)

@month.route('/artists/<artist>/')
def artist(user_id: int, year: int, month: int, artist: int):

    total_time = db.get_artist_total(user_id, artist, flask.g.period).to_hour_and_seconds()
    top_albums = db.get_artist_top_albums(user_id, artist, flask.g.period)
    top_songs = db.get_artist_top_songs(user_id, artist, flask.g.period)

    artist_info = db.get_artist_info(artist)

    return flask.render_template('artist_month.html',
                                 month_name=calendar.month_name[month],
                                 year=year,
                                 artist_info=artist_info,
                                 total_time=total_time,
                                 top_albums=top_albums,
                                 top_songs=top_songs)

@month.route('/artists/')
def artists(user_id: int, year: int, month: int):

    top = db.get_top_artists(user_id, flask.g.period, images=False)

    return flask.render_template("top_artists_month.html",
                        year=year,
                        month_name=calendar.month_name[month],
                        top=top)

@month.route('/albums/')
def albums(user_id: int, year: int, month: int):

    top = db.get_top_albums(user_id, flask.g.period, images=False)

    return flask.render_template("top_albums_month.html",
                                 year=year,
                                 month_name=calendar.month_name[month],
                                 top=top)

@month.route('/songs/')
def song(user_id: int, year: int, month: int):

    top = db.get_top_songs(user_id, flask.g.period, images=False)

    return flask.render_template("top_songs_month.html",
                                 year=year,
                                 month_name=calendar.month_name[month],
                                 top=top)
