# CP0014 - 512 KiB PRG / 256 KiB CHR layout and Nemesis 2 maps in the ROM (Frente F, structure)

## Board decision (Frente E)

MMC5 with **CHR-ROM**, kept: the engine's ExRAM extended attributes select a
4 KiB CHR bank per tile, which is what makes 1872 chapter-2 tiles coexist with
the Nemesis tiles at zero per-frame cost. CHR-RAM would free PRG for
compressed graphics but would need a decompressor in the frame budget; not
chosen. PRG grows from 128 KiB to **512 KiB** (64 banks of 8 KiB), CHR from
128 KiB to **256 KiB**. The kernel and boot banks move to the last two banks
(62/63), where the MMC5 power-on mapping expects the reset vector.

PRG bank map: 0-9 Nemesis descriptors/maps/actors/boss/title (unchanged), 10
STAGECODE (stage logic), 11-13 reserved (13 is the combat fixture bank), 14-25
the twelve Nemesis 2 map descriptors (8 KiB each), 26-27 the Nemesis 2
metatile banks, 28-61 reserved for Nemesis 2 code, Salamander and Nemesis 3,
62 CODE, 63 BOOT/SOUND/VECTORS. CHR: 0 title tiles, 1 HUD font, 2-18 Nemesis
terrain + sprites + Big Core, 19-22 title art, 24 title panel, 25-38 Nemesis 2.

## Nemesis 2 maps (Frente F)

`tools/build_n2_assets.py` converts the extracted Nemesis 2 maps into the
same descriptor layout the Nemesis engine reads: header (terrain interval,
metatile base, script length, checkpoint, metatile bank), per-third tile maps
with four palettes chosen from real terrain usage, the raw 6-block column
script renumbered to a per-map metatile list (compact 8-byte blocks expanded),
sprite bank ids for the map's 64 hardware frames. `DrawColumn` now takes the
metatile bank from the descriptor instead of a constant, so the Nemesis 2
column builder is the existing one: both games use six 4x4 pieces per
four-column group.

`LoadStage` dispatches on the new `chapter` byte (1 Nemesis, 2 Nemesis 2):
chapter 2 maps `N2_MAP_BANK + stage - 1` at `$8000`. Nemesis-only logic
(StageEvents, stage ticks, targets, waves) is gated to chapter 1. The cheat
menu's GAME item now starts Nemesis 2 maps 1..12 (map ids 0..11; campaign
order is in reports/nemesis2_structure.json). `tools/test_n2_maps.py` loads
all twelve through the menu, scrolls 600 frames each with zero missed NMIs
and captures reports/cp0014/n2_map_NN.png.

What this is not: no Nemesis 2 enemies, bosses, weapons, capsules, interior,
secret entrances, scroll stops, endings or music. Terrain collision uses the
Nemesis rule (non-zero character below $77 is solid) provisionally. Sprite
frames are the raw hardware frames with the Nemesis sprite palettes.

## Fixtures

`tools/test_combat_native.py` derives the fixture bank, trampoline bank and
reset vector from the ROM header instead of assuming 128 KiB.
