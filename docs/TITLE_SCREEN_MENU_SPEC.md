# Native title screen and menu - implementation specification

Status: specification, not a runtime implementation or a completed-game claim.
Target: the existing CP0004 native NES/Famicom MMC5 runtime.
Reviewed: 2026-10-25.

This document makes the proposed title/menu treatment concrete. It does not
replace the complete-game scope, restart the engine, or supersede the gameplay
priorities in HANDOFF.md. A polished title is not evidence that the anthology is
complete. No game code or original asset is modified by this documentation commit.

## 1. Evidence baseline

The inspected source is the authority, not references to unidentified images:

| File | Inspected Git blob | Relevant behavior |
| --- | --- | --- |
| src/native_kernel.s | 57ebc209c3b7bde8eb104b18544e4edd27c1d394 | Main calls Title; mode 0 accepts Start directly; Title uploads a static nametable and palette. |
| src/native_boot.s | 19d946cc63e8256c58dba20525bf6baa78b4df17 | NMI owns graphics transfers; PollPad exposes newly pressed buttons; TitleName/TitlePalette are linked assets. |
| tools/create_title_asset.py | 2aacf1a2d8c9cc5ae0bb4e0a9b5988f3a674e2ee | Generates the actual logo, fighter, stars, PRESS START, 4 KiB CHR and 1 KiB nametable. |
| docs/HANDOFF.md | 090d5a6a6be1776d70c586dcaedeebbeb6276f6f | CP0004 is partial native gameplay; full campaign and final cheat menu remain pending. |

Re-read these files before implementation if their hashes have changed. Preserve
intervening work. Do not use this document to overwrite a newer runtime.

The generator's old asset-only metadata is not an integration test: the current
runtime already references its output. Report asset encoding, runtime linkage
and controller-level behavior separately.

## 2. Direction and scope

Keep the existing NEMESIS LEGENDS logo and fighter design. Retain their pixel
art, not an imagined first/second reference image. Replace the lower timeline
ornament and baked PRESS START with a real opaque menu panel. Keep the fighter
stationary in this revision; do not scroll the entire title to imitate a moving
panel. No high-resolution mockup, framebuffer movie or per-frame CHR expansion.

The opening presents one campaign:

Nemesis -> Nemesis 2 -> Salamander -> Nemesis 3.

Do not create a four-game launcher. Do not put 1 PLAYER / 2 PLAYERS on the global
opening: that would imply a multiplayer campaign implementation that does not
exist. Preserve the planned source-specific co-op in the appropriate chapter;
this UI decision does not remove it from the project.

## 3. Exact composition

Coordinates below are native pixels, origin at the top left. Bounds use
[x, x + width) and [y, y + height).

| Element | Geometry / rule |
| --- | --- |
| Canvas | 256 x 240; 32 x 30 background tiles. |
| Existing brand and main logo | Preserve current upper-screen art. |
| Existing subtitle | Preserve the current THE BURTON LEGACY area. |
| Fighter | Preserve current footprint, approximately x=102..150, y=142..179. |
| Menu panel | x=48, y=184, width=160, height=40. |
| Panel in tiles | column 6, row 23; 20 columns x 5 rows. |
| First item | START GAME, x=80, y=192. |
| Second item | OPTIONS, x=80, y=208. |
| Cursor | x=64; y=192 or 208 according to selection. |
| Footer | NES / FAMICOM, centered at y=224, using the small existing font style. |

The panel ends before y=224 and does not cover the fighter. The center interior
row is blank, separating the two menu items. Remove the original ornament around
y=187 and PRESS START around y=199 from the base nametable. Do not render both
PRESS START and an active menu. Replace THE COMPLETE MSX SAGA in the unfinished
build's footer; do not imply a finished anthology in checkpoint artwork.

The panel is black and opaque, with a one-pixel blue frame and small amber corner
accents. Text is light; the cursor is amber. Reuse the existing palette entries
$0F, $12, $30, $27. The existing background palette layout can remain shared;
this revision does not require MMC5 extended attributes or scanline splits.
Do not change neighboring attribute quadrants to recolor the panel in isolation.

Every panel tile, including the blank interior, replaces the underlying starfield.
No stars, fighter fragments or decorative sprites may cross its interior. Color
index zero alone does not occlude sprites: keep title OAM hidden rather than
relying on a black background to hide them.

