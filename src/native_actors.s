.setcpu "6502"
.include "longbranch.inc"
.include "native.inc"
.include "actors.inc"
.include "boss.inc"
.import DrawSprite, PlayerHit, SourceObjectDefaults, AngleTable, SineTable, AdvanceStage
.import MidPiece,VolcanoParticle
.import Stage2RockInit,Stage2RockFrame
.import TerrainSolid, ProjectileFrame, ProjectileDraw, AimBullet
.export ActorsFrame,ActorsDraw,SpawnCannon,SpawnWaves,ShotsFrame,InitActors
.export SpawnMidActor
.export SpawnActor, ActorKilled, ObjectPointer, RNG, FireAtPlayer, CollectCapsule
.segment "ACTORS"
InitActors:
 lda #0
 ldx #0
@clear:
 sta OBJECTS,x
 sta OBJECTS+$100,x
 sta OBJECTS+$200,x
 sta SHOTS,x
 sta ENEMY_SHOTS,x
 sta A_GLOBAL,x
 sta HISTORY,x
 sta BS,x
 inx
 bne @clear
 lda #12
 sta actor_limit
 lda #0
 sta cannon_ptr
 lda stagebase
 clc
 adc #$a
 sta cannon_ptr+1
 rts

RNG:
 lda rseed
 asl a
 bcc :+
 eor #$1d
:
 sta rseed
 rts

; Object index A (0..11) -> pointer. Does not touch X or scratch.
ObjectPointer:
 pha
 and #7
 asl a
 asl a
 asl a
 asl a
 asl a
 sta objptr
 pla
 lsr a
 lsr a
 lsr a
 clc
 adc #$6d
 sta objptr+1
 rts

; A=type, sprite_x/y=source coordinates, sprite_pal=mark, s9=optional flags.
; Return C set if all 12 records are busy. Newly created record in objptr.
SpawnActor:
 pha
 ldx #0
@find:
 txa
 jsr ObjectPointer
 ldy #O_TYPE
 lda (objptr),y
 beq SpawnFound
 inx
 cpx #12
 bne @find
 pla
 sec
 rts
SpawnMidActor:
 pha
 lda #17
 sta actor_limit
 lda mid_parts
 clc
 adc #11
 jsr ObjectPointer
SpawnFound:
 lda #0
 ldy #31
@clear:
 sta (objptr),y
 dey
 bpl @clear
 pla
 ldy #O_TYPE
 sta (objptr),y
 cmp #32
 bcc :+
 lda #1
:
 asl a
 asl a
 tax
 ldy #O_DRAW
 lda SourceObjectDefaults,x
 sta (objptr),y
 iny
 lda SourceObjectDefaults+1,x
 sta (objptr),y
 iny
 lda SourceObjectDefaults+2,x
 sta (objptr),y
 ldy #O_HP
 lda SourceObjectDefaults+3,x
 sta (objptr),y
 ldy #O_FLAGS
 lda #3
 sta (objptr),y
 lda sprite_x
 ldy #O_X
 sta (objptr),y
 lda sprite_y
 ldy #O_Y
 sta (objptr),y
 lda sprite_pal
 ldy #O_MARK
 sta (objptr),y
 beq :+
 lda #8
 ldy #O_COLOR
 sta (objptr),y
:
 lda #$80
 ldy #O_FIRE
 sta (objptr),y
 ldy #O_TYPE
 lda (objptr),y
 cmp #1
 beq @cannon
 cmp #2
 beq @two
 cmp #3
 beq @three
 cmp #4
 jeq @four
 cmp #5
 jeq @five
 cmp #6
 jeq @six
 cmp #8
 jeq @rock
 cmp #9
 jeq @nine
 cmp #$0f
 beq @native_extra
 cmp #$20
 beq @native_extra
 cmp #$12
 jeq @capsule
 cmp #$13
 jeq @capsule
 ; Unsupported source handlers remain explicitly observable, not generic motion.
 sta unknown_type
 clc
 rts
@nine:
 ; Source p03:$AD27/$AD33: three pixels left, tracking starts at x<$80.
 lda #$fd
 ldy #O_VXH
 sta (objptr),y
 lda #$ec
 ldy #O_FRAME
 sta (objptr),y
 clc
 rts
