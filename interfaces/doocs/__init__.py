import pydoocs
from badger import interface


class Interface(interface.Interface):

    name = 'doocs'

    def __init__(self, params=None):
        super().__init__(params)

    @staticmethod
    def get_default_params():
        return None

    def get_value(self, channel: str):
        val = pydoocs.read(channel)

        return val['data']

    def set_value(self, channel: str, value):
        pydoocs.write(channel, float(value))