## 4. Entrance sequence

Frame numbers are presentation targets at the existing NTSC cadence, relative
to the first visible title frame after the one-time asset load. They are not
measured runtime results. A phase may advance only after its queued write was
consumed; do not lose rows if the producer falls behind.

| Frame | Visible action |
| --- | --- |
| 0 | Base art is present with the palette black; panel area contains no menu text. |
| 4 | Apply a dim intermediate palette. |
| 8 | Apply the final palette. |
| 12..27 | Hold the logo and fighter without camera movement. |
| 28, 30, 32, 34, 36 | Reveal one 20-tile panel row, bottom upward: rows 27, 26, 25, 24, 23. |
| 40 | Write START GAME. |
| 44 | Write OPTIONS. |
| 48 | Show the cursor on START GAME and accept navigation, after all writes are acknowledged. |

This is an upward reveal, not a subpixel slide. Store five panel row templates,
not a complete nametable for every animation frame. The target is about 0.8 s at
60 Hz after the initial load. This does not establish PAL support; PAL cadence
and the rest of the game require separate validation.

Use explicit palette ramps rather than subtracting blindly from NES color codes.
Suggested ramp for the four shared entries:

- black: $0F, $0F, $0F, $0F;
- dim: $0F, $02, $10, $07;
- final: $0F, $12, $30, $27.

Keep that ramp configurable for actual-console contrast checks. Do not add
high-frequency whole-screen flashing.

A newly pressed Start or A during the entrance requests fast-forward. It finishes
the final panel through the same bounded upload queue, then waits for release.
It must NOT start the game with that same press. A later distinct press confirms
START GAME. Fast-forward is not permission to upload all 100 panel tiles in one
rendered-frame transaction.

## 5. Cursor and controls

Use an 8 x 8 background cursor tile, not a new hardware sprite. This avoids
changing the runtime's existing 8 x 16 sprite configuration. Generate two cursor
tiles with identical geometry: amber and blue. Alternate every 30 title frames;
keep the selected item readable continuously. Reset the cursor cycle on movement.
A selection update erases the old cursor and writes the new one in one small
transaction; never leave two cursors visible.

- Up / Down: move between the two items, with wraparound.
- A or Start: confirm once on the newly pressed edge.
- B: return from OPTIONS; no action on the root title menu.
- Held direction: repeat after 15 frames, then every 5 frames.
- Simultaneous opposite directions: no navigation.
- Simultaneous A and Start: one confirmation, not two.

Reuse PollPad and pressed. Do not poll the controller independently inside NMI
or interpret held Start as repeated scene confirmations. The controller state
must be consumed at the title-to-campaign boundary so it cannot immediately pause
the game or skip the first narrative event.

## 6. OPTIONS must be functional

The minimal OPTIONS submenu has SOUND ON/OFF and BACK. Use the same panel and
input rules. SOUND affects both music and effects and persists for the current
powered session. Do not imply a persistent save system.

Turning sound off must actually silence sounding channels; simply skipping
future audio updates can leave a sustained tone. Turning it back on must restore
a valid driver state without corrupting the campaign or mapper banks. Apply the
setting consistently when LoadStage initializes audio. The current audio_on flag
is a driver-running flag, not automatically a complete user mute implementation.
Validate the donor driver's stop/restart or mute mechanism before selecting it.

There is no invented title music ID in this specification. Keep the existing
title silence until a real native score and verified driver entry are integrated.
A missing soundtrack may not be hidden behind an MP3 recording.

Do not ship a selectable OPTIONS label whose handler is absent. If its handler
is still missing, this specification has not been fully implemented. Do not add
CONTINUE, SAVE, DIFFICULTY or SOUND TEST buttons as nonfunctional decoration.
The final Silicon Forge Sound Test belongs to the later cheat-menu integration.

## 7. Native integration points

Prefer a small src/native_title.s module with TitleInit, TitleUpdate and
TitleUploadQueue. Those symbols are proposed, not present in the inspected code.
Move or delegate the existing Title routine without duplicating its full asset
load in another engine. Update the ordinary native build module list explicitly.

Maintain mode=0 for all title/submenu states. Add a separate title-local substate:

INIT -> FADE -> HOLD -> PANEL -> TEXT -> READY
READY -> OPTIONS -> READY
READY -> EXIT -> existing campaign startup

Do not call FrameGame, SpawnWaves or stage-event handlers from these states. Do
not advance world position, campaign RNG, enemy timers, lives or score while
navigating the title. This module is presentation and input, not gameplay.

On confirmed START GAME, execute the existing new-game initialization exactly
once: Flow_NewGame, score/route reset, lives, first stage and LoadStage. Preserve
the CP0004 gameplay path until the actual cutscene dispatcher is integrated.
Do not claim that the planned story scenes now exist. In the completed campaign,
START GAME must enter the initial narrative event and then follow the same
campaign router, without returning to the title between chapters.

Before calling a loader, disable rendering/NMI through the actual PPU controls
and clear ownership of pending title transfers. SEI is not an NMI disable. Restore
scroll, CHR mapping, relevant PPU state and the existing IRQ policy through the
loader. Never leave a title cursor or palette write queued after gameplay begins.

## 8. Existing queue hazard to address

The inspected Title routine clears mode, camera, audio_on and graphics controls,
but does not explicitly clear every stage graphics request. The inspected NMI
can consume column_pending, boss_dirty and hud_pending before applying its
mode-dependent scroll behavior. Therefore a return from gameplay can allow a
stale request to overwrite title data. This is a source-level risk, not a
reproduced emulator failure in this documentation task.

During TitleInit, with the display transaction safely owned by the initializer:

1. Hide OAM and stop accepting stage uploads.
2. Clear column_pending, boss_dirty and hud_pending.
3. Clear the title queue, its publication flag and title input latches.
4. Reset title substate, timer, selection and repeat counter.
5. Load the base art while rendering is disabled.
6. Publish the initialized state, then enable normal frame processing.

A title-only NMI upload branch should bypass stage columns, boss queues and HUD
writes, while retaining the existing ready handshake, audio policy and required
register restoration. Do not break the stage upload path to fix the title.

## 9. Memory and upload contract

These are proposed caps to validate, not measured costs or claims of free RAM:

| Resource | Cap / rule |
| --- | --- |
| Background CHR | Keep the existing 4 KiB title allocation; at most 256 distinct 2bpp tiles. |
| Nametable | One base 1,024-byte asset, including attributes; no animation-frame bank stack. |
| Panel templates | Five rows x 20 tile IDs = 100 bytes of row payload. |
| Additional RAM | At most 64 bytes: 48-byte queue plus 16 bytes of UI state. |
| Additional PRG | Initial target at most 2 KiB for title/UI code and small tables; measure the linker delta. |
| Rendered-frame upload | At most 32 data bytes total across nametable/palette writes and at most 4 commands. |
| UI hardware sprites | Zero. |

The 48-byte queue can hold a command count, up to four three-byte command headers
(address high, address low, length), and at most 32 data bytes: 45 bytes maximum.
Keep pending/publication state within the state allocation. Reject malformed
lengths and out-of-range title destinations; never allow a producer overflow.

Main constructs the whole queue only when the previous one has been consumed,
then publishes the pending flag last. NMI consumes only a published transaction
and acknowledges it after completing all writes. The producer must not overwrite
a pending queue. Restore the PPU address latch and scroll following transfers.

Clear/all-screen transfers are allowed only in the explicit rendering-disabled
load, not during the animated menu. The 32-byte limit includes palette changes;
schedule palette and panel phases separately when their combined payload would
exceed it. CHR-ROM is not a writable runtime decompression destination.

Assign RAM through the actual project's memory map/linker conventions. Do not
invent a free zero-page range or alias actor/audio memory. Integrate UI glyphs
into the title tile dictionary before final serialization, produce named tile
IDs, and verify the combined tile count. Do not assume earlier free tile counts
still apply after regenerating the logo and font. Add only missing glyphs such
as slash and the cursor; no second general-purpose font bank is required.

The practical VBlank budget must include the existing OAM DMA, register handling,
queue decoding, any pre-transfer work and DMA interference. Keep the current
budget-test limits; byte count alone is not a cycle proof. Require completion of
all PPU/OAM work before rendering resumes under the worst tested NTSC path.
Do not gain time by lowering game simulation frequency or disabling audio ticks.

