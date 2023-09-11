from flask import Flask, render_template, redirect
import matplotlib
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta

from datetime import datetime, timedelta
from os.path import exists
from os import mkdir
from glob import glob
from math import floor
from configparser import ConfigParser
from typing import Literal, Optional
import calendar
import json

import db

matplotlib.use("agg")
app = Flask(__name__, static_url_path='', static_folder='static')

if not exists('./reports/'):
    mkdir("./reports/")

config = ConfigParser()
config.read("config.ini")

spotify_times_path = config['PATHES']['spotify_times']
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

# returns path to report
def generate_listening_report(start : datetime, end : datetime) -> str:
    if end < start:
        print("Error, start date is after end date.")
        return

    days = glob(spotify_times_path + "*.json")

    days_in_range = []

    for day in days:
        if "overall" in day.split("/")[-1] or "last" in day.split("/")[-1]:
            continue

        file_date = datetime.strptime(day.split("/")[-1][:10], "%d-%m-%Y")
        if file_date >= start and file_date <= end:
            days_in_range.append(day)

    report = {}
    for day in days_in_range:
        with open(day, "r") as f:
            day_data = json.loads(f.read())

        for artist in day_data:
            if artist not in report:
                report[artist.lower()] = { "overall" : 0, "albums" : {} }

            for album in day_data[artist]["albums"]:
                if album not in report[artist.lower()]["albums"]:
                    report[artist.lower()]["albums"][album] = { "overall" : 0, "songs" : {} }

                for song in day_data[artist]["albums"][album]["songs"]:
                    if song not in report[artist.lower()]["albums"][album]["songs"]:
                        report[artist.lower()]["albums"][album]["songs"][song] = 0

                    report[artist.lower()]["albums"][album]["songs"][song] += day_data[artist]["albums"][album]["songs"][song]
                    report[artist.lower()]["overall"] += day_data[artist]["albums"][album]["songs"][song]
                    report[artist.lower()]["albums"][album]["overall"] += day_data[artist]["albums"][album]["songs"][song]

    if report:
        save_location = "reports/" + f'{datetime.strftime(start, "%d-%m-%Y")}-{datetime.strftime(end, "%d-%m-%Y")}.json'
        with open(save_location, "w") as f:
            f.write(json.dumps(report, indent=4))

        return save_location
    else:
        return None

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
        return "static/month.png"

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
        return "static/week.png"

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
        return "static/day.png"


    else:
        return 'bad period'


def keyfunc(tup :  tuple) -> int:
    key, d = tup
    return d['overall']


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



@app.route('<int:user>/month/<int:year>/<int:month>/<str:artist>/')
def artist_month(user : int, year : int, month : int, artist : str):
    artist = artist.lower()

    now = datetime.now()

    if month > now.month or month < 1:
        return 'Month is invalid'

    last_day = calendar.monthrange(year, month)[1]

    if month < 10:
        start = datetime.strptime(f"01-0{month}-{year}", "%d-%m-%Y")
    else:
        start = datetime.strptime(f"01-{month}-{year}", "%d-%m-%Y")

    if month == today.month:
        end = today
    else:
        end = datetime.strptime(f"{last_day}-{month}-{year}", "%d-%m-%Y")

    filename = f'{datetime.strftime(start, "%d-%m-%Y")}-{datetime.strftime(end, "%d-%m-%Y")}.json'

    if not exists("reports/" + filename) or month == today.month:
        generate_listening_report(start, end)

    with open("reports/" + filename, 'r') as f:
        data = json.loads(f.read())

    total_time = listenTimeFormat(data[artist]["overall"])

    # Sort albums by listen time
    albums_sorted = sorted(data[artist]["albums"].items(), key=keyfunc, reverse=True)

    top_albums = {}
    for album_tuple in albums_sorted:
        album_name, album_info = album_tuple

        top_albums[album_name] = listenTimeFormat(album_info["overall"])


    # Make dict of top songs
    all_songs = {}
    for album in data[artist]["albums"]:
        for song in data[artist]["albums"][album]["songs"]:
            all_songs[song] = data[artist]["albums"][album]["songs"][song]

    sorted_songs = {k: v for k, v in sorted(all_songs.items(), key=lambda item: item[1], reverse=True)}

    top_songs = {}
    for song in sorted_songs:
        top_songs[song] = listenTimeFormat(sorted_songs[song])

    return render_template('artist_month.html', artist_name=artist.replace('-', ' ').title(), month_name=calendar.month_name[month], year=year, artist_listen_time=total_time, top_albums=top_albums, top_songs=top_songs)




@app.route('/overall/<artist>/')
def artist(artist : str):
    artist = artist.lower()


    with open(spotify_times_path + "overall.json", 'r') as f:
        data = json.loads(f.read())

    total_time = listenTimeFormat(data[artist]["overall"])

    # Sort albums by listen time
    albums_sorted = sorted(data[artist]["albums"].items(), key=keyfunc, reverse=True)

    top_albums = {}
    for album_tuple in albums_sorted:
        album_name, album_info = album_tuple

        top_albums[album_name] = listenTimeFormat(album_info["overall"])


    # Make dict of top songs
    all_songs = {}
    for album in data[artist]["albums"]:
        for song in data[artist]["albums"][album]["songs"]:
            all_songs[song] = data[artist]["albums"][album]["songs"][song]

    sorted_songs = {k: v for k, v in sorted(all_songs.items(), key=lambda item: item[1], reverse=True)}

    top_songs = {}
    for song in sorted_songs:
        top_songs[song] = listenTimeFormat(sorted_songs[song])

    return render_template('artist.html', artist_name=artist.replace('-', ' ').title(), artist_listen_time=total_time, top_albums=top_albums, top_songs=top_songs)


@app.route('/test/')
def test():
    return generate_overall_graph("day")
