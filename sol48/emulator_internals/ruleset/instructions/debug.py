from sol48.emulator_internals.helpers import *

# debug msg enable => 0xa0
def exec_0xa0(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    debug(self,0xa0,'Debug mode enabled.')

# debug msg disable => 0xa1
def exec_0xa1(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    debug(self,0xa1,'Debug mode disabled.')
    old_debug_mode = self.debug_mode
    self.debug_mode = False
    return {'Debug Closing': old_debug_mode and self._debug_whitelist[0xa1]}

# debug msg whitelist => 0xa2
def exec_0xa2(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    debug(self,0xa2,f'Opcode 0x{bin_to_hex(arg1)} added to the debug message whitelist.')
    self._debug_whitelist[int(arg1,2)] = True

# debug msg blacklist => 0xa3
def exec_0xa3(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    debug(self,0xa3,f'Opcode 0x{bin_to_hex(arg1)} added to the debug message blacklist.')
    old_whitelisted = self._debug_whitelist[0xa3]
    self._debug_whitelist[int(arg1,2)] = False
    return {'Debug Closing': self.debug_mode and old_whitelisted}

# debug msg whitelist all => 0xa4
def exec_0xa4(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    debug(self,0xa4,f'All opcodes added to the debug message whitelist.')
    self._debug_whitelist = [True]*0xFF

# debug msg blacklist all => 0xa5
def exec_0xa5(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    debug(self,0xa5,f'All Opcodes added to the debug message blacklist.')
    old_whitelisted = self._debug_whitelist[0xa5]
    self._debug_whitelist = [False]*0xFF
    return {'Debug Closing': self.debug_mode and old_whitelisted}

# debug read => 0xa6
def exec_0xa6(self: CPU, arg1_type: str, arg2_type: str, arg1: str, arg2: str):
    match ARGTYPE(int(arg1_type,2)):
        case ARGTYPE.REG: # Register
            reg = REG(int(arg1,2)).name
            debug(self,0xa6,f'Register {reg.upper()} reads: {value_display(parse_arg_value(self,arg1_type,arg1),signed=True)}')
        case ARGTYPE.IMM: # Immediate
            debug(self,0xa6,f'Passed immediate value is: {value_display(arg1,signed=True)}')
        case ARGTYPE.MEM: # Memory
            reg = REG(int(arg1,2)).name
            debug(self,0xa6,f'Memory at address found in register {reg.upper()} ({value_display(self.registers[reg].read(),hide_binary=True)}) reads: {value_display(parse_arg_value(self,arg1_type,arg1),signed=True)}')
        case ARGTYPE.ADDR: # Address
            debug(self,0xa6,f'Memory at address {value_display(arg1,hide_binary=True)} reads: {value_display(parse_arg_value(self,arg1_type,arg1),signed=True)}')
        case ARGTYPE.CODE: # Interrupt Code
            debug(self,0xa6,f'Interrupt code 0x{bin_to_hex(arg1,digits=2)} is assigned to handler at address: 0x{bin_to_hex(parse_arg_value(self,arg1_type,arg1))}')
        case ARGTYPE.PORT: # IO Port
            raise NotImplementedError
        case ARGTYPE.FLAG: # Flag
            flag = FLAG(int(arg1,2)).name
            debug(self,0xa6,f'Flag {flag.upper()} reads: {self.flags[flag]}')
        case ARGTYPE.TIME_ASPECT: # Time Aspect
            aspect = TIME_ASPECT(int(arg1,2))
            debug(self,0xa6,f'Time aspect "{aspect.name.title()}" is currently: {value_display(parse_arg_value(self,arg1_type,arg1),signed=True)}')