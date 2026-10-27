# NEMESIS LEGENDS NES — CONTINUATION (CP0014, 2026-10-27)

Repository: https://github.com/llioncourt/NemesisLegendsNES
GitHub last confirmed baseline before this execution: `47b4b3bcf6708fd7c42032472e53203baec19e9a` (CP0011 plus the lean-tool sync).
Current tested private ROM: `build/native/Nemesis_Legends_CP0014.nes`; consult `manifests/checkpoint.json` for exact SHA-256. Update this document's remote commit only after server verification. Do not reset or abandon the existing native motor. Public distribution: IPS only; the source ROMs and derived commercial CHR/audio stay private.

## Actual coverage, not release claims

1. **Nemesis / Gradius MSX**: partial native stages 1 and 2 (rock walls, 900-frame rain, Big Core, bonus9), stage3's two source type-1 Big Core encounters at world `$0060` and `$01AF` and bonus10/normal branches to stage4. Cross-stage MSX target types 2/3/4 persist from stage1 into stage4; three distinct touches activate bonus11 and route to stage5. **CP0012:** stage4's normal route now runs its complete source end sequence (p01:$6E15): ceiling eruption at `$0128`, five-piece tower at `$0171`, "boss 5" eight-piece spawner at the `$019F` scroll limit, scroll release to `$01C0`, type-1 Big Core, stage5. Source enemy type `$0A` and a faithful type 6 hopper were ported; both previously parked on screen and could block the Big Core wait in stages 1, 3 and 4. Stage5 onward contains resource descriptors, not playable faithful level logic. Full Nemesis MSX is **NOT complete**. The screenshot criticism about sparse art and HUD is not resolved.
2. **Nemesis 2 MSX**: **CP0014:** all twelve maps converted to native descriptors and loadable/scrollable in the ROM (banks 14-27, CHR 25-38) through the cheat menu; structure inventory (`reports/nemesis2_structure.json`) with stage scripts, bosses, enemy types, weapons, cutscenes and music. No native enemies, bosses, weapon system, interior/secret events, endings or music yet.
3. **Salamander MSX**: campaign router and secret Operation X requirements only; no full native campaign, planet missions, co-op, audiovisual equivalence or validated ending.
4. **Nemesis 3 MSX**: original validated/decompiled, campaign router metadata, but no native levels, chronology/cutscenes or ending integration.

## Working native systems

**CP0013:** Silicon Forge cheat menu (Konami Code; real loaders; debug row), banked STAGECODE bank for stage logic, extractors for all four MSX games and six NES references, universal asset manifest (`manifests/asset_manifest.json`, 1727 records), MSX x NES matrix, master storyboard (`manifests/storyboard.json`), memory budget. The brief's Frentes B-E and G have their first measured deliverables; F (whole-campaign ROM structure) and H (stages 5-8, chapters 2-4) are next.

MMC5 6502 title/menu (not user-approved art), native 8x8 source columns, stage-specific enemy/weapon/laser/boss support, cross-stage target memory, bonus router, 30/40/60 logical-FPS option with NTSC video and APU at 60Hz, source driver references; no complete native OST. Compact source tile data and decomp resources remain in their original private source directory, not inflated per-frame playback.

## Critical missing systems and visual quality

- Stage5 (`final_de_la_fase_5` p01:$6EA8: two bank-3 encounters, limit `$1FF`), stages 6-8 scripted combat, bonus12 and the Nemesis ending. The normal route must not bypass unfinished bosses. Enemy types `$0B`, `$0C`, `$0D`, `$0E` and later source types are still unported (type `$0C` appears in stage-6 opening waves).
- Full original enemy actor types/patterns, sprites, scenic layers and collision parity. The CP0008 user's screenshot showed black void, repeated sprites and poor HUD; **these visuals are still NOT fixed**.
- All Nemesis 2 / Salamander / Nemesis 3 mechanics, cutscenes and endings, native music conversion, global deduplication and total CPU/ROM budget certification, full stage playthrough without QA help, Konami Code + Silicon Forge cheat menu.
- The normal-to-next-stage tests are *assisted*, injection only of QA invulnerability. The cross-stage three-target test is controller-driven. The source wave bit5 test **injects world/phase/camera each frame** as a *unit fixture*, not a stage4 route.

## Verified tests / build

Build private ROM: `python tools/build_native.py --tools toolchain/linux-x64/bin --assets` (hash checked source assets); repeat without `--assets` to confirm deterministic output. Run `python tools/checkpoint.py test` for full scoped tests; or individually:

```
python tools/test_stage_one.py --core toolchain/linux-x64/bin/fceumm_libretro.so
python tools/test_stage_two.py --core toolchain/linux-x64/bin/fceumm_libretro.so
python tools/test_stage_three.py
python tools/test_stage_four.py
python tools/test_cheat_menu.py
python tools/test_n2_maps.py
python tools/test_secret_targets.py
python tools/test_source_groups.py --core toolchain/linux-x64/bin/fceumm_libretro.so
python tools/test_combat_native.py --core toolchain/linux-x64/bin/fceumm_libretro.so --tools toolchain/linux-x64/bin
python tools/test_pacing_native.py --core toolchain/linux-x64/bin/fceumm_libretro.so
python tools/test_title_native.py --core toolchain/linux-x64/bin/fceumm_libretro.so
python tools/test_vblank_budget.py
python tools/test_campaign_native.py --core toolchain/linux-x64/bin/fceumm_libretro.so --tool-dir toolchain/linux-x64/bin
python -m unittest discover -s tests -p 'test_*.py'
```

All new source transformations are locally built and tested for their *documented narrow scope*; see reports `reports/cp0012` (and `reports/cp0011` for the previous checkpoint). The FCEUmm tests are not hardware tests and do not certify a completed game.

## Next concrete engineering action

Port stage 5 from the MSX Z80 deasm: `final_de_la_fase_5` (p01:$6EA8) calls bank 3 twice (`$B946` mounts the first encounter, `$BB95` the second, flags E988/E990), releases the scroll to `$01FF`, then the ordinary Big Core. Port the stage-5 enemy types its waves use (check the opening-wave byte and group bits in `build/native/stage_05.bin`), keep the wait-for-clear source behaviour, add `tools/test_stage_five.py` on the same controller-driven pattern, and only then remove any remaining halt. Then stages 6-8 (type `$0C` first), the Nemesis ending, and the specialized chapters 2-4. Do not invent source events or declare phase transitions as finished gameplay.
