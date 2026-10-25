# Nemesis MSX mirror-record decoder correction

Source: `antxiko/Nemesis-disassembly`, commit
`3e486bc2f39c65eb97a944cda246f85fd30218ec`, `tools/graficos.py` and
`src/nemesis_p00.asm` (ASM blob 58e5382a3efb5a0510f5c0a7100da2816ee66c7d).

Original ROM SHA-256:
`3210f8a0f2309dd4b9a89fc2b24d0f178ce4393a0a1f2854fbce545c361261bc`.

The external helper treats mirror-record fields incorrectly and bit-reverses
color bytes during horizontal flips. The original program does neither.

## Actual four-byte record

`[source tile][destination tile][third-selection flags][tile count]`

A zero source tile terminates the table. Source third: flag bit 2 selects the
first third, otherwise bit 1 selects the second, otherwise the third. Destination
bits 5, 4 and 3 select the first, second and third screen thirds respectively.

The first stage's horizontal record at bank 5, address `$96AE`, is
`63 68 29 05`: five tiles starting at `$63`, copied to `$68`, with flags `$29`.

## Binary evidence in bank 0

- `$434D`: `DD 6E 03 26 00 29 29 29 22 01 E1` reads the count from IX+3,
  multiplies it by eight, and stores the byte count at `$E101`.
- `$4454`: `DD 6E 00 26 00 29 29 29` reads the source tile from IX+0.
- `$43F2`: `21 00 E3 ED 5B 01 E1 06 08 CB 1E 8F 10 FB 77 23 1B 7A B3 20 F2 C9`
  reverses the pattern-byte bits in `$E300` only. Color buffer `$E700` is not
  visited by this routine.

Horizontal reflection reverses pixel bits but preserves the foreground/
background color nibbles. Vertical reflection reverses the eight row bytes of
both the pattern and the color record. `extract_nemesis_msx.py` follows this
behavior and the test suite checks both transformations and the source bytes.

## Scope

This is a local correction to the extraction tool, not a bug report submitted
to the external repository, not a ROM patch, and not a claim that every upstream
format has now been verified. Full openMSX VRAM comparison remains pending.
