# Build and test entry points

## Playable native integration (private assets)

The private checkpoint includes `build/native/Nemesis_Legends_CP0004.nes` ready
for an NTSC NES emulator with MMC5 and NES 2.0 support. No Python is needed to
play the included ROM. The build is incomplete; see the runtime handoff.

To rebuild the supplied converted assets with ca65/ld65:

```
python tools/build_native.py --tools "/path with spaces/to/cc65/bin"
```

To regenerate converted assets from the hash-checked private originals as well:

```
python tools/build_native.py --tools "/path/to/cc65/bin" --assets
```

On Windows the same Python entry points accept the matching tool executables.
The supplied compiler/core binaries are Linux x64, not Windows executables.
Public source checkouts intentionally do not contain commercial input assets.

After building, run the scoped native checks:

```
python tools/test_combat_native.py --tools /path/to/cc65/bin --core /path/to/fceumm_libretro.so
python tools/test_native_integration.py --core /path/to/fceumm_libretro.so
python tools/test_stage_one.py --core /path/to/fceumm_libretro.so
python tools/test_vblank_budget.py
```

The reports contain the ROM hash and distinguish component fixtures, assisted
runs, ordinary input tests and bounded timing assumptions. They do not certify
complete gameplay or physical hardware.

## Public source-only checks

Python 3.10 or newer and the packages in `requirements.txt` are required.
Install them in a local virtual environment, then run:

```
python -m unittest discover -s tests -p test_public.py -v
```

These checks do not require commercial inputs. They are not full-game tests.

## Native 6502 progression checks

Install cc65 (ca65 and ld65) and provide an explicit FCEUmm libretro core:

```
python tools/test_campaign_native.py --core /path/to/fceumm_libretro.so
```

On Windows use the matching DLL. When the assemblers are not on PATH, pass
`--tool-dir "C:\path with spaces\cc65\bin"`. The Linux toolchain artifact built
by this repository is for Linux x64 only; it is not a Windows distribution.

The script builds `build/campaign/campaign_unit_test.nes`, executes native
routines in the core, checks 288 source-derived route cases, checks the 6502
stack, and runs a deliberately corrupted native-table negative control. The
cartridge is a headless test harness, not a gameplay build for release.

## Private extraction and audio reproduction

Place the eight original supplied ZIPs in `inputs/`. Keep their filenames;
paths and the project directory may contain spaces. Run:

```
python tools/rebuild_evidence.py
```

The Windows wrapper is `REBUILD_EVIDENCE.cmd`. This regenerates input selection,
Nemesis/Nemesis 2 source assets, three NSF and three KSS driver wrappers, and the
custom native title asset. It does not silently overwrite the reviewed progress
ledger or source catalogue. It does not produce a complete game ROM.

To also render the reference soundtrack, provide libgme and ffmpeg/ffprobe:

```
python tools/rebuild_evidence.py --render-audio
```

Without MP3 rendering, the MP3 integration test is explicitly skipped, not
reported as passed. With the private checkpoint's 98 MP3s present, all 22
original integration tests pass. Reference rips are not MSX-to-NES arrangements.

## Original source reconstruction

Acquire the four pinned public source trees with `tools/fetch_sources.py`, or
use the source-evidence workflow artifact. This acquisition step needs network;
once acquired, extraction/reassembly/test work is local. The original images
must already have been selected by the evidence rebuilder.

```
python tools/verify_upstream.py --pasmo /path/to/pasmo
```

This invokes the assembler directly, checks every bank and rebuilds all four
originals privately. It does not execute arbitrary downloaded shell scripts.
No source reconstruction or component test should be called a full NES game.
