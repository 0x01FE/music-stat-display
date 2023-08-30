from flask import Flask, render_template, redirect
from datetime import datetime
from datetime import timedelta
import calendar
import json
from os.path import exists
from os import mkdir
from glob import glob
from math import floor
from configparser import ConfigParser
import matplotlib.pyplot as plt
from typing import Literal, Optional


app = Flask(__name__, static_url_path='', static_folder='static')

if not exists('./reports/'):
    mkdir("./reports/")

config = ConfigParser()
config.read("config.ini")

spotify_times_path = config['PATHES']['spotify_times']
templates_path = config['PATHES']['templates']

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
def generate_overall_graph(period : str) -> str:
    # Analyze the past 12 months, including this one so far.
    if period == 'month':
        today = datetime.today()

        months = range(1, today.month + 1)

        months_last_year = range(len(months), 12)

        months_with_data = [[], []] # First list is the current year, second is last year

        # Check which of the months in the ranges we have data for
        days = glob(spotify_times_path + "*-*-*.json")

        for day in days:
            filename = day.split("/")[-1]

            if "overall" in filename or "last" in filename:
                continue

            date = filename[:10].split('-') # list with (day, month, year)

            i = 0
            for x in date:
                date[i] = int(x)
                i+=1

            if date[2] == today.year and date[1] in months:
                if date[1] not in months_with_data[0]:
                    months_with_data[0].append(date[1])

            elif date[2] == today.year - 1 and date[1] in months_last_year:
                if date[1] not in months_with_data[1]:
                    months_with_data[1].append(date[1])

        # last_day = calendar.monthrange(year, month)[1]
        monthly_totals = []
        dates = []

        for month in sorted(months_with_data[1]):
            start = datetime.strptime(f"01-{month}-{today.year-1}", "%d-%m-%Y")
            end = datetime.strptime(f"{calendar.monthrange(today.year, month)[1]}-{month}-{today.year-1}", "%d-%m-%Y")

            report_path = generate_listening_report(start, end)

            with open(report_path, 'r') as f:
                report_data = json.loads(f.read())

            monthly_totals.append(msToHour(calculate_total_listening_time(report_data)))
            dates.append(f'{month}-{today.year-1}')

        for month in sorted(months_with_data[0]):
            start = datetime.strptime(f"01-{month}-{today.year}", "%d-%m-%Y")
            end = datetime.strptime(f"{calendar.monthrange(today.year, month)[1]}-{month}-{today.year}", "%d-%m-%Y")

            report_path = generate_listening_report(start, end)

            with open(report_path, 'r') as f:
                report_data = json.loads(f.read())

            monthly_totals.append(msToHour(calculate_total_listening_time(report_data)))
            dates.append(f'{month}-{today.year}')

        fig, ax = plt.subplots()
        ax.plot(dates, monthly_totals)
        ax.set(xlabel='Date', ylabel='time (hours)', title='Listening Time')
        ax.grid()

        for i, txt in enumerate(monthly_totals):
            ax.annotate(txt, (dates[i], monthly_totals[i]))

        fig.savefig("static/month.png")
        return "static/month.png"

    # Graph of the past eight weeks
    elif period == 'week':
        today = datetime.today()

        weeks = []
        end = today
        for week in range(0, 9):
            start = end - timedelta(days=7)
            weeks.append((start, end))
            end = start - timedelta(days=1)

        weekly_totals = []
        dates = []
        for week in reversed(weeks):
            report_path = generate_listening_report(week[0], week[1])

            if not report_path:
                continue

            with open(report_path, 'r') as f:
                report_data = json.loads(f.read())

            weekly_totals.append(msToHour(calculate_total_listening_time(report_data)))
            dates.append(f'{week[0].day}-{week[0].month}')

        fig, ax = plt.subplots()
        ax.plot(dates, weekly_totals)
        ax.set(xlabel='Date', ylabel='time (hours)', title='Listening Time')
        ax.grid()

        for i, txt in enumerate(weekly_totals):
            ax.annotate(txt, (dates[i], weekly_totals[i]))

        fig.savefig("static/week.png", bbox_inches='tight')
        return "static/week.png"

    # Graph of the past 14 days
    elif period == 'day':
        today = datetime.today() - timedelta(days=3)

        daily_totals = []
        dates = []
        for day in range(0, 15):

            with open(spotify_times_path + f"{datetime.strftime(today, '%d-%m-%Y')}.json", 'r') as f:
                report_data = json.loads(f.read())

            daily_totals.append(msToHour(calculate_total_listening_time(report_data)))
            dates.append(f'{today.day}')

            today = today - timedelta(days=1)

        dates = [a for a in reversed(dates)]
        daily_totals = [a for a in reversed(daily_totals)]

        fig, ax = plt.subplots()
        ax.plot(dates, daily_totals)
        ax.set(xlabel='Date', ylabel='time (hours)')
        ax.grid()

        for i, txt in enumerate(daily_totals):
            ax.annotate(txt, (dates[i], daily_totals[i]))

        fig.savefig("static/day.png", bbox_inches='tight')
        return "static/day.png"


    else:
        return 'bad period'


