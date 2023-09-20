import datetime
import calendar

def calculate_date_range(year : int, month : int) -> tuple[datetime.datetime, datetime.datetime]:
    last_day = calendar.monthrange(year, month)[1]

    if month < 10:
        end = datetime.datetime.strptime(f"{year}-0{month}-{last_day}", "%Y-%m-%d")
    else:
        end = datetime.datetime.strptime(f"{year}-{month}-{last_day}", "%Y-%m-%d")

    start = datetime.datetime.strptime(f"{year}-{month}", "%Y-%m")

    return (start, end)


def valid_month(year : int, month : int) -> bool:

    today = datetime.datetime.now()

    if month > today.month or month < 1 or year > today.year or year < 2023:
        return False
    else:
        return True

