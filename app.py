import dateutil.relativedelta
import datetime
import configparser
import calendar

import flask
import flask_wtf.csrf
import waitress
import matplotlib
import matplotlib.pyplot

import db
import date_range
import listen_time


matplotlib.use("agg")
matplotlib.font_manager.fontManager.addfont("./static/CyberpunkWaifus.ttf")

app = flask.Flask(__name__, static_url_path='', static_folder='static')

csrf = flask_wtf.csrf.CSRFProtect()
csrf.init_app(app)

config = configparser.ConfigParser()
config.read("config.ini")

templates_path = config['PATHES']['templates']
DATABASE = config['PATHES']['DATABASE']





def color_graph(title : str, ax : matplotlib.axes.Axes, plot : matplotlib.lines.Line2D) -> matplotlib.axes.Axes:
    # Graph Background
    ax.set_facecolor("#00031c")

    # Graph Border
    for spine in ax.spines.values():
        spine.set_color('xkcd:pink')

    # Data Line Color
    for line in plot:
        line.set_color("xkcd:hot pink")

    # Axis Label Colors
    ax.set_xlabel('Date', color="xkcd:hot pink", font="CyberpunkWaifus", fontsize=15)
    ax.set_ylabel("Time (Hours)", color="xkcd:hot pink", font="CyberpunkWaifus", fontsize=15)

    # Tick colors
    ax.tick_params(axis="x", colors="xkcd:powder blue")
    ax.tick_params(axis="y", colors="xkcd:powder blue")

    # Title Color
    ax.set_title(title, color="xkcd:hot pink", font="CyberpunkWaifus", fontsize=20)

    # Grid
    ax.grid(color="xkcd:dark purple")

    return ax

'''
takes in a period of time to use as the X-axis
acceptable periods :
    - month
    - week
    - day

Returns path to graph
'''
def generate_overall_graph(user_id : int, period : str) -> str:
    # Analyze the past 12 months, including this one so far.
    if period == 'month':
        now = datetime.datetime.now()

        totals = []
        dates = []
        for i in range(1, 13):
            start = now - dateutil.relativedelta.relativedelta(months=i) # Why does normal timedelta not support months?
            end = now - dateutil.relativedelta.relativedelta(months=i-1)
            time = db.get_total_time(user_id, date_range.DateRange(start, end))

            if not time:
                break

            totals.append(time.to_hours())
            dates.append(start.strftime("%Y-%m-%d"))

        totals = list(reversed(totals))
        dates = list(reversed(dates))

        fig, ax = matplotlib.pyplot.subplots(facecolor="xkcd:black")
        line = ax.plot(dates, totals)

        color_graph("Monthly Summary", ax, line)

        for i, txt in enumerate(totals):
            ax.annotate(txt, (dates[i], totals[i]), color="xkcd:powder blue")

        fig.savefig("static/month.png")

    # Graph of the past eight weeks
    elif period == 'week':
        now = datetime.datetime.now()

        totals = []
        dates = []

        for i in range(1, 9):
            start = now - dateutil.relativedelta.relativedelta(weeks=i) # Why does normal timedelta not support months?
            end = now - dateutil.relativedelta.relativedelta(weeks=i-1)
            time = db.get_total_time(user_id, date_range.DateRange(start, end))

            if not time:
                time = listen_time.ListenTime(0)

            totals.append(time.to_hours())
            dates.append(start.strftime("%Y-%m-%d"))

        totals = list(reversed(totals))
        dates = list(reversed(dates))

        fig, ax = matplotlib.pyplot.subplots(facecolor="xkcd:black")
        line = ax.plot(dates, totals)

        color_graph("Weekly Summary", ax, line)

        for i, txt in enumerate(totals):
            ax.annotate(txt, (dates[i], totals[i]), color="xkcd:powder blue")

        fig.savefig("static/week.png", bbox_inches='tight')

    # Graph of the past 14 days
    elif period == 'day':
        now = datetime.datetime.strptime("2023-09-16", "%Y-%m-%d")

        totals = []
        dates = []

        for i in range(1, 9):
            start = now - dateutil.relativedelta.relativedelta(days=i) # Why does normal timedelta not support months?
            end = now - dateutil.relativedelta.relativedelta(days=i-1)
            time = db.get_total_time(user_id, date_range.DateRange(start, end))

            if not time:
                time = listen_time.ListenTime(0)

            totals.append(time.to_hours())
            dates.append(start.strftime("%m-%d"))

        totals = list(reversed(totals))
        dates = list(reversed(dates))

        fig, ax = matplotlib.pyplot.subplots(facecolor="xkcd:black")
        line = ax.plot(dates, totals)

        color_graph("Daily Summary", ax, line)

        for i, txt in enumerate(totals):
            ax.annotate(txt, (dates[i], totals[i]), color="xkcd:powder blue")

        fig.savefig("static/day.png", bbox_inches='tight')

    else:
        return 'bad period'

    matplotlib.pyplot.close()
    return f'static/{period}.png'



@app.route('/<int:user>/')
def overview(user : int):

    for period in ['day', 'week', 'month']:
        generate_overall_graph(user, period)


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

    return flask.render_template('artist.html', artist_name=artist_name, artist_listen_time=total_time, top_albums=top_albums, top_songs=top_songs)

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



@app.route('/')
def root():
    return 'home'

if __name__ == '__main__':
    waitress.serve(app, host='0.0.0.0', port=802)
