from sol48.emulator_internals.helpers import *

# hlt => 0x70
def exec_0x70(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    code = parse_arg_value(self,arg1_type,arg1)
    debug(self,0x70,f'Halting execution until an interrupt{f' with code 0x{int_to_hex(code,digits=2)}'} occurs.')
    self.halted = True if code == 0 else code

# int => 0x71
def exec_0x71(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    code = parse_arg_value(self,arg1_type,arg1)
    debug(self,0x71,f'Sending an interrupt signal with code 0x{int_to_hex(code,digits=2)}...')
    self.interrupt(code)

# intd => 0x72
def exec_0x72(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    code, addr = parse_arg_values(self,arg1_type,arg2_type,arg1,arg2)
    debug(self,0x72,f'Setting handler address for interrupt signal with code 0x{int_to_hex(code,digits=2)} to {value_display(arg2_type,True)}.')
    self.ITABLE.write(addr,self.ruleset.mem_depth*code)

# ires => 0x73
def exec_0x73(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    debug(self,0x73,f'Returning from the current interrupt handler and restoring flags...')
    self.interrupt_return(reset_flags=True)
    return {'INC PC': False}

# iret => 0x74
def exec_0x74(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    debug(self,0x74,f'Returning from the current interrupt handler...')
    self.interrupt_return(reset_flags=False)
    return {'INC PC': False}