# Source evidence review - CP0002

Four upstream MSX disassemblies are pinned in `evidence/source_catalog.json`.
The complete source snapshot has 912 hash-verified files after fixing the CI
artifact's initial hidden-file omission. It excludes commercial ROM binaries
and redundant audiovisual captures, not source files. It is not a Git checkout
with commit history; the exact upstream commits and archive hashes are recorded.

`tools/verify_upstream.py` independently invokes Pasmo for all 80 ASM banks,
checks every bank against its selected input, then checks concatenated originals:
Nemesis 131072 bytes; Nemesis 2 131072; Salamander 131072; Nemesis 3 262144.
All 655360 bytes match. Detailed per-bank results live in the private checkpoint's
`reports/upstream_reassembly.json`; the public measured summary has the four
whole-ROM hashes and source pins. The verifier regenerates the full report.

Reassembly alone cannot prove that every upstream label, interpretation or data
reader is correct. The Nemesis mirror-reader correction already demonstrates
this: an ASM listing can reproduce the original while a separate graphics
helper misreads its data. Continue validating behavior against original bytes
and execution rather than treating comments as an infallible specification.

## Sources already usable

- `antxiko/Nemesis-disassembly`: full pinned source, exact reconstruction, local
  corrected terrain/graphics reader, source PSG driver wrapper.
- `antxiko/Nemesis2-disassembly`: full pinned source, exact reconstruction,
  local compact maps and sprite-variant extraction, PSG/SCC driver wrapper.
- `antxiko/Salamander-disassembly`: full pinned source, exact reconstruction,
  source PSG/SCC wrapper; stage/actor/cutscene extraction remains to integrate.
- `antxiko/Nemesis3-disassembly`: full pinned source, exact reconstruction,
  canonical original recovered from the user's 16-entry archive; gameplay,
  graphics and sound extraction remain separate pending tasks.

## Supplemental NES references

`Fabulu/Mixup` contains a semantic JavaScript Gradius reimplementation and ROM
notes; it is not native MMC5 code. `MikeWuPing/UEFI_Salamander` contains a C
reimplementation and extraction evidence; its author reports audio and fidelity
limitations. Neither was substituted for an end-to-end validated native port.
No verified complete Gradius II Famicom disassembly was established by the
investigation. This does not prove that no other useful public project exists.

The six supplied NES/Famicom originals remain available privately for donor
asset and native-code analysis. Their mappers and hashes are recorded. Shared
melody, graphics or a similar enemy name are not enough to claim behavior parity.
