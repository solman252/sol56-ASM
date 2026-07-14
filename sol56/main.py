import pygame, time
from lib.emulator import *
from lib.customasm import *

#region Translators

start_time = time.time()

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

time_keys = {
    '0000':'uptime',
    '0001':'milli-second of second',
    '0010':'second of minute',
    '0011':'minute of hour',
    '0100':'hour of day',
    '0101':'day of the week',
    '0110':'day of the month',
    '0111':'day of the year',
    '1000':'month',
    '1001':'year',
}

intr_keys = {
    '00000000': 'all',
    '00010000': 'pc',
    '00100000': 'reg',
    '00100001': 'reg all',
    '00110000': 'flag',
    '00110001': 'flag all',
    '01000000': 'state',
}

keycodes = {k: i+1 for i,k in enumerate([
    pygame.K_a,             # 0x0001
    pygame.K_b,             # 0x0002
    pygame.K_c,             # 0x0003
    pygame.K_d,             # 0x0004
    pygame.K_e,             # 0x0005
    pygame.K_f,             # 0x0006
    pygame.K_g,             # 0x0007
    pygame.K_h,             # 0x0008
    pygame.K_i,             # 0x0009
    pygame.K_j,             # 0x000A
    pygame.K_k,             # 0x000B
    pygame.K_l,             # 0x000C
    pygame.K_m,             # 0x000D
    pygame.K_n,             # 0x000E
    pygame.K_o,             # 0x000F
    pygame.K_p,             # 0x0010
    pygame.K_q,             # 0x0011
    pygame.K_r,             # 0x0012
    pygame.K_s,             # 0x0013 
    pygame.K_t,             # 0x0014
    pygame.K_u,             # 0x0015
    pygame.K_v,             # 0x0016
    pygame.K_w,             # 0x0017
    pygame.K_x,             # 0x0018
    pygame.K_y,             # 0x0019
    pygame.K_z,             # 0x001A
    pygame.K_0,             # 0x001B
    pygame.K_1,             # 0x001C
    pygame.K_2,             # 0x001D
    pygame.K_3,             # 0x001E
    pygame.K_4,             # 0x001F
    pygame.K_5,             # 0x0020
    pygame.K_6,             # 0x0021
    pygame.K_7,             # 0x0022
    pygame.K_8,             # 0x0023
    pygame.K_9,             # 0x0024
    pygame.K_KP0,           # 0x0025
    pygame.K_KP1,           # 0x0026
    pygame.K_KP2,           # 0x0027
    pygame.K_KP3,           # 0x0028
    pygame.K_KP4,           # 0x0029
    pygame.K_KP5,           # 0x002A
    pygame.K_KP6,           # 0x002B
    pygame.K_KP7,           # 0x002C
    pygame.K_KP8,           # 0x002D
    pygame.K_KP9,           # 0x002E
    pygame.K_KP_ENTER,      # 0x002F
    pygame.K_KP_PLUS,       # 0x0030
    pygame.K_KP_MINUS,      # 0x0031
    pygame.K_KP_MULTIPLY,   # 0x0032
    pygame.K_KP_DIVIDE,     # 0x0033
    pygame.K_KP_PERIOD,     # 0x0034
    pygame.K_F1,            # 0x0035
    pygame.K_F2,            # 0x0036
    pygame.K_F3,            # 0x0037
    pygame.K_F4,            # 0x0038
    pygame.K_F5,            # 0x0039
    pygame.K_F6,            # 0x003A
    pygame.K_F7,            # 0x003B
    pygame.K_F8,            # 0x003C
    pygame.K_F9,            # 0x003D
    pygame.K_F10,           # 0x003E
    pygame.K_F11,           # 0x003F
    pygame.K_F12,           # 0x0040
    pygame.K_BACKQUOTE,     # 0x0041
    pygame.K_MINUS,         # 0x0042
    pygame.K_EQUALS,        # 0x0043
    pygame.K_LEFTBRACKET,   # 0x0044
    pygame.K_RIGHTBRACKET,  # 0x0045
    pygame.K_BACKSLASH,     # 0x0046
    pygame.K_SEMICOLON,     # 0x0047
    pygame.K_QUOTE,         # 0x0048
    pygame.K_COMMA,         # 0x0049
    pygame.K_PERIOD,        # 0x004A
    pygame.K_SLASH,         # 0x004B
    pygame.K_UP,            # 0x004C
    pygame.K_DOWN,          # 0x004D
    pygame.K_LEFT,          # 0x004E
    pygame.K_RIGHT,         # 0x004F
    pygame.K_LSHIFT,        # 0x0050
    pygame.K_LCTRL,         # 0x0051
    pygame.K_LALT,          # 0x0052
    pygame.K_RSHIFT,        # 0x0053
    pygame.K_RCTRL,         # 0x0054
    pygame.K_RALT,          # 0x0055
    pygame.K_ESCAPE,        # 0x0056
    pygame.K_RETURN,        # 0x0057
    pygame.K_TAB,           # 0x0058
    pygame.K_BACKSPACE,     # 0x0059
    pygame.K_SPACE,         # 0x005A
    pygame.K_CAPSLOCK,      # 0x005B
    pygame.K_NUMLOCK,       # 0x005C
    pygame.K_SCROLLOCK,     # 0x005D
    pygame.K_PRINT,         # 0x005E
    pygame.K_BREAK,         # 0x005F
    pygame.K_INSERT,        # 0x0060
    pygame.K_HOME,          # 0x0061
    pygame.K_PAGEUP,        # 0x0062
    pygame.K_DELETE,        # 0x0063
    pygame.K_END,           # 0x0064
    pygame.K_PAGEDOWN,      # 0x0065
])}
#endregion Translators

