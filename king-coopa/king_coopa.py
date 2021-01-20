#! /usr/bin/python3


from datetime import datetime
from sun_times_calc import SunTimesCalculator
from sun_trigger import SunTrigger
from linear_actuators import AMTGF12V350T1, TESTER, LinearActuator
from configuration import Configuration
from door_opener import DoorOpener
from gpiozero import LED, OutputDevice
from time import sleep
from art import tprint
import api_server as server


def main():
    tprint("King")
    tprint("   Coopa !")

    config = Configuration()

    door_opener = DoorOpener(
        actuator_class=LinearActuator, open_time="Some time", close_time="Some time", config=config
    )

    server.run(config, door_opener)

    door_opener.start()


if __name__ == "__main__":
    main()
