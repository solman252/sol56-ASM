from lib.emulator import *

inst_depth = 56
mem_depth = 16
interrupt_codes = 256
registers = {'a':16,'b':16,'c':16,'d':16,'res':16,'vid_r':8,'vid_g':8,'vid_b':8,'vid_addr':16}
flags = ['s','c','z','n','o']



#region Ruleset Instruction Defs

#region Special Instructions
ruleset.add_rule('nop','0x00 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')
ruleset.add_rule('nop r1','0x00 @ 0x01 @ r1`4 @ 0x0 @ 0x0000 @ 0x0000')
ruleset.add_rule('nop v1','0x00 @ 0x02 @ v1`40')

ruleset.add_rule('intd','0x01 @ _v`8 @ r1`4 @ r2`4 @ v1`16 @ v2`16')

ruleset.add_rule('intr','0x02 @ _v`8 @ rf`4 @ 0x0 @ 0x0000 @ 0x0000')

ruleset.add_rule('int','0x03 @ _v`8 @ r1`4 @ 0x0 @ v1`16 @ 0x0000')

ruleset.add_rule('hlt','0x04 @ _v`8 @ r1`4 @ 0x0 @ v1`16 @ 0x0000')

ruleset.add_rule('time','0x05 @ 0x0 @ m`4 @ r1`4 @ 0x0 @ 0x0000 @ 0x0000')
#endregion Special Instructions

#region ALU Instructions
ruleset.add_rule('flag','0x06 @ f`4 @ 0b000 @ v`1 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')

ruleset.add_rule('add','0x07 @ _v`8 @ r1`4 @ r2`4 @ v1`16 @ v2`16')

ruleset.add_rule('sub','0x08 @ _v`8 @ r1`4 @ r2`4 @ v1`16 @ v2`16')

ruleset.add_rule('and','0x09 @ _v`8 @ r1`4 @ r2`4 @ v1`16 @ v2`16')

ruleset.add_rule('or','0x0A @ _v`8 @ r1`4 @ r2`4 @ v1`16 @ v2`16')

ruleset.add_rule('xor','0x0B @ _v`8 @ r1`4 @ r2`4 @ v1`16 @ v2`16')

ruleset.add_rule('xnor','0x0C @ _v`8 @ r1`4 @ r2`4 @ v1`16 @ v2`16')

ruleset.add_rule('bsl','0x0D @ _v`8 @ r1`4 @ r2`4 @ v1`16 @ v2`16')

ruleset.add_rule('bsr','0x0E @ _v`8 @ r1`4 @ r2`4 @ v1`16 @ v2`16')

ruleset.add_rule('brl','0x0F @ _v`8 @ r1`4 @ r2`4 @ v1`16 @ v2`16')

ruleset.add_rule('brr','0x10 @ _v`8 @ r1`4 @ r2`4 @ v1`16 @ v2`16')
#endregion ALU Instructions

#region Register / Memory Management Instructions
ruleset.add_rule('mov','0x11 @ _v`8 @ r1`4 @ r2`4 @ 0x0000 @ v2`16')

ruleset.add_rule('ldr','0x12 @ _v`8 @ r1`4 @ r2`4 @ 0x0000 @ v2`16')

ruleset.add_rule('str','0x13 @ _v`8 @ r1`4 @ r2`4 @ v1`16 @ v2`16')
#endregion Register / Memory Management Instructions

#region Jumping Instructions
ruleset.add_rule('jmp','0x14 @ _v`8 @ r1`4 @ 0x0 @ v1`16 @ 0x0000')

ruleset.add_rule('jif','0x15 @ _v`8 @ f`4 @ r1`4 @ 0x0 @ v1`16 @ 0x0000')

ruleset.add_rule('jnot','0x16 @ _v`8 @ f`4 @ r1`4 @ 0x0 @ v1`16 @ 0x0000')

ruleset.add_rule('jeq','0x17 @ 0x00 @ r1`4 @ r2`4 @ v1`16 @ 0x0000')
ruleset.add_rule('jeqz','0x17 @ 0x01 @ r1`4 @ 0x0 @ v1`16 @ 0x0000')

ruleset.add_rule('jlt','0x18 @ 0x00 @ r1`4 @ r2`4 @ v1`16 @ 0x0000')
ruleset.add_rule('jltz','0x18 @ 0x01 @ r1`4 @ 0x0 @ v1`16 @ 0x0000')

ruleset.add_rule('jgt','0x19 @ 0x00 @ r1`4 @ r2`4 @ v1`16 @ 0x0000')
ruleset.add_rule('jgtz','0x19 @ 0x01 @ r1`4 @ 0x0 @ v1`16 @ 0x0000')

ruleset.add_rule('jle','0x1A @ 0x00 @ r1`4 @ r2`4 @ v1`16 @ 0x0000')
ruleset.add_rule('jlez','0x1A @ 0x01 @ r1`4 @ 0x0 @ v1`16 @ 0x0000')

ruleset.add_rule('jge','0x1B @ 0x00 @ r1`4 @ r2`4 @ v1`16 @ 0x0000')
ruleset.add_rule('jgez','0x1B @ 0x01 @ r1`4 @ 0x0 @ v1`16 @ 0x0000')
#endregion Jumping Instructions

#region Power Instructions
ruleset.add_rule('pwd','0x1C @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000')
#endregion Power Instructions

#region Video Instructions
# TODO
#endregion Video Instructions

#endregion Ruleset Instruction Defs
