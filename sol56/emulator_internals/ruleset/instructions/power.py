from emulator_internals.helpers import *

def exec_pwd(self: CPU):
    debug(self,'Shutting down.\n}')
    exit()

instructions = {
    'pwd': ('0x1E @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000',exec_pwd),
}