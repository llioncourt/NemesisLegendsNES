; Nemesis Legends - native 6502 campaign progression.
; This module is NOT a game by itself. Only the real actor/stage simulation may
; issue completion/secret events; no timers or auto-winning stages are used.
; Source provenance and the deliberate chronological bridge are in
; docs/CAMPAIGN_FLOW.md. The stage IDs are those of the original MSX games.
.setcpu "6502"
.include "campaign.inc"
.export Flow_State, Flow_NewGame, Flow_Event
.segment "BSS"
Flow_State: .res FLOW_SIZE
.segment "ZEROPAGE"
flow_event: .res 1
flow_param: .res 1
.segment "CODE"

Flow_NewGame:
    lda #0
    ldx #FLOW_SIZE-1
@clear:
    sta Flow_State,x
    dex
    bpl @clear
    jmp StartChapter

; A = event, X = parameter (planet ID for EVENT_CHOOSE_PLANET).
; Return A = action, carry clear for accepted, set for invalid.
; All registers are caller-saved. No mapper, PPU or APU state is touched.
Flow_Event:
    sta flow_event
    stx flow_param
    lda #ACTION_NONE
    sta Flow_State+F_ACTION
    lda Flow_State+F_CHAPTER
    cmp #4
    bcs Invalid
    lda Flow_State+F_COMPLETED
    and #8
    bne Invalid
    lda flow_event
    cmp #EVENT_SCENE_DONE
    bne @not_scene
    jmp SceneDone
@not_scene:
    lda Flow_State+F_SCENE
    bne Invalid
    lda flow_event
    cmp #EVENT_RETRY
    bne @not_retry
    jmp RetryChapter
@not_retry:
    lda Flow_State+F_RETRY
    bne Invalid
    lda flow_event
    cmp #EVENT_CLEAR
    bne @not_clear
    jmp ClearStage
@not_clear:
    cmp #EVENT_BONUS
    bne @not_bonus
    jmp EnterBonus
@not_bonus:
    cmp #EVENT_INTERIOR
    bne @not_interior
    jmp EnterInterior
@not_interior:
    cmp #EVENT_SECRET
    bne @not_secret
    jmp EnterSecret
@not_secret:
    cmp #EVENT_CHOOSE_PLANET
    bne @not_choose
    jmp ChoosePlanet
@not_choose:
    cmp #EVENT_CRYSTAL
    bne @not_crystal
    jmp TakeCrystal
@not_crystal:
    cmp #EVENT_MAP
    bne @not_map
    jmp TakeMap
@not_map:
    cmp #EVENT_ENDING_DEVICE
    bne @not_device
    jmp TakeEndingDevice
@not_device:
    cmp #EVENT_WHIRLPOOL
    bne Invalid
    jmp Whirlpool

Invalid:
    lda #ACTION_INVALID
    sta Flow_State+F_ACTION
    sec
    rts
Accepted:
    lda Flow_State+F_ACTION
    clc
    rts
LoadStage:
    sta Flow_State+F_STAGE
    lda #ACTION_LOAD
    sta Flow_State+F_ACTION
    jmp Accepted
ShowScene:
    sta Flow_State+F_SCENE
    lda #ACTION_SCENE
    sta Flow_State+F_ACTION
    jmp Accepted

StartChapter:
    ; Preserve chapter number and historical completed-chapter bits only.
    lda #0
    ldx #FLOW_SIZE-1
@clear:
    cpx #F_COMPLETED
    beq @next
    sta Flow_State,x
@next:
    dex
    bne @clear
    lda #1
    jmp LoadStage

ClearStage:
    lda Flow_State+F_CHAPTER
    beq ClearN1
    cmp #1
    bne @not_n2
    jmp ClearN2
@not_n2:
    cmp #2
    bne @n3
    jmp ClearSalamander
@n3:
    jmp ClearN3

ClearN1:
    ldx Flow_State+F_STAGE
    beq Invalid
    cpx #13
    bcs Invalid
    cpx #8
    bne @route
    lda #SCENE_N1_END
    jmp ShowScene
@route:
    lda N1Next,x
    jmp LoadStage
EnterBonus:
    lda Flow_State+F_CHAPTER
    bne Invalid
    ldx Flow_State+F_STAGE
    cpx #13
    bcs Invalid
    lda N1Bonus,x
    beq Invalid
    jmp LoadStage

