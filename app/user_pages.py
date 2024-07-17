import configparser
import itertools
import datetime
import dateutil
import logging
import random
import json
import os

import spotipy
import flask

import daterange
import usermonth
import graphs
import db
from user import User

LAST_PLAYLIST_NEGATIVE_WEIGHT = -0.5


# Config Setup
config = configparser.ConfigParser()

logger = logging.getLogger(__name__)

dev = False
if 'env' in os.environ:
    dev: bool = os.environ['env'] == 'DEV'

if dev:
    config.read("config-dev.ini")
else:
    config.read("config.ini")

TEMPLATE_PATH = config["FLASK"]["TEMPLATES"]

# Flask Blueprint Setup
user = flask.Blueprint(name='user_pages',
                       import_name=__name__,
                       template_folder=TEMPLATE_PATH,
                       url_prefix='/<int:user_id>/')

user.register_blueprint(usermonth.month)

@user.url_value_preprocessor
def is_logged_in(endpoint, values):

    logger.debug(f'User accessing route "{flask.request.url}"')

    # Check if a user is logged in
    if 'user' in flask.session:
        flask.g.current_user = {
            "id" : db.get_user_id(flask.session['user']['id']),
            "display_name" : flask.session['user']['display_name'],
            "pfp_url" : flask.session['user']['images'][0]['url']
        }

        logger.debug(f'User is logged in as {flask.g.current_user["display_name"]}')

    else:
        flask.g.current_user = None
        logger.debug("User is _NOT_ logged in")

    # Check if profile is private

    viewed_user: int = values['user_id']

    accessing_user: int | None = None
    if flask.g.current_user:
        accessing_user = flask.g.current_user['id']

    if not db.is_user_public(viewed_user) and accessing_user != user:
        return flask.abort(401)


# Stat Displays

@user.route('/')
def user_home(user_id: int):

    logger.info("Geting music stat counts...")
    logger.info(f'Current user: {flask.g.current_user}')
    info = {}
    info["artist_count"] = db.get_artist_count(user_id)
    info["album_count"] = db.get_album_count(user_id)
    info["song_count"] = db.get_song_count(user_id)
    info["id"] = user_id

    today = datetime.datetime.today()
    six_m_period = daterange.last_n_months(6)
    one_m_period = daterange.last_n_months(1)

    logger.info("Getting times...")
    times = {
        "overall" : db.get_total_time(user_id).to_hour_and_seconds(),
        "six_months" : db.get_total_time(user_id, six_m_period).to_hour_and_seconds(),
        "one_month" : db.get_total_time(user_id, one_m_period).to_hour_and_seconds()
    }

    logger.info("Getting top everything")
    periods = [
        {
            "name" : "all-time",
            "top_artists" : db.get_top_artists(user_id, top=10),
            "top_albums" : db.get_top_albums(user_id, top=10),
            "top_songs" : db.get_top_songs(user_id, top=10)
        },
        {
            "name" : "6m",
            "top_artists" : db.get_top_artists(user_id, six_m_period, top=10),
            "top_albums" : db.get_top_albums(user_id, six_m_period, top=10),
            "top_songs" : db.get_top_songs(user_id, six_m_period, top=10)
        },
        {
            "name" : "4w",
            "top_artists" : db.get_top_artists(user_id, one_m_period, top=10),
            "top_albums" : db.get_top_albums(user_id, one_m_period, top=10),
            "top_songs" : db.get_top_songs(user_id, one_m_period, top=10)
        }
    ]

    # Generate graphs
    graphs.generate_daily_graph(user_id)
    graphs.generate_weekly_graph(user_id)
    graphs.generate_monthly_graph(user_id)

    return flask.render_template('user_home.html',
                                 info=info,
                                 times=times,
                                 periods=periods,
                                 year=today.year,
                                 month=today.month,
                                 user_info=flask.g.current_user)

@user.route('/artists/')
def artists_overview(user_id: int):

    # All Time
    overall = db.get_top_artists(user_id, images=False)

    # Past 6 Months
    period = daterange.last_n_months(6)

    six_months = db.get_top_artists(user_id, period, images=False)

    # Past 1 Month
    period = daterange.last_n_months(1)

    one_month = db.get_top_artists(user_id, period, images=False)

    return flask.render_template('top_artists.html',
                                 overall=overall,
                                 six_months=six_months,
                                 one_month=one_month)

