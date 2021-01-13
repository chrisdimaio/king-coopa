import datetime
from suntime import Sun, SunTimeException


class SunTimesCalculator:
    def __init__(self, longitude, latitude):
        # East Hampstead NH
        self.latitude = 42.8836989
        self.longitude = -71.1681156

        self._cache = {}

    def get_sunrise(self):
        return self._calc_cache()["sunrise"]

    def get_sunset(self):
        return self._calc_cache()["sunset"]

    # Sunrise/sunset calculations are heavy so we cache them for each day.
    def _calc_cache(self):
        date = datetime.date.today()
        if date not in self._cache:
            # Not point in keeping the previos times.
            self._cache = {}
            self._cache[date] = self._calc()
        return self._cache[date]

    """
        Suntime Docs: https://github.com/SatAgro/suntime
    """

    def _calc(self):
        sun = Sun(self.latitude, self.longitude)
        return {
            "sunrise": sun.get_local_sunrise_time(),
            "sunset": sun.get_local_sunset_time()
        }
