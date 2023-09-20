import math

class ListenTime:

    mili : int

    def __init__(self, mili : int):
        self.mili = mili

    def to_hour_and_seconds(self) -> tuple[int, int]:
        minutes = self.mili/1000/60
        hours = math.floor(minutes/60)

        return (hours, round((minutes % 60), 2))

    def to_hours(self) -> int:
        return round(self.mili/1000/60/60, 1)

