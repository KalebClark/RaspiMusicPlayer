# Raspberry Pi Music Player

Music Player running on Raspberry Pi with buttons for play, pause, nex/prev track, shuffle and repeat.
Potentiometer for volume control and toggle switch for mute / dim. Powered by [Volumio](volumio.org). 

My addition is code to read the buttons and switches and control the standard volumio interface.

## Installation

- Follow the [normal install instructions](https://volumio.github.io/docs/User_Manual/Quick_Start_Guide) for [Volumio](volumio.org)
- [Enable SSH](https://volumio.github.io/docs/User_Manual/SSH.html)
- [Configure](https://volumio.org/raspberry-pi-display-and-volumio-touchscreen-music-player/) the [Official Raspberry Pi Display](https://www.element14.com/community/docs/DOC-78156/l/raspberry-pi-7-touchscreen-display)

Note on configuring the display: Do not change the volumio password before you install. Volumio requires that the password be ```volumio``` to install. It is hardcoreded in their install scripts.

### Python & Python Modules
This turned out to be a pain, needs python version > 3.5 which introduced a bunch of issues installing. Its doable, but not straight forward or easy. I used pyenv to get the right version, then satisfied dependencies as they came up with module installation. Once you have ver > 3.5 installed then proceed.

Easiest way to do this is with pyenv. Check [here for details](https://realpython.com/intro-to-pyenv).

Also compile openssl from source and set flags like this:
```
export LDFLAGS="-L/usr/local/lib/"
export LD_LIBRARY_PATH="/usr/local/lib/"
export CPPFLAGS="-I/usr/local/include -I/usr/local/include/openssl"
```

#### Required Modules
- os
- json
- board
- busio
- requests
- digitalio
- numpy
- logging
- threading
- sleep
- time
- RPI.GPIO
- adafruit-blinka
- requests
- adafruit-circuitpython-mcp3xxx
- adafruit-circuitpython-cap1188

### Enable SPI
- Run ``` sudo apt-get update```
- Run ```sudo apt-get install raspi-config``` to install the raspi-config tool.
- run ```raspi-config```
- Select "Interfacing options"
- Select "Enable SPI"
- Select "Interfacing Options"
- Select "Enable i2c"
- Reboot

```bash
pip install foobar
```

## Usage
``` python io_test.py```
