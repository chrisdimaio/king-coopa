from collections import OrderedDict
from gpiozero import (
    CompositeDevice,
    DigitalOutputDevice,
    GPIOPinMissing,
    SourceMixin
)

from time import sleep


class GenericLinearActuator(SourceMixin, CompositeDevice):
    def __init__(self, open_pin, close_pin, up_duration, down_duration, duty_cycle):
        if not all(p is not None for p in [open_pin, close_pin]):
            raise GPIOPinMissing(
                'forward and backward pins must be provided'
            )

        devices = OrderedDict((
            ('up_device', DigitalOutputDevice(open_pin)),
            ('down_device', DigitalOutputDevice(close_pin)),
        ))

        self.up_duration = up_duration
        self.down_duration = down_duration
        self.duty_cycle = duty_cycle

        super(GenericLinearActuator, self).__init__(
            _order=devices.keys(), **devices)

    def up(self):
        self.down_device.off()
        self.up_device.on()
        sleep(self.up_duration)
        self.up_device.off()
        sleep(self.duty_cycle * self.up_duration)

    def down(self):
        self.up_device.off()
        self.down_device.on()
        sleep(self.down_duration)
        self.down_device.off()
        sleep(self.duty_cycle * self.down_duration)

# Specific models


class AMTGF12V350T1(GenericLinearActuator):
    DUTY_CYCLE = .2
    STROKE = 350
    SPEED = 5.7

    def __init__(self, open_pin, close_pin):
        cycle_time = self.STROKE/self.SPEED
        super().__init__(open_pin, close_pin, cycle_time, cycle_time, self.DUTY_CYCLE)


class LinearActuator(GenericLinearActuator):
    REQUIRED_SPECS = ["duty_cycle", "speed", "stroke"]

    def __init__(self, specs, open_pin, close_pin):
        for s in self.REQUIRED_SPECS:
            if s not in specs:
                raise Exception("Missing equired spec '{}'.".format(s))

        self.stroke = specs["stroke"]
        self.speed = specs["speed"]
        self.duty_cycle = specs["duty_cycle"]

        cycle_time = self.stroke/self.speed
        super().__init__(open_pin, close_pin, cycle_time, cycle_time, self.duty_cycle)


class TESTER(GenericLinearActuator):
    DUTY_CYCLE = .2
    STROKE = 35
    SPEED = 5.7

    def __init__(self, open_pin, close_pin):
        cycle_time = self.STROKE/self.SPEED
        super().__init__(open_pin, close_pin, cycle_time, cycle_time, self.DUTY_CYCLE)
