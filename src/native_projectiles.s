.setcpu "6502"
.include "longbranch.inc"
.include "native.inc"
.include "actors.inc"
.import LaserStep,LaserDraw
.import BossShotHit,Stage4ShotHit
.import DrawSprite8
.import DrawSprite,PlayerHit,ActorKilled,ObjectPointer,AngleTable,SineTable
.export ProjectileFrame,ProjectileDraw,TerrainSolid,AimBullet
.segment "CODE"

; sprite_x/y are source coordinates. C=solid. Source tile ID is returned in A.
; Terrain uses the source character classification, not palette or visible RGB.
TerrainSolid:
 lda sprite_y
 cmp #176
 bcs @empty
 lsr a
 lsr a
 lsr a
 sta s5
 lda sprite_x
 clc
 adc camera
 pha
 and #$f8
 asl a
 sta ptr3
 lda #0
 rol a
 sta ptr3+1
 asl ptr3
 rol ptr3+1
 lda ptr3+1
 clc
 adc #$60
 sta ptr3+1
 pla
 ldy s5
 lda (ptr3),y
 beq @empty
 cmp #$77
 bcc @solid
 sta s5
 lda stage_id
 cmp #3
 beq @s3
 cmp #4
 beq @s4
@empty:clc
 rts
@s3:
 lda s5
 sec
 sbc #$a1
 cmp #$1b
 bcc @solid
 clc
 rts
@s4:
 lda s5
 sec
 sbc #$ba
 cmp #12
 bcc @solid
 clc
 rts
@solid:sec
 rts

ProjectileFrame:
 jsr UpdateOptions
 jsr Upgrade
 ; Terrain collision at the ship's center and nose, using source map IDs.
 lda player_x
 clc
 adc #5
 sta sprite_x
 lda player_y
 clc
 adc #8
 sta sprite_y
 jsr TerrainSolid
 bcc :+
 jsr PlayerHit
:
 lda sprite_x
 clc
 adc #7
 sta sprite_x
 jsr TerrainSolid
 bcc :+
 jsr PlayerHit
:
 lda mode
 cmp #1
 beq :+
 rts
:
 jsr FirePlayer
 lda #0
 sta shots_done
@shots:
 lda shots_done
 asl a
 asl a
 asl a
 asl a
 sta shot_ptr
 lda #$66
 sta shot_ptr+1
 ldy #0
 lda (shot_ptr),y
 jeq @next
 sta sf
 cmp #3
 bne :+
 jsr LaserStep
 jmp @next
:
 ldy #1
 lda (shot_ptr),y
 ldy #3
 clc
 adc (shot_ptr),y
 ldy #1
 sta (shot_ptr),y
 cmp #248
 jcs @erase
 ldy #2
 lda (shot_ptr),y
 ldy #4
 clc
 adc (shot_ptr),y
 ldy #2
 sta (shot_ptr),y
 cmp #174
 jcs @erase
 lda sf
 cmp #4
 bne @terrain
 ; Missile lands then follows the upper surface, as source type 4 does.
 lda (shot_ptr),y
 clc
 adc #8
 sta sprite_y
 ldy #1
 lda (shot_ptr),y
 sta sprite_x
 jsr TerrainSolid
 bcc @terrain
 ldy #4
 lda #0
 sta (shot_ptr),y
 ldy #3
 lda #4
 sta (shot_ptr),y
 jmp @hit
@terrain:
 ldy #1
 lda (shot_ptr),y
 sta sprite_x
 ldy #2
 lda (shot_ptr),y
 sta sprite_y
 jsr TerrainSolid
 jcs @erase
@hit:
 jsr BossShotHit
 jcs @erase
 jsr Stage4ShotHit
 jcs @erase
 ldy #1
 lda (shot_ptr),y
 sta s6
 iny
 lda (shot_ptr),y
 sta s7
 lda #0
 sta obj
 sta objptr
 lda #>OBJECTS
 sta objptr+1
