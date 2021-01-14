from datetime import datetime, tzinfo, timedelta
from sun_times_calc import SunTimesCalculator


class SunTrigger:
    def __init__(self, config):
        self.stc = SunTimesCalculator(
            longitude=config.longitude, latitude=config.latitude)
        self.sunrise_offset = timedelta(minutes=config.sunrise_offset)
        self.sunset_offset = timedelta(minutes=config.sunset_offset)

    def is_sunrise(self):
        return self._is_event(self.stc.get_sunrise(), self.sunrise_offset)

    def is_sunset(self):
        return self._is_event(self.stc.get_sunset(), self.sunset_offset)

    def _is_event(self, event, offset):
        diff = (datetime.now() - event.replace(tzinfo=None) - offset).seconds
        return diff >= 0 and diff <= 60