@rock:
 jsr Stage2RockInit
 clc
 rts
@native_extra:
 clc
 rts
@cannon:
 lda s9
 and #$20
 lsr a
 lsr a
 lsr a
 lsr a
 sta s8
 lda s9
 and #$40
 bne :+
 inc s8
:
 lda s8
 ldy #O_AYL
 sta (objptr),y
 lda #48
 ldy #O_FIRE
 sta (objptr),y
 clc
 rts
@two:
 lda #$fc
 ldy #O_VXH
 sta (objptr),y
 clc
 rts
@three:
 lda #4
 ldy #O_VYH
 sta (objptr),y
 ldy #O_AXH
 sta (objptr),y
 lda #$fe
 ldy #O_VXH
 sta (objptr),y
 lda #$80
 ldy #O_AYL
 sta (objptr),y
 iny
 lda #$ff
 sta (objptr),y
 clc
 rts
@four:
 lda #$80
 ldy #O_VXL
 sta (objptr),y
 iny
 lda #$fe
 sta (objptr),y
 clc
 rts
@five:
 lda sprite_y
 bmi @floor
 lda #0
 ldy #O_SIDE
 sta (objptr),y
 lda #$f8
 bne @walkframe
@floor:
 lda #1
 ldy #O_SIDE
 sta (objptr),y
 lda #$e8
@walkframe:
 ldy #O_FRAME
 sta (objptr),y
 lda #10
 ldy #O_LIFE
 sta (objptr),y
 jsr RNG
 and #31
 clc
 adc #45
 ldy #O_CLOCK
 sta (objptr),y
 lda #2
 ldy #O_VXH
 sta (objptr),y
 clc
 rts
@six:
 lda #120
 ldy #O_LIFE
 sta (objptr),y
 lda #$60
 ldy #O_AYL
 sta (objptr),y
 lda #$fa
 ldy #O_VYH
 sta (objptr),y
 lda #2
 ldx sprite_x
 bpl :+
 lda #$fe
:
 ldy #O_VXH
 sta (objptr),y
 clc
 rts
@capsule:
 lda #0
 ldy #O_FLAGS
 sta (objptr),y
 lda #1
 ldy #O_DRAW
 sta (objptr),y
 clc
 rts

SpawnCannon:
 lda new_column
 beq @done
@next:
 ldy #1
 lda (cannon_ptr),y
 cmp #$ff
 beq @done
 cmp worldhi
 bcc @due
 bne @done
 dey
 lda (cannon_ptr),y
 cmp worldlo
 bcc @due
 bne @done
@due:
 ldy #2
 lda (cannon_ptr),y
 sta s9
 and #31
 asl a
 asl a
 asl a
 sta sprite_y
 lda #248
 sta sprite_x
 lda #0
 sta sprite_pal
 lda #1
 jsr SpawnActor
 lda cannon_ptr
 clc
 adc #3
 sta cannon_ptr
 bcc @next
 inc cannon_ptr+1
 jmp @next
@done:rts

MarkNext:
 lda mark_counter
 and #15
 tax
 inc mark_counter
 lda Marks,x
 sta sprite_pal
 rts

SpawnWaves:
 lda phase
 bne @done
 lda stage_id
 cmp #9
 bcs @done
 jsr OpeningWave
 lda worldhi
 lsr a
 lda worldlo
 ror a
 lsr a
 lsr a
 lsr a
 lsr a
 and #15
 tay
 lda #0
 sta ptr2
 lda stagebase
 clc
 adc #$d
 sta ptr2+1
 lda (ptr2),y
 sta wave_side
 and #1
 beq :+
 jsr SpawnPair
:
 lda wave_side
 and #2
 beq :+
 jsr SpawnStream
:
 lda wave_side
 and #4
 beq :+
 jsr SpawnLeft
:
 lda wave_side
 and #8
 beq :+
 jsr SpawnBottom
:
 ; Bit 4 = original type-9 flock; bit 5 = original mixed type5/6.
 ; Source p03:$A359-$A37B calls six independently selected groups.
 lda wave_side
 and #$10
 beq :+
 jsr SpawnFlock
:
 lda wave_side
 and #$20
 beq :+
 jsr SpawnMixed
