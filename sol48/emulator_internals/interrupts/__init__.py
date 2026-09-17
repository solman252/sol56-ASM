from sol48.emulator_internals.helpers import *

def caller(self: CPU):
    if self.flags['i']:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                handler_addr = int(self.ITABLE.read(self.ruleset.mem_depth,self.ruleset.mem_depth),2)
                if handler_addr == 0: exit()
                self.interrupt(0x01)

            elif event.type == pygame.KEYDOWN:
                self.interrupt(0x02)
                self.registers['a'].write(int_to_bin(keycodes.get(event.key,0),self.registers['a'].size))

            elif event.type == pygame.KEYUP:
                self.interrupt(0x03)
                self.registers['a'].write(int_to_bin(keycodes.get(event.key,0),self.registers['a'].size))

def exception_handler(self: CPU, exception: str, **kwargs):
    match exception:
        case 'No Instruction Matches':
            if self.debug_mode: print(f'EXCEPTION 0x06',end=' => ')
            self.interrupt(0x06)
            self.registers['a'].write(int_to_bin(self.PC,self.registers['a'].size))
        case 'Invalid Interrupt Code':
            if self.debug_mode: print(f'EXCEPTION 0x07',end=' => ')
            self.interrupt(0x07)
            self.registers['a'].write(int_to_bin(self.PC,self.registers['a'].size))
        case _: raise NotImplementedError

def on_enter(self: CPU, code: int):
    self.registers['iflags'].write(''.join(str(int(self.flags[f])) for f in self.ruleset.flags).ljust(self.registers['iflags'].size,'0'))

def on_exit(self: CPU, code: int, reset_flags: bool):
    if reset_flags:
        iflags = self.registers['iflags'].read()
        for i,f in enumerate(self.ruleset.flags): self.flags[f] = iflags[i] == '1'

__all__ = ['caller','exception_handler','on_enter','on_exit']