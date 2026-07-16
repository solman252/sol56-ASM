#include "rules.asm"

intd INTHANDLERS.Exit, 0x01
intd INTHANDLERS.KeyDown, 0x02
; intd INTHANDLERS.KeyUp, 0x03
intd FUNCTIONS.PlotLine, 0x10

; vid mode, rgb

; mov vid_color, 0xFF4488 ; pinkish

; ; p1 = top left
; mov a, 0x00
; mov b, 0x00

; ; p2 = bottom right
; mov c, 0xFF
; mov d, 0xFF

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