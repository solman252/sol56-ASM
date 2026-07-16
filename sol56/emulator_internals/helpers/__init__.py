from lib.emulator import *
import emulator_internals as internal
from emulator_internals.helpers.argument_names import *
from emulator_internals.helpers.keycodes import keycodes

def dummy_func(*args,**kwargs): pass

def debug(self: CPU, *values, sep=' ', end='\n', indent=True):
    s = (('' if self._debug_indented else '\n')+'    ' if indent else '')+sep.join([str(v) for v in values])+end
    if self.debug_mode: print(s,end='')
    self.debug_log.append(s)
    self._debug_indented = indent

def register_or_val(self: CPU, reg: str, val: str): return val if int(reg,2) == 0 else self.registers[reg_keys[reg]].read()

def bit_rotate_left(val: str, amount: int):
    bits = len(val)
    val = int(val,2)
    return int_to_bin((val << amount%bits) & (2**bits-1) | ((val & (2**bits-1)) >> (bits-(amount%bits))),bits)

def bit_rotate_right(val: str, amount: int):
    bits = len(val)
    val = int(val,2)
    return int_to_bin(((val & (2**bits-1)) >> amount%bits) | (val << (bits-(amount%bits)) & (2**bits-1)),bits)

def bitwise(operator: str, val1: str, val2: str | int | None = None):
    if val2 is None and operator != '~': raise ValueError('Argument `val2` must be provided unless the operator is \'~\'.')
    if val2 is not None and type(val2) != int: val2 = int(val2,2)
    operations = {
        '~': lambda v1, v2: int_to_bin(~int(v1,2),len(v1)),
        '^': lambda v1, v2: int_to_bin(int(v1,2) ^ v2,len(v1)),
        '&': lambda v1, v2: int_to_bin(int(v1,2) & v2,len(v1)),
        '|': lambda v1, v2: int_to_bin(int(v1,2) | v2,len(v1)),
        '<<': lambda v1, v2: int_to_bin(int(v1,2) << v2,len(v1)),
        '>>': lambda v1, v2: int_to_bin(int(v1,2) >> v2,len(v1)),
        '<%': bit_rotate_left,
        '%>': bit_rotate_right,
    }
    if operator in operations: return operations[operator](val1,val2)
    raise ValueError(f'Unknown bitwise operator \'{operator}\'.')

def sign_val(self: CPU, val: str):
    if self.flags['s'] and val[0] == '1': return -(int(bitwise('~',val),2)+1)
    return int(val,2)
