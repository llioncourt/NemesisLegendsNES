# Nemesis Legends NES

Silicon Forge native NES/Famicom adaptation of the complete MSX continuity:
**Nemesis -> Nemesis 2 -> Salamander -> Nemesis 3**.

One continuous chronological campaign, not four ROMs behind a selection menu.
The accepted scope preserves every source stage, return/bonus route, Operation X,
chapter-specific weapons, co-op, story event and ending. Donor NES/Famicom code
and graphics may be reused where they genuinely match the MSX content.

## Current checkpoint: CP0002

**There is not yet a playable Nemesis Legends game ROM.** The repository now
contains real source, extraction tools and native 6502 progression code, not only
a planning README. The native test cartridge is a component test, not a game.

Verified locally:

- All four canonical MSX inputs identified by hash; 137 supplied ROM images audited.
- 912 upstream source files acquired and checked at four exact commits.
- 80 Z80 ASM banks reassembled: all 655,360 bytes match the supplied originals.
- Native 6502 progression module: 288 route/event checks executed in FCEUmm,
  plus a corrupted-native-table negative control and stack-leak checks.
- 13 public source-only tests and 22 private extraction/audio integration tests pass.
- Preserved CP0001 resources: 12 Nemesis terrain records, 12 Nemesis 2 map IDs,
  48 sprite variants, native custom title assets, three NSF and three KSS source
  rips, 98 private reference MP3s and an 877-character Suno style prompt.

These figures do **not** claim completed gameplay, adapted cutscenes, full music
conversion, whole-game timing validation or an implemented cheat menu.

## Build and evidence

See [build/test instructions](docs/BUILD_AND_TEST.md), the
[handoff](docs/HANDOFF.md), [native progression contract](docs/CAMPAIGN_FLOW.md),
[source review](docs/SOURCE_REVIEW.md), and [coverage ledger](manifests/content_coverage.json).
The Python evidence tools work with local original ZIPs and paths with spaces.
Public tests do not need commercial ROMs. Native tests require ca65, ld65 and an
explicit FCEUmm core. Pinned acquisition and Linux verification-tool workflows
are included; no emulator is part of the production cartridge design.

## Public/private boundary

The public repository contains source, fixtures, provenance, measured summaries
and rebuild tools. Commercial originals, original ZIPs, whole donor PRG dumps,
reference audio and regenerated source-asset binaries remain in the private
recovery package. They were preserved, not deleted during migration. Public
completed-game releases use IPS patches under the project owner's standing rule.

## Remaining gates

The native actors, bosses, collisions, renderer, co-op, cutscene scripting,
seamless runtime integration, source-to-NES arrangements, and full-route hardware
verification remain implementation work. The requested Konami Code and English
Silicon Forge cheat menu follow complete-campaign integration, not replace it.

Do not restart this as a generic shooter, captured playback or a title demo.
See [NOTICE](NOTICE.md) for source and third-party attribution boundaries.
