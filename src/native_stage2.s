; Nemesis (MSX) stage 2: original source-derived events, not a generic wave.
; References: p03:$AB86-$ABD3 (900-frame rock rain), $AC13-$AC81
; (six five-rock walls), $ACBD-$AD16 (type 8 growth), $B091-$B142
; (secret target $0190 and 64-frame freeze); p01:$6D66-$6DA5 (finish).
; Bonus-stage transitions: p01:$6F97-$6FB2 and native campaign router.
.setcpu "6502"
.include "native.inc"
.include "actors.inc"
.include "boss.inc"
.include "campaign.inc"
.include "longbranch.inc"
.import SpawnActor, RNG, DrawSprite, EnterBigCore, AdvanceStage, LoadStage
.import Flow_State, Flow_Event
.export Stage2Init, Stage2Tick, Stage2Draw, Stage2RockInit, Stage2RockFrame
.export S2_State
.segment "BSS"
; Public QA symbols via native.lbl. These are in cartridge work RAM, not ExRAM.
S2_State:
s2_wall_left:     .res 1
s2_wall_idx:      .res 1
s2_target:        .res 1   ; 0 absent, 1 visible, 2 touched
s2_target_x:      .res 1
s2_bonus_wait:    .res 1
s2_rain_lo:       .res 1
s2_rain_hi:       .res 1
s2_rain_period:   .res 1
s2_attempts_lo:   .res 1
s2_attempts_hi:   .res 1
s2_spawned_lo:    .res 1
s2_spawned_hi:    .res 1
s2_wall_events:   .res 1
s2_target_hits:   .res 1
s2_dropped:       .res 1
s2_rain_finished: .res 1
.segment "ACTORS"
Stage2Init:
 lda #0
 ldx #15
@clear:
 sta S2_State,x
 dex
 bpl @clear
 rts

; Called once per live logical frame, after movement and the source-column tick.
Stage2Tick:
 lda stage_id
 cmp #2
 beq @stage2
 cmp #9
 jcc @done
 cmp #13
 bcs @done
 jmp BonusStageTick
@stage2:
 lda phase
 beq @travel
 cmp #9
 jeq @rain
 cmp #10
 jeq @bonus
 cmp #1
 jeq @post_rain
@done:rts
@travel:
 lda new_column
 beq @wall_pending
 jsr SourceWallCheck
 jsr TargetAdvance
@wall_pending:
 jsr WallRelease
 lda s2_target
 cmp #1
 bne @endtravel
 ; Source p03:$B0DD checks |shipY-targetY| < 8 and X in [targetX,targetX+15].
 lda player_y
 sec
 sbc #$88
 clc
 adc #8
 cmp #16
 bcs @endtravel
 lda player_x
 sec
 sbc s2_target_x
 cmp #16
 bcs @endtravel
 lda #2
 sta s2_target
 inc s2_target_hits
 lda #10
 sta phase
 lda #64
 sta s2_bonus_wait
 lda #$ad
 sta audio_cmd
 rts
@endtravel:
 lda worldhi
 cmp #1
 jcc @done
 bne @start_rain
 lda worldlo
 cmp #$cf
 jcc @done
@start_rain:
 lda #9
 sta phase
 lda #$84              ; 0x0384 = 900 frames at standard difficulty
 sta s2_rain_lo
 lda #3
 sta s2_rain_hi
 lda #$14              ; source $14 - difficulty; standard starts at zero
 sta s2_rain_period
 rts
@rain:
 lda s2_rain_lo
 bne :+
 dec s2_rain_hi
:
 dec s2_rain_lo
 lda s2_rain_lo
 ora s2_rain_hi
 beq @finish_rain
 dec s2_rain_period
 jne @done
 lda #$14
 sta s2_rain_period
 jsr RNG
 and #$0f
 asl a
 tax
 lda RainPositions,x
 sta sprite_x
 lda RainPositions+1,x
 sta sprite_y
 jsr SpawnRock
 rts
@finish_rain:
 inc s2_rain_finished
 lda #1                 ; source $6D97 releases scroll to $01DF
 sta phase
 rts
@post_rain:
 lda worldhi
 cmp #1
 jcc @done
 bne @boss
 lda worldlo
 cmp #$df
 jcc @done
@boss:
 jsr EnterBigCore      ; source final-stage boss type 1, same as stage 1
 rts
@bonus:
 dec s2_bonus_wait
 jne @done
 lda #EVENT_BONUS       ; source $E1C0; bonus 2 -> 9
 ldx #0
 jsr Flow_Event
 cmp #ACTION_LOAD
 jne @done
 lda Flow_State+F_STAGE
 sta stage_id
 lda #1
 sta route_flag
 lda #$20
 sta worldlo
 lda #0
 sta worldhi
 jsr LoadStage
 rts

