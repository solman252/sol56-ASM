from emulator_internals.helpers import *

def exec_jmp(self: CPU, variant: str, reg1: str, val1: str):
    addr = register_or_val(self, reg1, val1).zfill(self.ruleset.mem_depth)
    self.PC = 

instructions = {
    'jmp': ('0x15 @ variant`8 @ reg1`4 @ 0x0 @ val1`16 @ 0x0000', exec_jmp),

    'jif': ('0x16 @ variant`8 @ f`4 @ reg1`4 @ 0x0 @ val1`16 @ 0x0000', dummy_func),

    'jnot': ('0x17 @ variant`8 @ f`4 @ reg1`4 @ 0x0 @ val1`16 @ 0x0000', dummy_func),

    'jeq': ('0x18 @ 0x00 @ reg1`4 @ reg2`4 @ val1`16 @ 0x0000', dummy_func),
    'jeqz': ('0x18 @ 0x01 @ reg1`4 @ 0x0 @ val1`16 @ 0x0000', dummy_func),

    'jne': ('0x19 @ 0x00 @ reg1`4 @ reg2`4 @ val1`16 @ 0x0000', dummy_func),
    'jnez': ('0x19 @ 0x01 @ reg1`4 @ 0x0 @ val1`16 @ 0x0000', dummy_func),

    'jlt': ('0x1A @ 0x00 @ reg1`4 @ reg2`4 @ val1`16 @ 0x0000', dummy_func),
    'jltz': ('0x1A @ 0x01 @ reg1`4 @ 0x0 @ val1`16 @ 0x0000', dummy_func),

    'jgt': ('0x1B @ 0x00 @ reg1`4 @ reg2`4 @ val1`16 @ 0x0000', dummy_func),
    'jgtz': ('0x1B @ 0x01 @ reg1`4 @ 0x0 @ val1`16 @ 0x0000', dummy_func),

    'jle': ('0x1C @ 0x00 @ reg1`4 @ reg2`4 @ val1`16 @ 0x0000', dummy_func),
    'jlez': ('0x1C @ 0x01 @ reg1`4 @ 0x0 @ val1`16 @ 0x0000', dummy_func),

    'jge': ('0x1D @ 0x00 @ reg1`4 @ reg2`4 @ val1`16 @ 0x0000', dummy_func),
    'jgez': ('0x1D @ 0x01 @ reg1`4 @ 0x0 @ val1`16 @ 0x0000', dummy_func),
}