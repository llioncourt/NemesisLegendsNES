.setcpu "6502"
.include "longbranch.inc"
.include "native.inc"
.include "actors.inc"
.import TerrainSolid,ActorKilled,ObjectPointer,BossShotHit,DrawSprite8
.export LaserStep,LaserDraw
.segment "CODE"
; Native laser record: [3,X,Y,state,owner,length,remaining,...].
; Source p02:9D8F,9E66-9EDF: grow four characters/frame, detach at 8/15,
; move 32px/frame, shrink by four characters after terrain contact.
LaserStep:
 ldy #3
 lda (shot_ptr),y
 beq @grow
 ldy #1
 lda (shot_ptr),y
 clc
 adc #32
 jcs @erase
 sta (shot_ptr),y
 ldy #3
 lda (shot_ptr),y
 cmp #2
 bcc @clip
 ldy #5
 lda (shot_ptr),y
 cmp #5
 jcc @erase
 sec
 sbc #4
 sta (shot_ptr),y
 jmp @clip
@grow:
 ldy #4
 lda (shot_ptr),y
 beq @ship
 sec
 sbc #1
 asl a
 tax
 lda OPTIONS,x
 clc
 adc #16
 sta s0
 lda OPTIONS+1,x
 clc
 adc #8
 and #$f8
 sta s1
 jmp @xy
@ship:
 lda player_x
 clc
 adc #16
 sta s0
 lda player_y
 clc
 adc #8
 and #$f8
 sta s1
@xy:
 lda s0
 and #$f8
 ldy #1
 sta (shot_ptr),y
 iny
 lda s1
 sta (shot_ptr),y
 ldx #4
@growth:
 ldy #5
 lda (shot_ptr),y
 clc
 adc #1
 sta (shot_ptr),y
 iny
 lda (shot_ptr),y
 sec
 sbc #1
 sta (shot_ptr),y
 beq @long
 dex
 bne @growth
 jmp @clip
@long:
 ldy #3
 lda #1
 sta (shot_ptr),y
@clip:
 ldy #1
 lda (shot_ptr),y
 sta s9                  ; beginning X
 eor #$ff
 clc
 adc #1
 lsr a
 lsr a
 lsr a
 sta s8                  ; last complete on-screen character
 ldy #5
 lda (shot_ptr),y
 cmp s8
 bcc :+
 lda s8
 sta (shot_ptr),y
:
 jeq @erase
 sta sa                  ; current length
 ldy #2
 lda (shot_ptr),y
 sta sprite_y
 lda #0
 sta sb
@terrain:
 lda sb
 asl a
 asl a
 asl a
 clc
 adc s9
 sta sprite_x
 jsr TerrainSolid
 bcs @blocked
 inc sb
 lda sb
 cmp sa
 bcc @terrain
 jmp @boss
@blocked:
 lda sb
 ldy #5
 sta (shot_ptr),y
 jeq @erase
 sta sa
 lda #2
 ldy #3
 sta (shot_ptr),y
@boss:
 lda phase
 cmp #5
 bcc @actors
 cmp #8
 bcs @actors
 lda boss_x
 clc
 adc #8
 sec
 sbc s9
 bcc @actors
 sta sb
 lda sa
 asl a
 asl a
 asl a
 cmp sb
 bcc @actors
 ; Present the front intersection to the common core gate, then restore X.
 lda boss_x
 ldy #1
 sta (shot_ptr),y
 jsr BossShotHit
 lda s9
 ldy #1
 sta (shot_ptr),y
 bcc @actors
 lda boss_x
 sec
 sbc s9
 lsr a
 lsr a
 lsr a
 clc
 adc #1
 ldy #5
 sta (shot_ptr),y
 lda #2
 ldy #3
 sta (shot_ptr),y
@actors:
 ldy #2
 lda (shot_ptr),y
 sta sc
 lda #0
 sta obj
 sta objptr
 lda #>OBJECTS
 sta objptr+1
@enemy:
 ldy #O_FLAGS
 lda (objptr),y
 and #2
 beq @next
 ldy #O_Y
 lda sc
 sec
 sbc (objptr),y
 clc
 adc #2
 cmp #18
 bcs @next
 ldy #O_X
 lda (objptr),y
 clc
 adc #8
 sec
 sbc s9
 bcc @next
 sta sb
 ldy #5
 lda (shot_ptr),y
 asl a
 asl a
 asl a
 cmp sb
 bcc @next
 ; Source p01:72AE-72C2: a laser kills vulnerable ordinary enemies directly,
 ; unlike the normal shot's HP decrement. Three explicitly resistant types stay.
 ldy #O_TYPE
 lda (objptr),y
 cmp #$0b
 beq @next
 cmp #$1b
 beq @next
 cmp #$1e
 beq @next
 jsr ActorKilled
@next:
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
@done:rts
@erase:
 lda #0
 ldy #0
 sta (shot_ptr),y
 rts

; One 8x16 hardware sprite per 8-pixel laser character. Source physics is kept
; independently of NES scanline visibility. Alternate traversal avoids fixing
; the hidden end of a long beam to the same side every frame.
LaserDraw:
 ldy #5
 lda (shot_ptr),y
 beq @done
 sta sa
 lda #0
 sta sb
@cell:
 lda logic
 and #1
 beq @forward
 lda sa
 sec
 sbc sb
 sec
 sbc #1
 jmp @offset
@forward:lda sb
@offset:
 asl a
 asl a
 asl a
 ldy #1
 clc
 adc (shot_ptr),y
 sta sprite_x
 ldy #2
 lda (shot_ptr),y
 clc
 adc #15
 sta sprite_y
 lda #125
 sta sprite_frame
 lda #0
 sta sprite_flags
 sta sprite_pal
 jsr DrawSprite8
 inc sb
 lda sb
 cmp sa
 bcc @cell
@done:rts
