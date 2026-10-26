# CP0008 — MSX Nemesis stage 2: source-derived native event integration

Status: **WIP, tested partial gameplay, not a complete first game or anthology.**
This follows CP0007. The approved title/art/font, first-stage gameplay and
all source inputs remain preserved. Only authored 6502 source, tests and
checkpoints are changed. The original encrypted/commercial data is kept
private; no Z80 interpreter or captured footage executes in the NES cartridge.

## Source references (verified with the pinned MSX disassembly)

| Original MSX source | Native behavior in CP0008 |
| --- | --- |
| p03:$AB86-$ABD3 | Precisely 0x384=900 frames of rock rain. 20-frame standard-difficulty spawn cadence, 16 indexed coordinate pairs. Original Z80-R is approximated by the existing 6502 RNG; bit-exact PRNG parity not claimed. |
| p03:$ABF3-$AC81 | Six world distances $0144, $014C, $0170, $0178, $0180 and $0188. Five rocks at source Y=$8C,$6C,$4C,$2C,$0C, one per logical frame. |
| p03:$ACAF-$AD1D | Type-8 rock initialization, three 10-frame growth steps (source frames $C0/$C4/$C8), collision enable after maturation. No type-8 projectile fire on the first loop, as in the original. |
| p03:$B091-$B142 | Hidden target at $0190, Y=$88, 8-pixel movement left per new world column. Collision within source $10 x/$10 tolerance freezes for 64 frames and enters source bonus route 9. |
| p01:$6D66-$6DA5 | Native Big Core final encounter and stage-3 transition after the rain. The existing first-stage core sprite and AI are reused because the source boss type matches. |
| p01:$6F97-$6FB2 | Bonus stages 9–12 return to their source next stage using `Flow_Event(EVENT_CLEAR)`; transitions use the source compact descriptor event distance (bytes 4–5), **not** the beginning of the terrain segment. |

Source wall positions originate from the exact ROM. Every spawn is subject to
the **existing 12-record actor pool**, so spawning is not guaranteed without
player combat. The first attempt to automatically despawn type-2 enemies when
they reached the right edge broke stage-one capsule regression. That change
was **reverted**. The normal stage-two test shoots to clear slots through real
combat rather than bypassing actor allocation rules. A no-fire run can have
suppressed rock spawns when all slots are occupied; fidelity to MSX saturation
under every input sequence still needs direct source-frame comparison.

The bonus-stage terrain and static cannon content are sourced from the original
stage descriptor, not a fake 64-frame cutscene. The 64-frame freeze applies
only to target contact in the preceding stage. A playable bonus *entry and exit*
is demonstrated; comprehensive bonus enemy/secret fidelity is not approved.

## Native implementation

- `src/native_stage2.s` is the dedicated phase/actor/bonus module, bank P7
  at $A000. It references the common campaign router instead of embedding a
  second fake stage list. No duplicated terrain or expanded frame streams.
- `src/native_actors.s` adds dispatch for original type-8 rocks. Source type-2
  rules and stage-one capsule behavior remain intact.
- `src/native_kernel.s` initializes the stage-specific actor state after
  loading each stage, drives events each logical frame, and draws the source
  target without replacing gameplay with a cutscene.
- `src/native_boss.s` reuses the original type-1 Big Core handling for stage2
  phases5–8, while stage1's other original encounters remain stage1-only.
- Runtime state is 16 bytes in BSS, following `Flow_State` at $0500; use the
  linker map to confirm $0510. State is cleared on native stage loads.

## Actual tests, not simulated playback

`python tools/test_stage_two.py --core toolchain/linux-x64/bin/fceumm_libretro.so`
executes two controller-driven runs. Both start a new game, shoot through the
real stage-one boss, and proceed without writes to stage ID, scroll position,
phase, enemy records, health, target coordinates, countdown or campaign router.
**The only injected QA condition is invulnerability**, `$0053=1`, labelled in
every test report. This is an assisted route, not a human playthrough.

### Normal route (current compiled ROM)

- Stage two begins on test tick 5,197; the 900-frame rain runs from 8,650 to
  9,550. Big Core phase begins at 9,679; stage 3 is entered at 10,651.
- Six 5-rock walls were triggered and 74 rock creation calls made; 40 calls
  succeeded with actual player shooting. 34 calls encountered full source
  allocation; the engine does not invent extra slots. No missed NMI across the
  assisted route. Boss attack/timeout follows existing source-derived logic.

### Secret route

- Target is physically touched; 64-frame freeze; actual stage-9 load at tick
  8,370. Stage-9 terrain is traversed until the original event marker is met;
  stage3 is entered at tick 10,855. No direct stage injection; 0 missed NMIs.
- Holding vertical controls rather than shooting can saturate all slots, so
  this route is *not* used to claim every optional rock was spawned.

The regression suite separately verifies the previously working stage-one boss
kill and 720-frame timeout, stage-one capsule collection, 10 native gameplay
checks, 60 combat assertions with a negative control, 56 title checks, 288
campaign-router checks, and bounded VBlank transfers. Static Python source
and package verification are separate from these native execution tests.

Screenshots, JSON reports and logs are in `reports/cp0008/`. A screenshot or
passing event assertion does not establish visual parity with an MSX source
frame; stage-two sprite palette fidelity remains unresolved.

## Measured budget from the current ca65/ld65 map

- Cartridge: **262,160 bytes**, iNES mapper 5; PRG-ROM 128 KiB, CHR-ROM 128 KiB.
- New stage2 ACTORS segment: `$02DE` bytes (734 bytes); the total ACTORS
  segment is `$0D80` bytes in an 8-KiB bank, 4,736 bytes available.
- Combined CODE/RODATA in common $C000 bank uses `$19D4` of 8 KiB, leaving
  `$062C` bytes (~1,580). The stage2 module deliberately stays out of CODE.
- BSS 32 bytes total ($0500-$051F), including 16 bytes campaign + 16 stage2;
  zero-page used by campaign remains 2 bytes ($80-$81).
- Screen transfer uses the existing verified column and boss queues; native
  CP0008 normal/bonus assisted paths recorded zero missed NMI. This does not
  establish all possible boss/shot combinations or PAL/hardware timing.

These are **current** ROM figures, not a complete four-game capacity proof.
Much more source content remains to be converted and integrated. Do not expand
PRG/CHR by filling unused banks with duplicate assets; revisit mapper budget
only after a measured whole-game inventory.

## Limitations and next functional gates

This checkpoint does NOT implement or approve complete Nemesis: stages 3–8,
optional stages10–12, later bosses, complete source cutscenes, game endings,
source-exact palettes/animations and musical score remain incomplete.
The other three MSX games are retained as canonical private inputs and parsed
source evidence, but NOT playable integrated chapters. Completion requires a
real beginning-to-end run of the four chapters and all mandatory secret route
checks, not merely passing this file's tests.

Priority: original stage-three movement, enemy/boss scripts, stage3 target and
bonus10 route, then stages4–8, the other three chapters, native soundtrack,
cutscenes and final Silicon Forge Konami Code. No restart or generic tech demo.
