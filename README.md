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
- numpy

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

```python
import foobar

foobar.pluralize('word') # returns 'words'
foobar.pluralize('goose') # returns 'geese'
foobar.singularize('phenomena') # returns 'phenomenon'
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
