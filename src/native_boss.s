.setcpu "6502"
.include "longbranch.inc"
.include "native.inc"
.include "actors.inc"
.include "boss.inc"
.import Stage3MidbossCleared,S3_State
.import SpawnMidActor
.import SpawnActor,RNG,ObjectPointer,DrawSprite,AdvanceStage,UpdateHUD,StarRows,PlayerHit
.export StageEvents,EnterBigCore,BuildBossQueue,UploadBossQueue,BossShotHit
.export MidPiece,VolcanoParticle,EmitLinearBullet

.segment "CODE"
; Called once per logical frame. Phase values are runtime states, not invented
; source levels. N1 stage 1 event positions/counts are source p01:6CCE-6D64.
StageEvents:
 lda stage_id
 cmp #1
 beq @source_one
 cmp #2
 beq @stage3_shared
 cmp #3
 bne @notyet
@stage3_shared:
 ; Stage 2 shares the source type-1 Big Core once its rock-rain phase ends.
 ; Do not run stage-1 midpiece/volcano/scroll setup for stage 2.
 lda phase
 cmp #5
 jeq @enter
 cmp #6
 jeq @fight
 cmp #7
 jeq @destroy
 cmp #8
 jeq @after
 rts
@source_one:
 lda phase
 beq @travel
 cmp #2
 jeq @volcano
 cmp #3
 jeq @tail
 cmp #4
 jeq @waitclear
 cmp #5
 jeq @enter
 cmp #6
 jeq @fight
 cmp #7
 jeq @destroy
 cmp #8
 jeq @after
@notyet:rts
@travel:
 lda worldhi
 cmp #1
 bne @notyet
 lda worldlo
 cmp #$65
 bcc @notyet
 lda mid_seen
 bne @endcheck
 inc mid_seen
 lda #5
 sta mid_parts
@mid:
 ldx mid_parts
 dex
 lda MidX,x
 sta sprite_x
 lda MidY,x
 sta sprite_y
 lda #0
 sta sprite_pal
 lda #$20
 jsr SpawnMidActor
 bcs @endcheck
 ldy #O_TYPE
 lda #$20
 sta (objptr),y
 ldy #O_DRAW
 lda #1
 sta (objptr),y
 ldx mid_parts
 dex
 txa
 clc
 adc #35
 ldy #O_FRAME
 sta (objptr),y
 ldy #O_HP
 lda #10
 sta (objptr),y
 ldy #O_FLAGS
 lda #3
 sta (objptr),y
 ldy #O_FIRE
 lda #92
 sta (objptr),y
 dec mid_parts
 bne @mid
@endcheck:
 lda worldlo
 cmp #$9f
 bcc @notyet
 lda #2
 sta phase
 lda #$c2
 sta phase_timer
 lda #1
 sta phase_hi
 lda #$9b
 sta audio_cmd
 rts
@volcano:
 lda logic
 and #1
 jne @vreturn
 lda phase_timer
 bne :+
 dec phase_hi
:
 dec phase_timer
 lda phase_timer
 ora phase_hi
 bne @emit
 lda #3
 sta phase
 rts
@emit:
 lda phase_timer
 and #1
 tax
 lda VentX,x
 sta sprite_x
 lda #127
 sta sprite_y
 lda #0
 sta sprite_pal
 lda #$0f
 jsr SpawnActor
 jcs @vreturn
 ; Defaults p01:6BA3, type $0F. Gravity p01:6C8E is $0088.
 ldy #O_TYPE
 lda #$0f
 sta (objptr),y
 ldy #O_COLOR
 lda #8
 sta (objptr),y
 ldy #O_AYL
 lda #$88
 sta (objptr),y
 iny
 lda #0
 sta (objptr),y
 jsr RNG
 and #7
 asl a
 asl a
 tax
 ; Source velocity p01:718D. Stage 1 negates vertical velocity.
 lda VolcanoSpeeds,x
 eor #$ff
 clc
 adc #1
 ldy #O_VYL
 sta (objptr),y
 lda VolcanoSpeeds+1,x
 eor #$ff
 adc #0
 iny
 sta (objptr),y
 lda VolcanoSpeeds+2,x
 sta s0
 lda VolcanoSpeeds+3,x
 sta s1
 lda phase_timer
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
 ldy #O_VXL
 lda s0
 sta (objptr),y
 iny
 lda s1
 sta (objptr),y
 ; First thirty particles use half velocity: source remaining >= $01A4.
 lda phase_hi
 beq @vcount
 lda phase_timer
 cmp #$a4
 bcc @vcount
 ldy #O_VYH
 lda (objptr),y
 cmp #$80
 ror a
 sta (objptr),y
 dey
 lda (objptr),y
 ror a
 sta (objptr),y
 ldy #O_VXH
 lda (objptr),y
 cmp #$80
 ror a
 sta (objptr),y
 dey
 lda (objptr),y
 ror a
 sta (objptr),y
