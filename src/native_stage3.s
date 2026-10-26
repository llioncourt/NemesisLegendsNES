; Nemesis MSX stage 3 source-target and bonus10 routing. Not a complete stage.
; Source: Nemesis-disassembly p03 B09A,B0CB,B0DD,B123 and p01 6DA7.
.setcpu "6502"
.include "native.inc"
.include "campaign.inc"
.include "longbranch.inc"
.import Flow_State,Flow_Event,LoadStage,DrawSprite
.export Stage3Init,Stage3Tick,Stage3Draw,S3_State
.segment "BSS"
S3_State:
s3_target: .res 1
s3_target_x: .res 1
s3_bonus_wait: .res 1
s3_collected: .res 1
s3_end_reached: .res 1
.segment "ACTORS"
Stage3Init:
 lda #0
 ldx #4
@clear: sta S3_State,x
 dex
 bpl @clear
 rts
Stage3Tick:
 lda stage_id
 cmp #3
 jne @done
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
 ; Stage 3's actual boss is not ported. Halt at source travel bound,
 ; never skip absent gameplay or silently mark stage 3 complete.
 lda worldhi
 cmp #1
 jcc @done
 jne @stop
 lda worldlo
 cmp #$9f
 jcc @done
@stop:
 lda #12
 sta phase
 inc s3_end_reached
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
 lda #$3f
 sta sprite_y
 lda #124
 sta sprite_frame
 lda #2
 sta sprite_pal
 lda #0
 sta sprite_flags
 jsr DrawSprite
@done:rts
