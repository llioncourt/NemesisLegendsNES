# CP0002 handoff - migration, byte-exact sources and native campaign module

## Current truth

There is no playable Nemesis Legends game ROM. A real 6502 campaign progression
module now exists and passes 288 event tests in FCEUmm. Do not describe that
module or its headless unit-test cartridge as the complete port or a playable
chapter. No gameplay frame-rate claim has been established.

## Originals and preserved evidence

Eight original ZIPs, unchanged, are in the private package's `inputs/`.
137 unique images were audited: 131 MSX and six NES/Famicom. All four required
canonical MSX sources are present; Nemesis 3 is the 262,144-byte image with
SHA-1 `7393f677e0fae5fc83071c6b74756117b7d75e2d`, not an enhanced variant.
`tools/rebuild_evidence.py` reconstructs the hash-addressed private cache.

## Newly verified

The complete public source snapshots of the four pinned MSX disassemblies were
acquired through the repository's source-evidence workflow. 912 file hashes were
checked; commercial ROMs and redundant audiovisual captures were deliberately
excluded from the snapshot. The first artifact omitted hidden files; the fixed
second artifact includes them and was fully checked.

All 80 ASM banks were assembled directly with Pasmo and compared with the
supplied originals: 655,360 bytes, zero differences. `tools/verify_upstream.py`
reproduces this check and reports each bank's source and output hashes. No
reassembly success is treated as proof of a native NES gameplay port.

The Linux tool artifact includes cc65/Pasmo and a pinned FCEUmm core, with their
licenses and corresponding FCEUmm source. It is a verification tool package,
not a required runtime dependency of the future NES cartridge.

`src/campaign.s` implements source-derived main, bonus, interior, return,
planet-selection and map-revisit routes. Read `docs/CAMPAIGN_FLOW.md` for exact
source addresses, the explicit anthology retry policy and native test scope.
The 22 pre-existing private extraction/audio tests still pass.

## Preserved CP0001 outputs

Nemesis: 12 static terrain records. Nemesis 2: 12 map IDs and 48 sprite variants.
The corrected Nemesis mirror reader is still guarded by original-byte checks.
A custom title exists as native CHR/nametable/palette data, not yet integrated.
Three NES NSF rips contain 42 selected native source cues; three MSX KSS rips
contain 56 selected reference cues. The private package has 98 named MP3s and
an 877-character Suno prompt. These are source references, not a finished
MSX-to-NES soundtrack conversion. Nemesis 3 audio is not yet extracted.

## Public/private boundary

The public repository contains source, test fixtures, provenance, manifests,
rebuild tools and measured summaries. Original commercial ROM/ZIP files, raw
PRG dumps and reference soundtrack binaries remain in the private recovery
package. Generated assets can be rebuilt; they were not deleted from the
private working project to prepare the public tree. Public game releases use
IPS under the owner's standing rule.

## Remaining production work

Complete extraction of Salamander/Nemesis 3 graphics, all enemy and boss states,
collision data, spawn scripts, source dialogue/sequences and score formats;
measure the whole-content RAM/ROM/CHR/CPU/PPU budget; implement and integrate the
native gameplay renderer, actors, weapons, collisions, co-op and source events;
connect the tested progression module to those real events; adapt all cutscenes
and chapter bridges; convert the remaining score with a complete base-APU mix;
validate every route/ending/death/continue; only then add the requested Konami
Code and English Silicon Forge cheat menu, including Sound Test.

Do not reset the project or replace original content with generic stages. Do
not ask for the accepted scope or supplied ROMs again. No asynchronous work or
future-delivery task is scheduled by this checkpoint.
