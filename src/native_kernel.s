.setcpu "6502"
.include "native.inc"
.include "campaign.inc"
.import Flow_State, Flow_NewGame, Flow_Event
.import PollPad, HideSprites, StarRows, SpriteCode, SoundRequest, ClearPPU
.import TitleName,TitlePalette
.import ActorsFrame, ActorsDraw, SpawnCannon, SpawnWaves, ShotsFrame, InitActors
.export Main, DrawColumn, UploadColumn, LoadStage, FrameGame
.export DrawSprite, UpdateHUD, PlayerHit, LoadDataBank, AdvanceStage
.segment "CODE"
Main:
 jsr Title
@loop:
 lda ready
 bne @loop
 jsr PollPad
 lda mode
 bne @playing
 lda pressed
 and #BTN_START
 beq @titleidle
 jsr Flow_NewGame
 lda #3
 sta player_lives
 lda #1
 sta stage_id
 lda #$20
 sta worldlo
 lda #0
 sta worldhi
 jsr LoadStage
 jmp @finish
@titleidle:
 jmp @finish
@playing:
 lda pressed
 and #BTN_START
 beq @notpause
 lda mode
 cmp #1
 bne @unpause
 lda #2
 sta mode
 jmp @notpause
@unpause:
 cmp #2
 bne @notpause
 lda #1
 sta mode
@notpause:
 lda mode
 cmp #1
 bne @dead
 jsr FrameGame
 jmp @finish
@dead:
 cmp #3
 bne @finish
 dec player_dead
 bne @finish
 lda player_lives
 beq @gameover
 dec player_lives
 ; Original checkpoints: restart $20 before midpoint, otherwise the midpoint.
 lda #10
 sta ptr
 lda stagebase
 sta ptr+1
 ldy #1
 lda worldhi
 cmp (ptr),y
 bcc @fromstart
 bne @midpoint
 dey
 lda worldlo
 cmp (ptr),y
 bcc @fromstart
@midpoint:
 ldy #0
 lda (ptr),y
 sta worldlo
 iny
 lda (ptr),y
 sta worldhi
 jmp @restart
@fromstart:
 lda #$20
 sta worldlo
 lda #0
 sta worldhi
@restart:
 jsr LoadStage
 jmp @finish
@gameover:
 lda #$af
 jsr SoundRequest
 jsr Title
@finish:
 lda #1
 sta ready
 jmp @loop

Title:
 sei
 lda #0
 sta screenon
 sta $2000
 sta $2001
 sta $5204
 sta mode
 sta camera
 sta audio_on
 sta $5104
 jsr HideSprites
 jsr ClearPPU
 lda #0
 sta $5104
 ldx #0
@bank:
 txa
 sta $5128,x
 inx
 cpx #4
 bne @bank
 bit $2002
 lda #$20
 sta $2006
 lda #0
 sta $2006
 lda #<TitleName
 sta ptr
 lda #>TitleName
 sta ptr+1
 ldx #4
 ldy #0
@title:
 lda (ptr),y
 sta $2007
 iny
 bne @title
 inc ptr+1
 dex
 bne @title
 bit $2002
 lda #$3f
 sta $2006
 lda #0
 sta $2006
 ldx #0
@pal:
 lda TitlePalette,x
 sta $2007
 inx
 cpx #32
 bne @pal
 lda #0
 sta $2005
 sta $2005
 lda #$a0
 sta $2000
 lda #$1e
 sta $2001
 lda #1
 sta screenon
 cli
 rts

LoadDataBank:
 lda stage_bank
 ora #$80
 sta $5114
 rts

LoadStage:
 sei
 lda #0
 sta screenon
 sta $2000
 sta $2001
 sta $5204
 sta audio_on
 sta column_pending
 sta phase
 sta phase_timer
 sta phase_hi
 sta wave_state
 sta wave_timer
 sta power_slot
 sta power_missile
 sta power_double
 sta power_laser
 sta power_options
 sta power_shield
 sta player_speed
 sta player_dead
 sta score_lo
 sta score_hi
 sta boss_hp
 sta route_flag
 lda stage_id
 sec
 sbc #1
 lsr a
 sta stage_bank
 jsr LoadDataBank
 lda stage_id
 and #1
 bne @evenbase
 lda #$90
 bne @base
@evenbase: lda #$80
@base:
 sta stagebase
 lda #0
 sta ptr
 lda stagebase
 sta ptr+1
 ldy #$10
 ldx #0
@sprites:
 lda (ptr),y
 sta $5120,x
 iny
 inx
 cpx #8
 bne @sprites
 lda #$86
 sta $5115
 jsr ClearPPU
 ; Per-stage background palettes and four fixed sprite palettes.
 bit $2002
 lda #$3f
 sta $2006
 lda #0
 sta $2006
 ldy #$20
@pal:
 lda (ptr),y
 sta $2007
 iny
 cpy #$30
 bne @pal
 ldx #0
