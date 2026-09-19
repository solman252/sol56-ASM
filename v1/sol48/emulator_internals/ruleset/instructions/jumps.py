from sol48.emulator_internals.helpers import *

# jmp => 0x60
def exec_0x60(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    return conditional_jump(self,0x60,arg1_type,arg1,None,True)

# jif => 0x61
def exec_0x61(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    flag = FLAG(int(arg1,2)).name
    return conditional_jump(self,0x61,arg2_type,arg2,
        f'Flag {flag.upper()} reads',
        self.flags[flag]
    )

# jnf => 0x62
def exec_0x62(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    flag = FLAG(int(arg1,2)).name
    return conditional_jump(self,0x62,arg2_type,arg2,
        f'Flag {flag.upper()} reads',
        not self.flags[flag]
    )

# jlt => 0x63
def exec_0x63(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    return conditional_jump(self,0x63,arg1_type,arg1,
        'a < b (signed)',
        self.flags['s'] != self.flags['o']
    )

# jle => 0x64
def exec_0x64(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    return conditional_jump(self,0x64,arg1_type,arg1,
        'a <= b (signed)',
        self.flags['z'] or (self.flags['s'] != self.flags['o'])
    )

# jgt => 0x65
def exec_0x65(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    return conditional_jump(self,0x65,arg1_type,arg1,
        'a > b (signed)',
        (not self.flags['z']) and (self.flags['s'] == self.flags['o'])
    )

# jge => 0x66
def exec_0x66(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    return conditional_jump(self,0x66,arg1_type,arg1,
        'a >= b (signed)',
        self.flags['s'] == self.flags['o']
    )

# jbe => 0x67
def exec_0x67(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    return conditional_jump(self,0x67,arg1_type,arg1,
        'a <= b (unsigned)',
        self.flags['c'] or self.flags['z']
    )

# ja => 0x68
def exec_0x68(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    return conditional_jump(self,0x68,arg1_type,arg1,
        'a > b (unsigned)',
        (not self.flags['c']) and (not self.flags['z'])
    )