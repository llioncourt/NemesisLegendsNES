# CP0009 - native cadence hotfix and measured evidence

## Original complaint and baseline

The user supplied a CP0008 gameplay screenshot with a black background, red
opening enemies and a simplified text HUD. The user reported unplayably fast
combat. This is a direct defect report, not an approval. The visual system
remains incomplete even after this patch.

Source audit finds no duplicated gameplay tick: Main only executes FrameGame
on the NMI-ready handshake, and E062 initialized to 1 in MSX
`p00:466A-468C` yields one background column per eight logical frames.
At original 60Hz, an idle ship suffers its first collision after 116 video
frames on pinned FCEUmm. The current speed is unforgiving to new players.

## Incremental code change

`src/native_pacing.s` allocates three bytes after the existing campaign
BSS $0500 and stage2 BSS $0510; the new addresses are $0520..$0522.
`src/native_kernel.s` processes SELECT every rendered frame; it cycles 30,
40 and 60Hz gameplay simulation. The HUD shows SPD:30/40/60. Existing pause
semantics and title are preserved. Physical video refresh and donor APU
still run at 60Hz in every mode. Game timers, scroll, actor motion, shots and
boss scripts share the selected *logical* clock and slow together: this is an
accessibility extension, explicitly NOT the original MSX time scale.

Mode 0 is cold-reset default 30Hz (one update every two rendered frames).
Mode 1 is 40Hz (two updates for each three rendered frames).
Mode 2 is 60Hz source-reference (update every video frame).

A one-video-frame A edge on a skipped simulation step is latched and consumed
by the next logic step, preventing lost upgrades. SELECT works during play or
while paused. A title return keeps the preference within the power session;
cold boot restores mode 0. No game clock or mapper hardware is modified.

## Verification

`tools/test_pacing_native.py` is a controller-level test on the actual unmodified
FCEUmm core: 120 video frames produce 60/80/120 logical frames for modes
30/40/60; no skipped NMIs; HUD, SELECT cycle, pause and single-frame A press
are checked. First collision with no controller input is 242 video frames at
30Hz versus 116 at 60Hz. This is only a reproducible survival margin, not
complete playability proof.

CP0008 source-route regressions are reexecuted at mode 60 (selected by real
controller events) and preserve the MSX-derived 720-frame boss timeout and
900-frame rain. No new stage, music, art or enemy is introduced. The rest of
the four-game coverage remains unchanged.

## Remaining work

Source-frame visual parity of stage 1, sprite shapes/palettes, authentic power-up
meter, stage 3 onward, bonus10-12, the other three complete MSX chapters,
cutscenes, native soundtrack, Konami Code, full campaign tests, physical/PAL
verification and IPS public distribution. Prioritize those over more title
polish. 