@enemy:
 ldy #O_FLAGS
 lda (objptr),y
 and #2
 beq @enext
 ; Source-like 18-pixel vertical overlap with enemy's 16-pixel graphic.
 ldy #O_Y
 lda s7
 sec
 sbc (objptr),y
 clc
 adc #2
 cmp #18
 bcs @enext
 ldy #O_X
 lda s6
 sec
 sbc (objptr),y
 clc
 adc #8
 cmp #24
 bcs @enext
 ldy #O_HP
 lda (objptr),y
 sec
 sbc #1
 sta (objptr),y
 bne @erase
 jsr ActorKilled
 jmp @erase
@enext:
 lda objptr
 clc
 adc #32
 sta objptr
 bcc :+
 inc objptr+1
:
 inc obj
 lda obj
 cmp actor_limit
 bne @enemy
 jmp @next
@erase:
 ldy #0
 lda #0
 sta (shot_ptr),y
@next:
 inc shots_done
 lda shots_done
 cmp #9
 jne @shots
 jsr EnemyShots
 rts

Upgrade:
 lda pressed
 and #BTN_A
 jeq @done
 lda power_slot
 beq @done
 cmp #1
 beq @speed
 cmp #2
 beq @missile
 cmp #3
 beq @double
 cmp #4
 beq @laser
 cmp #5
 beq @option
 cmp #6
 beq @shield
 rts
@speed:
 lda player_speed
 cmp #8
 bcs @done
 inc player_speed
 jmp @consume
@missile:
 lda power_missile
 cmp #2
 bcs @done
 inc power_missile
 jmp @consume
@double:
 lda power_double
 bne @done
 lda #1
 sta power_double
 lda #0
 sta power_laser
 jmp @consume
@laser:
 lda power_laser
 cmp #2
 bcs @done
 inc power_laser
 lda #0
 sta power_double
 jmp @consume
@option:
 lda power_options
 cmp #2
 bcs @done
 lda power_options
 bne @second_option
 ldx #0
@fill_history:
 lda player_x
 sta HISTORY,x
 lda player_y
 sta HISTORY+1,x
 inx
 inx
 cpx #128
 bne @fill_history
@second_option:
 inc power_options
 jmp @consume
@shield:
 lda power_shield
 bne @done
 lda #10
 sta power_shield
@consume:
 lda #0
 sta power_slot
 lda #$a9
 sta audio_cmd
@done:rts

UpdateOptions:
 ; Source p02:9C41-9C8F: direction-valid frames advance the FIFO.
 ; Only animation, not the FIFO, has a two-frame cadence at 9C90.
 lda power_options
 beq @done
 lda pad
 and #$0f
 beq @done
 cmp #3
 beq @done
 cmp #12
 beq @done
 cmp #15
 beq @done
 inc option_cursor
 lda option_cursor
 and #63
 sta option_cursor
 asl a
 tax
 lda player_x
 sta HISTORY,x
 lda player_y
 sta HISTORY+1,x
@positions:
 lda option_cursor
 sec
 sbc #8
 and #63
 asl a
 tax
 lda HISTORY,x
 sta OPTIONS
 lda HISTORY+1,x
 sta OPTIONS+1
 lda option_cursor
 sec
 sbc #16
 and #63
 asl a
 tax
 lda HISTORY,x
 sta OPTIONS+2
 lda HISTORY+1,x
 sta OPTIONS+3
@done:rts

FirePlayer:
 lda pad
 and #BTN_B
 beq @released
 lda pressed
 and #BTN_B
 bne @fire
 lda fire_delay
 beq @fire
 dec fire_delay
 rts
@released:
 lda #0
 sta fire_delay
 rts
@fire:
 lda #14
 sta fire_delay
 lda #0
 sta firing_owner
@owner:
 lda firing_owner
 beq @ship
 sec
 sbc #1
 asl a
 tax
 lda OPTIONS,x
 sta s0
 lda OPTIONS+1,x
 sta s1
 jmp @base
@ship:
 lda player_x
 sta s0
 lda player_y
 sta s1
