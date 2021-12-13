from badger import interface

from numpy import random


class Interface(interface.Interface):

    name = 'doocs_mock'

    def __init__(self, params=None):
        super().__init__(params)

    @staticmethod
    def get_default_params():
        return None

    def get_value(self, channel: str):
        print("Called get_value for channel: {}.".format(channel))
        return random.random()

    def set_value(self, channel: str, value):
        print("Called set_value for channel: {}, with value: {}".format(channel, value))
