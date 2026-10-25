# Nemesis Legends NES

Silicon Forge native NES/Famicom adaptation of the complete MSX continuity:
**Nemesis -> Nemesis 2 -> Salamander -> Nemesis 3**.

One continuous campaign, not a four-ROM launcher. Preserve complete source
stages, return routes, secret areas, Operation X, chapter-specific weapons,
co-op, story and endings. Reuse NES/Famicom code and assets only where they match.

## Verified status

The private CP0001 evidence/audio checkpoint and its Nemesis 3 addendum are
being migrated. All four canonical MSX inputs are present and hash-verified.
**There is no playable Nemesis Legends ROM in CP0001.** Extracted maps, source
music and title graphics are not a completed port.

## Public distribution

Source, tools, manifests and patches belong here. Original commercial ROMs,
input ZIPs and reference soundtrack binaries remain in the private recovery
package. Public releases use IPS patches according to the project owner's rule.
Do not delete private evidence to prepare a public checkout.

## Non-negotiable implementation requirements

* One native 6502 runtime designed and budgeted for all four complete games.
* Chronological campaign and seamless chapter transitions, with source-grounded cutscenes.
* Deduplication before compression; preserve compact data and provenance.
* Measure CPU, RAM, ROM and PPU budgets before claiming the complete content fits.
* Base-APU music must be complete without MMC5 expansion audio.
* Add the Konami Code and English Silicon Forge cheat menu after full-campaign integration.
* Report extraction, conversion, integration and gameplay testing separately.

See the committed handoff and coverage reports for exact progress.
