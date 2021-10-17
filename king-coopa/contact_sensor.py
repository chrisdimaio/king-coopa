# from gpiozero import Button
from door_sensor import DoorSensor
from time import sleep
from configuration import Configuration

sensor = DoorSensor(Configuration())

# True is open false is closed
current_state = None


while(True):
    print("sensor is closed: " + str(sensor.is_closed()) +
          ", info: " + str(sensor.serializable()))
    # current_state = sensor.is_pressed

    # # Report door state
    # if sensor.is_closed():
    #     print("Door closed!")
    #     print(sensor.info())
    #     sensor.wait_for_release()
    # else:
    #     print("Door opened!")
    #     print(sensor.info())
    #     sensor.wait_for_press()
    sleep(3)
