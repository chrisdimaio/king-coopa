from datetime import datetime


class SunTrigger:
    A_SUNRISE = datetime(2021, 1, 12, 11, 30)
    A_SUNSET = datetime(2021, 1, 12, 11, 45)

    def __init__(self, offset):
        pass

    def is_sunrise(self):
        return self._is_event(self.A_SUNRISE)

    def is_sunset(self):
        return self._is_event(self.A_SUNSET)

    def _is_event(self, event):
        diff = (datetime.now() - event).seconds
        return diff >= 0 and diff <= 60
