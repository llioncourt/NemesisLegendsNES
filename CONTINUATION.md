# NEMESIS LEGENDS NES — CONTINUATION (CP0011, 2026-10-26)

Repository: https://github.com/llioncourt/NemesisLegendsNES
GitHub last confirmed baseline before this execution: `5b1f15ed09f63d230bb01a19753ed821a2ffb1cb` (CP0010).
Current tested private ROM: `build/native/Nemesis_Legends_CP0011.nes`; consult `manifests/checkpoint.json` for exact SHA-256. Update this document's remote commit only after server verification. Do not reset or abandon the existing native motor. Public distribution: IPS only; the source ROMs and derived commercial CHR/audio stay private.

## Actual coverage, not release claims

1. **Nemesis / Gradius MSX**: partial native stages 1 and 2 (rock walls, 900-frame rain, Big Core, bonus9), stage3's two source type-1 Big Core encounters at world `$0060` and `$01AF` and bonus10/normal branches to stage4. Cross-stage MSX target types 2/3/4 persist from stage1 into stage4; three distinct touches activate bonus11 and route to stage5. Group bits 4 and 5 now call the original eight-type9 flock and the mixed type5/type6 spawners. The natural type9 group is seen in stage3; the mixed group has only been validated in an **isolated RAM-injected stage4 segment** beyond the unported boss. Stage4's two original boss encounters and normal clear are **not integrated**; the original checkpoint blocks progress at world `$0128`. Stage5 onward contains resource descriptors, not playable faithful level logic. Full Nemesis MSX is **NOT complete**. The screenshot criticism about sparse art and HUD is not resolved.
2. **Nemesis 2 MSX**: source-extracted maps and campaign event-router metadata; no full native levels, unique weapon system, ending, cutscenes or validated complete campaign.
3. **Salamander MSX**: campaign router and secret Operation X requirements only; no full native campaign, planet missions, co-op, audiovisual equivalence or validated ending.
4. **Nemesis 3 MSX**: original validated/decompiled, campaign router metadata, but no native levels, chronology/cutscenes or ending integration.

## Working native systems

MMC5 6502 title/menu (not user-approved art), native 8x8 source columns, stage-specific enemy/weapon/laser/boss support, cross-stage target memory, bonus router, 30/40/60 logical-FPS option with NTSC video and APU at 60Hz, source driver references; no complete native OST. Compact source tile data and decomp resources remain in their original private source directory, not inflated per-frame playback.

## Critical missing systems and visual quality

- Original stage4 specialized warning at `$0128`, both stage4 bosses (one first, second around `$0171`, then `$01C0` scroll), stage5-8 scripted combat and bonus12. The normal route must not bypass unfinished bosses.
- Full original enemy actor types/patterns, sprites, scenic layers and collision parity. The CP0008 user's screenshot showed black void, repeated sprites and poor HUD; **these visuals are still NOT fixed**.
- All Nemesis 2 / Salamander / Nemesis 3 mechanics, cutscenes and endings, native music conversion, global deduplication and total CPU/ROM budget certification, full stage playthrough without QA help, Konami Code + Silicon Forge cheat menu.
- The normal-to-next-stage tests are *assisted*, injection only of QA invulnerability. The cross-stage three-target test is controller-driven. The source wave bit5 test **injects world/phase/camera each frame** as a *unit fixture*, not a stage4 route.

## Verified tests / build

Build private ROM: `python tools/build_native.py --tools toolchain/linux-x64/bin --assets` (hash checked source assets); repeat without `--assets` to confirm deterministic output. Run `python tools/checkpoint.py test` for full scoped tests; or individually:

```
python tools/test_stage_one.py --core toolchain/linux-x64/bin/fceumm_libretro.so
python tools/test_stage_two.py --core toolchain/linux-x64/bin/fceumm_libretro.so
python tools/test_stage_three.py
python tools/test_secret_targets.py
python tools/test_source_groups.py --core toolchain/linux-x64/bin/fceumm_libretro.so
python tools/test_combat_native.py --core toolchain/linux-x64/bin/fceumm_libretro.so --tools toolchain/linux-x64/bin
python tools/test_pacing_native.py --core toolchain/linux-x64/bin/fceumm_libretro.so
python tools/test_title_native.py --core toolchain/linux-x64/bin/fceumm_libretro.so
python tools/test_vblank_budget.py
python tools/test_campaign_native.py --core toolchain/linux-x64/bin/fceumm_libretro.so --tool-dir toolchain/linux-x64/bin
python -m unittest discover -s tests -p 'test_*.py'
```

All new source transformations are locally built and tested for their *documented narrow scope*; see reports `reports/cp0011`. The FCEUmm tests are not hardware tests and do not certify a completed game.

## Next concrete engineering action

Port the source stage4 specialized original bosses from the MSX Z80 deasm (`third_party/antxiko__Nemesis-disassembly/src/nemesis_p01.asm`, `final_de_la_fase_4` `$6E15`, first warning at `$0128`, second at `$0171`) and their custom background-object renderer/collisions. Add hostile actor/attack integration and original stage4 normal clear; remove existing phase13 halt **only after both bosses are playable and testable**. Then source stage5-8, finalize Nemesis, and build specialized original chapters 2-4. Do not invent source events or declare phase transitions as finished gameplay.
