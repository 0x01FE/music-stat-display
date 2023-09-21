import datetime
import calendar

class DateRange:

    start : datetime.datetime
    end : datetime.datetime

    def __init__(self, start : datetime.datetime | None = None, end : datetime.datetime | None = None):
        self.start = start
        self.end = end

    def to_str(self) -> tuple[str, str]:
        return (self.start.strftime("%Y-%m-%d"), self.end.strftime("%Y-%m-%d"))

    def get_range(self, year : int, month : int) -> bool:

        today = datetime.datetime.today()

        if month > today.month or month < 1 or year > today.year or year < 2023:
            return False


        last_day = calendar.monthrange(year, month)[1]

        if month < 10:
            self.end = datetime.datetime.strptime(f"{year}-0{month}-{last_day}", "%Y-%m-%d")
        else:
            self.end = datetime.datetime.strptime(f"{year}-{month}-{last_day}", "%Y-%m-%d")

        self.start = datetime.datetime.strptime(f"{year}-{month}", "%Y-%m")
        return True

