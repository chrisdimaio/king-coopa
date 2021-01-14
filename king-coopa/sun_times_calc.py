import datetime
from suntime import Sun, SunTimeException


class SunTimesCalculator:
    def __init__(self, longitude, latitude):
        self._longitude = longitude
        self._latitude = latitude

        self._cache = {}

    def get_sunrise(self):
        return self._calc_cache()["sunrise"]

    def get_sunset(self):
        return self._calc_cache()["sunset"]

    # Sunrise/sunset calculations are heavy so we cache them for each day.
    def _calc_cache(self):
        date = datetime.date.today()
        if date not in self._cache:
            # No point in keeping the previos times.
            self._cache = {}
            self._cache[date] = self._calc()
        return self._cache[date]

    """
        Suntime Docs: https://github.com/SatAgro/suntime
    """

    def _calc(self):
        sun = Sun(self._latitude, self._longitude)
        # return {
        #     "sunrise": datetime.datetime(year=2021, month=1, day=14, hour=1, minute=30, second=0),
        #     "sunset": sun.get_local_sunset_time()
        # }
        return {
            "sunrise": sun.get_local_sunrise_time(),
            "sunset": sun.get_local_sunset_time()
        }
