from sys import path, argv; path.append('..'); cwd = path[0]; del path
from sol48.emulator_internals.helpers import *
from lib.customasm import *

debug_mode = False

ruleset = internal.ruleset.init(debug_mode)
cpu = CPU('x48 CPU',100,ruleset,debug_mode)

program = argv[2] if len(argv) == 3 else (argv[1].removeprefix('-program=') if len(argv) == 2 else 'programs/test.asm')
cpu.RAM.write(assemble(input_file=program).replace('\n',''))

if int(cpu.RAM.read(),2) == 0:
    if debug_mode: print('No instructions loaded, exiting early.')
else:
    cpu.start_time = time.time()
    while True: cpu.clock()