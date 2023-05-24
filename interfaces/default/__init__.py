from badger import interface
from typing import Dict


class Interface(interface.Interface):

    name = 'default'
    # If params not specified, it would be an empty dict

    _states: Dict

    def __init__(self, **data):
        super().__init__(**data)

        self._states = {}

    def get_value(self, channel: str):
        try:
            value = self._states[channel]
        except KeyError:
            self._states[channel] = value = 0

        return value

    def set_value(self, channel: str, value):
        self._states[channel] = value
