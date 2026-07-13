#once

#bankdef rules {
    #bits 16
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

#ruledef {
; ---- Special Instructions ---- {

    ; No operation, does nothing this cycle.
    nop => 0x00 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

    ; Halt CPU execution until an interrupt signal is received.
    hlt => asm { hlt 0x0000 }
    ; Argument may be used to differentiate which halt is occuring. Purely for debugging purposes.
    hlt {r1: reg} => 0x01 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000
    hlt {v1: u16} => 0x01 @ 0x01 @ 0x0 @ 0x0 @ v1`16 @ 0x0000
    
    ; interrupts basically are a dict of interrupt codes as the key, and an address of an interrupt handler to jump to
    ; interrupts are caused by external factors like keyboard and mouse and stuff
    ; we also need to store the address of the current instruction and the state of the flags and registers
    ; halting just waits for an interrupt, i dunno if halting for a specefic interrupt is a thing but ill implement it

; }

; ---- ALU Operations ---- {

    ; Set signed vs unsigned mode on ALU
    sign u => 0x02 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; ALU uses interprets values as unsigned.
    sign s => 0x02 @ 0x01 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; ALU uses interprets values as signed.

    ; Set carry in for ALU
    carry 0 => 0x02 @ 0x02 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
    carry 1 => 0x02 @ 0x03 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

    ; Set flags
    flag z, 0 => 0x02 @ 0x04 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
    flag z, 1 => 0x02 @ 0x05 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

    flag n, 0 => 0x02 @ 0x06 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
    flag n, 1 => 0x02 @ 0x07 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

    flag o, 0 => 0x02 @ 0x08 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
    flag o, 1 => 0x02 @ 0x09 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

    ; For all ALU operations:
    ; Result is written to res,
    ; FLAG_S will determine if in signed mode or not,
    ; FLAG_C acts as carry in,
    ; FLAG_Z will show whether the result == 0,
    ; FLAG_N will show whether the result is negative (if in signed mode),
    ; FLAG_O will show whether an overflow occurred,

    ; Add 2 values together.
    ; If ALU is in unsigned mode, FLAG_C will show whether a carry occured.
    ; If ALU is in signed mode, FLAG_O will show whether a overflow occured.
    add {r1: reg}, {r2: reg} => 0x03 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} + {r2}
    add {r1: reg}, {v2: u16} => 0x03 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2`16 ; res <- {r1} + v2
    add {v1: u16}, {r2: reg} => 0x03 @ 0x02 @ 0x0 @ r2`16 @ v1`16 @ 0x0000 ; res <- v1 + {r2}
    add {v1: u16}, {v2: u16} => 0x03 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 + v2

    ; Subtract one value from another.
    ; If ALU is in unsigned mode, FLAG_C will show whether a carry occured.
    ; If ALU is in signed mode, FLAG_O will show whether a overflow occured.
    sub {r1: reg}, {r2: reg} => 0x04 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} - {r2}
    sub {r1: reg}, {v2: u16} => 0x04 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} - v2
    sub {v1: u16}, {r2: reg} => 0x04 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 - {r2}
    sub {v1: u16}, {v2: u16} => 0x04 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 - v2

    ; Perform a bitwise and between 2 values.
    and {r1: reg}, {r2: reg} => 0x05 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} & {r2}
    and {r1: reg}, {v2: u16} => 0x05 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} & v2
    and {v1: u16}, {r2: reg} => 0x05 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 & {r2}
    and {v1: u16}, {v2: u16} => 0x05 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 & v2

    ; Perform a bitwise or between 2 values.
    or {r1: reg}, {r2: reg} => 0x06 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} | {r2}
    or {r1: reg}, {v2: u16} => 0x06 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} | v2
    or {v1: u16}, {r2: reg} => 0x06 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 | {r2}
    or {v1: u16}, {v2: u16} => 0x06 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 | v2

    ; Perform a bitwise xor between 2 values.
    xor {r1: reg}, {r2: reg} => 0x07 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} ^ {r2}
    xor {r1: reg}, {v2: u16} => 0x07 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} ^ v2
    xor {v1: u16}, {r2: reg} => 0x07 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 ^ {r2}
    xor {v1: u16}, {v2: u16} => 0x07 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 ^ v2

    ; Perform a bitwise xnor between values from 2 registers.
    xnor {r1: reg}, {r2: reg} => 0x08 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- ~({r1} ^ {r2})
    xnor {r1: reg}, {v2: u16} => 0x08 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- ~({r1} ^ v2)
    xnor {v1: u16}, {r2: reg} => 0x08 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- ~(v1 ^ {r2})
    xnor {v1: u16}, {v2: u16} => 0x08 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- ~(v1 ^ v2)

    ; Bit-shift a value by another value to the left.
    bsl {r1: reg}, {r2: reg} => 0x09 @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} << {r2}
    bsl {r1: reg}, {v2: u16} => 0x09 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} << v2
    bsl {v1: u16}, {r2: reg} => 0x09 @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 << {r2}
    bsl {v1: u16}, {v2: u16} => 0x09 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 << v2
    bsl {r1: reg} => asm { bsl {r1}, 1 }

    ; Bit-shift a value by another value to the right.
    bsr {r1: reg}, {r2: reg} => 0x0A @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} >> {r2}
    bsr {r1: reg}, {v2: u16} => 0x0A @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} >> v2
    bsr {v1: u16}, {r2: reg} => 0x0A @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 >> {r2}
    bsr {v1: u16}, {v2: u16} => 0x0A @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 >> v2
    bsr {r1: reg} => asm { bsr {r1}, 1 }

    ; Bit-rotate a value by another value to the left.
    brl {r1: reg}, {r2: reg} => 0x0B @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} <) {r2}
    brl {r1: reg}, {v2: u16} => 0x0B @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} <) v2
    brl {v1: u16}, {r2: reg} => 0x0B @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 <) {r2}
    brl {v1: u16}, {v2: u16} => 0x0B @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 <) v2
    brl {r1: reg} => asm { brl {r1}, 1 }

    ; Bit-rotate a value by another value to the right.
    brr {r1: reg}, {r2: reg} => 0x0C @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; res <- {r1} (> {r2}
    brr {r1: reg}, {v2: u16} => 0x0C @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; res <- {r1} (> v2
    brr {v1: u16}, {r2: reg} => 0x0C @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; res <- v1 (> {r2}
    brr {v1: u16}, {v2: u16} => 0x0C @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; res <- v1 (> v2
    brr {r1: reg} => asm { brl {r1}, 1 }

; }

; ---- Register / Memory Management ---- {

    ; Copy the right value into the left register.
    mov {r1: reg}, {r2: reg} => 0x0D @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; r1 <- {r2}
    mov {r1: reg}, {v2: u16} => 0x0D @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; r1 <- v2

    ; Copy the value in RAM at the right address into the left register.
    ldr {r1: reg}, [{r2: reg}] => 0x0E @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; r1 <- RAM[{r2}]
    ldr {r1: reg}, [{v2: u16}] => 0x0E @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; r1 <- RAM[v2]

    ; Store the left value into RAM at the right address.
    str {r1: reg}, [{r2: reg}] => 0x0F @ 0x00 @ r1 @ r2 @ 0x0000 @ 0x0000 ; {r1} -> RAM[{r2}]
    str {r1: reg}, [{v2: u16}] => 0x0F @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2 ; {r1} -> RAM[v2]
    str {v1: u16}, [{r2: reg}] => 0x0F @ 0x02 @ 0x0 @ r2 @ v1 @ 0x0000 ; v1 -> RAM[{r2}]
    str {v1: u16}, [{v2: u16}] => 0x0F @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ v2`16 ; v1 -> RAM[v2]

; }

; ---- Screen Instructions ---- {

    vid r, {r1: reg} => asm { mov vid_r, {r1} }
    vid r, {v1: u16} => asm { mov vid_r, {v1} }

    vid g, {r1: reg} => asm { mov vid_g, {r1} }
    vid g, {v1: u16} => asm { mov vid_g, {v1} }

    vid b, {r1: reg} => asm { mov vid_b, {r1} }
    vid b, {v1: u16} => asm { mov vid_b, {v1} }

    vid rg, {r1: reg} => asm {
        mov vid_r, {r1}
        mov vid_g, {r1}
    }
    vid rg, {v1: u16} => asm {
        mov vid_r, {v1}
        mov vid_g, {v1}
    }

    vid rb, {r1: reg} => asm {
        mov vid_r, {r1}
        mov vid_b, {r1}
    }
    vid rb, {v1: u16} => asm {
        mov vid_r, {v1}
        mov vid_b, {v1}
    }

    vid gb, {r1: reg} => asm {
        mov vid_g, {r1}
        mov vid_b, {r1}
    }
    vid gb, {v1: u16} => asm {
        mov vid_g, {v1}
        mov vid_b, {v1}
    }

    vid rgb, {r1: reg} => asm {
        mov vid_r, {r1}
        mov vid_g, {r1}
        mov vid_b, {r1}
    }
    vid rgb, {v1: u16} => asm {
        mov vid_r, {v1}
        mov vid_g, {v1}
        mov vid_b, {v1}
    }

    vid addr, {r1: reg} => asm { mov vid_addr, {r1} }
    vid addr, {v1: u16} => asm { mov vid_addr, {v1} }

    ; Write to the framebuffer at address {vid_addr} with color (vid_r,vid_g,vid_b)
    vwr => 0x10 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Screen.framebuffer[vid_addr] <- (vid_r,vid_g,vid_b)

    vwr {r1: reg} => asm {
        mov vid_addr, {r1}
        vwr
    }
    vwr {v1: u16} => asm {
        mov vid_addr, {v1}
        vwr
    }

    ; Clear the framebuffer.
    vcl => 0x11 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Screen.framebuffer[0:] <- (0,0,0)

    ; Flush framebuffer to the screen.
    vfl => 0x12 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Screen[0:] <- Screen.framebuffer[0:]

; }

; ---- Branch Instructions ---- {

    jmp {r1: reg} => 0x13 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; PC <- {r1}
    jmp {v1: u16} => 0x13 @ 0x01 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; PC <- v1

    bif s {r1: reg} => 0x14 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if s: PC <- {r1}
    bif s {v1: u16} => 0x14 @ 0x01 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if s: PC <- v1

    bif c {r1: reg} => 0x14 @ 0x02 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if c: PC <- {r1}
    bif c {v1: u16} => 0x14 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if c: PC <- v1

    bif z {r1: reg} => 0x14 @ 0x04 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if z: PC <- {r1}
    bif z {v1: u16} => 0x14 @ 0x05 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if z: PC <- v1

    bif n {r1: reg} => 0x14 @ 0x06 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if n: PC <- {r1}
    bif n {v1: u16} => 0x14 @ 0x07 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if n: PC <- v1

    bif o {r1: reg} => 0x14 @ 0x08 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if o: PC <- {r1}
    bif o {v1: u16} => 0x14 @ 0x09 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if o: PC <- v1

    ; bif lt {r1: reg} => 0x14 @ 0x0A @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if n ^ o: PC <- {r1}
    ; bif lt {v1: u16} => 0x14 @ 0x0B @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if n ^ o: PC <- v1

    ; bif gt {r1: reg} => 0x14 @ 0x0C @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if z & (n ^ o): PC <- {r1}
    ; bif gt {v1: u16} => 0x14 @ 0x0D @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if z & (n ^ o): PC <- v1

    ; bif le {r1: reg} => 0x14 @ 0x0E @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if z | (n ^ o): PC <- {r1}
    ; bif le {v1: u16} => 0x14 @ 0x0F @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if z | (n ^ o): PC <- v1

    ; bif ge {r1: reg} => 0x14 @ 0x10 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if ~(n ^ o): PC <- {r1}
    ; bif ge {v1: u16} => 0x14 @ 0x11 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if ~(n ^ o): PC <- v1

    bnot s {r1: reg} => 0x15 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if s: PC <- {r1}
    bnot s {v1: u16} => 0x15 @ 0x01 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if s: PC <- v1

    bnot c {r1: reg} => 0x15 @ 0x02 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if c: PC <- {r1}
    bnot c {v1: u16} => 0x15 @ 0x03 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if c: PC <- v1

    bnot z {r1: reg} => 0x15 @ 0x04 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if z: PC <- {r1}
    bnot z {v1: u16} => 0x15 @ 0x05 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if z: PC <- v1

    bnot n {r1: reg} => 0x15 @ 0x06 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if n: PC <- {r1}
    bnot n {v1: u16} => 0x15 @ 0x07 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if n: PC <- v1

    bnot o {r1: reg} => 0x15 @ 0x08 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if o: PC <- {r1}
    bnot o {v1: u16} => 0x15 @ 0x09 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if o: PC <- v1

    ; bnot lt {r1: reg} => 0x15 @ 0x0A @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if n ^ o: PC <- {r1}
    ; bnot lt {v1: u16} => 0x15 @ 0x0B @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if n ^ o: PC <- v1

    ; bnot gt {r1: reg} => 0x15 @ 0x0C @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if z & (n ^ o): PC <- {r1}
    ; bnot gt {v1: u16} => 0x15 @ 0x0D @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if z & (n ^ o): PC <- v1

    ; bnot le {r1: reg} => 0x15 @ 0x0E @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if z | (n ^ o): PC <- {r1}
    ; bnot le {v1: u16} => 0x15 @ 0x0F @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if z | (n ^ o): PC <- v1

    ; bnot ge {r1: reg} => 0x15 @ 0x10 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; if ~(n ^ o): PC <- {r1}
    ; bnot ge {v1: u16} => 0x15 @ 0x11 @ 0x0 @ 0x0 @ v1`16 @ 0x0000 ; if ~(n ^ o): PC <- v1

; }

; ---- Keyboard Instructions ---- {

    kp {r1: reg} => 0x16 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; r1 <- KEYBOARD_QUEUE.pop()

    kl {r1: reg} => 0x17 @ 0x00 @ r1 @ 0x0 @ 0x0000 @ 0x0000 ; r1 <- KEYBOARD_QUEUE.length

    kcl => 0x18 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Clear KEYBOARD_QUEUE.

; }
    
; ---- Power Instructions ---- {

    slp => 0x19 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Enter sleep mode.

    pwd => 0x1A @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000 ; Shut off the power.

; }

} ; #endruledef