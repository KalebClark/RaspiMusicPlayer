from RaspiMusic.RaspiMusic import RaspiMusic
from time import sleep
import logging
import threading, time
#import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library


def hwLoop():
    while True:
        rpm.update()
        time.sleep(0.05)

def swLoop():
    while True:
        #logging.info("SOFTWARE Loop....")
        rpm.getState()
        sleep(1)

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    logging.info("MAIN: Starting")
    rpm = RaspiMusic()
    thread1 = threading.Thread(target=hwLoop)
    thread1.start()
    thread2 = threading.Thread(target=swLoop)
    thread2.start()
    #GPIO.setwarnings(False)
    #GPIO.setmode(GPIO.BCM)
    #GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


    #while True:
    #    if GPIO.input(17) == GPIO.HIGH:
    #        print("gotcha bitch!")
    #        time.sleep(0.05)