@base:
 lda firing_owner
 asl a
 asl a
 asl a
 asl a
 sta s2
 asl a
 clc
 adc s2
 sta shot_ptr
 lda #$66
 sta shot_ptr+1
 ldy #0
 lda (shot_ptr),y
 bne @second
 lda #1
 ldx power_laser
 beq :+
 lda #3
:
 sta (shot_ptr),y
 lda s0
 clc
 adc #16
 iny
 sta (shot_ptr),y
 lda s1
 clc
 adc #8
 and #$f8
 iny
 sta (shot_ptr),y
 lda #12
 iny
 sta (shot_ptr),y
 lda #0
 iny
 sta (shot_ptr),y
 lda #$a7
 sta audio_cmd
 lda power_laser
 beq @second
 ldy #3
 lda #0
 sta (shot_ptr),y
 iny
 lda firing_owner
 sta (shot_ptr),y
 iny
 lda #0
 sta (shot_ptr),y
 iny
 lda #8
 ldx power_laser
 cpx #2
 bcc :+
 lda #15
:
 sta (shot_ptr),y
@second:
 lda shot_ptr
 clc
 adc #16
 sta shot_ptr
 lda power_double
 beq @missile
 ldy #0
 lda (shot_ptr),y
 bne @missile
 lda #2
 sta (shot_ptr),y
 lda s0
 clc
 adc #8
 iny
 sta (shot_ptr),y
 lda s1
 iny
 sta (shot_ptr),y
 lda #12
 iny
 sta (shot_ptr),y
 lda #$fa
 iny
 sta (shot_ptr),y
@missile:
 lda power_missile
 beq @next
 lda shot_ptr
 clc
 adc #16
 sta shot_ptr
 ldy #0
 lda (shot_ptr),y
 bne @next
 lda #4
 sta (shot_ptr),y
 lda s0
 clc
 adc #8
 iny
 sta (shot_ptr),y
 lda s1
 clc
 adc #8
 iny
 sta (shot_ptr),y
 lda #2
 iny
 sta (shot_ptr),y
 iny
 sta (shot_ptr),y
@next:
 inc firing_owner
 lda power_options
 cmp firing_owner
 jcs @owner
 rts

; Source-angle aiming with a build-time fixed-point velocity table; no atan at runtime.
AimBullet:
 lda #0
 sta s4
 ldy #O_X
 lda player_x
 sec
 sbc (objptr),y
 bcs :+
 eor #$ff
 clc
 adc #1
 inc s4
:
 sta s0
 ldy #O_Y
 lda player_y
 sec
 sbc (objptr),y
 bcs :+
 eor #$ff
 clc
 adc #1
 lda s4
 ora #2
 sta s4
 lda player_y
 sec
 ldy #O_Y
 sbc (objptr),y
 eor #$ff
 clc
 adc #1
:
 sta s1
 and #$f0
 clc
 adc s0
 cmp #$30
 bcc @done
 lda s0
 lsr a
 lsr a
 lsr a
 lsr a
 sta s2
 lda s1
 and #$f0
 ora s2
 tax
 lda AngleTable,x
 and #63
 tax
 lda AimVYLo,x
 sta s0
 lda AimVYHi,x
 sta s1
 lda AimVXLo,x
 sta s2
 lda AimVXHi,x
 sta s3
 lda s4
 and #1
 beq :+
 lda s2
 eor #$ff
 clc
 adc #1
 sta s2
 lda s3
 eor #$ff
 adc #0
 sta s3
:
 lda s4
 and #2
 beq :+
 lda s0
 eor #$ff
 clc
 adc #1
 sta s0
 lda s1
 eor #$ff
 adc #0
 sta s1
:
 ldx #0
@slot:
 lda ENEMY_SHOTS,x
 beq @found
 txa
 clc
 adc #16
 tax
 cpx #160
 bne @slot
