; Adjustable gameplay pacing. Linked after all existing BSS segments to preserve
; the CP0008 campaign and stage-two RAM ABI exactly ($0500 and $0510).
.setcpu "6502"
.export GamePace_Mode, GamePace_Phase, GamePace_Edges
.segment "BSS"
; Mode 0=30 logical Hz, 1=40 logical Hz, 2=60 logical Hz.
; Physical video and APU clocks remain 60Hz for all three modes.
GamePace_Mode:  .res 1
GamePace_Phase: .res 1
GamePace_Edges: .res 1
