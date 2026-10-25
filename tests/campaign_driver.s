; Headless native unit-test cartridge, NOT a released game or a gameplay demo.
.setcpu "6502"
.import Flow_NewGame, Flow_Event
.segment "HEADER"
.byte "NES", $1a, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
.segment "CODE"
Reset:
    sei
    cld
    ldx #$ff
    txs
    lda #0
    sta $2000
    sta $2001
    sta $4010
    sta $4015
    lda #$40
    sta $4017
    jsr Flow_NewGame
    lda #$a5
    sta $0706
Wait:
    lda $0700
    beq Wait
    cmp #1
    beq NewGame
    lda $0701
    ldx $0702
    jsr Flow_Event
    jmp Result
NewGame:
    jsr Flow_NewGame
Result:
    sta $0703
    php
    pla
    and #1
    sta $0704
    tsx
    stx $0707
    inc $0705
    lda #0
    sta $0700
    jmp Wait
NMI: rti
.segment "VECTORS"
.word NMI, Reset, NMI
.segment "CHR"
.res $2000,0
