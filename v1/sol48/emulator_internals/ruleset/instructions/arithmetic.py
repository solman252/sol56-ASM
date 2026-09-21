from sol48.emulator_internals.helpers import *

# add => 0x20
def exec_0x20(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v1_s, v2_s = [bin_to_signed(v) for v in [v1,v2]] ; v1_u, v2_u = [int(v,2) for v in [v1,v2]]
    res_s = v1_s + v2_s ; res_u = v1_u + v2_u
    out = signed_to_bin(res_s,self.registers['res'].size)

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out,res_s,res_u,True,True)

    debug(self,0x20,f'Signed addition: {v1_s} + {v2_s} = {f'{res_s} ({bin_to_signed(int_to_bin(res_s,self.registers['res'].size))} with overflow)' if self.flags['o'] else res_s}')
    debug(self,0x20,f'Unsigned addition: {v1_u} + {v2_u} = {f'{res_u} ({int(out,2)} with carry)' if self.flags['c'] else res_u}')
    display_res(self,0x20,out,arg1_type,arg1)
    display_flags(self,0x20,True,True)

# adc => 0x21
def exec_0x21(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v1_s, v2_s = [bin_to_signed(v) for v in [v1,v2]] ; v1_u, v2_u = [int(v,2) for v in [v1,v2]]
    c = int(self.flags['c'])
    res_s = v1_s + v2_s + c ; res_u = v1_u + v2_u + c
    out = signed_to_bin(res_s,self.registers['res'].size)

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out,res_s,res_u,True,True)

    debug(self,0x21,f'Signed addition: {v1_s} + {v2_s} + {c} = {f'{res_s} ({bin_to_signed(int_to_bin(res_s,self.registers['res'].size))} with overflow)' if self.flags['o'] else res_s}')
    debug(self,0x21,f'Unsigned addition: {v1_u} + {v2_u} + {c} = {f'{res_u} ({int(out,2)} with carry)' if self.flags['c'] else res_u}')
    display_res(self,0x21,out,arg1_type,arg1)
    display_flags(self,0x21,True,True)

# sub => 0x22
def exec_0x22(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v1_s, v2_s = [bin_to_signed(v) for v in [v1,v2]] ; v1_u, v2_u = [int(v,2) for v in [v1,v2]]
    res_s = v1_s - v2_s ; res_u = v1_u - v2_u
    out = signed_to_bin(res_s,self.registers['res'].size)

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out,res_s,res_u,False,True)
    self.flags['c'] = res_u < 0

    debug(self,0x22,f'Signed subtraction: {v1_s} - {v2_s} = {f'{res_s} ({bin_to_signed(int_to_bin(res_s,self.registers['res'].size))} with overflow)' if self.flags['o'] else res_s}')
    debug(self,0x22,f'Unsigned subtraction: {v1_u} - {v2_u} = {f'{res_u} ({int(out,2)} with carry)' if self.flags['c'] else res_u}')
    display_res(self,0x22,out,arg1_type,arg1)
    display_flags(self,0x22,True,True)

# sbb => 0x23
def exec_0x23(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v1_s, v2_s = [bin_to_signed(v) for v in [v1,v2]] ; v1_u, v2_u = [int(v,2) for v in [v1,v2]]
    c = int(self.flags['c'])
    res_s = v1_s - v2_s - c ; res_u = v1_u - v2_u - c
    out = signed_to_bin(res_s,self.registers['res'].size)

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out,res_s,res_u,False,True)
    self.flags['c'] = res_u < 0

    debug(self,0x23,f'Signed subtraction: {v1_s} - {v2_s} - {c} = {f'{res_s} ({bin_to_signed(int_to_bin(res_s,self.registers['res'].size))} with overflow)' if self.flags['o'] else res_s}')
    debug(self,0x23,f'Unsigned subtraction: {v1_u} - {v2_u} - {c} = {f'{res_u} ({int(out,2)} with carry)' if self.flags['c'] else res_u}')
    display_res(self,0x23,out,arg1_type,arg1)
    display_flags(self,0x23,True,True)

# div => 0x24
def exec_0x24(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = [int(v,2) for v in parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)]
    if v2 == 0:
        debug(self,0x24,f'Unsigned division: {v1} / {v2} = UNDEFINED')
        debug(self,0x24,'Raising devision by zero exception.')
        self.interrupt(0x04)
        self.registers['a'].write(int_to_bin(self.PC,self.registers['a'].size))
        return

    res = v1 // v2
    out = int_to_bin(res,self.registers['res'].size)

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)

    debug(self,0x24,f'Unsigned division: {v1} / {v2} = {res}')
    display_res(self,0x24,out,arg1_type,arg1)
    display_flags(self,0x24)

# idiv => 0x25
def exec_0x25(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = [bin_to_signed(v) for v in parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)]
    if v2 == 0:
        debug(self,0x24,f'Unsigned division: {v1} / {v2} = UNDEFINED')
        debug(self,0x24,'Raising devision by zero exception.')
        self.interrupt(0x04)
        self.registers['a'].write(int_to_bin(self.PC,self.registers['a'].size))
        return

    res = int(v1 / v2)
    out = signed_to_bin(res)

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out,res,res,False,True)

    debug(self,0x25,f'Signed division: {v1} / {v2} = {f'{res} ({bin_to_signed(int_to_bin(res,self.registers['res'].size))} with overflow)' if self.flags['o'] else res}')
    display_res(self,0x25,out,arg1_type,arg1)
    display_flags(self,0x25,False,True)

