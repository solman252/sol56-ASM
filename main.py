from typing import Callable
import re, time, pygame

def bin_to_hex(bin_str: str) -> str: return hex(int(bin_str,2))[2:].zfill(len(bin_str)//4)
def hex_to_bin(hex_str: str) -> str: return bin(int(hex_str,16))[2:].zfill(len(hex_str)*4)
def int_to_bin(v: int, l: int) -> str: return bin(v)[2:].zfill(l)
def int_to_hex(v: int, l: int) -> str: return hex(v)[2:].zfill(l)

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
    def __init__(self, inst_size: int, registers: dict[str,int] | None = None):
        self.inst_size = inst_size
        
        self.registers = {k.strip().lower(): v for k,v in registers.items()} if registers is not None else {}

        self.instructions: dict[str,Ruleset.Instruction] = {}

    class Instruction:
        def __init__(self, ruleset: 'Ruleset', name: str, args: dict[str,int] | None, opcode: str):
            self.name = name.strip().lower()
            self.args = {arg.strip().lower(): size for arg,size in args.items()} if args is not None else {}
            
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
                elif segment in self.args.keys():
                    match_exp.append(f'([01]{{{self.args[segment]}}})')
                else:
                    raise ValueError(f'Unexpected segment \'{segment}\' in opcode.')
            
            self.match_exp = ''.join(match_exp)

            ruleset.instructions[self.match_exp] = self
    
    def add_rule(self, name: str, args: dict[str,int] | None, opcode: str):
        Ruleset.Instruction(self,name,args,opcode)

class CPU:
    def __init__(self, name: str, screen_size: tuple[int,int], screen_fps: int, ruleset: Ruleset, execute_func: Callable, RAM: MEM, flags: list[str] | None = None, debug_mode: bool = False):
        self.name = name
        self.screen_size = screen_size
        self.screen_fps = screen_fps

        self.ruleset = ruleset

        self.execute_func = execute_func

        self.registers: dict[str,MEM] = {reg: MEM(size) for reg,size in self.ruleset.registers.items()}
        self.flags: dict[str,bool] = {flag.strip().lower():False for flag in flags} if flags is not None else {}

        self.RAM = RAM

        self.PC = 0

        self.debug_log: list[str] = []
        self.debug_mode: bool = debug_mode

        self.display = pygame.display.set_mode(screen_size)
        self.VRAM = pygame.Surface(screen_size,pygame.SRCALPHA)
        pygame.display.set_caption(name)
        self.pygame_clock = pygame.time.Clock()

        self.asleep = False
        self.sleep_time = 0

        self.keyboard_queue = []

    def reset(self):
        self.RAM.reset()
        for reg in self.registers.values(): reg.reset()
        for flag in self.flags.keys(): self.flags[flag] = False

        self.PC = 0
    
    def clock(self):
        self.pygame_clock.tick(self.screen_fps)

        if self.asleep:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F12:
                    self.asleep = False
                    result = self.execute_func(self,'0 (Custom)','wake',{'sleeptime':time.time()-self.sleep_time})
                    self.sleep_time = 0

            pygame.display.flip()
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT: exit()
            if event.type in [pygame.KEYDOWN,pygame.KEYUP]: self.keyboard_queue.append((event.key,event.type))

        # Fetch
        opcode = self.RAM.read(self.ruleset.inst_size*self.PC,self.ruleset.inst_size)
        
        # Decode
        matches = []
        for match_exp,inst in self.ruleset.instructions.items():
            data = re.findall(match_exp,opcode)
            if data:
                args = data[0]
                if type(args) == str: args = tuple([args])
                args = {key: args[index] for index,key in enumerate(inst.args.keys())}
                matches.append((inst.name,args))

        # Execute
        if len(matches) == 0:
            raise Exception(f'opcode \'{opcode}\' does not match any instruction for the ruleset provided.')
        if len(matches) > 1:
            raise Exception(f'opcode \'{opcode}\' matches more than one instruction for the ruleset provided.')
        self.execute_func(self,opcode,*matches[0])
        
        pygame.display.flip()

ruleset = Ruleset(56,{'a':16,'b':16,'c':16,'d':16,'res':16,'vid_r':8,'vid_g':8,'vid_b':8,'vid_addr':16})

#region Ruleset Rules

#region Special Instructions

# No operation, does nothing this cycle.
# nop => 0x00 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
ruleset.add_rule('nop',{},'0x00 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

# Halt CPU execution until an interrupt signal is received.
# Argument may be used to differentiate which halt is occuring. Purely for debugging purposes.
# hlt {r1: reg} => 0x01 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000
ruleset.add_rule('hlt r1',{'r1':4},'0x01 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
# hlt {v1: u16} => 0x01 @ 0x01 @ 0x0 @ 0x0 @ v1`16 @ 0x0000
ruleset.add_rule('hlt v1',{'v1':16},'0x01 @ 0x01 @ 0x0 @ 0x0 @ v1`16 @ 0x0000')

#endregion Special Instructions

#region ALU Operations

# Set signed vs unsigned mode on ALU
# sign u => 0x02 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; ALU uses interprets values as unsigned.
ruleset.add_rule('sign u',{},'0x02 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')
# sign s => 0x02 @ 0x01 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; ALU uses interprets values as signed.
ruleset.add_rule('sign s',{},'0x02 @ 0x01 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

# Set carry in for ALU
# carry 0 => 0x02 @ 0x02 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
ruleset.add_rule('carry 0',{},'0x02 @ 0x02 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')
# carry 1 => 0x02 @ 0x03 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
ruleset.add_rule('carry 1',{},'0x02 @ 0x03 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

# Set flags
# flag z 0 => 0x02 @ 0x04 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
ruleset.add_rule('flag z 0',{},'0x02 @ 0x04 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')
# flag z 1 => 0x02 @ 0x05 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
ruleset.add_rule('flag z 1',{},'0x02 @ 0x05 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

# flag n 0 => 0x02 @ 0x06 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
ruleset.add_rule('flag n 0',{},'0x02 @ 0x06 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')
# flag n 1 => 0x02 @ 0x07 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
ruleset.add_rule('flag n 1',{},'0x02 @ 0x07 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

# flag o 0 => 0x02 @ 0x08 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
ruleset.add_rule('flag o 0',{},'0x02 @ 0x08 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')
# flag o 1 => 0x02 @ 0x09 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
ruleset.add_rule('flag o 1',{},'0x02 @ 0x09 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

# For all ALU operations:
# Result is written to res,
# FLAG_S will determine if in signed mode or not,
# FLAG_C acts as carry in,
# FLAG_Z will show whether the result == 0,
# FLAG_N will show whether the result is negative (if in signed mode),
# FLAG_O will show whether an overflow occurred,

# Add 2 values together.
# If ALU is in unsigned mode, FLAG_C will show whether a carry occured.
# If ALU is in signed mode, FLAG_O will show whether a overflow occured.
# add {r1: reg}, {r2: reg} => 0x03 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} + {r2}
ruleset.add_rule('add r1 r2',{'r1':4,'r2':4},'0x03 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000')
# add {r1: reg}, {v2: u16} => 0x03 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2`16 ; res <- {r1} + v2
ruleset.add_rule('add r1 v2',{'r1':4,'v2':16},'0x03 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2`16')
# add {v1: u16}, {r2: reg} => 0x03 @ 0x02 @ 0x0 @ r2`16 @ v1`16 @ 0x0000 ; res <- v1 + {r2}
ruleset.add_rule('add v1 r2',{'v1':16,'r2':4},'0x03 @ 0x02 @ 0x0 @ r2`16 @ v1`16 @ 0x0000')
# add {v1: u16}, {v2: u16} => 0x03 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 + v2
ruleset.add_rule('add v1 v2',{'v1':16,'v2':16},'0x03 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16')

# Subtract one value from another.
# If ALU is in unsigned mode, FLAG_C will show whether a carry occured.
# If ALU is in signed mode, FLAG_O will show whether a overflow occured.
# sub {r1: reg}, {r2: reg} => 0x04 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} - {r2}
ruleset.add_rule('sub r1 r2',{'r1':4,'r2':4},'0x04 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000')
# sub {r1: reg}, {v2: u16} => 0x04 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} - v2
ruleset.add_rule('sub r1 v2',{'r1':4,'v2':16},'0x04 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2')
# sub {v1: u16}, {r2: reg} => 0x04 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 - {r2}
ruleset.add_rule('sub v1 r2',{'v1':16,'r2':4},'0x04 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000')
# sub {v1: u16}, {v2: u16} => 0x04 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 - v2
ruleset.add_rule('sub v1 v2',{'v1':16,'v2':16},'0x04 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16')

# Perform a bitwise and between 2 values.
# and {r1: reg}, {r2: reg} => 0x05 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} & {r2}
ruleset.add_rule('and r1 r2',{'r1':4,'r2':4},'0x05 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000')
# and {r1: reg}, {v2: u16} => 0x05 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} & v2
ruleset.add_rule('and r1 v2',{'r1':4,'v2':16},'0x05 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2')
# and {v1: u16}, {r2: reg} => 0x05 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 & {r2}
ruleset.add_rule('and v1 r2',{'v1':16,'r2':4},'0x05 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000')
# and {v1: u16}, {v2: u16} => 0x05 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 & v2
ruleset.add_rule('and v1 v2',{'v1':16,'v2':16},'0x05 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16')

# Perform a bitwise or between 2 values.
# or {r1: reg}, {r2: reg} => 0x06 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} | {r2}
ruleset.add_rule('or r1 r2',{'r1':4,'r2':4},'0x06 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000')
# or {r1: reg}, {v2: u16} => 0x06 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} | v2
ruleset.add_rule('or r1 v2',{'r1':4,'v2':16},'0x06 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2')
# or {v1: u16}, {r2: reg} => 0x06 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 | {r2}
ruleset.add_rule('or v1 r2',{'v1':16,'r2':4},'0x06 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000')
# or {v1: u16}, {v2: u16} => 0x06 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 | v2
ruleset.add_rule('or v1 v2',{'v1':16,'v2':16},'0x06 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16')

# Perform a bitwise xor between 2 values.
# xor {r1: reg}, {r2: reg} => 0x07 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} ^ {r2}
ruleset.add_rule('xor r1 r2',{'r1':4,'r2':4},'0x07 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000')
# xor {r1: reg}, {v2: u16} => 0x07 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} ^ v2
ruleset.add_rule('xor r1 v2',{'r1':4,'v2':16},'0x07 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2')
# xor {v1: u16}, {r2: reg} => 0x07 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 ^ {r2}
ruleset.add_rule('xor v1 r2',{'v1':16,'r2':4},'0x07 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000')
# xor {v1: u16}, {v2: u16} => 0x07 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 ^ v2
ruleset.add_rule('xor v1 v2',{'v1':16,'v2':16},'0x07 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16')

# Perform a bitwise xnor between values from 2 registers.
# xnor {r1: reg}, {r2: reg} => 0x08 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- ~({r1} ^ {r2})
ruleset.add_rule('xnor r1 r2',{'r1':4,'r2':4},'0x08 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000')
# xnor {r1: reg}, {v2: u16} => 0x08 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- ~({r1} ^ v2)
ruleset.add_rule('xnor r1 v2',{'r1':4,'v2':16},'0x08 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2')
# xnor {v1: u16}, {r2: reg} => 0x08 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- ~(v1 ^ {r2})
ruleset.add_rule('xnor v1 r2',{'v1':16,'r2':4},'0x08 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000')
# xnor {v1: u16}, {v2: u16} => 0x08 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- ~(v1 ^ v2)
ruleset.add_rule('xnor v1 v2',{'v1':16,'v2':16},'0x08 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16')

# Bit-shift a value by another value to the left.
# bsl {r1: reg}, {r2: reg} => 0x09 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} << {r2}
ruleset.add_rule('bsl r1 r2',{'r1':4,'r2':4},'0x09 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000')
# bsl {r1: reg}, {v2: u16} => 0x09 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} << v2
ruleset.add_rule('bsl r1 v2',{'r1':4,'v2':16},'0x09 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2')
# bsl {v1: u16}, {r2: reg} => 0x09 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 << {r2}
ruleset.add_rule('bsl v1 r2',{'v1':16,'r2':4},'0x09 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000')
# bsl {v1: u16}, {v2: u16} => 0x09 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 << v2
ruleset.add_rule('bsl v1 v2',{'v1':16,'v2':16},'0x09 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16')

# Bit-shift a value by another value to the right.
# bsr {r1: reg}, {r2: reg} => 0x0A @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} >> {r2}
ruleset.add_rule('bsr r1 r2',{'r1':4,'r2':4},'0x0A @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000')
# bsr {r1: reg}, {v2: u16} => 0x0A @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} >> v2
ruleset.add_rule('bsr r1 v2',{'r1':4,'v2':16},'0x0A @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2')
# bsr {v1: u16}, {r2: reg} => 0x0A @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 >> {r2}
ruleset.add_rule('bsr v1 r2',{'v1':16,'r2':4},'0x0A @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000')
# bsr {v1: u16}, {v2: u16} => 0x0A @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 >> v2
ruleset.add_rule('bsr v1 v2',{'v1':16,'v2':16},'0x0A @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16')

# Bit-rotate a value by another value to the left.
# brl {r1: reg}, {r2: reg} => 0x0B @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} <) {r2}
ruleset.add_rule('brl r1 r2',{'r1':4,'r2':4},'0x0B @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000')
# brl {r1: reg}, {v2: u16} => 0x0B @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} <) v2
ruleset.add_rule('brl r1 v2',{'r1':4,'v2':16},'0x0B @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2')
# brl {v1: u16}, {r2: reg} => 0x0B @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 <) {r2}
ruleset.add_rule('brl v1 r2',{'v1':16,'r2':4},'0x0B @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000')
# brl {v1: u16}, {v2: u16} => 0x0B @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 <) v2
ruleset.add_rule('brl v1 v2',{'v1':16,'v2':16},'0x0B @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16')

# Bit-rotate a value by another value to the right.
# brr {r1: reg}, {r2: reg} => 0x0C @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} (> {r2}
ruleset.add_rule('brr r1 r2',{'r1':4,'r2':4},'0x0C @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000')
# brr {r1: reg}, {v2: u16} => 0x0C @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} (> v2
ruleset.add_rule('brr r1 v2',{'r1':4,'v2':16},'0x0C @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2')
# brr {v1: u16}, {r2: reg} => 0x0C @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 (> {r2}
ruleset.add_rule('brr v1 r2',{'v1':16,'r2':4},'0x0C @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000')
# brr {v1: u16}, {v2: u16} => 0x0C @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 (> v2
ruleset.add_rule('brr v1 v2',{'v1':16,'v2':16},'0x0C @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16')

#endregion ALU Operations

#region Register / Memory Management

# Copy the right value into the left register.
# mov {r1: reg}, {r2: reg} => 0x0D @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; r1 <- {r2}
ruleset.add_rule('mov r1 r2',{'r1':4,'r2':4},'0x0D @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000')
# mov {r1: reg}, {v2: u16} => 0x0D @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; r1 <- v2
ruleset.add_rule('mov r1 v2',{'r1':4,'v2':16},'0x0D @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2')

# Copy the value in RAM at the right address into the left register.
# ldr {r1: reg}, [{r2: reg}] => 0x0E @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; r1 <- RAM[{r2}]
ruleset.add_rule('ldr r1 r2',{'r1':4,'r2':4},'0x0E @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000')
# ldr {r1: reg}, [{v2: u16}] => 0x0E @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; r1 <- RAM[v2]
ruleset.add_rule('ldr r1 v2',{'r1':4,'v2':16},'0x0E @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2')

# Store the left value into RAM at the right address.
# str {r1: reg}, [{r2: reg}] => 0x0F @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; {r1} -> RAM[{r2}]
ruleset.add_rule('str r1 r2',{'r1':4,'r2':4},'0x0F @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000')
# str {r1: reg}, [{v2: u16}] => 0x0F @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; {r1} -> RAM[v2]
ruleset.add_rule('str r1 v2',{'r1':4,'v2':16},'0x0F @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2')
# str {v1: u16}, [{r2: reg}] => 0x0F @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; v1 -> RAM[{r2}]
ruleset.add_rule('str v1 r2',{'v1':16,'r2':4},'0x0F @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000')
# str {v1: u16}, [{v2: u16}] => 0x0F @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; v1 -> RAM[v2]
ruleset.add_rule('str v1 v2',{'v1':16,'v2':16},'0x0F @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16')

#endregion Register / Memory Management

#region Screen Instructions

# Write to the framebuffer at address {vid_addr} with color (vid_r,vid_g,vid_b)
# vwr => 0x10 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Screen.framebuffer[vid_addr] <- (vid_r,vid_g,vid_b)
ruleset.add_rule('vwr',{},'0x10 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

# Clear the framebuffer.
# vcl => 0x11 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Screen.framebuffer[0:] <- (0,0,0)
ruleset.add_rule('vcl',{},'0x11 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

# Flush framebuffer to the screen.
# vfl => 0x12 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Screen[0:] <- Screen.framebuffer[0:]
ruleset.add_rule('vfl',{},'0x12 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

#endregion Screen Instructions

#region Branch Instructions

# jmp {r1: reg} => 0x13 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; PC <- {r1}
ruleset.add_rule('jmp r1',{'r1': 4},'0x13 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
# jmp {v1: u16} => 0x13 @ 0x01 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; PC <- v1
ruleset.add_rule('jmp v1',{'v1':16},'0x13 @ 0x01 @ 0x0 @ 0x0 @ v1`16 @ 0x0000')

# bif s {r1: reg} => 0x14 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if s: PC <- {r1}
ruleset.add_rule('bif s r1',{'r1': 4},'0x14 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
# bif s {v1: u16} => 0x14 @ 0x01 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if s: PC <- v1
ruleset.add_rule('bif s v1',{'v1':16},'0x14 @ 0x01 @ 0x0 @ 0x0 @ v1`16 @ 0x0000')

# bif c {r1: reg} => 0x14 @ 0x02 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if c: PC <- {r1}
ruleset.add_rule('bif c r1',{'r1': 4},'0x14 @ 0x02 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
# bif c {v1: u16} => 0x14 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if c: PC <- v1
ruleset.add_rule('bif c v1',{'v1':16},'0x14 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ 0x0000')

# bif z {r1: reg} => 0x14 @ 0x04 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if z: PC <- {r1}
ruleset.add_rule('bif z r1',{'r1': 4},'0x14 @ 0x04 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
# bif z {v1: u16} => 0x14 @ 0x05 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if z: PC <- v1
ruleset.add_rule('bif z v1',{'v1':16},'0x14 @ 0x05 @ 0x0 @ 0x0 @ v1`16 @ 0x0000')

# bif n {r1: reg} => 0x14 @ 0x06 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if n: PC <- {r1}
ruleset.add_rule('bif n r1',{'r1': 4},'0x14 @ 0x06 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
# bif n {v1: u16} => 0x14 @ 0x07 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if n: PC <- v1
ruleset.add_rule('bif n v1',{'v1':16},'0x14 @ 0x07 @ 0x0 @ 0x0 @ v1`16 @ 0x0000')

# bif o {r1: reg} => 0x14 @ 0x08 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if o: PC <- {r1}
ruleset.add_rule('bif o r1',{'r1': 4},'0x14 @ 0x08 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
# bif o {v1: u16} => 0x14 @ 0x09 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if o: PC <- v1
ruleset.add_rule('bif o v1',{'v1':16},'0x14 @ 0x09 @ 0x0 @ 0x0 @ v1`16 @ 0x0000')


# bnot s {r1: reg} => 0x15 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if s: PC <- {r1}
ruleset.add_rule('bnot s r1',{'r1': 4},'0x15 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
# bnot s {v1: u16} => 0x15 @ 0x01 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if s: PC <- v1
ruleset.add_rule('bnot s v1',{'v1':16},'0x15 @ 0x01 @ 0x0 @ 0x0 @ v1`16 @ 0x0000')

# bnot c {r1: reg} => 0x15 @ 0x02 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if c: PC <- {r1}
ruleset.add_rule('bnot c r1',{'r1': 4},'0x15 @ 0x02 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
# bnot c {v1: u16} => 0x15 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if c: PC <- v1
ruleset.add_rule('bnot c v1',{'v1':16},'0x15 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ 0x0000')

# bnot z {r1: reg} => 0x15 @ 0x04 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if z: PC <- {r1}
ruleset.add_rule('bnot z r1',{'r1': 4},'0x15 @ 0x04 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
# bnot z {v1: u16} => 0x15 @ 0x05 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if z: PC <- v1
ruleset.add_rule('bnot z v1',{'v1':16},'0x15 @ 0x05 @ 0x0 @ 0x0 @ v1`16 @ 0x0000')

# bnot n {r1: reg} => 0x15 @ 0x06 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if n: PC <- {r1}
ruleset.add_rule('bnot n r1',{'r1': 4},'0x15 @ 0x06 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
# bnot n {v1: u16} => 0x15 @ 0x07 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if n: PC <- v1
ruleset.add_rule('bnot n v1',{'v1':16},'0x15 @ 0x07 @ 0x0 @ 0x0 @ v1`16 @ 0x0000')

# bnot o {r1: reg} => 0x15 @ 0x08 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if o: PC <- {r1}
ruleset.add_rule('bnot o r1',{'r1': 4},'0x15 @ 0x08 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
# bnot o {v1: u16} => 0x15 @ 0x09 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if o: PC <- v1
ruleset.add_rule('bnot o v1',{'v1':16},'0x15 @ 0x09 @ 0x0 @ 0x0 @ v1`16 @ 0x0000')

#endregion Branch Instructions

#region Keyboard Instructions

# kp {r1: reg} => 0x16 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; r1 <- KEYBOARD_QUEUE.pop()
ruleset.add_rule('kp',{'r1': 4},'0x16 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000')

# kl {r1: reg} => 0x17 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; r1 <- KEYBOARD_QUEUE.length
ruleset.add_rule('kl',{'r1': 4},'0x17 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000')

# kcl => 0x18 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Clear KEYBOARD_QUEUE.
ruleset.add_rule('kcl',{},'0x18 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

#endregion Keyboard Instructions

#region Power Instructions

# pwd => 0x19 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Shut off the power.
ruleset.add_rule('pwd',{},'0x19 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

# slp => 0x1A @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Enter sleep mode.
ruleset.add_rule('slp',{},'0x1A @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

#endregion Power Instructions

#endregion Ruleset Rules

def cpu_exec(self: CPU, opcode: str, inst: str, args: dict[str,str]):
    #region Setup
    reg_keys = {
        '0001':'a',
        '0010':'b',
        '0011':'c',
        '0100':'d',
        '0101':'res',
        '0110':'vid_r',
        '0111':'vid_g',
        '1000':'vid_b',
        '1001':'vid_addr'
    }

    branched = False

    debug_count = 0
    def debug(*values, sep=' ', end='\n', indent=True):
        nonlocal debug_count
        if self.debug_mode: print(('\n' if indent and debug_count == 0 else '')+('    ' if indent else '')+sep.join([str(v) for v in values]),end=end)
        self.debug_log.append(sep.join([str(v) for v in values])+end)
        if indent: debug_count += 1

    debug(f'{str(self.PC).zfill(5)} => 0b{opcode} => {inst} {args} => {{',end='',indent=False)

    def read_reg(key: str): return self.registers[reg_keys[args[key]]].read()

    def get_args() -> list[str]:
        out = []
        for k,v in args.items():
            if k[0] == 'r':
                out.append(read_reg(k))
            elif k[0] == 'v':
                out.append(v)
        return out

    variant_data = inst.split(' ')[1:]
    if len(variant_data) == 1: variant_data = variant_data[0]

    highest_val = pow(2,self.registers['res'].size)

    #endregion Setup
    match(inst.split(' ')[0]):
        #region Special Instructions

        case 'nop': pass

        case 'hlt':
            # if variant_data == 'r1':
            #     val = bin_to_hex(read_reg('r1'))
            # elif variant_data == 'v1':
            #     val = bin_to_hex(args['v1'])
            debug(f'Halting code execution.')
            # debug(f'Interrupt handler for interrupt code 0x{val}')

        #endregion Special Instructions
        
        #region ALU Operations

        case 'sign':
            val = variant_data == 's'
            self.flags['s'] = val
            debug(f'ALU sign mode set to {'' if val else 'un'}signed.')

        case 'carry':
            val = variant_data == '1'
            self.flags['c'] = val
            debug(f'Carry flag set to {int(val)}.')

        case 'flag':
            val = variant_data[1] == '1'
            self.flags[variant_data[0]] = val
            debug(f'{ {'z':'Zero','n':'Negative','o':'Overflow'}[variant_data[0]] } flag set to {int(val)}.')

        case 'add':
            v1,v2 = get_args()
            s = int(self.flags['s'])
            # add stuff for signed mode
            c = int(self.flags['c'])
            out = v1+v2+c
            co = out >= highest_val
            if co:
                out -= highest_val
                self.flags['o' if self.flags['s'] else 'c'] = True
            self.registers['res'].write(int_to_bin(out,self.registers['res'].size))

            debug(f'{v1} + {v2} + {c} = {out}')
            if co: debug(('Overflow' if self.flags['s'] else 'Carry')+' has occured.')
            debug()
            debug(f'res = {out}')
            if co:debug(f'flag_{'o' if self.flags['s'] else 'c'} = 1')
        
        case 'and':
            v1,v2 = get_args()
            out = ''.join([str(int((v1[i] == '1') & (v2[i] == '1'))) for i in range(len(v1))])
            self.registers['res'].write(out)
            debug(f'{v1} & {v2} = {out}')
            debug(f'res = {out}')
        
        case 'or':
            v1,v2 = get_args()
            out = ''.join([str(int((v1[i] == '1') | (v2[i] == '1'))) for i in range(len(v1))])
            self.registers['res'].write(out)
            debug(f'{v1} | {v2} = {out}')
            debug(f'res = {out}')
        
        case 'xor':
            v1,v2 = get_args()
            out = ''.join([str(int((v1[i] == '1') ^ (v2[i] == '1'))) for i in range(len(v1))])
            self.registers['res'].write(out)
            debug(f'{v1} ^ {v2} = {out}')
            debug(f'res = {out}')
        
        case 'xnor':
            v1,v2 = get_args()
            out = ''.join([str(int(not ((v1[i] == '1') ^ (v2[i] == '1')))) for i in range(len(v1))])
            self.registers['res'].write(out)
            debug(f'~({v1} ^ {v2}) = {out}')
            debug(f'res = {out}')
        
        case 'bsl':
            v1,v2 = get_args()
            v2 = int(v2,2)
            out = v1[min(v2,len(v1)):].ljust(len(v1),'0')
            self.registers['res'].write(out)
            debug(f'{v1} << {v2}) = {out}')
            debug(f'res = {out}')
        
        case 'bsr':
            v1,v2 = get_args()
            v2 = int(v2,2)
            out = v1[:len(v1)-min(v2,len(v1))].rjust(len(v1),'0')
            self.registers['res'].write(out)
            debug(f'{v1} >> {v2}) = {out}')
            debug(f'res = {out}')
        
        case 'brl':
            v1,v2 = get_args()
            v2 = int(v2,2)
            out = v1[v2%len(v1):]+v1[:v2%len(v1)]
            self.registers['res'].write(out)
            debug(f'{v1} <) {v2}) = {out}')
            debug(f'res = {out}')
        
        case 'brr':
            v1,v2 = get_args()
            v2 = int(v2,2)
            out = v1[len(v1)-(v2%len(v1)):]+v1[:len(v1)-v2%len(v1)]
            self.registers['res'].write(out)
            debug(f'{v1} (> {v2}) = {out}')
            debug(f'res = {out}')
                
        #endregion ALU Operations

        #region Register / Memory Management

        case 'mov':
            r1 = reg_keys[args['r1']]
            v2 = get_args()[1]

            self.registers[r1].write(v2)

            debug(f'{r1} <- {v2}')

        case 'ldr':
            r1 = reg_keys[args['r1']]
            v2 = get_args()[1]

            out = self.RAM.read(self.ruleset.inst_size*(int(v2,2)+1)-self.registers[r1].size,self.registers[r1].size)

            self.registers[r1].write(out)

            debug(f'{r1} <- RAM[{v2}] (0b{out})')

        case 'str':
            v1,v2 = get_args()

            self.RAM.write(v1,self.ruleset.inst_size*(int(v2,2)+1)-len(v1))

            debug(f'{v1} -> RAM[{v2}]')

        #endregion Register / Memory Management

    if not branched: self.PC += 1

    debug('}',indent=False)
    
    if inst == 'pwd': exit()

if __name__ == '__main__':
    from customasm import *
    program_code = assemble(input_file='program.asm').replace('\n','')
    cpu = CPU('Sol\'s CPU Emulator',(256,256),60,ruleset,cpu_exec,MEM(56*65536,program_code),['s','c','z','n','o'],True)
    while True: cpu.clock()