# Nemesis Legends NES - state of the machine (2026-10-29 10:25 BRT)

Saved because the account credits ran out. Everything below lets a new session continue
without this container.

## Where each thing lives

- Git `llioncourt/NemesisLegendsNES`, branch `main`, last commit `02f9fe9` (CP0026): all code,
  public catalogues and docs. Read `docs/DECISIONS.md` (owner scope), then `CONTINUATION.md`.
- Private project package (sent in chat): `Nemesis_Legends_CP0026_Private_Recovery.zip`
  (project folder `Nemesis_Legends_CP0001`: ROMs in private_sources, assets, build, rips).
  Playable ROM: `build/native/Nemesis_Legends_CP0016.nes` (unchanged since CP0016).
- Private evidence package (sent in chat now): `Nemesis_Legends_ESTADO_evidencias.zip` =
  `/home/claude/work/evidence/` without the regenerable emulator captures (`captures/`), the
  WAV renders (`music_arrange/wav/`, MP3 copies were sent in CP0026) and the music traces.
  Unzip it to `/home/claude/work/evidence/` (the briefs use that absolute path).

## Phase status (owner's ten phases)

1. Extraction: DONE (CP0017-CP0020): catalogues of every object, screen, music and stage.
2. Comparison and choice: DONE (CP0021-CP0023): asset_choice, stage_gfx_choice, music_choice.
3. Consistency: DONE (CP0024): manifests/legends_assets.json (474 assets).
4. Art direction: DONE (CP0025): docs/ART_DIRECTION.md, recolour plan, conversion sample.
5. Missing assets, IN PROGRESS:
   - Music: DONE (CP0026): 70 MSX-only tunes arranged (APU and MMC5); data in
     `evidence/music_arrange/*.json`, format `docs/MUSIC_FORMAT.md`.
   - Art lot "nes" (84 NES visuals, recolour + adapt): DONE, `evidence/art_out/nes/` (78 done, 6 partial).
   - Art lot "n3" (102 Nemesis 3 assets): DONE, `evidence/art_out/n3/`.
   - Art lot "n1n2" (83 Nemesis + Nemesis 2 assets): STOPPED mid-way, partial output in
     `evidence/art_out/n1n2/` (85 entries incl. tools); resume with BRIEF_ART_PRODUCTION.md,
     key "n1n2" of `evidence/art_tasks.json`, skipping assets whose folder has asset.json+tiles.chr.
   - Art lot "sal" (71 Salamander assets): STOPPED mid-way, partial output in
     `evidence/art_out/sal/` (78 entries incl. tools); resume the same way, key "sal".
   - MSX-only stage tile sets (11) and the ADAPT stage sets (29): not started (phase 5/7).
6-10: not started.

## Owner's last requests

- "faz uma wip com os graficos ja alterados": a WIP ROM of the playable Nemesis stages 1-4 with
  the new sprites (Salamander FC ship, new weapons, capsules, explosions, enemies), BG unchanged.
  STOPPED mid-way. Brief: `evidence/BRIEF_WIP_ROM.md`. Partial code: `evidence/wip/wip_inprogress.patch`
  (new tools/wip_sprites.py, mapping and sheet building started; no ROM yet). Restart: copy the
  project to `/home/claude/work/wip_build`, apply the patch, continue the brief.
- Pending owner decision: remove the 334 test screenshots (reports/cp0012-cp0016/*.png) from the
  public repo (they show converted Konami graphics) and whether to rewrite git history. Nothing
  was removed.
- Owner has not answered whether the art direction of the CP0025 sample is approved; "continue"
  was taken as go-ahead.

## Briefs (in evidence/, reusable)

BRIEF_COMMON.md, BRIEF_NES.md, BRIEF_STAGES.md, BRIEF_COMPARE.md, BRIEF_STAGE_GFX.md,
BRIEF_MUSIC_MATCH.md, BRIEF_CONSISTENCY.md, BRIEF_ART.md, BRIEF_CONVERT_SAMPLE.md,
BRIEF_MUSIC_ARRANGE.md, BRIEF_ART_PRODUCTION.md, BRIEF_WIP_ROM.md.

## Machine setup needed by the tools

openMSX (apt, C-BIOS machines), xvfb-run, ffmpeg, Python 3 with numpy and Pillow, the project's
bundled ca65/ld65/FCEUmm in `toolchain/linux-x64/bin/`. Drive folder of the project:
`Claude Files/Nemesis Legends NES Port/` (id 1Ogrgg3dp1jkxwN9cxuKWHqpUnoh6dbU1), one text folder per checkpoint.