# mul => 0x26
def exec_0x26(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = [int(v,2) for v in parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)]
    res = v1 * v2
    out = int_to_bin(res,self.registers['res'].size)

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)
    self.flags['c'] = res > 0xFFFF
    self.flags['o'] = self.flags['c']

    debug(self,0x26,f'Unsigned multiplication (low bits): {v1} * {v2} = {res}')
    display_res(self,0x26,out,arg1_type,arg1)
    display_flags(self,0x26,True,True)

# imul => 0x27
def exec_0x27(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = [bin_to_signed(v) for v in parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)]
    res = v1 * v2
    out = signed_to_bin(res,self.registers['res'].size)

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)
    self.flags['c'] = res < -0x8000 or res > 0x7FFF
    self.flags['o'] = self.flags['c']

    debug(self,0x27,f'Signed multiplication (low bits): {v1} * {v2} = {res}')
    display_res(self,0x27,out,arg1_type,arg1)
    display_flags(self,0x27,True,True)

# mulh => 0x28
def exec_0x26(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = [int(v,2) for v in parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)]
    res = v1 * v2
    out = int_to_bin(res,bits=32)[:16]

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)

    debug(self,0x28,f'Unsigned multiplication (high bits): {v1} * {v2} = {res}')
    display_res(self,0x28,out,arg1_type,arg1)
    display_flags(self,0x28)

# imulh => 0x29
def exec_0x29(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = [bin_to_signed(v) for v in parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)]
    res = v1 * v2
    out = signed_to_bin(res,bits=32)[:16]

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)

    debug(self,0x29,f'Signed multiplication (high bits): {v1} * {v2} = {res}')
    display_res(self,0x29,out,arg1_type,arg1)
    display_flags(self,0x29)

# mod => 0x2a
def exec_0x2a(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = [int(v,2) for v in parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)]
    res = v1 % v2
    out = int_to_bin(res,self.registers['res'].size)

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)

    debug(self,0x2a,f'Unsigned modulo: {v1} % {v2} = {res}')
    display_res(self,0x2a,out,arg1_type,arg1)
    display_flags(self,0x2a)

# imod => 0x2b
def exec_0x2b(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = [bin_to_signed(v) for v in parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)]
    res = v1 - ((abs(v1) // abs(v2)) * (-1 if (v1 < 0) != (v2 < 0) else 1)) * v2
    out = signed_to_bin(res)

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out)

    debug(self,0x2b,f'Signed modulo: {v1} % {v2} = {res}')
    display_res(self,0x2b,out,arg1_type,arg1)
    display_flags(self,0x2b)

# neg => 0x2c
def exec_0x2c(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v = parse_arg_value(self,arg1_type,arg1)
    v = bin_to_signed(v)
    res = v * -1
    out = signed_to_bin(res,self.registers['res'].size)

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out,res,res,False,True)

    debug(self,0x2c,f'Negation: {v} * -1 = {f'{res} ({bin_to_signed(int_to_bin(res,self.registers['res'].size))} with overflow)' if self.flags['o'] else res}')
    display_res(self,0x2c,out,arg1_type,arg1)
    display_flags(self,0x2c,False,True)

# abs => 0x2d
def exec_0x2d(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v = parse_arg_value(self,arg1_type,arg1)
    v = bin_to_signed(v)
    res = abs(v)
    out = signed_to_bin(res,self.registers['res'].size)

    write_res(self,out,arg1_type,arg1)
    set_flags(self,out,res,res,False,True)

    debug(self,0x2d,f'Absolute: abs({v}) = {f'{res} ({bin_to_signed(int_to_bin(res,self.registers['res'].size))} with overflow)' if self.flags['o'] else res}')
    display_res(self,0x2d,out,arg1_type,arg1)
    display_flags(self,0x2d,False,True)

# inc => 0x2e
def exec_0x2e(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v1_s, v2_s = [bin_to_signed(v) for v in [v1,v2]] ; v1_u, v2_u = [int(v,2) for v in [v1,v2]]
    res_s = v1_s + v2_s ; res_u = v1_u + v2_u
    out = signed_to_bin(res_s,self.registers['res'].size)

    reg = parse_arg(self,arg1_type,arg1)
    self.registers[reg].write(out)
    set_flags(self,out,res_s,res_u,True,True)

    debug(self,0x2e,f'Signed addition: {v1_s} + {v2_s} = {f'{res_s} ({bin_to_signed(int_to_bin(res_s,self.registers['res'].size))} with overflow)' if self.flags['o'] else res_s}')
    debug(self,0x2e,f'Unsigned addition: {v1_u} + {v2_u} = {f'{res_u} ({int(out,2)} with carry)' if self.flags['c'] else res_u}')
    debug(self,0x2e,f'{value_display(out,signed=True)} written to register {reg.upper()}.')
    display_flags(self,0x2e,True,True)

# dec => 0x2f
def exec_0x2f(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v1_s, v2_s = [bin_to_signed(v) for v in [v1,v2]] ; v1_u, v2_u = [int(v,2) for v in [v1,v2]]
    res_s = v1_s - v2_s ; res_u = v1_u - v2_u
    out = signed_to_bin(res_s,self.registers['res'].size)

    reg = parse_arg(self,arg1_type,arg1)
    self.registers[reg].write(out)
    set_flags(self,out,res_s,res_u,False,True)
    self.flags['c'] = res_u < 0

    debug(self,0x22,f'Signed subtraction: {v1_s} - {v2_s} = {f'{res_s} ({bin_to_signed(int_to_bin(res_s,self.registers['res'].size))} with overflow)' if self.flags['o'] else res_s}')
    debug(self,0x22,f'Unsigned subtraction: {v1_u} - {v2_u} = {f'{res_u} ({int(out,2)} with carry)' if self.flags['c'] else res_u}')
    debug(self,0x22,f'{value_display(out,signed=True)} written to register {reg.upper()}.')
    display_flags(self,0x22,True,True)