#! /usr/bin/python3


from linear_actuators import AMTGF12V350T1, TESTER
from door_opener import DoorOpener
from gpiozero import LED, OutputDevice
from time import sleep


def main():
    door_opener = DoorOpener(
        actuator_class=TESTER, open_time="Some time", close_time="Some time"
    )

    door_opener.start()
    door_opener.open()
    sleep(3)
    door_opener.close()


if __name__ == "__main__":
    main()
