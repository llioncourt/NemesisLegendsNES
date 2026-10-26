.setcpu "6502"
.include "native.inc"
.include "boss.inc"
.include "longbranch.inc"
.import HideSprites, ClearPPU
.export TitleInit, TitleFrame, TitleVBlank
.segment "TITLE"
; CP0007: reconstructed scenic backdrop, genuine Gradius II glyphs, bounded reveal.
; Commands: 1 panel row (20 NT + 20 ExRAM bytes), 2 palette (32),
; 3 first label (12), 4 second label (12), 5 cursor (2), 6 both labels + cursor (26).
; Main publishes title_dirty LAST. NMI acknowledges after the entire transaction.
TitleInit:
 sei
 lda #0
 sta $2000
 sta screenon
 sta $2001
 sta $5204
 sta mode
 sta camera
 sta audio_on
 sta column_pending
 sta boss_dirty
 sta hud_pending
 sta $5130
 sta $5200
 ldx #15
@clearstate:
 cpx #3                  ; preserve the user's sound preference
 beq @nextstate
 sta title_page,x
@nextstate:
 dex
 bpl @clearstate
 jsr HideSprites
 jsr ClearPPU
 lda #<ArtExRAM
 sta ptr
 lda #>ArtExRAM
 sta ptr+1
 lda #0
 sta ptr2
 lda #$5c
 sta ptr2+1
 ldx #4
 ldy #0
@ex:
 lda (ptr),y
 sta (ptr2),y
 iny
 bne @ex
 inc ptr+1
 inc ptr2+1
 dex
 bne @ex
 bit $2002
 lda #$20
 sta $2006
 lda #0
 sta $2006
 lda #<ArtName
 sta ptr
 lda #>ArtName
 sta ptr+1
 ldx #4
 ldy #0
@nt:
 lda (ptr),y
 sta $2007
 iny
 bne @nt
 inc ptr+1
 dex
 bne @nt
 ; The base scene has its old baked labels removed during asset generation.
 ; Never clear these nametable rows to blank: that introduced visible holes
 ; while the animated opaque panel had not yet covered the scene.
 bit $2002
 lda #$3f
 sta $2006
 lda #0
 sta $2006
 ldx #32
 lda #$0f
@black:
 sta $2007
 dex
 bne @black
 lda #1
 sta $5104
 sta title_intro
 sta title_release        ; also guards a held confirm at a title return
 lda #0
 sta $2005
 sta $2005
 lda #$93
 sta audio_cmd
 lda sound_muted
 bne @silent
 lda #$0f
 sta $4015
 lda #1
 sta audio_on
 jmp @enable
@silent:
 lda #0
 sta $4015
@enable:
 lda #1
 sta ready
 sta screenon
 lda #$a0
 sta $2000
 lda #$1e
 sta $2001
 cli
 rts

TitleFrame:
 lda title_dirty
 jeq @idlequeue
 clc
 rts
@idlequeue:
 lda title_intro
 jeq ReadyFrame
 lda pressed
 and #(BTN_START|BTN_A)
 beq @nofast
 lda #1
 sta title_fast
 sta title_release
@nofast:
 inc title_tick
 ldx title_step
 lda title_fast
 bne @event
 lda title_tick
 cmp EventFrames,x
 bcs @event
 clc
 rts
@event:
 cpx #2
 bcs @panel
 stx title_dim
 lda #2
 sta title_dirty
 jmp @advance
@panel:
 cpx #10
 bcs @labels
 txa
 eor #$ff
 clc
 adc #10                ; event 2 -> bottom row 7, event 9 -> top row 0
 sta title_row
 lda #1
 sta title_dirty
 jmp @advance
@labels:
 cpx #10
 bne @second
 lda #3
 bne @publish
@second:
 cpx #11
 bne @cursor
 lda #4
 bne @publish
@cursor:
 lda #0
 sta title_intro
 sta title_blink
 lda #5
@publish:
 sta title_dirty
@advance:
 inc title_step
 clc
 rts

ReadyFrame:
 lda title_release
 beq @released
 lda pad
 and #(BTN_START|BTN_A)
 bne @no
 lda #0
 sta title_release