; Stage 9-12 are source bonus routes. Their event markers are in the
; original compact stage descriptors (bytes 4..5), not invented timers.
BonusStageTick:
 lda new_column
 beq @done
 lda #4
 sta ptr
 lda stagebase
 sta ptr+1
 ldy #5                 ; exact source endpoint in descriptor bytes 4..5
 lda worldhi
 cmp (ptr),y
 jcc @done
 bne @clear
 dey
 lda worldlo
 cmp (ptr),y
 jcc @done
@clear:
 jsr AdvanceStage
@done:rts

SourceWallCheck:
 lda worldhi
 cmp #1
 bne @target
 ldx #5
@loop:
 lda worldlo
 cmp WallDistances,x
 beq @start
 dex
 bpl @loop
 jmp @target
@start:
 inc s2_wall_events
 lda #5
 sta s2_wall_left
 lda #0
 sta s2_wall_idx
@target:
 lda worldhi
 cmp #1
 jne @done
 lda worldlo
 cmp #$90
 jne @done
 lda s2_target
 jne @done
 lda #1
 sta s2_target
 lda #$f0
 sta s2_target_x
@done:rts
TargetAdvance:
 lda s2_target
 cmp #1
 jne @done
 lda worldhi
 cmp #1
 jne @done
 lda worldlo
 cmp #$90
 beq @done             ; spawn frame starts at source X=$F0
 lda s2_target_x
 sec
 sbc #8
 sta s2_target_x
 bcs @done
 lda #0
 sta s2_target
@done:rts
WallRelease:
 lda s2_wall_left
 beq @done
 ldx s2_wall_idx
 lda RockWallY,x
 sta sprite_y
 lda #$c0
 sta sprite_x
 jsr SpawnRock
 inc s2_wall_idx
 dec s2_wall_left
@done:rts
SpawnRock:
 inc s2_attempts_lo
 bne :+
 inc s2_attempts_hi
:
 lda #0
 sta sprite_pal
 lda #8
 jsr SpawnActor
 bcc @success
 inc s2_dropped
 rts
@success:
 inc s2_spawned_lo
 bne :+
 inc s2_spawned_hi
:
 rts
Stage2Draw:
 lda stage_id
 cmp #2
 jne @done
 lda s2_target
 cmp #1
 jne @done
 lda mode
 cmp #1
 jne @done
 lda s2_target_x
 sta sprite_x
 lda #$97               ; source target at Y=$88, native DrawSprite +15
 sta sprite_y
 lda #124               ; existing source-derived 16x16 marker artwork
 sta sprite_frame
 lda #2
 sta sprite_pal
 lda #0
 sta sprite_flags
 jsr DrawSprite
@done:rts

; Type 8 source grows across three 10-frame intervals with source frames
; $C0/$C4/$C8; becomes vulnerable only after the third. The first source
; game loop does not fire these rocks at the ship (p03:$ACEA-$ACFC).
Stage2RockInit:
 ldy #O_FLAGS
 lda #0
 sta (objptr),y
 ldy #O_CLOCK
 lda #10
 sta (objptr),y
 ldy #O_LIFE
 lda #0
 sta (objptr),y
 ldy #O_FRAME
 lda #$c0
 sta (objptr),y
 ldy #O_COLOR
 lda #5
 sta (objptr),y
 rts
Stage2RockFrame:
 ; Source rocks remain bound to the scrolling screen during travel.
 lda phase
 cmp #0
 beq @scroll
 cmp #1
 bne @animate
@scroll:
 ldy #O_X
 lda (objptr),y
 cmp #9
 bcs @move
 lda #0
 ldy #O_TYPE
 sta (objptr),y
 rts
@move:
 sec
 sbc #1
 sta (objptr),y
@animate:
 ldy #O_STATE
 lda (objptr),y
 jne @done
 ldy #O_CLOCK
 lda (objptr),y
 sec
 sbc #1
 sta (objptr),y
 jne @done
 lda #10
 sta (objptr),y
 ldy #O_LIFE
 lda (objptr),y
 clc
 adc #1
 sta (objptr),y
 tax
 lda RockFrames-1,x
 ldy #O_FRAME
 sta (objptr),y
 lda RockColours-1,x
 ldy #O_COLOR
 sta (objptr),y
 cpx #3
 jne @done
 lda #1
 ldy #O_STATE
 sta (objptr),y
 lda #3
 ldy #O_FLAGS
 sta (objptr),y
@done:rts

WallDistances: .byte $44,$4c,$70,$78,$80,$88
RockWallY: .byte $8c,$6c,$4c,$2c,$0c
RockFrames: .byte $c0,$c4,$c8
RockColours: .byte 5,7,15
; x,y pairs from source p03:$ABD3, all 16 source spawn positions.
RainPositions:
 .byte $08,$10,$98,$10,$20,$30,$48,$30
 .byte $70,$48,$48,$60,$30,$80,$98,$80
 .byte $08,$90,$28,$a8,$80,$a8,$18,$c0
 .byte $60,$c0,$08,$d8,$08,$f0,$98,$f0
