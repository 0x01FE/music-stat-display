from flask import Flask, render_template
import matplotlib
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
from flask_wtf.csrf import CSRFProtect
from waitress import serve

from datetime import datetime
from math import floor
from configparser import ConfigParser
import calendar

import db

matplotlib.use("agg")
app = Flask(__name__, static_url_path='', static_folder='static')

csrf = CSRFProtect()
csrf.init_app(app)

config = ConfigParser()
config.read("config.ini")

templates_path = config['PATHES']['templates']
DATABASE = config['PATHES']['DATABASE']




def msToHour(mili : int) -> int:
    return round(mili/1000/60/60, 1)

def listenTimeFormat(mili : int) -> tuple:

    minutes = mili/1000/60
    hours = floor(minutes/60)

    return (hours, round(minutes % 60, 2))

def calculate_total_listening_time(data : dict) -> int:

    overall_time = 0
    for artist in data:
        overall_time += data[artist]["overall"]

    return overall_time


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

            totals.append(msToHour(time))
            dates.append(start.strftime("%Y-%m-%d"))

        totals = list(reversed(totals))
        dates = list(reversed(dates))

        fig, ax = plt.subplots()
        ax.plot(dates, totals)
        ax.set(xlabel='Date', ylabel='time (hours)', title='Listening Time')
        ax.grid()

        for i, txt in enumerate(totals):
            ax.annotate(txt, (dates[i], totals[i]))

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

            totals.append(msToHour(time))
            dates.append(start.strftime("%Y-%m-%d"))

        totals = list(reversed(totals))
        dates = list(reversed(dates))

        fig, ax = plt.subplots()
        ax.plot(dates, totals)
        ax.set(xlabel='Date', ylabel='time (hours)', title='Listening Time')
        ax.grid()

        for i, txt in enumerate(totals):
            ax.annotate(txt, (dates[i], totals[i]))

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

            totals.append(msToHour(time))
            dates.append(start.strftime("%Y-%m-%d"))

        totals = list(reversed(totals))
        dates = list(reversed(dates))

        fig, ax = plt.subplots()
        ax.plot(dates, totals)
        ax.set(xlabel='Date', ylabel='time (hours)')
        ax.grid()

        for i, txt in enumerate(totals):
            ax.annotate(txt, (dates[i], totals[i]))

        fig.savefig("static/day.png", bbox_inches='tight')

    else:
        return 'bad period'

    plt.close()
    return f'static/{period}.png'



@app.route('/<int:user>/')
def user_root(user : int):

    for period in ['day', 'week', 'month']:
        generate_overall_graph(user, period)


    today = datetime.today()

    top_artists = db.get_top_artists(user, top=5)
    top_albums = db.get_top_albums(user, top=5)
    top_songs = db.get_top_songs(user, top=5)

    total_time = listenTimeFormat(db.get_total_time(user))

    artist_count = db.get_artist_count(user)
    album_count = db.get_album_count(user)
    song_count = db.get_song_count(user)


    return render_template('home.html', top_albums=top_albums, top_songs=top_songs, top_artists=top_artists, year=today.year, month=today.month, artist_count=artist_count, total_time=total_time, album_count=album_count, song_count=song_count)




@app.route('/<int:user>/artists/')
def overall_artists(user: int):

    top_artists = db.get_top_artists(user)

    return render_template('overall_artists.html', data=top_artists)

@app.route('/<int:user>/albums/')
def overall_albums(user : int):
    top_albums = db.get_top_albums(user)

    return render_template('overall_albums.html', top_albums=top_albums)

@app.route('/<int:user>/songs/')
def overall_songs(user : int):
    top_songs = db.get_top_songs(user)

    return render_template('overall_songs.html', top_songs=top_songs)



@app.route('/<int:user>/month/<int:year>/<int:month>/')
def overall_month(user : int, year : int, month : int):

    today = datetime.now()

    if month > today.month or month < 1:
        return 'Month is invalid'

    last_day = calendar.monthrange(year, month)[1]

    if month < 10:
        end = datetime.strptime(f"{year}-0{month}-{last_day}", "%Y-%m-%d")
    else:
        end = datetime.strptime(f"{year}-{month}-{last_day}", "%Y-%m-%d")

    start = datetime.strptime(f"{year}-{month}", "%Y-%m")

    top_artists = db.get_top_artists(user, start, end)
    if not (total_time := db.get_total_time(user, start, end)):
        return "No data for this month."
    total_time = listenTimeFormat(total_time)
    artist_count = db.get_artist_count(user, start, end)


    links = (f"../../{year}/{month - 1}", f"../../{year}/{month + 1}")

    return render_template('overall_month.html', data=top_artists, month_name=calendar.month_name[month], year=year, selector_links=links, month_total=total_time, artist_total=artist_count)



@app.route('/<int:user>/month/<int:year>/<int:month>/<artist>/')
def artist_month(user : int, year : int, month : int, artist : str):
    artist = artist.lower()

    today = datetime.now()

    if month > today.month or month < 1:
        return 'Month is invalid'

    last_day = calendar.monthrange(year, month)[1]

    if month < 10:
        end = datetime.strptime(f"{year}-0{month}-{last_day}", "%Y-%m-%d")
    else:
        end = datetime.strptime(f"{year}-{month}-{last_day}", "%Y-%m-%d")

    start = datetime.strptime(f"{year}-{month}", "%Y-%m")

    total_time = listenTimeFormat(db.get_artist_total(user, artist, start, end))
    top_albums = db.get_artist_top_albums(user, artist, start, end)
    top_songs = db.get_artist_top_songs(user, artist, start, end)

    return render_template('artist_month.html', artist_name=artist.replace('-', ' ').title(), month_name=calendar.month_name[month], year=year, artist_listen_time=total_time, top_albums=top_albums, top_songs=top_songs)




@app.route('/<int:user>/<artist>/')
def artist(user: int, artist : str):
    artist = artist.lower()

    total_time = listenTimeFormat(db.get_artist_total(user, artist))
    top_albums = db.get_artist_top_albums(user, artist)
    top_songs = db.get_artist_top_songs(user, artist)

    return render_template('artist.html', artist_name=artist.replace('-', ' ').title(), artist_listen_time=total_time, top_albums=top_albums, top_songs=top_songs)

@app.route('/')
def root():
    return 'home'



if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=802)
