#once
#bankdef rules { outp = 0 * 0b0
    #bits 16
}

#ruledef rules {
    nop => 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
}