@user.route('/artists/<artist>/')
def artist_overview(user_id: int, artist: int):

    times = {}

    # All Time
    overall = {}

    times["overall"] = db.get_artist_total(user_id, artist).to_hour_and_seconds()
    overall["top_albums"] = db.get_artist_top_albums(user_id, artist)
    overall["top_songs"] = db.get_artist_top_songs(user_id, artist)

    artist_info = db.get_artist_info(artist)

    # Past 6 Months
    period = daterange.last_n_months(6)

    six_months = {}

    times["six_months"] = db.get_artist_total(user_id, artist, period)
    if times["six_months"]:
        times["six_months"] = times["six_months"].to_hour_and_seconds()
    six_months["top_albums"] = db.get_artist_top_albums(user_id, artist, period)
    six_months["top_songs"] = db.get_artist_top_songs(user_id, artist, period)

    # Past 1 Month
    period = daterange.last_n_months(1)

    one_month = {}

    times["one_month"] = db.get_artist_total(user_id, artist, period)
    if times["one_month"]:
        times["one_month"] = times["one_month"].to_hour_and_seconds()
    one_month["top_albums"] = db.get_artist_top_albums(user_id, artist, period)
    one_month["top_songs"] = db.get_artist_top_songs(user_id, artist, period)

    return flask.render_template('artist.html',
                                 artist_info=artist_info,
                                 overall=overall,
                                 six_months=six_months,
                                 one_month=one_month,
                                 times=times)

@user.route('/albums/')
def albums_overview(user_id: int):

    # All Time
    overall = db.get_top_albums(user_id, images=False)

    # Past 6 Months
    period = daterange.last_n_months(6)

    six_months = db.get_top_albums(user_id, period, images=False)

    # Past 1 Month
    period = daterange.last_n_months(1)

    one_month = db.get_top_albums(user_id, period, images=False)

    return flask.render_template('top_albums.html',
                                 overall=overall,
                                 six_months=six_months,
                                 one_month=one_month)

@user.route('/songs/')
def songs_overview(user_id: int):

    # All Time
    overall = db.get_top_songs(user_id, images=False)

    # Past 6 Months
    period = daterange.last_n_months(6)

    six_months = db.get_top_songs(user_id, period, images=False)

    # Past 1 Month
    period = daterange.last_n_months(1)

    one_month = db.get_top_songs(user_id, period, images=False)

    return flask.render_template('top_songs.html',
                                 overall=overall,
                                 six_months=six_months,
                                 one_month=one_month)


@user.route('/biggraph/<int:artist>/')
def big_artist_graph(user_id: int, artist: int):

    graphs.generate_artist_graph(user_id, artist, daterange.daily_ranges(365), 'yd')

    return flask.send_file(f"static/{artist}-yd.png")

@user.route('/wrapped/<int:year>/')
def wrapped(user_id: int, year: int):
    logger.info("User asking for wrapped endpoint")

    end = datetime.datetime.strptime(f"12-31-{year}", "%m-%d-%Y")
    start = end - dateutil.relativedelta.relativedelta(years=1)

    period = daterange.DateRange(start, end)

    logger.debug("Getting top info")
    top_artists = db.get_top_artists(user_id, period, top=10)
    top_albums = db.get_top_albums(user_id, period, top=10)
    top_songs = db.get_top_songs(user_id, period, top=10)

    stats = {}

    logger.debug("Getting total time")
    stats["time"] = db.get_total_time(user_id, period).to_hour_and_seconds()

    logger.debug("Getting counts")
    stats["artist_count"] = db.get_artist_count(user_id, period)
    stats["album_count"] = db.get_album_count(user_id, period)
    stats["song_count"] = db.get_song_count(user_id, period)

    logger.debug("Getting top played things?")
    top_played_artists = db.get_top_played_artists(user_id, period, top=10)
    top_played_songs = db.get_top_played_songs(user_id, period, top=10)

    top_skipped_songs = db.get_top_skipped_songs(user_id, period, top=10)

    return flask.render_template("wrapped.html",
                                 stats=stats,
                                 year=year,
                                 top_albums=top_albums,
                                 top_songs=top_songs,
                                 top_artists=top_artists,
                                 top_skipped_songs=top_skipped_songs,
                                 top_played_artists=top_played_artists,
                                 top_played_songs=top_played_songs)

# OTHER