@vcount:
 inc volcano_emitted
 bne @vreturn
 inc volcano_emitted_hi
@vreturn:rts
@tail:
 lda worldhi
 cmp #1
 bne @vreturn
 lda worldlo
 cmp #$c0
 bcc @vreturn
 lda #4
 sta phase
 lda #30
 sta phase_timer
 rts
@waitclear:
 dec phase_timer
 bne @vreturn
 lda #1
 sta phase_timer
 ldx #0
@actors:
 txa
 pha
 jsr ObjectPointer
 ldy #O_TYPE
 lda (objptr),y
 sta s0
 pla
 tax
 lda s0
 bne @vreturn
 inx
 cpx #12
 bne @actors
 ldx #0
@bullets:
 lda ENEMY_SHOTS,x
 bne @vreturn
 txa
 clc
 adc #16
 tax
 cpx #160
 bne @bullets
 jmp EnterBigCore
@enter:
 lda logic
 and #7
 bne @breturn
 lda boss_x
 sec
 sbc #8
 sta boss_x
 cmp #152
 bne @redraw
 lda #6
 sta phase
 lda #$d0
 sta phase_timer
 lda #2
 sta phase_hi
 lda #1
 sta boss_open
@redraw:
 jsr BuildBossQueue
@breturn:rts
@fight:
 lda boss_hp
 jeq @leave
 lda bs_move
 bne @moving
 inc bs_move
 jsr RNG
 and #3
 sta bs_steps
 lda #0
 sta boss_dir
 lda boss_y
 clc
 adc #24
 cmp player_y
 bcc :+
 inc boss_dir
:
 lda #1
 sta bs_wait
 jsr CoreFourShots
 jmp @life
@moving:
 dec bs_wait
 bne @life
 lda #5
 sta bs_wait
 inc bs_steps
 lda bs_steps
 cmp #11
 bcc @step
 lda #0
 sta bs_move
 jmp @life
@step:
 lda boss_dir
 beq @down
 lda boss_y
 sec
 sbc #8
 cmp #16
 bcs @sety
 lda #0
 sta boss_dir
 lda #16
 bne @sety
@down:
 lda boss_y
 clc
 adc #8
 cmp #120
 bcc @sety
 lda #1
 sta boss_dir
 lda #112
@sety:
 sta boss_y
 lda #1
 sta bs_needs
@life:
 lda phase_timer
 bne :+
 dec phase_hi
:
 dec phase_timer
 lda phase_hi
 cmp #2
 bne @nearend
 lda phase_timer
 cmp #$58
 bne @collision
 lda #0
 sta boss_open
 inc bs_needs
 jmp @collision
@nearend:
 lda phase_hi
 bne @collision
 lda phase_timer
 cmp #120
 bne @exhausted
 lda #1
 sta boss_open
 inc bs_needs
 inc boss_closures
@exhausted:
 lda phase_timer
 bne @collision
 ; The original retreats/explodes after its 720-frame window even if not killed.
 jmp @leave
@collision:
 jsr BossPlayerCollision
 lda bs_needs
 jeq @breturn
 jmp BuildBossQueue
@leave:
 lda #7
 sta phase
 lda #40
 sta phase_timer
 lda #2
 sta boss_open
 jmp BuildBossQueue
