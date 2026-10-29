# Owner decisions (2026-10-28) - the scope every later session follows

These decisions were made by the project owner in the session of 2026-10-28.
They replace any earlier ordering in CONTINUATION/HANDOFF where they conflict.
Do not reopen them; ask the owner only about what is not covered here.

## Goal

One native NES/Famicom MMC5 ROM that plays as a single game: Nemesis ->
Nemesis 2 -> Salamander -> Nemesis 3 in chronological order, no game-select
menu. The coverage reference is the complete content of the four MSX games.

## Execution order (owner's phases)

1. **Extraction.** Extract every asset of every source ROM, MSX and NES.
   - **1.1** Map every stage of the four MSX games and where each stage's assets
     are. Stage logic may already be converted to the NES at this point, even
     without final assets. The rules of each game that are not stages also go
     here: each game's weapon system, Salamander's vertical stages and the
     secrets.
2. **Comparison and choice.** Map everything the MSX games have. Search all
   the NES games (Gradius JP/US, Gradius II Famicom, Life Force US/Rev 1,
   Salamander Famicom) for the same assets: enemy ships, bosses and stage
   graphics. If an asset exists on the NES, use it whatever game it comes
   from; if it exists in more than one NES game, use the most detailed one.
   Compare NES vs MSX first, then NES vs NES.
3. **Consistency.** An enemy, sub-boss, boss, stage element, music or any other
   asset that appears in more than one place (in any of the MSX games) is the
   same asset everywhere in Legends. The visual is shared; the behaviour stays
   the original behaviour of the game it comes from.
4. **Art direction.** The quality of the found assets sets the direction. The
   Gradius II Famicom assets are the most beautiful and are the art direction.
   Everything that does not come from Gradius II is standardised to the same
   graphic quality (palette, shading, detail), including the player ships.
5. **Missing assets.** Every MSX asset with no NES equivalent is converted and
   added, so the catalogue has no gaps, keeping the direction and quality of
   the existing assets.
6. **Graphics QA** for consistency.
   - Between 6 and 7: measure the cartridge space. Reuse every repeated asset
     once (global deduplication across the four games) and compress with RLE.
7. **Rebuild the stages** with the assets.
8. **Chronological order** of the stages with the rebuilt cutscenes.
9. **QoL and the Silicon Forge cheat menu** (Konami Code): invincibility,
   lives, stage select, theater mode for the cutscenes, sound mode and any other
   option that fits the game.
10. **Deliver the playable ROM.**

## Music

If the same music exists in a NES game, use the NES version. If not, convert
the MSX music in two arrangements: one for the plain APU and one using the MMC5
channels. The APU version is a real arrangement ("remix") for the base channels,
not a stripped MMC5 version. Music follows the same phases as the graphics
(extract, compare, choose, consistency).

## Player ships

- Player 1 always uses the Salamander (Famicom) player 1 ship, in every chapter.
  Reason: they are the only ships that already have the sprites for vertical
  stages.
- The Nemesis, Nemesis 2 and Nemesis 3 chapters are single player.
- The Salamander chapters enable the second player, with the Salamander
  (Famicom) player 2 ship.
- Both ships are recoloured to the Gradius II palette with the rest.

## Secrets that needed a second cartridge on MSX

- TwinBee (Nemesis) and Penguin Adventure / Pentarou (Nemesis 2): not used.
- Operation X (Salamander): Nemesis 2 is in the same cartridge, so the
  second-cartridge condition is always true. The player must still find the
  Crystal Breeze in one of the three middle planets to unlock Operation X and the
  good ending, as in the original.
- Nemesis 3 good ending: as in the original, it depends on the secret
  Space-Fighter Shield in stage 10.

## Delivery rhythm

- Work continues checkpoint after checkpoint without stopping. Each checkpoint
  plan is posted to the owner and executed without waiting for approval. Stop
  only when the owner says so or for a decision only the owner can make.
- Every checkpoint delivers a playable ROM, a commit on `main` (code only,
  nothing derived from the ROMs), a folder per checkpoint in the owner's Drive
  (`Claude Files/Nemesis Legends NES Port/CPxxxx/`, text files) and the ROM and
  private package sent in the chat.
- No long played QA batteries; automated emulator tests only.
- Public releases are IPS patches only.