@no:
 clc
 rts
@released:
 ; Two opposite directions never generate a movement, including a repeat.
 lda pad
 and #(BTN_UP|BTN_DOWN)
 cmp #(BTN_UP|BTN_DOWN)
 beq @opposites
 cmp title_dir
 beq @held
 sta title_dir
 lda #15
 sta title_repeat
 lda title_dir
 bne @move
 jmp @select
@held:
 lda title_dir
 beq @select
 dec title_repeat
 bne @select
 lda #5
 sta title_repeat
 jmp @move
@opposites:
 lda #0
 sta title_dir
 sta title_repeat
@select:
 lda pressed
 and #BTN_SELECT
 beq @choose
@move:
 lda title_index
 eor #1
 sta title_index
 lda #0
 sta title_blink
 sta title_alt
 lda #5
 sta title_dirty
@choose:
 lda title_page
 bne @options
 lda pressed
 and #(BTN_START|BTN_A)
 jeq @blink
 lda title_index
 bne @openoptions
 ; No pending title request may leak into the first gameplay NMI.
 lda #0
 sta title_dirty
 sta pressed
 sec
 rts
@openoptions:
 lda #1
 sta title_page
 lda #0
 sta title_index
 sta title_blink
 sta title_alt
 lda #6
 sta title_dirty
 clc
 rts
@options:
 lda pressed
 and #BTN_B
 bne @back
 lda pressed
 and #(BTN_START|BTN_A)
 beq @sides
 lda title_index
 bne @back
 jmp @toggle
@sides:
 lda title_index
 bne @blink
 lda pressed
 and #(BTN_LEFT|BTN_RIGHT)
 beq @blink
 cmp #(BTN_LEFT|BTN_RIGHT)
 beq @blink
@toggle:
 lda sound_muted
 eor #1
 sta sound_muted
 beq @soundon
 lda #0
 sta audio_on
 sta $4015
 jmp @changed
@soundon:
 lda #$0f
 sta $4015
 lda #$93
 sta audio_cmd
 lda #1
 sta audio_on
@changed:
 lda #6
 sta title_dirty
 clc
 rts
@back:
 lda #0
 sta title_page
 sta title_blink
 sta title_alt
 lda #1
 sta title_index
 lda #6
 sta title_dirty
 clc
 rts
@blink:
 lda title_dirty
 bne @done
 inc title_blink
 lda title_blink
 cmp #30
 bcc @done
 lda #0
 sta title_blink
 lda title_alt
 eor #1
 sta title_alt
 lda #5
 sta title_dirty
@done:
 clc
 rts

TitleVBlank:
 lda title_dirty
 beq TitleDMA
 cmp #1
 jeq UploadPanelRow
 cmp #2
 jeq UploadTitlePalette
 cmp #3
 beq @first
 cmp #4
 beq @second
 cmp #5
 beq @cursor
 cmp #6
 bne @invalid
 jsr FirstLabel
 jsr SecondLabel
 jsr CursorCells
 jmp TitleAck
@first:
 jsr FirstLabel
 jmp TitleAck
@second:
 jsr SecondLabel
 jmp TitleAck
@cursor:
 jsr CursorCells
 jmp TitleAck
@invalid:
 lda #1
 sta title_error
TitleAck:
 lda #0
 sta title_dirty
TitleDMA:
 lda #0
 sta $2003
 lda #2
 sta $4014
 rts

UploadPanelRow:
 ldx title_row
 cpx #8
 bcc @valid
 lda #1
 sta title_error
 jmp TitleAck
@valid:
 ; ExRAM CPU writes use mode 2 only within this bounded VBlank transaction.
 lda #2
 sta $5104
 lda AttrRowLo,x
 sta nptr
 lda AttrRowHi,x
 sta nptr+1
 lda ScreenRowLo,x
 sta nptr2
 lda ExRowHi,x
 sta nptr2+1
 ldy #0
