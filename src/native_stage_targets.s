; Common original MSX secret-target transport for N1 stages 1, 4 and 7.
; From Nemesis-disassembly p03:$B06A-$B136: one marker at $FC/$88 (type 2),
; two markers at $C0/$10 (type 3), $104/$10 (type 4), and $177/$38 (type 1).
; E06C remembers last distinct type; E06D counts until three distinct touches.
; The original sends a third touch to source bonus route for the current level.
; Nemesis stages 2/3 already have independent *single-touch* routes.
.setcpu "6502"
.include "native.inc"
.include "campaign.inc"
.include "longbranch.inc"
.import Flow_State,Flow_Event,DrawSprite,LoadStage
.export TargetNewGame,TargetInit,TargetTick,TargetDraw,Target_State
.segment "BSS"
Target_State:
tg_type:        .res 1 ; zero inactive; original markers 1..4
tg_x:           .res 1
tg_y:           .res 1
tg_wait:        .res 1
tg_last:        .res 1 ; persistent across stage loads
 tg_count:      .res 1 ; number of distinct original markers (0..2)
tg_hits:        .res 1
tg_bonus:       .res 1
tg_gate:        .res 1
tg_spawned:     .res 1
tg_stage_1:     .res 1
tg_stage_4a:    .res 1
tg_stage_4b:    .res 1
tg_stage_7:     .res 1
.segment "ACTORS"
TargetNewGame:
 lda #0
 ldx #13
@clear: sta Target_State,x
 dex
 bpl @clear
 rts
TargetInit:
 lda #0
 sta tg_type
 sta tg_x
 sta tg_y
 sta tg_wait
 sta tg_bonus
 sta tg_gate
 sta tg_spawned
 sta tg_stage_1
 sta tg_stage_4a
 sta tg_stage_4b
 sta tg_stage_7
 rts

TargetTick:
 lda stage_id
 cmp #1
 beq @eligible
 cmp #4
 beq @eligible
 cmp #7
 jne @done
@eligible:
 lda phase
 cmp #14
 jeq @bonus_wait
 cmp #13
 jeq @done
 cmp #4
 jcs @done
 lda new_column
 jeq @contact
 ; Original coordinates are measured in 8-pixel source columns.
 lda stage_id
 cmp #1
 bne @stage4
 lda worldhi
 bne @move
 lda worldlo
 cmp #$fc
 bne @move
 lda tg_stage_1
 bne @move
 inc tg_stage_1
 lda #2
 ldx #$88
 jsr @spawn
 jmp @contact
@stage4:
 cmp #4
 bne @stage7
 lda worldhi
 bne @four_b
 lda worldlo
 cmp #$c0
 bne @move
 lda tg_stage_4a
 bne @move
 inc tg_stage_4a
 lda #3
 ldx #$10
 jsr @spawn
 jmp @contact
@four_b:
 lda worldhi
 cmp #1
 bne @move
 lda worldlo
 cmp #$04
 bne @move
 lda tg_stage_4b
 bne @move
 inc tg_stage_4b
 lda #4
 ldx #$10
 jsr @spawn
 jmp @contact
@stage7:
 lda worldhi
 cmp #1
 bne @move
 lda worldlo
 cmp #$77
 bne @move
 lda tg_stage_7
 bne @move
 inc tg_stage_7
 lda #1
 ldx #$38
 jsr @spawn
 jmp @contact
@move:
 lda tg_type
 jeq @contact
 lda tg_x
 sec
 sbc #8
 sta tg_x
 bcs @contact
 lda #0
 sta tg_type
@contact:
 lda tg_type
 beq @stage_gate
 lda player_y
 sec
 sbc tg_y
 clc
 adc #8
 cmp #16
 bcs @stage_gate
 lda player_x
 sec
 sbc tg_x
 cmp #16
 bcs @stage_gate
 ; This is a *new* target contact. Compare types, as the MSX does.
 lda tg_type
 cmp tg_last
 beq @stage_gate ; repeated marker is ignored, not consumed
 sta tg_last
 inc tg_hits
 inc tg_count
 lda tg_count
 cmp #3
 bcc @disable
 lda #0
 sta tg_count
 lda #14
 sta phase
 lda #64
 sta tg_wait
 lda #$cd
 sta audio_cmd
 inc tg_bonus
@disable:
 lda #0
 sta tg_type
 rts
@stage_gate:
 ; Stage4 has not yet ported its two distinct scripted bosses. The original
 ; first boss warning occurs at $0128; do not let unimplemented gameplay
 ; silently scroll through it. The secret route at $0104 remains reachable.
 lda stage_id
 cmp #4
 jne @done
 lda new_column
 beq @done
 lda worldhi
 cmp #1
 jcc @done
 jne @gate
 lda worldlo
 cmp #$28
 bcc @done
@gate:
 inc tg_gate
 lda #13
 sta phase
 rts
@bonus_wait:
 dec tg_wait
 jne @done
 lda #EVENT_BONUS
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
@done: rts
@spawn:
 ; A = type, X = MSX Y coordinate. X=$F0 on entrance.
 sta tg_type
 stx tg_y
 lda #$f0
 sta tg_x
 inc tg_spawned
 rts

TargetDraw:
 lda tg_type
 beq @done
 lda mode
 cmp #1
 jne @done
 lda tg_x
 sta sprite_x
 lda tg_y
 clc
 adc #15
 sta sprite_y
 lda #124
 sta sprite_frame
 lda #2
 sta sprite_pal
 lda #0
 sta sprite_flags
 jsr DrawSprite
@done: rts
