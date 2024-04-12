import dateutil.relativedelta
import datetime
import configparser
import calendar
import os
import base64


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

    today = datetime.datetime.today()

    top_artists = db.get_top_artists(user, top=10)
    top_albums = db.get_top_albums(user, top=10)
    top_songs = db.get_top_songs(user, top=10)

    total_time = db.get_total_time(user).to_hour_and_seconds()

    artist_count = db.get_artist_count(user)
    album_count = db.get_album_count(user)
    song_count = db.get_song_count(user)


    return flask.render_template('user_home.html',
                                 top_albums=top_albums,
                                 top_songs=top_songs,
                                 top_artists=top_artists,
                                 year=today.year,
                                 month=today.month,
                                 artist_count=artist_count,
                                 total_time=total_time,
                                 album_count=album_count,
                                 song_count=song_count,
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

@app.route('/<int:user>/wrapped/<int:year>/')
def wrapped(user : int, year : int):

    end = datetime.datetime.strptime(f"12-31-{year}", "%m-%d-%Y")
    start = end - dateutil.relativedelta.relativedelta(years=1)

    period = date_range.DateRange(start, end)

    top_artists = db.get_top_artists(user, period, top=10)
    top_albums = db.get_top_albums(user, period, top=10)
    top_songs = db.get_top_songs(user, period, top=10)

    total_time = db.get_total_time(user, period)
    total_time = total_time.to_hour_and_seconds()

    artist_count = db.get_artist_count(user, period)
    album_count = db.get_album_count(user, period)
    song_count = db.get_song_count(user, period)

    top_played_artists = db.get_top_played_artists(user, period, top=10)
    top_played_songs = db.get_top_played_songs(user, period, top=10)

    top_skipped_songs = db.get_top_skipped_songs(user, period, top=10)

    return flask.render_template("wrapped.html", year=year, top_albums=top_albums, top_songs=top_songs, top_artists=top_artists, artist_count=artist_count, total_time=total_time, album_count=album_count, song_count=song_count, top_skipped_songs=top_skipped_songs, top_played_artists=top_played_artists, top_played_songs=top_played_songs)

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


if __name__ == '__main__':
    if 'env' in os.environ:
        if os.environ['env'] == 'DEV':
            app.run()
        else:
            waitress.serve(app, host='0.0.0.0', port=PORT)
    else:
        waitress.serve(app, host='0.0.0.0', port=PORT)
