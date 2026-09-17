from lib.emulator import *
import sol48.emulator_internals as internal
from sol48.emulator_internals.helpers.arg_types import *
from sol48.emulator_internals.helpers.keycodes import keycodes

import math, datetime, time, pygame

from typing import Any
from types import FunctionType

def dummy_func(*args,**kwargs): pass

def debug(self: CPU, opcode: int, *values, sep: str = ' ', end: str = '\n', indent: bool = True, ignore_debug_mode: bool = False):
    s = (('' if self._debug_indented else '\n')+'    ' if indent else '')+sep.join([str(v) for v in values])+end
    if (self.debug_mode and self._debug_whitelist[opcode]) or ignore_debug_mode:print(s,end='')
    self.debug_log.append(s)
    self._debug_indented = indent

def parse_arg(self: CPU, arg_type: str, arg: str):
    match ARGTYPE(int(arg_type,2)):
        case ARGTYPE.REG: # Register
            return REG(int(arg,2)).name
        case ARGTYPE.IMM: # Immediate
            return arg
        case ARGTYPE.MEM: # Memory
            return self.RAM.read(int(self.registers[REG(int(arg,2)).name].read(),2)*self.ruleset.mem_depth,self.ruleset.mem_depth)
        case ARGTYPE.ADDR: # Address
            return self.RAM.read(int(arg,2)*self.ruleset.mem_depth,self.ruleset.mem_depth)
        case ARGTYPE.CODE: # Interrupt Code
            return int(arg,2)
        case ARGTYPE.PORT: # IO Port
            raise NotImplementedError
        case ARGTYPE.FLAG: # Flag
            return FLAG(int(arg,2)).name
        case ARGTYPE.TIME_ASPECT: # Time Aspect
            return TIME_ASPECT(int(arg,2))

def parse_arg_value(self: CPU, arg_type: str, arg: str) -> str:
    match ARGTYPE(int(arg_type,2)):
        case ARGTYPE.REG: # Register
            return self.registers[REG(int(arg,2)).name].read()
        case ARGTYPE.IMM: # Immediate
            return arg
        case ARGTYPE.MEM: # Memory
            return self.RAM.read(int(self.registers[REG(int(arg,2)).name].read(),2)*self.ruleset.mem_depth,self.ruleset.mem_depth)
        case ARGTYPE.ADDR: # Address
            return self.RAM.read(int(arg,2)*self.ruleset.mem_depth,self.ruleset.mem_depth)
        case ARGTYPE.CODE: # Interrupt Code
            return int(arg,2)
        case ARGTYPE.PORT: # IO Port
            raise NotImplementedError
        case ARGTYPE.FLAG: # Flag
            return int_to_bin(int(self.flags[FLAG(int(arg,2)).name]))
        case ARGTYPE.TIME_ASPECT: # Time Aspect
            return int_to_bin(get_time_aspect(self,TIME_ASPECT(int(arg,2))))

def display_value(self: CPU, arg_type: str, arg: str, signed: bool = False):
    match ARGTYPE(int(arg_type,2)):
        case ARGTYPE.REG: # Register
            reg = REG(int(arg,2)).name
            return f'Register {reg.upper()} ({value_display(parse_arg_value(self,arg_type,arg),signed=signed)})'
        case ARGTYPE.IMM: # Immediate
            return f'Immediate value ({value_display(arg,signed=signed)})'
        case ARGTYPE.MEM: # Memory
            reg = REG(int(arg,2)).name
            return f'Memory at address found in register {reg.upper()} ({value_display(parse_arg_value(self,arg_type,arg),signed=signed)})'
        case ARGTYPE.ADDR: # Address
            return f'Memory at immediate address ({value_display(parse_arg_value(self,arg_type,arg,signed=signed))})'
        case ARGTYPE.CODE: # Interrupt Code
            return f'Handler address for interrupt code 0x{bin_to_hex(arg,digits=2)} (0x{bin_to_hex(parse_arg_value(self,arg_type,arg))})'
        case ARGTYPE.PORT: # IO Port
            raise NotImplementedError
        case ARGTYPE.FLAG: # Flag
            flag = FLAG(int(arg,2)).name
            return f'Flag {flag.upper()} ({self.flags[flag]})'
        case ARGTYPE.TIME_ASPECT: # Time Aspect
            aspect = TIME_ASPECT(int(arg,2))
            return f'Time aspect "{aspect.name.title()}" ({value_display(parse_arg_value(self,arg_type,arg),signed=signed)})'

def get_time_aspect(self, aspect: TIME_ASPECT):
    now = datetime.datetime.now()
    match aspect:
        case TIME_ASPECT.uptime: return int(time.time() - self.start_time) % 0xFFFF+1
        case TIME_ASPECT.ms: return now.microsecond // 10000
        case TIME_ASPECT.sec: return now.second
        case TIME_ASPECT.min: return now.minute
        case TIME_ASPECT.hour: return now.hour
        case TIME_ASPECT.weekday: return now.isoweekday()
        case TIME_ASPECT.monthday: return now.day
        case TIME_ASPECT.yearday: return now.timetuple().tm_yday
        case TIME_ASPECT.month: return now.month
        case TIME_ASPECT.year: return now.year

def parse_args(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str): return parse_arg(self,arg1_type,arg1), parse_arg(self,arg2_type,arg2)

