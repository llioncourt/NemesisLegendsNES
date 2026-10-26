# Build and test - lean CP0005

## Integrity

`python tools/checkpoint.py verify` checks every shipped file against
`CHECKPOINT_FILES.json`, then the playable ROM and ten canonical input images.
This is an integrity check for a fresh unpack. Editing files or replacing reports
with new test runs will naturally invalidate their recorded package hashes.
Additional build output files are not silently included in the checkpoint.

## Native ROM

```
python tools/checkpoint.py build
python tools/checkpoint.py build --assets
```

The first command uses the converted data already supplied. The second regenerates
it from the selected originals and requires numpy/Pillow. Both must reproduce the
exact CP0005 ROM hash in `manifests/checkpoint.json`. All game code is unchanged.
On Linux x64, the bundled `toolchain/linux-x64/bin` is selected automatically.
On Windows, provide Windows ca65/ld65 with `--tools "C:\cc65\bin"`, or put them
on PATH. This package deliberately does not pretend Linux binaries run on Windows.

## Scoped QA

```
python tools/checkpoint.py test
```

This runs public/evidence tests, the 288-case campaign module test, 60 production
combat assertions, controller integration, the two assisted first-stage routes
and bounded vblank checks. No fresh gameplay completion is claimed.
Pass `--core` and `--tools` for alternate platform-native tools. Test output is
created under `build/` and `reports/`. MP3/archival-ZIP checks are explicitly
skipped in the lean edition, not counted as passed. Missing selected ROMs are fatal.
The old reference-audio playback captures are not a claim of converted MSX music.

## Source evidence and Z80 reassembly

```
python tools/rebuild_evidence.py
python tools/verify_upstream.py --pasmo toolchain/linux-x64/bin/pasmo
```

The evidence rebuilder now uses `manifests/selected_sources.json` directly and
requires no upload ZIP or network access. The ten selected input files remain at
their existing SHA-256 filenames. The source acquisition manifest explicitly
records a code/text subset: websites, image galleries and upstream MP3s were
omitted; retained source bytes and revision pins are unchanged. Only the project's
bank-reassembly verifier is certified here, not every website-producing upstream
Makefile target or its separate test suite.

The source tool `source_audit.py` still supports old upload collections. To repeat
that historical 137-image audit, use `rebuild_evidence.py --archives` in a separate
full-audit workspace containing all eight ZIPs. That is not required for this build.

## Optional listening renders

The six source drivers and named track indices are retained. The 98 MP3s live in
`Nemesis_Legends_Source_Music_CP0001.zip`, not in the working checkpoint. They can
also be re-rendered with `rebuild_evidence.py --render-audio` when libgme and
ffmpeg/ffprobe are installed. No empty MP3 directory counts as validated audio.

The native tool binaries require a compatible Linux x64 runtime. Python packages
are environment dependencies, not bundled wheels or a Windows offline installer.

For native title validation: python tools/test_title_native.py --core PATH

## CP0008 stage-two route test

From inside the unchanged `Nemesis_Legends_CP0001` folder, run the existing
`python tools/checkpoint.py test` entry point. It now also executes:

```
python tools/test_stage_two.py --core toolchain/linux-x64/bin/fceumm_libretro.so
```

The native ROM is `build/native/Nemesis_Legends_CP0008.nes`. The 900-frame rock
rain and secret stage9 branch are exercised **with invulnerability injected**,
clearly labelled in `reports/cp0008/stage_two_integration.json`. No other
stage/timer/position/route writes are injected. The code compiles with cc65 on
Windows once the private input assets have been recovered. The bundled Linux
core/tool executables are not Windows PE binaries.

A passing stage-two route test does **not** mean stages3–8, the other three MSX
chapters, full music and story have been implemented.