def keyfunc(tup :  tuple) -> int:
    key, d = tup
    return d['overall']

def get_top(item_type : Literal['artists', 'albums', 'songs'], top : Optional[int] = None) -> dict:
    with open(spotify_times_path + "overall.json", 'r') as f:
        data = json.loads(f.read())

    if item_type == 'artists':
        data = sorted(data.items(), key=keyfunc, reverse=True)
        if top:
            data = data[:top]

        sorted_artists = {}
        for artist_tuple in data:
            artist_name, artist_info = artist_tuple

            sorted_artists[artist_name.replace("-", " ").title()] =  (listenTimeFormat(artist_info["overall"]), artist_name)

        return sorted_artists

    elif item_type == 'albums':
        albums = {}
        for artist in data:
            for album in data[artist]["albums"]:
                albums[album] = {
                    "overall" : data[artist]["albums"][album]["overall"],
                    "artist" : artist            
                }
        data = sorted(albums.items(), key=keyfunc, reverse=True)
        if top:
            data = data[:top]
        
        sorted_albums = {}
        for album in data:
            album_title, album_info = album

            sorted_albums[album_title] = (listenTimeFormat(album_info["overall"]), album_info["artist"].replace("-", " ").title(), album_info['artist'])

        return sorted_albums

    elif item_type == 'songs':
        songs = {}
        for artist in data:
            for album in data[artist]["albums"]:
                for song in data[artist]["albums"][album]["songs"]:
                    songs[song] = {
                        "overall" : data[artist]["albums"][album]["songs"][song],
                        "artist" : artist            
                    }
        data = sorted(songs.items(), key=keyfunc, reverse=True)
        if top:
            data = data[:top]
        
        sorted_songs = {}
        for song in data:
            song_title, song_info = song

            sorted_songs[song_title] = (listenTimeFormat(song_info["overall"]), song_info["artist"].replace("-", " ").title(), song_info["artist"])

        return sorted_songs


@app.route('/')
def root():
    for period in ['day', 'week', 'month']:
        generate_overall_graph(period)

    today = datetime.today()

    top_artists = get_top('artists', top=5)
    top_albums = get_top('albums', top=5)
    top_songs = get_top('songs', top=5)

    with open(spotify_times_path + "overall.json", 'r') as f:
        data = json.loads(f.read())

    total_time = listenTimeFormat(calculate_total_listening_time(data))
    artist_count = len(data)

    # For total albums/songs count
    all_albums = []
    all_songs = []
    for artist in data:
        for album in data[artist]["albums"]:
            if album not in all_albums:
                all_albums.append(album)
            for song in data[artist]["albums"][album]["songs"]:
                if song not in all_songs:
                    all_songs.append(song)

    return render_template('home.html', top_albums=top_albums, top_songs=top_songs, top_artists=top_artists, year=today.year, month=today.month, artist_count=artist_count, total_time=total_time, album_count=len(all_albums), song_count=len(all_songs))

@app.route('/overall/')
def overall():
    return redirect('/')

@app.route('/overall/artists/')
def overall_artists():

    top_artists = get_top('artists')

    return render_template('overall_artists.html', data=top_artists)

@app.route('/overall/albums/')
def overall_albums():
    top_albums = get_top('albums')

    return render_template('overall_albums.html', top_albums=top_albums)

@app.route('/overall/songs/')
def overall_songs():
    top_songs = get_top('songs')

    return render_template('overall_songs.html', top_songs=top_songs)

@app.route('/month/<year>/<month>/')
def overall_month(year : str, month : str):
    month = int(month)
    year = int(year)

    today = datetime.now()

    if month > today.month or month < 1:
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

    total_time = listenTimeFormat(calculate_total_listening_time(data))
    artist_count = len(data)

    data = sorted(data.items(), key=keyfunc, reverse=True)

    sorted_artists = {}
    for artist_tuple in data:
        artist_name, artist_info = artist_tuple

        sorted_artists[artist_name.replace("-", " ").title()] =  (listenTimeFormat(artist_info["overall"]), artist_name)

    links = (f"../../{year}/{month - 1}", f"../../{year}/{month + 1}")

    return render_template('overall_month.html', data=sorted_artists, month_name=calendar.month_name[month], year=year, selector_links=links, month_total=total_time, artist_total=artist_count)



@app.route('/month/<year>/<month>/<artist>/')
def artist_month(year : str, month : str, artist : str):
    artist = artist.lower()
    month = int(month)
    year = int(year)

    today = datetime.now()

    if month > today.month or month < 1:
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
