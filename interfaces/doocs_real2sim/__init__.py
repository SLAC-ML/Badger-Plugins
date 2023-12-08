import pydoocs
from badger import interface


class Interface(interface.Interface):

    name = 'doocs_real2sim'

    def __init__(self, params=None):
        super().__init__(params)

    @staticmethod
    def get_default_params():
        return None
    
    def _replace_fac(channel: str) -> str:
        if channel.startswith("XFEL."):
            return channel.replace("XFEL.", "XFEL_SIM.")
        else:
            return channel


    def get_value(self, channel: str):
        channel = self._replace_fac(channel)
        val = pydoocs.read(channel)

        return val['data']

    def set_value(self, channel: str, value):
        channel = self._replace_fac(channel)
        pydoocs.write(channel, float(value))
