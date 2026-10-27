; Nemesis MSX stage 4 end sequence, from p01:$6E15 final_de_la_fase_4.
;  1. World $0128: ceiling eruption, source tanda mode 2 (p01:$70D6/$7132/$713C):
;     type $0F rocks from the crater at X=$D0 that scrolls with the map, every
;     even frame, remaining counter $00B4, upward gravity $FF78 (p01:$6C77).
;  2. World $0171: the same five-piece tower as stage 1 (p02:$8E77), 32 columns.
;  3. World $019F (scroll limit E105): "boss 5" (E151=$0501 -> p02:$8CE4), a
;     600-frame spawner of up to eight type-6 pieces (HP $28, 10-step route
;     p02:$8D64, ship tracking, 2 px per frame), no HP of its own.
;  4. Scroll resumes to $01C0 (p01:$6E8C), then the ordinary type-1 Big Core
;     (L_6D43) and acaba_la_fase -> stage 5. Difficulty E111 is zero here.
.setcpu "6502"
.include "native.inc"
.include "actors.inc"
.include "boss.inc"
.include "longbranch.inc"
.import SpawnActor,SpawnTower,ObjectPointer,RNG,PlayerHit,DrawSprite,SpriteCode
.import TerrainSolid,VolcanoSpeeds
.export Stage4Init,Stage4Tick,Stage4Draw,Stage4ShotHit,Stage4LaserHit,S4_State

P_STEP=0
P_X=1
P_Y=2
P_HP=3

.segment "BSS"
S4_State:
s4_step:        .res 1   ; E065: 0 before $128, 1 tower/limit, 2 boss 5, 3 run to $1C0, 4 core
s4_tanda:       .res 1   ; E140 (2 while the eruption runs)
s4_crater:      .res 1   ; E141 crater X, -8 per column
s4_count:       .res 2   ; E148 remaining rocks
s4_tower:       .res 1   ; E1B0
s4_tower_t:     .res 1   ; E1B2 group timer, -8 per column
s4_b5:          .res 1   ; E190: 0 start, 1 spawning, 2 draining, 3 finished
s4_b5_timer:    .res 2   ; E153 600-frame window
s4_b5_period:   .res 1   ; E156
s4_b5_reload:   .res 1   ; E157
s4_rocks:       .res 1   ; QA: rocks emitted
s4_b5_spawned:  .res 1   ; QA: pieces spawned
s4_b5_killed:   .res 1   ; QA: pieces destroyed by the player
S4_Pieces:      .res 32  ; eight E780 pieces: step, X, Y, HP (HP 0 = free)
S4_END:

.segment "ACTORS"
Stage4Init:
 lda #0
 ldx #(S4_END-S4_State-1)
@clear:
 sta S4_State,x
 dex
 bpl @clear
 rts

Stage4Tick:
 lda stage_id
 cmp #4
 jne @rts
 lda phase
 cmp #15
 jeq Boss5Tick
 cmp #0
 jne @rts
 jsr TandaTick
 jsr RockTerrain
 jsr TowerTick
 lda new_column
 jeq @rts
 lda worldhi
 cmp #1
 jne @rts
 lda worldlo
 ldx s4_step
 beq @step0
 cpx #1
 beq @step1
 cpx #3
 beq @step3
 rts
@step0:
 ; p01:$6E3B: at exactly $0128, E140=2, E148=$00B4, E141=$D0.
 cmp #$28
 bne @rts
 lda #2
 sta s4_tanda
 lda #$d0
 sta s4_crater
 lda #$b4
 sta s4_count
 lda #0
 sta s4_count+1
 lda #$9b
 sta audio_cmd
 rts
@step1:
 cmp #$71
 beq @tower
 cmp #$9f
 bne @rts
 ; E107: the scroll reached its limit; E151=$0501 starts boss 5.
 lda #15
 sta phase
 lda #0
 sta s4_b5
 lda #2
 sta s4_step
 rts
