import dateutil.relativedelta
import datetime
import random
import configparser
import itertools
import calendar
import os
import base64
import json


import flask
import flask_session
import flask_wtf.csrf
import waitress
import spotipy
import wtforms


import db
import date_range
import graphs
from user import User

app = flask.Flask(__name__, static_url_path='', static_folder='static')

csrf = flask_wtf.csrf.CSRFProtect()
csrf.init_app(app)

# App Setup
config = configparser.ConfigParser()

dev = False
if 'env' in os.environ:
    dev = os.environ['env'] == 'DEV'

if dev:
    config.read("config-dev.ini")
else:
    config.read("config.ini")

templates_path = config['PATHES']['templates']
DATABASE = config['PATHES']['DATABASE']
PORT = config['NETWORK']['PORT']

# Spotipy Setup
SCOPES = config["SPOTIFY"]["SCOPES"]

# Session Setup
app.config['SECRET_KEY'] = base64.b64decode(config["FLASK"]["SECRET"])
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './data/.flask_session/'
flask_session.Session(app)


# Other
LAST_PLAYLIST_NEGATIVE_WEIGHT = -0.5


@app.route('/')
def root():

    auth_manager = spotipy.oauth2.SpotifyOAuth(scope=SCOPES, show_dialog=True)

    # Being redirected from Spotify auth page
    if flask.request.args.get("code"):
        auth_manager.get_access_token(flask.request.args.get("code"))

        # Get user info
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        user_info = spotify.me()

        flask.session["user"] = user_info
        flask.session["api"] = spotify

        # if user is not in database
        if not db.user_exists(user_info['id']):

            print("User not in database, adding...")

            # Save token for use in tracking container
            cache_handler = spotipy.CacheFileHandler(cache_path=f"./data/.{user_info['id']}-cache")
            cache_handler.save_token_to_cache(auth_manager.get_cached_token())

            # Add user to database
            db.add_user(user_info['display_name'], user_info['id'])

        return flask.redirect('/')

    if 'user' not in flask.session:
        auth_url = auth_manager.get_authorize_url()

        return flask.render_template('login_index.html', auth_url=auth_url)

    else:
        user_id = db.get_user_id(flask.session['user']['id'])

        print(f'redirect to /{user_id}/')
        return flask.redirect(f'/{user_id}/')

@app.route('/logout/')
def logout():
    if 'user' in flask.session:
        flask.session.pop('user')
    if 'api' in flask.session:
        flask.session.pop('api')
    return flask.redirect('/')

@app.route('/<int:user>/')
def user_home(user : int):

    # Check if this user should be accessed
    if 'user' in flask.session:
        accessing_user = db.get_user_id(flask.session['user']['id'])
        display_name = flask.session['user']['display_name']
        user_pfp_url = flask.session['user']['images'][0]['url']

    else:
        accessing_user = None
        display_name = None
        user_pfp_url = None

    if not db.is_user_public(user) and accessing_user != user:
        return "This user's profile is not public!"

    info = {}
    info["artist_count"] = db.get_artist_count(user)
    info["album_count"] = db.get_album_count(user)
    info["song_count"] = db.get_song_count(user)
    info["id"] = user

    today = datetime.datetime.today()
    six_m_period = date_range.last_n_months(6)
    one_m_period = date_range.last_n_months(1)

    times = {
        "overall" : db.get_total_time(user).to_hour_and_seconds(),
        "six_months" : db.get_total_time(user, six_m_period).to_hour_and_seconds(),
        # "one_month" : db.get_total_time(user, one_m_period).to_hour_and_seconds()
    }

    periods = [
        {
            "name" : "all-time",
            "top_artists" : db.get_top_artists(user, top=10),
            "top_albums" : db.get_top_albums(user, top=10),
            "top_songs" : db.get_top_songs(user, top=10)
        },
        {
            "name" : "6m",
            "top_artists" : db.get_top_artists(user, six_m_period, top=10),
            "top_albums" : db.get_top_albums(user, six_m_period, top=10),
            "top_songs" : db.get_top_songs(user, six_m_period, top=10)
        },
        {
            "name" : "4w",
            "top_artists" : db.get_top_artists(user, one_m_period, top=10),
            "top_albums" : db.get_top_albums(user, one_m_period, top=10),
            "top_songs" : db.get_top_songs(user, one_m_period, top=10)
        }
    ]

    # Generate graphs
    graphs.generate_daily_graph(user)
    graphs.generate_weekly_graph(user)
    graphs.generate_monthly_graph(user)

    return flask.render_template('user_home.html',
                                 info=info,
                                 times=times,
                                 periods=periods,
                                 year=today.year,
                                 month=today.month,
                                 display_name=display_name,
                                 user_pfp_url=user_pfp_url)

class SettingsForm(flask_wtf.FlaskForm):
    checkbox = wtforms.BooleanField('Public')

@app.route('/settings/')
def settings():

    form = SettingsForm()

    if 'user' in flask.session:
        display_name = flask.session['user']['display_name']
        user_pfp_url = flask.session['user']['images'][0]['url']
    else:
        return flask.redirect('/')

    return flask.render_template('user_settings.html', display_name=display_name, user_pfp_url=user_pfp_url, form=form)

@app.route('/settings/save/', methods=['POST'])
def settings_save():
    form = SettingsForm(csrf_enabled=True)

    user_spotify_id = flask.session['user']['id']

    db.update_public(user_spotify_id, form.checkbox.data)

    return flask.redirect('/settings/')

