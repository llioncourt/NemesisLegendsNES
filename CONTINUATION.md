# NEMESIS LEGENDS NES - CONTINUATION (CP0023, 2026-10-29)

Repository: https://github.com/llioncourt/NemesisLegendsNES (`main`).
Last pinned checkpoint: **CP0023** (Phase 2c, music vs NES; Phase 2 complete). The playable ROM is
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
- **1b, NES catalogue (CP0018, done):** `manifests/catalog_nes.json`, `docs/CATALOG_NES.md`.
  Gradius US/JP 65 objects, Gradius II 115, Life Force US/Rev 1 110, Salamander (Famicom) 137;
  2800 frames, 2674 pixel-verified against the screen; all stages of every game played.
  Gradius II switches CHR in 1 KiB pieces and mixes them on screen: the 33 real on-screen sets
  are in its evidence (the old 8 KiB bank PNGs never show a real set). Life Force Rev 1 changes
  one title byte and a palette refresh only; Gradius JP changes the title and endings only.
  Salamander (Famicom) ships: two layouts only, horizontal (stages 1, 3, 5) and vertical
  (2, 4, 6); player 2 = player 1 tiles with palettes 0 and 1 swapped.
- **1c, music and sound (CP0019, done):** `manifests/catalog_music.json`, `docs/CATALOG_MUSIC.md`.
  Every request of the eight games logged in play: 111 music, 52 jingles, 284 effects (plus
  channel parts, silences and driver commands). Rip titles corrected by role
  (`tools/apply_music_catalogue.py`): 8 of 15 Gradius II titles were on the wrong code, 4 Gradius
  jingles and 5 Salamander (Famicom) cues had the wrong role (its boss theme 0x3A was labelled
  unused), the Nemesis rip listed 6 channel parts as tracks, Nemesis 2's 15 unidentified cues are
  named. New rips: Life Force NSF (40 songs) and Nemesis 3 KSS (83 tracks), both identical to the
  games frame by frame. The Nemesis "stage start" jingles 0x32/0x13 are the volcano eruptions.
- **1.1, stages and rules (CP0020, done):** `manifests/stages_msx.json`, `docs/STAGES_AND_RULES.md`.
  Play order: Nemesis 13 visits (1-2-9-3-10-4-11-5-6-7-12-8, ending), Nemesis 2 32 records (stages
  1-7, 11 boss interiors, return 6-1, stage 0, secret stages 9-11), Salamander 7 (planets 3/4/5 in
  radar order, Operation X only with the crystal), Nemesis 3 19 (stages 1-11, computer scenes,
  return visits, two endings). 2876 spawn entries decoded and checked against emulator runs.
  New facts: R.DRILL appears only in stages 4, 6 and 10 of Nemesis 2; Nemesis 3 has a type-6
  weapon entrance in stage 8 and a big-beam capsule in stage 10 that the catalogue had missed;
  Salamander's second-round flag 0xE305 is never written (its second-round variants never play).

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
- NES: Salamander (Famicom) CHR region_04 is cut at 119 tiles (the game copies 120; tile $D7
  of the stage-6 boss is missing); regions 02/17/19 of it and regions 04/11/17/18/19/21/24 of
  Life Force are never loaded by the games; several Life Force region labels are wrong (09 is
  the stage-3 fire set, 01/20 are the stage-5/3 boss backgrounds, 02 the stage-6 sphere).
  Run-time CHR changes (Salamander FC stage-1 brain fade-in and stage-3 flames, Life Force
  stage-1 boss fade-in and stage-3 animation) are not in any static decode.
- The private evidence folders already hold correct decoders for all of the above.

## Build and test

```
python tools/checkpoint.py build      # add --assets to regenerate from the originals
python tools/checkpoint.py test
```

Reference captures: openMSX with the free C-BIOS (MSX) and the bundled FCEUmm
core (NES) were used on 2026-10-28 to capture the player ships in game.

## Phase 2 progress

- **2a, objects and screens (CP0021, done):** `manifests/asset_choice.json`, `docs/ASSET_CHOICE.md`
  (`tools/asset_choice.py`). 602 MSX objects and screens compared with the four NES catalogues:
  REUSE_NES 103, ADAPT_NES 121, OWNER_SHIP 7, CONVERT_MSX 310, NOT_NEEDED 61.
  Shared assets (options, shots, laser, missile, ripple, capsules, explosions, enemy bullet,
  HUD, font, death explosion, game over and pause screens, Ducker) get one NES version for
  the whole game (table `SHARED` in the tool, reviewed on side-by-side sheets): ship-bound
  assets and player weapons from the Salamander FC / Life Force set (matches the owner's ship,
  only set with vertical-stage drawings, most frames), HUD, font, large explosion, enemy
  bullet and screens from Gradius II. The Gradius II catalogue's "jumper" is the Ducker design.
- **2b, stage graphics (CP0022, done):** `manifests/stage_gfx_choice.json`, `docs/STAGE_GFX_CHOICE.md`
  (`tools/stage_gfx_choice.py`). 74 stage records: the MSX layout stays, the NES stage that
  draws it is chosen. Reuse 5, adapt 57, convert 12 (Nemesis stage 5 bone graveyard,
  Salamander stage 5 Kierke, Nemesis 3 water stage 3, sand stage 7, computer interludes,
  ending, secret room; Nemesis 2 interlude and ending). Shared themes agree across games:
  every fortress uses Gradius II stage 6, Moai Gradius II stage 4, cell stages Salamander FC
  stage 1, Nemesis volcano stages the Gradius II volcano section.
- **2c, music (CP0023, done):** `manifests/music_choice.json`, `docs/MUSIC_CHOICE.md`
  (`tools/music_choice.py`). 101 MSX music/jingle codes compared by notes (each game's own
  driver, transposition-invariant) with 62 NES codes: USE_NES 22 (Nemesis 12 from Gradius,
  boss theme from Gradius II; Salamander 6 from Salamander FC / Gradius II; Nemesis 3 4),
  CONVERT_MSX 76 (all of Nemesis 2's music is its own), 3 silent slots. The Gradius boss
  theme ("Aircraft Carrier") used by Nemesis, Nemesis 3 and Life Force maps to Gradius II
  0x74 everywhere; the Salamander boss theme to Gradius II 0x78. Life Force and Salamander FC
  play bit-identical music.

## Next concrete action

Phase 3 (consistency): every asset that appears in more than one MSX game (enemy, boss,
stage element, music) becomes ONE Legends asset with one visual, keeping each game's own
behaviour. Start from the shared NES choices of phase 2 (same chosen NES object or tune =
same asset), add the MSX-only assets shared between games (identical or near-identical MSX
drawings, e.g. Nemesis 2 data reused by Salamander stage 7), and publish the Legends asset
registry. Then Phase 4 (Gradius II art direction).