:
 ; Any later reserved bits stay visible to diagnostics, not invented actors.
 lda wave_side
 and #$c0
 beq @done
 sta unknown_type
@done:rts

OpeningWave:
 lda wave_state
 bne @active
 lda new_column
 jeq @done
 lda worldhi
 jne @done
 lda worldlo
 cmp #$80
 jcs @done
 and #7
 jne @done
 inc wave_serial
 lda wave_serial
 and #7
 asl a
 asl a
 sta group_current
 tax
 lda wave_serial
 sta GROUPS,x
 lda #6
 sta GROUPS+1,x
 sta GROUPS+2,x
 sta wave_count
 lda #$10
 sta ptr2
 lda stagebase
 clc
 adc #$d
 sta ptr2+1
 ldy #0
 lda (ptr2),y
 ldx wave_serial
 txa
 and #1
 beq @low
 lda (ptr2),y
 lsr a
 lsr a
 lsr a
 lsr a
 jmp @type
@low:
 lda (ptr2),y
@type:
 and #15
 sta wave_type
 lda #8
 ldx wave_serial
 txa
 and #1
 beq @upper
 lda #152
 bne @height
@upper:lda #8
@height:sta wave_y
 lda #1
 sta wave_timer
 sta wave_state
@active:
 dec wave_timer
 bne @done
 lda #4
 sta wave_timer
 lda #240
 sta sprite_x
 lda wave_y
 sta sprite_y
 lda #0
 sta sprite_pal
 lda wave_type
 jsr SpawnActor
 bcs @done
 lda #1
 ldy #O_GROUP
 sta (objptr),y
 iny
 lda group_current
 sta (objptr),y
 dec wave_count
 bne @done
 lda #0
 sta wave_state
@done:rts

SpawnPair:
 lda pair_timer
 beq @spawn
 dec pair_timer
 bne @done
@spawn:
 lda #112
 sta pair_timer
 jsr MarkNext
 lda #240
 sta sprite_x
 lda #48
 sta sprite_y
 lda #3
 jsr SpawnActor
 lda #96
 sta sprite_y
 lda #3
 jsr SpawnActor
@done:rts
SpawnStream:
 lda stream_left
 bne @active
 lda #3
 sta stream_left
 lda #112
 sta stream_timer
 rts
@active:
 dec stream_timer
 bne @done
 lda #8
 sta stream_timer
 dec stream_left
 ldx stream_left
 lda StreamY,x
 sta sprite_y
 lda #240
 sta sprite_x
 lda #0
 sta sprite_pal
 lda #4
 jsr SpawnActor
@done:rts
SpawnLeft:
 lda left_left
 bne @active
 lda #8
 sta left_left
 lda #1
 sta left_timer
@active:
 dec left_timer
 bne @done
 lda #112
 sta left_timer
 dec left_left
 ldx left_left
 lda LeftY,x
 sta sprite_y
 lda #0
 sta sprite_x
 jsr MarkNext
 lda #5
 jsr SpawnActor
@done:rts
SpawnBottom:
 lda bottom_left
 bne @active
 lda #4
 sta bottom_left
 lda #1
 sta bottom_timer
@active:
 dec bottom_timer
 bne @done
 lda #96
 sta bottom_timer
 dec bottom_left
 lda #240
 ldx bottom_left
 bne :+
 lda #0
:
 sta sprite_x
 lda #143
 sta sprite_y
 jsr MarkNext
 lda #6
 jsr SpawnActor
@done:rts

; Source p03:$A5D7-$A60C: eight type-9 units, 7 frames apart.
; First four enter at y=$88, last four at y=$18; 60-frame recharge.
SpawnFlock:
 lda flock_left
 bne @active
 lda flock_timer
 beq @reset
 dec flock_timer
 bne @done
@reset:
 lda #8
 sta flock_left
 lda #1
 sta flock_timer
 rts
@active:
 dec flock_timer
 bne @done
 lda #7
 sta flock_timer
 dec flock_left
 bne @emit
 lda #60
 sta flock_timer
@emit:
 lda #240
 sta sprite_x
 lda flock_left
 cmp #4
 lda #$18
 bcc :+
 lda #$88
