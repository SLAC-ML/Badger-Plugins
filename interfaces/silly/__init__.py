import numpy as np
from typing import List, Dict
from badger import interface
from operator import itemgetter
import logging


class Interface(interface.Interface):

    name = 'silly'
    params: Dict = {
        'channel_prefix': 'c',
        'channel_count': 8
    }

    # Private variables
    _channels: List[str]
    _states: Dict[str, float]

    def __init__(self, **data):
        super().__init__(**data)

        prefix, count = itemgetter(
            'channel_prefix', 'channel_count')(self.params)

        self._channels = []
        self._states = {}
        for i in range(count):
            self._channels.append(f'{prefix}{i + 1}')
            self._states[f'{prefix}{i + 1}'] = 0

        self._channels.append('norm')
        self._states['norm'] = 0

    @interface.log
    def get_value(self, channel: str):
        try:
            value = self._states[channel]
        except KeyError:
            logging.warn(f'Channel {channel} doesn\'t exist!')
            value = None

        return value

    @interface.log
    def set_value(self, channel: str, value):
        if channel not in self._channels:
            logging.warn(f'Channel {channel} doesn\'t exist!')
            return

        try:
            self._states[channel] = value
            values = np.array([self._states[channel]
                              for channel in self._channels[:-1]])
            self._states['norm'] = np.sqrt(np.sum(values ** 2))
        except KeyError:
            logging.warn(f'Channel {channel} doesn\'t exist!')
