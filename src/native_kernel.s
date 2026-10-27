.setcpu "6502"
.include "native.inc"
.include "boss.inc"
.include "campaign.inc"
.import Flow_State, Flow_NewGame, Flow_Event
.import PollPad, HideSprites, StarRows, SpriteCode, SoundRequest, ClearPPU
.import TitleInit, TitleFrame
.import ActorsFrame, ActorsDraw, SpawnCannon, SpawnWaves, ShotsFrame, InitActors
.import StageEvents
.import Stage2Init, Stage2Tick, Stage2Draw
.import Stage3Init, Stage3Tick, Stage3Draw
.import Stage4Init, Stage4Tick, Stage4Draw, Stage4ShotHit, Stage4LaserHit
.export Stage4ShotHitBanked, Stage4LaserHitBanked
.import TargetNewGame,TargetInit,TargetTick,TargetDraw
.export Main, DrawColumn, UploadColumn, LoadStage, FrameGame
.export DrawSprite8
 .export DrawSprite, UpdateHUD, PlayerHit, LoadDataBank, AdvanceStage
.import GamePace_Mode, GamePace_Phase, GamePace_Edges
.import CheatCode, CheatOpen, CheatFrame, CheatDebugRow
.export NewGame, RestoreGameScreen
.segment "CODE"
Main:
 jsr Title
@loop:
 lda ready
 bne @loop
 jsr PollPad
 lda mode
 bne @playing
 ; Konami Code on the title opens the Silicon Forge cheat menu (CP0013).
 jsr CheatCode
 bcc @title_ordinary
 jsr CheatOpen
 jmp @finish
@title_ordinary:
 jsr TitleFrame
 bcc @titleidle
 jsr NewGame
 jmp @finish
@titleidle:
 jmp @finish
@playing:
 cmp #5
 bne @not_menu
 jsr CheatFrame
 jmp @finish
@not_menu:
 cmp #2
 bne @no_code
 ; Konami Code while paused opens the cheat menu (not during the boss screen).
 lda phase
 cmp #4
 bcc @code_ok
 cmp #9
 bcc @no_code
@code_ok:
 jsr CheatCode
 bcc @no_code
 jsr CheatOpen
 jmp @finish
@no_code:
 ; SELECT toggles comfortable/original cadence in game and while paused.
 ; This is a presentation-rate option, never a speed-up of the NES clock.
 lda pressed
 and #BTN_SELECT
 beq @no_pace_toggle
 inc GamePace_Mode
 lda GamePace_Mode
 cmp #3
 bcc @pace_mode_ok
 lda #0
 sta GamePace_Mode
@pace_mode_ok:
 lda #0
 sta GamePace_Phase
 sta GamePace_Edges
 jsr UpdateHUD
@no_pace_toggle:
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
 lda GamePace_Mode
 cmp #2
 beq @original_pace
 ; Preserve single-frame A power-up presses across skipped logical steps.
 lda pressed
 and #BTN_A
 ora GamePace_Edges
 sta GamePace_Edges
 inc GamePace_Phase
 lda GamePace_Mode
 bne @comfort_40
 ; 30Hz: skip alternate simulation frames, OAM/audio remain at 60Hz.
 lda GamePace_Phase
 and #1
 bne @finish
 jmp @paced_step
@comfort_40:
 ; 40Hz: skip every third simulation opportunity; 2/3 exact cadence.
 lda GamePace_Phase
 cmp #3
 bcc @phase40_ok
 lda #0
 sta GamePace_Phase
@phase40_ok:
 cmp #1
 beq @finish
@paced_step:
 lda pressed
 ora GamePace_Edges
 sta pressed
 lda #0
 sta GamePace_Edges
@original_pace:
 jsr FrameGame
 jmp @finish
@dead:
 cmp #3
 bne @finish
 dec player_dead
 bne @finish
 lda player_lives
 beq @gameover
 lda cheat_flags
 and #1
 bne :+
 dec player_lives
:
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

NewGame:
 lda #1
 sta chapter
 jsr Flow_NewGame
 jsr TargetNewGame
 lda #0
 sta score_lo
 sta score_hi
 sta route_flag
 lda #3
 sta player_lives
 lda #1
 sta stage_id
 lda #$20
 sta worldlo
 lda #0
 sta worldhi
 jmp LoadStage

