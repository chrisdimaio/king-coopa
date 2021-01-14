from collections import OrderedDict
from gpiozero import (
    CompositeDevice,
    DigitalOutputDevice,
    GPIOPinMissing,
    SourceMixin
)

from time import sleep


class LinearActuator(SourceMixin, CompositeDevice):
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

        super(LinearActuator, self).__init__(_order=devices.keys(), **devices)

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


class AMTGF12V350T1(LinearActuator):
    DUTY_CYCLE = .2
    STROKE = 350
    SPEED = 5.7

    def __init__(self, open_pin, close_pin):
        cycle_time = self.STROKE/self.SPEED
        super().__init__(open_pin, close_pin, cycle_time, cycle_time, self.DUTY_CYCLE)


class TESTER(LinearActuator):
    DUTY_CYCLE = .2
    STROKE = 35
    SPEED = 5.7

    def __init__(self, open_pin, close_pin):
        cycle_time = self.STROKE/self.SPEED
        super().__init__(open_pin, close_pin, cycle_time, cycle_time, self.DUTY_CYCLE)
