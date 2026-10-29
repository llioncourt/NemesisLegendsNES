# NEMESIS LEGENDS NES - CONTINUATION (CP0017, 2026-10-29)

Repository: https://github.com/llioncourt/NemesisLegendsNES (`main`).
Last pinned checkpoint: **CP0017** (Phase 1a, MSX asset catalogue). The playable ROM is
still `build/native/Nemesis_Legends_CP0016.nes` (sha256 in `manifests/checkpoint.json`). Do not reset or abandon the native
motor. Public distribution: IPS only; source ROMs and derived graphics/audio
stay private.

**Read `docs/DECISIONS.md` first.** It holds the owner's scope of 2026-10-28
(ten phases, asset rules, art direction, player ships, music, secrets, delivery
rhythm) and overrides older orderings in this file and in HANDOFF.

## Actual coverage, not release claims

1. **Nemesis (MSX):** native stages 1-4 with the normal and bonus routes
   (bonus 9, 10, 11), Big Cores, cross-stage targets; stage 4 reaches stage 5.
   Stage 5 onward: map descriptors only. Every sprite and tile is still an MSX
   conversion.
2. **Nemesis 2 (MSX):** twelve maps loadable and scrollable, chained through
   the campaign module with scene placeholders. No enemies, bosses, weapons,
   events, endings or music.
3. **Salamander (MSX):** campaign router only; no maps in the ROM.
4. **Nemesis 3 (MSX):** eleven maps loadable and scrollable, chained with scene
   placeholders. No enemies, bosses, interludes, endings or music.

Cheat menu (Konami Code), 30/40/60 logical-FPS pacing, 512 KiB PRG / 256 KiB
CHR MMC5 board. Free space in the CP0016 ROM: 24 PRG banks (192 KiB), 46 KiB of
CHR; the kernel bank has 733 bytes left, so new shared code goes to banked
segments.

## Phase 1 progress

- **1a, MSX catalogue (CP0017, done):** `manifests/catalog_msx.json`, `docs/CATALOG_MSX.md`,
  method in `docs/CATALOG_METHOD.md`. Nemesis 75 objects / 18 screens, Nemesis 2 122 / 31,
  Salamander 134 / 30, Nemesis 3 180 / 22; 3537 frames; every stage, boss, secret route and
  screen played in openMSX with 0 unmapped drawings. Gaps (86, mostly unused types and
  frames never caught on screen) are listed per game.
- **1b, NES catalogue (CP0018, in progress):** Gradius US/JP, Gradius II, Life Force US/Rev 1,
  Salamander (Famicom), with `tools/nes_ppu_state.py` for CHR-RAM games.
- **1c, music (CP0019, next):** the sound-request routine logged in a full emulator run gives
  the exact music of every stage, boss and ending (method tested on Nemesis).
- **1.1, stage map and rules (CP0020).**

## Extractor findings to apply when the stage graphics are rebuilt (phase 7)

- Nemesis: the star patch also overwrites row 0 of char F8 (first normal-shot char; real
  row 0 is 0xE7); the game blinks only F6/F7 (p00:475B). Fixing it changes the current
  ROM, so it waits. `source_vram.bin` lacks the stage font in third 2 (p00:58BA).
- Nemesis 2: map ids are the in-game stage numbers (map_00 final fortress, map_08 boss
  interior, maps 09-11 secret stages; the return trip replays 6 to 1). Stage sprite tables
  assume empty VRAM, but the game keeps the previous stage's patterns in slots a stage
  does not write. Runtime graphics (boss chars/sprites, explosion set, REFLEX RING, special
  capsule char E9, meter labels, animated chars) are not in `source_vram.bin`.
- Salamander: the open claim about patterns 0x40-0x6F is wrong (0x06 draws 0xE0-0xEC from
  the stage-4 set; 0x30/0x38 belong to stage 7; 0x40 is char-drawn). Patterns written while
  playing (ship postures 0x00-0x0F by p01:6060, ship explosion 0x40-0x4F, joined ship,
  interlude ship) are missing from the stage tables.
- Nemesis 3: boss 0x0D loads no set (p00:5101 returns first); stage 10 brings boss 0x11
  after 0x0F (p01:61B5); missing from the static extractor: boss drawings p06:82B9,
  enemy/piece char drawings p08:BD4C/B834, pieces with their own drawing code (stage-1
  sun p03:A36B, types 0x0D/0x1E/0x2E/0x2F/0x30), boss-explosion set p20:6BBC with
  p03:A70B, boss 0x0B alternate set p20:6B83, score digits chars 0x40-0x49 (p00:4A0F).
- The private evidence folders already hold correct decoders for all of the above.

## Build and test

```
python tools/checkpoint.py build      # add --assets to regenerate from the originals
python tools/checkpoint.py test
```

Reference captures: openMSX with the free C-BIOS (MSX) and the bundled FCEUmm
core (NES) were used on 2026-10-28 to capture the player ships in game.

## Next concrete action

Finish Phase 1: CP0018 (NES catalogue), CP0019 (music and sound of all ten ROMs),
CP0020 (1.1: every stage of the four MSX games with its assets, events, routes, weapon
systems, Salamander's vertical stages and the secrets). Then Phase 2 (NES vs MSX match).
