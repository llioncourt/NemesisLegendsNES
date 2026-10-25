.setcpu "6502"
.include "native.inc"
.import DrawSprite, PlayerHit, SourceObjectDefaults, AngleTable, SineTable, AdvanceStage
.export ActorsFrame,ActorsDraw,SpawnCannon,SpawnWaves,ShotsFrame,InitActors
.segment "ACTORS"
InitActors:
 lda #0
 ldx #0
@clear:
 sta OBJECTS,x
 sta OBJECTS+$100,x
 sta SHOTS,x
 sta ENEMY_SHOTS,x
 inx
 bne @clear
 lda #0
 sta cannon_ptr
 lda stagebase
 clc
 adc #$a
 sta cannon_ptr+1
 rts
SpawnCannon:
 rts
SpawnWaves:
 rts
ActorsFrame:
 rts
ActorsDraw:
 rts
ShotsFrame:
 rts