; N2 p01:7C59: outbound 1..7, then inbound 6..0.
N2Next:
    lda Flow_State+F_STAGE
    ldx Flow_State+F_DIRECTION
    bne @back
    clc
    adc #1
    rts
@back:
    sec
    sbc #1
    rts
ClearN2:
    lda Flow_State+F_STAGE
    cmp #12
    bcc @valid
    jmp Invalid
@valid:
    cmp #8
    bcs @return
    cmp #7
    beq @turn
    cmp #0
    beq @end
    jsr N2Next
    jmp LoadStage
@return:
    lda Flow_State+F_RETURN_STAGE
    cmp #8
    bcc @load_return
    jmp Invalid
@load_return:
    jmp LoadStage
@turn:
    lda #SCENE_N2_TURN
    jmp ShowScene
@end:
    lda #SCENE_N2_END
    jmp ShowScene
EnterInterior:
    lda Flow_State+F_CHAPTER
    cmp #1
    bne @invalid
    lda Flow_State+F_STAGE
    beq @invalid
    cmp #6
    bcs @invalid
    jsr N2Next
    sta Flow_State+F_RETURN_STAGE
    lda #8
    jmp LoadStage
@invalid:
    jmp Invalid
EnterSecret:
    lda Flow_State+F_CHAPTER
    cmp #1
    bne @invalid
    lda Flow_State+F_STAGE
    cmp #10
    beq @eleven
    cmp #3
    beq @nine
    cmp #6
    bne @invalid
    lda #10
    bne @save
@nine:
    lda #9
@save:
    pha
    jsr N2Next
    sta Flow_State+F_RETURN_STAGE
    pla
    jmp LoadStage
@eleven:
    lda #11
    jmp LoadStage
@invalid:
    jmp Invalid

ClearSalamander:
    lda Flow_State+F_STAGE
    cmp #1
    beq @two
    cmp #2
    beq PlanetChoice
    cmp #6
    beq @end
    cmp #7
    beq @operation
    cmp #3
    bcc @invalid
    cmp #6
    bcs @invalid
    sec
    sbc #3
    tax
    lda Bits,x
    ora Flow_State+F_PLANETS
    sta Flow_State+F_PLANETS
    cmp #7
    bne PlanetChoice
    lda Flow_State+F_CRYSTAL
    beq @six
    lda #7
    jmp LoadStage
@two:
    lda #2
    jmp LoadStage
@operation:
    lda #1
    sta Flow_State+F_OPERATION_X
@six:
    lda #6
    jmp LoadStage
@end:
    lda Flow_State+F_OPERATION_X
    beq @bad
    lda Flow_State+F_CRYSTAL
    beq @bad
    lda #SCENE_SAL_GOOD
    jmp ShowScene
@bad:
    lda #SCENE_SAL_BAD
    jmp ShowScene
@invalid:
    jmp Invalid
PlanetChoice:
    lda #STAGE_PLANET_CHOICE
    sta Flow_State+F_STAGE
    lda #ACTION_CHOOSE
    sta Flow_State+F_ACTION
    jmp Accepted
ChoosePlanet:
    lda Flow_State+F_CHAPTER
    cmp #2
    bne @invalid
    lda Flow_State+F_STAGE
    cmp #STAGE_PLANET_CHOICE
    bne @invalid
    lda flow_param
    cmp #3
    bcc @invalid
    cmp #6
    bcs @invalid
    sec
    sbc #3
    tax
    lda Bits,x
    and Flow_State+F_PLANETS
    bne @invalid
    lda flow_param
    jmp LoadStage
@invalid:
    jmp Invalid
TakeCrystal:
    lda Flow_State+F_CHAPTER
    cmp #2
    bne @invalid
    lda Flow_State+F_STAGE
    cmp #1
    bcc @invalid
    cmp #8
    bcs @invalid
    lda #1
    sta Flow_State+F_CRYSTAL
    jmp Accepted
@invalid:
    jmp Invalid

ClearN3:
    lda Flow_State+F_STAGE
    beq @invalid
    cmp #12
    bcs @invalid
    cmp #11
    beq @end
    lda Flow_State+F_BACKTRACK
    bne @maps
    lda Flow_State+F_STAGE
    cmp #9
    beq @maps
    cmp #3
    beq @after3
    cmp #4
    beq @after4
    clc
    adc #1
    jmp LoadStage
@after3:
    lda #SCENE_N3_AFTER3
    jmp ShowScene
@after4:
    lda #SCENE_N3_AFTER4
    jmp ShowScene
