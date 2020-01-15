# Raspberry Pi Music Player

Music Player running on Raspberry Pi with buttons for play, pause, nex/prev track, shuffle and repeat.
Potentiometer for volume control and toggle switch for mute / dim. Powered by [Volumio](volumio.org). 

My addition is code to read the buttons and switches and control the standard volumio interface.

## Installation

- Follow the [normal install instructions](https://volumio.github.io/docs/User_Manual/Quick_Start_Guide) for [Volumio](volumio.org)
- [Enable SSH](https://volumio.github.io/docs/User_Manual/SSH.html)
- [Configure](https://volumio.org/raspberry-pi-display-and-volumio-touchscreen-music-player/) the [Official Raspberry Pi Display](https://www.element14.com/community/docs/DOC-78156/l/raspberry-pi-7-touchscreen-display)

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
