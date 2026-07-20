from emulator_internals.helpers import *

def jmp(self: CPU, addr: str, condition_met: bool = True, condition: str = ''):
    addr = addr.zfill(self.ruleset.mem_depth)
    if condition_met: self.PC = int(addr,2)
    debug(self,f'{'J' if condition_met else 'Not j'}umping to 0x{bin_to_hex(addr)} ({self.PC}){'' if condition == '' else f'{condition} == {condition_met}'}')

def exec_jmp(self: CPU, variant: str, reg1: str, val1: str):
    jmp(self, register_or_val(self, reg1, val1))

def exec_jif(self: CPU, variant: str, flag: str, reg1: str, val1: str):
    jmp(self, register_or_val(self, reg1, val1), self.flags[flag_keys[flag]], flag_keys[flag])

def exec_jnot(self: CPU, variant: str, flag: str, reg1: str, val1: str):
    jmp(self, register_or_val(self, reg1, val1), !self.flags[flag_keys[flag]], '~'+flag_keys[flag])

def exec_jeq(self: CPU, variant: str, reg1: str, reg2: str, val1: str):
    r1 = self.registers[reg_keys[reg1]].read()
    r2 = '0' if variant == '0000' else self.registers[reg_keys[reg2]].read()
    jmp(self, register_or_val(self, reg1, val1), !self.flags[flag_keys[flag]], '~'+flag_keys[flag])

instructions = {
    'jmp': ('0x15 @ variant`8 @ reg1`4 @ 0x0 @ val1`16 @ 0x0000', exec_jmp),

    'jif': ('0x16 @ variant`8 @ flag`4 @ reg1`4 @ val1`16 @ 0x0000', exec_jif),

    'jnot': ('0x17 @ variant`8 @ f`4 @ reg1`4 @ val1`16 @ 0x0000', exec_jnot),

    'jeq': ('0x18 @ 0x00 @ reg1`4 @ reg2`4 @ val1`16 @ 0x0000', lambda self, **kwargs: v1, v2 = reg_keys[kwargs['reg1']], reg_keys[kwargs['reg2']]; exec_jmp(self, **kwargs, condition_met = !self.flags[f_k], condition = '~'+f_k)),
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