:
 sta sprite_y
 lda #0
 sta sprite_pal
 lda #9
 jsr SpawnActor
 bcs @done
 inc flock_spawned
@done:rts

; Source p03:$A679-$A6BF: mixed band of eight, sharing p03:$A648
; four-unit group counters. First four type 5 enter from ship-opposite
; vertical side, last four type 6 alternate horizontal entry.
SpawnMixed:
 lda bottom_left
 bne @active
 lda #8
 sta bottom_left
 lda #1
 sta bottom_timer
 rts
@active:
 dec bottom_timer
 bne @done
 lda #80
 sta bottom_timer
 dec bottom_left
 lda bottom_left
 cmp #4
 bcc @type6
 lda #0
 sta sprite_x
 lda player_y
 cmp #$58
 lda #$90
 bcc :+
 lda #8
:
 sta sprite_y
 lda #5
 bne @spawn
@type6:
 lda bottom_left
 and #1
 beq @left
 lda #240
 bne @setx
@left:
 lda #0
@setx:
 sta sprite_x
 lda #$90
 sta sprite_y
 lda #6
@spawn:
 pha
 lda #0
 sta sprite_pal
 pla
 jsr SpawnActor
 bcs @done
 inc mixed_spawned
@done:rts

ActorsFrame:
 lda #0
 sta fire_used
 sta obj
@loop:
 lda obj
 jsr ObjectPointer
 ldy #O_TYPE
 lda (objptr),y
 jeq @next
 cmp #1
 beq @cannon
 cmp #2
 beq @two
 cmp #3
 beq @three
 cmp #4
 beq @four
 cmp #5
 beq @five
 cmp #6
 beq @six
 cmp #8
 beq @rock
 cmp #9
 beq @nine
 cmp #$0f
 beq @volcano
 cmp #$20
 beq @mid
 cmp #$12
 beq @capsule
 cmp #$13
 beq @capsule
 cmp #$15
 beq @explode
 jmp @next
@cannon:jsr Cannon
 jmp @collide
@two:jsr TypeTwo
 jmp @move
@three:jsr TypeThree
 jmp @move
@four:jsr TypeFour
 jmp @move
@five:jsr TypeFive
 jmp @move
@mid:jsr MidPiece
 jmp @collide
@volcano:jsr VolcanoParticle
 jmp @move
@six:jsr TypeSix
 jmp @move
@rock:jsr Stage2RockFrame
 jmp @collide
@nine:jsr TypeNine
 jmp @move
@capsule:jsr Capsule
 jmp @next
@explode:jsr Explosion
 jmp @next
@move:
 jsr MoveObject
@collide:
 jsr ShieldContact
 bcs @next
 ldy #O_TYPE
 lda (objptr),y
 beq @next
 ldy #O_Y
 lda player_y
 sec
 sbc (objptr),y
 clc
 adc #8
 cmp #16
 bcs @next
 ldy #O_X
 lda player_x
 sec
 sbc (objptr),y
 clc
 adc #10
 cmp #20
 bcs @next
 jsr PlayerHit
@next:
 inc obj
 lda obj
 cmp actor_limit
 jne @loop
 lda actor_limit
 cmp #17
 bne @done
 lda OBJECTS+12*32
 ora OBJECTS+13*32
 ora OBJECTS+14*32
 ora OBJECTS+15*32
 ora OBJECTS+16*32
 bne @done
 lda #12
 sta actor_limit
@done:
 rts

; Source p01:7420-745D checks the twelve ordinary enemy slots only.
; Y span is 33 and X span 21 at player X+12; no shield protection from terrain.
ShieldContact:
 lda power_shield
 beq @no
 lda obj
 cmp #12
 bcs @no
 ldy #O_FLAGS
 lda (objptr),y
 and #2
 beq @no
 ldy #O_Y
 lda player_y
 sec
 sbc (objptr),y
 clc
 adc #16
 cmp #33
 bcs @no
 ldy #O_X
 lda player_x
 clc
 adc #24
 sec
 sbc (objptr),y
 cmp #21
 bcs @no
 dec power_shield
 jsr ActorKilled
 sec
 rts
@no:clc
 rts

