# CP0005 - approved title integrated into the game

## Scope

The approved reference is assets/title_art/approved.png, SHA-256
`94a13d196f72fb8978b46396c3a4cdbceae9755c9906562ed3238fcfc4723bab`. The scenic background and corrected ship are retained.
A local build-time mask removes the baked menu text and cursor. The game draws
its own three selectable entries, and retains the 2026 Silicon Forge credit.
The high-resolution artwork is deliberately reduced to actual NES constraints.

## Allocation

- ROM: 262160 bytes, unchanged from CP0004.
- New background: 896 unique 2bpp tiles,
  14336 useful bytes, 16 KiB allocation in CHR banks 19-22.
- Cursor: 32 useful bytes, one 1 KiB sprite bank (92), one OAM entry.
- Nametable: 1,024 bytes; extended attributes: 1,024 bytes.
- Four palettes, 12 distinct background colours.
- Native title code and tables: 2848 bytes in PRG bank 9.
- Menu RAM: $07E0-$07E3. The existing actor/projectile memory is not repurposed.
- All 77,824 bytes of pre-existing graphics remain byte-identical.
- Original stage/map/boss-data banks 0-6 and 8 remain byte-identical.
  Actor source is unchanged; the linker updates 18 call-target bytes in bank 7.

The ExRAM is uploaded while rendering is disabled and $5104=2, then switched to
$5104=1 for extended-attribute rendering. CHR is ROM-resident, not uploaded every
frame. Only 36 nametable characters and OAM are updated when a menu page changes.
The bounded worst-case title video write is at CPU cycle 1,237 of the nominal
2,273-cycle NTSC vblank budget, including worst-case OAM DMA. No DMC DMA was
assumed during this timing measurement. No mid-frame palette writes are used.
MMC5 reference: https://www.nesdev.org/wiki/MMC5#Extended_attributes

## Controls

Up/Down or Select moves through 1 PLAYER, 2 PLAYERS and OPTIONS. A/Start confirms.
1 PLAYER uses the existing stage entry. OPTIONS enables/disables the actual APU
sound and preserves the choice into gameplay. B or BACK returns to the title.
2 PLAYERS opens a notice; it does not fake co-op or silently launch single player.
The requested final Silicon Forge cheat menu is still a separate pending feature.

## Verification

25 title/control/timing assertions pass, including a negative control that removes
the title bank. The title is stable for 180 compared frames and produces audible
native donor-APU output. All original 60 combat assertions pass, and their mutated
laser negative control still fails. Ten controller integration checks pass.
The 2,000-frame weapon-stress run reports zero missed NMIs. The two assisted
first-stage runs reach stage 2; invulnerability is explicit in those reports.
The campaign router still passes 288 checks. 42 public/private unit tests complete,
with three expected skips for external input ZIPs and MP3s absent from this lean
checkpoint. This is not a full-game or physical-hardware certification.

ROM SHA-256: `0fc137f6ccbf772b28719e998cad37d397891d4d6611d1ea10992baf6a8e0396`.
IPS base CP0004 SHA-256: `0c9d1135a7675165e8d7125db0f5d8a990265e112b7508f9701cb63662c70d02`.
The 25252-byte IPS reapplies byte-identically to the delivered cartridge.

The local screenshot reports/cp0005/title.png is a 256x240 emulator capture.
title_3x.png uses nearest-neighbour integer enlargement; it is not the concept image.

## Recovery and publication

This private checkpoint includes the exact inputs and current generated data.
No GitHub write was performed for this title update. The baseline public commit
is b4deb7066dc73dd99b868e2ac2cb3487c153c470. Do not mistake older CI reports for
verification of CP0005; the CP0005 results are the included local reports.
