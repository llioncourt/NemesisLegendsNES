.setcpu "6502"
.include "native.inc"
.import Main, DrawColumn, UploadColumn, LoadStage, FrameGame
.export Reset, NMI, IRQ, PollPad, HideSprites, StarRows, SourceObjectDefaults
.export AngleTable, SineTable, SpriteCode, SoundRequest, ClearPPU
.export TitleName, TitlePalette
.segment "HEADER"
.byte "NES",$1a,8,16,$50,$08,0,0,$07,0,0,0,0,0
.segment "BOOT"
Reset:
 sei
 cld
 ldx #$ff
 txs
 inx
 stx $2000
 stx $2001
 stx $4010
 stx $4015
 stx $5204
 lda #$40
 sta $4017
 bit $2002
@vb1: bit $2002
 bpl @vb1
@vb2: bit $2002
 bpl @vb2
 lda #0
 tax
@ram:
 sta $0000,x
 sta $0100,x
 sta $0200,x
 sta $0300,x
 sta $0400,x
 sta $0500,x
 sta $0600,x
 sta $0700,x
 inx
 bne @ram
 lda #3
 sta $5100
 sta $5101
 lda #2
 sta $5102
 lda #1
 sta $5103
 lda #0
 sta $5113
 sta $5105
 sta $5130
 sta $5104
 lda #$80
 sta $5114
 lda #$87
 sta $5115
 lda #$8e
 sta $5116
 lda #$8f
 sta $5117
 lda #$a7
 sta rseed
 lda #$0f
 sta $4015
 jsr HideSprites
 jmp Main

NMI:
 pha
 txa
 pha
 tya
 pha
 inc frame
 lda screenon
 beq @audio
 lda ready
 bne @consume
 lda mode
 cmp #1
 bne @audio
 inc missed
 jmp @audio
@consume:
 lda #0
 sta $5204
 lda column_pending
 beq @oam
 jsr UploadColumn
 lda #0
 sta column_pending
@oam:
 lda #0
 sta $2003
 lda #2
 sta $4014
 lda hud_pending
 beq @scroll
 bit $2002
 lda #$a0
 sta $2000
 lda #$23
 sta $2006
 lda #$20
 sta $2006
 ldx #0
@hud:
 lda HUD,x
 sta $2007
 inx
 cpx #32
 bne @hud
 lda #0
 sta hud_pending
@scroll:
 bit $2002
 lda camera
 sta $2005
 lda #0
 sta $2005
 lda #$a0
 sta $2000
 lda mode
 beq @nonsplit
 lda #199
 sta $5203
 lda $5204
 lda #$80
 sta $5204
@nonsplit:
 lda #0
 sta ready
@audio:
 lda audio_on
 beq @done
 lda audio_cmd
 beq @tick
 jsr $ec1e
 lda #0
 sta audio_cmd
@tick:
 jsr $ed02
@done:
 pla
 tay
 pla
 tax
 pla
 rti

IRQ:
 pha
 lda $5204
 lda #0
 sta $5204
 bit $2002
 sta $2005
 sta $2005
 pla
 rti

PollPad:
 lda pad
 sta oldpad
 lda #1
 sta $4016
 sta pad
 lsr a
 sta $4016
@read:
 lda $4016
 lsr a
 rol pad
 bcc @read
 lda oldpad
 eor #$ff
 and pad
 sta pressed
 rts

HideSprites:
 lda #$f0
 ldx #0
@h:
 sta OAM,x
 inx
 inx
 inx
 inx
 bne @h
 rts

SoundRequest:
 sta audio_cmd
 rts

ClearPPU:
 bit $2002
 lda #$20
 sta $2006
 lda #0
 sta $2006
 ldx #4
 ldy #0
@nt: sta $2007
 iny
 bne @nt
 dex
 bne @nt
 lda #2
 sta $5104
 ldx #0
@ex:
 sta $5c00,x
 sta $5d00,x
 sta $5e00,x
 sta $5f00,x
 inx
 bne @ex
 rts

StarRows: .incbin "build/native/tables.bin",0,32
SourceObjectDefaults: .incbin "build/native/tables.bin",$100,$80
AngleTable: .incbin "build/native/tables.bin",$200,$100
SineTable: .incbin "build/native/tables.bin",$300,$40
; Logical 16x16 frame -> NES 8x16 left sprite code. Right sprite is +2.
SpriteCode:
.repeat 128,I
 .byte ((I*4)&$fe)|((I*4)>>8)
.endrepeat
TitleName: .incbin "assets/title/title.nam"
TitlePalette: .incbin "assets/title/title.pal"

.segment "SOUND"
.incbin "build/native/audio.bin"
.segment "VECTORS"
.word NMI,Reset,IRQ
.segment "STAGE0"
.incbin "build/native/stage_01.bin"
.incbin "build/native/stage_02.bin"
.segment "STAGE1"
.incbin "build/native/stage_03.bin"
.incbin "build/native/stage_04.bin"
.segment "STAGE2"
.incbin "build/native/stage_05.bin"
.incbin "build/native/stage_06.bin"
.segment "STAGE3"
.incbin "build/native/stage_07.bin"
.incbin "build/native/stage_08.bin"
.segment "STAGE4"
.incbin "build/native/stage_09.bin"
.incbin "build/native/stage_10.bin"
.segment "STAGE5"
.incbin "build/native/stage_11.bin"
.incbin "build/native/stage_12.bin"
.segment "MAPS"
.incbin "build/native/metatiles.bin"
.segment "GRAPHICS"
.incbin "build/native/graphics.chr"