def video_init(self: CPU):
    self.display = pygame.display.set_mode([self.ruleset.mem_depth**2]*2)
    pygame.display.set_caption(self.name)
    self.pygame_clock = pygame.time.Clock()

def video_handler(self: CPU):
    pygame.display.flip()
    self.pygame_clock.tick(self.clock_speed)

def interrupt_caller(self: CPU):

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            self.interrupt(0x01)

        elif event.type == pygame.KEYDOWN:
            self.interrupt(0x02)
            self.registers['a'].write(int_to_bin(keycodes.get(event.key,0),self.registers['a'].size))

        elif event.type == pygame.KEYUP:
            self.interrupt(0x03)
            self.registers['a'].write(int_to_bin(keycodes.get(event.key,0),self.registers['a'].size))

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
            t = time.time()-start_time
            dt = time.localtime(t+start_time)
            print(dt)
            mode = time_keys[args.get('m','0000')]
            v = 0
            match(mode):
                case 'uptime': v = round(t-0.5)
                case 'milli-second of second':
                    if time.get_clock_info('time').resolution > 0.001:
                        self.PC += 1
                        self.interrupt(0x03)
                        return
                    v = round(t - round(t-0.5) * 1000)
                case 'second of minute': v = dt.tm_sec
                case 'minute of hour': v = dt.tm_min
                case 'hour of day': v = dt.tm_hour
                case 'day of the week': v = dt.tm_wday
                case 'day of the month': v = dt.tm_mday
                case 'day of the year': v = dt.tm_yday
                case 'month': v = dt.tm_mon
                case 'year': v = dt.tm_year
            print(int_to_bin(v,self.ruleset.mem_depth))
            self.registers[reg_keys[orig_args['r1']]].write(int_to_bin(v,self.ruleset.mem_depth))
            debug(f'Current {mode} -> {reg_keys[orig_args['r1']]}')
        #endregion Special Instructions

        #region ALU Instructions
        case 'flag':
            flag = args['f']
            v = args['v'] == '1'
            if flag == '0101':
                for flag in self.ruleset.flags: self.flags[flag] = v
                debug(f'Setting all flags to {v}.')
            else:
                flag = flag_keys[flag]
                self.flags[flag] = v
                debug(f'Setting flag {flag} to {v}.')
        
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

ruleset = Ruleset(56,16,256,{'a':16,'b':16,'c':16,'d':16,'res':16,'vid_r':8,'vid_g':8,'vid_b':8,'vid_addr':16},['s','c','z','n','o'],video_init,exec_handler,interrupt_caller,video_handler)

#region Ruleset Instruction Defs

#region Special Instructions
ruleset.add_rule('nop',{},'0x00 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')
ruleset.add_rule('nop r1',{'r1':4},'0x00 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ 0x0000')
ruleset.add_rule('nop v1',{'v1':40},'0x00 @ 0x02 @ v1`40')

