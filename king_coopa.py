#! /usr/bin/python3
import threading

from gpiozero import LED, OutputDevice
from time import sleep


def main():
    # blink()
    # led()
    open_door_led()
    sleep(11)
    close_door_led()
    while(True):
        pass


def close_door_led():
    def function():
        led = LED(26)
        led.on()
        sleep(10)
        led.off()
    t = threading.Thread(target=function)
    t.start()


def open_door_led():
    def function():
        led = LED(20)
        led.on()
        sleep(10)
        led.off()
    t = threading.Thread(target=function)
    t.start()


def led():
    def function():
        led = LED(26)

        while(True):
            led.on()
            sleep(.2)
            led.off()
            sleep(.2)

    t = threading.Thread(target=function)
    t.start()


def blink():
    def function():
        grn = LED(19)
        blu = LED(13)
        red = LED(6)

        blu.on()

        while(True):
            grn.on()
            red.on()
            sleep(.5)
            grn.off()
            red.off()
            sleep(.75)

    t = threading.Thread(target=function)
    t.start()
    # t.join()


if __name__ == "__main__":
    main()