MoveObject:
 ldy #O_YF
 lda (objptr),y
 ldy #O_VYL
 clc
 adc (objptr),y
 ldy #O_YF
 sta (objptr),y
 iny
 lda (objptr),y
 ldy #O_VYH
 adc (objptr),y
 ldy #O_Y
 sta (objptr),y
 clc
 adc #8
 cmp #192
 bcs Despawn
 ldy #O_X
 lda (objptr),y
 sta s8
 dey
 lda (objptr),y
 ldy #O_VXL
 clc
 adc (objptr),y
 ldy #O_XF
 sta (objptr),y
 iny
 lda (objptr),y
 ldy #O_VXH
 adc (objptr),y
 ldy #O_X
 sta (objptr),y
 cmp #$f8
 bcc @done
 lda s8
 cmp #16
 bcc Despawn
@done:rts
Despawn:
 lda #0
 ldy #O_TYPE
 sta (objptr),y
 ldy #O_FLAGS
 sta (objptr),y
 rts

Cannon:
 lda phase
 cmp #2
 beq @aim
 cmp #4
 bcs @aim
 ldy #O_X
 lda (objptr),y
 sec
 sbc #1
 sta (objptr),y
 bcc Despawn
@aim:
 ldy #O_AYL
 lda (objptr),y
 clc
 adc #$20
 sta ptr2
 lda stagebase
 clc
 adc #$d
 sta ptr2+1
 ldy #0
 lda (ptr2),y
 ; Six original facing frames; horizontal/vertical bearing chooses the sector.
 clc
 adc #2
 ldy #O_FRAME
 sta (objptr),y
 jsr FireAtPlayer
 rts

TypeTwo:
 ldy #O_CLOCK
 lda (objptr),y
 clc
 adc #1
 sta (objptr),y
 lsr a
 lsr a
 and #3
 ldy #O_FRAME
 sta (objptr),y
 ldy #O_STATE
 lda (objptr),y
 beq @state0
 cmp #1
 beq @state1
 cmp #2
 beq @state2
 cmp #3
 beq @state3
 rts
@state0:
 lda #129
 sta s8
 lda #127
 sta s9
 jmp @threshold
@state2:
 lda #81
 sta s8
 lda #79
 sta s9
@threshold:
 ldy #O_Y
 lda (objptr),y
 cmp #80
 bcc :+
 lda s9
 sta s8
:
 ldy #O_X
 lda (objptr),y
 cmp s8
 bcs @done
 ldy #O_STATE
 lda (objptr),y
 clc
 adc #1
 sta (objptr),y
 lda #4
 ldy #O_VXH
 sta (objptr),y
 ldy #O_Y
 lda (objptr),y
 cmp #80
 lda #4
 bcc :+
 lda #$fc
:
 ldy #O_VYH
 sta (objptr),y
 rts
@state1:
 ldy #O_X
 lda (objptr),y
 cmp #159
 bcc @done
 ldy #O_Y
 lda (objptr),y
 and #$f8
 sta (objptr),y
 lda #2
 ldy #O_STATE
 sta (objptr),y
 lda #0
 ldy #O_VYH
 sta (objptr),y
 lda #$fc
 ldy #O_VXH
 sta (objptr),y
 rts
@state3:
 ldy #O_Y
 lda player_y
 sec
 sbc (objptr),y
 clc
 adc #4
 cmp #9
 bcs @done
 lda (objptr),y
 and #$f8
 sta (objptr),y
 lda #4
 ldy #O_STATE
 sta (objptr),y
 lda #0
 ldy #O_VYH
 sta (objptr),y
@done:rts

TypeThree:
 jsr FireAtPlayer
 ldy #O_CLOCK
 lda (objptr),y
 clc
 adc #1
 sta (objptr),y
 lsr a
 lsr a
 lsr a
 and #7
 tax
 lda CurveFrames,x
 ldy #O_FRAME
 sta (objptr),y
 jsr AddAY
 ldy #O_VYL
 lda (objptr),y
 bne @done
 iny
 lda (objptr),y
 cmp #4
 beq @negative
 cmp #$fc
 bne @done
 lda #$80
 ldy #O_AYL
 sta (objptr),y
 iny
 lda #0
 sta (objptr),y
 rts
