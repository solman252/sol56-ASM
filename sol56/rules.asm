#once
#bankdef rules { outp = 0 * 0b0
    #bits 56 ; Intstuction bitcount
}

; ---- Subrules ---- {
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

    #subruledef time_modes {
        uptime => 0x0
        ms => 0x1
        sec => 0x2
        min => 0x3
        hour => 0x4
        weekday => 0x5
        monthday => 0x6
        yearday => 0x6
        month => 0x7
        year => 0x8
    }


; }

#ruledef {
    ; ---- Special Instructions ---- {

        ; -- NOP -- {
            ; No operation, does nothing this cycle.
            nop =>           0x00 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

            ; You can use this arguement to put a register into without worry of it affecting anything.
            nop {r1: reg} => 0x00 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ 0x0000

            ; You can use this arguement to put 40 bits of custom data in without any worry of it affecting anything.
            nop {v1: i40} => 0x00 @ 0x02 @ v1`40

            ; - Macros - {
                debug {r1: reg} => asm { nop {r1} }
                debug {v1: i40} => asm { nop {v1} }

                ; Specefically for the emulator, enable debug printing.
                debug enable => asm { nop 0x1FCE2A8739 }
                ; Specefically for the emulator, disable debug printing.
                debug disable => asm { nop 0x1FCE2A873C }
            ; }
        
        ; }

        ; -- INTD -- {
            ; Define an interrupt handler with the left value being the handler's address and the right value being the interrupt code.
            intd {r1: reg}, [{r2: reg}] => 0x01 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000
            intd {r1: reg}, [{v2: u8}] =>  0x01 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ 0x00 @ v2`8
            intd {v1: u16}, [{r2: reg}] => 0x01 @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000
            intd {v1: u16}, [{v2: u8}] =>  0x01 @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ 0x00 @ v2`8

            ; Undefine all interrupt handlers.
            intd clear => 0x01 @ 0x04 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

            ; - Macros - {
                intd reset => asm { intd clear }
            ; }
        ; }

        ; -- INTR -- {
            ; Return back from handling an interrupt to main code execution and restore all registers and flags to their pre-interrupt state.
            intr => 0x02 @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

            ; Return back from handling an interrupt to main code execution.
            intr pc => 0x02 @ 0x10 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

            ; Restore a register to it's pre-interrupt state.
            intr reg, {r: reg} => 0x20 @ 0x01 @ r @ 0x0 @ 0x0000 @ 0x0000

            ; Restore all registers to their pre-interrupt state.
            intr reg => 0x02 @ 0x21 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

            ; Restore a flag to it's pre-interrupt state.
            intr flag, {f: flag} => 0x30 @ 0x01 @ f @ 0x0 @ 0x0000 @ 0x0000

            ; Restore all flags to their pre-interrupt state.
            intr flag => 0x02 @ 0x31 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

            ; Restore all registers and flags to their pre-interrupt state.
            intr state => 0x02 @ 0x40 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

            ; - Macros - {
                intr ret => asm { intr pc }
                intr return => asm { intr pc }

                intr reg, all => asm { intr reg }
                intr flag, all => asm { intr flag }

                intr rest => asm { intr state }
                intr restore => asm { intr state }
            ; }
        ; }

        ; -- INT {
            ; Generate an interrupt signal with the arguement as the interrupt code.
            int {r1: reg} => 0x03 @ 0x00 @ r1  @ 0x0 @ 0x0000      @ 0x000
            int {v1: u8} =>  0x03 @ 0x01 @ 0x0 @ 0x0 @ 0x00 @ v1`8 @ 0x0000
        ; }

        ; -- HLT -- {
            ; Halt CPU execution until an interrupt signal is received.
            hlt =>           0x04 @ 0x00 @ 0x0 @ 0x0 @ 0x0000      @ 0x0000

            ; Argument may be used to specify an interrupt signal to halt until.
            hlt {r1: reg} => 0x04 @ 0x01 @ r1  @ 0x0 @ 0x0000      @ 0x0000
            hlt {v1: u8} =>  0x04 @ 0x02 @ 0x0 @ 0x0 @ 0x00 @ v1`8 @ 0x0000
        ; }

        ; -- TIME -- {
            ; Store an aspect of the time (see time_modes) into a register.
            time {m: time_modes}, {r1: reg} => 0x05 @ 0x0 @ m @ r1 @ 0x0 @ 0x0000 @ 0x0000
        ;}

        ; - Macros - {
            clr state => asm {
                mov all, 0
                flag all, 0
            }

            reset => asm {
                intd clear
                clr state
                jmp 0
            }
        ; }
    ; }

    ; ---- ALU Operations ---- {
        ; For all ALU operations:
        ; Result is written to the RES register,
        ; FLAG_S will determine if in signed mode or not,
        ; FLAG_C acts as carry in / out,
        ; FLAG_Z will show whether the result is 0,
        ; FLAG_N will show whether the result is negative (if in signed mode),
        ; FLAG_O will show whether an overflow occurred.

        ; -- FLAG -- {
            ; Set the value of a flag
            flag {f: flag}, {v: u1} => 0x06 @ f   @ 0b000 @ v`1 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

            ; Set the value of all flags
            flag all, {v: u1}       => 0x06 @ 0x5 @ 0b000 @ v`1 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000

            ; - Macros {
                sign u => asm { flag f_s, 0 }
                sign 0 => asm { flag f_s, 0 }
                sign s => asm { flag f_s, 1 }
                sign 1 => asm { flag f_s, 1 }

                carry 0 => asm { flag f_c, 0 }
                carry 1 => asm { flag f_c, 1 }
            ; }
        ; }

        ; -- ADD -- {
            ; Add 2 values together and store the result in the RES register.
            add {r1: reg}, {r2: reg} => 0x07 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000
            add {r1: reg}, {v2: i16} => 0x07 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16
            add {v1: i16}, {r2: reg} => 0x07 @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000
            add {v1: i16}, {v2: i16} => 0x07 @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16 

            ; Same as add, but with carry in.
            addc {r1: reg}, {r2: reg} => 0x07 @ 0x04 @ r1  @ r2  @ 0x0000 @ 0x0000
            addc {r1: reg}, {v2: i16} => 0x07 @ 0x05 @ r1  @ 0x0 @ 0x0000 @ v2`16
            addc {v1: i16}, {r2: reg} => 0x07 @ 0x06 @ 0x0 @ r2  @ v1`16  @ 0x0000
            addc {v1: i16}, {v2: i16} => 0x07 @ 0x07 @ 0x0 @ 0x0 @ v1`16  @ v2`16
        ; }

        ; -- SUB -- {
            ; Subtract one value from another and store the result in the RES register.
            ; If ALU is in unsigned mode, FLAG_C will show whether a carry occured.
            ; If ALU is in signed mode, FLAG_O will show whether a overflow occured.
            sub {r1: reg}, {r2: reg} => 0x08 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000
            sub {r1: reg}, {v2: i16} => 0x08 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16
            sub {v1: i16}, {r2: reg} => 0x08 @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000
            sub {v1: i16}, {v2: i16} => 0x08 @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16
        ; }

        ; -- AND -- {
            ; Perform a bitwise and between 2 values and store the result in the RES register.
            and {r1: reg}, {r2: reg} => 0x09 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000
            and {r1: reg}, {v2: i16} => 0x09 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16
            and {v1: i16}, {r2: reg} => 0x09 @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000
            and {v1: i16}, {v2: i16} => 0x09 @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16
        ; }

        ; -- OR -- {
            ; Perform a bitwise or between 2 values and store the result in the RES register.
            or {r1: reg}, {r2: reg} => 0x0A @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000
            or {r1: reg}, {v2: i16} => 0x0A @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16
            or {v1: i16}, {r2: reg} => 0x0A @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000
            or {v1: i16}, {v2: i16} => 0x0A @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16
        ; }
        
        ; -- XOR -- {
            ; Perform a bitwise xor between 2 values and store the result in the RES register.
            xor {r1: reg}, {r2: reg} => 0x0B @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000
            xor {r1: reg}, {v2: i16} => 0x0B @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16
            xor {v1: i16}, {r2: reg} => 0x0B @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000
            xor {v1: i16}, {v2: i16} => 0x0B @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16
        ; }

        ; -- XNOR -- {
            ; Perform a bitwise xnor between 2 values and store the result in the RES register.
            xnor {r1: reg}, {r2: reg} => 0x0C @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000
            xnor {r1: reg}, {v2: i16} => 0x0C @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16
            xnor {v1: i16}, {r2: reg} => 0x0C @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000
            xnor {v1: i16}, {v2: i16} => 0x0C @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16
        ; }

        ; -- BSL -- {
            ; Bit-shift a value by another value to the left and store the result in the RES register.
            bsl {r1: reg}, {r2: reg} => 0x0D @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000
            bsl {r1: reg}, {v2: u16} => 0x0D @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16
            bsl {v1: i16}, {r2: reg} => 0x0D @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000
            bsl {v1: i16}, {v2: u16} => 0x0D @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16
            bsl {r1: reg} => asm { bsl {r1}, 1 }
        ; }

        ; -- BSR -- {
            ; Bit-shift a value by another value to the right and store the result in the RES register.
            bsr {r1: reg}, {r2: reg} => 0x0E @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000
            bsr {r1: reg}, {v2: u16} => 0x0E @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16
            bsr {v1: i16}, {r2: reg} => 0x0E @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000
            bsr {v1: i16}, {v2: u16} => 0x0E @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16
            bsr {r1: reg} => asm { bsr {r1}, 1 }
        ; }

        ; -- BRL -- {
            ; Bit-rotate a value by another value to the left and store the result in the RES register.
            brl {r1: reg}, {r2: reg} => 0x0F @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000
            brl {r1: reg}, {v2: u16} => 0x0F @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16
            brl {v1: i16}, {r2: reg} => 0x0F @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000
            brl {v1: i16}, {v2: u16} => 0x0F @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16
            brl {r1: reg} => asm { brl {r1}, 1 }
        ; }

        ; -- BRR -- {
            ; Bit-rotate a value by another value to the right and store the result in the RES register.
            brr {r1: reg}, {r2: reg} => 0x10 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000
            brr {r1: reg}, {v2: u16} => 0x10 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16
            brr {v1: i16}, {r2: reg} => 0x10 @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000
            brr {v1: i16}, {v2: u16} => 0x10 @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16
            brr {r1: reg} => asm { brl {r1}, 1 }
        ; }

    ; }

    ; ---- Register / Memory Management ---- {

        ; -- MOV -- {
            ; Copy the right value into the left register.
            mov {r1: reg}, {r2: reg} => 0x11 @ 0x00 @ r1 @ r2  @ 0x0000 @ 0x0000
            mov {r1: reg}, {v2: i16} => 0x11 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2`16
            mov {r1: reg}, {f: flag} => 0x11 @ 0x02 @ r1 @ f   @ 0x0000 @ 0x0000

            ; Copy the right value into all registers.
            mov all, {r2: reg} => 0x11 @ 0x00 @ 0x0 @ r2  @ 0x0000 @ 0x0000
            mov all, {v2: i16} => 0x11 @ 0x01 @ 0x0 @ 0x0 @ 0x0000 @ v2`16
            mov all, {f: flag} => 0x11 @ 0x02 @ 0x0 @ f   @ 0x0000 @ 0x0000
        ; }

        ; -- LDR -- {
            ; Copy the value in RAM at the right address into the left register.
            ldr {r1: reg}, [{r2: reg}] => 0x12 @ 0x00 @ r1 @ r2  @ 0x0000 @ 0x0000
            ldr {r1: reg}, [{v2: u16}] => 0x12 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ v2`16

            ; Copy the value in RAM at the right address into all registers.
            ldr all, {r2: reg} => 0x12 @ 0x00 @ 0x0 @ r2  @ 0x0000 @ 0x0000
            ldr all, {v2: i16} => 0x12 @ 0x01 @ 0x0 @ 0x0 @ 0x0000 @ v2`16

            ; - Macros - {
                mov {r1: reg}, [{r2: reg}] => asm { ldr {r1}, [{r2}] }
                mov {r1: reg}, [{v2: u16}] => asm { ldr {r1}, [{v2}] }
            ; }

        ; }

        ; -- str -- {
            ; Store the left value into RAM at the right address.
            str {r1: reg}, [{r2: reg}] => 0x13 @ 0x00 @ r1  @ r2  @ 0x0000 @ 0x0000
            str {r1: reg}, [{v2: u16}] => 0x13 @ 0x01 @ r1  @ 0x0 @ 0x0000 @ v2`16
            str {v1: i16}, [{r2: reg}] => 0x13 @ 0x02 @ 0x0 @ r2  @ v1`16  @ 0x0000
            str {v1: i16}, [{v2: u16}] => 0x13 @ 0x03 @ 0x0 @ 0x0 @ v1`16  @ v2`16

            ; - Macros - {
                mov [{r1: reg}], {r2: reg} => asm { str r2, [r1]}
                mov [{v1: u16}], {r2: reg} => asm { str r2, [v1]}
                mov [{r1: reg}], {v2: i16} => asm { str v2, [r1]}
                mov [{v1: i16}], {v2: i16} => asm { str v2, [v1]}
            ; }

        ; }

    ; }

    ; ---- Jump Instructions ---- {

        ; -- JMP -- {
            ; Unconditionally jump to an address.
            jmp {r1: reg} => 0x14 @ 0x00 @ r1  @ 0x0 @ 0x0000 @ 0x0000
            jmp {v1: u16} => 0x14 @ 0x01 @ 0x0 @ 0x0 @ v1`16  @ 0x0000
        ; }

        ; -- JIF -- {
            ; Conditionally jump to an address if a flag is set to true.
            jif {f: flag}, {r1: reg} => 0x15 @ 0x0 @ f @ r1  @ 0x0 @ 0x0000 @ 0x0000
            jif {f: flag}, {v1: u16} => 0x15 @ 0x1 @ f @ 0x0 @ 0x0 @ v1`16  @ 0x0000
        ; }

        ; -- JNOT -- {
            ; Conditionally jump to an address if a flag is set to false.
            jnot {f: flag}, {r1: reg} => 0x16 @ 0x0 @ f @ r1  @ 0x0 @ 0x0000 @ 0x0000
            jnot {f: flag}, {v1: u16} => 0x16 @ 0x1 @ f @ 0x0 @ 0x0 @ v1`16  @ 0x0000
        ; }

        ; -- JEQ -- {
            ; Conditionally jump to an address if the value in one register is equal to another.
            jeq {r1: reg}, {r2: reg}, {v1: u16} => 0x17 @ 0x00 @ r1 @ r2  @ v1`16  @ 0x0000

            ; Same as jeq, but compare one register's value to 0.
            jeqz {r1: reg}, {v1: u16}           => 0x17 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ 0x0000
        ; }

        ; -- JLT -- {
            ; Conditionally jump to an address if the value in one register is less than another.
            jlt {r1: reg}, {r2: reg}, {v1: u16} => 0x18 @ 0x00 @ r1 @ r2  @ v1`16  @ 0x0000

            ; Same as jlt, but compare one register's value to 0.
            jltz {r1: reg}, {v1: u16}           => 0x18 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ 0x0000
        ; }

        ; -- JGT -- {
            ; Conditionally jump to an address if the value in one register is greater than another.
            jgt {r1: reg}, {r2: reg}, {v1: u16} => 0x19 @ 0x00 @ r1 @ r2  @ v1`16  @ 0x0000

            ; Same as jgt, but compare one register's value to 0.
            jgtz {r1: reg}, {v1: u16}           => 0x19 @ 0x01 @ r1 @ 0x0 @ 0x0000 @ 0x0000
        ; }

        ; -- JLE -- {
            ; Conditionally jump to an address if the value in one register is less than or equal to another.
            jle {r1: reg}, {r2: reg}, {v1: u16} => 0x1A @ 0x00 @ r1 @ r2  @ v1`16  @ 0x0000

            ; Same as jle, but compare one register's value to 0.
            jlez {r1: reg}, {v1: u16}           => 0x1A @ 0x01 @ r1 @ 0x0 @ 0x0000 @ 0x0000
        ; }

        ; -- JGE -- {
            ; Conditionally jump to an address if the value in one register is greater than or equal to another.
            jge {r1: reg}, {r2: reg}, {v1: u16} => 0x1B @ 0x00 @ r1 @ r2  @ v1`16  @ 0x0000

            ; Same as jge, but compare one register's value to 0.
            jgez {r1: reg}, {v1: u16}           => 0x1B @ 0x01 @ r1 @ 0x0 @ 0x0000 @ 0x0000
        ; }
    ; }
        
    ; ---- Power Instructions ---- {

        ; -- PWD -- {
            ; Shut off the power supply.
            pwd => 0x1C @ 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
        ; }

    ; }

    ; ---- Video Instructions ---- {

    ; }

}