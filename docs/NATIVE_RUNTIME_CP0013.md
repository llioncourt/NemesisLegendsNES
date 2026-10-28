# CP0013 - Silicon Forge cheat menu, universal asset manifest, four-game inventories

## Cheat menu (Frente G)

Konami Code (UP UP DOWN DOWN LEFT RIGHT LEFT RIGHT B A) on the title or while
paused opens the menu (mode 5). It is drawn with the HUD font through a new
second text-row mailbox (`HUD2`, `hud2_addr`, `hud2_pending`, `hud2_exattr`)
that the NMI uploads one row per frame, with the ExRAM font attribute for the
row. Code lives in `src/native_cheat.s`: Konami detection, apply/exit and the
debug row in the actors bank (mapped during the main loop), the menu itself in
the title bank 9, which is mapped at `$8000` while the menu is open.

Items: INVINCIBLE (QA flag bit 0), LIVES normal/infinite, GAME (only Nemesis
is startable; the other three show WIP and stay in the menu), STAGE 1..12,
CHECKPOINT start/midpoint (the descriptor checkpoint LoadStage itself uses),
SHIP SPEED 0..7, MISSILE, DOUBLE, LASER, OPTIONS 0..2, SHIELD, PACE 30/40/60,
SOUND TEST (A plays the command), DEBUG HUD, WARP TO END (scroll limit minus
`$30` columns), RESTART STAGE, START GAME / RESUME.

Every action goes through the real loaders: `NewGame` (factored out of the
title path), `LoadStage` (stage select, checkpoint, warp, restart, with the
campaign module's `F_STAGE` kept in step) and `RestoreGameScreen` (the
LoadStage screen sequence without any state reset, for a plain resume that
keeps world, actors and camera). No parallel loading path exists. The menu is
refused during the Big Core screen (phases 4..8), where the nametable is not the
stage window.

Debug row (row 26): `W:` world, `P:` phase, `M:` missed NMIs, `A:` live actor
records, `S:` sprites used, `F:` frame counter, refreshed every eighth frame.

`tools/test_cheat_menu.py` drives all of it from the controller with no RAM
writes: 15 checks (reports/cp0013/cheat_menu_tests.json).

## Inventories and generators (Frentes B, C, D, E)

| tool | output | what it is |
|---|---|---|
| `tools/extract_salamander_msx.py` | assets/msx/salamander/, reports/salamander_extraction.json, reports/salamander_structure.json | 7 maps (3 vertical) + 3 detours, 1534 unique tiles, 8 boss tile sets, 230 RLE streams, bosses/music/addresses |
| `tools/extract_nemesis3_msx.py` | assets/msx/nemesis3/, reports/nemesis3_extraction.json, reports/nemesis3_structure.json | see the report for counts |
| `tools/extract_nes_graphics.py` | assets/nes/, reports/nes_extraction.json | CHR banks of the six NES references, tile dictionary, CHR-RAM regions with confidence |
| `tools/nemesis_structure.py` | reports/nemesis_structure.json | stage order, records, checkpoints, cannons, wave bits, end routines, music table, boss kinds, targets, object types |
| `tools/asset_manifest.py` | manifests/asset_manifest.json, manifests/asset_coverage.json, docs/ASSET_COVERAGE.md | one record per resource, six independent states, reuse classes |
| `tools/compare_msx_nes.py` | reports/msx_nes_matrix.json, docs/MSX_NES_MATRIX.md | silhouette matches MSX tiles/sprites vs NES tiles (candidates, not decisions) |
| `tools/storyboard.py` | manifests/storyboard.json, docs/STORYBOARD.md | the continuous campaign sequence with per-sequence state |
| `tools/budget.py` | reports/budget.json, docs/BUDGET.md | measured ROM/RAM use and four-game projection |

All generated documents say so in their first line and are regenerated from
the structured sources; none of them claims completion.
