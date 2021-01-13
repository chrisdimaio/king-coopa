#! /usr/bin/python3


from datetime import datetime
from sun_times_calc import SunTimesCalculator
from sun_trigger import SunTrigger
from linear_actuators import AMTGF12V350T1, TESTER
from door_opener import DoorOpener
from gpiozero import LED, OutputDevice
from time import sleep


def main():
    door_opener = DoorOpener(
        actuator_class=TESTER, open_time="Some time", close_time="Some time"
    )

    trigger = SunTrigger(3)
    print("Is sunrise: {}".format(trigger.is_sunrise()))
    print("Is sunset: {}".format(trigger.is_sunset()))

    # door_opener.start()
    # door_opener.open()
    # sleep(3)
    # door_opener.close()


if __name__ == "__main__":
    main()