; Redraw the current stage window, palettes, sprite banks and HUD font rows
; without touching game state (cheat menu resume). Same sequence as LoadStage.
RestoreGameScreen:
 sei
 lda camera
 pha
 lda #0
 sta screenon
 sta $2000
 sta $2001
 sta $5204
 sta column_pending
 jsr LoadDataBank
 lda #0
 sta ptr
 lda stagebase
 sta ptr+1
 ldy #$10
 ldx #0
@rsprites:
 lda (ptr),y
 sta $5120,x
 iny
 inx
 cpx #8
 bne @rsprites
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
@rpal:
 lda (ptr),y
 sta $2007
 iny
 cpy #$30
 bne @rpal
 ldx #0
@rspal:
 lda SpritePalette,x
 sta $2007
 inx
 cpx #16
 bne @rspal
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
@rwindow:
 jsr DrawColumn
 jsr UploadColumn
 inc worldlo
 bne :+
 inc worldhi
:
 dec work
 bne @rwindow
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
@rfont:
 sta $5f20,x
 sta $5f40,x
 inx
 cpx #32
 bne @rfont
 lda #1
 sta $5104
 lda #$87
 sta $5115
 lda #1
 sta hud_pending
 pla
 sta camera
 lda #1
 sta screenon
 lda #$a0
 sta $2000
 lda #$1c
 sta $2001
 cli
 rts

Title:
 lda #0
 sta $2000
 sta screenon
 sta $2001
 sta $5204
 lda #$89
 sta $5114
 sta bank8000
 jmp TitleInit

LoadDataBank:
 lda stage_bank
 ora #$80
 sta $5114
 sta bank8000
 rts

; Stage-specific logic lives in the STAGECODE bank (10), mapped at $8000 only
; while it runs; the $8000 slot otherwise holds stage/boss/title data.
StageCodeIn:
 lda #$8a
 sta $5114
 rts
StageCodeOut:
 lda bank8000
 bne :+
 lda #$80              ; never seeded (unit fixtures): stage data bank 0
:
 sta $5114
 rts
; Hooks run for every shot; only switch banks when stage 4 is actually active.
Stage4ShotHitBanked:
 lda stage_id
 cmp #4
 bne @none
 jsr StageCodeIn
 jsr Stage4ShotHit
 php
 jsr StageCodeOut
 plp
 rts
@none:
 clc
 rts
Stage4LaserHitBanked:
 lda stage_id
 cmp #4
 bne @skip
 jsr StageCodeIn
 jsr Stage4LaserHit
 jmp StageCodeOut
@skip:
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
 sta boss_dirty
 sta phase_timer
 sta phase_hi
 sta wave_state
 sta wave_timer
 sta player_dead
 sta player_xf
 sta player_yf
 sta boss_hp
 lda route_flag
 bne @retain_power
 lda #0
 sta power_slot
 sta power_missile
 sta power_double
 sta power_laser
 sta power_options
 sta power_shield
 sta player_speed
@retain_power:
 lda #0
 sta route_flag
 lda chapter
 cmp #2
 beq @chapter2
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
 jmp @based
@chapter2:
 ; Nemesis 2: one 8 KiB descriptor per map in banks N2_MAP_BANK..+11, at $8000.
 lda stage_id
 sec
 sbc #1
 clc
 adc #N2_MAP_BANK
 sta stage_bank
 jsr LoadDataBank
 lda #$80
 sta stagebase
@based:
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
 jsr Stage2Init
 jsr Stage3Init
 jsr StageCodeIn
 jsr Stage4Init
 jsr StageCodeOut
 jsr TargetInit
 lda #$50
 sta player_x
 lda #$4a
 sta player_y
 ldx #0
@history:
 lda player_x
 sta HISTORY,x
 lda player_y
 sta HISTORY+1,x
 inx
 inx
 cpx #128
 bne @history
 lda #90
 sta player_iframes
 lda #0
 sta fire_delay
 sta GamePace_Phase
 sta GamePace_Edges
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
 lda sound_muted
 beq @audio_enabled
 lda #0
 sta audio_on
 sta $4015
