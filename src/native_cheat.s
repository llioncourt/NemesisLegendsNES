; Silicon Forge cheat menu (CP0013). Konami Code on the title or while paused.
; The menu is a separate mode (5) drawn with the HUD font through the HUD2 row
; mailbox; every action goes through the real loaders (NewGame, LoadStage,
; RestoreGameScreen), never through parallel debug paths.
.setcpu "6502"
.include "native.inc"
.include "campaign.inc"
.include "longbranch.inc"
.include "actors.inc"
.import HideSprites, ClearPPU, NewGame, LoadStage, RestoreGameScreen, LoadDataBank
.import Flow_State, GamePace_Mode, GamePace_Phase, GamePace_Edges
.export CheatCode, CheatOpen, CheatFrame, CheatDebugRow, Cheat_State

ITEMS=17
ROW_TITLE=3
ROW_FIRST=5
; value types
VT_ONOFF=0
VT_LIVES=1
VT_GAME=2
VT_DEC=3
VT_CHECK=4
VT_PACE=5
VT_HEX=6
VT_PRESS=7

.segment "BSS"
Cheat_State:
cheat_seq:      .res 1   ; Konami Code progress 0..9
cheat_from:     .res 1   ; mode when opened: 0 title, 2 pause
cheat_cursor:   .res 1
cheat_draw:     .res 1   ; next row to upload (0..ITEMS), ITEMS+1 = idle
cheat_action:   .res 1
cheat_vals:     .res ITEMS ; one value byte per item
cheat_opened:   .res 1   ; QA counter
CHEAT_END:

; ------------------------------------------------------- game-time code (bank 7)
; Mapped at $A000 whenever the main loop runs; CheatApply switches only $5114.
.segment "ACTORS"
KonamiSeq: .byte BTN_UP,BTN_UP,BTN_DOWN,BTN_DOWN,BTN_LEFT,BTN_RIGHT,BTN_LEFT,BTN_RIGHT,BTN_B,BTN_A
; C set when the ten-press sequence completed on this frame.
CheatCode:
 lda pressed
 beq @no
 ldx cheat_seq
 cmp KonamiSeq,x
 bne @mismatch
 inx
 cpx #10
 bcc @store
 lda #0
 sta cheat_seq
 sec
 rts
@mismatch:
 ldx #0
 cmp KonamiSeq
 bne @store
 inx
@store:
 stx cheat_seq
@no:
 clc
 rts

CheatOpen:
 sei
 inc cheat_opened
 lda mode
 sta cheat_from
 lda #5
 sta mode
 lda #0
 sta screenon
 sta $2000
 sta $2001
 sta $5204
 sta column_pending
 sta hud_pending
 sta hud2_pending
 sta cheat_cursor
 sta cheat_draw
 sta cheat_action
 sta camera
 lda #$89
 sta $5114
 sta bank8000
 jsr HideSprites
 jsr ClearPPU
 bit $2002
 lda #$3f
 sta $2006
 lda #0
 sta $2006
 ldx #0
@pal:
 lda #$0f
 cpx #3
 bne :+
 lda #$30
:
 sta $2007
 inx
 cpx #32
 bne @pal
 ; Seed the menu from the live game when opened from pause.
 ldx #ITEMS-1
 lda #0
@clear:
 sta cheat_vals,x
 dex
 bpl @clear
 lda qa_flags
 and #1
 sta cheat_vals+0
 lda cheat_flags
 and #1
 sta cheat_vals+1
 lda chapter
 bne :+
 lda #1
:
 sta cheat_vals+2
 lda stage_id
 bne :+
 lda #1
:
 sta cheat_vals+3
 lda player_speed
 sta cheat_vals+5
 lda power_missile
 sta cheat_vals+6
 lda power_double
 sta cheat_vals+7
 lda power_laser
 sta cheat_vals+8
 lda power_options
 sta cheat_vals+9
 lda power_shield
 beq :+
 lda #1
:
 sta cheat_vals+10
 lda GamePace_Mode
 sta cheat_vals+11
 lda #$aa
 sta cheat_vals+12
 lda cheat_flags
 and #2
 beq :+
 lda #1
:
 sta cheat_vals+13
 lda #0
 sta $2005
 sta $2005
 lda #1
 sta screenon
 lda #$a0
 sta $2000
 lda #$0a
 sta $2001
 cli
 rts