@user.route('/compare/')
def compare(user_id: int):

    # Get most recent from spotify
    current_user = User(user_id)

    recent = current_user.api.current_user_recently_played()

    spotify_50 = []
    for track in recent["items"]:

        track = track['track']

        song_name = track["name"]
        artists = ""

        for artist in track["artists"]:
            artists += artist["name"]

            if artist != track["artists"][-1]:
                artists += ", "

        spotify_50.append(f"{song_name} by {artists.lower()}")

    # Get most recent from database
    database_50 = []

    recent = db.get_last_n(user_id)

    for result in recent:
        song_id = result[0]
        song_name = db.get_song_name_by_id(song_id)

        artists = ""

        for artist in (result := db.get_songs_artists(song_id)):
            artists += artist

            if artist != result[-1]:
                artists += ", "

        database_50.append(f"{song_name} by {artists}")

    matches = len(set(spotify_50) & set(database_50))

    accuracy: float = (matches / 50) * 100

    return flask.render_template("compare.html",
                                 accuracy=accuracy,
                                 database_50=database_50,
                                 spotify_50=spotify_50)

"""
A basic implementation of a playlist mixing algorithm

Calling it an 'algorithm' might be a stretch

The idea is that I can go back X amount of time and look at a users top played songs
I take the top PLAYED song and take not of that (let's call that number of plays M)

I then go through the top Y played songs giving them a weight of (M) divided by their number of plays (P)

So
W = M/P

Then I go through their top played songs for a much shorter amount of time (like a month / week or so)
and do the same thing. That way I can get a mix of songs they've recently enjoyed + what they've been enjoying
for a while.

TODO:
    - tweak algo?
    - have link to playlist at bottom of page

"""
@user.route('/mix/')
def mix_playlist(user_id: int):

    if 'api' not in flask.session:
        return 'please login :)'

    output = ""

    api: spotipy.Spotify = flask.session['api']
    user_id: str = flask.session['user']['id']
    playlist = []
    negative_weights = []


    # Fetch playlist info
    with open("./data/generated-playlists.json", 'r') as f:
        playlists_json = json.loads(f.read())

    # If no existing playlist make one
    if user_id not in playlists_json:
        r = api.user_playlist_create(user_id, "0x01fe.net Mix", description="Playlist generated by stats.0x01fe.net")

        playlist_id = r['id']
        playlists_json[user_id] = playlist_id

        # Write id of playlist made
        with open("./data/generated-playlists.json", 'w') as f:
            f.write(json.dumps(playlists_json))

    # Clear playlist if exists
    else:
        playlist_id = playlists_json[user_id]

        r = api.user_playlist_tracks(user_id, playlist_id)

        if r['items']:
            uris_to_delete = []
            for song in r['items']:
                if song['track']:
                    uris_to_delete.append(song['track']['uri'])
                    negative_weights.append((None, song['track']['id'], LAST_PLAYLIST_NEGATIVE_WEIGHT))

            if uris_to_delete:
                api.user_playlist_remove_all_occurrences_of_tracks(user_id, playlist_id, uris_to_delete)

    offset = 0
    while len(playlist) <= 50:
        weights = negative_weights if negative_weights else []

        add_weights(weights, db.get_mix_weights(user_id, daterange.last_n_months(6), 40, offset)) # Get some "older" stuff
        add_weights(weights, db.get_mix_weights(user_id, daterange.last_n_months(1), 40, offset)) # Get some newer stuff

        # get some OLD stuff
        period = daterange.last_n_months(18)

        period.end = period.start + dateutil.relativedelta.relativedelta(months=6)
        add_weights(weights, db.get_mix_weights(user_id, period, 20, offset))


        # Mix it prioritizing stuff with higher play counts
        playlist.extend(mix_songs(weights))
        offset += 20

    for song in playlist:
        for i in song:
            output += str(i) + ', '
        output += '<br>'

    output += f'<br>{len(playlist)} Songs'

    uris = []
    for song in playlist:
        uris.append(f'spotify:track:{song[1]}')

    print(uris)
    if len(uris) > 99:
        uris = uris[:99]

    api.playlist_add_items(playlist_id, uris)

    return output

def add_weights(weights1: list, weights2: list) -> list:

    # Add duplicate item weights, otherwise append
    for a in range(0, len(weights2)):
        found = False
        for b in range(0, len(weights1)):
            if weights1[b][1] == weights2[a][1]:
                weights1.append((weights1[b][1], weights1[b][-1] + weights2[a][-1]))
                weights1.pop(b)
                weights2.pop(a)
                found = True

        if not found:
            weights1.append(weights2[a])

    # Remove dupes
    weights1.sort()
    weights1 = list(k for k, _ in itertools.groupby(weights1))

    return weights1

def mix_songs(weights : list) -> list:
    playlist = []

    for song in weights:
        weight: float = song[-1]

        P = random.randint(0, 100) / 100.0

        if P <= weight:
            playlist.append(song)

    return playlist
