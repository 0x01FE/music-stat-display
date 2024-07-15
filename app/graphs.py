import os
import typing
import logging
import datetime
import dateutil.relativedelta

# Mute matplot lib debug logs
logging.getLogger('matplotlib').setLevel(logging.WARNING)

import matplotlib
import matplotlib.pyplot

import db
import daterange
import listen_time

matplotlib.use("agg")
matplotlib.font_manager.fontManager.addfont("app/static/CyberpunkWaifus.ttf")
matplotlib.pyplot.rcParams["figure.figsize"] = (12, 7)

FILE_EXPIRATION_MINUTES = 15

def build_path(time_frame : str, user_id : str) -> str:
    return f'app/static/user-{user_id}-{time_frame}.png'

# Check if file is too new to warrant a new graph.
def is_old(path : str) -> bool:
    try:
        creation_time: float = os.path.getctime(path)

        now: float = datetime.datetime.now().timestamp()

        time_detla: float = now - creation_time

        if time_detla >= (FILE_EXPIRATION_MINUTES * 60):
            return True
        else:
            return False

    # If no file is found, that's a good case for making a new one.
    except FileNotFoundError:
        return True

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
    ax.tick_params(axis="x", colors="xkcd:powder blue", labelrotation=45)
    ax.tick_params(axis="y", colors="xkcd:powder blue")

    # Title Color
    ax.set_title(title, color="xkcd:hot pink", font="CyberpunkWaifus", fontsize=20)

    # Grid
    ax.grid(color="xkcd:dark purple")

    return ax


# Returns path to graph image (png)
def generate_daily_graph(user_id : int) -> None:

    save_path = build_path('daily', user_id)
    if not is_old(save_path):
        return

    now = datetime.datetime.now()

    totals = []
    dates = []

    for i in range(1, 9):
        start = now - dateutil.relativedelta.relativedelta(days=i)
        end = now - dateutil.relativedelta.relativedelta(days=i-1)
        time = db.get_total_time(user_id, daterange.DateRange(start, end))

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

    fig.savefig(save_path, bbox_inches='tight')


def generate_weekly_graph(user_id : int) -> None:

    save_path = build_path('weekly', user_id)
    if not is_old(save_path):
        return

    now = datetime.datetime.now()

    totals = []
    dates = []

    for i in range(1, 9):
        start = now - dateutil.relativedelta.relativedelta(weeks=i)
        end = now - dateutil.relativedelta.relativedelta(weeks=i-1)
        time = db.get_total_time(user_id, daterange.DateRange(start, end))

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

    fig.savefig(save_path, bbox_inches='tight')


def generate_monthly_graph(user_id : int) -> None:

    save_path = build_path('monthly', user_id)
    if not is_old(save_path):
        return

    now = datetime.datetime.now()

    totals = []
    dates = []
    for i in range(1, 13):
        start = now - dateutil.relativedelta.relativedelta(months=i) # Why does normal timedelta not support months?
        end = now - dateutil.relativedelta.relativedelta(months=i-1)
        time = db.get_total_time(user_id, daterange.DateRange(start, end))

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

    fig.savefig(save_path)


def generate_artist_graph(user_id : int, artist_id : int, ranges : list[daterange.DateRange], period : typing.Literal['d', 'w', 'm', 'yd']) -> str:

    match period:
        case "d":
            file_name = "day"
            adj = "Daily"
        case "w":
            file_name = "week"
            adj = "Weekly"
        case "m":
            file_name = "month"
            adj = "Monthly"
        case "yd":
            file_name = "yd"
            adj = "Daily (For a Year)"

    times: list[listen_time.ListenTime] = []
    dates: list[str] = []
    for range in ranges:
        time = db.get_artist_total(user_id, artist_id, range)

        if not time:
            time = listen_time.ListenTime(0)

        times.append(time.to_hours())
        dates.append(range.start.strftime("%Y-%m-%d"))

    artist_name = db.get_artist_info(artist_id)

    times = list(reversed(times))
    dates = list(reversed(dates))

    fig, ax = matplotlib.pyplot.subplots(facecolor="xkcd:black")
    line = ax.plot(dates, times)

    color_graph(f"{artist_name} {adj} Summary", ax, line)

    for i, txt in enumerate(times):
        ax.annotate(txt, (dates[i], times[i]), color="xkcd:powder blue")

    if period == "yd":
        print('?')
        fig.set_size_inches(72, 7)
    else:
        fig.set_size_inches(12, 7)

    fig.savefig(f"app/static/{artist_id}-{file_name}.png")
