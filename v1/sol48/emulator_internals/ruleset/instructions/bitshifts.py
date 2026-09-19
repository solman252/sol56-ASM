from sol48.emulator_internals.helpers import *

# shl => 0x40
def exec_0x40(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v2 = int(v2,2)
    out = v1[v2:]+('0'*v2)

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)

    debug(self,0x40,f'Left shift: {display_value(self,arg1_type,arg1)} << {display_value(self,arg2_type,arg2)} = {value_display(out)}')
    display_res(self,0x40,out,arg1_type,arg1)
    display_flags(self,0x40)

# shr => 0x41
def exec_0x41(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v2 = int(v2,2)
    out = v1[:-v2].zfill(len(v1))

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)

    debug(self,0x41,f'Logical / unsigned right shift: {display_value(self,arg1_type,arg1)} >>> {display_value(self,arg2_type,arg2)} = {value_display(out)}')
    display_res(self,0x41,out,arg1_type,arg1)
    display_flags(self,0x41)

# sar => 0x42
def exec_0x42(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v2 = int(v2,2)
    out = (v1[0]*v2)+v1[:-v2]

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)

    debug(self,0x42,f'Arithmetic / signed right shift: {display_value(self,arg1_type,arg1)} >>> {display_value(self,arg2_type,arg2)} = {value_display(out)}')
    display_res(self,0x42,out,arg1_type,arg1)
    display_flags(self,0x42)

# rol => 0x43
def exec_0x43(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v2 = int(v2,2) % len(v1)
    out = v1[v2:]+v1[:v2]

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)

    debug(self,0x43,f'Left rotation: {display_value(self,arg1_type,arg1)} <) {display_value(self,arg2_type,arg2)} = {value_display(out)}')
    display_res(self,0x43,out,arg1_type,arg1)
    display_flags(self,0x43)

# ror => 0x44
def exec_0x44(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v2 = -(int(v2,2) % len(v1))
    out = v1[v2:]+v1[:v2]

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)

    debug(self,0x44,f'Right rotation: {display_value(self,arg1_type,arg1)} (> {display_value(self,arg2_type,arg2)} = {value_display(out)}')
    display_res(self,0x44,out,arg1_type,arg1)
    display_flags(self,0x44)

# rcl => 0x45
def exec_0x45(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v2 = int(v2,2) % (len(v1)+1)
    if v2 == 0:
        out = v1
    else:
        v1 = str(int(self.flags['c'])) + v1
        out = v1[v2:]+v1[:v2]
        self.flags['c'] = out[0] == '1'
        out = out[1:]

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)

    debug(self,0x45,f'Left rotation with carry: {display_value(self,arg1_type,arg1)} <) {display_value(self,arg2_type,arg2)} = {value_display(out)}')
    display_res(self,0x45,out,arg1_type,arg1)
    display_flags(self,0x45,v2 != 0)

# rcr => 0x46
def exec_0x46(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v2 = -(int(v2,2) % (len(v1)+1))
    if v2 == 0:
        out = v1
    else:
        v1 = v1 + str(int(self.flags['c']))
        out = v1[v2:]+v1[:v2]
        self.flags['c'] = out[-1] == '1'
        out = out[:-1]

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)

    debug(self,0x46,f'Right rotation with carry: {display_value(self,arg1_type,arg1)} (> {display_value(self,arg2_type,arg2)} = {value_display(out)}')
    display_res(self,0x46,out,arg1_type,arg1)
    display_flags(self,0x46,v2 != 0)