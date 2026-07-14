#include "rules.asm"

debug enable

intd interrupt_handle_exit, [0x01]
intd interrupt_handle_keydown, [0x02]

hlt 0x01
pwd

interrupt_handle_exit:
    pwd
intr

interrupt_handle_keydown:
    clr state
    ; ESC -> Shut down {
        mov b, 0x0055
        xor a, b
        jnot f_z, $+1 + 1 ; skip next 1 instructions
        pwd
    ; }

    ; Space -> Debug RTC {
        mov b, 0x005A
        xor a, b
        jnot f_z, $+1 + 2 ; skip next 2 instructions
        time uptime, a
        debug a
    ; }
intr