; Apply the menu and leave. Entered by jmp from the bank-9 frame code; returns
; to Main's caller. A = action (1 start/resume, 2 warp to end zone, 3 restart).
CheatApply:
 sta cheat_action
 lda qa_flags
 and #$fe
 ora cheat_vals+0
 sta qa_flags
 lda cheat_flags
 and #$fc
 ora cheat_vals+1
 sta s0
 lda cheat_vals+13
 asl a
 ora s0
 sta cheat_flags
 lda cheat_vals+11
 sta GamePace_Mode
 lda #0
 sta GamePace_Phase
 sta GamePace_Edges
 lda cheat_vals+2
 cmp #3
 beq @unsupported_game   ; Salamander: vertical stages, no loader yet
 lda cheat_from
 beq @from_title
 lda cheat_action
 cmp #1
 bne @reload
 lda cheat_vals+3
 cmp stage_id
 bne @reload
 lda cheat_vals+2
 cmp chapter
 bne @reload
 ; Plain resume: powers, then the screen as it was.
 jsr @powers
 jsr RestoreGameScreen
 lda #2
 sta mode
 ; Drop CheatInput's return into bank-9 code: that bank is no longer mapped.
 pla
 pla
 rts
@unsupported_game:
 ; Other chapters are not playable yet: stay in the menu.
 lda #0
 sta cheat_draw
 rts
@from_title:
 jsr NewGame
@reload:
 ; Chapter 1 or 2 (Nemesis 2 maps are loadable terrain only, no gameplay yet).
 lda cheat_vals+2
 sta chapter
 sta Flow_State+F_CHAPTER
 lda cheat_vals+3
 sta stage_id
 sta Flow_State+F_STAGE
 lda #1
 sta route_flag
 lda #$20
 sta worldlo
 lda #0
 sta worldhi
 jsr LoadStage
 lda cheat_action
 cmp #2
 beq @warp
 lda cheat_vals+4
 beq @loaded
 ; Midpoint checkpoint from the stage descriptor (same source LoadStage uses).
 lda #10
 sta ptr
 lda stagebase
 sta ptr+1
 ldy #0
 lda (ptr),y
 sta worldlo
 iny
 lda (ptr),y
 sta worldhi
 jmp @again
@warp:
 ; Scroll limit minus $30 columns: the approach to the stage's end sequence.
 lda #4
 sta ptr
 lda stagebase
 sta ptr+1
 ldy #0
 lda (ptr),y
 sec
 sbc #$30
 sta worldlo
 iny
 lda (ptr),y
 sbc #0
 sta worldhi
@again:
 lda #1
 sta route_flag
 jsr LoadStage
@loaded:
 jsr @powers
 lda #1
 sta mode
 pla
 pla
 rts
@powers:
 lda cheat_vals+5
 sta player_speed
 lda cheat_vals+6
 sta power_missile
 lda cheat_vals+7
 sta power_double
 lda cheat_vals+8
 sta power_laser
 lda cheat_vals+9
 sta power_options
 lda cheat_vals+10
 beq :+
 lda #2
:
 sta power_shield
 rts

; Debug text row (row 26) every eighth frame: world, phase, missed NMIs,
; live actors, sprites used, frame counter.
CheatDebugRow:
 lda logic
 and #7
 jne @rts
 lda hud2_pending
 jne @rts
 ldx #31
 lda #' '
@fill:
 sta HUD2,x
 dex
 bpl @fill
 lda #'W'
 sta HUD2+0
 lda #':'
 sta HUD2+1
 lda worldhi
 ldx #2
 jsr HexAt
 lda worldlo
 ldx #4
 jsr HexAt
 lda #'P'
 sta HUD2+7
 lda #':'
 sta HUD2+8
 lda phase
 ldx #9
 jsr HexAt
 lda #'M'
 sta HUD2+12
 lda #':'
 sta HUD2+13
 lda missed
 ldx #14
 jsr HexAt
 lda #'A'
 sta HUD2+17
 lda #':'
 sta HUD2+18
 ldx #0
 ldy #0
@count:
 lda OBJECTS,x
 beq :+
 iny
:
 txa
 clc
 adc #32
 tax
 bne @count
 lda OBJECTS+256
 beq :+
 iny
