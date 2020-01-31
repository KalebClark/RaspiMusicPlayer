from time import sleep
import logging
import threading, time
from RPM.RPM import RPM

delay = .5

def setup():
    logging.info("Starting Setup")

def loop():
    logging.info("Loop...")
    #rpm.update()

def hwLoop():
    while True:
        #logging.info("H Loop...")
        rpm.update()
        sleep(.05)

def swLoop():
    while True:
        #logging.info("SOFTWARE Loop....")
        rpm.getStatus()
        sleep(1)


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    logging.info("MAIN: Starting")
    rpm = RPM()
    #rpm.wsConnect()
    # setup()
    # looping = True
    # while looping:
    #     loop()
    #     sleep(.1)
    thread1 = threading.Thread(target=hwLoop)
    thread1.start()
    thread2 = threading.Thread(target=swLoop)
    thread2.start()
