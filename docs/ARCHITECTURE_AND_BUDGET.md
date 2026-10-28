# Whole-game architecture contract and measured resource boundary

## Target, not a claim of implementation

One NES/Famicom native 6502 runtime, provisionally mapper MMC5. The previously
proposed 1 MiB PRG and 1 MiB CHR are capacity ceilings, not an instruction to pad
ROMs to that size and not proof that the complete game fits. Final board/RAM
configuration and hardware compatibility remain to be established.

No four-ROM launcher, no Z80 game emulation presented as a native port, no
pre-rendered cutscene/frame-stream architecture, and no per-frame captured
register stream used in place of a proper music sequencer.

The destination needs shared resource/event/collision/rendering services with
chapter-specific movement, weapons, enemy behavior, co-op, secrets and final
conditions. Reuse code only after identifying mapper, RAM and timing assumptions.
The original NES games use different mappers (CNROM, VRC4, VRC3/UxROM); their
native executable code cannot simply be concatenated into an MMC5 cartridge.

MMC5 extended attributes change palette/bank selection, not the 2bpp pixel depth
of a NES tile. Many extracted MSX tiles use more than four colors across their
rows. A measured and visually reviewed conversion is still necessary. ExRAM is
memory, not a CPU; it cannot decompress resources autonomously.

## Measurements already available

- `reports/source_audit.json`: input bytes, mapper identity, CHR totals,
  8 KiB block comparisons and source revision matches.
- `reports/nes_raw_tile_duplicates.json`: raw NES CHR duplicate candidates.
  12,288 occurrences reduce to 8,173 exact 16-byte patterns. This does not merge
  palette, collision, orientation or animation identities.
- `reports/nemesis_extraction.json`: 12 source terrain records, 1,169 distinct
  decoded indexed tiles and 167 recorded RLE entrypoints.
- `reports/nemesis2_extraction.json`: 12 map IDs, 4,192 tile columns, 1,695 distinct
  decoded indexed tiles, 48 sprite-state sets and 148 RLE entrypoints.
- `reports/global_dedup.json`: 2,864 locally unique MSX indexed tiles reduce to
  2,821 across the two extracted games. These are **source indexed pixels**, not
  final NES CHR. Zero/one palette indices were not silently conflated.
- `assets/title/title.json`: measured title CHR, nametable, palette and tile count.

RLE entrypoint byte sums may overlap; do not add them as disjoint ROM usage.
Full VRAM images, expanded maps, contact sheets, MP3s and NSF/KSS reference
containers are **not** the proposed cartridge data layout.

## Remaining whole-game measurements

Complete enemy/script/cutscene/music coverage, converted tile palettes and bank
sets, decoder overhead, memory working sets, sprite occupancy, OAM and PPU
transfer budgets, worst-case CPU cycles, IRQ behavior, load times, SRAM/save
usage, full soundtrack conversion size, and final ROM utilization. The current scoped CP0004 measurements below do not establish a numeric
whole-game fit or complete-campaign performance claim.

Hardware reference: https://www.nesdev.org/wiki/MMC5
NSF format reference: https://www.nesdev.org/wiki/NSF

## CP0002 native component measurement

The campaign module and its headless mailbox driver compile to 1,023 CODE bytes.
The module owns 16 state bytes and two zero-page bytes. Its 288 route checks run
in FCEUmm. These are measured component figures, not the whole-game budget.
All four original MSX source trees also reassemble exactly (80 banks, 655,360
bytes); this removes the missing-source gate, not the gameplay-budget gates.

## CP0004 current allocation and measured integration

The active board is NES 2.0 MMC5: 128 KiB PRG, 128 KiB CHR, 8 KiB work RAM.
The current useful generated CHR is 77,824 bytes (53,248 allocation padding),
with 1,312 unique terrain patterns and 43 unique 1 KiB sprite banks. Original
compact metatiles occupy 6,110 useful bytes; the twelve 4 KiB stage descriptors
include intentionally reserved space. They are not twelve completed stages.

The engine retains a 1 KiB source-ID collision ring, 17 maximum 32-byte actor
records, nine player-shot records and ten enemy-shot records. Big Core has a
bounded background update queue. IRQ/DMA/video transfer code is real native
6502, not a register replay. Current linked segments and PRG bank roles are in
`reports/native_runtime_budget.json`.

`reports/cp0004/vblank_budget.json` executes the actual NMI binary with explicit
NTSC/DMA assumptions: worst video-write margin 216 cycles, with an oversized
queue rejected. Separate FCEUmm stress and assisted first-stage runs recorded
zero missed NMIs on their stated inputs. Neither is full-game/physical-hardware
certification. Reserve planning still has to cover unintegrated chapters,
cutscenes, sound arrangements and their worst-case workloads.


## CP0014 decision: board sized for the four chapters

MMC5, PRG-ROM 512 KiB (64 x 8 KiB), CHR-ROM 256 KiB, 8 KiB WRAM. CHR-ROM is
kept because ExRAM per-tile bank selection already gives every chapter its own
tiles without a decompressor in the frame budget. PRG bank roles and the
chapter-2 integration are in `docs/NATIVE_RUNTIME_CP0014.md`; measured use and
the four-game projection are regenerated by `tools/budget.py` into
`docs/BUDGET.md`. The 1 MiB ceilings remain available if the projection
(360 KiB CHR upper bound before deduplication for all four games) is not
reduced enough by global deduplication and palette merging.
