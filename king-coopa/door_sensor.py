from gpiozero import Button, GPIOPinMissing


class DoorSensor(Button):
    def __init__(self, config):
        if config.sensor_pin is None:
            raise GPIOPinMissing('Door sensor pin must be set.')
        super().__init__(config.sensor_pin)

    def serializable(self):
        # Converts TRUE/FALSE to human readable door states.
        def _state(raw_state):
            from device_states import States
            if raw_state:
                return States.CLOSED.value
            return States.OPEN.value

        return {
            "state": _state(self.is_pressed)
        }

    def is_closed(self):
        return self.is_pressed
