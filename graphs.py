import datetime
import dateutil.relativedelta

import matplotlib
import matplotlib.pyplot

import db
import date_range
import listen_time

matplotlib.use("agg")
matplotlib.font_manager.fontManager.addfont("./static/CyberpunkWaifus.ttf")
matplotlib.pyplot.rcParams["figure.figsize"] = (12, 7)


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
def generate_daily_graph(user_id : int) -> str:
    now = datetime.datetime.now()

    totals = []
    dates = []

    for i in range(1, 9):
        start = now - dateutil.relativedelta.relativedelta(days=i)
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


def generate_weekly_graph(user_id : int) -> str:
    now = datetime.datetime.now()

    totals = []
    dates = []

    for i in range(1, 9):
        start = now - dateutil.relativedelta.relativedelta(weeks=i)
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


def generate_monthly_graph(user_id : int) -> str:
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