@destroy:
 dec phase_timer
 jne @breturn
 lda #0
 sta bs_visible
 jsr BuildBossQueue
 lda #8
 sta phase
 lda #120
 sta phase_timer
 lda #$ab
 sta audio_cmd
 lda boss_hp
 bne :+
 inc score_hi
 inc bs_killed
:
 rts
@after:
 dec phase_timer
 jne @breturn
 inc core_cleared
 lda stage_id
 cmp #3
 bne @ordinary_clear
 ; S3_State + 6 = final source type-1 boss has already been entered.
 lda S3_State+6
 bne @ordinary_clear
 jmp Stage3MidbossCleared
@ordinary_clear:
 jmp AdvanceStage

; Force blank only at the source's one-off boss graphics load, never per frame.
EnterBigCore:
 sei
 lda #0
 sta screenon
 sta $2000
 sta $2001
 sta $5204
 sta column_pending
 sta camera
 lda #$88
 sta $5114
 bit $2002
 lda #$20
 sta $2006
 lda #0
 sta $2006
 ldx #3
 ldy #0
@clear:
 sta $2007
 sta $6000,y
 sta $6100,y
 sta $6200,y
 sta $6300,y
 iny
 bne @clear
 dex
 bne @clear
 ; Static stars in the boss's dedicated 4 KiB pattern bank.
 ldx #0
@star:
 lda StarRows,x
 clc
 adc #1
 sta s0
 lsr a
 lsr a
 lsr a
 clc
 adc #$20
 sta $2006
 lda s0
 asl a
 asl a
 asl a
 asl a
 asl a
 sta s1
 txa
 ora s1
 sta $2006
 lda #$f6
 sta $2007
 inx
 cpx #32
 bne @star
 lda #2
 sta $5104
 lda $8000
 ldx #0
@attributes:
 sta $5c00,x
 sta $5d00,x
 sta $5e00,x
 inx
 bne @attributes
 lda #1
 ldx #0
@font:
 sta $5f20,x
 inx
 cpx #32
 bne @font
 lda #1
 sta $5104
 bit $2002
 lda #$3f
 sta $2006
 lda #0
 sta $2006
 ldx #0
@pal:
 lda $8004,x
 sta $2007
 inx
 cpx #4
 bne @pal
 lda #248
 sta boss_x
 sta bs_oldx
 lda #64
 sta boss_y
 sta bs_oldy
 lda #22
 sta boss_hp
 lda #1
 sta boss_open
 sta bs_visible
 sta core_seen
 lda #0
 sta bs_move
 sta bs_killed
 sta bs_needs
 lda #5
 sta phase
 jsr UpdateHUD
 jsr BuildBossQueue
 lda #0
 sta $2005
 sta $2005
 lda #$a0
 sta $2000
 lda #$1c
 sta $2001
 lda #1
 sta screenon
 cli
 rts

; Union of old and new 11x8 tile rectangles. Source moves one tile per step,
; therefore maximum transfer is 11x9 or 12x8, not an expanded full-frame stream.
BuildBossQueue:
 lda #0
 sta bs_needs
 lda boss_x
 cmp bs_oldx
 bcc :+
 lda bs_oldx
:
 lsr a
 lsr a
 lsr a
 sta s0                  ; left column
 lda boss_x
 cmp bs_oldx
 bcs :+
 lda bs_oldx
:
 lsr a
 lsr a
 lsr a
 clc
 adc #11
 cmp #32
 bcc :+
 lda #32
:
 sec
 sbc s0
 sta s2
 sta BQWIDTH
 lda boss_y
 cmp bs_oldy
 bcc :+
 lda bs_oldy
:
 lsr a
 lsr a
 lsr a
 clc
 adc #2
 sta s1                  ; upper row includes 16-pixel playfield inset
 lda boss_y
 cmp bs_oldy
 bcs :+
 lda bs_oldy
:
 lsr a
 lsr a
 lsr a
 clc
 adc #10
 sec
 sbc s1
 sta s3
 sta BQHEIGHT
 lda #0
 sta sc                  ; row index
 sta sd                  ; buffer row offset