@audio_enabled:
 lda #$a0
 sta $2000
 lda #$1c
 sta $2001
 cli
 rts

; Construct one column using the original six-metatile script. No full-map RAM.
DrawColumn:
 lda #0
 sta ptr
 lda stagebase
 sta ptr+1
 ldy #12
 lda (ptr),y            ; metatile bank ($5115 value) named by the descriptor
 sta $5115
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
 lda chapter
 cmp #1
 bne :+
 jsr StageEvents
:
 lda #0
 sta new_column
 lda phase
 cmp #2
 beq @noscroll
 cmp #4
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
 lda chapter
 cmp #1
 bne @no_chapter1_logic
 jsr Stage2Tick
 jsr Stage3Tick
 jsr StageCodeIn
 jsr Stage4Tick
 jsr StageCodeOut
 jsr TargetTick
 lda phase
 bne @no_chapter1_logic
 jsr SpawnWaves
@no_chapter1_logic:
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
 ; Source p02:99EB/99F7/9A0F, composited to two NES sprites.
 lda #0
 sta sprite_frame
 sta sprite_pal
 sta sprite_flags
 lda pad
 and #(BTN_UP|BTN_DOWN)
 cmp #BTN_UP
 bne :+
 inc sprite_frame
:
 cmp #BTN_DOWN
 bne :+
 lda #2
 sta sprite_frame
:
 lda power_shield
 beq @ship_ready
 cmp #2
 bcs @strong_shield
 lda sprite_frame
 clc
 adc #3
 sta sprite_frame
 lda logic
 and #4
 beq @ship_ready
 lda #1
 sta sprite_pal
 bne @shield_blink
@strong_shield:
 lda sprite_frame
 clc
 adc #9
 sta sprite_frame
 lda logic
 and #4
 beq @ship_ready
 lda #3
 sta sprite_pal
@shield_blink:
 lda sprite_frame
 clc
 adc #3
 sta sprite_frame
@ship_ready:
 jsr DrawSprite
@actors:
 jsr ActorsDraw
 jsr Stage2Draw
 jsr Stage3Draw
 jsr StageCodeIn
 jsr Stage4Draw
 jsr StageCodeOut
 jsr TargetDraw
 jsr UpdateHUD
 lda logic
 and #7
 bne @qa_done
 ; Read-only QA snapshot: allows tests to inspect volatile cart RAM via libretro.
 ldx #31
@qa:
 lda $6600,x
 sta $0700,x
 lda $6900,x
 sta $0720,x
 lda OBJECTS,x
 sta $0740,x
 lda $6b00,x
 sta $0760,x
 dex
 bpl @qa
@qa_done:
 ; Group spawner production QA counters; $07C4/$07C5 are outside
 ; title state ($07E0..$07EF) and outside stage collision cache.
 lda $6918
 sta $07c4
 lda $6919
 sta $07c5
 lda cheat_flags
 and #2
 beq :+
 jsr CheatDebugRow
:
 ; Read-only QA mirror of the 17 actor records (type, X, Y, frame) at
 ; $0780..$07C3 and the ten enemy-shot flags at $07C6..$07CF, refreshed with
 ; the snapshot above. Tests inspect it; gameplay never reads it.
 lda logic
 and #7
 bne @mirror_done
 ldx #0
 ldy #0
@mirror:
 lda OBJECTS,x
 sta $0780,y
 lda OBJECTS+6,x
 sta $0781,y
 lda OBJECTS+4,x
 sta $0782,y
 lda OBJECTS+12,x
 sta $0783,y
 iny
 iny
 iny
 iny
 txa
 clc
 adc #32
 tax
 bne @mirror
 ldx #0
 ldy #0
@mirror_hi:
 lda OBJECTS+256,x
 sta $07a0,y
 lda OBJECTS+256+6,x
 sta $07a1,y
 lda OBJECTS+256+4,x
 sta $07a2,y
 lda OBJECTS+256+12,x
 sta $07a3,y
 iny
 iny
 iny
 iny
 txa
 clc
 adc #32
 tax
 bne @mirror_hi
 lda OBJECTS+512
 sta $07c0
 lda OBJECTS+512+6
 sta $07c1
 lda OBJECTS+512+4
 sta $07c2
 lda OBJECTS+512+12
 sta $07c3
 ldx #0
 ldy #0