@tower:
 ; p02:$8E77 at $0171: E1B0=1, E1B2=$F8, five pieces from table $8EBA.
 lda s4_tower
 bne @rts
 lda #1
 sta s4_tower
 lda #$f8
 sta s4_tower_t
 jmp SpawnTower
@step3:
 ; enciende_al_jefe_4 at $01C0 -> L_6D43: ordinary Big Core once the screen is clear.
 cmp #$c0
 bne @rts
 lda #4
 sta phase
 lda #30
 sta phase_timer
 lda #4
 sta s4_step
@rts: rts

; corre_la_tanda_de_enemigos p01:$70D6, mode 2.
TandaTick:
 lda s4_tanda
 jeq @rts
 lda new_column
 beq @emit
 lda s4_crater
 sec
 sbc #8
 sta s4_crater
 bcs @emit
@finish:
 ; acaba_la_tanda_de_enemigos p01:$7116 -> E150; step 0 clears E140 and advances.
 lda #0
 sta s4_tanda
 lda #1
 sta s4_step
 rts
@emit:
 lda logic
 and #1
 jne @rts
 lda s4_count
 bne :+
 dec s4_count+1
:
 dec s4_count
 lda s4_count
 ora s4_count+1
 beq @finish
 lda s4_crater
 sta sprite_x
 lda #$20
 sta sprite_y
 lda #0
 sta sprite_pal
 lda #$0f
 jsr SpawnActor
 jcs @rts
 ; remata_el_tipo_15 p01:$6C77: stage 4 gravity $FF78, colour 6 or 8.
 ldy #O_AYL
 lda #$78
 sta (objptr),y
 iny
 lda #$ff
 sta (objptr),y
 jsr RNG
 and #2
 clc
 adc #6
 ldy #O_COLOR
 sta (objptr),y
 ; velocidad_de_la_tanda p01:$713C: table $718D by R&7; vertical kept positive.
 jsr RNG
 and #7
 asl a
 asl a
 tax
 lda VolcanoSpeeds,x
 ldy #O_VYL
 sta (objptr),y
 lda VolcanoSpeeds+1,x
 iny
 sta (objptr),y
 lda VolcanoSpeeds+2,x
 sta s0
 lda VolcanoSpeeds+3,x
 sta s1
 lda s4_count
 and #1
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
 ; Remaining >= $A5: both components halved (first fifteen rocks).
 lda s4_count+1
 bne @half
 lda s4_count
 cmp #$a5
 bcc @counted
@half:
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
@counted:
 inc s4_rocks
@rts: rts

; mira_si_choca_con_el_mapa_2 p01:$71AD: a rock meeting terrain bursts (no score).
RockTerrain:
 ldx #0
@loop:
 txa
 pha
 jsr ObjectPointer
 ldy #O_TYPE
 lda (objptr),y
 cmp #$0f
 bne @next
 ldy #O_X
 lda (objptr),y
 sta sprite_x
 ldy #O_VYH
 lda (objptr),y
 bmi @up
 ldy #O_Y
 lda (objptr),y
 clc
 adc #$10
 bcs @next
 bcc @probe
@up:
 ldy #O_Y
 lda (objptr),y
@probe:
 sta sprite_y
 jsr TerrainSolid
 bcc @next
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
 lda #$aa
 sta audio_cmd
@next:
 pla
 tax
 inx
 cpx #12
 bne @loop
 rts

; corre_el_grupo p02:$8ED6: E1B2 -= 8 per column; on borrow the tower is over.
TowerTick:
 lda s4_tower
 beq @rts
 lda new_column
 beq @rts
 lda s4_tower_t
 sec
 sbc #8
 sta s4_tower_t
 bcs @rts
 lda #0
 sta s4_tower
 ldx #12
@clear:
 txa
 pha
 jsr ObjectPointer
 ldy #O_TYPE
 lda (objptr),y
 cmp #$20
 bne :+
 lda #0
 sta (objptr),y
 ldy #O_FLAGS
 sta (objptr),y
:
 pla
 tax
 inx
 cpx #17
 bne @clear