@row:
 lda s1
 clc
 adc sc
 sta s8                  ; absolute tile row
 lsr a
 lsr a
 lsr a
 clc
 adc #$20
 ldx sc
 sta BQHI,x
 lda s8
 asl a
 asl a
 asl a
 asl a
 asl a
 ora s0
 sta BQLO,x
 lda #12
 sec
 sbc s2
 clc
 adc sd
 sta se                  ; right-aligned output
 lda #0
 sta sb                  ; column index
@column:
 lda s0
 clc
 adc sb
 sta s9                  ; absolute tile column
 jsr BossTileAt
 ldx se
 sta BOSSQ,x
 inc se
 inc sb
 lda sb
 cmp s2
 bne @column
 lda sd
 clc
 adc #12
 sta sd
 inc sc
 lda sc
 cmp s3
 bne @row
 lda boss_x
 sta bs_oldx
 lda boss_y
 sta bs_oldy
 lda #1
 sta boss_dirty
 inc boss_blits
 rts

; Input s8=row and s9=column. Return source character in A.
BossTileAt:
 lda bs_visible
 beq @star
 lda boss_y
 lsr a
 lsr a
 lsr a
 clc
 adc #2
 sta s4
 lda s8
 sec
 sbc s4
 cmp #8
 bcs @star
 sta s4                  ; local row
 lda boss_x
 lsr a
 lsr a
 lsr a
 sta s5
 lda s9
 sec
 sbc s5
 cmp #11
 bcs @star
 sta s5                  ; local column
 lda s4
 cmp #3
 beq @facecheck
 cmp #4
 bne @body
@facecheck:
 lda s5
 sec
 sbc #1
 cmp #3
 bcc @eye
 lda s5
 sec
 sbc #4
 cmp #3
 bcc @face
@body:
 lda s4
 asl a
 sta s6
 asl a
 asl a
 clc
 adc s6
 adc s4
 adc s5
 tax
 lda $8100,x
 bne @done
@star:
 ldx s9
 lda StarRows,x
 clc
 adc #1
 cmp s8
 bne @blank
 lda #$f6
 bne @done
@blank:lda #0
@done:rts
@eye:
 sta s6
 lda boss_hp
 lsr a
 lsr a
 tax
 lda SixTimes,x
 sta s7
 lda s4
 cmp #3
 beq :+
 lda s6
 clc
 adc #3
 sta s6
:
 lda s6
 clc
 adc s7
 tax
 lda $8160,x
 rts
@face:
 sta s6
 ldx boss_open
 lda SixTimes,x
 sta s7
 lda s4
 cmp #3
 beq :+
 lda s6
 clc
 adc #3
 sta s6
:
 lda s6
 clc
 adc s7
 tax
 lda $8190,x
 rts

; NMI-only. Writes at most 99 data bytes; fixed unrolled row tail avoids a
; 15-cycle/byte indirect loop. ExRAM is unchanged during body motion.
UploadBossQueue:
 lda #0
 sta nreg
 ldy #0
BossUploadRow:
 ldx nreg
 bit $2002
 lda BQHI,x
 sta $2006
 lda BQLO,x
 sta $2006
 ldx BQWIDTH
 lda RowJumpLo,x
 sta nptr
 lda RowJumpHi,x
 sta nptr+1
 jmp (nptr)
R12:lda BOSSQ+0,y
 sta $2007
R11:lda BOSSQ+1,y
 sta $2007
R10:lda BOSSQ+2,y
 sta $2007
R9:lda BOSSQ+3,y
 sta $2007
R8:lda BOSSQ+4,y
 sta $2007
R7:lda BOSSQ+5,y
 sta $2007
R6:lda BOSSQ+6,y
 sta $2007
R5:lda BOSSQ+7,y
 sta $2007
R4:lda BOSSQ+8,y
 sta $2007
R3:lda BOSSQ+9,y
 sta $2007
R2:lda BOSSQ+10,y
 sta $2007
R1:lda BOSSQ+11,y
 sta $2007
R0:
 tya
 clc
 adc #12
 tay
 inc nreg
 lda nreg
 cmp BQHEIGHT
 bcc BossUploadRow
 lda #0
 sta boss_dirty
 rts
RowJumpLo:.lobytes R0,R1,R2,R3,R4,R5,R6,R7,R8,R9,R10,R11,R12
RowJumpHi:.hibytes R0,R1,R2,R3,R4,R5,R6,R7,R8,R9,R10,R11,R12
SixTimes:.byte 0,6,12,18,24,30

