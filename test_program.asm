#include "rules.asm"

; ---- Special Instructions ----
    nop
    hlt
    hlt 0x05
; }

; ---- ALU Operations ----
    sign s
    sign u

    carry 0
    carry 1

    add a, b
    sub b, c
    and c, d
    or d, a
    xor a, b
    xnor b, c
    bsl d
    bsr a
    brl b
    brr c
; }

; ---- Register Management ---- {
    mov a, b
    mov a, res
    mov a, 0x05
    ldr a, [b]
    ldr a, [res]
    ldr a, [0x05]
    str a, [b]
    str a, [res]
    str a, [0x05]
    str 0x05, [b]
; }

; ---- Screen Instructions ---- {
    vid r, b
    vid r, 0xFF
    vid g, b
    vid g, 0xFF
    vid b, b
    vid b, 0xFF
    vid rgb, b
    vid rgb, 0xFF
    vid addr, b
    vid addr, 0x05
    vwr
    vcl
    vfl
; }

; ---- Branch Instructions ---- {
    jmp a
    bz a
    bnz a
    bc a
    bnc a
    bn a
    bnn a
    bo a
    bno a
    blt a
    bgt a
    ble a
    bge a
    jmp 0x05
    bz 0x05
    bnz 0x05
    bc 0x05
    bnc 0x05
    bn 0x05
    bnn 0x05
    bo 0x05
    bno 0x05
    blt 0x05
    bgt 0x05
    ble 0x05
    bge 0x05
; }

; ---- Keyboard Instructions ---- {
    kp a
    kl a
    kcl
; }

; ---- Power Instructions ---- {
    slp
    pwd
; }