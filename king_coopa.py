#! /usr/bin/python3

from linear_actuator import LinearActuator
from gpiozero import LED, OutputDevice
from time import sleep


def main():
    door = LinearActuator(up=20, down=26, up_duration=10,
                          down_duration=12, duty_cycle=.4)
    door.up()
    door.down()


if __name__ == "__main__":
    main()