:
 tya
 ldx #19
 jsr HexAt
 lda #'S'
 sta HUD2+22
 lda #':'
 sta HUD2+23
 lda sprite_index
 lsr a
 lsr a
 ldx #24
 jsr HexAt
 lda #'F'
 sta HUD2+27
 lda #':'
 sta HUD2+28
 lda frame
 ldx #29
 jsr HexAt
 lda #$40
 sta hud2_addr
 lda #$23
 sta hud2_addr+1
 lda #0
 sta hud2_exattr
 lda #1
 sta hud2_pending
@rts: rts

HexDigits: .byte "0123456789ABCDEF"
; A = byte, X = column: two hex digits into HUD2.
HexAt:
 pha
 lsr a
 lsr a
 lsr a
 lsr a
 tay
 lda HexDigits,y
 sta HUD2,x
 pla
 and #15
 tay
 lda HexDigits,y
 sta HUD2+1,x
 rts

; --------------------------------------------------------- menu (bank 9 code)
.segment "TITLE"
Labels:
 .byte "INVINCIBLE    "
 .byte "LIVES         "
 .byte "GAME          "
 .byte "STAGE         "
 .byte "CHECKPOINT    "
 .byte "SHIP SPEED    "
 .byte "MISSILE       "
 .byte "DOUBLE        "
 .byte "LASER         "
 .byte "OPTIONS       "
 .byte "SHIELD        "
 .byte "PACE          "
 .byte "SOUND TEST    "
 .byte "DEBUG HUD     "
 .byte "WARP TO END   "
 .byte "RESTART STAGE "
 .byte "START GAME    "
TitleText:   .byte "   SILICON FORGE CHEAT MENU     "
ValType:     .byte VT_ONOFF,VT_LIVES,VT_GAME,VT_DEC,VT_CHECK,VT_DEC,VT_ONOFF,VT_ONOFF,VT_ONOFF,VT_DEC,VT_ONOFF,VT_PACE,VT_HEX,VT_ONOFF,VT_PRESS,VT_PRESS,VT_PRESS
ValMin:      .byte 0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0
ValMax:      .byte 1,1,4,12,1,7,1,1,1,2,1,2,255,1,0,0,0
TxtOff:      .byte "OFF     "
TxtOn:       .byte "ON      "
TxtNormal:   .byte "NORMAL  "
TxtInf:      .byte "INFINITE"
TxtStart:    .byte "START   "
TxtMid:      .byte "MIDPOINT"
TxtPress:    .byte "PRESS A "
TxtResume:   .byte "RESUME        "
TxtPace:     .byte "30 FPS  ","40 FPS  ","60 FPS  "
TxtGames:    .byte "NEMESIS ","NEMESIS2","SAL WIP ","NEMESIS3"

CheatFrame:
 ; Input first, every frame; pending rows are uploaded one per frame after it.
 jsr CheatInput
 lda mode
 cmp #5
 bne @rts0
 lda hud2_pending
 bne @rts0
 lda cheat_draw
 cmp #ITEMS+1
 jcc DrawMenuRow
@rts0:
 rts
CheatInput:
 lda pressed
 and #BTN_UP
 beq @no_up
 dec cheat_cursor
 jpl @moved
 lda #ITEMS-1
 sta cheat_cursor
 jne @moved
@no_up:
 lda pressed
 and #BTN_DOWN
 beq @no_down
 inc cheat_cursor
 lda cheat_cursor
 cmp #ITEMS
 jcc @moved
 lda #0
 sta cheat_cursor
 jeq @moved
@no_down:
 ldx cheat_cursor
 lda pressed
 and #BTN_LEFT
 beq @no_left
 lda ValType,x
 cmp #VT_PRESS
 beq @rts
 lda cheat_vals,x
 cmp ValMin,x
 beq @wrap_high
 dec cheat_vals,x
 jmp @moved
@wrap_high:
 lda ValMax,x
 sta cheat_vals,x
 jmp @moved
@no_left:
 lda pressed
 and #BTN_RIGHT
 beq @no_right
 lda ValType,x
 cmp #VT_PRESS
 beq @rts
 lda cheat_vals,x
 cmp ValMax,x
 beq @wrap_low
 inc cheat_vals,x
 jmp @moved
@wrap_low:
 lda ValMin,x
 sta cheat_vals,x
 jmp @moved
