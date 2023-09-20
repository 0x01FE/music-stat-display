from flask import Flask, render_template
import matplotlib
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
from flask_wtf.csrf import CSRFProtect
from waitress import serve

from datetime import datetime
from configparser import ConfigParser
import calendar

import db
import utils


matplotlib.use("agg")
matplotlib.font_manager.fontManager.addfont("./static/CyberpunkWaifus.ttf")

app = Flask(__name__, static_url_path='', static_folder='static')

csrf = CSRFProtect()
csrf.init_app(app)

config = ConfigParser()
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
        now = datetime.now()

        totals = []
        dates = []
        for i in range(1, 13):
            start = now - relativedelta(months=i) # Why does normal timedelta not support months?
            end = now - relativedelta(months=i-1)
            time = db.get_total_time(user_id, start, end)

            if not time:
                break

            totals.append(time.to_hours())
            dates.append(start.strftime("%Y-%m-%d"))

        totals = list(reversed(totals))
        dates = list(reversed(dates))

        fig, ax = plt.subplots(facecolor="xkcd:black")
        line = ax.plot(dates, totals)

        color_graph("Monthly Summary", ax, line)

        for i, txt in enumerate(totals):
            ax.annotate(txt, (dates[i], totals[i]), color="xkcd:powder blue")

        fig.savefig("static/month.png")

    # Graph of the past eight weeks
    elif period == 'week':
        now = datetime.now()

        totals = []
        dates = []

        for i in range(1, 9):
            start = now - relativedelta(weeks=i) # Why does normal timedelta not support months?
            end = now - relativedelta(weeks=i-1)
            time = db.get_total_time(user_id, start, end)

            if not time:
                break

            totals.append(time.to_hours())
            dates.append(start.strftime("%Y-%m-%d"))

        totals = list(reversed(totals))
        dates = list(reversed(dates))

        fig, ax = plt.subplots(facecolor="xkcd:black")
        line = ax.plot(dates, totals)

        color_graph("Weekly Summary", ax, line)

        for i, txt in enumerate(totals):
            ax.annotate(txt, (dates[i], totals[i]), color="xkcd:powder blue")

        fig.savefig("static/week.png", bbox_inches='tight')

    # Graph of the past 14 days
    elif period == 'day':
        now = datetime.now()

        totals = []
        dates = []

        for i in range(1, 9):
            start = now - relativedelta(days=i) # Why does normal timedelta not support months?
            end = now - relativedelta(days=i-1)
            time = db.get_total_time(user_id, start, end)

            if not time:
                break

            totals.append(time.to_hours())
            dates.append(start.strftime("%m-%d"))

        totals = list(reversed(totals))
        dates = list(reversed(dates))

        fig, ax = plt.subplots(facecolor="xkcd:black")
        line = ax.plot(dates, totals)

        color_graph("Daily Summary", ax, line)

        for i, txt in enumerate(totals):
            ax.annotate(txt, (dates[i], totals[i]), color="xkcd:powder blue")

        fig.savefig("static/day.png", bbox_inches='tight')

    else:
        return 'bad period'

    plt.close()
    return f'static/{period}.png'



@app.route('/<int:user>/')
def overview(user : int):

    for period in ['day', 'week', 'month']:
        generate_overall_graph(user, period)


    today = datetime.today()

    top_artists = db.get_top_artists(user, top=5)
    top_albums = db.get_top_albums(user, top=5)
    top_songs = db.get_top_songs(user, top=5)

    total_time = db.get_total_time(user).to_hour_and_seconds()

    artist_count = db.get_artist_count(user)
    album_count = db.get_album_count(user)
    song_count = db.get_song_count(user)


    return render_template('overall.html', top_albums=top_albums, top_songs=top_songs, top_artists=top_artists, year=today.year, month=today.month, artist_count=artist_count, total_time=total_time, album_count=album_count, song_count=song_count)

@app.route('/<int:user>/artists/')
def artists_overview(user: int):

    top_artists = db.get_top_artists(user)

    return render_template('artists_overview.html', data=top_artists)

