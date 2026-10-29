# NEMESIS LEGENDS NES - CONTINUATION (CP0016, 2026-10-28)

Repository: https://github.com/llioncourt/NemesisLegendsNES (`main`).
Last pinned checkpoint: **CP0016**, `build/native/Nemesis_Legends_CP0016.nes`
(sha256 in `manifests/checkpoint.json`). Do not reset or abandon the native
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

## Known gaps found on 2026-10-28

- `tools/extract_nemesis_msx.py` loads only the common sprite block ($86BB):
  the two per-stage blocks of p00:$42AD, the stage-5 block $8FCB and the
  second-cartridge block $9963 are missing (47 of 117 unique sprite patterns).
- MSX bosses drawn with characters, intro/cutscene/ending sprites of Nemesis,
  Nemesis 2 and Salamander, and Nemesis 2 bosses are not extracted yet.
- Salamander (Famicom) and Life Force use CHR-RAM; their graphics come from a
  static decoder pass and may be incomplete.
- The asset bible covers Nemesis vs Gradius (US) only; the final QA round's
  report file is missing from the evidence zip.

## Build and test

```
python tools/checkpoint.py build      # add --assets to regenerate from the originals
python tools/checkpoint.py test
```

Reference captures: openMSX with the free C-BIOS (MSX) and the bundled FCEUmm
core (NES) were used on 2026-10-28 to capture the player ships in game.

## Next concrete action

Phase 1 of `docs/DECISIONS.md`: extract every asset of the four MSX games and the
six NES ROMs (sprites, characters, bosses, cutscenes, fonts, palettes, music),
fix the Nemesis sprite extractor, extend the universal asset manifest, and map
every stage (1.1) with its assets and rules.