@rts: rts

; paso_del_jefe_3 p02:$8CEA.
Boss5Tick:
 lda s4_b5
 bne @running
 lda #$58
 sta s4_b5_timer
 lda #2
 sta s4_b5_timer+1
 lda #$48
 sta s4_b5_period
 sta s4_b5_reload
 lda #1
 sta s4_b5
 rts
@running:
 jsr MovePieces
 jsr PieceContact
 lda s4_b5
 cmp #1
 bne @drain
 ; suelta_una_pieza_3 p02:$8D0A
 lda s4_b5_timer
 bne :+
 dec s4_b5_timer+1
:
 dec s4_b5_timer
 lda s4_b5_timer
 ora s4_b5_timer+1
 bne @period
 lda #2
 sta s4_b5
 rts
@period:
 dec s4_b5_period
 bne @rts
 lda s4_b5_reload
 sta s4_b5_period
 ldx #0
@find:
 lda S4_Pieces+P_HP,x
 beq @spawn
 txa
 clc
 adc #4
 tax
 cpx #32
 bne @find
 rts
@spawn:
 ; ficha p02:$8D2F: type 6, step 0, Y=$18, X=$F8, HP=$28.
 lda #0
 sta S4_Pieces+P_STEP,x
 lda #$f8
 sta S4_Pieces+P_X,x
 lda #$18
 sta S4_Pieces+P_Y,x
 lda #$28
 sta S4_Pieces+P_HP,x
 inc s4_b5_spawned
 rts
@drain:
 ; mira_si_se_acabo_el_jefe_3 p02:$8D39: no piece and no explosion left.
 cmp #2
 bne @rts
 ldx #0
@alive:
 lda S4_Pieces+P_HP,x
 bne @rts
 txa
 clc
 adc #4
 tax
 cpx #32
 bne @alive
 ldx #0
@explosions:
 txa
 pha
 jsr ObjectPointer
 ldy #O_TYPE
 lda (objptr),y
 cmp #$15
 beq @still
 pla
 tax
 inx
 cpx #12
 bne @explosions
 ; E150 -> espera_y_suelta_hasta_1C0: E151=0, E105=$01C0, scroll resumes.
 lda #3
 sta s4_b5
 lda #0
 sta phase
 lda #3
 sta s4_step
 rts
@still:
 pla
 tax
@rts: rts

; corre_las_ocho_piezas_3 p02:$8D46, route table p02:$8D64.
StepDX:     .byte $fe,$fe,$fe,$fe,$fe,$fe,$fe,$fe,$00,$02
StepDY:     .byte $00,$02,$00,$fe,$00,$02,$00,$fe,$02,$00
StepAxis:   .byte P_X,P_Y,P_X,P_Y,P_X,P_Y,P_X,P_X,P_Y,P_X
StepTarget: .byte $e6,$30,$98,$18,$66,$30,$18,$08,$78,$e0
MovePieces:
 ldx #0
@loop:
 lda S4_Pieces+P_HP,x
 beq @next
 lda S4_Pieces+P_STEP,x
 cmp #10
 beq @track
 bcs @charge
 tay
 lda S4_Pieces+P_X,x
 clc
 adc StepDX,y
 sta S4_Pieces+P_X,x
 lda S4_Pieces+P_Y,x
 clc
 adc StepDY,y
 sta S4_Pieces+P_Y,x
 lda StepAxis,y
 cmp #P_X
 bne @axisy
 lda S4_Pieces+P_X,x
 jmp @compare
@axisy:
 lda S4_Pieces+P_Y,x
@compare:
 cmp StepTarget,y
 bne @next
 inc S4_Pieces+P_STEP,x
 bne @next
@track:
 ; p02:$8DF0: within eight rows of the ship, or outside $30..$87, charge.
 lda player_y
 sec
 sbc S4_Pieces+P_Y,x
 clc
 adc #8
 cmp #17
 bcc @aligned
 lda player_y
 cmp S4_Pieces+P_Y,x
 bcs @down
 dec S4_Pieces+P_Y,x
 dec S4_Pieces+P_Y,x
 jmp @bounds
