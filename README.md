# Nemesis Legends — CP0007 (title restoration + Gradius II font)

Native playable MMC5 checkpoint; **the four-game campaign is NOT complete**.
Preserves the CP0006 title animation, root START GAME, functional OPTIONS sound,
first Nemesis stage gameplay, stage-2 entry and previous test baseline.

**New:** the original background scenery now remains present behind the rising
menu; no menu/footer rows are artificially emptied. The title and OPTIONS font
is extracted from the supplied genuine Gradius II Famicom ROM (verified 36
original 8x8 characters). A matching Famicom-font credit is composited over
scenery rather than a black footer band. The main illustrated logo is unchanged.

ROM: `build/native/Nemesis_Legends_CP0007.nes`
SHA256: `158675b365d3f2920bd11c89e7a860cc37cca60d6dd221d30f16271c6e66a19e`

Launch in an NTSC MMC5-capable emulator. Up/Down/Select choose; A/Start confirm;
A/Start during entrance skips to the ready menu without launching; OPTIONS
changes SOUND ON/OFF and B returns. During play: directional pad moves,
B fires, A consumes selected power-up, Start pauses. Sound setting persists
until reset. Two-player mode is not falsely exposed as playable.

The first-stage event route, volcano, Big Core and entry to stage 2 remain.
All later stages and chapters, story scenes, seamless transitions, co-op,
endings, the remaining soundtrack and the Silicon Forge cheat menu are pending.
**This is not a complete-game release.**

Verification: 56 actual ROM title/controller checks, 60 NMI command paths,
60 combat checks, 10 integration cases, 288 route unit cases, two assisted
stage-1 to stage-2 test runs and 42 Python tests (3 external-input skips).
No PAL or physical hardware certification.

Run `python tools/checkpoint.py verify`, `build`, or `test` from the unchanged
inner directory. Details: `docs/NATIVE_RUNTIME_CP0007.md` and `docs/HANDOFF.md`.
Use `requirements-title-art.txt` only if reprocessing the high-res approved art.
Do not publish original ROMs/graphic dumps; public playable releases are IPS-only.
