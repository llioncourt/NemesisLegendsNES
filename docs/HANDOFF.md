# CP0017 handoff (2026-10-29) - Phase 1a, MSX asset catalogue

Every object and screen of the four MSX games catalogued from the code and checked in
openMSX runs of every stage (0 unmapped drawings): `manifests/catalog_msx.json`,
`docs/CATALOG_MSX.md`, `docs/CATALOG_METHOD.md`. The Nemesis extractor now loads the
per-stage sprite blocks (47 -> 107 drawings; TwinBee's 10 excluded). New capture tools:
`tools/msx_capture.py`, `tools/nes_ppu_state.py`. ROM unchanged (CP0016). Extractor
findings for phase 7 are in CONTINUATION.md.

# CP0016 handoff (2026-10-28) - pinned; owner's scope fixed

- CP0016 is pinned: the WIP ROM of 2026-10-27 was rebuilt byte-identical from
  the CP0014 private package plus `main` and `checkpoint.py test` passed.
- PR #2 (CP0012-CP0016) was merged into `main` by the owner's decision; work
  continues on `main`.
- `docs/DECISIONS.md` holds the owner's scope and rules. Next: Phase 1
  (extraction of every MSX and NES asset, stage mapping 1.1).

---

# Handoff after CP0015 (session of 2026-10-27, stopped for lack of credits)

## State of the branch `claude/repo-review-d7tp9q` (PR #2)
- Last pinned checkpoint: **CP0015** (`manifests/checkpoint.json`, ROM sha 6bb2384a...). `python tools/checkpoint.py test` passes on it.
- **CP0016 is work in progress, not pinned**: `src/native_kernel.s` (AdvanceStage: chapter = Flow F_CHAPTER+1; mode 4 scene placeholder), `src/native_cheat.s` (CheatApply stores F_CHAPTER = chapter-1; SceneOpen/SceneFrame/SceneApply; TextScreenOpen/On shared with the cheat menu), `tools/test_chapter_flow.py` (8 checks pass on the CP0016 build, sha c10f9928...). `tools/build_native.py` and `tools/checkpoint.py` already name CP0016. The pinned-hash unit test fails until the manifest is re-pinned.
- To close CP0016: rebuild, `checkpoint.py test`, pin `manifests/checkpoint.json`, write `docs/NATIVE_RUNTIME_CP0016.md`, update README/CONTINUATION/content_coverage, commit, build the private package (scratchpad `make_package.sh`, retarget to CP0016).

## Asset bible (Frente B/C) - done and QA-audited
- `tools/asset_bible.py` -> `manifests/asset_bible.json`, `docs/ASSET_BIBLE.md`: 60 game objects. MSX side proven from the Z80 code, NES side proven from OAM captures of Gradius NES (US) with the game's own palettes. Policies: REUSE_NES 24, ADAPT_NES 3, CONVERT_MSX 26, NES-only 7. QA: 57 PASS, 3 UNRESOLVED (Moai background reference, boss kinds 1 and 2).
- The evidence (per-object PNGs, sprgen reconstructions, OAM logs, QA reports) is private: zip `Nemesis_Legends_Asset_Bible_Evidence.zip` delivered to the owner; it must go into the private package. The generator needs `--msx <folder> --nes <folder> --qa <report.json> --rom-qa <round1 report.json>` from that zip.
- **No ROM uses NES graphics yet.** Every ROM so far draws MSX conversions. Next step: a per-object "MSX frame -> NES tiles + palette" table fed into `tools/build_native_assets.py`, starting with the shared objects (ship, option, shield, capsules, shots, missile, laser, explosion), then stage-1 enemies. The bible's `rom_deviations` list the current drawing bugs (enemy shot uses frame 27, blue capsule red palette, option without colour cycle, missile without rolling frame, etc.).

## Specs ready for Frente H
- Nemesis stage 5: full behavioural spec from the disassembly (end sequence p01:$6EA8, types $1B-$1F, pods/turrets, music) in the owner's scratchpad delivery `spec_nemesis_stage5.md` (private; add to the package). Port it in the STAGECODE bank with `tools/test_stage_five.py`.
- Nemesis 2 map-1 gameplay spec: not produced (agent stopped).

## Rules confirmed by the owner this session
- Follow the brief's frentes in order; do not substitute priorities. Deliver a playable ROM at each checkpoint; IPS only for public distribution; private material never committed.
- Asset identification only with evidence (code for MSX, OAM capture for NES); every bible change goes through the independent QA agent.

---

# CP0015 handoff

Private ROM `build/native/Nemesis_Legends_CP0015.nes`. `checkpoint.py test` now includes `tools/test_n3_maps.py`. Chapter 4 maps: `tools/build_n3_assets.py`, banks 28-40, `N3_MAP_BANK`. See `docs/NATIVE_RUNTIME_CP0015.md`.

---

# CP0014 handoff - 512K/256K board, Nemesis 2 maps loadable

Private ROM: `build/native/Nemesis_Legends_CP0014.nes` (786448 bytes; hash in
`manifests/checkpoint.json`). Build: `python tools/checkpoint.py build` (runs
`tools/build_n2_assets.py` and `tools/build_native_assets.py` with `--assets`).
Tests: `python tools/checkpoint.py test` now includes `tools/test_n2_maps.py`.
Bank map and decisions: `docs/NATIVE_RUNTIME_CP0014.md`. Chapter dispatch is
the `chapter` byte (`$7F`); Nemesis 2 descriptors are the Nemesis layout, so
the next step for chapter 2 is gameplay (reports/nemesis2_structure.json has
the stage scripts, bosses, 65 enemy types, weapons and music tables), in a new
STAGECODE-style bank. For Nemesis, stage 5 is next (spec pending from
`final_de_la_fase_5` p01:$6EA8).

---

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
