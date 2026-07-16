import pygame

def init(self: CPU):
    self.display = pygame.display.set_mode([self.ruleset.mem_depth**2]*2)
    pygame.display.set_caption(self.name)
    self.pygame_clock = pygame.time.Clock()

def handler(self: CPU):
    pygame.display.flip()
    self.pygame_clock.tick(self.clock_speed)