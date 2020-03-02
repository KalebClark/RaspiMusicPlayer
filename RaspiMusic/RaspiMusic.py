import os
import json
import time
import board
import busio
import logging
import requests
import digitalio
import numpy as np
import RPi.GPIO as GPIO
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_cap1188.i2c import CAP1188_I2C
from adafruit_mcp3xxx.analog_in import AnalogIn

## Setup logging
format = "%(name)s(%(levelname)s): %(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

# RaspiMusic Class
# This class handles all IO with the hardware, as well as communications
# with volumio. By REST API and command line mpc for seeking since volumio
# REST API does not have an endpoint for this.
class RaspiMusic:
    def __init__(self):
        self.host = "localhost"
        self.port = ":3000"
        self.apiPath = "/api/v1/"
        self.last_raw_vol = 0
        self.last_raw_fad = 0
        self.vol_raw_range = [0, 65472]
        self.vol_real_range = [100, 0]
        self.bouncetime = 500
        self.dim_amount = 50
        self.xsetRun = False
        self.seekRun = 0
        self.seeking = False
        self.vstate = {
            'status': None,
            'seek': 0,
            'duration': None,
            'random': None,
            'repeat': None,
            'volume': None,
            'mute': False,
            'dim': False
        }
        
        # Setup CAP1188 Board
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.cap = CAP1188_I2C(self.i2c)
        self.cap._write_register(0x1F, 65)

        # Setup MCP3008
        self.mcp = MCP.MCP3008(
            busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI),
            digitalio.DigitalInOut(board.D8)
        )

        # Setup TB6612FNG Motor Controller
        self.pin_in1 = 24
        self.pin_in2 = 23
        self.pin_pwm = 18
        self.pin_en = 25
        GPIO.setup(self.pin_in1, GPIO.OUT)
        GPIO.setup(self.pin_in2, GPIO.OUT)
        GPIO.setup(self.pin_pwm, GPIO.OUT)
        GPIO.setup(self.pin_en, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin_pwm, 100)
        self.pwm.start(45)
        GPIO.output(self.pin_en, GPIO.HIGH)
        self.motorOff()

        # Setup buttons & Toggle Switch
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Toggle Dim
        GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Toggle Mute    
        GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Repeat Button
        GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Previous Button
        GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Play/Pause Button
        GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Next Button
        GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Random Button

        # Set interupts and callbacks for momentary buttons.    
        GPIO.add_event_detect(17, GPIO.FALLING, callback=self.btn_repeat, bouncetime=self.bouncetime)
        GPIO.add_event_detect(27, GPIO.FALLING, callback=self.btn_prev, bouncetime=self.bouncetime)
        GPIO.add_event_detect(22, GPIO.FALLING, callback=self.btn_playpause, bouncetime=self.bouncetime)
        GPIO.add_event_detect(5, GPIO.FALLING, callback=self.btn_next, bouncetime=self.bouncetime)
        GPIO.add_event_detect(6, GPIO.FALLING, callback=self.btn_random, bouncetime=self.bouncetime)

    """
        tgl_dim()

        When toggle switch is detected to be thrown in this direction, it triggers
        this method. 

        Sets the vstate state and fires off the REST command
    """
    def tgl_dim(self):
        cur_dim = self.vstate['dim']
        if cur_dim:
            self.vstate['dim'] = False
            new_vol = self.getVolumeKnob()
        else:
            self.vstate['dim'] = True
            new_vol = self.getDimAmount()

        logging.info("Toggle: Dim " + str(int(new_vol)))
        self.sendApiCmd("volume", str(int(new_vol)))

    """
        tgl_mute()

        When toggle switch is detected to be thrown in this direction, it triggers
        this method.

        Sets the vstate state and fires off the REST command.
    """
    def tgl_mute(self):
        cur_mute = self.vstate['mute']
        if cur_mute:
            mute_cmd = 'unmute'
            self.vstate['mute'] = False
        else:
            mute_cmd = 'mute'
            self.vstate['mute'] = True

        logging.info("Toggle: Mute " + mute_cmd)
        self.sendApiCmd("volume", mute_cmd)

    """
        btn_repeat(channel)
        This method is fired by an event handler setup for the input on this button.
    """
    def btn_repeat(self, channel):
        logging.info("Button: Repeat")
        self.sendApiCmd("repeat", True)

    """
        btn_prev(channel)
        This method is fired by an event handler setup for the input on this button.
    """
    def btn_prev(self, channel):
        logging.info("Button: Previous")
        self.sendApiCmd("prev")

    """
        btn_playpause(channel)
        This method is fired by an event handler setup for the input on this button.
    """
    def btn_playpause(self, channel):
        logging.info("Button: Play/Pause")
        self.sendApiCmd("toggle")
        self.displayOn()

    """
        btn_next(channel)
        This method is fired by an event handler setup for the input on this button.
    """
    def btn_next(self, channel):
        logging.info("Button: Next")
        self.sendApiCmd("next")

    """
        btn_random(channel)
        This method is fired by an event handler setup for the input on this button.
    """
    def btn_random(self, channel):
        logging.info("Button: Random")
        self.sendApiCmd("random", True)

    """
        seekSong(song_len, seek)

    """
    def seekSong(self, song_len, seek):
        if self.seeking:
            return

        song_len = (song_len * 1000)
        song_seek = (song_len * (seek/100))
        cmd =  "mpc seek "+ str(seek) + "%"
        os.system(cmd)
        self.seeking = True
        logging.info("Seeking to: " + str(seek))

    """
        motorLeft()
        Set the direction of the motor, wait then shut off motor
    """
    def motorLeft(self):
        GPIO.output(self.pin_in1, False)
        GPIO.output(self.pin_in2, True)
        time.sleep(.25)
        self.motorOff()
        #GPIO.output(self.pin_en, True)

    """
        motorRight()
        Set the direction of the motor, wait then shut off motor
    """
    def motorRight(self):
        GPIO.output(self.pin_in1, True)
        GPIO.output(self.pin_in2, False)
        time.sleep(.25)
        self.motorOff()
        #GPIO.output(self.pin_en, True)

    """
        motorOff()
        Set motor inputs to OFF. 
    """
    def motorOff(self):
        GPIO.output(self.pin_in1, False)
        GPIO.output(self.pin_in2, False)
        #GPIO.output(self.pin_en, False)

    """
        motorSet()
        Change the duty cycle of the pwm pin for motor speed.
    """
    def motorSet(self, val):
        self.pwm.ChangeDutyCycle(val)

    """
        fadeTouch()
        Check if fader capacitive touch has been activated and 
        return boolean value.
    """
    def fadeTouch(self):
        if self.cap[1].value:
            self.displayOn()
            return True

        return False

    """
        sendApiCmd(cmd, arg(optional))
        Format REST API command and send it!
    """
    def sendApiCmd(self, cmd, arg=None):
        api_host = "http://" + self.host + self.port

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

    """
        setVolume(volume)
        Return if system is muted. If dimmed, get appropriate dim value. Send
        the volume value via REST API
    """
    def setVolume(self, volume):
        if self.vstate['mute']:
            return
        if self.vstate['dim']:
            volume = self.getDimAmount()
        self.sendApiCmd("volume", volume)
    
    """
        getDimAmount()
        Get the current value from the volume knob and do the math 
        to set new volume reduction by self.dimAmount %
    """
    def getDimAmount(self):
        cur_vol = self.getVolumeKnob()
        return cur_vol - ((self.dim_amount * cur_vol) / 100)

    """
        getFaderPos()
        Read raw value from MCP chip and subtract from last read. If greater than 500 in difference,
        interpolate and save as last read. If less than 500, interpolate and return. 
    """
    def getFaderPos(self):
        fad_raw = AnalogIn(self.mcp, MCP.P1).value
        adjust_val = abs(fad_raw - self.last_raw_fad)
        if adjust_val > 500:
            fad = int(np.interp(fad_raw, [0, 65472], [0, 100]))
            self.last_raw_fad = fad_raw
        else:
            fad = int(np.interp(self.last_raw_fad, [0, 65472], [0, 100]))

        return fad    

    """
        Read values from volume knob
        We do some trickery here by storing the last good reading from the pot
        then checking to see if it has changed beyond a threshold. If it has, then
        we return a good value. Otherwise, we return the last good reading. 
        This is done because the readings are jittery coming from the pot and fluctuate
        +- ~400 in either direction. The threshold of 500 is not noticable and gives us
        a nice padding.
    """
    def getVolumeKnob(self):
        vol_raw = AnalogIn(self.mcp, MCP.P0).value
        adjust_val = abs(vol_raw - self.last_raw_vol)
        if adjust_val > 650:
            vol = int(np.interp(vol_raw, self.vol_raw_range, self.vol_real_range))
            self.last_raw_vol = vol_raw
        else:
            vol = int(np.interp(self.last_raw_vol, self.vol_raw_range, self.vol_real_range))

        return vol
    """
        getSongPos()
        Get position from API read state. 
    """
    def getSongPos(self):
        cur_pos = self.vstate['seek']
        if cur_pos:
            cur_pos = int(cur_pos / 1000)
        song_len = self.vstate['duration']
        pos = int(np.interp(int(cur_pos), [0, song_len], [0,100]))
        #logging.info("Fader: pos({:03d}), len({:03d})".format(pos, song_len))

        return pos

    """
        getState()
        Get data from REST API and set vstate dictionary. 
    """
    def getState(self):
        # print("GetStatus")
        state = self.sendApiCmd("getState")
        data = state.json()
        self.vstate['status'] = data['status']
        self.vstate['seek'] = data['seek']
        self.vstate['duration'] = data['duration']
        self.vstate['random'] = data['random']
        self.vstate['repeat'] = data['repeat']
        self.vstate['volume'] = data['volume']
        self.vstate['mute'] = data['mute'] 
        self.xsetRun = False

        # Seek counter
        if self.seekRun > 0:
            self.seekRun += 1

        if self.seekRun >= 4:
            self.seekRun = 0
            self.seeking = False

    """
        getMuteSwitch()
        Read GPIO input for mute switch and return boolean
    """
    def getMuteSwitch(self):
        if GPIO.input(16) == GPIO.HIGH:
            return True
        else:
            return False

    """
        getDimSwitch()
        Read GPIO input for dim switch and return boolean
    """
    def getDimSwitch(self):
        if GPIO.input(26) == GPIO.HIGH:
            return True
        else:
            return False

    """
        displayOn()
        Run xset command to turn display on. 
    """
    def displayOn(self):
        if not self.xsetRun:
            os.system("xset -display :0 s reset dpms force on")
        self.xsetRun = True

    # UPDATE
    #####################################################
    def update(self):
        # Dim & Mute
        mute_switch = self.getMuteSwitch()
        dim_switch = self.getDimSwitch()

        # Mute
        if mute_switch != self.vstate['mute']:
            self.tgl_mute()

        # Dim
        if dim_switch != self.vstate['dim']:
            self.tgl_dim()

        # Volume
        vol = self.getVolumeKnob()
        if vol != self.vstate['volume']:
            if not self.vstate['dim']:
                self.setVolume(vol)

        # Get Song & Fader Position
        fader_pos = self.getFaderPos()
        song_pos = self.getSongPos()
        diff = abs(song_pos - fader_pos)

        # Turn off motor controller when touched.
        while self.fadeTouch():
            time.sleep(.05)
            self.seekRun = 1
            print("Waiting...")

        if self.seekRun > 1 and diff >= 10:
            self.seekSong(self.vstate['duration'], fader_pos)

        # Set Speed
        if diff >= 10:
            self.pwm.ChangeDutyCycle(65)
        else:
            self.pwm.ChangeDutyCycle(20)

        # Move the fader

        if diff >= 3 and self.vstate['status'] == "play" and self.seekRun == 0:
            if song_pos >= fader_pos:
                self.motorRight()
            elif song_pos <= fader_pos:
                self.motorLeft()