@no_right:
 lda pressed
 and #BTN_START
 bne @go
 lda pressed
 and #BTN_A
 beq @rts
 cpx #12
 bne @not_sound
 lda #1
 sta audio_on
 lda cheat_vals+12
 sta audio_cmd
 rts
@not_sound:
 cpx #14
 bne @not_warp
 lda #2
 jmp CheatApply
@not_warp:
 cpx #15
 bne @not_restart
 lda #3
 jmp CheatApply
@not_restart:
 cpx #16
 bne @rts
@go:
 lda #1
 jmp CheatApply
@moved:
 lda #0
 sta cheat_draw
@rts: rts
DrawMenuRow:
 ; row 0 = title, rows 1..ITEMS = items
 ldx #31
 lda #' '
@blank:
 sta HUD2,x
 dex
 bpl @blank
 lda cheat_draw
 bne @item
 ldx #0
@title:
 lda TitleText,x
 sta HUD2,x
 inx
 cpx #32
 bne @title
 lda #ROW_TITLE
 jmp @send
@item:
 sec
 sbc #1
 sta s0                ; item index
 cmp cheat_cursor
 bne :+
 lda #'-'
 sta HUD2+0
:
 ; label: 14 chars at column 2
 lda s0
 asl a
 asl a
 asl a
 asl a
 sec
 sbc s0
 sec
 sbc s0                ; *14
 tay
 ldx #0
@label:
 lda Labels,y
 sta HUD2+2,x
 iny
 inx
 cpx #14
 bne @label
 lda s0
 cmp #16
 bne @value
 lda cheat_from
 beq @value
 ldx #0
@resume:
 lda TxtResume,x
 sta HUD2+2,x
 inx
 cpx #14
 bne @resume
@value:
 ldx s0
 lda cheat_vals,x
 sta s1
 lda ValType,x
 cmp #VT_ONOFF
 beq @onoff
 cmp #VT_LIVES
 beq @lives
 cmp #VT_GAME
 beq @game
 cmp #VT_DEC
 beq @dec
 cmp #VT_CHECK
 beq @check
 cmp #VT_PACE
 beq @pace
 cmp #VT_HEX
 beq @hex
 ldy #<TxtPress
 ldx #>TxtPress
 jmp @text8
@onoff:
 lda s1
 beq :+
 ldy #<TxtOn
 ldx #>TxtOn
 jmp @text8
:
 ldy #<TxtOff
 ldx #>TxtOff
 jmp @text8
@lives:
 lda s1
 beq :+
 ldy #<TxtInf
 ldx #>TxtInf
 jmp @text8
:
 ldy #<TxtNormal
 ldx #>TxtNormal
 jmp @text8
@check:
 lda s1
 beq :+
 ldy #<TxtMid
 ldx #>TxtMid
 jmp @text8
:
 ldy #<TxtStart
 ldx #>TxtStart
 jmp @text8
@pace:
 lda s1
 asl a
 asl a
 asl a
 clc
 adc #<TxtPace
 tay
 lda #>TxtPace
 adc #0
 tax
 jmp @text8
@game:
 lda s1
 sec
 sbc #1
 asl a
 asl a
 asl a
 clc
 adc #<TxtGames
 tay
 lda #>TxtGames
 adc #0
 tax
 jmp @text8
@dec:
 lda s1
 ldx #'0'
 cmp #10
 bcc :+
 sbc #10
 ldx #'1'
:
 stx HUD2+17
 clc
 adc #'0'
 sta HUD2+18
 jmp @row
@hex:
 lda s1
 lsr a
 lsr a
 lsr a
 lsr a
 tay
 lda HexDigits,y
 sta HUD2+17
 lda s1
 and #15
 tay
 lda HexDigits,y
 sta HUD2+18
 jmp @row
@text8:
 sty ptr
 stx ptr+1
 ldy #0
@copy:
 lda (ptr),y
 sta HUD2+17,y
 iny
 cpy #8
 bne @copy
@row:
 lda s0
 clc
 adc #ROW_FIRST
@send:
 ; nametable address of row A: $2000 + A*32
 sta s2
 lda #0
 sta hud2_addr
 lda s2
 lsr a
 lsr a
 lsr a
 clc
 adc #$20
 sta hud2_addr+1
 lda s2
 and #7
 asl a
 asl a
 asl a
 asl a
 asl a
 sta hud2_addr
 lda #1
 sta hud2_exattr
 sta hud2_pending
 inc cheat_draw
 rts
