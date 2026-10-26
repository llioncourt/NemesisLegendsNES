# CP0006 - actual native title implementation

ROM SHA-256: `0e892e7bb6e6418241748c13da1fde344d70c99c89cf7d057ad35e457837af2d`. Size 262160 bytes. This is a title/UI revision of the
existing CP0005 playable checkpoint, not completion of Nemesis Legends.

## Implementation

The newer approved CP0005 composition, not the older CP0004 placeholder art,
is preserved byte-for-byte. Panel geometry is x=48, y=152, 160x64 pixels, leaving
the fighter and footer untouched. It covers the old text slots. START GAME and
OPTIONS occupy rows 21 and 24. The two-page sound menu is functional. The root
no longer offers an unavailable two-player mode.

The opening uses explicit black/dim/final palettes; eight panel rows reveal
bottom-up; the two labels follow; the cursor then becomes active. The normal
sequence reaches its last event after 52 title updates. Start/A during this
sequence runs the same bounded events faster; it never starts gameplay without
release and a new press. Cursor colour alternates every 30 updates. Directions
repeat at 15 then 5 updates; opposite directions cancel.

The panel is regular 2bpp background data in CHR bank 24, 4 KiB. The original
approved art remains in banks 19-22. No original gameplay CHR was overwritten.
All OAM entries remain hidden in the title; the cursor is a background tile.
The 16-byte state occupies $07E0-$07EF, outside game and audio state.

Main publishes one fixed-size command, and the existing ready handshake lets
NMI consume/acknowledge it. Panel-row commands update 20 ExRAM bytes in mode 2,
restore mode 1, and update 20 nametable bytes, all inside VBlank. Other commands
are at most 32 palette or 26 text/cursor bytes. Invalid commands and row indices
are rejected. This is an explicitly measured adaptation of the older menu spec's
32-byte cap: the 40-byte row command has no unbounded queue or frame-sized dump.
Hardware reference: https://www.nesdev.org/wiki/MMC5

Worst measured title video write: CPU cycle 1403, margin 870 against the test's
2273-cycle NTSC bound. All 60 legal combinations pass, including page, mute,
palette and all row positions. Timing assumes worst 514-cycle OAM DMA and no
DMC DMA during video work. The driver is called after the final video writes.
These are bounded binary execution tests plus FCEUmm runtime tests, not physical
NES measurements. PAL and hardware remain untested.

Title entry now disables PPU NMI before replacing the bank used by TitleVBlank.
Stage/HUD/boss requests are cleared in initialization; forced-game-over return
and stale-HUD cleanup were tested and are explicitly identified as QA injection.
Normal menu/input/start/mute tests use only the controller, not memory injection.

## Regressions and limitations

Combat, laser, boss, projectiles and campaign source modules remain byte-identical
to CP0005. The approved PNG, CHR, nametable, extended attributes and palette are
also unchanged; see preservation.json. Two assisted stage-one boss routes again
reach stage 2; the 2000-frame dense-weapon test reports zero missed NMIs.
No later stage, chapter, co-op mode, story scene or final cheat menu was added.
The native title track is the existing donor-APU track, not a new MSX arrangement.
The root sound toggle persists until reset; there is no new save system.

## Delivery

The private checkpoint contains current production inputs and sources. No GitHub
commit was made in this step. The IPS is against the exact private CP0005 ROM,
not an original Konami cartridge; applying it was verified byte-for-byte.
