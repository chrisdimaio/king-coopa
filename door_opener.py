class DoorOpener:
    def __init__(self, actuator_class, open_time, close_time):
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

        # Add logic later
        self.up_duration = 10
        self.down_duration = 10
        self.duty_cycle = .4

        self.actuator = actuator_class(
            up=20, down=26, up_duration=self.up_duration, down_duration=self.down_duration, duty_cycle=self.duty_cycle
        )

    def close(self):
        self.actuator.down()

    def open(self):
        self.actuator.up()