@spal:
 lda SpritePalette,x
 sta $2007
 inx
 cpx #16
 bne @spal
 ; Initial window consists of previous 32 source columns.
 lda worldlo
 sec
 sbc #32
 sta worldlo
 lda worldhi
 sbc #0
 sta worldhi
 lda worldlo
 asl a
 asl a
 asl a
 sta camera
 lda #32
 sta work
@window:
 jsr DrawColumn
 jsr UploadColumn
 inc worldlo
 bne :+
 inc worldhi
:
 dec work
 bne @window
 lda worldlo
 bne :+
 dec worldhi
:
 dec worldlo
 lda #0
 sta column_pending
 ; HUD has its own bitmap bank in ExRAM; this is not a split CHR hack.
 lda #2
 sta $5104
 ldx #0
 lda #1
@font:
 sta $5f20,x
 sta $5f40,x
 inx
 cpx #32
 bne @font
 lda #1
 sta $5104
 lda #$87
 sta $5115
 jsr InitActors
 lda #$50
 sta player_x
 lda #$4a
 sta player_y
 lda #90
 sta player_iframes
 lda #0
 sta fire_delay
 lda #1
 sta mode
 jsr HideSprites
 jsr UpdateHUD
 lda #1
 sta hud_pending
 lda #0
 sta camera
 sta $2005
 sta $2005
 lda #$96
 sta audio_cmd
 lda #1
 sta audio_on
 sta ready
 sta screenon
 lda #$a0
 sta $2000
 lda #$1c
 sta $2001
 cli
 rts

; Construct one column using the original six-metatile script. No full-map RAM.
DrawColumn:
 lda #$86
 sta $5115
 lda #0
 sta ptr
 lda stagebase
 sta ptr+1
 lda worldlo
 and #31
 sta column_slot
 ; Select rows that lie inside the original terrain interval.
 ldy #1
 lda (ptr),y
 cmp #$ff
 beq @stars
 lda worldhi
 cmp (ptr),y
 bcc @stars
 bne @startok
 dey
 lda worldlo
 cmp (ptr),y
 bcc @stars
@startok:
 ldy #3
 lda worldhi
 cmp (ptr),y
 bcc @inside
 bne @stars
 dey
 lda worldlo
 cmp (ptr),y
 bcc @inside
 beq @inside
@stars:
 ldx #0
 lda #0
@clearcol:
 sta COL_SOURCE,x
 inx
 cpx #22
 bne @clearcol
 lda worldlo
 and #31
 tax
 lda StarRows,x
 sec
 sbc #1
 tax
 cpx #22
 bcc :+
 jmp @convert
:
 lda #$f6
 sta COL_SOURCE,x
 jmp @convert
@inside:
 ldy #0
 lda worldlo
 sec
 sbc (ptr),y
 sta relative
 iny
 lda worldhi
 sbc (ptr),y
 sta relative+1
 lda relative
 and #3
 sta terrain_offset
 lsr relative+1
 ror relative
 lsr relative+1
 ror relative
 ; record offset = group * 6
 lda relative
 asl a
 sta script
 lda relative+1
 rol a
 sta script+1
 asl script
 rol script+1
 lda script
 clc
 adc relative
 sta script
 lda script+1
 adc relative+1
 sta script+1
 lda script
 clc
 adc relative
 sta script
 lda script+1
 adc relative+1
 clc
 adc stagebase
 adc #7
 sta script+1
 lda #0
 sta row
 sta piece
@metatile:
 ldy piece
 lda (script),y
 sta map_ptr
 lda #0
 sta map_ptr+1
 asl map_ptr
 rol map_ptr+1
 asl map_ptr
 rol map_ptr+1
 asl map_ptr
 rol map_ptr+1
 asl map_ptr
 rol map_ptr+1
 ldy #6
 lda map_ptr
 clc
 adc (ptr),y
 sta map_ptr
 iny
 lda map_ptr+1
 adc (ptr),y
 clc
 adc #$20
 sta map_ptr+1
 lda map_ptr
 clc
 adc terrain_offset
 sta map_ptr
 bcc :+
 inc map_ptr+1
:
 ldy #0
@rows:
 lda (map_ptr),y
 ldx row
 sta COL_SOURCE,x
 inc row
 lda row
 cmp #22
 beq @convert
 tya
 clc
 adc #4
 tay
 cpy #16
 bne @rows
 inc piece
 jmp @metatile
@convert:
 ; Cache original source IDs for source collision rules (32-byte column stride).
 lda column_slot
 asl a
 asl a
 asl a
 asl a
 asl a
 sta colcache
 lda column_slot
 lsr a
 lsr a
 lsr a
 clc
 adc #$60
 sta colcache+1
 lda #0
 sta lookup
 lda stagebase
 clc
 adc #1
 sta lookup+1
 ldx #0
@tile:
 stx row
 txa
 lsr a
 lsr a
 lsr a
 clc
 adc stagebase
 adc #1
 sta lookup+1
 lda COL_SOURCE,x
 tay
 lda (lookup),y
 sta COL_TILES,x
 lda lookup+1
 clc
 adc #3
 sta lookup+1
 lda (lookup),y
 sta COL_ATTRS,x
 ldy row
 lda COL_SOURCE,x
 sta (colcache),y
 inx
 cpx #22
 bne @tile
 lda #1
 sta column_pending
 lda #$87
 sta $5115
 rts