@negative:
 lda #$80
 ldy #O_AYL
 sta (objptr),y
 iny
 lda #$ff
 sta (objptr),y
@done:rts
AddAY:
 ldy #O_VYL
 lda (objptr),y
 ldy #O_AYL
 clc
 adc (objptr),y
 ldy #O_VYL
 sta (objptr),y
 iny
 lda (objptr),y
 ldy #O_AYH
 adc (objptr),y
 ldy #O_VYH
 sta (objptr),y
 rts

TypeFour:
 jsr FireAtPlayer
 ldy #O_Y
 lda player_y
 sec
 sbc (objptr),y
 sta s8
 clc
 adc #3
 cmp #7
 bcc @level
 lda #$80
 ldy #O_VXL
 sta (objptr),y
 iny
 lda #$fe
 sta (objptr),y
 ldy #O_VYL
 lda #$80
 sta (objptr),y
 lda s8
 bmi @up
 lda #1
 iny
 sta (objptr),y
 lda #$b8
 bne @frame
@up:
 lda #$fe
 iny
 sta (objptr),y
 lda #$b4
 bne @frame
@level:
 lda #0
 ldy #O_VYL
 sta (objptr),y
 iny
 sta (objptr),y
 ldy #O_X
 lda player_x
 cmp (objptr),y
 bcs @slow
 lda #0
 ldy #O_VXL
 sta (objptr),y
 iny
 lda #$fd
 sta (objptr),y
 jmp @straight
@slow:
 lda #$80
 ldy #O_VXL
 sta (objptr),y
 iny
 lda #$fe
 sta (objptr),y
@straight:lda #$b0
@frame:
 ldy #O_FRAME
 sta (objptr),y
 rts

TypeFive:
 ; Source walking/standing/exiting state machine, with native tile collision.
 lda logic
 and #31
 bne @state
 ldy #O_LIFE
 lda (objptr),y
 beq @exit
 sec
 sbc #1
 sta (objptr),y
 bne @state
@exit:
 lda #2
 ldy #O_STATE
 sta (objptr),y
 lda #$fe
 ldy #O_VXH
 sta (objptr),y
@state:
 ldy #O_STATE
 lda (objptr),y
 cmp #2
 beq @walk
 cmp #1
 beq @standing
 ldy #O_CLOCK
 lda (objptr),y
 sec
 sbc #1
 sta (objptr),y
 bne @walk
 lda #1
 ldy #O_STATE
 sta (objptr),y
 lda #90
 ldy #O_CLOCK
 sta (objptr),y
 lda #0
 ldy #O_VXH
 sta (objptr),y
 jmp @standing
@standing:
 jsr FireAtPlayer
 ldy #O_CLOCK
 lda (objptr),y
 sec
 sbc #1
 sta (objptr),y
 bne @face
 jsr RNG
 and #31
 clc
 adc #45
 ldy #O_CLOCK
 sta (objptr),y
 lda #0
 ldy #O_STATE
 sta (objptr),y
 ldy #O_X
 lda player_x
 cmp (objptr),y
 lda #2
 bcs :+
 lda #$fe
:
 ldy #O_VXH
 sta (objptr),y
@face:
 lda #$d8
 ldy #O_SIDE
 ldx #0
 cmp #0
 lda (objptr),y
 beq :+
 ldx #1
:
 ldy #O_X
 lda player_x
 cmp (objptr),y
 lda #$d8
 bcc :+
 lda #$fc
:
 cpx #0
 beq @setframe
 sec
 sbc #$18
 jmp @setframe
@walk:
 ldx #0
 ldy #O_VXH
 lda (objptr),y
 bmi :+
 ldx #2
:
 ldy #O_SIDE
 lda (objptr),y
 beq :+
 inx
 inx
 inx
 inx
:
 lda logic
 and #4
 beq :+
 inx
:
 lda WalkerFrames,x
@setframe:
 ldy #O_FRAME
 sta (objptr),y
 ; Fit the feet/ceiling to the original source-tile collision surface.
 ldy #O_X
 lda (objptr),y
 sta sprite_x
 ldy #O_Y
 lda (objptr),y
 sta sprite_y
 ldy #O_SIDE
 lda (objptr),y
 beq @ceiling
 lda sprite_y
 clc
 adc #16
 sta sprite_y
 jsr TerrainSolid
 bcs @floorup
 ldy #O_Y
 lda (objptr),y
 cmp #144
 bcs @done
 clc
 adc #8
 sta (objptr),y
 rts