@app.route('/<int:user>/artists/')
def artists_overview(user: int):

    # All Time
    overall = db.get_top_artists(user, images=False)

    # Past 6 Months
    period = date_range.last_n_months(6)

    six_months = db.get_top_artists(user, period, images=False)

    # Past 1 Month
    period = date_range.last_n_months(1)

    one_month = db.get_top_artists(user, period, images=False)

    return flask.render_template('top_artists.html',
                                 overall=overall,
                                 six_months=six_months,
                                 one_month=one_month)

@app.route('/<int:user>/artists/<artist>/')
def artist_overview(user: int, artist : int):

    times = {}

    # All Time
    overall = {}

    times["overall"] = db.get_artist_total(user, artist).to_hour_and_seconds()
    overall["top_albums"] = db.get_artist_top_albums(user, artist)
    overall["top_songs"] = db.get_artist_top_songs(user, artist)

    artist_info = db.get_artist_info(artist)

    # Past 6 Months
    period = date_range.last_n_months(6)

    six_months = {}

    times["six_months"] = db.get_artist_total(user, artist, period)
    if times["six_months"]:
        times["six_months"] = times["six_months"].to_hour_and_seconds()
    six_months["top_albums"] = db.get_artist_top_albums(user, artist, period)
    six_months["top_songs"] = db.get_artist_top_songs(user, artist, period)

    # Past 1 Month
    period = date_range.last_n_months(1)

    one_month = {}

    times["one_month"] = db.get_artist_total(user, artist, period)
    if times["one_month"]:
        times["one_month"] = times["one_month"].to_hour_and_seconds()
    one_month["top_albums"] = db.get_artist_top_albums(user, artist, period)
    one_month["top_songs"] = db.get_artist_top_songs(user, artist, period)

    return flask.render_template('artist.html', artist_info=artist_info, overall=overall, six_months=six_months, one_month=one_month, times=times)

@app.route('/<int:user>/albums/')
def albums_overview(user : int):

    # All Time
    overall = db.get_top_albums(user, images=False)

    # Past 6 Months
    period = date_range.last_n_months(6)

    six_months = db.get_top_albums(user, period, images=False)

    # Past 1 Month
    period = date_range.last_n_months(1)

    one_month = db.get_top_albums(user, period, images=False)

    return flask.render_template('top_albums.html',
                                 overall=overall,
                                 six_months=six_months,
                                 one_month=one_month)

@app.route('/<int:user>/songs/')
def songs_overview(user : int):

    # All Time
    overall = db.get_top_songs(user, images=False)

    # Past 6 Months
    period = date_range.last_n_months(6)

    six_months = db.get_top_songs(user, period, images=False)

    # Past 1 Month
    period = date_range.last_n_months(1)

    one_month = db.get_top_songs(user, period, images=False)

    return flask.render_template('top_songs.html',
                                 overall=overall,
                                 six_months=six_months,
                                 one_month=one_month)

@app.route('/<int:user>/biggraph/<int:artist>/')
def big_artist_graph(user : int, artist : int):

    graphs.generate_artist_graph(user, artist, date_range.daily_ranges(365), 'yd')

    return flask.send_file(f"static/{artist}-yd.png")

@app.route('/<int:user>/wrapped/<int:year>/')
def wrapped(user : int, year : int):

    end = datetime.datetime.strptime(f"12-31-{year}", "%m-%d-%Y")
    start = end - dateutil.relativedelta.relativedelta(years=1)

    period = date_range.DateRange(start, end)

    top_artists = db.get_top_artists(user, period, top=10)
    top_albums = db.get_top_albums(user, period, top=10)
    top_songs = db.get_top_songs(user, period, top=10)

    stats = {}

    stats["time"] = db.get_total_time(user, period).to_hour_and_seconds()

    stats["artist_count"] = db.get_artist_count(user, period)
    stats["album_count"] = db.get_album_count(user, period)
    stats["song_count"] = db.get_song_count(user, period)

    top_played_artists = db.get_top_played_artists(user, period, top=10)
    top_played_songs = db.get_top_played_songs(user, period, top=10)

    top_skipped_songs = db.get_top_skipped_songs(user, period, top=10)

    return flask.render_template("wrapped.html",
                                 stats=stats,
                                 year=year,
                                 top_albums=top_albums,
                                 top_songs=top_songs,
                                 top_artists=top_artists,
                                 top_skipped_songs=top_skipped_songs,
                                 top_played_artists=top_played_artists,
                                 top_played_songs=top_played_songs)

@app.route('/db/')
def database():
    return flask.send_file(DATABASE)

@app.route('/<int:user>/compare/')
def compare(user : int):

    # Get most recent from spotify
    current_user = User(user)

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

    recent = db.get_last_n(user)

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

    return flask.render_template("compare.html", accuracy=accuracy, database_50=database_50, spotify_50=spotify_50)


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
@app.route('/<int:user>/mix/')
def mix_playlist(user : int):

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

        add_weights(weights, db.get_mix_weights(user, date_range.last_n_months(6), 40, offset)) # Get some "older" stuff
        add_weights(weights, db.get_mix_weights(user, date_range.last_n_months(1), 40, offset)) # Get some newer stuff

        # get some OLD stuff
        period = date_range.last_n_months(18)

        period.end = period.start + dateutil.relativedelta.relativedelta(months=6)
        add_weights(weights, db.get_mix_weights(user, period, 20, offset))


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


if __name__ == '__main__':
    if 'env' in os.environ:
        if dev:
            app.run(port=PORT)
        else:
            waitress.serve(app, host='0.0.0.0', port=PORT)
    else:
        waitress.serve(app, host='0.0.0.0', port=PORT)
