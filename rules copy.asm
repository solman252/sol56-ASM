; RAM: 256 addresses x 16bit values.
; CPU reads/writes only the 8 LSBs.
; Instructions use all 16 bits, with 8 MSB as opcode and 8 LSB as argument.
; The lowest steps per clock tick it can go is 4.
; On my PC, I recomend 5 s/ct, with 4800 s/s, for 100 instructions per second, or 100Hz / 0.1kHz.

#once

#bankdef rules {
    #bits 16
    outp = 0 * 0x00
}

#subruledef reg {
  a => 0b00
  b => 0b01
  c => 0b10
  d => 0b11
}

#ruledef {
; ---- Special Instructions ---- {

    ; No operation, does nothing this cycle.
    nop => 0b000000 @ 0b00 @ 0x00

    ; Halt CPU execution until an interrupt signal is received.
    hlt => asm { hlt 0x00 }
    ; {id} may be used to differentiate which halt is occuring. Purely for debugging purposes.
    hlt {id: u8} => 0b000001 @ 0b00 @ id`8
    
; }

; ---- ALU Operations ---- {

    ; Set signed vs unsigned mode on ALU
    sign u => 0b000010 @ 0b00 @ 0x00 ; ALU uses interprets values as unsigned.
    sign s => 0b000010 @ 0b00 @ 0x01 ; ALU uses interprets values as signed.

    ; Set carry in for ALU
    carry 0 => 0b000010 @ 0b00 @ 0x02
    carry 1 => 0b000010 @ 0b00 @ 0x03

    ; For all ALU operations:
    ; Result is written to res,
    ; FLAG_Z will show whether the result == 0,
    ; FLAG_N will show whether the result is negative (if in signed mode.),

    ; Add the values from 2 registers together.
    ; If ALU is in unsigned mode, FLAG_C will show whether a carry occured.
    ; If ALU is in signed mode, FLAG_O will show whether a overflow occured.
    add {r1: reg}, {r2: reg} => 0b000011 @ r1 @ r2 @ 0b000000 ; res = {r1} + {r2}

    ; Subtract the value from 1 register by another.
    ; If ALU is in unsigned mode, FLAG_C will show whether a carry occured.
    ; If ALU is in signed mode, FLAG_O will show whether a overflow occured.
    sub {r1: reg}, {r2: reg} => 0b000011 @ r1 @ r2 @ 0b000001 ; res = {r1} - {r2}

    ; Perform a bitwise and between values from 2 registers.
    and {r1: reg}, {r2: reg} => 0b000011 @ r1 @ r2 @ 0b000010 ; res = {r1} & {r2}

    ; Perform a bitwise or between values from 2 registers.
    or {r1: reg}, {r2: reg} => 0b000011 @ r1 @ r2 @ 0b000011 ; res = {r1} | {r2}

    ; Perform a bitwise xor between values from 2 registers.
    xor {r1: reg}, {r2: reg} => 0b000011 @ r1 @ r2 @ 0b000100 ; res = {r1} ^ {r2}

    ; Perform a bitwise xnor between values from 2 registers.
    xnor {r1: reg}, {r2: reg} => 0b000011 @ r1 @ r2 @ 0b000101 ; res = ~({r1} ^ {r2})

    ; Bitshift the value from a register once to the left.
    bsl {r: reg} => 0b000011 @ r @ 0x06 ; {r} = {r} << 1

    ; Bitshift the value from a register once to the right.
    bsr {r: reg} => 0b000011 @ r @ 0x07 ; {r} = {r} >> 1

    ; Rotate the bits in the value from a register once to the left.
    brl {r: reg} => 0b000011 @ r @ 0x08 ; {r} = RotLeft({r},1)

    ; Rotate the bits in the value from a register once to the right.
    brr {r: reg} => 0b000011 @ r @ 0x09 ; {r} = RotRight({r},1)

; }

; ---- Register / Memory Management ---- {

    ; Copy the value from the right register into the left register.
    mov {dest: reg}, {source: reg} => 0b000100 @ dest @ source @ 0b000000 ; {dest} = {source}
    ; Copy the ALU result into a register.
    mov {dest: reg}, res => 0b000100 @ dest @ 0x01 ; {dest} = res
    ; Set the value of a register to {val}.
    mov {dest: reg}, {val: u8} => 0b000101 @ dest @ val`8 ; {dest} = {val}

    ; Load the value in memory stored at the address stored in the last 8 bits of the right register into the left register.
    ldr {dest: reg}, [{source: reg}] => 0b000110 @ dest @ source @ 0b000000 ; {dest} = RAM[{source}]
    ; Load the value in memory stored at the address stored in the last 8 bits of the ALU result into register {dest}.
    ldr {dest: reg}, [res] => 0b000110 @ dest @ 0x01 ; {dest} = RAM[res]
    ; Load the value in memory stored at address {source_addr} into register {dest}.
    ldr {dest: reg}, [{source_addr: u8}] => 0b000111 @ dest @ source_addr`8 ; {dest} = RAM[{source_addr}]

    ; add mode store variants sol

    ; Store the value from the left register into memory at the address stored in the right register.
    str {source: reg}, [{dest: reg}] => 0b001000 @ source @ dest @ 0b000000 ; RAM[{dest}] = {source}
    ; Store the value from a register into memory at the address stored in the ALU result.
    str {source: reg}, [res] => 0b001000 @ source @ 0x01 ; RAM[res] = {source}
    ; Store the value from a register into memory at address {val}.
    str {source: reg}, [{dest_addr: u8}] => 0b001001 @ source @ dest_addr`8 ; RAM[{dest_addr}] = {source}
    ; Store {val} into memory at the address stored in a register.
    str {val: u8}, [{dest: reg}] => 0b001010 @ dest @ val`8 ; RAM[{dest}] = {val}

; }

; ---- Screen Instructions ---- {

    ; add alpha channel sol

    ; RGB channels are 4bit, so writing to them will only store the 4 least significant bits.

    ; Set the red channel of the pixel to be written to the value from a register.
    vid r, {source: reg} => 0b001011 @ 0b00 @ source @ 0b000000 ; VID_R = {source} (8 LSB)
    ; Set the red channel of the pixel to be written to {val}.
    vid r, {val: u8} => 0b001011 @ 0b01 @ val`8 ; VID_R = {val}

    ; Set the green channel of the pixel to be written to the value from a register.
    vid g, {source: reg} => 0b001100 @ 0b00 @ source @ 0b000000 ; VID_G = {source} (8 LSB)
    ; Set the green channel of the pixel to be written to {val}.
    vid g, {val: u8} => 0b001100 @ 0b01 @ val`8 ; VID_G = {val}

    ; Set the blue channel of the pixel to be written to the value from a register.
    vid b, {source: reg} => 0b001101 @ 0b00 @ source @ 0b000000 ; VID_G = {source} (8 LSB)
    ; Set the blue channel of the pixel to be written to {val}.
    vid b, {val: u8} => 0b001101 @ 0b01 @ val`8 ; VID_B = {val}

    ; Set the all channels of the pixel to be written to the value from a register.
    vid rgb, {source: reg} => 0b001110 @ 0b00 @ source @ 0b000000 ; VID_G = {source} (8 LSB)
    ; Set the all channels of the pixel to be written to {val}.
    vid rgb, {val: u8} => 0b001110 @ 0b01 @ val`8 ; VID_B = {val}

    ; Set the screen address of the pixel to be written to the value from a register.
    vid addr, {source: reg} => 0b001111  @ 0b00 @ source @ 0b000000 ; VID_ADDR = {source} (8 LSB)
    ; Set the screen address of the pixel to be written to {addr}.
    vid addr, {addr: u8} => 0b001111 @ 0b01 @ addr`8 ; VID_ADDR = {addr}

    ; Write to the framebuffer at address {VID_ADDR} with color [VID_R,VID_G,VIF_B]
    vwr => 0b010001 @ 0b00 @ 0x00 ; Screen.framebuffer[VID_ADDR] = [VID_R,VID_G,VIF_B]

    ; Clear the framebuffer.
    vcl => 0b010010 @ 0b00 @ 0x00 ; Screen.framebuffer[:] = [0,0,0]

    ; Flush framebuffer to the screen.
    vfl => 0b010011 @ 0b00 @ 0x00 ; Screen[0:] = Screen.framebuffer[0:]

; }

