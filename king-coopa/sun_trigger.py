from datetime import datetime, tzinfo
from sun_times_calc import SunTimesCalculator


class SunTrigger:
    def __init__(self, offset):
        self.stc = SunTimesCalculator(longitude=1234, latitude=123)

    def is_sunrise(self):
        return self._is_event(self.stc.get_sunrise())

    def is_sunset(self):
        return self._is_event(self.stc.get_sunset())

    def _is_event(self, event):
        diff = (datetime.now() - event.replace(tzinfo=None)).seconds
        return diff >= 0 and diff <= 60
