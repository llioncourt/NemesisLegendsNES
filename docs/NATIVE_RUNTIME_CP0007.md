# Nemesis Legends — CP0007 / restored title scene and original Famicom font

**Private playable MMC5 checkpoint; not a completed four-game anthology.**
ROM: `build/native/Nemesis_Legends_CP0007.nes`.
SHA-256: `158675b365d3f2920bd11c89e7a860cc37cca60d6dd221d30f16271c6e66a19e`. Size: 262,160 bytes.

This revision continues CP0006 and changes only title presentation. The
underlying 256x240 scene no longer clears the original menu lines or footer
to solid black. The base art is locally repaired by source-image inpainting,
then quantized/deduplicated into native MMC5 extended-attribute CHR. The
background is visible while the opaque menu rises in eight steps.

## Actual Gradius II font

The private **Gradius II (Japan).nes** image is hash-verified before reading its
128 KiB CHR ROM. The native small font uses original 8x8 pixel shapes: 10 digits
and 26 capital letters, sourced from 4-KiB CHR page 6, tile IDs 128..163.
The source byte span SHA-256 is:
`c5ebbacfc0b66e13f1899a469154801c1b3337f1db42505fe7f69b0836f20441`.

The only transformation is copying the original glyph bitplane into both 2bpp
planes to render white under the existing title palette. The literal glyph
source is not hard-coded in the public repository. It is read from the user's
private owned ROM by `tools/gradius2_font.py`. The in-game menu, sound options,
and bottom `2026 SILICON FORGE` credit use these glyph shapes.

The large cinematic NEMESIS LEGENDS logo and the Konami visual signature remain
the approved illustration, not text fonts. Existing source game mechanics and
all four-part saga acceptance scope are preserved.

## Native implementation changes

- `tools/compile_title_art.py`: no zero-filled menu rows, no cleared footer band;
  patch the credit onto existing scenery instead of painting a black rectangle;
  943 unique scenic tiles, 15,088 data bytes within 16 KiB allocation.
- `tools/build_title_panel.py`: use source-derived Famicom alphabet, same
  panel geometry and eight-row entrance, same root START GAME / OPTIONS.
- `src/native_title.s`: remove the former unconditional writes of 36 blank
  cells while initializing the title; base image is already clean.
- `tools/build_native.py`: verify embedded scenic banks, optionally regenerate
  the art before the source native graphics, then build with original font.
- `tools/test_title_native.py`: unchanged behavior assertions, retargeted to CP0007.

## Verified native behavior

- **56 title/input/negative checks PASS**, including 13 early-confirm gates,
  opaque panel, sound mute/unmute, Start transition, gameover title return,
  reset, long idle and malformed VBlank commands.
- **60 legal title NMI paths PASS** in the project's bounded counter;
  highest last video write at cycle **1408** against the assumed 2273-cycle
  NTSC window. This is not a real-hardware cycle measurement.
- **60 combat assertions and mutated-laser negative control PASS**.
- **10 native controller/gameplay integration checks PASS**.
- **288 campaign-event native component checks PASS** with negative control.
- **Two assisted stage-one runs reach stage two**, one by projectile kill and
  one through source boss timeout; neither proves stage two is complete.
- **42 public/private Python tests pass** with three declared skips.
- **Five scoped NTSC VBlank cases pass**. No PAL/physical hardware verdict.

See `reports/cp0007/title_tests.json`, `reports/cp0007/bank_delta.json`,
`reports/cp0007/title.png`, `reports/cp0007/title_3x.png`.

## Rebuild & distribution

```bash
python tools/checkpoint.py verify
python tools/checkpoint.py build
python tools/checkpoint.py test
# Full art regeneration from approved high-resolution input:
python tools/build_native.py --assets --tools toolchain/linux-x64/bin
```

Do not rename the internal `Nemesis_Legends_CP0001` directory. Linux tool binaries
are not Windows tools; use native cc65/ld65 binaries on Windows. Full art
regeneration needs `requirements-title-art.txt`; normal rebuild uses the
preserved generated asset. Original commercial inputs and extracted graphics
remain private. The public repository receives authored code and documentation;
complete original ROMs are not published. Public game releases remain **IPS-only**.

## Remaining game scope

The native game still ends its implemented campaign coverage after stage 1 and
stage-2 entry. Stage 2 and beyond, Nemesis 2, Salamander, Nemesis 3,
cutscenes, seamless chapter changes, co-op, endings, music conversions,
Konami Code and the final Silicon Forge cheat menu are incomplete.
No title/menu improvements are evidence of progress on those systems.