@floorup:
 lda sprite_y
 sec
 sbc #8
 sta sprite_y
 jsr TerrainSolid
 bcc @done
 ldy #O_Y
 lda (objptr),y
 sec
 sbc #8
 sta (objptr),y
 rts
@ceiling:
 jsr TerrainSolid
 bcc @ceilingup
 ldy #O_Y
 lda (objptr),y
 clc
 adc #8
 sta (objptr),y
 rts
@ceilingup:
 lda sprite_y
 sec
 sbc #8
 sta sprite_y
 jsr TerrainSolid
 bcs @done
 ldy #O_Y
 lda (objptr),y
 cmp #9
 bcc @done
 sec
 sbc #8
 sta (objptr),y
@done:rts

TypeSix:
 jsr FireAtPlayer
 lda logic
 lsr a
 lsr a
 and #3
 asl a
 asl a
 clc
 adc #$a0
 ldy #O_FRAME
 sta (objptr),y
 ldy #O_VYH
 lda (objptr),y
 bmi @gravity
 ldy #O_Y
 lda (objptr),y
 cmp #159
 bcs @bounce
 clc
 adc #16
 sta sprite_y
 ldy #O_X
 lda (objptr),y
 sta sprite_x
 jsr TerrainSolid
 bcc @gravity
@bounce:
 lda #0
 ldy #O_VYL
 sta (objptr),y
 iny
 lda #$fa
 sta (objptr),y
 rts
@gravity:jmp AddAY

TypeNine:
 jsr FireAtPlayer
 ldy #O_CLOCK
 lda (objptr),y
 clc
 adc #1
 cmp #24
 bcc :+
 lda #0
:
 sta (objptr),y
 lsr a
 lsr a
 tax
 lda NineFrames,x
 ldy #O_FRAME
 sta (objptr),y
 ldy #O_X
 lda (objptr),y
 cmp #$80
 bcs @done
 ldy #O_Y
 lda player_y
 sec
 sbc (objptr),y
 clc
 adc #3
 cmp #7
 bcc @neutral
 lda player_y
 cmp (objptr),y
 lda #$ff
 bcc @setvy
 lda #1
 bne @setvy
@neutral:
 lda #0
@setvy:
 ldy #O_VYH
 sta (objptr),y
@done:rts

FireAtPlayer:
 ldy #O_FIRE
 lda (objptr),y
 sec
 sbc #1
 sta (objptr),y
 bne @done
 lda #128
 sta (objptr),y
 lda fire_used
 bne @done
 inc fire_used
 jmp AimBullet
@done:rts

ActorKilled:
 ; Preserve group and marked-enemy capsule semantics; explosion lasts 16 frames.
 inc kills_low
 bne :+
 inc kills_high
:
 inc score_lo
 bne :+
 inc score_hi
:
 lda #$aa
 sta audio_cmd
 ldy #O_TYPE
 lda #$15
 sta (objptr),y
 lda #0
 ldy #O_CLOCK
 sta (objptr),y
 ldy #O_FLAGS
 sta (objptr),y
 ldy #O_DRAW
 sta (objptr),y
 lda #$78
 ldy #O_FRAME
 sta (objptr),y
 rts
Explosion:
 ldy #O_CLOCK
 lda (objptr),y
 clc
 adc #1
 sta (objptr),y
 cmp #16
 bcs @finish
 lsr a
 and #6
 asl a
 clc
 adc #$78
 ldy #O_FRAME
 sta (objptr),y
 rts
@finish:
 ldy #O_GROUP
 lda (objptr),y
 beq @marked
 iny
 lda (objptr),y
 tax
 dec GROUPS+2,x
 bne @remove
 lda #1
 bne @capsule
@marked:
 ldy #O_MARK
 lda (objptr),y
 beq @remove
@capsule:
 clc
 adc #$11
 ldy #O_TYPE
 sta (objptr),y
 cmp #$12
 beq :+
 lda #$22
 jmp :++