@app.route('/<int:user>/artists/<artist>/')
def artist_overview(user: int, artist : str):
    artist = artist.lower()

    total_time = db.get_artist_total(user, artist).to_hour_and_seconds()
    top_albums = db.get_artist_top_albums(user, artist)
    top_songs = db.get_artist_top_songs(user, artist)

    return render_template('artist.html', artist_name=artist.replace('-', ' ').title(), artist_listen_time=total_time, top_albums=top_albums, top_songs=top_songs)

@app.route('/<int:user>/albums/')
def albums_overview(user : int):
    top_albums = db.get_top_albums(user)

    return render_template('albums_overview.html', top_albums=top_albums)

@app.route('/<int:user>/songs/')
def songs_overview(user : int):
    top_songs = db.get_top_songs(user)

    return render_template('songs_overview.html', top_songs=top_songs)



@app.route('/<int:user>/month/<int:year>/<int:month>/')
def month_overview(user : int, year : int, month : int):

    if not utils.valid_month(year, month):
        return "Invalid month or year."

    start, end = utils.calculate_date_range(year, month)

    top_artists = db.get_top_artists(user, start, end, top=5)
    top_albums = db.get_top_albums(user, start, end, top=5)
    top_songs = db.get_top_songs(user, start, end, top=5)

    if not (total_time := db.get_total_time(user, start, end)):
        return "No data for this month."
    total_time = total_time.to_hour_and_seconds()

    artist_count = db.get_artist_count(user, start, end)
    album_count = db.get_album_count(user, start, end)
    song_count = db.get_song_count(user, start, end)


    links = (f"../../{year}/{month - 1}", f"../../{year}/{month + 1}")

    return render_template('month_overview.html', month_name=calendar.month_name[month], year=year, top_artists=top_artists, top_albums=top_albums, top_songs=top_songs, artist_count=artist_count, total_time=total_time, album_count=album_count, song_count=song_count)


@app.route('/<int:user>/month/<int:year>/<int:month>/artists/<artist>/')
def artist_month_overview(user : int, year : int, month : int, artist : str):
    artist = artist.lower()

    if not utils.valid_month(year, month):
        return "Invalid month or year."

    start, end = utils.calculate_date_range(year, month)

    total_time = db.get_artist_total(user, artist, start, end).to_hour_and_seconds()
    top_albums = db.get_artist_top_albums(user, artist, start, end)
    top_songs = db.get_artist_top_songs(user, artist, start, end)

    return render_template('artist_month_overview.html', artist_name=artist.replace('-', ' ').title(), month_name=calendar.month_name[month], year=year, artist_listen_time=total_time, top_albums=top_albums, top_songs=top_songs)

@app.route('/<int:user>/month/<int:year>/<int:month>/artists/')
def artists_month_overview(user : int, year : int, month : int):

    if not utils.valid_month(year, month):
        return "Invalid month or year."

    start, end = utils.calculate_date_range(year, month)

    top_artists = db.get_top_artists(user, start, end)

    return render_template('artists_month_overview.html', top_artists=top_artists, month_name=calendar.month_name[month], year=year)

@app.route('/<int:user>/month/<int:year>/<int:month>/albums/')
def albums_month_overview(user : int, year : int, month : int):

    if not utils.valid_month(year, month):
        return "Invalid month or year."

    start, end = utils.calculate_date_range(year, month)

    top_albums = db.get_top_albums(user, start, end)

    return render_template('albums_month_overview.html', top_albums=top_albums, month_name=calendar.month_name[month], year=year)

@app.route('/<int:user>/month/<int:year>/<int:month>/songs/')
def songs_month_overview(user : int, year : int, month : int):

    if not utils.valid_month(year, month):
        return "Invalid month or year."

    start, end = utils.calculate_date_range(year, month)

    top_songs = db.get_top_songs(user, start, end)

    return render_template('songs_month_overview.html', top_songs=top_songs, month_name=calendar.month_name[month], year=year)



@app.route('/')
def root():
    return 'home'



if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=802)
