# Nemesis Legends NES

Silicon Forge native NES/Famicom adaptation of the complete MSX continuity:
**Nemesis -> Nemesis 2 -> Salamander -> Nemesis 3**.

One continuous chronological campaign, not four ROMs behind a selection menu.
The accepted scope preserves every source stage, return/bonus route, Operation X,
chapter-specific weapons, co-op, story event and ending. Donor NES/Famicom code
and graphics may be reused where they genuinely match the MSX content.

## Current checkpoint: CP0004

**A runnable native MMC5 gameplay build now exists; the four-game anthology is
not complete.** The private cartridge integrates Nemesis stage 1's main route,
its five-part encounter, volcanic sequence, Big Core, death/checkpoints and
stage-2 entry. The custom title, ship, weapons, Options and source-derived
terrain run on the NES; no original-game emulator or captured playback is used.

Start begins/pauses, B fires and A activates the selected power-up. Normal boot
has no QA assistance. Stage 2 onward is incomplete; do not call entry into stage 2
completion of that stage or the first game.

Verified on the exact build identified by `reports/native_runtime_budget.json`:
60 production-6502 combat assertions and negative control; 10 controller-level
checks; two assisted start-to-stage-2 boss routes; five bounded NMI transfer
cases plus an oversized-queue negative control. The 2,000-frame dense-weapon test
recorded zero missed NMIs. The separate router's 288 event tests, 13 public and
22 private evidence tests also pass. Hardware/PAL/full-campaign validation is
not implied. See [runtime evidence and gaps](docs/NATIVE_RUNTIME_CP0004.md).

Preserved evidence: all four canonical originals, 80 byte-exact reconstructed
Z80 banks, source maps, reference NSF/KSS/MP3 music and the Suno prompt. Source
music rips are not a completed MSX-to-NES score conversion.

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

Finish Nemesis stage 2 and all subsequent stages/routes, then integrate the
remaining three chapters with their actual mechanics. Co-op, source cutscenes,
seamless chapter bridges, endings, remaining music, full hardware verification,
and the final Konami Code / English Silicon Forge menu are still pending.
Known combat/palette/score/presentation gaps are explicit in the runtime document.

Do not restart this as a generic shooter, captured playback or a title demo.
See [NOTICE](NOTICE.md) for source and third-party attribution boundaries.
