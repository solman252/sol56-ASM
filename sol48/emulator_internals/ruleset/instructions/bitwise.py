from sol48.emulator_internals.helpers import *

# and => 0x30
def exec_0x30(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    out = bitwise_operation(*parse_arg_values(self,arg1_type,arg2_type,arg1,arg2), lambda a, b: a and b)
    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)
    debug(self,0x30,f'Logical AND: {display_value(self,arg1_type,arg1)} & {display_value(self,arg2_type,arg2)} = {value_display(out)}')
    display_res(self,0x30,out,arg1_type,arg1)
    display_flags(self,0x30)

# or => 0x31
def exec_0x31(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    out = bitwise_operation(*parse_arg_values(self,arg1_type,arg2_type,arg1,arg2), lambda a, b: a or b)
    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)
    debug(self,0x31,f'Logical OR: {display_value(self,arg1_type,arg1)} | {display_value(self,arg2_type,arg2)} = {value_display(out)}')
    display_res(self,0x31,out,arg1_type,arg1)
    display_flags(self,0x31)

# xor => 0x32
def exec_0x32(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    out = bitwise_operation(*parse_arg_values(self,arg1_type,arg2_type,arg1,arg2), lambda a, b: a != b)
    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)
    debug(self,0x32,f'Logical XOR: {display_value(self,arg1_type,arg1)} ^ {display_value(self,arg2_type,arg2)} = {value_display(out)}')
    display_res(self,0x32,out,arg1_type,arg1)
    display_flags(self,0x32)

# not => 0x33
def exec_0x33(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    arg1 = parse_arg_value(self,arg1_type,arg1)
    out = bitwise_operation(arg1, '', lambda a, b: not a)
    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)
    debug(self,0x33,f'Logical NOT: ~ {display_value(self,arg1_type,arg1)} = {value_display(out)}')
    display_res(self,0x33,out,arg1_type,arg1)
    display_flags(self,0x33)

# nand => 0x34
def exec_0x34(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    out = bitwise_operation(*parse_arg_values(self,arg1_type,arg2_type,arg1,arg2), lambda a, b: not (a and b))
    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)
    debug(self,0x34,f'Logical NAND: ~({display_value(self,arg1_type,arg1)} & {display_value(self,arg2_type,arg2)}) = {value_display(out)}')
    display_res(self,0x34,out,arg1_type,arg1)
    display_flags(self,0x34)

# nor => 0x35
def exec_0x35(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    out = bitwise_operation(*parse_arg_values(self,arg1_type,arg2_type,arg1,arg2), lambda a, b: not (a or b))
    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)
    debug(self,0x35,f'Logical NOR: ~({display_value(self,arg1_type,arg1)} | {display_value(self,arg2_type,arg2)}) = {value_display(out)}')
    display_res(self,0x35,out,arg1_type,arg1)
    display_flags(self,0x35)

# xnor => 0x36
def exec_0x36(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    out = bitwise_operation(*parse_arg_values(self,arg1_type,arg2_type,arg1,arg2), lambda a, b: a == b)
    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)
    debug(self,0x36,f'Logical XNOR: ~({display_value(self,arg1_type,arg1)} ^ {display_value(self,arg2_type,arg2)}) = {value_display(out)}')
    display_res(self,0x36,out,arg1_type,arg1)
    display_flags(self,0x36)