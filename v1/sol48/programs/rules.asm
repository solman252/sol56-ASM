#once
#bankdef rules { outp = 0 * 0b0
    #bits 16
}

; ---- Subrules ---- {
    #subruledef REG {
        ; All registers are 16bit
        pc => 0x1 ; Program Counter
        iflags => 0x2 ; Result of ALU operations
        res => 0x3 ; Result of ALU operations
        ar => 0x4 ; General use register 1
        br => 0x5 ; General use register 2
        cr => 0x6 ; General use register 3
        dr => 0x7 ; General use register 4
        er => 0x8 ; General use register 5
        fr => 0x9 ; General use register 6
    }

    #subruledef IMM { ; An immediate 16bit value
        {v: i16} => v`16
    }

    #subruledef MEM { ; Memory addressed by the value in a register
        [{r: REG}] => r
    }

    #subruledef ADDR { ; Memory addressed by an immediate value
        [{v: u16}] => v`16
    }

    #subruledef CODE { ; An interrupt code (0x00 -> 0xFF)
        INT[{v: u8}] => v`8
    }

    #subruledef PORT { ; An IO port (0x00 -> 0xFF)
        IO[{v: u8}] => v`8
    }

    #subruledef FLAG {
        zf => 0xa ; Zero flag
        sf => 0xb ; Sign flag
        cf => 0xc ; Carry flag
        of => 0xd ; Overflow flag
        if => 0xe ; Interupt flag
        rf => 0xf ; Result flag
    }

    #subruledef TIME_ASPECT {
        uptime => 0x0
        ms => 0x1
        sec => 0x2
        min => 0x3
        hour => 0x4
        weekday => 0x5
        monthday => 0x6
        yearday => 0x7
        month => 0x8
        year => 0x9
    }

    #subruledef _ARG {
        {a: REG} => 0x1 @ a`16
        {a: IMM} => 0x2 @ a`16
        {a: MEM} => 0x3 @ a`16
        {a: ADDR} => 0x4 @ a`16
        {a: CODE} => 0x5 @ a`16
        {a: PORT} => 0x6 @ a`16
        {a: FLAG} => 0x7 @ a`16
        {a: TIME_ASPECT} => 0x8 @ a`16
    }

    ; Argument Type Masks {
        _NONE = 0x001 ; No argument
        _REG = 0x002 ; A register
        _IMM = 0x004 ; An immediate 16bit value
        _MEM = 0x008 ; Memory addressed by the value in a register
        _ADDR = 0x010 ; Memory addressed by an immediate value
        _CODE = 0x020 ; An interrupt code (0x00 -> 0xFF)
        _PORT = 0x040 ; An IO port (0x00 -> 0xFF)
        _FLAG = 0x080 ; A flag
        _TIME_ASPECT = 0x100 ; An aspect of the time
        _ANY = 0x1FF ; Any argument type
        _READABLE = _REG|_IMM|_MEM|_ADDR ; Argument types pointing to readable storage
        _WRITEABLE = _REG|_MEM|_ADDR ; Argument types pointing to writeable storage
    ; }

    #fn _op_parse_args(base, arg1_types, arg2_types, arg1, arg2) => {
        ; Takes in the base code, 2 type-masks, and 2 arguments, then constructs the final instruction binary.
        type1 = arg1[19:16]
        type2 = arg2[19:16]
        assert(arg1_types[type1:type1] == 1,"Argument 1 does not match the allowed argument types.")
        assert(arg2_types[type2:type2] == 1,"Argument 2 does not match the allowed argument types.")
        assert(!(( ; First argument is being written to, prevent overwright of program counter
            (base == 0x2a) || ; inc
            (base == 0x2b) || ; dec
            (base == 0x2c) || ; neg
            (base == 0x2d) ; abs
        ) && (type1 == 0x1) && (arg1 == (0x1 @ 0x1`16))),"The program counter is not writeable, try jumping instead.")
        assert(!(( ; Second argument is being written to, prevent overwright of program counter
            (base == 0x10) ; mov
        ) && (type2 == 0x1) && (arg2 == (0x1 @ 0x1`16))),"The program counter is not writeable, try jumping instead.")
        assert(!((base == 0x10) && (arg1 == arg2)),"The source and destination must not be the same.")
        base`8 @ type1`4 @ type2`4 @ arg1`16 @ arg2`16
    }

    #subruledef OPCODE {
        {opcode: u8} => opcode`8

        nop => 0x00
        time => 0x01

        mov => 0x10

        add => 0x20
        adc => 0x21
        sub => 0x22
        sbb => 0x23
        div => 0x24
        idiv => 0x25
        mul => 0x26
        imul => 0x27
        mod => 0x28
        imod => 0x29
        inc => 0x2a
        dec => 0x2b
        neg => 0x2c
        abs => 0x2d
        min => 0x2e
        max => 0x2f

        and => 0x30
        or => 0x31
        xor => 0x32
        not => 0x33
        nand => 0x34
        nor => 0x35
        xnor => 0x36

        shl => 0x40
        shr => 0x41
        sar => 0x42
        rol => 0x43
        ror => 0x44
        rcl => 0x45
        rcr => 0x46

        set => 0x50
        clr => 0x51
        cmp => 0x52
        test => 0x53

        jmp => 0x60
        jif => 0x61
        jnf => 0x62
        jlt => 0x63
        jle => 0x64
        jgt => 0x65
        jge => 0x66
        jbe => 0x67
        ja => 0x68

        hlt => 0x70
        int => 0x71
        intd => 0x72
        iret => 0x73

        pwd => 0x80

        debug msg enable => 0xa0
        debug msg disable => 0xa1
        debug msg whitelist => 0xa2
        debug msg blacklist => 0xa3
        debug msg whitelist all => 0xa4
        debug msg blacklist all => 0xa5
        debug read => 0xa6
    }
