from sol48.emulator_internals.helpers import *

# set => 0x50
def exec_0x50(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    flag = FLAG(int(arg1,2)).name
    self.flags[flag] = True
    debug(self,0x50,f'Flag {flag.upper()} set to True.')

# clr => 0x51
def exec_0x51(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    flag = FLAG(int(arg1,2)).name
    self.flags[flag] = False
    debug(self,0x51,f'Flag {flag.upper()} cleared to False.')

# cpf => 0x52
def exec_0x51(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    source = FLAG(int(arg1,2)).name
    dest = FLAG(int(arg2,2)).name
    self.flags[dest] = self.flags[source]
    debug(self,0x52,f'Value of flag {source.upper()} ({self.flags[source]}) copied to flag {dest.upper()}.')

# cmp => 0x53
def exec_0x53(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    v1, v2 = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    v1_s, v2_s = [bin_to_signed(v) for v in [v1,v2]] ; v1_u, v2_u = [int(v,2) for v in [v1,v2]]
    res_s = v1_s - v2_s ; res_u = v1_u - v2_u
    out = signed_to_bin(res_s)

    set_flags(self,out,res_s,res_u,False,True)
    self.flags['c'] = res_u < 0

    debug(self,0x53,f'Signed subtraction: {v1_s} - {v2_s} = {f'{res_s} ({bin_to_signed(int_to_bin(res_s,self.registers['res'].size))} with overflow)' if self.flags['o'] else res_s}')
    debug(self,0x53,f'Unsigned subtraction: {v1_u} - {v2_u} = {f'{res_u} ({int(out,2)} with carry)' if self.flags['c'] else res_u}')
    display_flags(self,0x53,True,True)

# test => 0x54
def exec_0x53(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    out = bitwise_operation(*parse_arg_values(self,arg1_type,arg2_type,arg1,arg2), lambda a, b: a and b)
    set_flags(self,out)
    debug(self,0x54,f'{display_value(self,arg1_type,arg1)} & {display_value(self,arg2_type,arg2)} = {value_display(out)}')
    display_flags(self,0x54)