@mirror_shots:
 lda ENEMY_SHOTS,x
 sta $07c6,y
 iny
 txa
 clc
 adc #16
 tax
 cpx #160
 bne @mirror_shots
@mirror_done:
 rts

MovePlayer:
 ; Source p02:9B0D,9B4D: signed 8.8 base $0080 times 3+min(speed,7).
 ; Opposite directions cancel, and diagonal movement keeps both source axes.
 lda player_speed
 cmp #8
 bcc :+
 lda #7
:
 clc
 adc #3
 lsr a
 sta temp2
 lda #0
 ror a
 sta temp
 lda pad
 and #(BTN_UP|BTN_DOWN)
 cmp #BTN_UP
 beq @up
 cmp #BTN_DOWN
 beq @down
 jmp @horizontal
@up:
 lda player_yf
 sec
 sbc temp
 sta player_yf
 lda player_y
 sbc temp2
 bcs :+
 lda #0
 sta player_yf
:
 sta player_y
 jmp @horizontal
@down:
 lda player_yf
 clc
 adc temp
 sta player_yf
 lda player_y
 adc temp2
 cmp #166
 bcc :+
 lda #0
 sta player_yf
 lda #165
:
 sta player_y
@horizontal:
 lda pad
 and #(BTN_LEFT|BTN_RIGHT)
 cmp #BTN_LEFT
 beq @left
 cmp #BTN_RIGHT
 beq @right
 rts
@left:
 lda player_xf
 sec
 sbc temp
 sta player_xf
 lda player_x
 sbc temp2
 cmp #8
 bcs :+
 lda #0
 sta player_xf
 lda #8
:
 sta player_x
 rts
@right:
 lda player_xf
 clc
 adc temp
 sta player_xf
 lda player_x
 adc temp2
 cmp #217
 bcc :+
 lda #0
 sta player_xf
 lda #216
:
 sta player_x
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

DrawSprite8:
 ldx sprite_index
 cpx #$fc
 bcs @done
 ldy sprite_frame
 lda SpriteCode,y
 sta OAM+1,x
 lda sprite_y
 sta OAM,x
 lda sprite_pal
 ora sprite_flags
 sta OAM+2,x
 lda sprite_x
 sta OAM+3,x
 txa
 clc
 adc #4
 sta sprite_index
@done:rts

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
 lda stage_id
 eor HUD+3
 cmp #$30
 bne @update
 lda player_lives
 eor HUD+8
 cmp #$30
 bne @update
 lda power_slot
 eor HUD+15
 cmp #$30
 bne @update
 lda power_options
 eor HUD+21
 cmp #$30
 bne @update
 lda GamePace_Mode
 beq @check_30
 cmp #1
 beq @check_40
 lda #'6'
 bne @check_pace_char
@check_40:
 lda #'4'
 bne @check_pace_char
@check_30:
 lda #'3'
@check_pace_char:
 cmp HUD+29
 bne @update
 rts
@update:
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
 sta HUD+15
 lda power_options
 clc
 adc #$30
 sta HUD+21
 lda GamePace_Mode
 beq @speed_30
 cmp #1
 beq @speed_40
 lda #'6'
 bne @speed_draw
@speed_40:
 lda #'4'
 bne @speed_draw
@speed_30:
 lda #'3'
@speed_draw:
 sta HUD+29
 lda #'0'
 sta HUD+30
 lda #1
 sta hud_pending
 rts

AdvanceStage:
 lda #EVENT_CLEAR
 ldx #0
 jsr Flow_Event
 cmp #ACTION_LOAD
 bne @scene
 lda #1
 sta route_flag
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
SpritePalette: .byte $0f,$30,$16,$12,$0f,$16,$30,$26,$0f,$28,$30,$16,$0f,$30,$1c,$26
HUDTemplate: .byte "ST:1  L:3  PWR:0  OP:0   SPD:30 "
