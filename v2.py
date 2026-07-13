from typing import Callable
import re, time, pygame

def bin_to_hex(bin_str: str) -> str: return hex(int(bin_str,2))[2:].upper().zfill(len(bin_str)//4)
def hex_to_bin(hex_str: str) -> str: return bin(int(hex_str,16))[2:].zfill(len(hex_str)*4)
def int_to_bin(n: int, bits: int, signed: bool = False) -> str: return format(n % (1 << bits), f'0{bits}b') if signed else bin(n)[2:].zfill(bits)
def int_to_hex(v: int, bits: int) -> str: return hex(v)[2:].upper().zfill(bits)

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
    def __init__(self, inst_depth: int, color_depth: int, mem_depth: int, interrupt_depth: int, registers: dict[str,int], flags: list[str], exec_handler: Callable, interrupt_caller: Callable):
        self.inst_depth = inst_depth
        self.color_depth = color_depth
        self.mem_depth = mem_depth
        self.interrupt_depth = interrupt_depth
        
        self.registers: dict[str,int] = {k.strip().lower(): v for k,v in registers.items()}
        self.flags: dict[str] = [flag.strip().lower() for flag in flags]

        self.instructions: dict[str,Ruleset.Instruction] = {}
        self.exec_handler = exec_handler
        self.interrupt_caller = interrupt_caller

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
    
    def add_rule(self, name: str, args: dict[str,int] | None, opcode: str): Ruleset.Instruction(self,name,args,opcode)

class CPU:
    def __init__(self, name: str, clock_speed: float, ruleset: Ruleset, debug_mode: bool = False):
        self.name = name
        self.clock_speed = clock_speed

        self.ruleset = ruleset

        self.registers: dict[str,MEM] = {reg: MEM(size) for reg,size in self.ruleset.registers.items()}
        self.flags: dict[str,bool] = {flag:False for flag in self.ruleset.flags}
        self.PRAM = MEM(pow(2,self.ruleset.mem_depth)*self.ruleset.inst_depth)
        self.VRAM = MEM(pow(2,self.ruleset.mem_depth)*3*self.ruleset.color_depth)
        self.RAM = MEM(pow(2,self.ruleset.mem_depth)*self.ruleset.mem_depth)
        self.ITABLE = MEM(self.ruleset.interrupt_depth*self.ruleset.mem_depth)

        self.PC = 0

        self.halted = False
        self.handling_interrupt = None
        self.istate_registers: dict[str,MEM] = {reg: MEM(size) for reg,size in self.ruleset.registers.items()}
        self.istate_flags: dict[str,MEM] = {reg: MEM(size) for reg,size in self.ruleset.registers.items()}
        self.istate_PC = 0

        self.debug_log: list[str] = []
        self.debug_mode: bool = debug_mode

        self.display = pygame.display.set_mode([pow(self.ruleset.mem_depth,2)]*2)
        pygame.display.set_caption(name)
        self.pygame_clock = pygame.time.Clock()

    def reset(self):
        for reg in self.registers.values(): reg.reset()
        for flag in self.flags.keys(): self.flags[flag] = False
        for reg in self.istate_registers.values(): reg.reset()
        for flag in self.istate_flags.keys(): self.flags[flag] = False
        self.VRAM.reset()
        self.RAM.reset()
        self.ITABLE.reset()

        self.PC = 0
        self.istate_PC = 0

        self.halted = False
        self.handling_interrupt = None

        self.debug_log: list[str] = []
    
    def interrupt(self, code: int):
        if code < 0 or code > self.ruleset.interrupt_depth: raise ValueError('Interrupt code must be from 0-256.')
        if self.debug_mode: print(f'\nINTERRUPT 0x{int_to_hex(code,(self.ruleset.interrupt_depth-1)//4)}')
        self.istate_PC = self.PC
        self.PC = int(self.ITABLE.read(self.ruleset.mem_depth*code,self.ruleset.mem_depth),2)

        for k,v in self.registers.items():
            self.istate_registers[k].write(v.read())
            v.reset()
        for k,v in self.flags.items():
            self.istate_flags[k] = v
            self.flags[k] = False

        self.handling_interrupt = code

        if self.PC == 0:
            if self.debug_mode: print('No handler set.')
            self.interrupt_return()
            
        if self.debug_mode: print()
    
    def interrupt_return(self):
        for k,v in self.istate_registers.items(): self.registers[k].write(v.read())
        for k,v in self.istate_flags.items(): self.flags[k] = v
        self.PC = self.istate_PC
        self.istate_PC = 0
        if self.halted == None or self.halted == self.handling_interrupt: self.halted = False
        if self.debug_mode: print(f'Jumping back to 0x{int_to_hex(self.PC,self.ruleset.mem_depth//4)} after handling interrupt 0x{int_to_hex(self.handling_interrupt,(self.ruleset.interrupt_depth-1)//4)}.')
        self.handling_interrupt = None
    
    def clock(self):
        self.ruleset.interrupt_caller(self)

        if (self.halted == False) or self.handling_interrupt != None:

            # Fetch
            opcode = self.PRAM.read(self.ruleset.inst_depth*self.PC,self.ruleset.inst_depth)
            
            # Decode
            # TODO: match arg to key not to index
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
            self.ruleset.exec_handler(self,opcode,*matches[0])
        
        pygame.display.flip()
        self.pygame_clock.tick(self.clock_speed)

if __name__ == '__main__':
    def interrupt_caller(self: CPU):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.interrupt(0x01)

            elif event.type == pygame.KEYDOWN:
                self.interrupt(0x02)
                self.registers['a'].write(int_to_bin(event.key,self.registers['a'].size))

            elif event.type == pygame.KEYUP:
                self.interrupt(0x03)
                self.registers['a'].write(int_to_bin(event.key,self.registers['a'].size))

    def exec_handler(self: CPU, opcode: str, inst: str, args: dict[str,str]):
        reg_keys = {
            '0001':'a',
            '0010':'b',
            '0011':'c',
            '0100':'d',
            '0101':'res',
            '0110':'vid_r',
            '0111':'vid_g',
            '1000':'vid_b',
            '1001':'vid_addr',
        }
        flag_keys = {
            '0000':'s',
            '0001':'c',
            '0010':'z',
            '0011':'n',
            '0100':'o',
        }

        inc_pc = True

        debug_count = 0
        def debug(*values, sep=' ', end='\n', indent=True):
            nonlocal debug_count
            if self.debug_mode: print(('\n' if indent and debug_count == 0 else '')+('    ' if indent else '')+sep.join([str(v) for v in values]),end=end)
            self.debug_log.append(sep.join([str(v) for v in values])+end)
            if indent: debug_count += 1
        
        if opcode == hex_to_bin('00021FCE2A8739') and not self.debug_mode:
            self.debug_mode = True
            debug('Debug mode enabled.\nYou can disable debug mode by passing in 0x1FCE2A873C to the NOP command.\n',indent=False)

        debug(f'0x{int_to_hex(self.PC,self.ruleset.mem_depth//4)}: {inst} {args} => {{',end='',indent=False)

        orig_args = args.copy()
        for k,v in args.copy().items():
            vk = 'v'+k[1:]
            if k[0] == 'r':
                if (vk in args and int(args[vk],2) != 0) or int(v,2) == 0: continue
                args.pop(k)
                args[vk] = self.registers[reg_keys[v]].read()

        match(inst.split(' ')[0]):

            #region Special Instructions
            case 'nop':
                if args: debug(f'Data \'{tuple(args.values())[0]}\' passed in.')
            
            case 'itd':
                v2 = args['v2']
                if len(v2) == 16: v2 = v2[8:]
                self.ITABLE.write(args['v1'],self.ruleset.mem_depth*int(v2,2))
                debug(f'0x{bin_to_hex(args['v1'])} -> ITABLE[0x{bin_to_hex(v2)}]')
            
            case 'itr':
                debug(end='')
                self.interrupt_return()
                inc_pc = False

            case 'hlt':
                code = args.get('v1')
                if code: self.halted = int(code,2)
                debug(f'Halting code execution until an interrupt{f' with code 0x{bin_to_hex(code)}' if code else ''} occurs.')

            case 'int':
                code = args.get('v1')
                debug(f'Generating interrupt signal with code 0x{bin_to_hex(code)}.')
                debug('}',indent=False)
                self.PC += 1
                self.interrupt(int(code,2))
                return
            #endregion Special Instructions

            #region ALU Instructions
            case 'flag':
                flag = flag_keys[args['f']]
                v = args['v'] == '1'
                self.flags[flag] = v
                debug(f'Setting flag {flag} to {v}.')
            
            case 'add':
                v1, v2, c = int(args['v1'],2), int(args['v2'],2), int(self.flags['c'])
                if self.flags['s']: 
                    if args['v1'][0] == '1': v1 = -(int(''.join(['0' if c == '1' else '1' for c in args['v1']]),2)+1)
                    if args['v2'][0] == '1': v2 = -(int(''.join(['0' if c == '1' else '1' for c in args['v2']]),2)+1)

                out = v1+v2+c
                self.flags['c'] = ((not self.flags['s']) and out >= pow(2,self.ruleset.mem_depth)) or (self.flags['s'] and out >= pow(2,self.ruleset.mem_depth-1))
                if self.flags['c']: out -= (pow(2,self.ruleset.mem_depth-1) if self.flags['s'] else pow(2,self.ruleset.mem_depth))
                self.flags['o'] = self.flags['s'] and out < -pow(2,self.ruleset.mem_depth-1)
                if self.flags['o']: out += pow(2,self.ruleset.mem_depth-1)+1
                self.flags['n'] = out < 0
                self.flags['z'] = out == 0

                self.registers['res'].write(int_to_bin(out,self.ruleset.mem_depth,self.flags['s']))

                debug(f'In {'' if self.flags['s'] else 'un'}signed mode:')
                debug(f'{v1} + {v2} + {c} = {out}')
                debug('New flags: (')
                for f in 'czno':
                    debug(f'  {f} = {self.flags[f]}')
                debug(')')
 
            case 'sub':
                v1, v2 = int(args['v1'],2), int(args['v2'],2)
                if self.flags['s']: 
                    if args['v1'][0] == '1': v1 = -(int(''.join(['0' if c == '1' else '1' for c in args['v1']]),2)+1)
                    if args['v2'][0] == '1': v2 = -(int(''.join(['0' if c == '1' else '1' for c in args['v2']]),2)+1)

                out = v1-v2
                self.flags['c'] = ((not self.flags['s']) and out >= pow(2,self.ruleset.mem_depth)) or (self.flags['s'] and out >= pow(2,self.ruleset.mem_depth-1))
                if self.flags['c']: out -= (pow(2,self.ruleset.mem_depth-1) if self.flags['s'] else pow(2,self.ruleset.mem_depth))
                self.flags['o'] = self.flags['s'] and out < -pow(2,self.ruleset.mem_depth-1)
                if self.flags['o']: out += pow(2,self.ruleset.mem_depth-1)+1
                self.flags['n'] = out < 0
                self.flags['z'] = out == 0

                self.registers['res'].write(int_to_bin(out,self.ruleset.mem_depth,self.flags['s']))

                debug(f'In {'' if self.flags['s'] else 'un'}signed mode:')
                debug(f'{v1} - {v2} = {out}')
                debug('New flags: (')
                for f in 'czno':
                    debug(f'  {f} = {self.flags[f]}')
                debug(')')
 
            case 'and':
                v1, v2 = args['v1'], args['v2']
                out = ''.join(['1' if (v1[i] == '1') and (v2[i] == '1') else '0' for i in range(len(v1))])
                self.registers['res'].write(out)
                debug(f'0b{v1} & 0b{v2} = 0b{out}')
                self.flags['z'] = int(out,2) == 0
                self.flags['n'] = self.flags['s'] and -(int(''.join(['0' if c == '1' else '1' for c in out]),2)+1) if out[0] == '1' else int(out,2) < 0
                debug('New flags: (')
                for f in 'zn':
                    debug(f'  {f} = {self.flags[f]}')
                debug(')')
 
            case 'or':
                v1, v2 = args['v1'], args['v2']
                out = ''.join(['1' if (v1[i] == '1') or (v2[i] == '1') else '0' for i in range(len(v1))])
                self.registers['res'].write(out)
                debug(f'0b{v1} | 0b{v2} = 0b{out}')
                self.flags['z'] = int(out,2) == 0
                self.flags['n'] = self.flags['s'] and -(int(''.join(['0' if c == '1' else '1' for c in out]),2)+1) if out[0] == '1' else int(out,2) < 0
                debug('New flags: (')
                for f in 'zn':
                    debug(f'  {f} = {self.flags[f]}')
                debug(')')
 
            case 'xor':
                v1, v2 = args['v1'], args['v2']
                out = ''.join(['1' if (v1[i] == '1') ^ (v2[i] == '1') else '0' for i in range(len(v1))])
                self.registers['res'].write(out)
                debug(f'0b{v1} ^ 0b{v2} = 0b{out}')
                self.flags['z'] = int(out,2) == 0
                self.flags['n'] = self.flags['s'] and -(int(''.join(['0' if c == '1' else '1' for c in out]),2)+1) if out[0] == '1' else int(out,2) < 0
                debug('New flags: (')
                for f in 'zn':
                    debug(f'  {f} = {self.flags[f]}')
                debug(')')
 
            case 'xnor':
                v1, v2 = args['v1'], args['v2']
                out = ''.join(['0' if (v1[i] == '1') ^ (v2[i] == '1') else '1' for i in range(len(v1))])
                self.registers['res'].write(out)
                debug(f'~(0b{v1} ^ 0b{v2}) = 0b{out}')
                self.flags['z'] = int(out,2) == 0
                self.flags['n'] = self.flags['s'] and -(int(''.join(['0' if c == '1' else '1' for c in out]),2)+1) if out[0] == '1' else int(out,2) < 0
                debug('New flags: (')
                for f in 'zn':
                    debug(f'  {f} = {self.flags[f]}')
                debug(')')
 
            case 'bsl':
                v1, v2 = args['v1'], int(args['v2'],2)
                out = v1[:self.ruleset.mem_depth-min(v2,self.ruleset.mem_depth)].ljust(self.ruleset.mem_depth,'0')
                self.registers['res'].write(out)
                debug(f'0b{v1} << {v2} = 0b{out}')
                self.flags['z'] = int(out,2) == 0
                self.flags['n'] = self.flags['s'] and -(int(''.join(['0' if c == '1' else '1' for c in out]),2)+1) if out[0] == '1' else int(out,2) < 0
                debug('New flags: (')
                for f in 'zn':
                    debug(f'  {f} = {self.flags[f]}')
                debug(')')
 
            case 'bsr':
                v1, v2 = args['v1'], int(args['v2'],2)
                out = v1[min(v2,self.ruleset.mem_depth):].zfill(self.ruleset.mem_depth)
                self.registers['res'].write(out)
                debug(f'0b{v1} >> {v2} = 0b{out}')
                self.flags['z'] = int(out,2) == 0
                self.flags['n'] = self.flags['s'] and -(int(''.join(['0' if c == '1' else '1' for c in out]),2)+1) if out[0] == '1' else int(out,2) < 0
                debug('New flags: (')
                for f in 'zn':
                    debug(f'  {f} = {self.flags[f]}')
                debug(')')
 
            case 'brl':
                v1, v2 = args['v1'], int(args['v2'],2) % self.ruleset.mem_depth
                out = v1[v2:]+v1[:v2]
                self.registers['res'].write(out)
                debug(f'0b{v1} <) {int(args['v2'],2)} = 0b{out}')
                self.flags['z'] = int(out,2) == 0
                self.flags['n'] = self.flags['s'] and -(int(''.join(['0' if c == '1' else '1' for c in out]),2)+1) if out[0] == '1' else int(out,2) < 0
                debug('New flags: (')
                for f in 'zn':
                    debug(f'  {f} = {self.flags[f]}')
                debug(')')

            case 'brr':
                v1, v2 = args['v1'], int(args['v2'],2) % self.ruleset.mem_depth
                out = v1[self.ruleset.mem_depth-v2:]+v1[:self.ruleset.mem_depth-v2]
                self.registers['res'].write(out)
                debug(f'0b{v1} (> {int(args['v2'],2)} = 0b{out}')
                self.flags['z'] = int(out,2) == 0
                self.flags['n'] = self.flags['s'] and -(int(''.join(['0' if c == '1' else '1' for c in out]),2)+1) if out[0] == '1' else int(out,2) < 0
                debug('New flags: (')
                for f in 'zn':
                    debug(f'  {f} = {self.flags[f]}')
                debug(')')
            #endregion ALU Instructions

            #region Register / Memory Management Instructions
            case 'mov':
                if args['_v'] == '00000010': v2 = str(int(self.flags[flag_keys[args['f_r1']]])).zfill(self.ruleset.mem_depth)
                else: v2 = args['v2']

                self.registers[reg_keys[orig_args['f_r1']]].write(v2)
                debug(f'{reg_keys[orig_args['f_r1']]} <- 0x{bin_to_hex(v2)}')

            case 'ldr':
                v2 = self.RAM.read(self.ruleset.mem_depth*int(args['v2'],2),self.ruleset.mem_depth)
                self.registers[reg_keys[orig_args['r1']]].write(v2)
                debug(f'{reg_keys[orig_args['r1']]} <- 0x{bin_to_hex(v2)}')

            case 'str':
                v2 = args['v2']
                self.RAM.write(args['v1'],self.ruleset.mem_depth*int(v2,2))
                debug(f'0x{bin_to_hex(args['v1'])} -> RAM[0x{bin_to_hex(v2)}]')
            #endregion Register / Memory Management Instructions

            #region Video Instructions
            # TODO
            #endregion Video Instructions

            #region Branching Instructions
            case 'jmp':
                v1 = int(args['v1'],2)
                self.PC = v1
                inc_pc = False
                debug(f'Jumping to 0x{int_to_hex(v1,(self.ruleset.mem_depth-1)//4)}.')

            case 'jif':
                v1 = int(args['v1'],2)
                f = self.flags[flag_keys[args['f']]]
                if f:
                    self.PC = v1
                    inc_pc = False
                debug(f'{'J' if f else 'Not j'}umping to 0x{int_to_hex(v1,(self.ruleset.mem_depth-1)//4)}. ({flag_keys[args['f']]} = {f})')

            case 'jnot':
                v1 = int(args['v1'],2)
                f = self.flags[flag_keys[args['f']]]
                if not f:
                    self.PC = v1
                    inc_pc = False
                debug(f'{'Not j' if f else 'J'}umping to 0x{int_to_hex(v1,(self.ruleset.mem_depth-1)//4)}. ({flag_keys[args['f']]} = {f})')

            case 'jeq':
                r1, r2, addr = reg_keys[orig_args['r1']], reg_keys[orig_args['r2']], int(orig_args['v1'],2)
                j = self.registers[r1].read() == self.registers[r2].read()
                if j:
                    self.PC = addr
                    inc_pc = False
                debug(f'{'J' if j else 'Not j'}umping to 0x{int_to_hex(addr,(self.ruleset.mem_depth-1)//4)}. ({r1} {'=' if j else '!'}= {r2})')
            
            case 'jeqz':
                r1, addr = reg_keys[orig_args['r1']], int(orig_args['v1'],2)
                j = int(self.registers[r1].read(),2) == 0
                if j:
                    self.PC = addr
                    inc_pc = False
                debug(f'{'J' if j else 'Not j'}umping to 0x{int_to_hex(addr,(self.ruleset.mem_depth-1)//4)}. ({r1} {'=' if j else '!'}= 0)')

            case 'jlt':
                r1, r2, addr = reg_keys[orig_args['r1']], reg_keys[orig_args['r2']], int(orig_args['v1'],2)
                v1, v2 = self.registers[r1].read(), self.registers[r2].read()
                v1 = -(int(''.join(['0' if c == '1' else '1' for c in v1]),2)+1) if self.flags['s'] and v1[0] == '1' else int(v1,2)
                v2 = -(int(''.join(['0' if c == '1' else '1' for c in v2]),2)+1) if self.flags['s'] and v2[0] == '1' else int(v2,2)
                j = v1 < v2
                if j:
                    self.PC = addr
                    inc_pc = False
                debug(f'{'J' if j else 'Not j'}umping to 0x{int_to_hex(addr,(self.ruleset.mem_depth-1)//4)}. ({r1} {'<' if j else '>='} {r2})')
            
            case 'jltz':
                r1, addr = reg_keys[orig_args['r1']], int(orig_args['v1'],2)
                j = self.flags['s'] and self.registers[r1].read()[0] == '1'
                if j:
                    self.PC = addr
                    inc_pc = False
                debug(f'{'J' if j else 'Not j'}umping to 0x{int_to_hex(addr,(self.ruleset.mem_depth-1)//4)}. ({r1} {'<' if j else '>='} 0)')

            case 'jgt':
                r1, r2, addr = reg_keys[orig_args['r1']], reg_keys[orig_args['r2']], int(orig_args['v1'],2)
                v1, v2 = self.registers[r1].read(), self.registers[r2].read()
                v1 = -(int(''.join(['0' if c == '1' else '1' for c in v1]),2)+1) if self.flags['s'] and v1[0] == '1' else int(v1,2)
                v2 = -(int(''.join(['0' if c == '1' else '1' for c in v2]),2)+1) if self.flags['s'] and v2[0] == '1' else int(v2,2)
                j = v1 > v2
                if j:
                    self.PC = addr
                    inc_pc = False
                debug(f'{'J' if j else 'Not j'}umping to 0x{int_to_hex(addr,(self.ruleset.mem_depth-1)//4)}. ({r1} {'>' if j else '<='} {r2})')
            
            case 'jgtz':
                r1, addr = reg_keys[orig_args['r1']], int(orig_args['v1'],2)
                v1 = self.registers[r1].read()
                v1 = -(int(''.join(['0' if c == '1' else '1' for c in v1]),2)+1) if self.flags['s'] and v1[0] == '1' else int(v1,2)
                j = v1 > 0
                if j:
                    self.PC = addr
                    inc_pc = False
                debug(f'{'J' if j else 'Not j'}umping to 0x{int_to_hex(addr,(self.ruleset.mem_depth-1)//4)}. ({r1} {'>' if j else '<='} 0)')

            case 'jle':
                r1, r2, addr = reg_keys[orig_args['r1']], reg_keys[orig_args['r2']], int(orig_args['v1'],2)
                v1, v2 = self.registers[r1].read(), self.registers[r2].read()
                v1 = -(int(''.join(['0' if c == '1' else '1' for c in v1]),2)+1) if self.flags['s'] and v1[0] == '1' else int(v1,2)
                v2 = -(int(''.join(['0' if c == '1' else '1' for c in v2]),2)+1) if self.flags['s'] and v2[0] == '1' else int(v2,2)
                j = v1 <= v2
                if j:
                    self.PC = addr
                    inc_pc = False
                debug(f'{'J' if j else 'Not j'}umping to 0x{int_to_hex(addr,(self.ruleset.mem_depth-1)//4)}. ({r1} {'<=' if j else '<>'} {r2})')
            
            case 'jlez':
                r1, addr = reg_keys[orig_args['r1']], int(orig_args['v1'],2)
                v1 = self.registers[r1].read()
                v1 = -(int(''.join(['0' if c == '1' else '1' for c in v1]),2)+1) if self.flags['s'] and v1[0] == '1' else int(v1,2)
                j = v1 <= 0
                if j:
                    self.PC = addr
                    inc_pc = False
                debug(f'{'J' if j else 'Not j'}umping to 0x{int_to_hex(addr,(self.ruleset.mem_depth-1)//4)}. ({r1} {'<=' if j else '>'} 0)')

            case 'jge':
                r1, r2, addr = reg_keys[orig_args['r1']], reg_keys[orig_args['r2']], int(orig_args['v1'],2)
                v1, v2 = self.registers[r1].read(), self.registers[r2].read()
                v1 = -(int(''.join(['0' if c == '1' else '1' for c in v1]),2)+1) if self.flags['s'] and v1[0] == '1' else int(v1,2)
                v2 = -(int(''.join(['0' if c == '1' else '1' for c in v2]),2)+1) if self.flags['s'] and v2[0] == '1' else int(v2,2)
                j = v1 >= v2
                if j:
                    self.PC = addr
                    inc_pc = False
                debug(f'{'J' if j else 'Not j'}umping to 0x{int_to_hex(addr,(self.ruleset.mem_depth-1)//4)}. ({r1} {'>=' if j else '<'} {r2})')
            
            case 'jgez':
                r1, addr = reg_keys[orig_args['r1']], int(orig_args['v1'],2)
                v1 = self.registers[r1].read()
                v1 = -(int(''.join(['0' if c == '1' else '1' for c in v1]),2)+1) if self.flags['s'] and v1[0] == '1' else int(v1,2)
                j = v1 >= 0
                if j:
                    self.PC = addr
                    inc_pc = False
                debug(f'{'J' if j else 'Not j'}umping to 0x{int_to_hex(addr,(self.ruleset.mem_depth-1)//4)}. ({r1} {'>=' if j else '<'} 0)')
            #endregion Branching Instructions

            #region Power Instructions
            case 'pwd': debug('Shutting down.')
            #endregion Power Instructions

        if inc_pc: self.PC += 1
        debug('}',indent=False)
        if opcode == hex_to_bin('00021FCE2A873C') and self.debug_mode:
            debug('\nDebug mode disabled.\nYou can enable debug mode by passing in 0x1FCE2A8739 to the NOP command.\n',indent=False)
            self.debug_mode = False
        if inst == 'pwd': exit()

    from customasm import *
    program_code = assemble(input_file='program.asm').replace('\n','')

    ruleset = Ruleset(56,8,16,256,{'a':16,'b':16,'c':16,'d':16,'res':16,'vid_r':8,'vid_g':8,'vid_b':8,'vid_addr':16},['s','c','z','n','o'],exec_handler,interrupt_caller)
    #region Ruleset Instruction Defs

    #region Special Instructions
    ruleset.add_rule('nop',{},'0x00 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')
    ruleset.add_rule('nop r1',{'r1':4},'0x00 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
    ruleset.add_rule('nop v1',{'v1':40},'0x00 @ 0x02 @ v1`40')

    ruleset.add_rule('intd',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x01 @ _v @ r1 @ r2 @ v1 @ v2')

    ruleset.add_rule('intr',{},'0x02 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

    ruleset.add_rule('hlt',{'_v':8,'r1':4,'v1':16},'0x03 @ _v @ r1 @ 0x0 @ v1 @ 0x0000')

    ruleset.add_rule('int',{'_v':8,'r1':4,'v1':16},'0x04 @ _v @ r1 @ 0x0 @ v1 @ 0x0000')
    #endregion Special Instructions

    #region ALU Instructions
    ruleset.add_rule('flag',{'f':4,'v':1},'0x05 @ f @ 0b000 @ v`1 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

    ruleset.add_rule('add',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x06 @ _v @ r1 @ r2 @ v1 @ v2')

    ruleset.add_rule('sub',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x07 @ _v @ r1 @ r2 @ v1 @ v2')

    ruleset.add_rule('and',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x08 @ _v @ r1 @ r2 @ v1 @ v2')

    ruleset.add_rule('or',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x09 @ _v @ r1 @ r2 @ v1 @ v2')

    ruleset.add_rule('xor',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x0A @ _v @ r1 @ r2 @ v1 @ v2')

    ruleset.add_rule('xnor',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x0B @ _v @ r1 @ r2 @ v1 @ v2')

    ruleset.add_rule('bsl',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x0C @ _v @ r1 @ r2 @ v1 @ v2')

    ruleset.add_rule('bsr',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x0D @ _v @ r1 @ r2 @ v1 @ v2')

    ruleset.add_rule('brl',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x0E @ _v @ r1 @ r2 @ v1 @ v2')

    ruleset.add_rule('brr',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x0F @ _v @ r1 @ r2 @ v1 @ v2')
    #endregion ALU Instructions

    #region Register / Memory Management Instructions
    ruleset.add_rule('mov',{'_v':8,'f_r1':4,'r2':4,'v2':16},'0x10 @ _v @ f_r1 @ r2 @ 0x0000 @ v2')

    ruleset.add_rule('ldr',{'_v':8,'r1':4,'r2':4,'v2':16},'0x11 @ _v @ r1 @ r2 @ 0x0000 @ v2')

    ruleset.add_rule('str',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x12 @ _v @ r1 @ r2 @ v1 @ v2')
    #endregion Register / Memory Management Instructions

    #region Branching Instructions
    ruleset.add_rule('jmp',{'_v':8,'r1':4,'v1':16},'0x13 @ _v @ r1 @ 0x0 @ v1 @ 0x0000')
    ruleset.add_rule('jif',{'_v':4,'f':4,'r1':4,'v1':16},'0x14 @ _v @ f @ r1 @ 0x0 @ v1 @ 0x0000')
    ruleset.add_rule('jnot',{'_v':4,'f':4,'r1':4,'v1':16},'0x15 @ _v @ f @ r1 @ 0x0 @ v1 @ 0x0000')
    ruleset.add_rule('jeq',{'r1':4,'r2':4,'v1':16},'0x16 @ 0x00 @ r1 @ r2 @ v1 @ 0x0000')
    ruleset.add_rule('jeqz',{'r1':4,'v1':16},'0x16 @ 0x01 @ r1 @ 0x0 @ v1 @ 0x0000')
    ruleset.add_rule('jlt',{'r1':4,'r2':4,'v1':16},'0x17 @ 0x00 @ r1 @ r2 @ v1 @ 0x0000')
    ruleset.add_rule('jltz',{'r1':4,'v1':16},'0x17 @ 0x01 @ r1 @ 0x0 @ v1 @ 0x0000')
    ruleset.add_rule('jgt',{'r1':4,'r2':4,'v1':16},'0x18 @ 0x00 @ r1 @ r2 @ v1 @ 0x0000')
    ruleset.add_rule('jgtz',{'r1':4,'v1':16},'0x18 @ 0x01 @ r1 @ 0x0 @ v1 @ 0x0000')
    ruleset.add_rule('jle',{'r1':4,'r2':4,'v1':16},'0x19 @ 0x00 @ r1 @ r2 @ v1 @ 0x0000')
    ruleset.add_rule('jlez',{'r1':4,'v1':16},'0x19 @ 0x01 @ r1 @ 0x0 @ v1 @ 0x0000')
    ruleset.add_rule('jge',{'r1':4,'r2':4,'v1':16},'0x1A @ 0x00 @ r1 @ r2 @ v1 @ 0x0000')
    ruleset.add_rule('jgez',{'r1':4,'v1':16},'0x1A @ 0x01 @ r1 @ 0x0 @ v1 @ 0x0000')
    #endregion Branching Instructions

    #region Power Instructions
    ruleset.add_rule('pwd',{},'0x18 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')
    #endregion Power Instructions

    #region Video Instructions
    # TODO
    #endregion Video Instructions

    #endregion Ruleset Instruction Defs

    cpu = CPU('x56 CPU',100,ruleset)
    cpu.PRAM.write(program_code)
    while True: cpu.clock()