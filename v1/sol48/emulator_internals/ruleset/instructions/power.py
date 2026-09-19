from sol48.emulator_internals.helpers import *

# pwd => 0x80
def exec_0x80(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    debug(self,0x80,'Powering down...')
    return {'Exit': True}