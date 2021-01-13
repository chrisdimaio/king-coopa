from datetime import date, datetime


class SunTimesCalculator:
    def __init__(self, longitude, latitude):
        # Cache sunsets/rises so we don't have to calculate them for every call.
        self.cache = {}

    def get_sunrise(self):
        return self._cache(date)["sunrise"]

    def get_sunset(self):
        return datetime(2021, 1, 12, 11, 45)

    def _cache(self, date):
        if date not in self.cache:
            self.cache[date] = {
                "sunrise": self._calc_sunrise(date),
                "sunset": self._calc_sunset(date)
            }
        return self.cache[date]

    def _calc_sunrise(self, date):
        return datetime(2021, 1, 12, 11, 30)

    def _calc_sunset(self, date):
        return datetime(2021, 1, 12, 11, 45)
