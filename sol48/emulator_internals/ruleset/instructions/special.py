from sol48.emulator_internals.helpers import *

# nop => 0x00
def exec_0x00(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    debug(self,0x00,'No operation performed.')

# time => 0x01
def exec_0x01(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    aspect: TIME_ASPECT ; reg: REG ; aspect, reg = parse_args(self,arg1_type,arg2_type,arg1,arg2)
    value: int = get_time_aspect(self,aspect)
    self.registers[reg].write(int_to_bin(value,self.registers[reg].size))
    debug(self,0x01,f'Time Aspect "{aspect.name.title()}" ({value} / 0x{int_to_hex(value)} / 0b{int_to_bin(value,self.registers[reg].size)}) written to register {reg.upper()}.')