:
 lda #$21
:
 ldy #O_FRAME
 sta (objptr),y
 lda #1
 ldy #O_DRAW
 sta (objptr),y
 lda #0
 ldy #O_CLOCK
 sta (objptr),y
 rts
@remove:jmp Despawn
Capsule:
 ldy #O_X
 lda (objptr),y
 sec
 sbc #1
 sta (objptr),y
 jcc Despawn
 sec
 sbc player_x
 clc
 adc #12
 cmp #24
 bcs @done
 ldy #O_Y
 lda (objptr),y
 sec
 sbc player_y
 clc
 adc #12
 cmp #24
 bcs @done
 ldy #O_TYPE
 lda (objptr),y
 cmp #$13
 beq CollectBomb
 jsr CollectCapsule
 jmp Despawn
@done:rts
; Source p01:758E-75B7: collect blue bomb without advancing the bar.
; Kill the twelve regular and five separate encounter records of types 1..15.
; Do not erase enemy bullets, ordinary capsules, or the separate Big Core.
CollectBomb:
 inc capsules_taken
 inc bombs_taken
 jsr Despawn
 lda obj
 pha
 lda #0
 sta obj
@clear:
 lda obj
 jsr ObjectPointer
 ldy #O_TYPE
 lda (objptr),y
 cmp #$20                ; native alias of a source five-part record in state 1
 beq @kill
 cmp #1
 bcc @next
 cmp #$10
 bcs @next
@kill:
 jsr ActorKilled
@next:
 inc obj
 lda obj
 cmp actor_limit
 bcc @clear
 pla
 sta obj
 jsr ObjectPointer
 lda #$aa
 sta audio_cmd
 rts
CollectCapsule:
 lda score_lo
 clc
 adc #5
 sta score_lo
 bcc :+
 inc score_hi
:
 inc capsules_taken
 inc power_slot
 lda power_slot
 cmp #7
 bcc :+
 lda #1
 sta power_slot
:
 lda #$a9
 sta audio_cmd
 rts

ActorsDraw:
 ; Rotate only presentation order: simulation and source collision order stay fixed.
 ; Alternate projectile priority so a long laser cannot starve all enemy sprites.
 lda logic
 and #1
 beq :+
 jsr ProjectileDraw
:
 inc draw_cursor
 lda draw_cursor
 cmp actor_limit
 bcc :+
 lda #0
 sta draw_cursor
:
 sta obj
 lda actor_limit
 sta draw_left
@loop:
 lda obj
 jsr ObjectPointer
 ldy #O_TYPE
 lda (objptr),y
 beq @next
 ldy #O_X
 lda (objptr),y
 sta sprite_x
 ldy #O_Y
 lda (objptr),y
 clc
 adc #15
 sta sprite_y
 ldy #O_DRAW
 lda (objptr),y
 beq @hardware
 cmp #1
 bne @next
 ldy #O_FRAME
 lda (objptr),y
 cmp #56
 bcs @next
 clc
 adc #64
 bne @frame
@hardware:
 ldy #O_FRAME
 lda (objptr),y
 lsr a
 lsr a
@frame:
 sta sprite_frame
 ldy #O_COLOR
 lda (objptr),y
 cmp #8
 beq :+
 lda #0
 jmp @pal
:
 lda #1
@pal:
 sta sprite_pal
 lda #0
 sta sprite_flags
 jsr DrawSprite
@next:
 inc obj
 lda obj
 cmp actor_limit
 bcc :+
 lda #0
 sta obj
:
 dec draw_left
 bne @loop
 lda logic
 and #1
 bne :+
 jmp ProjectileDraw
:
 rts
ShotsFrame:jmp ProjectileFrame
Marks:.byte 0,0,0,1,0,0,0,1,0,0,0,2,0,0,0,1
StreamY:.byte 32,128,64,112
LeftY:.byte 8,144,8,8,144,8,144,144
NineFrames:.byte $ec,$f0,$f4,$f8,$f4,$f0
CurveFrames:.byte $8c,$90,$94,$98,$9c,$98,$94,$90
WalkerFrames:.byte $d0,$d4,$f4,$f8,$dc,$e0,$e8,$ec