ruleset.add_rule('intd',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x01 @ _v @ r1 @ r2 @ v1 @ v2')

ruleset.add_rule('intr',{'_v':8,'rf':4},'0x02 @ _v @ rf @ 0x0 @ 0x0000 @ 0x0000')

ruleset.add_rule('int',{'_v':8,'r1':4,'v1':16},'0x03 @ _v @ r1 @ 0x0 @ v1 @ 0x0000')

ruleset.add_rule('hlt',{'_v':8,'r1':4,'v1':16},'0x04 @ _v @ r1 @ 0x0 @ v1 @ 0x0000')

ruleset.add_rule('time',{'m':4,'r1':4},'0x05 @ 0x0 @ m @ r1 @ 0x0 @ 0x0000 @ 0x0000')
#endregion Special Instructions

#region ALU Instructions
ruleset.add_rule('flag',{'f':4,'v':1},'0x06 @ f @ 0b000 @ v`1 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

ruleset.add_rule('add',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x07 @ _v @ r1 @ r2 @ v1 @ v2')

ruleset.add_rule('sub',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x08 @ _v @ r1 @ r2 @ v1 @ v2')

ruleset.add_rule('and',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x09 @ _v @ r1 @ r2 @ v1 @ v2')

ruleset.add_rule('or',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x0A @ _v @ r1 @ r2 @ v1 @ v2')

ruleset.add_rule('xor',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x0B @ _v @ r1 @ r2 @ v1 @ v2')

ruleset.add_rule('xnor',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x0C @ _v @ r1 @ r2 @ v1 @ v2')

ruleset.add_rule('bsl',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x0D @ _v @ r1 @ r2 @ v1 @ v2')

ruleset.add_rule('bsr',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x0E @ _v @ r1 @ r2 @ v1 @ v2')

ruleset.add_rule('brl',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x0F @ _v @ r1 @ r2 @ v1 @ v2')

ruleset.add_rule('brr',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x10 @ _v @ r1 @ r2 @ v1 @ v2')
#endregion ALU Instructions

#region Register / Memory Management Instructions
ruleset.add_rule('mov',{'_v':8,'r1':4,'r2':4,'v2':16},'0x11 @ _v @ r1 @ r2 @ 0x0000 @ v2')

ruleset.add_rule('ldr',{'_v':8,'r1':4,'r2':4,'v2':16},'0x12 @ _v @ r1 @ r2 @ 0x0000 @ v2')

ruleset.add_rule('str',{'_v':8,'r1':4,'r2':4,'v1':16,'v2':16},'0x13 @ _v @ r1 @ r2 @ v1 @ v2')
#endregion Register / Memory Management Instructions

#region Jumping Instructions
ruleset.add_rule('jmp',{'_v':8,'r1':4,'v1':16},'0x14 @ _v @ r1 @ 0x0 @ v1 @ 0x0000')

ruleset.add_rule('jif',{'_v':4,'f':4,'r1':4,'v1':16},'0x15 @ _v @ f @ r1 @ 0x0 @ v1 @ 0x0000')

ruleset.add_rule('jnot',{'_v':4,'f':4,'r1':4,'v1':16},'0x16 @ _v @ f @ r1 @ 0x0 @ v1 @ 0x0000')

ruleset.add_rule('jeq',{'r1':4,'r2':4,'v1':16},'0x17 @ 0x00 @ r1 @ r2 @ v1 @ 0x0000')
ruleset.add_rule('jeqz',{'r1':4,'v1':16},'0x17 @ 0x01 @ r1 @ 0x0 @ v1 @ 0x0000')

ruleset.add_rule('jlt',{'r1':4,'r2':4,'v1':16},'0x18 @ 0x00 @ r1 @ r2 @ v1 @ 0x0000')
ruleset.add_rule('jltz',{'r1':4,'v1':16},'0x18 @ 0x01 @ r1 @ 0x0 @ v1 @ 0x0000')

ruleset.add_rule('jgt',{'r1':4,'r2':4,'v1':16},'0x19 @ 0x00 @ r1 @ r2 @ v1 @ 0x0000')
ruleset.add_rule('jgtz',{'r1':4,'v1':16},'0x19 @ 0x01 @ r1 @ 0x0 @ v1 @ 0x0000')

ruleset.add_rule('jle',{'r1':4,'r2':4,'v1':16},'0x1A @ 0x00 @ r1 @ r2 @ v1 @ 0x0000')
ruleset.add_rule('jlez',{'r1':4,'v1':16},'0x1A @ 0x01 @ r1 @ 0x0 @ v1 @ 0x0000')

ruleset.add_rule('jge',{'r1':4,'r2':4,'v1':16},'0x1B @ 0x00 @ r1 @ r2 @ v1 @ 0x0000')
ruleset.add_rule('jgez',{'r1':4,'v1':16},'0x1B @ 0x01 @ r1 @ 0x0 @ v1 @ 0x0000')
#endregion Jumping Instructions

#region Power Instructions
ruleset.add_rule('pwd',{},'0x1C @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')
#endregion Power Instructions

#region Video Instructions
# TODO
#endregion Video Instructions

#endregion Ruleset Instruction Defs

#region Run Emulator
cpu = CPU('x56 CPU',100,ruleset)
program_code = assemble(input_file='program.asm').replace('\n','')
cpu.PRAM.write(program_code)
while True: cpu.clock()
#endregion Run Emulator

'''
TODO:

Video stuff, so thats per pixel setting, blitting, and text mode.
'''