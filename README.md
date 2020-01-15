# Raspberry Pi Music Player

Music Player running on Raspberry Pi with buttons for play, pause, nex/prev track, shuffle and repeat.
Potentiometer for volume control and toggle switch for mute / dim. Powered by Volumio. 

My addition is code to read the buttons and switches and control the standard volumio interface.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

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
