from emulator_internals.helpers import *

def exec_flag(self: CPU, flag: str, value: str):
    flag = flag_keys[flag]
    value = value == '1'
    self.flags[flag] = value
    debug(self,f'Flag {flag} set to {str(value).lower()}.')

def set_flags(self: CPU, result: int | None = None, flags: list[str] = ['c','z','n','o']):
    res = self.registers['res']
    size = res.size
    res = int(res.read(),2) if result == None else result

    self.flags['c'] = res >= 2**size
    self.flags['z'] = res == 0
    self.flags['n'] = res < 0
    self.flags['o'] = res < - (2**(size-1))
    
    for flag in flags: debug(self,f'Flag {flag} set to {str(self.flags[flag]).lower()}.')

def exec_add_sub(self: CPU, variant: str, reg1: str, reg2: str, val1: str, val2: str, use_carry: bool = False, subtract: bool = False, modulo: bool = False):
    v1, v2 = [sign_val(self,register_or_val(self,reg,val)) for (reg,val) in [(reg1,val1),(reg2,val2)]]
    use_carry = use_carry and not (subtract or modulo)
    c = int(self.flags['c']) if use_carry else 0

    result = v1 % v2 if modulo else (v1 - v2 if subtract else v1 + v2 + c)
    debug(self,f'{v1} {'%' if modulo else ('-' if subtract else '+')} {v2}{f' + {c}' if use_carry else ''} = {result}')

    out = int_to_bin(result,self.registers['res'].size,self.flags['s'])
    self.registers['res'].write(out)
    debug(self,f'Result register set to 0x{bin_to_hex(out)} ({result})')
    set_flags(self,result)

def exec_bit_op(self: CPU, variant: str, reg1: str, reg2: str, val1: str, val2: str, operator: str = '&', xnor: bool = False):
    v1, v2 = [register_or_val(self,reg,val) for (reg,val) in [(reg1,val1),(reg2,val2)]]
    if xnor: operator = '^'

    out = bitwise(operator,v1,v2)
    if xnor: out = bitwise('~',out)
    debug(self,f'{'~(' if xnor else ''}0b{v1} {operator} {f'{int(v2,2)}' if operator in ['<<','>>','<%','%>'] else f'0b{v2}'}{')' if xnor else ''} = 0b{out}')

    self.registers['res'].write(out)
    debug(self,f'Result register set to 0x{bin_to_hex(out)} (0b{out})')
    set_flags(self)

instructions = {
    'flag': ('0x06 @ flag`4 @ 0b000 @ value`1 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000', exec_flag),

    'add': ('0x07 @ 0x0 @ variant`4 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', exec_add_sub),

    'addc': ('0x07 @ 0x1 @ variant`4 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', lambda self, **kwargs: exec_add_sub(self, **kwargs, use_carry=True)),

    'sub': ('0x08 @ variant`8 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', lambda self, **kwargs: exec_add_sub(self, **kwargs, subtract=True)),

    'mod': ('0x09 @ variant`8 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', lambda self, **kwargs: exec_add_sub(self, **kwargs, modulo=True)),

    'and': ('0x0A @ variant`8 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', exec_bit_op),

    'or': ('0x0B @ variant`8 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', lambda self, **kwargs: exec_bit_op(self, **kwargs, operator='|')),

    'xor': ('0x0C @ variant`8 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', lambda self, **kwargs: exec_bit_op(self, **kwargs, operator='^')),

    'xnor': ('0x0D @ variant`8 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', lambda self, **kwargs: exec_bit_op(self, **kwargs, xnor=True)),

    'bsl': ('0x0E @ variant`8 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', lambda self, **kwargs: exec_bit_op(self, **kwargs, operator='<<')),

    'bsr': ('0x0F @ variant`8 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', lambda self, **kwargs: exec_bit_op(self, **kwargs, operator='>>')),

    'brl': ('0x10 @ variant`8 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', lambda self, **kwargs: exec_bit_op(self, **kwargs, operator='<%')),

    'brr': ('0x11 @ variant`8 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', lambda self, **kwargs: exec_bit_op(self, **kwargs, operator='%>')),
}