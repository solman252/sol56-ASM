
import time
import emulator_internals as internal
from lib.emulator import *
from lib.customasm import *

start_time = time.time()

def exec_handler(self: CPU, opcode: str, inst: str, args: dict[str,str]):
    #region Debug Printing
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
    #endregion Debug Printing

    #region Automatically convert args to values
    orig_args = args.copy()
    for k,v in args.copy().items():
        vk = 'v'+k[1:]
        if k[0] == 'r':
            if (vk in args and int(args[vk],2) != 0) or int(v,2) == 0: continue
            args.pop(k)
            args[vk] = self.registers[reg_keys[v]].read()
    #endregion Automatically convert args to values

    inc_pc = True

    match(inst.split(' ')[0]):

        #region Special Instructions
        case 'nop':
            if args: v = tuple(args.values())[0]; debug(f'Data 0b{v} / 0x{bin_to_hex(v)} passed in.')
        
        case 'intd':
            if args['_v'] == '0100':
                self.ITABLE.clear()
                debug(f'All interrupt handlers undefined.')
            else:
                v2 = args['v2']
                if len(v2) == 16: v2 = v2[8:]
                self.ITABLE.write(args['v1'],self.ruleset.mem_depth*int(v2,2))
                debug(f'Defined interrupt handler 0x{bin_to_hex(v2)} => 0x{bin_to_hex(args['v1'])}')
        
        case 'intr':
            variant = intr_keys[args['_v']]

            if variant in ['reg all','state', 'all']:
                debug('Restoring all registers to pre-interrupt state.')
                for k,v in self.istate_registers.items(): self.registers[k].write(v.read())
                
            if variant in ['flag all','state', 'all']:
                debug('Restoring all flags to pre-interrupt state.')
                for k,v in self.istate_flags.items(): self.flags[k] = v

            if variant == 'reg':
                r = reg_keys[args['rf']]
                debug(f'Restoring register {r} to pre-interrupt state.')
                self.registers[r].write(self.istate_registers[r].read())

            if variant == 'flag':
                f = flag_keys[args['rf']]
                debug(f'Restoring flag {f} to pre-interrupt state.')
                self.flags[f] = self.istate_flags[r]

            if variant in ['all','pc']:
                debug(end='')
                self.interrupt_return()
                inc_pc = False

        case 'int':
            code = args.get('v1')
            debug(f'Generating interrupt signal with code 0x{bin_to_hex(code)}.')
            debug('}',indent=False)
            self.PC += 1
            self.interrupt(int(code,2))
            return

        case 'hlt':
            code = args.get('v1')
            if code: self.halted = int(code,2)
            debug(f'Halting code execution until an interrupt{f' with code 0x{bin_to_hex(code)}' if code else ''} occurs.')

        case 'time':   
            t = (time.time_ns() // (10 ** 9)) -start_time
            dt = time.localtime(t+start_time)
            mode = time_keys[args.get('m','0000')]
            v = 0
            match(mode):
                case 'uptime': v = round(t-0.5)
                case 'milli-second of second':
                    if time.get_clock_info('perf_counter').resolution > 0.001:
                        self.PC += 1
                        self.interrupt(0x04)
                        return
                    v = round((t - round(t-0.5)) * 1000)
                case 'second of minute': v = dt.tm_sec
                case 'minute of hour': v = dt.tm_min
                case 'hour of day': v = dt.tm_hour
                case 'day of the week': v = dt.tm_wday
                case 'day of the month': v = dt.tm_mday
                case 'day of the year': v = dt.tm_yday
                case 'month': v = dt.tm_mon
                case 'year': v = dt.tm_year
            # self.registers[reg_keys[orig_args['r1']]].write(int_to_bin(v,self.ruleset.mem_depth))
            debug(f'Current {mode} -> {reg_keys[orig_args['r1']]}')
        #endregion Special Instructions

        #region ALU Instructions
        case 'flag':
            flag = args['f']
            v = args['v'] == '1'
            if flag == '0101':
                for flag in self.ruleset.flags: self.flags[flag] = v
                debug(f'Set all flags to {v}.')
            else:
                flag = flag_keys[flag]
                self.flags[flag] = v
                debug(f'Set flag {flag} to {v}.')
        
        case 'add':
            v1, v2, c = int(args['v1'],2), int(args['v2'],2), int(self.flags['c'])
            if self.flags['s']:
                if args['v1'][0] == '1': v1 = -(int(''.join(['0' if c == '1' else '1' for c in args['v1']]),2)+1)
                if args['v2'][0] == '1': v2 = -(int(''.join(['0' if c == '1' else '1' for c in args['v2']]),2)+1)

            out = v1+v2+(c if int(args['_v'],2) >= 0x04 else 0)
            self.flags['c'] = ((not self.flags['s']) and out >= 2**self.ruleset.mem_depth) or (self.flags['s'] and out >= 2**(self.ruleset.mem_depth-1))
            if self.flags['c']: out -= (2**(self.ruleset.mem_depth-1) if self.flags['s'] else 2**self.ruleset.mem_depth)
            self.flags['o'] = self.flags['s'] and out < -(2**(self.ruleset.mem_depth-1))
            if self.flags['o']: out += 2**(self.ruleset.mem_depth-1) + 1
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
            self.flags['c'] = ((not self.flags['s']) and out >= 2**self.ruleset.mem_depth) or (self.flags['s'] and out >= 2**(self.ruleset.mem_depth-1))
            if self.flags['c']: out -= (2**(self.ruleset.mem_depth-1) if self.flags['s'] else 2**self.ruleset.mem_depth)
            self.flags['o'] = self.flags['s'] and out < -(2**(self.ruleset.mem_depth-1))
            if self.flags['o']: out += 2**(self.ruleset.mem_depth-1) + 1
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
            if args['_v'] == '00000010': v2 = str(int(self.flags[flag_keys[args['r2']]])).zfill(self.ruleset.mem_depth)
            else: v2 = args['v2']

            if orig_args['r1'] == '0000':
                for r in self.registers.values():
                    r.write(v2[len(v2)-r.size:])
                debug(f'Set all registers values to 0x{bin_to_hex(v2)}')
            else:
                self.registers[reg_keys[orig_args['r1']]].write(v2)
                debug(f'{reg_keys[orig_args['r1']]} <- 0x{bin_to_hex(v2)}')

        case 'ldr':
            v2 = self.RAM.read(self.ruleset.mem_depth*int(args['v2'],2),self.ruleset.mem_depth)

            if orig_args['r1'] == '0000':
                for r in self.registers.keys(): self.registers[r].write(v2)
                debug(f'Set all registers values to 0x{bin_to_hex(v2)}')
            else:
                self.registers[reg_keys[orig_args['r1']]].write(v2)
                debug(f'{reg_keys[orig_args['r1']]} <- 0x{bin_to_hex(v2)}')

        case 'str':
            v2 = args['v2']
            self.RAM.write(args['v1'],self.ruleset.mem_depth*int(v2,2))
            debug(f'0x{bin_to_hex(args['v1'])} -> RAM[0x{bin_to_hex(v2)}]')
        #endregion Register / Memory Management Instructions

        #region Jumping Instructions
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
        #endregion Jumping Instructions

        #region Power Instructions
        case 'pwd': debug('Shutting down.')
        #endregion Power Instructions

        #region Video Instructions
        # TODO
        #endregion Video Instructions

    if inc_pc: self.PC += 1
    debug('}',indent=False)
    if opcode == hex_to_bin('00021FCE2A873C') and self.debug_mode:
        debug('\nDebug mode disabled.\nYou can enable debug mode by passing in 0x1FCE2A8739 to the NOP command.\n',indent=False)
        self.debug_mode = False
    if inst == 'pwd': exit()

ruleset = Ruleset(
    internal.ruleset.inst_depth,
    internal.ruleset.mem_depth,
    internal.ruleset.interrupt_codes,
    internal.ruleset.registers,
    internal.ruleset.flags,
    video_init,exec_handler,interrupt_caller,video_handler)

#region Run Emulator
cpu = CPU('x56 CPU',100,ruleset)
# WEB COMMENTED
# cpu.PRAM.write(assemble(input_file='program.asm').replace('\n',''))
with open('assembled.bin','r') as f: program_code = cpu.PRAM.write(f.read())
while True: cpu.clock()
#endregion Run Emulator

'''
TODO:

Video blitting, and text mode.

Fix ms of second time command
'''