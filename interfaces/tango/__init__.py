import tango
from badger import interface


class Interface(interface.Interface):

    name = 'tango'

    def __init__(self, params=None):
        super().__init__(params)

    @staticmethod
    def get_default_params():
        return None

    def get_value(self, channel: str, attr: str):
        attr = tango.AttributeProxy(channel)
        return attr.read().value

    def set_value(self, channel: str, value, attr: str):
        dev = tango.DeviceProxy(channel)
        dev.write_attribute(attr, value)