; ---- Branch Instructions ---- {

    jmp {r: reg} => 0b010100 @ r @ 0x00 ; PC = {r} (8 LSB)
    bz {r: reg} => 0b010100 @ r @ 0x01 ; if FLAG_Z: PC = {r} (8 LSB)
    bnz {r: reg} => 0b010100 @ r @ 0x02 ; if !FLAG_Z: PC = {r} (8 LSB)
    bc {r: reg} => 0b010100 @ r @ 0x03 ; if FLAG_C: PC = {r} (8 LSB)
    bnc {r: reg} => 0b010100 @ r @ 0x04 ; if !FLAG_C: PC = {r} (8 LSB)
    bn {r: reg} => 0b010100 @ r @ 0x05 ; if FLAG_N: PC = {r} (8 LSB)
    bnn {r: reg} => 0b010100 @ r @ 0x06 ; if !FLAG_N: PC = {r} (8 LSB)
    bo {r: reg} => 0b010100 @ r @ 0x07 ; if FLAG_O: PC = {r} (8 LSB)
    bno {r: reg} => 0b010100 @ r @ 0x08 ; if !FLAG_O: PC = {r} (8 LSB)
    blt {r: reg} => 0b010100 @ r @ 0x09 ; if (FLAG_N ^ FLAG_O): PC = {r} (8 LSB)
    bgt {r: reg} => 0b010100 @ r @ 0x0A ; if (FLAG_Z & (FLAG_N ^ FLAG_O)): PC = {r} (8 LSB)
    ble {r: reg} => 0b010100 @ r @ 0x0B ; if FLAG_Z | (FLAG_N ^ FLAG_O): PC = {r} (8 LSB)
    bge {r: reg} => 0b010100 @ r @ 0x0C ; if !(FLAG_N ^ FLAG_O): PC = {r} (8 LSB)

    jmp {addr: u8} => 0b010101 @ 0b00 @ addr`8 ; PC = addr
    bz {addr: u8} => 0b010111 @ 0b00 @ addr`8 ; if FLAG_Z: PC = addr
    bnz {addr: u8} => 0b011000 @ 0b00 @ addr`8 ; if !FLAG_Z: PC = addr
    bc {addr: u8} => 0b011001 @ 0b00 @ addr`8 ; if FLAG_C: PC = addr
    bnc {addr: u8} => 0b011010 @ 0b00 @ addr`8 ; if !FLAG_C: PC = addr
    bn {addr: u8} => 0b011011 @ 0b00 @ addr`8 ; if FLAG_N: PC = addr
    bnn {addr: u8} => 0b011100 @ 0b00 @ addr`8 ; if !FLAG_N: PC = addr
    bo {addr: u8} => 0b011101 @ 0b00 @ addr`8 ; if FLAG_O: PC = addr
    bno {addr: u8} => 0b011110 @ 0b00 @ addr`8 ; if !FLAG_O: PC = addr
    blt {addr: u8} => 0b011111 @ 0b00 @ addr`8 ; if (FLAG_N ^ FLAG_O): PC = addr
    bgt {addr: u8} => 0b100000 @ 0b00 @ addr`8 ; if (FLAG_Z & (FLAG_N ^ FLAG_O)): PC = addr
    ble {addr: u8} => 0b100001 @ 0b00 @ addr`8 ; if FLAG_Z | (FLAG_N ^ FLAG_O): PC = addr
    bge {addr: u8} => 0b100010 @ 0b00 @ addr`8 ; if !(FLAG_N ^ FLAG_O): PC = addr

; }

; ---- Keyboard Instructions ---- {

    kp {dest: reg} => 0b100011 @ dest @ 0x00 ; dest = KEYBOARD_QUEUE.pop()

    kl {dest: reg} => 0b100100 @ dest @ 0x00 ; dest = KEYBOARD_QUEUE.length

    kcl => 0b100101 @ 0b00 @ 0x00 ; Clear KEYBOARD_QUEUE.

; }
    
; ---- Power Instructions ---- {

    pwd => 0b100110 @ 0b00 @ 0x00 ; Shut off the power.

    slp => 0b100110 @ 0b00 @ 0x01 ; Enter sleep mode.

; }

} ; #endruledef