@down:
 inc S4_Pieces+P_Y,x
 inc S4_Pieces+P_Y,x
@bounds:
 lda S4_Pieces+P_Y,x
 cmp #$30
 bcc @aligned
 cmp #$88
 bcc @next
@aligned:
 inc S4_Pieces+P_STEP,x
 bne @next
@charge:
 lda S4_Pieces+P_X,x
 sec
 sbc #2
 sta S4_Pieces+P_X,x
 cmp #$f0
 bcc @next
 lda #0
 sta S4_Pieces+P_HP,x
@next:
 txa
 clc
 adc #4
 tax
 cpx #32
 jne @loop
 rts

; choca_la_nave p02:$98DA with the piece characters $BA..$C5 (pared_de_la_fase_5):
; probes (shipY+8, shipX) and (shipY+8, shipX+8) against the 4x3 block whose
; four corner cells are empty.
PieceContact:
 ldx #0
@loop:
 lda S4_Pieces+P_HP,x
 jeq @next
 lda player_y
 clc
 adc #8
 sec
 sbc S4_Pieces+P_Y,x
 cmp #24
 bcs @next
 sta s0
 lda player_x
 sec
 sbc S4_Pieces+P_X,x
 jsr @probe
 bcs @hit
 lda player_x
 clc
 adc #8
 sec
 sbc S4_Pieces+P_X,x
 jsr @probe
 bcc @next
@hit:
 txa
 pha
 jsr PlayerHit
 pla
 tax
@next:
 txa
 clc
 adc #4
 tax
 cpx #32
 bne @loop
 rts
@probe:
 cmp #32
 bcs @miss
 sta s1
 lda s0
 cmp #8
 bcc @edge
 cmp #16
 bcc @solid
@edge:
 lda s1
 cmp #8
 bcc @miss
 cmp #24
 bcs @miss
@solid:
 sec
 rts
@miss:
 clc
 rts

; Player shot against the pieces: p01:$760E / caja $2018 / le_da_al_jefe $773F.
; C set = shot consumed. Shot record: byte 1 X, byte 2 Y.
Stage4ShotHit:
 lda stage_id
 cmp #4
 bne @no
 lda phase
 cmp #15
 bne @no
 txa
 pha
 tya
 pha
 ldy #1
 lda (shot_ptr),y
 sta sd
 iny
 lda (shot_ptr),y
 sta se
 ldx #0
@loop:
 lda S4_Pieces+P_HP,x
 beq @next
 jsr PieceBox
 bcs @next
 ; Normal shot: consumed, four points of damage.
 lda S4_Pieces+P_HP,x
 sec
 sbc #4
 beq @dead
 bcc @dead
 sta S4_Pieces+P_HP,x
 lda #$aa
 sta audio_cmd
 sec
 bcs @out
@dead:
 jsr PieceDestroyed
 sec
 bcs @out
@next:
 txa
 clc
 adc #4
 tax
 cpx #32
 bne @loop
 clc
@out:
 pla
 tay
 pla
 tax
 rts
@no: clc
 rts

; sd/se = point; X = piece. C clear when inside [Y-1,Y+$18] x [X-15,X+$20].
PieceBox:
 lda se
 sec
 sbc S4_Pieces+P_Y,x
 clc
 adc #1
 cmp #$1a
 bcs @outside
 lda sd
 sec
 sbc S4_Pieces+P_X,x
 clc
 adc #15
 cmp #$30
 bcs @outside
 clc
 rts
@outside:
 sec
 rts

; Laser: one point per frame, beam not consumed (p01:$773F laser path).
; s9 = beam start X, sa = beam length in characters, shot byte 2 = Y.
Stage4LaserHit:
 lda stage_id
 cmp #4
 bne @rts
 lda phase
 cmp #15
 bne @rts
 txa
 pha
 tya
 pha
 ldy #2
 lda (shot_ptr),y
 sta se
 ldx #0