def parse_arg_values(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str): return parse_arg_value(self,arg1_type,arg1), parse_arg_value(self,arg2_type,arg2)

def int_to_bin(v: int, bits: int = 16): return bin(v).removeprefix('0b').zfill(bits)[-bits:]

def int_to_hex(v: int, bits: int | None = 16, digits: int | None = None):
    if digits == None:
        if bits == None:
            raise ValueError('Either bits or digits must be provided.')
        else:
            digits = math.ceil(bits / 4)
    return hex(v).removeprefix('0x').zfill(digits)[-digits:].upper()

def bin_to_hex(v: str, digits: int | None = None): return int_to_hex(int(v,2), digits= digits if digits != None else len(v)//4)

def hex_to_bin(v: str, bits: int | None = None): return int_to_bin(int(v,16), bits if bits != None else len(v)*4)

def bin_to_signed(v: str):
    n = int(v, 2)
    return n - (1 << len(v)) if n & (1 << (len(v) - 1)) else n

def signed_to_bin(v: str, bits: int = 16): return format(v & ((1 << bits) - 1), f'0{bits}b')

def value_display(v: str, hide_binary: bool = False, signed: bool = False):
    sep = '->'
    return f'{int(v,2)} (unsigned){f' {sep} {bin_to_signed(v)} (signed)' if signed else ''} {sep} 0x{bin_to_hex(v)}{'' if hide_binary else f' {sep} 0b{v}'}'

def bitwise_operation(v1: str, v2: str, operation: FunctionType):
    v1 = v1.zfill(max(len(v1),len(v2))) ; v2 = v2.zfill(max(len(v1),len(v2)))
    return ''.join(['1' if operation(v1[i] == '1',v2[i] == '1') is True else '0' for i in range(len(v1))])

def set_flags(self: CPU, out: str, res_s: int = 0, res_u: int = 0, carry: bool = False, overflow: bool = False):
    self.flags['z'] = int(out,2) == 0
    self.flags['s'] = out[0] == '1'

    if carry:
        self.flags['c'] = res_u > 0xFFFF

    if overflow:
        self.flags['o'] = res_s < -0x8000 or res_s > 0x7FFF

def display_flags(self: CPU, opcode: int, carry: bool = False, overflow: bool = False):
    debug(self,opcode,f'Zero flag set to {self.flags['z']}')
    debug(self,opcode,f'Sign flag set to {self.flags['s']}')
    if carry: debug(self,0x20,f'Carry flag set to {self.flags['c']}')
    if overflow: debug(self,0x20,f'Overflow flag set to {self.flags['o']}')

def conditional_jump(self: CPU, opcode: int, arg_type: str, arg: str, condition: str, condition_met: bool):
    arg = parse_arg(self,arg_type,arg)
    if int(arg,2) % self.ruleset.inst_depth != 0:
        debug(self,0x24,'Raising unaligned jump address exception.')
        self.interrupt(0x05)
        self.registers['a'].write(int_to_bin(self.PC,self.registers['a'].size))
        return
    if condition != None: debug(self,opcode,f'{condition}: {condition_met}')
    debug(self,opcode,f'{'J' if condition_met else 'Not j'}umping to address {value_display(arg,True)}.')
    if condition_met:
        self.PC = int(arg,2)
        return {'INC PC': False}

def conditional_move(self: CPU, opcode: int, arg1_type: str, arg1: str, arg2_type: str, arg2: str, condition: str, condition_met: bool):
    arg1 = parse_arg_value(self,arg1_type,arg1)

    match ARGTYPE(int(arg2_type,2)):
        case ARGTYPE.REG: # Register
            dest = f'Register {REG(int(arg2,2)).name.upper()}'
        case ARGTYPE.MEM: # Memory
            dest = f'Memory at address found in register {REG(int(arg2,2)).name.upper()}'
        case ARGTYPE.ADDR: # Address
            dest = f'Memory at immediate address'
        case ARGTYPE.PORT: # IO Port
            raise NotImplementedError

    if condition != None: debug(self,opcode,f'{condition}: {condition_met}')
    debug(self,opcode,f'{'C' if condition_met else 'Not c'}opying value {value_display(arg1,signed=True)} into {dest}.')
    if condition_met:
        match ARGTYPE(int(arg2_type,2)):
            case ARGTYPE.REG: # Register
                self.registers[REG(int(arg2,2)).name].write(arg1)
            case ARGTYPE.MEM: # Memory
                self.RAM.write(arg1,self.registers[REG(int(arg2,2)).name].read()*self.ruleset.mem_depth)
            case ARGTYPE.ADDR: # Address
                self.RAM.write(arg1,parse_arg_value(self,arg2_type,arg2)*self.ruleset.mem_depth)
            case ARGTYPE.PORT: # IO Port
                raise NotImplementedError

def write_res(self: CPU, out: str, arg_type: str, arg: str):
    self.registers['res'].write(out)
    if ARGTYPE(int(arg_type,2)) == ARGTYPE.REG and self.flags['r']: self.registers[REG(int(arg,2)).name].write(out)

def display_res(self: CPU, opcode: int, out: str, arg_type: str, arg: str):
    debug(self,opcode,f'{value_display(out,signed=True)} written to the result register.')
    if ARGTYPE(int(arg_type,2)) == ARGTYPE.REG and self.flags['r']: debug(self,opcode,f'{value_display(out,signed=True)} written to register {REG(int(arg,2)).name.upper()}.')