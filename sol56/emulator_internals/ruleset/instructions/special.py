from emulator_internals.helpers import *

instructions = {
    'nop': ('0x00 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000', dummy_func),
    'nop r1': ('0x00 @ 0x01 @ reg1`4 @ 0x0 @ 0x0000 @ 0x0000', dummy_func),
    'nop v1': ('0x00 @ 0x02 @ v1`40', dummy_func),

    'intd': ('0x01 @ variant`8 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', dummy_func),

    'intr': ('0x02 @ variant`8 @ rf`4 @ 0x0 @ 0x0000 @ 0x0000', dummy_func),

    'int': ('0x03 @ variant`8 @ reg1`4 @ 0x0 @ val1`16 @ 0x0000', dummy_func),

    'hlt': ('0x04 @ variant`8 @ reg1`4 @ 0x0 @ val1`16 @ 0x0000', dummy_func),

    'time': ('0x05 @ 0x0 @ m`4 @ reg1`4 @ 0x0 @ 0x0000 @ 0x0000', dummy_func),
}