import datetime
import calendar
import math


def calculate_date_range(year : int, month : int) -> tuple[datetime.datetime, datetime.datetime]:
    last_day = calendar.monthrange(year, month)[1]

    if month < 10:
        end = datetime.strptime(f"{year}-0{month}-{last_day}", "%Y-%m-%d")
    else:
        end = datetime.strptime(f"{year}-{month}-{last_day}", "%Y-%m-%d")

    start = datetime.strptime(f"{year}-{month}", "%Y-%m")

    return (start, end)


def valid_month(year : int, month : int) -> bool:

    today = datetime.now()

    if month > today.month or month < 1 or year > today.year or year < 2023:
        return False
    else:
        return True


def listen_time_format(mili : int) -> tuple[int, int]:

    minutes = mili/1000/60
    hours = math.floor(minutes/60)

    return (hours, round(minutes % 60, 2))