@maps:
    lda #SCENE_N3_MAPS
    jmp ShowScene
@end:
    lda Flow_State+F_ENDING_FLAG
    beq @ordinary
    lda #SCENE_N3_SECRET_END
    jmp ShowScene
@ordinary:
    lda #SCENE_N3_END
    jmp ShowScene
@invalid:
    jmp Invalid
TakeMap:
    lda Flow_State+F_CHAPTER
    cmp #3
    bne @invalid
    lda Flow_State+F_STAGE
    ldx #0
    cmp #5
    beq @set
    inx
    cmp #7
    beq @set
    inx
    cmp #8
    bne @invalid
@set:
    lda Bits,x
    ora Flow_State+F_MAPS
    sta Flow_State+F_MAPS
    jmp Accepted
@invalid:
    jmp Invalid
TakeEndingDevice:
    lda Flow_State+F_CHAPTER
    cmp #3
    bne @invalid
    lda Flow_State+F_STAGE
    cmp #10
    bne @invalid
    lda #1
    sta Flow_State+F_ENDING_FLAG
    jmp Accepted
@invalid:
    jmp Invalid
Whirlpool:
    lda Flow_State+F_CHAPTER
    cmp #3
    bne @invalid
    lda Flow_State+F_STAGE
    cmp #3
    bne @invalid
    lda #ACTION_RESTART
    sta Flow_State+F_ACTION
    jmp Accepted
@invalid:
    jmp Invalid

SceneDone:
    lda Flow_State+F_SCENE
    beq @invalid
    cmp #SCENE_N1_END
    beq FinishChapter
    cmp #SCENE_N2_END
    beq FinishChapter
    cmp #SCENE_SAL_GOOD
    beq FinishChapter
    cmp #SCENE_N3_END
    beq FinishCampaign
    cmp #SCENE_N3_SECRET_END
    beq FinishCampaign
    cmp #SCENE_N2_TURN
    beq @turn
    cmp #SCENE_SAL_BAD
    beq @bad
    cmp #SCENE_N3_AFTER3
    beq @advance
    cmp #SCENE_N3_AFTER4
    beq @advance
    cmp #SCENE_N3_MAPS
    beq RouteMaps
@invalid:
    jmp Invalid
@turn:
    lda #0
    sta Flow_State+F_SCENE
    lda #1
    sta Flow_State+F_DIRECTION
    lda #6
    jmp LoadStage
@bad:
    lda #0
    sta Flow_State+F_SCENE
    lda #1
    sta Flow_State+F_RETRY
    lda #ACTION_RETRY
    sta Flow_State+F_ACTION
    jmp Accepted
@advance:
    lda #0
    sta Flow_State+F_SCENE
    lda Flow_State+F_STAGE
    clc
    adc #1
    jmp LoadStage
FinishChapter:
    ldx Flow_State+F_CHAPTER
    lda Bits,x
    ora Flow_State+F_COMPLETED
    sta Flow_State+F_COMPLETED
    inc Flow_State+F_CHAPTER
    jmp StartChapter
FinishCampaign:
    lda #0
    sta Flow_State+F_SCENE
    lda Flow_State+F_COMPLETED
    ora #8
    sta Flow_State+F_COMPLETED
    lda #ACTION_FINISHED
    sta Flow_State+F_ACTION
    jmp Accepted
RouteMaps:
    lda #0
    sta Flow_State+F_SCENE
    lda Flow_State+F_MAPS
    cmp #7
    bne @missing
    lda #0
    sta Flow_State+F_BACKTRACK
    lda #10
    jmp LoadStage
@missing:
    lda #1
    sta Flow_State+F_BACKTRACK
    lda Flow_State+F_MAPS
    and #1
    beq @five
    lda Flow_State+F_MAPS
    and #2
    beq @seven
    lda #8
    jmp LoadStage
@five:
    lda #5
    jmp LoadStage
@seven:
    lda #7
    jmp LoadStage
RetryChapter:
    lda Flow_State+F_CHAPTER
    cmp #2
    bne @invalid
    lda Flow_State+F_RETRY
    beq @invalid
    jmp StartChapter
@invalid:
    jmp Invalid

.segment "RODATA"
; Index 0 is invalid. 9..12 are bonus maps, not main stages.
N1Next: .byte 0,2,3,4,5,6,7,8,0,3,4,5,8
N1Bonus: .byte 0,0,9,10,11,0,0,12,0,0,0,0,0
Bits: .byte 1,2,4,8