## 10. Final Silicon Forge menu remains a separate milestone

Preserve the user's sequencing: integrate the full campaign first, then the final
cheat menu. This title task does not substitute a cheat menu for missing stages.

The intended gameplay sequence remains:

UP, UP, DOWN, DOWN, LEFT, RIGHT, LEFT, RIGHT, B, A, START.

Use distinct press edges. A held direction is one code entry. Consume the final
Start before the normal pause handler. On success, pause world simulation and
open the English SILICON FORGE menu; BACK restores the exact paused scene.

Preserve the established dark, bordered terminal style with highlighted selection,
green/amber accents, decimal values and ON/OFF toggles. Group the final options
as PLAYER, WEAPONS, STAGE SELECT, SCENE SELECT, ENDINGS, SOUND TEST and RESET CHEATS.
Expose only implemented actions; stage/cutscene navigation uses the real campaign
router and its necessary state, never a direct jump into unmapped content. Keep
chapter-specific weapon and co-op rules. The title panel and cheat screen can
share glyphs/queue infrastructure, but not incompatible live state.

## 11. Acceptance tests required before calling the menu implemented

The following are required future tests, not tests executed by this document:

1. Rebuild title assets twice and verify identical hashes. Decode CHR/nametable
   back to pixels, check the 256-tile cap and verify panel/text bounds.
2. Boot the actual native build without memory injection. Capture the palette,
   panel rows, both labels and ready cursor using controller-level instrumentation.
3. Confirm every panel-interior pixel is opaque in the composition and no sprites
   cross it. Check legibility with overscan crop and more than one display palette.
4. Press Start separately in every entrance phase. Each press finishes the menu,
   requires release, and never starts or pauses gameplay accidentally.
5. Exercise wraparound, held repeats, simultaneous opposites, simultaneous A/Start,
   OPTIONS entry/exit and SOUND off/on with a tone already playing.
6. Enter START GAME and compare initial lives, score, route, weapons and first-stage
   state with the existing CP0004 startup; Flow_NewGame must execute exactly once.
7. Return to the title after game over and after a stage scene with a pending HUD,
   column or boss upload. Prove no stale upload changes the panel or logo.
8. Measure the heaviest title NMI with OAM, queue decoding and actual audio policy.
   Reject an oversized queue as a negative control; do not relax existing limits.
9. Re-run the current native integration, combat, stage-one, campaign-router and
   VBlank tests, documenting any test updates needed for the new Start semantics.
10. Verify cold boot, reset and a long idle session. Record ROM hash, emulator/core,
    test inputs, screenshots and whether physical hardware/PAL were actually tested.

Gameplay tests that previously pressed Start once may need a wait or a separate
fast-forward/release/confirm sequence. Changing those inputs is legitimate;
removing their assertions is not. A completed title test does not validate the
four chapters, converted soundtrack, co-op, story or endings.

## 12. Implementation handoff and reporting

Implement in the existing native project, not a separate title demo ROM. Preserve
existing build paths and sources. Keep original commercial inputs and regenerated
source assets within the established private/public boundary; public releases
remain IPS under the owner's standing rule.

The implementation change should contain the title module, generator changes,
build integration and tests together. Report exactly which controls, transitions,
audio behavior and regression cases passed. Keep gameplay coverage unchanged
unless gameplay was actually implemented and tested. Do not label this document
or an asset preview as a new playable checkpoint.

## Technical references

Repository evidence is pinned by the blob hashes in section 1. Hardware rules
were checked against these NESdev technical references on 2026-10-25:

- PPU programmer reference: https://www.nesdev.org/wiki/PPU_programmer_reference
- PPU registers: https://www.nesdev.org/wiki/PPU_registers
- PPU attribute tables: https://www.nesdev.org/wiki/PPU_attribute_tables
- PPU OAM: https://www.nesdev.org/wiki/PPU_OAM
- DMA: https://www.nesdev.org/wiki/DMA
- MMC5: https://www.nesdev.org/wiki/MMC5

The timing, layout, queue size and ROM/RAM caps above are this project's proposed
implementation contract. They are not statements that a new ROM was built,
measured or visually approved in this documentation change.
