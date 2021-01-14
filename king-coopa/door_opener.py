from sun_trigger import SunTrigger
from device_states import States
from time import sleep
from threading import Thread


class DoorOpener:
    # Seconds per cycle
    _FREQUENCY = 1

    def __init__(self, actuator_class, open_time, close_time, config):
        if actuator_class is None:
            raise Exception(
                "An actuator class must be specified."
            )
        if not all(p is not None for p in [open_time, close_time]):
            raise Exception(
                "Open and close times must be set."
            )
        self.actuator_class = actuator_class
        self.open_time = open_time
        self.close_time = close_time

        self.actuator = actuator_class(
            open_pin=config.open_pin, close_pin=config.close_pin
        )

        self.trigger = SunTrigger(config)
        self.state = States.CLOSED

    def start(self):
        def worker():
            while(True):
                if self.trigger.is_sunrise() and self.state is States.CLOSED:
                    print("Opening door...")
                    self.open()
                    print("State: {}".format(self.state.value))
                if self.trigger.is_sunset() and self.state is States.OPEN:
                    print("Closing door...")
                    self.close()
                    print("State: {}".format(self.state.value))
                sleep(self._FREQUENCY)

        t = Thread(target=worker)
        t.start()

    def close(self):
        self.state = States.CLOSING
        self.actuator.down()
        self.state = States.CLOSED

    def open(self):
        self.state = States.OPENING
        self.actuator.up()
        self.state = States.OPEN
