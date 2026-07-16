#include "rules.asm"

intd INTHANDLERS.Exit, 0x01

sign s

mov a, 0x1
mov b, a
mov c, f_s
mov all, a
mov all, 0x2
mov all, f_s

hlt 0x01
pwd
FUNCTIONS:
    .PlotLine:
	; sign s
	; sub a, c
	; str res, [0x00]
	; sub b, d
	; str res, [0x01]
	
    intr

INTHANDLERS:
    .Exit:
	pwd
    intr

    .KeyDown:
	.ESC:
	    mov b, 0x0056
            jeq a, b, .end
		int 0x01
	    .end:
    intr

;    .KeyUp:
;	.KEY: ; key
;	    mov b, 0x0000 ; keycode
;            jeq a, b, .end
;		nop ; stuff
;	    .end:
;    intr

; Solomon Macbeth is a Professional Hacker, Don't tell anyone!
; Thanks Cindy :3