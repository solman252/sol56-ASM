from sol48.emulator_internals.helpers import *

# mov => 0x10
def exec_0x10(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    conditional_move(self,0x10,arg1_type,arg1,arg2_type,arg2,None,True)

# mc => 0x11
def exec_0x11(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    conditional_move(self,0x11,arg1_type,arg1,arg2_type,arg2,
        f'Flag C reads',
        self.flags['c']
    )

# mnc => 0x12
def exec_0x12(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    conditional_move(self,0x12,arg1_type,arg1,arg2_type,arg2,
        f'Flag C reads',
        not self.flags['c']
    )

# mlt => 0x13
def exec_0x13(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    conditional_move(self,0x13,arg1_type,arg1,arg2_type,arg2,
        'a < b (signed)',
        self.flags['s'] != self.flags['o']
    )

# mle => 0x14
def exec_0x14(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    conditional_move(self,0x14,arg1_type,arg1,arg2_type,arg2,
        'a <= b (signed)',
        self.flags['z'] or (self.flags['s'] != self.flags['o'])
    )

# mgt => 0x15
def exec_0x15(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    conditional_move(self,0x15,arg1_type,arg1,arg2_type,arg2,
        'a > b (signed)',
        (not self.flags['z']) and (self.flags['s'] == self.flags['o'])
    )

# mge => 0x16
def exec_0x16(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    conditional_move(self,0x16,arg1_type,arg1,arg2_type,arg2,
        'a >= b (signed)',
        self.flags['s'] == self.flags['o']
    )

# mbe => 0x17
def exec_0x17(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    conditional_move(self,0x17,arg1_type,arg1,arg2_type,arg2,
        'a <= b (unsigned)',
        self.flags['c'] or self.flags['z']
    )

# ma => 0x18
def exec_0x18(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    conditional_move(self,0x18,arg1_type,arg1,arg2_type,arg2,
        'a > b (unsigned)',
        (not self.flags['c']) and (not self.flags['z'])
    )