; }

#ruledef rules {
    ; ---- Special Instructions (0x0_) ---- {
        nop => _op_parse_args(0x00, _NONE, _NONE, 0, 0) ; Does nothing this cycle
        time {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x01, _TIME_ASPECT, _WRITEABLE, arg1, arg2) ; Copy an aspect of the time to another spot
        call {arg1: _ARG} => _op_parse_args(0x02, _READABLE, _NONE, arg1, 0) ; Call the procedure at the provided address
        res => _op_parse_args(0x03, _NONE, _NONE, 0, 0) ; Return from a procedure and restore flags
        ret => _op_parse_args(0x04, _NONE, _NONE, 0, 0) ; Return from a procedure
    ; }

    ; ---- Data Management (0x1_) ---- {
        mov {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x10, _READABLE|_PORT, _WRITEABLE|_PORT, arg1, arg2) ; Copy a value to another spot
        mc {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x11, _READABLE|_PORT, _WRITEABLE|_PORT, arg1, arg2) ; Copy a value to another spot if the carry flag is set
        mnc {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x12, _READABLE|_PORT, _WRITEABLE|_PORT, arg1, arg2) ; Copy a value to another spot if the carry flag is not set
        meq {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x13, _READABLE|_PORT, _WRITEABLE|_PORT, arg1, arg2) ; Copy a value to another spot if one value is equal to another (signed) (zero flag is set)
        mne {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x14, _READABLE|_PORT, _WRITEABLE|_PORT, arg1, arg2) ; Copy a value to another spot if one value is not equal to another (signed) (zero flag is not set)
        mlt {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x15, _READABLE|_PORT, _WRITEABLE|_PORT, arg1, arg2) ; Copy a value to another spot if one value is less than another (signed) (sign flag != overflow flag)
        mle {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x16, _READABLE|_PORT, _WRITEABLE|_PORT, arg1, arg2) ; Copy a value to another spot if one value is less than or equal to another (signed) (zero flag is set OR sign flag != overflow flag)
        mgt {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x17, _READABLE|_PORT, _WRITEABLE|_PORT, arg1, arg2) ; Copy a value to another spot if one value is greater than another (signed) (zero flag is not set AND sign flag == overflow flag)
        mge {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x18, _READABLE|_PORT, _WRITEABLE|_PORT, arg1, arg2) ; Copy a value to another spot if one value is greater than or equal to another (signed) (sign flag == overflow flag)
        mb {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x19, _READABLE|_PORT, _WRITEABLE|_PORT, arg1, arg2) ; Copy a value to another spot if one value is less than another (unsigned) (carry flag is set)
        mbe {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x1a, _READABLE|_PORT, _WRITEABLE|_PORT, arg1, arg2) ; Copy a value to another spot if one value is less than or equal to another (unsigned) (carry flag is set OR zero flag is set)
        ma {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x1b, _READABLE|_PORT, _WRITEABLE|_PORT, arg1, arg2) ; Copy a value to another spot if one value is greater than another (unsigned) (carry flag is not set AND zero flag is not set)
        mae {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x1c, _READABLE|_PORT, _WRITEABLE|_PORT, arg1, arg2) ; Copy a value to another spot if one value is greater than or equal to another (unsigned) (carry flag is not set)
    ; }

    ; ---- Arithmetic (0x2_) ---- {
        add {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x20, _READABLE, _READABLE, arg1, arg2) ; Add 2 values together
        adc {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x21, _READABLE, _READABLE, arg1, arg2) ; Add 2 values together with carry in
        sub {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x22, _READABLE, _READABLE, arg1, arg2) ; Subtract one value from another
        sbb {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x23, _READABLE, _READABLE, arg1, arg2) ; Subtract one value from another with borrow
        div {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x24, _READABLE, _READABLE, arg1, arg2) ; Devide one unsigned value from another (result being the quotient)
        idiv {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x25, _READABLE, _READABLE, arg1, arg2) ; Devide one signed value from another (result being the quotient)
        mul {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x26, _READABLE, _READABLE, arg1, arg2) ; Multiply 2 unsigned values, with the result as the lower 16 bits
        imul {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x27, _READABLE, _READABLE, arg1, arg2) ; Multiply 2 signed values, with the result as the lower 16 bits
        mul {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x28, _READABLE, _READABLE, arg1, arg2) ; Multiply 2 unsigned values, with the result as the higher 16 bits
        imul {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x29, _READABLE, _READABLE, arg1, arg2) ; Multiply 2 signed values, with the result as the higher 16 bits
        mod {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x2a, _READABLE, _READABLE, arg1, arg2) ; Modulo one unsigned value by another
        imod {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x2b, _READABLE, _READABLE, arg1, arg2) ; Modulo one signed value by another
        neg {arg1: _ARG} => _op_parse_args(0x2c, _READABLE, _NONE, arg1, 0) ; Negate a value (positive -> negative and vice versa)
        abs {arg1: _ARG} => _op_parse_args(0x2d, _READABLE, _NONE, arg1, 0) ; Take the absolute of a value (negative -> positive, not vice-verca)
        inc {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x2e, _REG, _IMM, arg1, arg2) ; Increment a register by an amount
        inc {arg1: _ARG} => asm { inc {arg1}, 1 } ; A macro to allow no amount to be passed, making the default 1.
        dec {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x2f, _REG, _IMM, arg1, arg2) ; Decrement a register by an amount
        dec {arg1: _ARG} => asm { dec {arg1}, 1 } ; A macro to allow no amount to be passed, making the default 1.
    ; }

    ; ---- Bitwise Logic (0x3_) ---- {
        and {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x30, _READABLE, _READABLE, arg1, arg2) ; Perform a bitwise logical and operation on 2 values
        or {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x31, _READABLE, _READABLE, arg1, arg2) ; Perform a bitwise logical or operation on 2 values
        xor {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x32, _READABLE, _READABLE, arg1, arg2) ; Perform a bitwise logical xor operation on 2 values
        not {arg1: _ARG} => _op_parse_args(0x33, _READABLE, _NONE, arg1, 0) ; Perform a bitwise logical not operation on a value
        nand {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x34, _READABLE, _READABLE, arg1, arg2) ; Perform a bitwise logical nand operation on 2 values
        nor {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x35, _READABLE, _READABLE, arg1, arg2) ; Perform a bitwise logical nor operation on 2 values
        xnor {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x36, _READABLE, _READABLE, arg1, arg2) ; Perform a bitwise logical xnot operation on 2 values
    ; }

    ; ---- Bit Shifting / Rotation (0x4_) ---- {
        shl {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x40, _READABLE, _READABLE, arg1, arg2) ; Shift the bits in a value to the left
        sal {arg1: _ARG}, {arg2: _ARG} => asm { shl {arg1}, {arg2} } ; A macro for shl
        shr {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x41, _READABLE, _READABLE, arg1, arg2) ; Shift the bits in a value to the right
        sar {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x42, _READABLE, _READABLE, arg1, arg2) ; Shift the bits in a value to the right, copying the sign bit
        rol {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x43, _READABLE, _READABLE, arg1, arg2) ; Rotate the bits in a value to the left
        ror {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x44, _READABLE, _READABLE, arg1, arg2) ; Rotate the bits in a value to the right
        rcl {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x45, _READABLE, _READABLE, arg1, arg2) ; Rotate the bits in a value to the left, with carry in
        rcr {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x46, _READABLE, _READABLE, arg1, arg2) ; Rotate the bits in a value to the right, with carry in
    ; }

    ; ---- Flags (0x5_) ---- {
        set {arg1: _ARG} => _op_parse_args(0x50, _FLAG, _NONE, arg1, 0) ; Set the state of a flag to true
        clr {arg1: _ARG} => _op_parse_args(0x51, _FLAG, _NONE, arg1, 0) ; Set the state of a flag to false
        cpf {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x52, _FLAG, _FLAG, arg1, arg2) ; Copy the state of one flag to another
        cmp {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x53, _READABLE, _READABLE, arg1, arg2) ; Set the state of the flags as if a "sub" instruction had occurred
        test {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x54, _READABLE, _READABLE, arg1, arg2) ; Set the state of the flags as if an "and" instruction had occurred
        set {arg1: _ARG}, 1 => asm { set {arg1} } ; A macro for set
        set {arg1: _ARG}, 0 => asm { clr {arg1} } ; A macro for clr
    ; }

    ; ---- Jumps (0x6_) ---- {
        jmp {arg1: _ARG} => _op_parse_args(0x60, _READABLE, _NONE, arg1, 0) ; Jump to the provided address
        jif {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x61, _FLAG, _READABLE, arg1, arg2) ; Jump to the provided address if the provided flag is set
        jnf {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x62, _FLAG, _READABLE, arg1, arg2) ; Jump to the provided address if the provided flag is not set
        jeq {arg1: _ARG} => asm { jif zf, {arg1} } ; Jump to the provided address if one value is equal to another (signed) (zero flag is set)
        jne {arg1: _ARG} => asm { jnf zf, {arg1} } ; Jump to the provided address if one value is not equal to another (signed) (zero flag is not set)
        jlt {arg1: _ARG} => _op_parse_args(0x63, _READABLE, _NONE, arg1, 0) ; Jump to the provided address if one value is less than another (signed) (sign flag != overflow flag)
        jle {arg1: _ARG} => _op_parse_args(0x64, _READABLE, _NONE, arg1, 0) ; Jump to the provided address if one value is less than or equal to another (signed) (zero flag is set OR sign flag != overflow flag)
        jgt {arg1: _ARG} => _op_parse_args(0x65, _READABLE, _NONE, arg1, 0) ; Jump to the provided address if one value is greater than another (signed) (zero flag is not set AND sign flag == overflow flag)
        jge {arg1: _ARG} => _op_parse_args(0x66, _READABLE, _NONE, arg1, 0) ; Jump to the provided address if one value is greater than or equal to another (signed) (sign flag == overflow flag)
        jb {arg1: _ARG} => asm { jif cf, {arg1} } ; Jump to the provided address if one value is less than another (unsigned) (carry flag is set)
        jbe {arg1: _ARG} => _op_parse_args(0x67, _READABLE, _NONE, arg1, 0) ; Jump to the provided address if one value is less than or equal to another (unsigned) (carry flag is set OR zero flag is set)
        ja {arg1: _ARG} => _op_parse_args(0x68, _READABLE, _NONE, arg1, 0) ; Jump to the provided address if one value is greater than another (unsigned) (carry flag is not set AND zero flag is not set)
        jae {arg1: _ARG} => asm { jnf cf, {arg1} } ; Jump to the provided address if one value is greater than or equal to another (unsigned) (carry flag is not set)
    ; }

    ; ---- Interrupts (0x7_) ---- {
        hlt {arg1: _ARG} => _op_parse_args(0x70, _CODE, _NONE, arg1, 0) ; Halt execution untill an interrupt with the provided interrupt code occurs
        hlt => asm { hlt INT[0] } ; Halt execution untill any interrupt occurs
        hlt {code: u8} => asm { hlt INT[{code}] } ; A macro to allow an immediate value to be entered as the interrupt code without putting INT[] around it
        int {arg1: _ARG} => _op_parse_args(0x71, _CODE, _NONE, arg1, 0) ; Call an interrupt with the provided code
        int {code: u8} => asm { int INT[{code}] } ; A macro to allow an immediate value to be entered as the interrupt code without putting INT[] around it
        intd {arg1: _ARG}, {arg2: _ARG} => _op_parse_args(0x72, _CODE, _READABLE, arg1, arg2) ; Define the address in memory to jump to when an interrupt with the provided code occurs
        intd {code: u8}, {arg2: _ARG} => asm { intd INT[{code}], {arg2} } ; A macro to allow an immediate value to be entered as the interrupt code without putting INT[] around it
        ires => _op_parse_args(0x73, _NONE, _NONE, 0, 0) ; Return from an interrupt and restore flags
        iret => _op_parse_args(0x74, _NONE, _NONE, 0, 0) ; Return from an interrupt
    ; }

    ; ---- Power (0x8_) ---- {
        pwd => _op_parse_args(0x80, _NONE, _NONE, 0, 0) ; Shut the device off
    ; }

    ; ---- Video (0x9_) ---- {
        ; vram {start}
        ; vmode {text | rgb}
    ; }

    ; ---- Debug ---- {
        debug msg enable => _op_parse_args(0xa0, _NONE, _NONE, 0, 0) ; Enable debug message printing
        debug msg disable => _op_parse_args(0xa1, _NONE, _NONE, 0, 0) ; Disable debug message printing
        debug msg whitelist {arg1: OPCODE} => _op_parse_args(0xa2, _IMM, _NONE, 0x2 @ arg1`16, 0) ; Allow debug message printing for the provided opcode.
        debug msg blacklist {arg1: OPCODE} => _op_parse_args(0xa3, _IMM, _NONE, 0x2 @ arg1`16, 0) ; Disallow debug message printing for the provided opcode.
        debug msg whitelist all => _op_parse_args(0xa4, _NONE, _NONE, 0, 0) ; Allow debug message printing for all opcodes.
        debug msg blacklist all => _op_parse_args(0xa5, _NONE, _NONE, 0, 0) ; Disallow debug message printing for all opcodes.
        debug statemsg enable => asm {
            debug msg whitelist 0xa0
            debug msg whitelist 0xa1
            debug msg whitelist 0xa2
            debug msg whitelist 0xa3
            debug msg whitelist 0xa4
            debug msg whitelist 0xa5
        } ; Enable debug enable/disable message printing
        debug statemsg disable => asm {
            debug msg blacklist 0xa0
            debug msg blacklist 0xa1
            debug msg blacklist 0xa2
            debug msg blacklist 0xa3
            debug msg blacklist 0xa4
            debug msg blacklist 0xa5
        } ; Disable debug enable/disable message printing
        debug read {arg1: _ARG} => _op_parse_args(0xa6, _ANY, _NONE, arg1, 0) ; Read the value of something
    ; }
}