import numpy as np
from typing import List, Dict
from badger import interface
import logging


class Interface(interface.Interface):

    name = 'silly'

    # Intf params
    channel_prefix: str = 'c'
    channel_count: int = 8

    # Private variables
    _channels: List[str]
    _states: Dict[str, float]

    def __init__(self, **data):
        super().__init__(**data)

        prefix, count = self.channel_prefix, self.channel_count

        self._channels = []
        self._states = {}
        for i in range(count):
            self._channels.append(f'{prefix}{i + 1}')
            self._states[f'{prefix}{i + 1}'] = 0

        self._channels.append('norm')
        self._states['norm'] = 0

    @interface.log
    def get_values(self, channel_names):
        channel_outputs = {}

        for channel in channel_names:
            try:
                value = self._states[channel]
            except KeyError:
                logging.warn(f'Channel {channel} doesn\'t exist!')
                value = None

            channel_outputs[channel] = value

        return channel_outputs

    @interface.log
    def set_values(self, channel_inputs):
        for channel, value in channel_inputs.items():
            if channel not in self._channels:
                logging.warn(f'Channel {channel} doesn\'t exist!')
                continue

            try:
                self._states[channel] = value
                values = np.array([self._states[channel]
                                   for channel in self._channels[:-1]])
                self._states['norm'] = np.sqrt(np.sum(values ** 2))
            except KeyError:
                logging.warn(f'Channel {channel} doesn\'t exist!')
