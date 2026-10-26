# Nemesis Legends — CP0008: native Nemesis stage-two routes

**WIP / playable partial NES/Famicom MMC5 native port, not the completed saga.**

The product goal is unchanged: **one continuous chronological campaign**
**Nemesis → Nemesis 2 → Salamander → Nemesis 3**, preserving *all* source stages,
mechanics, bosses, secrets, story, music, endings and cutscenes. This is **not** a
four-ROM launcher, a framebuffer playback tool or an isolated prototype.

## What actually runs in CP0008

- Custom scenic title, ascending dark menu, real Gradius II Famicom font,
  START GAME / OPTIONS, sound toggle and native 6502 MMC5 runtime.
- Nemesis stage 1 main route, source-derived enemies and bosses, weapons, death,
  checkpoints and transfer to stage 2 (preserved from CP0007).
- Nemesis stage 2: six MSX rock-wall triggers (five rocks per trigger, subject
  to the original 12-slot actor pool), three growth frames, original target
  at world $0190 / Y=$88, normal 900-frame rock rain at $01CF, Big Core at
  $01DF and actual stage-3 entry. The bonus route freezes for 64 frames on
  target collision, enters original bonus stage 9, scrolls its original
  landscape, and returns to stage 3 when the source distance marker is met.
  The original player/enemy shoot-to-free-slots behavior is **not altered**
  to make assisted tests artificially succeed.

The stage-two native module is `src/native_stage2.s`. The original source ROM
is the authority: `third_party/antxiko__Nemesis-disassembly` and the
hash-checked private cartridge. See `docs/NATIVE_RUNTIME_CP0008.md`.

## Evidence and limitations

On the *unmodified FCEUmm core* with **explicit player invulnerability** (no
manual stage/timer/boss-health/rock progression injection), both paths were
executed from the real first-stage beginning:

- Normal stage 2 → 3: 6 wall triggers, 74 source rock requests, 900 simulated
  rain frames, Big Core and source timeout, **0 missed NMIs**.
- Secret stage 2 → bonus 9 → 3: player actually touches the target; the
  source 64-frame freeze and scroll through stage 9 are observed, **0 missed
  NMIs**. This is a branch/progression test, not proof that optional areas
  have complete enemies or polished source visuals.

**Stage 3 and subsequent stages are not complete**, and Nemesis 2, Salamander,
Nemesis 3, cutscenes, final chapter transitions, full NSF score and the final
Konami Code / Silicon Forge cheat menu are not yet integrated. The current
sprite palette reduction is provisional. Full-campaign and real-hardware
certification have **not** occurred. Read coverage facts in
`manifests/content_coverage.json`, not the title art or ROM size.

## Build and tests

The private package is rooted in `Nemesis_Legends_CP0001` (do not rename):

```text
python tools/checkpoint.py verify
python tools/checkpoint.py build
python tools/checkpoint.py test
python tools/checkpoint.py sources
```

`BUILD.cmd` and `VERIFY.cmd` provide Windows entry points after installing
platform-native cc65; paths with spaces are supported. The bundled Linux
compiler/core are for Linux x64 only. No online downloads are required for
local recovery. See `docs/BUILD_AND_TEST.md`.

## Distribution

This public repository contains authored source, tools, tests and measured
summaries. The user's original commercial MSX/NES ROMs, source-derived graphics
and commercial audio are **private recovery material**, not published here.
Public Silicon Forge game releases use **IPS patches only**. The private ROM
in the user package is for authorized local testing, not the public release.

Current checkpoint: **CP0008 WIP**. No `Nemesis_Legends_NES_Final.nes` exists.
