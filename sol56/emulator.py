from sys import path, argv; path.append('..'); del path
from emulator_internals.helpers import * 
from lib.customasm import *
import time

ruleset = internal.ruleset.init()
cpu = CPU('x56 CPU',100,ruleset,True)

program = argv[2] if len(argv) == 3 else (argv[1].removeprefix('-program=') if len(argv) == 2 else 'programs/test.asm')
cpu.PRAM.write(assemble(input_file=program).replace('\n',''))

cpu._debug_indented = False
cpu.start_time = time.time()

while True: cpu.clock()