@attributes:
 lda (nptr),y
 sta (nptr2),y
 iny
 cpy #20
 bne @attributes
 lda #1
 sta $5104              ; restore extended attributes before rendering resumes
 lda PanelRowLo,x
 sta nptr
 lda PanelRowHi,x
 sta nptr+1
 bit $2002
 lda ScreenRowHi,x
 sta $2006
 lda ScreenRowLo,x
 sta $2006
 ldy #0
@tiles:
 lda (nptr),y
 sta $2007
 iny
 cpy #20
 bne @tiles
 jmp TitleAck

UploadTitlePalette:
 bit $2002
 lda #$3f
 sta $2006
 lda #0
 sta $2006
 lda title_dim
 beq @dim
 ldx #0
@normal:
 lda ArtPalette,x
 sta $2007
 inx
 cpx #32
 bne @normal
 jmp TitleAck
@dim:
 ldx #0
@d:
 lda DimPalette,x
 sta $2007
 inx
 cpx #32
 bne @d
 jmp TitleAck

; Only these two rows are mutable text; the surrounding opaque panel stays put.
LabelOffset:
 ldx #0
 lda title_page
 beq @return
 ldx #24
 lda sound_muted
 beq @return
 ldx #48
@return:
 rts
FirstLabel:
 jsr LabelOffset
 bit $2002
 lda #$22
 sta $2006
 lda #$aa
 sta $2006
 ldy #12
@loop:
 lda MenuText,x
 sta $2007
 inx
 dey
 bne @loop
 rts
SecondLabel:
 jsr LabelOffset
 txa
 clc
 adc #12
 tax
 bit $2002
 lda #$23
 sta $2006
 lda #$0a
 sta $2006
 ldy #12
@loop:
 lda MenuText,x
 sta $2007
 inx
 dey
 bne @loop
 rts
CursorCells:
 bit $2002
 lda #$22
 sta $2006
 lda #$a8
 sta $2006
 lda title_index
 bne @firstblank
 lda title_alt
 clc
 adc #$90
 bne @firstwrite
@firstblank:
 lda #32
@firstwrite:
 sta $2007
 lda #$23
 sta $2006
 lda #$08
 sta $2006
 lda title_index
 beq @secondblank
 lda title_alt
 clc
 adc #$90
 bne @secondwrite
@secondblank:
 lda #32
@secondwrite:
 sta $2007
 rts

EventFrames: .byte 4,8,28,30,32,34,36,38,40,42,44,48,52
ScreenRowLo:
.repeat 8,I
 .byte <($2000+(19+I)*32+6)
.endrepeat
ScreenRowHi:
.repeat 8,I
 .byte >($2000+(19+I)*32+6)
.endrepeat
ExRowHi:
.repeat 8,I
 .byte >($5c00+(19+I)*32+6)
.endrepeat
PanelRowLo:
.repeat 8,I
 .byte <(PanelRows+I*20)
.endrepeat
PanelRowHi:
.repeat 8,I
 .byte >(PanelRows+I*20)
.endrepeat
AttrRowLo:
.repeat 8,I
 .byte <(PanelAttrs+I*20)
.endrepeat
AttrRowHi:
.repeat 8,I
 .byte >(PanelAttrs+I*20)
.endrepeat
MenuText:
.byte "START GAME  ","OPTIONS     "
.byte "SOUND ON    ","BACK        "
.byte "SOUND OFF   ","BACK        "
.assert *-MenuText = 72,error,"Menu strings must be 12 characters"
PanelRows: .incbin "assets/title_art/panel_rows.bin"
PanelAttrs: .incbin "assets/title_art/panel_attrs.bin"
DimPalette:
.byte $0f,$0f,$01,$10,$0f,$0f,$06,$17,$0f,$0f,$00,$17,$0f,$0f,$05,$14
.byte $0f,$10,$06,$01,$0f,$10,$06,$01,$0f,$10,$06,$01,$0f,$10,$06,$01
.align 256
ArtName: .incbin "assets/title_art/title.nam"
ArtExRAM: .incbin "assets/title_art/title.exram"
ArtPalette: .incbin "assets/title_art/title.pal"
.byte $0f,$30,$16,$11,$0f,$30,$16,$11,$0f,$30,$16,$11,$0f,$30,$16,$11