@done:rts
@found:
 lda #1
 sta ENEMY_SHOTS,x
 ldy #O_X
 lda (objptr),y
 clc
 adc #8
 sta ENEMY_SHOTS+1,x
 ldy #O_Y
 lda (objptr),y
 clc
 adc #8
 sta ENEMY_SHOTS+2,x
 lda #0
 sta ENEMY_SHOTS+3,x
 sta ENEMY_SHOTS+4,x
 lda s2
 sta ENEMY_SHOTS+5,x
 lda s3
 sta ENEMY_SHOTS+6,x
 lda s0
 sta ENEMY_SHOTS+7,x
 lda s1
 sta ENEMY_SHOTS+8,x
 rts

EnemyShots:
 ldx #0
@loop:
 lda ENEMY_SHOTS,x
 jeq @next
 lda ENEMY_SHOTS+1,x
 sta s8
 lda ENEMY_SHOTS+3,x
 clc
 adc ENEMY_SHOTS+5,x
 sta ENEMY_SHOTS+3,x
 lda ENEMY_SHOTS+1,x
 adc ENEMY_SHOTS+6,x
 sta ENEMY_SHOTS+1,x
 cmp #248
 bcc :+
 lda s8
 cmp #16
 bcc @erase
:
 lda ENEMY_SHOTS+4,x
 clc
 adc ENEMY_SHOTS+7,x
 sta ENEMY_SHOTS+4,x
 lda ENEMY_SHOTS+2,x
 adc ENEMY_SHOTS+8,x
 sta ENEMY_SHOTS+2,x
 cmp #176
 bcs @erase
 lda ENEMY_SHOTS+1,x
 sec
 sbc player_x
 cmp #16
 bcs @next
 lda ENEMY_SHOTS+2,x
 sec
 sbc player_y
 cmp #16
 bcs @next
 lda power_shield
 beq @hurt
 dec power_shield
 jmp @erase
@hurt:
 txa
 pha
 jsr PlayerHit
 pla
 tax
@erase:
 lda #0
 sta ENEMY_SHOTS,x
@next:
 txa
 clc
 adc #16
 tax
 cpx #160
 jne @loop
 rts

ProjectileDraw:
 lda #0
 sta shots_done
@opts:
 lda shots_done
 cmp power_options
 bcs @startshots
 asl a
 tax
 lda OPTIONS,x
 sta sprite_x
 lda OPTIONS+1,x
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
 inc shots_done
 jmp @opts
@startshots:
 lda #0
 sta shots_done
@shots:
 lda shots_done
 asl a
 asl a
 asl a
 asl a
 tax
 lda SHOTS,x
 beq @next
 cmp #3
 bne :+
 txa
 sta shot_ptr
 lda #$66
 sta shot_ptr+1
 jsr LaserDraw
 jmp @next
:
 tay
 lda ShotFrame,y
 sta sprite_frame
 lda SHOTS+1,x
 sta sprite_x
 lda SHOTS+2,x
 clc
 adc #15
 sta sprite_y
 lda #0
 sta sprite_flags
 lda #0
 sta sprite_pal
 jsr DrawSprite
@next:
 inc shots_done
 lda shots_done
 cmp #9
 bne @shots
 lda #0
 sta shots_done
@bullets:
 lda shots_done
 asl a
 asl a
 asl a
 asl a
 tax
 lda ENEMY_SHOTS,x
 beq @bnext
 lda ENEMY_SHOTS+1,x
 sta sprite_x
 lda ENEMY_SHOTS+2,x
 clc
 adc #15
 sta sprite_y
 lda #27
 sta sprite_frame
 lda #1
 sta sprite_pal
 lda #0
 sta sprite_flags
 jsr DrawSprite8
@bnext:
 inc shots_done
 lda shots_done
 cmp #10
 bne @bullets
 rts
ShotFrame:.byte 0,123,127,125,126
; Speeds from source sine table, source initial difficulty zero, base $50.
AimVYLo:.incbin "build/native/aim.bin",0,64
AimVYHi:.incbin "build/native/aim.bin",64,64
AimVXLo:.incbin "build/native/aim.bin",128,64
AimVXHi:.incbin "build/native/aim.bin",192,64
