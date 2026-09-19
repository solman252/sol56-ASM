from enum import Enum

class ARGTYPE(Enum):
    NONE        = 0x0
    REG         = 0x1
    IMM         = 0x2
    MEM         = 0x3
    ADDR        = 0x4
    CODE        = 0x5
    PORT        = 0x6
    FLAG        = 0x7
    TIME_ASPECT = 0x8

class REG(Enum):
    pc  = 0x1 # Program Counter
    iflags = 0x2 # Result of ALU operations
    res = 0x3 # Result of ALU operations
    a   = 0x4 # General use register 1
    b   = 0x5 # General use register 2
    c   = 0x6 # General use register 3
    d   = 0x7 # General use register 4
    e   = 0x8 # General use register 5
    f   = 0x9 # General use register 6

class FLAG(Enum):
    z = 0xa # Zero flag
    s = 0xb # Sign flag
    c = 0xc # Carry flag
    o = 0xd # Overflow flag
    i = 0xe # Interupt flag
    r = 0xf # Result flag

class TIME_ASPECT(Enum):
    uptime   = 0x0
    ms       = 0x1
    sec      = 0x2
    min      = 0x3
    hour     = 0x4
    weekday  = 0x5
    monthday = 0x6
    yearday  = 0x7
    month    = 0x8
    year     = 0x9