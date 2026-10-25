# CP0004 - native gameplay integration

## What this build actually does

`build/native/Nemesis_Legends_CP0004.nes` is a native NES 2.0 / MMC5 cartridge.
It boots the custom title, accepts controller input, runs Nemesis stage 1's
main route, reaches its five-part encounter, volcanic sequence and Big Core,
and loads stage 2 after destruction or the source-defined boss timeout.
There is no Z80 interpreter, original-game launcher, captured-frame player or
streamed register log in this cartridge. This is an incomplete production port,
not a completed four-game anthology.

Controls: Start begins/pauses; D-pad flies; B fires (hold for repeat); A activates
the currently selected power-up. Normal boot has no invulnerability or supplied
power-ups. QA assistance is an explicit RAM fixture used only by named tests.
The requested final Konami Code/menu has not been implemented.

## Source evidence used

Primary reference: the hash-verified MSX Nemesis image selected in
`manifests/selected_sources.json` and the pinned `antxiko/Nemesis-disassembly`
revision recorded in `manifests/upstream_repositories.json`.

- p00:4499 / p11:97DE: compact terrain intervals and six-metatile scripts.
- p00:4212: death checkpoints; p00:42AD: stage sprite loading.
- p02:9262: cannon placement; p03:A3A6/A5AF: source wave tables.
- p01:6CCE-6D64: first-stage encounter and event sequence.
- p01:713C/718D: volcano particles and their source velocities.
- p01:7E03 and neighboring routines: Big Core movement, openings and fire.
- p01:7EE6/7F3E/7F62: Big Core body and face character maps.
- p02:9B0D/9B4D: fractional ship movement, base 1.5 pixels per frame.
- p02:9C41-9C8F: Options' position queues; only the animation at 9C90
  has a two-frame cadence. Stationary/opposing directions do not move queues.
- p02:9D8F/9E66-9EDF: laser growth, detachment and 32-pixel detached movement.
- p01:72AE-72C2: laser contact kills vulnerable actors directly, rather than
  applying the ordinary shot's per-hit HP decrement.
- p01:7420-745D: force-field interception of the twelve ordinary enemy slots.
- p01:758E-75B7: blue capsule clears ordinary enemies, not the separate bullet
  pool or Big Core. Red capsules advance the selection and award five units.
- p02:99EB/99F7/9A0F: ship/force-field sprites, composited with source priority.
  Source field strength is ten; its weak visual state is the final remaining hit.

The NES Gradius donor sound engine runs at its original addresses, EC1E/ED02,
with real APU writes. This is limited native donor audio integration, not evidence
that all MSX scores or chapter-specific SFX have been converted.

## Native representation

The renderer reads the original compact column scripts and metatiles. Original
source character IDs remain in a 32-column collision cache, independently of
NES palette reduction. Converted graphics are deduplicated globally. Per-stage
sprite sheets are deduplicated in 1 KiB units. Big Core uses background tiles
and a bounded update queue rather than exhausting eight sprites per scanline.
The custom title is rendered by the real cartridge, not inserted into captures.

Current cartridge: 128 KiB PRG + 128 KiB CHR + 16-byte header. Useful generated
CHR is 77,824 bytes; remaining CHR is allocation padding. The 12 terrain records
are assets, not 12 completed stages. `reports/native_runtime_budget.json` records
bank allocation, linked segments and measured video-transfer limits.

## Reproduced tests and boundaries

- 60 assertions execute the **actual production 6502 combat routines** in FCEUmm.
  Test fixtures occupy unused PRG bank 13. A modified production laser growth
  instruction fails eight assertions; the oracle is not modified.
- 10 controller-level checks cover boot, input, pause/resume, firing, actual
  capsule acquisition, upgrading, ordinary death/respawn and weapon stress.
  The 2,000-frame dense-weapon run records zero missed NMIs. Assistance is
  explicitly labeled; this is not an unassisted first-stage clear.
- Two controller-driven first-stage runs reach stage 2: destruction through
  actual projectile damage and the source's 720-frame active-fight timeout.
  Both use invulnerability, not injected boss HP/timers/distances or stage
  completion. A separate labeled carry-over fixture checks retained equipment.
- Five bounded instruction-timing cases inspect the actual NMI binary.
  The worst measured video-write margin is 216 NTSC CPU cycles. A deliberately
  oversized boss queue fails. Assumptions (including DMA and no DMC during
  video transfer) are explicit in `tools/test_vblank_budget.py`.
- The separate campaign router still passes its 288 route/event tests.
- The 13 public and 22 private pre-existing evidence tests remain green.

These do not prove physical hardware equivalence, PAL timing, every possible
combat state, unassisted difficulty balance, or completion of later stages.

## Explicit remaining gaps

Stage 2 can be entered but its complete events/boss, other Nemesis stages and
bonus routes are not integrated. The other three chapters have not been made
playable. Unsupported actor types are counted, not silently treated as correct.
Some enemy aim/animation details, missile level-two behavior, score/life-award
logic, destruction presentation and source-specific effects still need work.
The HUD is functional but not the final Silicon Forge presentation.

MSX-to-NES palettes are lossy and require further visual review. Hardware sprite
visibility limits remain, especially with overlapping long lasers; logical
collisions do not disappear merely because an OAM entry is invisible.
All cutscenes, chapter bridges, co-op, endings, the final cheat menu and remaining
music conversions are pending. Never mark the anthology complete from these tests.
