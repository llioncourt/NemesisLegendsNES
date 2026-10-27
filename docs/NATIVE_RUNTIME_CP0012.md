# CP0012 - native Nemesis stage-4 end sequence and two source enemy types

Scope: the normal route of MSX Nemesis stage 4 now runs its original end
sequence instead of halting at world `$0128`. Everything below is measured on
the unmodified FCEUmm core with QA invulnerability injected and nothing else
(no stage, world, phase, boss or actor writes). It is not a hardware test and
not a claim of visual parity or an unassisted clear.

## Source behaviour ported

| Source | Native | Notes |
|---|---|---|
| p01:$6E15 `final_de_la_fase_4` | `src/native_stage4.s` state machine | Steps 0..4 as in the Z80: eruption, tower, limit `$019F`, boss 5, limit `$01C0`, Big Core, `acaba_la_fase`. |
| p01:$70D6 tanda mode 2, $7132, $713C, $718D | `TandaTick` | At exactly `$0128`: E140=2, E148=`$00B4`, crater X=`$D0`, minus 8 per column, over when the crater leaves. Type `$0F` rocks every even frame, speed table shared with the stage-1 volcano, first fifteen at half speed, horizontal sign from the remaining count, gravity `$FF78` (upward) and colour 6/8 from `remata_el_tipo_15` p01:$6C77. `VolcanoParticle` now adds the record's own acceleration, which leaves stage 1 byte-identical in behaviour. Rocks burst on terrain (p01:$71AD) without score. |
| p02:$8E77 `monta_las_cinco_piezas` | `SpawnTower` (shared with stage 1) | Same five pieces, HP 10, 92-frame bricks. The 32-column group timer E1B2 ends the encounter. Stage-4 piece graphics come from the stage-4 character set (sheet frames 99..103, previously blank in this stage). |
| p02:$8CE4 `paso_del_jefe_3` (E151=`$0501`) | `Boss5Tick`, `MovePieces`, `PieceContact`, `Stage4ShotHit`, `Stage4LaserHit`, `Stage4Draw` | 600-frame window, a piece every 72 frames (difficulty 0), up to eight, HP `$28`, the exact twelve-step route of p02:$8D64 at 2 px/frame including the ship-row tracking step, 4 damage per shot / 1 per laser frame, `$10` score, explosion on death, encounter over when no piece or explosion remains. Pieces are 4x3 source characters drawn as six 8x16 sprites with the four-frame blink of p02:$8E5F/$8E6B (sheet frames 104, 109..112). Ship contact uses the source cell probe with empty corners. |
| p01:$6EA0 / L_6D43 | `StageEvents` stage 4 | At `$01C0` the shared wait-for-clear and the type-1 Big Core, then `AdvanceStage` to stage 5. |
| p03:$AD6E/$AD92 type `$0A` | `TypeTen` | Stage 3/4/5 opening-wave type. Alternating upward/downward curve, vertical acceleration reversed when |vY| reaches 4.0, turns back below column `$30`, unaimed fire, six frames every four. Previously unported: the units parked at the screen edge and blocked every wait-for-clear. |
| p03:$A937/$A95A type 6 | `TypeSix` rewritten | Hopper with the `$78`-frame rope, ground test between rows `$58` and `$9F`, hops toward the ship's column, then two pixels left and out. The old approximation bounced in place forever (the "spinners" seen at the stage-1 edges). |

## Measured (reports/cp0012/stage_four_integration.json)

Controller-driven from the title, SPD:60, invulnerability only:
stage 4 entered, eruption at `$0128` with type-`$0F` rocks, tower at `$0171`
with five pieces, boss 5 at `$019F` with eight pieces spawned and up to six
alive at once, scroll resumed, Big Core wait at `$01C0`, Big Core fought,
stage 5 reached, zero missed NMIs inside stage 4.

`tools/test_secret_targets.py` route `none` now ends in stage 5 through this
sequence instead of the old phase-13 halt; route `all_three` still reaches
stage 5 through bonus 11.

## Known limits

- Difficulty E111 is fixed at zero: tower volley 92 frames, boss-5 period 72.
- Bricks of the tower are drawn with the generic bullet sprite, as in stage 1.
- Stage-4 visuals are the provisional palette reduction; no art approval.
- Missed NMIs still occur in stage 3 right after the `$0060` midboss load
  (pre-existing in CP0010/CP0011, 57 frames under this controller pattern);
  stage 4 itself misses none.
- Stage 5 onward remains resource descriptors, not playable source logic.
