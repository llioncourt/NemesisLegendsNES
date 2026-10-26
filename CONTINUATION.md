# CONTINUATION — CP0010 (2026-10-26)

## Latest verified baseline
GitHub parent: `448a342a61c0c4e8b4abea254c9859dfc5115fce` (CP0009).
Local CP0010 native MMC5 ROM SHA-256: `81d956aff0684ab4e21c26a861b84807c094840214928cf962c1d72edec501c1`.
Rebuild from existing private project assets. Do not restart and do not post commercial ROMs/CHR/NSF to public GitHub. Public release format: IPS.

## Actual game coverage (NOT complete)
- Nemesis MSX: Partial native first/second stages, first stage boss, second stage rock rain/walls, stage9 bonus route. Stage3 now has source target at $012A, row $30, 8 pixels per column, 64-frame contact freeze, optional bonus10 route that returns at stage4. **The normal stage3 path intentionally halts at source world $019F because its bosses and eight background objects are not yet implemented**. No stage4-8 complete native gameplay.
- Nemesis 2 MSX: Event router but no full native game.
- Salamander MSX: Event router/Operation X conditions but no full native game.
- Nemesis 3 MSX: Event router but no full native game.

## Existing systems
MMC5 6502 title, native ship/partial actor/weapon/laser system, source-backed terrain column decoder, limited stage scripts, 30/40/60 logical-Hz pacing at 60Hz video/APU and partial source music. Visually incomplete and not user-approved. No complete cutscenes, OST, full Silicon Forge cheat menu, or integrated campaign playthrough.

## Evidence
The local CP0010 emulation tests use FCEUmm with controller-started stage1 and explicitly injected QA invulnerability only. Stage3 entry at frame 10664; normal reaches $019F at frame 13732; secret touches at 12956, enters bonus10 at 13020 (64 frames), and reaches stage4 at 15505. CP0009 baseline was rebuilt before the changes. No hardware or full-game playthrough is claimed.

## Known gaps and immediate next action
Recover source stage3's eight background objects, enemy patterns, midboss and final boss from `third_party/antxiko__Nemesis-disassembly/src/nemesis_p01.asm` near `final_de_la_fase_3`, and p02 `pared_de_la_fase_3`. Implement actual native scripts instead of generic encounters. Only then enable stage3 normal completion. Continue with stage4/bonus11 and every later level and campaign without shortening the scope.

## Build and tests
```
python tools/build_native.py --tools toolchain/linux-x64/bin
python tools/test_stage_three.py
python tools/test_stage_two.py --core toolchain/linux-x64/bin/fceumm_libretro.so
python tools/test_stage_one.py --core toolchain/linux-x64/bin/fceumm_libretro.so
python tools/test_combat_native.py --core toolchain/linux-x64/bin/fceumm_libretro.so --tools toolchain/linux-x64/bin
python tools/test_pacing_native.py --core toolchain/linux-x64/bin/fceumm_libretro.so
python tools/test_vblank_budget.py
```
The proprietary input assets and compiled ROM are private; source/public repo does not contain them. No automated background execution is running.
