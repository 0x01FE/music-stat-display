import configparser
import calendar
import logging
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

TEMPLATE_PATH = config["PATHES"]["TEMPLATES"]

# Flask Blueprint Setup
month = flask.Blueprint(name='usermonth',
                       import_name=__name__,
                       template_folder=TEMPLATE_PATH,
                       url_prefix='/month/')

@month.route('/<int:year>/<int:month>/')
def month_overview(user_id: int, year: int, month: int):

    TOP_N = 10

    # Check if this user should be accessed
    if 'user' in flask.session:
        accessing_user = db.get_user_id(flask.session['user']['id'])
        display_name = flask.session['user']['display_name']
        user_pfp_url = flask.session['user']['images'][0]['url']

    else:
        accessing_user = None
        display_name = None
        user_pfp_url = None

    if not db.is_user_public(user_id) and accessing_user != user_id:
        return "This user's profile is not public!"

    period = daterange.DateRange()

    if not period.get_range(year, month):
        return "Invalid month or year"

    top = {}

    top["artists"] = db.get_top_artists(user_id, period, top=TOP_N)
    top["albums"] = db.get_top_albums(user_id, period, top=TOP_N)
    top["songs"] = db.get_top_songs(user_id, period, top=TOP_N)

    if not (total_time := db.get_total_time(user_id, period)):
        return "No data for this month"
    total_time = total_time.to_hour_and_seconds()

    info = {}

    info["artist_count"] = db.get_artist_count(user_id, period)
    info["album_count"] = db.get_album_count(user_id, period)
    info["song_count"] = db.get_song_count(user_id, period)

    return flask.render_template("user_monthly_overview.html",
                                 month_name=calendar.month_name[month],
                                 year=year,
                                 top=top,
                                 info=info,
                                 times=total_time,
                                 display_name=display_name,
                                 user_pfp_url=user_pfp_url)

@month.route('/<int:year>/<int:month>/artists/<artist>/')
def artist_month_overview(user_id: int, year: int, month: int, artist: int):

    period = daterange.DateRange()

    if not period.get_range(year, month):
        return "Invalid month or year."

    total_time = db.get_artist_total(user_id, artist, period).to_hour_and_seconds()
    top_albums = db.get_artist_top_albums(user_id, artist, period)
    top_songs = db.get_artist_top_songs(user_id, artist, period)

    artist_info = db.get_artist_info(artist)

    return flask.render_template('artist_month_overview.html',
                                 month_name=calendar.month_name[month],
                                 year=year,
                                 artist_info=artist_info,
                                 total_time=total_time,
                                 top_albums=top_albums,
                                 top_songs=top_songs)
