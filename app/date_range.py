import datetime
import calendar
import dateutil.relativedelta

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class DateRange:

    start : datetime.datetime
    end : datetime.datetime

    def __init__(self, start : datetime.datetime | None = None, end : datetime.datetime | None = None):
        self.start = start
        self.end = end

    def to_str(self) -> tuple[str, str]:
        return (self.start.strftime(DATE_FORMAT), self.end.strftime(DATE_FORMAT))

    def get_range(self, year : int, month : int) -> bool:

        today = datetime.datetime.today()

        if month < 1 or year > today.year:
            return False


        last_day = calendar.monthrange(year, month)[1]

        if month < 10:
            self.end = datetime.datetime.strptime(f"{year}-0{month}-{last_day}", "%Y-%m-%d")
        else:
            self.end = datetime.datetime.strptime(f"{year}-{month}-{last_day}", "%Y-%m-%d")

        self.start = datetime.datetime.strptime(f"{year}-{month}", "%Y-%m")
        return True



def monthly_ranges(months : int) -> list[DateRange]:
    ranges: list[DateRange] = []

    today = datetime.datetime.now()

    for month in range(1, months):
        start = today - dateutil.relativedelta.relativedelta(months=month)
        end = today - dateutil.relativedelta.relativedelta(months=month - 1)
        ranges.append(DateRange(start, end))

    return ranges



def weekly_ranges(weeks : int) -> list[DateRange]:
    ranges: list[DateRange] = []

    today = datetime.datetime.now()

    for week in range(1, weeks):
        start = today - dateutil.relativedelta.relativedelta(weeks=week)
        end = today - dateutil.relativedelta.relativedelta(weeks=week - 1)
        ranges.append(DateRange(start, end))

    return ranges



def daily_ranges(days : int) -> list[DateRange]:
    ranges: list[DateRange] = []

    today = datetime.datetime.now()

    for day in range(1, days):
        start = today - dateutil.relativedelta.relativedelta(days=day)
        end = today - dateutil.relativedelta.relativedelta(days=day - 1)
        ranges.append(DateRange(start, end))

    return ranges

def last_n_months(n : int) -> DateRange:
    today = datetime.datetime.now()

    start = today - dateutil.relativedelta.relativedelta(months=n)

    return DateRange(start, today)

def last_n_weeks(n : int) -> DateRange:
    today = datetime.datetime.now()

    start = today - dateutil.relativedelta.relativedelta(weeks=n)

    return DateRange(start, today)