@loop:
 lda S4_Pieces+P_HP,x
 beq @next
 ; Vertical box as for shots; horizontally the piece centre inside the beam.
 lda S4_Pieces+P_X,x
 clc
 adc #15
 sta sd
 sec
 sbc s9
 bcc @next
 sta sf
 lda sa
 asl a
 asl a
 asl a
 cmp sf
 bcc @next
 lda sd
 jsr PieceBox
 bcs @next
 dec S4_Pieces+P_HP,x
 bne @next
 jsr PieceDestroyed
@next:
 txa
 clc
 adc #4
 tax
 cpx #32
 bne @loop
 pla
 tay
 pla
 tax
@rts: rts

; revienta_y_cobra p01:$77C8: +$10 score, explosion at the piece, slot freed.
PieceDestroyed:
 lda #0
 sta S4_Pieces+P_HP,x
 inc s4_b5_killed
 lda score_lo
 clc
 adc #16
 sta score_lo
 bcc :+
 inc score_hi
:
 lda #$ab
 sta audio_cmd
 lda S4_Pieces+P_X,x
 clc
 adc #8
 sta sprite_x
 lda S4_Pieces+P_Y,x
 clc
 adc #4
 sta sprite_y
 lda #0
 sta sprite_pal
 txa
 pha
 lda #$15
 jsr SpawnActor
 bcs @full
 lda #0
 ldy #O_FLAGS
 sta (objptr),y
 ldy #O_DRAW
 sta (objptr),y
 ldy #O_CLOCK
 sta (objptr),y
 lda #$78
 ldy #O_FRAME
 sta (objptr),y
@full:
 pla
 tax
 rts

; dibuja_la_pieza_parpadeando p02:$8E45: two halves alternating every four frames.
CenterFrame: .byte 104,109
ArmFrame:    .byte 110,111
Stage4Draw:
 lda stage_id
 cmp #4
 jne @rts
 lda phase
 cmp #15
 jne @rts
 lda #0
 sta sprite_pal
 sta sprite_flags
 ldx #0
@loop:
 lda S4_Pieces+P_HP,x
 jeq @next
 txa
 pha
 lda S4_Pieces+P_Y,x
 clc
 adc #15
 sta s0
 lda S4_Pieces+P_X,x
 sta s1
 lda logic
 and #4
 beq :+
 lda #1
:
 sta s2
 ; centre 16x16 at (X+8, Y)
 lda s1
 clc
 adc #8
 bcs @arms
 sta sprite_x
 lda s0
 sta sprite_y
 ldy s2
 lda CenterFrame,y
 sta sprite_frame
 jsr DrawSprite
@arms:
 ldy s2
 lda ArmFrame,y
 tay
 lda SpriteCode,y
 sta s3
 lda s1
 sta sprite_x
 lda s0
 clc
 adc #8
 sta sprite_y
 lda s3
 jsr DrawCode8
 lda s1
 clc
 adc #24
 bcs @bottom
 sta sprite_x
 lda s3
 clc
 adc #2
 jsr DrawCode8
@bottom:
 ldy #112
 lda SpriteCode,y
 sta s3
 lda s0
 clc
 adc #16
 sta sprite_y
 lda s1
 clc
 adc #8
 bcs @drawn
 sta sprite_x
 lda s3
 jsr DrawCode8
 lda s1
 clc
 adc #16
 bcs @drawn
 sta sprite_x
 lda s3
 clc
 adc #2
 jsr DrawCode8
@drawn:
 pla
 tax
@next:
 txa
 clc
 adc #4
 tax
 cpx #32
 jne @loop
@rts: rts

; One 8x16 hardware sprite with an explicit CHR code in A, palette 0.
DrawCode8:
 ldx sprite_index
 cpx #$fc
 bcs @done
 sta OAM+1,x
 lda sprite_y
 sta OAM,x
 lda #0
 sta OAM+2,x
 lda sprite_x
 sta OAM+3,x
 inx
 inx
 inx
 inx
 stx sprite_index
@done: rts
