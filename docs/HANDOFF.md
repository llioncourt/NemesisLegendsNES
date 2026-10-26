# Current handoff: CP0007 restored scenic title + original Famicom font

Resume `build/native/Nemesis_Legends_CP0007.nes` and matching sources. Use
`docs/NATIVE_RUNTIME_CP0007.md` for hashes and test evidence. This changes only
title scene, Gradius II font and removal of the forced-black patches; native
stage-1 gameplay and campaign acceptance scope are unchanged. The other chapters
and final Silicon Forge cheat menu remain pending. Do not restart or mistake
a title update for a finished anthology. The private source input hashes, not
ROM filenames, define provenance. Public releases remain IPS-only.

---

# Current handoff: CP0006 animated opaque menu

Resume the private build `build/native/Nemesis_Legends_CP0006.nes`.
Read `docs/NATIVE_RUNTIME_CP0006.md` and `reports/cp0006/` first.
This replaces the CP0005 root menu and preserves its approved art/gameplay.
The four-game scope remains unfinished. Continue the actual stages; do not
restart the engine or spend another checkpoint rewriting title documentation.
Current ROM/source hash: `0e892e7bb6e6418241748c13da1fde344d70c99c89cf7d057ad35e457837af2d` (ROM SHA-256).
No GitHub publication was performed for CP0006; the matching source is in this
private package. Production tests run without runtime cheats; explicit assists
in the stage/combat tests are recorded separately.

---

## Earlier handoff, retained as historical context

# Current checkpoint: CP0005 approved title

Resume the CP0005 ROM and sources in this package, not the old CP0004 build.
Read NATIVE_RUNTIME_CP0005.md first. Native title code is src/native_title.s,
PRG bank 9, with actual CHR in banks 19-22 and one cursor bank 92. The art is
assets/title_art/. Up/Down/Select navigate; A/Start confirm; OPTIONS controls
sound. Co-op remains unavailable and is explicitly reported by the menu.
The menu item SILICON FORGE is removed; the 2026 footer credit remains.

The first-stage game content and gameplay core below are preserved. The new
UI tests and regression reports are reports/cp0005/. The old CP0004 report is
historical. This title revision is delivered locally, not yet published to GitHub.

---

# CP0004 handoff - runnable native integration, not the finished anthology

## Resume here, do not restart

The playable build is `build/native/Nemesis_Legends_CP0004.nes`. Its exact hash is
in `build/native/build.json` and `reports/native_runtime_budget.json`.
Start boots stage 1; B fires; A selects the highlighted power-up; Start pauses.
The stage-1 main event route and stage-2 entry are integrated. Stage 2 onward
remains incomplete. Read `docs/NATIVE_RUNTIME_CP0004.md` for behavior, source
addresses, tests and explicit fidelity gaps. The full four-game scope is unchanged.

The former CP0003 runtime was not recovered: only a source prefix survived.
CP0004 preserves the CP0002 campaign/evidence work and reconstructs the native
runtime in ordinary, independently committed modules. Intermediate CP0004A/B/C
archives are historical; use the latest final CP0004 build and its matching tests.
Never reconstruct the game from screenshots or call the old prefix a complete build.

## Source / build files

- `src/native_boot.s`: reset, NMI, IRQ, controller and real donor APU calls.
- `src/native_kernel.s`: title, source column decoder, source collision cache,
  input, fractional ship movement, stage loading and campaign-router integration.
- `src/native_actors.s`: source-derived actor states, waves, cannons, marked
  groups, capsules, collision, field interception and rendering.
- `src/native_projectiles.s`, `src/native_laser.s`: bullets, Options, upgrades,
  aimed fire, source-derived laser growth/collision and bounded sprite output.
- `src/native_boss.s`: first-stage five-part encounter, volcano and Big Core;
  dedicated background updates avoid a giant hardware-sprite boss.
- `src/campaign.s/.inc`: preserved four-game route module (288 component checks).
- `tools/build_native_assets.py`: exact-hash private input extraction, palette
  conversion and global CHR/sprite-bank deduplication. No expanded frame playback.
- `tools/build_native.py`, `cfg/native.cfg`: deterministic ca65/ld65 build.
- `tools/test_native_integration.py`, `test_combat_native.py`, `test_stage_one.py`,
  `test_vblank_budget.py`: scoped tests; assist/negative controls are explicit.

## Priority next work

Finish the complete Nemesis stage-2 event/enemy/boss set before claiming stage 2;
continue the source-derived stages, bonus conditions and final encounter. Preserve
chapter-specific behavior rather than reusing one generic enemy/boss everywhere.
Keep a complete-content ledger for the other three chapters. All resources and
canonical originals are already present; do not ask for them again.

Resolve documented visual/behavioral gaps: second-level missile behavior, source
score/extra-life logic, aim/animation detail, all effects, improved HUD and sprite
visibility under overlapping beams. Continue cutscene/event and music integration
without replacing it with source recordings. Add the final cheat menu after the
complete campaign, as requested.

## Existing verified evidence kept intact

This lean checkpoint keeps the ten selected originals (four MSX and six NES)
with unchanged SHA-256 filenames. The full eight upload ZIPs and the remaining
127 variants stay in the archived CP0004 recovery; they are not duplicated here.
All four pinned Z80 code snapshots and their technical text are retained. The
acquisition manifest describes the pruned code/text subset explicitly. The original
80-bank / 655,360-byte reassembly can be reproduced from these retained sources.
Nemesis 3 remains the canonical 256 KiB image, SHA-1
`7393f677e0fae5fc83071c6b74756117b7d75e2d`, not an enhancement.

The separate previous music package remains source reference: three NES NSF rips, three
MSX KSS rips, 98 MP3s and an 877-character Suno prompt. KSS files are not NSF
conversions. Nemesis 3 audio extraction and the remaining native arrangements are
still pending. Do not relabel these references as the completed converted score.

## Publication and recovery

Publish authored sources, tools, manifests, tests and measured reports; retain
original commercial ROM/ZIP/audio and generated source-asset binaries privately.
The lean private package includes the same runnable ROM and generated assets;
only packaging/support utilities and documentation changed. It must not
be uploaded wholesale into the public repository. Public completed releases use
IPS under the owner's rule. Linux tool binaries are not a Windows build kit.

Read the latest GitHub branch before publishing; use expected source hashes and
verify the downloaded result. Preserve complete checkpoints, not an incomplete
single compressed fragment. Do not replace failed runtime tests with declarations
or paper coverage. No background work is scheduled by this checkpoint.