BossPlayerCollision:
 lda player_x
 clc
 adc #8
 lsr a
 lsr a
 lsr a
 sta s9
 lda player_y
 clc
 adc #24
 lsr a
 lsr a
 lsr a
 sta s8
 jsr BossTileAt
 beq @done
 cmp #$f6
 beq @done
 jmp PlayerHit
@done:rts

; C=consume player shot. Hit gates match p01:7827: only odd shot types,
; open face, living core, the original eight-pixel front channel.
BossShotHit:
 lda phase
 cmp #5
 bcc @no
 cmp #8
 bcs @no
 ldy #1
 lda (shot_ptr),y
 sec
 sbc boss_x
 clc
 adc #8
 cmp #96
 bcs @no
 ldy #2
 lda (shot_ptr),y
 sec
 sbc boss_y
 cmp #64
 bcs @no
 lda boss_open
 bne @consume
 lda boss_hp
 beq @consume
 ldy #0
 lda (shot_ptr),y
 and #1
 beq @consume
 ldy #2
 lda (shot_ptr),y
 sec
 sbc boss_y
 sec
 sbc #29
 cmp #8
 bcs @consume
 dec boss_hp
 inc bs_hit
 inc bs_needs
 lda #$aa
 sta audio_cmd
@consume:
 sec
 rts
@no:clc
 rts

CoreFourShots:
 lda #0
 sta sa
@loop:
 ldx sa
 lda $81d0,x
 clc
 adc boss_y
 sta sprite_y
 lda $81d1,x
 clc
 adc boss_x
 sta sprite_x
 lda #$e0              ; source velocity -6.125, initial difficulty zero
 sta s4
 lda #$f9
 sta s5
 lda #0
 sta s6
 sta s7
 jsr EmitLinearBullet
 inc sa
 inc sa
 lda sa
 cmp #8
 bne @loop
 rts

; sprite_x/y position, s4/s5 VX, s6/s7 VY fixed point. Does not touch sa.
EmitLinearBullet:
 ldx #0
@free:
 lda ENEMY_SHOTS,x
 beq @found
 txa
 clc
 adc #16
 tax
 cpx #160
 bne @free
 rts
@found:
 lda #1
 sta ENEMY_SHOTS,x
 lda sprite_x
 sta ENEMY_SHOTS+1,x
 lda sprite_y
 sta ENEMY_SHOTS+2,x
 lda #0
 sta ENEMY_SHOTS+3,x
 sta ENEMY_SHOTS+4,x
 lda s4
 sta ENEMY_SHOTS+5,x
 lda s5
 sta ENEMY_SHOTS+6,x
 lda s6
 sta ENEMY_SHOTS+7,x
 lda s7
 sta ENEMY_SHOTS+8,x
 rts

.segment "ACTORS"
; Original five-piece group has independent 10-HP pieces and 92-frame shots.
MidPiece:
 ldy #O_X
 lda (objptr),y
 sec
 sbc #1
 sta (objptr),y
 bcs @fire
 ldy #O_TYPE
 lda #0
 sta (objptr),y
 rts
@fire:
 ldy #O_FIRE
 lda (objptr),y
 sec
 sbc #1
 sta (objptr),y
 bne @done
 lda #92
 sta (objptr),y
 ldy #O_X
 lda (objptr),y
 cmp #48
 bcc @done
 sec
 sbc #24
 sta sprite_x
 ldy #O_Y
 lda (objptr),y
 sta sprite_y
 lda #0
 sta s4
 sta s6
 sta s7
 lda #$fc
 sta s5
 jsr EmitLinearBullet
@done:rts

VolcanoParticle:
 ldy #O_VYL
 lda (objptr),y
 clc
 adc #$88
 sta (objptr),y
 iny
 lda (objptr),y
 adc #0
 sta (objptr),y
 rts

.segment "CODE"
MidX:.byte 240,240,232,240,240
MidY:.byte 76,84,94,104,112
VentX:.byte 188,60
VolcanoSpeeds:.incbin "build/native/boss.bin",$1b0,32
