from emulator_internals.helpers import *

import pygame

def caller(self: CPU):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            self.interrupt(0x01)

        elif event.type == pygame.KEYDOWN:
            self.interrupt(0x02)
            self.registers['a'].write(int_to_bin(keycodes.get(event.key,0),self.registers['a'].size))

        elif event.type == pygame.KEYUP:
            self.interrupt(0x03)
            self.registers['a'].write(int_to_bin(keycodes.get(event.key,0),self.registers['a'].size))

__all__ = ['caller']
