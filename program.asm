#include "rules.asm"

intd interrupt_handle_exit, [0x01]
intd interrupt_handle_keydown, [0x02]
intd interrupt_handle_keyup, [0x03]

hlt 0x01
pwd

interrupt_handle_exit:
    pwd
intr

interrupt_handle_keydown:
    mov b, 0x0055
    xor a, b
    jnot f_z, $+2 ; skip next instruction
    pwd
intr

interrupt_handle_keyup:
    debug a
intr