#once

#bankdef rules {
    #bits 56
    outp = 0 * 0x0
}

#subruledef reg {
  a => 0x1
  b => 0x2
  c => 0x3
  d => 0x4
  res => 0x5
  vid_r => 0x6
  vid_g => 0x7
  vid_b => 0x8
  vid_addr => 0x9
}

#subruledef flag {
  f_s => 0x0
  f_c => 0x1
  f_z => 0x2
  f_n => 0x3
  f_o => 0x4
}

#ruledef {
; ---- Special Instructions ---- {

    ; No operation, does nothing this cycle.
    nop =>           0x00 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
    nop {r1: reg} => 0x00 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ 0x0000 ; You can use this to put a register into without worry of it affecting anything.
    nop {v1: i40} => 0x00 @ 0x02 @ v1`40                       ; You can use this to put 40 bits of custom data in without any worry of it affecting anything.

    debug {r1: reg} => asm { nop {r1} }
    debug {v1: i40} => asm { nop {v1} }

    debug enable => asm { nop 0x1FCE2A8739 }
    debug disable => asm { nop 0x1FCE2A873C }

    ; Define an interrupt handler with the left value being the handler's address and the right value being the interrupt code.
    intd {r1: reg}, [{r2: reg}] => 0x01 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000      ; {r1} -> ITABLE[{r2}]
    intd {r1: reg}, [{v2: u8}] =>  0x01 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ 0x00 @ v2`8 ; {r1} -> ITABLE[v2]
    intd {v1: u16}, [{r2: reg}] => 0x01 @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000      ; v1 -> ITABLE[{r2}]
    intd {v1: u16}, [{v2: u8}] =>  0x01 @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ 0x00 @ v2`8 ; v1 -> ITABLE[v2]

    ; Return back from handling an interrupt to main code execution.
    intr => 0x02 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

    ; Halt CPU execution until an interrupt signal is received.
    ; Argument may be used to specify an interrupt signal to halt until.
    hlt =>           0x03 @ 0x00 @ 0x0 @ 0x0 @ 0x0000      @ 0x0000
    hlt {r1: reg} => 0x03 @ 0x01 @ r1  @ 0x0 @ 0x0000      @ 0x0000
    hlt {v1: u8} =>  0x03 @ 0x02 @ 0x0 @ 0x0 @ 0x00 @ v1`8 @ 0x0000

    int {r1: reg} => 0x04 @ 0x00 @ r1  @ 0x0 @ 0x0000      @ 0x000
    int {v1: u8} =>  0x04 @ 0x01 @ 0x0 @ 0x0 @ 0x00 @ v1`8 @ 0x0000

; }

; ---- ALU Operations ---- {

    ; Set the value of a flag
    flag {f: flag}, {v: u1} => 0x05 @ f @ 0b000 @ v`1 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

    sign u => asm { flag f_s, 0 }
    sign 0 => asm { flag f_s, 0 }
    sign s => asm { flag f_s, 1 }
    sign 1 => asm { flag f_s, 1 }

    carry 0 => asm { flag f_c, 0 }
    carry 1 => asm { flag f_c, 1 }

    ; For all ALU operations:
    ; Result is written to res,
    ; FLAG_S will determine if in signed mode or not,
    ; FLAG_C acts as carry in,
    ; FLAG_Z will show whether the result == 0,
    ; FLAG_N will show whether the result is negative (if in signed mode),
    ; FLAG_O will show whether an overflow occurred,

    ; Add 2 values together.
    ; FLAG_Z will show if the result is 0.
    ; If ALU is in unsigned mode, FLAG_C will show whether a carry occured.
    ; If ALU is in signed mode, FLAG_O will show whether a overflow occured, and FLAG_N will show if the result is negative.
    add {r1: reg}, {r2: reg} => 0x06 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000 ; res <- {r1} + {r2}
    add {r1: reg}, {v2: i16} => 0x06 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16  ; res <- {r1} + v2
    add {v1: i16}, {r2: reg} => 0x06 @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000 ; res <- v1 + {r2}
    add {v1: i16}, {v2: i16} => 0x06 @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16  ; res <- v1 + v2

    ; Subtract one value from another.
    ; If ALU is in unsigned mode, FLAG_C will show whether a carry occured.
    ; If ALU is in signed mode, FLAG_O will show whether a overflow occured.
    sub {r1: reg}, {r2: reg} => 0x07 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000 ; res <- {r1} - {r2}
    sub {r1: reg}, {v2: i16} => 0x07 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16  ; res <- {r1} - v2
    sub {v1: i16}, {r2: reg} => 0x07 @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000 ; res <- v1 - {r2}
    sub {v1: i16}, {v2: i16} => 0x07 @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16  ; res <- v1 - v2

    ; Perform a bitwise and between 2 values.
    and {r1: reg}, {r2: reg} => 0x08 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000 ; res <- {r1} & {r2}
    and {r1: reg}, {v2: i16} => 0x08 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16  ; res <- {r1} & v2
    and {v1: i16}, {r2: reg} => 0x08 @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000 ; res <- v1 & {r2}
    and {v1: i16}, {v2: i16} => 0x08 @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16  ; res <- v1 & v2

    ; Perform a bitwise or between 2 values.
    or {r1: reg}, {r2: reg} => 0x09 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000 ; res <- {r1} | {r2}
    or {r1: reg}, {v2: i16} => 0x09 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16  ; res <- {r1} | v2
    or {v1: i16}, {r2: reg} => 0x09 @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000 ; res <- v1 | {r2}
    or {v1: i16}, {v2: i16} => 0x09 @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16  ; res <- v1 | v2

    ; Perform a bitwise xor between 2 values.
    xor {r1: reg}, {r2: reg} => 0x0A @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000 ; res <- {r1} ^ {r2}
    xor {r1: reg}, {v2: i16} => 0x0A @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16  ; res <- {r1} ^ v2
    xor {v1: i16}, {r2: reg} => 0x0A @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000 ; res <- v1 ^ {r2}
    xor {v1: i16}, {v2: i16} => 0x0A @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16  ; res <- v1 ^ v2

    ; Perform a bitwise xnor between values from 2 registers.
    xnor {r1: reg}, {r2: reg} => 0x0B @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000 ; res <- ~({r1} ^ {r2})
    xnor {r1: reg}, {v2: i16} => 0x0B @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16  ; res <- ~({r1} ^ v2)
    xnor {v1: i16}, {r2: reg} => 0x0B @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000 ; res <- ~(v1 ^ {r2})
    xnor {v1: i16}, {v2: i16} => 0x0B @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16  ; res <- ~(v1 ^ v2)

    ; Bit-shift a value by another value to the left.
    bsl {r1: reg}, {r2: reg} => 0x0C @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000 ; res <- {r1} << {r2}
    bsl {r1: reg}, {v2: u16} => 0x0C @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16  ; res <- {r1} << v2
    bsl {v1: i16}, {r2: reg} => 0x0C @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000 ; res <- v1 << {r2}
    bsl {v1: i16}, {v2: u16} => 0x0C @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16  ; res <- v1 << v2
    bsl {r1: reg} => asm { bsl {r1}, 1 }

    ; Bit-shift a value by another value to the right.
    bsr {r1: reg}, {r2: reg} => 0x0D @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000 ; res <- {r1} >> {r2}
    bsr {r1: reg}, {v2: u16} => 0x0D @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16  ; res <- {r1} >> v2
    bsr {v1: i16}, {r2: reg} => 0x0D @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000 ; res <- v1 >> {r2}
    bsr {v1: i16}, {v2: u16} => 0x0D @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16  ; res <- v1 >> v2
    bsr {r1: reg} => asm { bsr {r1}, 1 }

    ; Bit-rotate a value by another value to the left.
    brl {r1: reg}, {r2: reg} => 0x0E @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000 ; res <- {r1} <) {r2}
    brl {r1: reg}, {v2: u16} => 0x0E @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16  ; res <- {r1} <) v2
    brl {v1: i16}, {r2: reg} => 0x0E @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000 ; res <- v1 <) {r2}
    brl {v1: i16}, {v2: u16} => 0x0E @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16  ; res <- v1 <) v2
    brl {r1: reg} => asm { brl {r1}, 1 }

    ; Bit-rotate a value by another value to the right.
    brr {r1: reg}, {r2: reg} => 0x0F @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000 ; res <- {r1} (> {r2}
    brr {r1: reg}, {v2: u16} => 0x0F @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16  ; res <- {r1} (> v2
    brr {v1: i16}, {r2: reg} => 0x0F @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000 ; res <- v1 (> {r2}
    brr {v1: i16}, {v2: u16} => 0x0F @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16  ; res <- v1 (> v2
    brr {r1: reg} => asm { brl {r1}, 1 }

; }

; ---- Register / Memory Management ---- {

    ; Copy the right value into the left register.
    mov {r1: reg}, {r2: reg} => 0x10 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000 ; r1 <- {r2}
    mov {r1: reg}, {v2: i16} => 0x10 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16  ; r1 <- v2
    mov {r1: reg}, {f: flag} => 0x10 @ 0x02 @ f   @ 0x1 @ 0x0000 @ 0x0000 ; r1 <- f

    ; Copy the value in RAM at the right address into the left register.
    ldr {r1: reg}, [{r2: reg}] => 0x11 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000 ; r1 <- RAM[{r2}]
    ldr {r1: reg}, [{v2: u16}] => 0x11 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16  ; r1 <- RAM[v2]

    mov {r1: reg}, [{r2: reg}] => asm { ldr {r1}, [{r2}] }
    mov {r1: reg}, [{v2: u16}] => asm { ldr {r1}, [{v2}] }

    ; Store the left value into RAM at the right address.
    str {r1: reg}, [{r2: reg}] => 0x12 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000 ; {r1} -> RAM[{r2}]
    str {r1: reg}, [{v2: u16}] => 0x12 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16  ; {r1} -> RAM[v2]
    str {v1: i16}, [{r2: reg}] => 0x12 @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000 ; v1 -> RAM[{r2}]
    str {v1: i16}, [{v2: u16}] => 0x12 @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16  ; v1 -> RAM[v2]

    mov [{r1: reg}], {r2: reg} => asm { str r2, [r1]}
    mov [{v1: u16}], {r2: reg} => asm { str r2, [v1]}
    mov [{r1: reg}], {v2: i16} => asm { str v2, [r1]}
    mov [{v1: i16}], {v2: i16} => asm { str v2, [v1]}

; }

; ---- Branch Instructions ---- {

    jmp {r1: reg} => 0x13 @ 0x00 @ r1  @ 0x0 @ 0x0000 @ 0x0000
    jmp {v1: u16} => 0x13 @ 0x01 @ 0x0 @ 0x0 @ v1`16  @ 0x0000

    jif {f: flag}, {r1: reg} => 0x14 @ 0x0 @ f @ r1  @ 0x0 @ 0x0000 @ 0x0000
    jif {f: flag}, {v1: u16} => 0x14 @ 0x1 @ f @ 0x0 @ 0x0 @ v1`16  @ 0x0000

    jnot {f: flag}, {r1: reg} => 0x15 @ 0x0 @ f @ r1  @ 0x0 @ 0x0000 @ 0x0000
    jnot {f: flag}, {v1: u16} => 0x15 @ 0x1 @ f @ 0x0 @ 0x0 @ v1`16  @ 0x0000

    jeq {r1: reg}, {r2: reg}, {v1: u16} => 0x16 @ 0x00 @ r1 @ r2  @ v1`16 @ 0x0000
    jeqz {r1: reg}, {v1: u16}           => 0x16 @ 0x01 @ r1 @ 0x0 @ v1`16 @ 0x0000

    jlt {r1: reg}, {r2: reg}, {v1: u16} => 0x17 @ 0x00 @ r1 @ r2  @ v1`16 @ 0x0000
    jltz {r1: reg}, {v1: u16}           => 0x17 @ 0x01 @ r1 @ 0x0 @ v1`16 @ 0x0000

    jgt {r1: reg}, {r2: reg}, {v1: u16} => 0x18 @ 0x00 @ r1 @ r2  @ v1`16 @ 0x0000
    jgtz {r1: reg}, {v1: u16}           => 0x18 @ 0x01 @ r1 @ 0x0 @ v1`16 @ 0x0000

    jle {r1: reg}, {r2: reg}, {v1: u16} => 0x19 @ 0x00 @ r1 @ r2  @ v1`16 @ 0x0000
    jlez {r1: reg}, {v1: u16}           => 0x19 @ 0x01 @ r1 @ 0x0 @ v1`16 @ 0x0000

    jge {r1: reg}, {r2: reg}, {v1: u16} => 0x1A @ 0x00 @ r1 @ r2  @ v1`16 @ 0x0000
    jgez {r1: reg}, {v1: u16}           => 0x1A @ 0x01 @ r1 @ 0x0 @ v1`16 @ 0x0000
; }
    
; ---- Power Instructions ---- {

    pwd => 0x1B @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Shut off the power.

; }

; ; ---- Video Instructions ---- {

;     vid r, {r1: reg} => asm { mov vid_r, {r1} }
;     vid r, {v1: u8} => asm { mov vid_r, 0x00 @ {v1`8} }

;     vid g, {r1: reg} => asm { mov vid_g, {r1} }
;     vid g, {v1: u8} => asm { mov vid_g, 0x00 @ {v1`8} }

;     vid b, {r1: reg} => asm { mov vid_b, {r1} }
;     vid b, {v1: u8} => asm { mov vid_b, 0x00 @ {v1`8} }

;     vid rg, {r1: reg} => asm {
;         mov vid_r, {r1}
;         mov vid_g, {r1}
;     }
;     vid rg, {v1: u8} => asm {
;         mov vid_r, 0x00 @ {v1`8}
;         mov vid_g, 0x00 @ {v1`8}
;     }

;     vid rb, {r1: reg} => asm {
;         mov vid_r, {r1}
;         mov vid_b, {r1}
;     }
;     vid rb, {v1: u8} => asm {
;         mov vid_r, 0x00 @ {v1`8}
;         mov vid_b, 0x00 @ {v1`8}
;     }

;     vid gb, {r1: reg} => asm {
;         mov vid_g, {r1}
;         mov vid_b, {r1}
;     }
;     vid gb, {v1: u8} => asm {
;         mov vid_g, 0x00 @ {v1`8}
;         mov vid_b, 0x00 @ {v1`8}
;     }

;     vid rgb, {r1: reg} => asm {
;         mov vid_r, {r1}
;         mov vid_g, {r1}
;         mov vid_b, {r1}
;     }
;     vid rgb, {v1: u8} => asm {
;         mov vid_r, 0x00 @ {v1`8}
;         mov vid_g, 0x00 @ {v1`8}
;         mov vid_b, 0x00 @ {v1`8}
;     }

;     vid addr, {r1: reg} => asm { mov vid_addr, {r1} }
;     vid addr, {v1: u16} => asm { mov vid_addr, {v1} }

;     ; Write to the framebuffer at address {vid_addr} with color (vid_r,vid_g,vid_b)
;     vwr => 0x1B @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Screen.framebuffer[vid_addr] <- (vid_r,vid_g,vid_b)

;     vwr {r1: reg} => asm {
;         mov vid_addr, {r1}
;         vwr
;     }
;     vwr {v1: u16} => asm {
;         mov vid_addr, {v1}
;         vwr
;     }

;     ; Clear the framebuffer.
;     vcl => 0x1C @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Screen.framebuffer[0:] <- (0,0,0)

;     ; Flush framebuffer to the screen.
;     vfl => 0x1D @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Screen[0:] <- Screen.framebuffer[0:]

; ; }

} ; #endruledef