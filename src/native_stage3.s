; Nemesis MSX stage 3 source-target and bonus10 routing. Not a complete stage.
; Source: Nemesis-disassembly p03 B09A,B0CB,B0DD,B123 and p01 6DA7.
.setcpu "6502"
.include "native.inc"
.include "campaign.inc"
.include "longbranch.inc"
.import Flow_State,Flow_Event,LoadStage,DrawSprite,EnterBigCore
.export Stage3Init,Stage3Tick,Stage3Draw,Stage3MidbossCleared,S3_State
.segment "BSS"
S3_State:
s3_target: .res 1             ; 0 inactive,1 active,2 collected
s3_target_x: .res 1
s3_bonus_wait: .res 1
s3_collected: .res 1
s3_end_reached: .res 1
s3_midboss_done: .res 1
s3_final_started: .res 1
.segment "ACTORS"
Stage3Init:
 lda #0
 ldx #6
@clear: sta S3_State,x
 dex
 bpl @clear
 rts
Stage3Tick:
 lda stage_id
 cmp #3
 jne @done
 lda phase
 cmp #5
 jcs @boss_or_later
 lda s3_midboss_done
 jne @regular
 lda new_column
 jeq @regular
 lda worldhi
 jne @regular
 lda worldlo
 cmp #$60
 jne @regular
 jsr EnterBigCore
 rts
@boss_or_later:
 ; Native Big Core phases 5..8 are advanced by StageEvents.
 cmp #11
 jcc @done
@regular:
 lda phase
 cmp #11
 jeq @bonus_wait
 cmp #12
 jeq @done
 lda new_column
 jeq @contact
 lda worldhi
 cmp #1
 jne @contact
 lda worldlo
 cmp #$2a
 jne @advance
 lda s3_target
 jne @advance
 lda #1
 sta s3_target
 lda #$f0
 sta s3_target_x
 jmp @contact
@advance:
 lda s3_target
 cmp #1
 jne @contact
 lda s3_target_x
 sec
 sbc #8
 sta s3_target_x
 jcs @contact
 lda #0
 sta s3_target
@contact:
 lda s3_target
 cmp #1
 jne @limit
 ; Source target row $30, ship row offset tolerance [-8,+7].
 lda player_y
 sec
 sbc #$30
 clc
 adc #8
 cmp #16
 jcs @limit
 lda player_x
 sec
 sbc s3_target_x
 cmp #16
 jcs @limit
 lda #2
 sta s3_target
 inc s3_collected
 lda #11
 sta phase
 lda #64
 sta s3_bonus_wait
 lda #$ad
 sta audio_cmd
 rts
@limit:
 ; Source p01 $6DF9/$6E04: after the first boss, advance up to $01AF,
 ; then call the *same* type-1 boss sequence, not a surrogate enemy.
 lda s3_midboss_done
 jeq @done
 lda s3_final_started
 jne @done
 lda new_column
 jeq @done
 lda worldhi
 cmp #1
 jcc @done
 jne @finish
 lda worldlo
 cmp #$af
 jcc @done
@finish:
 lda #1
 sta s3_final_started
 inc s3_end_reached
 jsr EnterBigCore
 rts
@bonus_wait:
 dec s3_bonus_wait
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
Stage3Draw:
 lda stage_id
 cmp #3
 jne @done
 lda s3_target
 cmp #1
 jne @done
 lda mode
 cmp #1
 jne @done
 lda s3_target_x
 sta sprite_x
 lda #$3f                 ; Native DrawSprite adds 15 to Y, source target $30.
 sta sprite_y
 lda #124
 sta sprite_frame
 lda #2
 sta sprite_pal
 lda #0
 sta sprite_flags
 jsr DrawSprite
@done:rts

Stage3MidbossCleared:
 lda #1
 sta s3_midboss_done
 lda #0
 sta phase
 sta phase_timer
 sta phase_hi
 rts
