# CP0013 handoff - cheat menu, banked stage code, four-game inventories

Private ROM: `build/native/Nemesis_Legends_CP0013.nes` (hash in
`manifests/checkpoint.json`). `python tools/checkpoint.py test` now also runs
`tools/test_cheat_menu.py`. Stage-specific logic goes in the `STAGECODE`
segment (bank 10 at `$8000`, mapped only while it runs; the `$5114` shadow is
`bank8000`); common services stay in ACTORS/CODE. Stage 5 code should be added
there, with its own `tools/test_stage_five.py`.

Inventories: run `python tools/extract_salamander_msx.py`,
`python tools/extract_nemesis3_msx.py`, `python tools/extract_nes_graphics.py`,
then `python tools/nemesis_structure.py`, `python tools/asset_manifest.py`,
`python tools/compare_msx_nes.py`, `python tools/storyboard.py`,
`python tools/budget.py`. All generated docs say so in their first line.

---

# CP0012 handoff - stage 4 end sequence; anthology remains WIP

Private ROM: `build/native/Nemesis_Legends_CP0012.nes` (hash in
`manifests/checkpoint.json`). Build with `python tools/checkpoint.py build`;
test with `python tools/checkpoint.py test`, which now includes
`tools/test_stage_four.py`.

New in CP0012: `src/native_stage4.s` (eruption, tower, boss 5, Big Core hand-off
for stage 4), source enemy type `$0A` and a faithful type 6 in
`src/native_actors.s`, stage-4 sprite frames 99..104 and 109..112 generated from
the stage-4 character set, and a read-only QA mirror of the actor records at
`$0780..$07CF` for the emulator tests. The phase-13 stage-4 halt is gone.

Next: stage 5 (`final_de_la_fase_5` p01:$6EA8, two bank-3 calls, limit `$1FF`),
then stages 6..8 and the Nemesis ending, before the other three chapters.

---

# CP0009 handoff - selectable speed; anthology remains WIP

## Resume without restarting the existing port

The only new production gameplay changes are 30/40/60 logical-FPS pacing,
controller SELECT cycle and HUD speed indicator. This is a mitigation of the
user's speed complaint, NOT a solution to the ugly graphics in the screenshot.
The CP0008 stages and bonus route remain. Four-chapter coverage has not advanced.

Private ROM: `build/native/Nemesis_Legends_CP0009.nes`. Build with `python
tools/checkpoint.py build`; test with `python tools/checkpoint.py test`.
Exact hashes are in `manifests/checkpoint.json`.

SELECT cycles 30 (default), 40, 60 while video/APU remain 60. A power-up press
is buffered through skipped frames. Original source-rhythm tests select 60 via
controller and pass. Full source graphics, canonical HUD, later stages, the
other three games, cutscenes, music conversion and final cheat menu remain
missing. Do not call it complete, do not reintroduce title-demo work.

---

# CP0008 handoff — native stage-2 branching, no anthology completion

## Resume this real baseline

The playable native ROM is `build/native/Nemesis_Legends_CP0008.nes`. The exact
hash and byte count are pinned by `manifests/checkpoint.json` and
`build/native/build.json`; regenerate with `python tools/checkpoint.py build`.

This checkpoint is an extension of CP0007, NOT a fresh port. The custom title,
Gradius II source font, native stage1, original donor APU, global gameplay
modules, 12 compact native stage descriptors, source reconciliation and all
private hashes remain intact. Never use CP0003 recovered prefix as runtime.

## What is newly implemented and tested

Read `docs/NATIVE_RUNTIME_CP0008.md`: stage2's six source 5-rock walls, source
900-frame rock rain, type8 growth, secret target at world $0190, 64-frame
branch into optional stage9, its terrain/return route, Big Core and stage3 entry.
The runtime uses the existing production 6502 motor, MMC5 and original compact
source map formats. The exact source references are listed there.

A controller-driven **assisted** route (invulnerability only) reaches stage3
from the normal path and another reaches stage3 via stage9. Both paths measure
zero missed NMIs. Native behavior tests must not be confused with complete
combat/cutscene/media parity. See the CP0008 JSON reports and PNG captures.

## Priority to continue, no new demo

1. Stage3 full original events, including optional target and bonus10. Source
   stage3 has no terrain but has real enemy, boss and secret mechanics.
2. Stage4/bonus11, stage5, stage6, stage7/bonus12, stage8 plus source ending.
3. Native **Nemesis 2**, **Salamander** incl Operation X and **Nemesis 3** as
   specialized game chapters in one continuous campaign.
4. Real APU music conversion (base channels mandatory, MMC5 extensions
   optional), source story/cutscenes, all endings and optional co-op rules.
5. Global deduplication and whole-game budget. Native full test campaign,
   Windows offline reproducible build and IPS-only public release.
6. After real full-campaign integration: Konami Code and **English Silicon Forge**
   cheat menu with stage/scene selectors and Sound Test, not mock actions.

## Recover the project

Keep the internal folder named `Nemesis_Legends_CP0001` (may sit under any
parent path, including spaces). Execute `VERIFY.cmd` or
`python tools/checkpoint.py verify`, `build`, `test`, or `sources`. Local
Linux tools/core are bundled privately; Windows needs matching platform
executables as described in `docs/BUILD_AND_TEST.md`. `CHECKPOINT_FILES.json`
is a source/private package integrity ledger; it is not public source.

Original source sets: 4 hash-verified MSX and 6 hash-verified NES/Famicom ROMs,
retained privately. Source-derived CHR, terrain, licensed music and a private
playable ROM must NOT be pushed wholesale to public GitHub. The repository
`llioncourt/NemesisLegendsNES` is the public code source of truth; IPS only for
public game distributions. Verify the actual remote commit before claiming
publication.

No automated task or background execution is active. The next execution must
start from this CP0008 source and run a measurable new gameplay checkpoint.
