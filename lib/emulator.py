from typing import Callable
import re

def bin_to_hex(bin_str: str) -> str: return hex(int(bin_str,2))[2:].upper().zfill(len(bin_str)//4)
def hex_to_bin(hex_str: str) -> str: return bin(int(hex_str,16))[2:].zfill(len(hex_str)*4)
def int_to_bin(n: int, bits: int = 1, signed: bool = False) -> str: return bin((n + (1 << bits)) % (1 << bits))[2:].zfill(bits)
def int_to_hex(v: int, bits: int = 1) -> str: return hex(v)[2:].upper().zfill(bits)

class MEM:
    def __init__(self, size: int, initial_data: str | None = None):
        if initial_data == None: initial_data = '0'*size

        if len(initial_data) > size: raise ValueError('initial_data contains more data than the storage size')
        if len(initial_data) < size: initial_data = initial_data + '0'*(size - len(initial_data))

        self.initial_data = initial_data
        self.data = initial_data
        self.size = size
    
    def read(self, index: int = 0, size: int | None = None):
        if size == None: size = self.size - index
        if index < 0 or index >= self.size: raise IndexError('data start index out of range')
        if index + size > self.size: raise IndexError('data end index out of range')
        return ''.join(self.data[index:index+size])
    
    def write(self, data: str, index: int = 0):
        if index < 0 or index >= self.size: raise IndexError('data start index out of range')
        if index + len(data) > self.size: raise IndexError('data end index out of range')
        self.data = self.data[:index] + data + self.data[index+len(data):]
    
    def reset(self):
        self.data = self.initial_data
    
    def clear(self):
        self.data = '0'*self.size

class Ruleset:
    def __init__(self, inst_depth: int, mem_depth: int, interrupt_codes: int, registers: dict[str,int], flags: list[str], video_init: Callable, video_handler: Callable, interrupt_caller: Callable, exec_handler: Callable):
        self.inst_depth = inst_depth
        self.mem_depth = mem_depth
        self.interrupt_codes = interrupt_codes
        
        self.registers: dict[str,int] = {k.strip().lower(): v for k,v in registers.items()}
        self.flags: list[str] = [flag.strip().lower() for flag in flags]

        self.instructions: dict[str,Ruleset.Instruction] = {}

        self.video_init = video_init
        self.exec_handler = exec_handler
        self.interrupt_caller = interrupt_caller
        self.video_handler = video_handler

    class Instruction:
        def __init__(self, ruleset: 'Ruleset', name: str, opcode: str):
            self.name = name.strip().lower()
            
            args = []

            match_exp = []
            for segment in opcode.split('@'):
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
                    raise ValueError(f'Unexpected segment \'{segment}\' in opcode.')
            
            self.match_exp = ''.join(match_exp)
            self.args = tuple(args)

            ruleset.instructions[self.match_exp] = self
    
    def add_rule(self, name: str, opcode: str): Ruleset.Instruction(self,name,opcode)

class CPU:
    def __init__(self, name: str, clock_speed: float, ruleset: Ruleset, debug_mode: bool = False):
        self.name = name
        self.clock_speed = clock_speed

        self.ruleset = ruleset

        self.registers: dict[str,MEM] = {reg: MEM(size) for reg,size in self.ruleset.registers.items()}
        self.flags: dict[str,bool] = {flag:False for flag in self.ruleset.flags}
        self.PRAM = MEM(pow(2,self.ruleset.mem_depth)*self.ruleset.inst_depth)
        self.RAM = MEM(pow(2,self.ruleset.mem_depth)*self.ruleset.mem_depth)
        self.ITABLE = MEM(self.ruleset.interrupt_codes*self.ruleset.mem_depth)

        self.PC = 0

        self.halted = False

        self.interrupt_queue = []

        self.istate_registers: dict[str,MEM] = {reg: MEM(size) for reg,size in self.ruleset.registers.items()}
        self.istate_flags: dict[str,MEM] = {reg: MEM(size) for reg,size in self.ruleset.registers.items()}
        self.istate_PC = 0

        self.debug_log: list[str] = []
        self.debug_mode: bool = debug_mode

        self.ruleset.video_init(self)

    def reset(self):
        for reg in self.registers.values(): reg.reset()
        for flag in self.flags.keys(): self.flags[flag] = False
        for reg in self.istate_registers.values(): reg.reset()
        for flag in self.istate_flags.keys(): self.flags[flag] = False
        self.RAM.reset()
        self.ITABLE.reset()

        self.PC = 0
        self.istate_PC = 0

        self.halted = False
        self.interrupt_queue = []

        self.debug_log: list[str] = []

        self.ruleset.video_init(self)
    
    def interrupt_logic(self):
        if len(self.interrupt_queue) == 0: return
        code = self.interrupt_queue[0]
        addr = int(self.ITABLE.read(self.ruleset.mem_depth*code,self.ruleset.mem_depth),2)
        if self.debug_mode: print(f'INTERRUPT 0x{int_to_hex(code,self.ruleset.interrupt_codes.bit_length()//4)}',end=' => ')
        if addr != 0:
            if self.debug_mode: print(f'Jumping to handler at 0x{int_to_hex(addr,self.ruleset.mem_depth)}')
            self.istate_PC = self.PC
            self.PC = addr

            for k,v in self.registers.items(): self.istate_registers[k].write(v.read())
            for k,v in self.flags.items(): self.istate_flags[k] = v
        else:
            if self.debug_mode: print('No handler set.')
            self.interrupt_queue.pop(0)
            self.interrupt_logic()
    
    def interrupt(self, code: int):
        if code < 0 or code > self.ruleset.interrupt_codes: raise ValueError('Interrupt code must be from 0-256.')
        self.interrupt_queue.append(code)

    def interrupt_return(self):
        self.PC = self.istate_PC
        self.istate_PC = 0
        if self.halted == None or self.halted == self.interrupt_queue: self.halted = False
        if self.debug_mode: print(f'Jumping back to 0x{int_to_hex(self.PC,self.ruleset.mem_depth//4)} after handling interrupt 0x{int_to_hex(self.interrupt_queue[0],self.ruleset.interrupt_codes.bit_length()//4)}.')
        self.interrupt_queue.pop(0)
    
    def clock(self):
        self.ruleset.interrupt_caller(self)

        self.interrupt_logic()

        if (self.halted == False) or len(self.interrupt_queue) != 0:

            # Fetch
            opcode = self.PRAM.read(self.ruleset.inst_depth*self.PC,self.ruleset.inst_depth)
            
            # Decode
            matches = []
            for match_exp,inst in self.ruleset.instructions.items():
                data = re.findall(match_exp,opcode)
                if data:
                    args = data[0]
                    if type(args) == str: args = tuple([args])
                    args = {key: args[index] for index,key in enumerate(inst.args)}
                    matches.append((inst.name,args))

            # Execute
            if len(matches) == 0:
                raise Exception(f'opcode \'{opcode}\' does not match any instruction for the ruleset provided.')
            if len(matches) > 1:
                raise Exception(f'opcode \'{opcode}\' matches more than one instruction for the ruleset provided.')
            self.ruleset.exec_handler(self,opcode,*matches[0])
        
        self.ruleset.video_handler(self)

__all__ = ['bin_to_hex','hex_to_bin','int_to_bin','int_to_hex','MEM','Ruleset','CPU']