; Runs only during forced blank or NMI. Uses separate scratch pointers.
UploadColumn:
 bit $2002
 lda #$a4
 sta $2000
 lda #$20
 sta $2006
 lda column_slot
 clc
 adc #$40
 sta $2006
 ldx #0
@tiles:
 lda COL_TILES,x
 sta $2007
 inx
 cpx #22
 bne @tiles
 lda #2
 sta $5104
 lda #$5c
 sta nptr+1
 lda column_slot
 clc
 adc #$40
 sta nptr
 ldy #0
 ldx #0
@attrs:
 lda COL_ATTRS,x
 sta (nptr),y
 lda nptr
 clc
 adc #32
 sta nptr
 bcc :+
 inc nptr+1
:
 inx
 cpx #22
 bne @attrs
 lda #1
 sta $5104
 lda #$a0
 sta $2000
 rts

FrameGame:
 inc logic
 lda #0
 sta new_column
 lda phase
 cmp #2
 bcs @noscroll
 inc camera
 lda camera
 and #7
 cmp #1
 bne @noscroll
 inc worldlo
 bne :+
 inc worldhi
:
 jsr DrawColumn
 lda #1
 sta new_column
 jsr SpawnCannon
@noscroll:
 jsr MovePlayer
 jsr SpawnWaves
 jsr ActorsFrame
 jsr ShotsFrame
 jsr HideSprites
 lda #0
 sta sprite_index
 lda player_iframes
 beq @ship
 dec player_iframes
 and #4
 bne @actors
@ship:
 lda player_x
 sta sprite_x
 lda player_y
 clc
 adc #15
 sta sprite_y
 lda #120
 sta sprite_frame
 lda pad
 and #BTN_UP
 beq :+
 lda #122
 sta sprite_frame
:
 lda pad
 and #BTN_DOWN
 beq :+
 lda #121
 sta sprite_frame
:
 lda #0
 sta sprite_pal
 sta sprite_flags
 jsr DrawSprite
@actors:
 jsr ActorsDraw
 jsr UpdateHUD
 rts

MovePlayer:
 lda #2
 sta temp
 lda player_speed
 lsr a
 clc
 adc temp
 sta temp
 lda pad
 and #BTN_UP
 beq @down
 lda player_y
 sec
 sbc temp
 bcs :+
 lda #0
:
 sta player_y
@down:
 lda pad
 and #BTN_DOWN
 beq @left
 lda player_y
 clc
 adc temp
 cmp #166
 bcc :+
 lda #165
:
 sta player_y
@left:
 lda pad
 and #BTN_LEFT
 beq @right
 lda player_x
 sec
 sbc temp
 cmp #8
 bcs :+
 lda #8
:
 sta player_x
@right:
 lda pad
 and #BTN_RIGHT
 beq @done
 lda player_x
 clc
 adc temp
 cmp #217
 bcc :+
 lda #216
:
 sta player_x
@done:
 rts

; A source frame is two 8x16 NES sprites, never four background writes.
DrawSprite:
 ldx sprite_index
 cpx #$f8
 bcs @done
 ldy sprite_frame
 lda SpriteCode,y
 sta OAM+1,x
 clc
 adc #2
 sta OAM+5,x
 lda sprite_y
 sta OAM,x
 sta OAM+4,x
 lda sprite_pal
 ora sprite_flags
 sta OAM+2,x
 sta OAM+6,x
 lda sprite_x
 sta OAM+3,x
 clc
 adc #8
 sta OAM+7,x
 txa
 clc
 adc #8
 sta sprite_index
@done:
 rts

PlayerHit:
 lda qa_flags
 and #1
 bne @no
 lda player_iframes
 bne @no
 lda mode
 cmp #1
 bne @no
 lda #3
 sta mode
 lda #90
 sta player_dead
 lda #$ac
 jsr SoundRequest
@no:rts

UpdateHUD:
 ldx #31
@copy:
 lda HUDTemplate,x
 sta HUD,x
 dex
 bpl @copy
 lda stage_id
 clc
 adc #$30
 sta HUD+3
 lda player_lives
 clc
 adc #$30
 sta HUD+8
 lda power_slot
 clc
 adc #$30
 sta HUD+14
 lda power_options
 clc
 adc #$30
 sta HUD+20
 lda #1
 sta hud_pending
 rts

AdvanceStage:
 lda #EVENT_CLEAR
 ldx #0
 jsr Flow_Event
 cmp #ACTION_LOAD
 bne @scene
 lda Flow_State+F_STAGE
 sta stage_id
 lda #$20
 sta worldlo
 lda #0
 sta worldhi
 jmp LoadStage
@scene:
 lda #4
 sta mode
 rts
SpritePalette: .byte $0f,$30,$16,$12,$0f,$16,$30,$12,$0f,$28,$30,$16,$0f,$12,$30,$16
HUDTemplate: .byte "ST:1  L:3  PWR:0  OP:0   NEMESIS "
