# Asset catalogue: method (Phase 1 of docs/DECISIONS.md)

The catalogue answers one question for every later phase: what exactly does each
source game draw, where, and how do we know. It has one record per game object
(player ship, weapon, power-up, item, enemy, sub-boss, boss, boss part, projectile,
effect, HUD element, char-drawn scenery) and one per screen (title, intro, story,
cutscene, interlude, ending, game over, continue, demo, fonts).

## Two proofs per record

1. **Code.** Every object, frame, sprite pattern number, char code and colour is read
   from the instruction or table that writes it (references as `pNN:$ADDR label` for the
   MSX games, CPU addresses and RAM variables for the NES games). Pictures are rendered
   only after the numbers are known.
2. **Emulator.** Each game is played through every stage, boss, secret route and screen
   (openMSX with C-BIOS for MSX, FCEUmm for NES), with invincibility and stage selection
   done by breakpoints or RAM writes found in the code. Every sprite and every
   char-drawn object on screen is mapped back to a catalogue record; anything unmapped
   is a gap. Result for the four MSX games (CP0017): 0 unmapped drawings. Result for the
   NES games (CP0018): every OAM entry of every captured frame traced to an object slot by
   re-running each game's own sprite builder on the saved RAM (0 unmapped, except 12
   entries in the first four frames of one Salamander FC run, before any RAM history).

## Where things are

- Public (git): `manifests/catalog_msx.json` and `docs/CATALOG_MSX.md` (`tools/catalog_msx.py`),
  `manifests/catalog_nes.json` and `docs/CATALOG_NES.md` (`tools/catalog_nes.py`). They hold names, roles, stages, pattern/char numbers, TMS9918
  colour numbers, code references, proof status and gaps. Large char layouts are reduced
  to their size; no ROM bytes, graphics or audio.
- Private (never in git): one evidence folder per game with `objects.json`,
  `screens.json`, `stages.json`, `coverage.json`, `gaps.json`, `method.md`, the rebuilt
  sprite tables (`sprgen/`), one PNG per object and screen (`png/`), contact sheets, the
  scripts that produced them (`tools/`, re-runnable against the ROM) and the emulator
  captures (`captures/`, several GB, regenerable with those scripts).
- Capture tools in git: `tools/msx_capture.py` (openMSX, headless, VRAM/RAM/screenshot
  dumps at chosen moments, key presses, pokes) and `tools/nes_ppu_state.py` (full PPU
  state of a running NES game from the FCEUmm savestate: nametables, palette RAM, OAM,
  PPU registers and CHR-RAM, which the libretro memory API does not expose).

## Rules the evidence follows

- MSX pattern numbers are 16x16 sprite numbers as the code uses them (multiples of 4);
  colours are TMS9918 numbers 0-15. NES palettes are NES palette indices read from
  palette RAM at the evidence frame.
- Objects that need a second cartridge are catalogued too; TwinBee (Nemesis) and the
  Penguin Adventure ship (Nemesis 2) carry `excluded: owner decision`. R.DRILL (Nemesis 2)
  is a normal special capsule and is not excluded. Operation X and the Crystal Breeze
  (Salamander) and the Space-Fighter Shield (Nemesis 3) are in.
- An object without a drawing (unused type, empty routine, invisible trigger) is allowed
  only when its notes or the gaps list explain it.
- `series_name` is the Gradius-series name when a source gives it; it is a lead for the
  NES comparison of phase 2, never a match by itself.
