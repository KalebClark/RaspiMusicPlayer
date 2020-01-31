from socketIO_client import SocketIO, LoggingNamespace
import requests
import json
import board
import time
import busio
import digitalio
import RPi.GPIO as GPIO
import numpy as np
import logging
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# MCP GRAB COMMAND: mpc | awk 'FNR == 2 {print $4}' | tr -d -c 0-9

format = "%(name)s(%(levelname)s): %(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

class RPM:
    def __init__(self):
        logging.info("CLASS: RPMS Instantiated")
        self.host = "localhost"
        self.port = "3000"
        self.apiPath = "/api/v1/"
        self.client = False
        self.dim_amount = 50
        self.status = {
            'status': None,
            'seek': None,
            'duration': None,
            'random': None,
            'repeat': None,
            'volume': None,
            'mute': False,
            'dim': False
        }
        # pot trickery
        self.vol_array = [0,0,0]
        self.vol_array_cnt = 0
        self.last_raw_vol = 0
        self.last_raw_fad = 0

        # Hardware Init
        self.mcp = MCP.MCP3008(
            busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI),
            digitalio.DigitalInOut(board.D5)
        )

        ## Motor
        self.in1_pin = 17
        self.in2_pin = 22
        self.en_pin = 27
        self.pwm_pin = 18
        GPIO.setup(self.in1_pin, GPIO.OUT)
        GPIO.setup(self.in2_pin, GPIO.OUT)
        GPIO.setup(self.en_pin, GPIO.OUT)
        GPIO.setup(self.pwm_pin, GPIO.OUT)

        self.pwm = GPIO.PWM(self.pwm_pin, 1000)
        self.pwm.start(50)


        ## Buttons
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(4, GPIO.FALLING, callback=self.toggleMute, bouncetime=200)

    def sendApiCmd(self, cmd, arg=None):
        api_host = "http://" + self.host + ":" + self.port

        if cmd == 'getState':
            api_path = self.apiPath + "getState"
        else:
            api_path = self.apiPath + "commands/?cmd=" + cmd

        api_url = api_host + api_path

        if arg != None:
            api_url = api_url + "&" + cmd + "=" + str(arg)

        resp = requests.get(api_url)
        if resp.status_code != 200:
            print("Error!!! This didnt happen: ", api_url)

        logging.info("sendApiCmd: {} {}".format(api_url, resp.status_code))
        return resp

    def togglePlay(self, channel):
        self.sendApiCmd("toggle")
    
    def toggleRandom(self, channel):
        self.sendApiCmd("random")

    def toggleMute(self, channel):
        cur_mute = self.status['mute']
        if cur_mute:
            mute_cmd = 'unmute'
            self.status['mute'] = False
        else:
            mute_cmd = 'mute'
            self.status['mute'] = True
        
        # resp = requests.get("http://localhost:3000/api/v1/commands/?cmd=volume&volume="+mute_cmd)
        self.sendApiCmd("volume", mute_cmd)

    def toggleDim(self, channel):
        cur_dim = self.status['dim']
        if cur_dim:
            self.status['dim'] = False
            new_vol = self.getVolumeKnob()
        else:
            self.status['dim'] = True
            new_vol = self.getDimAmount()
        # print("New Volume: ", new_vol)
        resp = requests.get("http://localhost:3000/api/v1/commands/?cmd=volume&volume="+str(int(new_vol)))

    def getDimAmount(self):
        cur_vol = self.getVolumeKnob()
        return cur_vol - ((self.dim_amount * cur_vol) / 100)

    # Read values from volume knob
    # We do some trickery here by storing the last good reading from the pot
    # then checking to see if it has changed beyond a threshold. If it has, then
    # we return a good value. Otherwise, we return the last good reading. 
    # This is done because the readings are jittery coming from the pot and fluctuate
    # +- ~400 in either direction. The threshold of 500 is not noticable and gives us
    # a nice padding.
    def getVolumeKnob(self):
        vol_raw = AnalogIn(self.mcp, MCP.P0).value
        adjust_val = abs(vol_raw - self.last_raw_vol)
        if adjust_val > 500:
            vol = int(np.interp(vol_raw, [0, 65472], [0, 100]))
            self.last_raw_vol = vol_raw
        else:
            vol = int(np.interp(self.last_raw_vol, [0, 65472], [0, 100]))

        return vol

    def getFaderPos(self):
        vol_raw = AnalogIn(self.mcp, MCP.P1).value
        adjust_val = abs(vol_raw - self.last_raw_fad)
        if adjust_val > 500:
            vol = int(np.interp(vol_raw, [0, 65472], [0, 100]))
            self.last_raw_fad = vol_raw
        else:
            vol = int(np.interp(self.last_raw_fad, [0, 65472], [0, 100]))

        return vol

    def getSongPos(self):
        cur_pos = self.status['seek']
        if cur_pos:
            cur_pos = int(cur_pos / 1000)
        song_len = self.status['duration']
        pos = int(np.interp(int(cur_pos), [0, song_len], [0,100]))
        #logging.info("Fader: pos({:03d}), len({:03d})".format(pos, song_len))

        return pos

    def setVolume(self, volume):
        if self.status['mute']:
            return
        if self.status['dim']:
            volume = self.getDimAmount()
        self.sendApiCmd("volume", volume)
        # resp = requests.get("http://localhost:3000/api/v1/commands/?cmd=volume&volume="+str(volume))     

    def getStatus(self):
        #print("getStatus")
        resp = requests.get('http://localhost:3000/api/v1/getState')
        if resp.status_code != 200:
            print("WHAT THE FUCL")
        data = resp.json()
        self.status['status'] = data['status']
        self.status['seek'] = data['seek']
        self.status['duration'] = data['duration']
        self.status['random'] = data['random']
        self.status['repeat'] = data['repeat']
        self.status['volume'] = data['volume']
        self.status['mute'] = data['mute']
        # self.status = {
        #     'status': data['status'],
        #     'seek': data['seek'],
        #     'duration': data['duration'],
        #     'random': data['random'],
        #     'repeat': data['repeat'],
        #     'volume': data['volume'],
        #     'mute': data['mute']
        # }
        #print(self.status)

    def motorLeft(self):
        GPIO.output(self.in1_pin, False)
        GPIO.output(self.in2_pin, True)
        GPIO.output(self.en_pin, True)

    def motorRight(self):
        GPIO.output(self.in1_pin, True)
        GPIO.output(self.in2_pin, False)
        GPIO.output(self.en_pin, True)

    def motorOff(self):
        GPIO.output(self.in1_pin, False)
        GPIO.output(self.in2_pin, False)
        GPIO.output(self.en_pin, False)

    def motorSet(self, val):
        self.pwm.ChangeDutyCycle(val)

    def update(self):
        # Get Volume
        volume = self.getVolumeKnob()
        if volume != self.status['volume']:
            self.setVolume(volume)

        # Get fader position
        fad_pos = self.getFaderPos()
        song_pos = self.getSongPos()
        #logging.info("Fader Check: {} {}".format(fad_pos, song_pos))

        # Motor Stuff
        # self.motorLeft()
        self.motorSet(45)
        if fad_pos == song_pos:
            logval = "MATCH"
            self.motorOff()
        elif fad_pos >= song_pos:
            self.motorLeft()
            logval = "LEFT"
        elif fad_pos <= song_pos:
            self.motorRight()
            logval = "RIGHT"

        #logging.info("Fader {}: {} {}".format(logval, fad_pos, song_pos))

        # if fad_pos >= song_pos:
        #     self.motorSet(60)
        #     self.motorRight()
        # elif fad_pos <= song_pos:
        #     self.motorSet(60)
        #     self.motorLeft()
        # elif fad_pos == song_pos:
        #     self.motorOff()

        jittery
        





