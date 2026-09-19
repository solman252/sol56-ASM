from typing import Callable
import re

def bin_to_hex(bin_str: str) -> str: return hex(int(bin_str,2))[2:].upper().zfill(len(bin_str)//4)
def hex_to_bin(hex_str: str) -> str: return bin(int(hex_str,16))[2:].zfill(len(hex_str)*4)
def int_to_bin(n: int, bits: int = 1, signed: bool = False) -> str: return bin((n + (1 << bits)) % (1 << bits))[2:].zfill(bits)
def int_to_hex(v: int, bits: int = 1) -> str: return hex(v)[2:].upper().zfill(bits//4)

class MEM:
    def __init__(self, size: int, initial_data: str | None = None):
        if initial_data is None: initial_data = '0'*size

        if len(initial_data) > size: raise ValueError('initial_data contains more data than the storage size')
        if len(initial_data) < size: initial_data = initial_data + '0'*(size - len(initial_data))

        self.initial_data = initial_data
        self.data = initial_data
        self.size = size
    
    def read(self, index: int = 0, size: int | None = None):
        if size is None: size = self.size - index
        if index < 0 or index >= self.size:
            try: self.ruleset.exception_handler(self,'Memory Read Invalid Start Index',mem=self,index=index,size=size)
            except NotImplementedError: raise IndexError('data start index out of range')
        if index + size > self.size: 
            try: self.ruleset.exception_handler(self,'Memory Read Invalid End Index',mem=self,index=index,size=size)
            except NotImplementedError: raise IndexError('data end index out of range')
        return ''.join(self.data[index:index+size])
    
    def write(self, data: str, index: int = 0):
        if index < 0 or index >= self.size: 
            try: self.ruleset.exception_handler(self,'Memory Write Invalid Start Index',mem=self,index=index,data=data)
            except NotImplementedError: raise IndexError('data start index out of range')
        if index + len(data) > self.size: 
            try: self.ruleset.exception_handler(self,'Memory Write Invalid End Index',mem=self,index=index,data=data)
            except NotImplementedError: raise IndexError('data end index out of range')
        self.data = self.data[:index] + data + self.data[index+len(data):]
    
    def reset(self):
        self.data = self.initial_data
    
    def clear(self):
        self.data = '0'*self.size

class Ruleset:
    def __init__(self, inst_depth: int, mem_depth: int, interrupt_codes: int, registers: dict[str,int], flags: list[str], video_init: Callable, video_handler: Callable, interrupt_caller: Callable, exception_handler: Callable, exception_codes: list[int], on_interrupt_enter: Callable, on_interrupt_exit: Callable, exec_handler: Callable, cpu_setup: Callable):
        self.inst_depth = inst_depth
        self.mem_depth = mem_depth
        self.interrupt_codes = interrupt_codes
        
        self.registers: dict[str,int] = {k.strip().lower(): v for k,v in registers.items()}
        self.flags: list[str] = [flag.strip().lower() for flag in flags]

        self.instructions: dict[str,Ruleset.Instruction] = {}

        self.video_init = video_init
        self.exec_handler = exec_handler
        self.interrupt_caller = interrupt_caller
        self.exception_handler = exception_handler
        self.exception_codes = exception_codes
        self.on_interrupt_enter = on_interrupt_enter
        self.on_interrupt_exit = on_interrupt_exit
        self.video_handler = video_handler
        self.cpu_setup = cpu_setup

    class Instruction:
        def __init__(self, ruleset: 'Ruleset', name: str, inst_binary: str):
            self.name = name.strip().lower()
            
            args = []

            match_exp = []
            for segment in inst_binary.split('@'):
                segment = segment.strip()

                if segment.startswith('0b'):
                    match_exp.append(segment[2:])
                elif segment.startswith('0x'):
                    match_exp.append(hex_to_bin(segment[2:]))
                elif '`' in segment:
                    key,size = segment.split('`')
                    match_exp.append(f'([01]{{{size}}})')
                    args.append(key)
                else:
                    raise ValueError(f'Unexpected segment \'{segment}\' in instruction binary.')
            
            self.match_exp = ''.join(match_exp)
            self.args = tuple(args)

            ruleset.instructions[self.match_exp] = self
    
    def add_rule(self, name: str, inst_binary: str): Ruleset.Instruction(self,name,inst_binary)

class CPU:
    def __init__(self, name: str, clock_speed: float, ruleset: Ruleset, debug_mode: bool = False):
        self.name = name
        self.clock_speed = clock_speed

        self.ruleset = ruleset

        self.registers: dict[str,MEM] = {reg: MEM(size) for reg,size in self.ruleset.registers.items()}
        self.flags: dict[str,bool] = {flag:False for flag in self.ruleset.flags}
        self.RAM = MEM(pow(2,self.ruleset.mem_depth)*self.ruleset.mem_depth)
        self.ITABLE = MEM(self.ruleset.interrupt_codes*self.ruleset.mem_depth)

        self.PC = 0

        self.halted = False

        self.interrupt_queue = []
        self.handling_interrupt = False
        self.istate_PC = 0

        self.debug_log: list[str] = []
        self.debug_mode: bool = debug_mode

        self.ruleset.cpu_setup(self)
        self.ruleset.video_init(self)

    def reset(self):
        for reg in self.registers.values(): reg.reset()
        for flag in self.flags.keys(): self.flags[flag] = False
        self.RAM.reset()
        self.ITABLE.reset()

        self.PC = 0
        self.istate_PC = 0

        self.halted = False
        self.interrupt_queue = []
        self.handling_interrupt = False

        self.debug_log: list[str] = []

        self.ruleset.cpu_setup(self)
        self.ruleset.video_init(self)
    
    def interrupt_logic(self):
        if len(self.interrupt_queue) == 0 or self.handling_interrupt: return
        self.handling_interrupt = True
        code = self.interrupt_queue[0]
        addr = int(self.ITABLE.read(self.ruleset.mem_depth*code,self.ruleset.mem_depth),2)
        self.istate_PC = self.PC
        if self.debug_mode and code not in self.ruleset.exception_codes: print(f'INTERRUPT 0x{int_to_hex(code,self.ruleset.interrupt_codes.bit_length())}',end=' => ')
        if addr != 0:
            if self.debug_mode: print(f'Jumping to handler at 0x{int_to_hex(addr,self.ruleset.mem_depth)}')
            self.PC = addr

            self.ruleset.on_interrupt_enter(self,code)
        else:
            self.PC = self.istate_PC
            self.istate_PC = 0
            if self.halted == code or self.halted is True: self.halted = False
            if self.debug_mode: print('No handler set.')
            self.interrupt_queue.pop(0)
            self.handling_interrupt = False
            self.interrupt_logic()
    
    def interrupt(self, code: int):
        if code < 0 or code > self.ruleset.interrupt_codes:
            try: self.ruleset.exception_handler(self,'Invalid Interrupt Code',code=code)
            except NotImplementedError: raise ValueError(f'Interrupt code must be from 0-{self.ruleset.interrupt_codes-1}.')
        self.interrupt_queue.append(code)

    def interrupt_return(self,*args,**kwargs):
        self.PC = self.istate_PC
        self.istate_PC = 0
        code = self.interrupt_queue.pop(0)
        if self.halted == code or self.halted is True: self.halted = False
        if self.debug_mode: print(f'    Jumping back to 0x{int_to_hex(self.PC,self.ruleset.mem_depth)} after handling interrupt 0x{int_to_hex(code,self.ruleset.interrupt_codes.bit_length())}.')
        self.handling_interrupt = False
        self.ruleset.on_interrupt_exit(self,code,*args,**kwargs)
    
    def clock(self):
        self.ruleset.interrupt_caller(self)

        self.interrupt_logic()

        if self.halted is False or len(self.interrupt_queue) > 0:

            # Fetch
            # inst_binary = self.PRAM.read(self.ruleset.inst_depth*self.PC,self.ruleset.inst_depth)
            inst_binary = self.RAM.read(self.ruleset.mem_depth*self.PC,self.ruleset.mem_depth*self.ruleset.inst_depth)
            
            # Decode
            matches = []
            for match_exp,inst in self.ruleset.instructions.items():
                data = re.findall(match_exp,inst_binary)
                if data:
                    args = data[0]
                    if type(args) == str: args = tuple([args])
                    args = {key: args[index] for index,key in enumerate(inst.args)}
                    matches.append((inst.name,args))

            # Execute
            if len(matches) == 0:
                try: self.ruleset.exception_handler(self,'No Instruction Matches',inst_binary=inst_binary)
                except NotImplementedError: raise Exception(f'Instruction binary 0b{inst_binary} does not match any instruction for the ruleset provided.')  
                matches.append((None,dict()))
            elif len(matches) > 1:
                try: self.ruleset.exception_handler(self,'Multiple Instruction Matches',inst_binary=inst_binary)
                except NotImplementedError: raise Exception(f'Instruction binary 0b{inst_binary} matches more than one instruction for the ruleset provided.')

            self.ruleset.exec_handler(self,inst_binary,*matches[0])
        
        self.ruleset.video_handler(self)

__all__ = ['MEM','Ruleset','CPU']