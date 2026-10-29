# MSX-only music arranged for the NES (Phase 5, music)

Owner's rule (docs/DECISIONS.md, Music): music that exists in a NES game uses the NES version
(docs/MUSIC_CHOICE.md); the MSX-only music is arranged twice, for the plain APU and for the
APU plus the two MMC5 pulse channels, and the APU version is a real arrangement, not the MMC5
version with channels muted. This page is the arrangement report (voice maps, choices, checks);
the note data, the tools and the audio renders stay private (they are transcriptions of the
original music). Engine-neutral data format: docs/MUSIC_FORMAT.md.


Every Legends music asset whose source is MSX (`music_match/music_assets.json`, source kind MSX) arranged twice: a plain-APU remix (pulse 1, pulse 2, triangle, noise) and an MMC5 version (the APU channels plus the two MMC5 pulses). Format: `FORMAT.md`; files `<asset_id>.json`; renders `wav/<asset_id>_apu.wav`, `_mmc5.wav` and `_msx.wav` (the MSX original from the trace), 44.1 kHz mono, APU and MMC5 at the same gain. Pilot (3 tunes, first pass, kept for reference): `pilot/`.

Re-run: `python3 tools/msx_extract.py` (runs the games' own sound engines, `traces/`), `python3 tools/arrange.py` (all; `--pilot` for the pilot), `python3 tools/report.py`. The rules are in the docstrings of `tools/voices.py` (voices, events, roles) and `tools/arrange.py` (channel mapping, remix, timbre); the synthesiser is `tools/nesynth.py`.

## How the voices were arranged

- Voices: PSG 1-3 tone, PSG 1-3 noise, SCC 1-5, each as note events with exact per-frame volume and pitch macros from the driver output; tempo = the MSX note grid (frames per row); loop = the frame from which the MSX output repeats exactly.
- Roles: drums (noise; tone-sweep drums), doubles (unison/octave copies), echoes (delayed copies), parallel harmony, bass (lowest), accompaniment figures (arp), pads, lead (loud, high, varied rhythm), counter-melodies.
- MMC5: bass on the triangle, lead/counter/harmony on pulse 1, pulse 2, MMC5 pulse 1, MMC5 pulse 2 in that order, drums on noise; doubles merged into the voice they double; extra voices merged where they never sound together, echoes in the rests of their voice, else folded as arpeggio.
- APU remix: pulse 1 = lead (+ its echo in the lead's rests), triangle = bass, noise = drums, pulse 2 = the first counter-melody whole, the other voices in its rests, and fast 1-frame arpeggios of the other voices' notes over its notes of 8 frames or more; what is still not heard goes into the lead's rests on pulse 1.
- Duty from the SCC waveform brightness (50 % / 25 % / 12.5 %), PSG -> 50 %; volumes from the MSX volume curves; triangle articulated by length (note ends where the MSX volume falls below 30 % of its peak for good); noise periods from the PSG noise period, tone-sweep drums -> noise by their start pitch.
- Coverage = share of a voice's sounding frames where its note (pitch class) sounds on some channel of that version (its own channel, an arpeggio step, or another channel in unison); drums: frames where the noise channel plays. Triangle coverage below 1 is the length articulation.

## Counts

| | count |
|---|---|
| MSX-source assets arranged | 70 |
| Nemesis (music / jingle) | 10 (3 / 7) |
| Nemesis 2 (music / jingle) | 24 (15 / 9) |
| Salamander (music / jingle) | 11 (6 / 5) |
| Nemesis 3 (music / jingle) | 25 (20 / 5) |
| looping / ending by themselves | 42 / 28 |
| MSX voices arranged | 446 |
| voices by role | counter 90, drums 89, bass 63, lead 58, pad 51, double 35, echo 29, arp 26, parallel 5 |
| MMC5 channels in use (tunes) | 2 ch: 6, 3 ch: 6, 4 ch: 8, 5 ch: 18, 6 ch: 32 |
| MMC5: voices merged (never together) / folded (arpeggio) | 1 / 15 |
| APU coverage of musical voices (not drums/echo/double): mean / min | 0.97 / 0.16 |
| MMC5 coverage of musical voices: mean / min | 0.99 / 0.33 |
| instruments (sum over files) | 11401 |

## Checks (`tools/validate.py`, `traces/validate.json`)

- 73 files (70 + 3 pilot): events sorted and not overlapping, instruments defined, every note inside the channel's range, noise indexes 0-15, loops inside the tune; problems: 0.
- MSX voices placed whole on their own MMC5 channel: 290; the compiled NES pitch equals the MSX pitch on 100.00 % of their sounding frames on average (arpeggio frames and octave-lifted sub-A1 frames aside).
- Renders: 210 WAVs in `wav/` (8918 s in all), each the arranged pass (at most 120 s), none silent.

## Voices the APU remix keeps only in part (coverage < 0.70; check by ear)

- nl.music.nemesis2_final_core_destroyed: SCC3 (arp) 0.35, pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames)
- nl.music.nemesis2_boss_beaten: PSG3 (bass) 0.56, triangle (length articulation of a sweep on the triangle)
- nl.music.nemesis2_boss_event_piece_blows_up: PSG1 (bass) 0.56, triangle (length articulation of a sweep on the triangle)
- nl.music.nemesis3_at_the_start_of_stages_3_and_5: SCC4 (counter) 0.70, pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames)
- nl.music.nemesis3_ship_destroyed: SCC4 (pad) 0.16, pulse2 (folded: in the rests of PSG2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests)
- nl.music.nemesis3_ship_destroyed: SCC5 (counter) 0.64, pulse2 (folded: in the rests of PSG2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests)
- nl.music.nemesis3_title: PSG1 (counter) 0.50, pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames)

## Per tune

### nl.music.nemesis_stage_4_eruption

Nemesis 0x13, jingle; 96 frames (1.6 s), no loop (ends); 2 frames per row (100 % of the onsets on the grid); 17 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |
| PSG3n | drums | noise | 1.0 | noise | 1.0 |

### nl.music.nemesis_stage_5_bgm

Nemesis 0x22, music; 1697 frames (28.3 s), loops to frame 304 (row 38); 8 frames per row (100 % of the onsets on the grid); 40 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| PSG2 | bass | triangle | 1.0 | triangle | 1.0 |

### nl.music.nemesis_bonus_stage_bgm

Nemesis 0x24, music; 2305 frames (38.4 s), loops to frame 384 (row 64); 6 frames per row (100 % of the onsets on the grid); 77 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| PSG2 | bass | triangle | 1.0 | triangle | 1.0 |

### nl.music.nemesis_presentation_tune

Nemesis 0x26, music; 1298 frames (21.6 s), no loop (ends); 6 frames per row (100 % of the onsets on the grid); 78 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| PSG2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| PSG3 | bass | triangle | 0.987 | triangle | 0.987 |

### nl.music.nemesis_stage_1_eruption

Nemesis 0x32, jingle; 126 frames (2.1 s), no loop (ends); 1 frames per row (100 % of the onsets on the grid); 29 instruments. notes below A1 lifted by an octave on the pulses (pulse2: 2).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | bass | triangle | 1.0 | triangle | 1.0 |
| PSG3 | lead | pulse1 | 1.0 | pulse1 | 1.0 |

### nl.music.nemesis_ending

Nemesis 0x38, jingle; 562 frames (9.4 s), no loop (ends); 4 frames per row (96 % of the onsets on the grid); 8 instruments. bass an octave down on the triangle.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | arp | pulse2 | 1.0 | pulse2 | 1.0 |
| PSG2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| PSG3 | bass | triangle (octave down) | 1.0 | triangle (octave down) | 1.0 |

### nl.music.nemesis_core_destroyed_ending_explosion

Nemesis 0x3B, jingle; 90 frames (1.5 s), no loop (ends); 1 frames per row (100 % of the onsets on the grid); 7 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | pad | pulse2 | 1.0 | pulse2 | 1.0 |
| PSG2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |

### nl.music.nemesis_screen_crumble

Nemesis 0x3E, jingle; 290 frames (4.8 s), no loop (ends); 1 frames per row (100 % of the onsets on the grid); 3 instruments. bass an octave down on the triangle.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | bass | triangle (octave down) | 1.0 | triangle (octave down) | 1.0 |
| PSG2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| PSG3n | drums | noise | 1.0 | noise | 1.0 |

### nl.music.nemesis_stage_cleared

Nemesis 0x41, jingle; 119 frames (2.0 s), no loop (ends); 1 frames per row (100 % of the onsets on the grid); 7 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | bass | triangle | 1.0 | triangle | 1.0 |

### nl.music.nemesis_ending_2

Nemesis 0x44, jingle; 140 frames (2.3 s), no loop (ends); 1 frames per row (100 % of the onsets on the grid); 12 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | bass | triangle | 1.0 | triangle | 1.0 |
| PSG2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| PSG3n | drums | noise | 1.0 | noise | 1.0 |

### nl.music.nemesis2_emergency_warning_alarm

Nemesis 2 0x28, jingle; 676 frames (11.3 s), no loop (ends); 6 frames per row (50 % of the onsets on the grid); 4 instruments. no bass voice; the triangle takes PSG1.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | pad | triangle | 1.0 | triangle | 1.0 |
| SCC1 | pad | pulse1 | 1.0 | pulse1 | 1.0 |

### nl.music.nemesis2_stage_0_bgm

Nemesis 2 0x29, music; 2881 frames (48.0 s), loops to frame 340 (row 68); 5 frames per row (92 % of the onsets on the grid); 236 instruments. notes below A1 lifted by an octave on the pulses (pulse2: 52, mmc5_pulse2: 64).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG2 | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | arp | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 | 1.0 |
| SCC3 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC4 | pad | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.99 | mmc5_pulse1 | 1.0 |
| SCC5 | pad | pulse2 | 1.0 | pulse2 | 1.0 |

### nl.music.nemesis2_stage_start_theme

Nemesis 2 0x2B, music; 3969 frames (66.2 s), loops to frame 8 (row 1); 8 frames per row (86 % of the onsets on the grid); 202 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG2 | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | counter | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC3 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC4 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC5 | counter | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 1.0 | mmc5_pulse2 | 1.0 |

### nl.music.nemesis2_stage_1_bgm

Nemesis 2 0x2C, music; 3841 frames (64.0 s), loops to frame 8 (row 1); 8 frames per row (100 % of the onsets on the grid); 219 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG2 | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3 | bass | triangle | 0.961 | triangle | 0.961 |
| SCC2 | double of PSG3 | merged into triangle (double of PSG3 (onsets 0.98, delay 0 frames, -12 semitones)) | 0.961 | merged into triangle (double of PSG3 (onsets 0.98, delay 0 frames, -12 semitones)) | 0.961 |
| SCC3 | pad | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | arp | pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.993 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis2_stage_2_bgm

Nemesis 2 0x2D, music; 3550 frames (59.2 s), loops to frame 336 (row 48); 7 frames per row (94 % of the onsets on the grid); 238 instruments. notes below A1 lifted by an octave on the pulses (pulse1: 6, pulse2: 3, mmc5_pulse2: 42).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG2 | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | arp | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.939 | mmc5_pulse2 | 1.0 |
| SCC3 | arp | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.832 | mmc5_pulse1 | 1.0 |
| SCC4 | arp | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC5 | lead | pulse1 | 1.0 | pulse1 | 1.0 |

### nl.music.nemesis2_stage_3_bgm

Nemesis 2 0x2E, music; 1155 frames (19.2 s), loops to frame 2 (row 0, +2 frames); 8 frames per row (85 % of the onsets on the grid); 42 instruments. no bass voice; the triangle takes SCC5.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| PSG3 | double of PSG2 | merged into pulse1 (double of PSG2 (onsets 1.00, delay 1 frames, +12 semitones)) | 1.0 | merged into pulse1 (double of PSG2 (onsets 1.00, delay 1 frames, +12 semitones)) | 1.0 |
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | double of SCC2 | merged into pulse2 (double of SCC2 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 | merged into pulse2 (double of SCC2 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 |
| SCC4 | double of SCC5 | merged into triangle (octave down) (double of SCC5 (onsets 1.00, delay 0 frames, +0 semitones)) | 0.947 | merged into triangle (octave down) (double of SCC5 (onsets 1.00, delay 0 frames, +0 semitones)) | 0.947 |
| SCC5 | counter | triangle (octave down) | 0.947 | triangle (octave down) | 0.947 |

### nl.music.nemesis2_stage_5_bgm

Nemesis 2 0x30, music; 4993 frames (83.2 s), loops to frame 8 (row 2); 4 frames per row (94 % of the onsets on the grid); 474 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG2 | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC3 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC4 | echo of SCC5 | pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.947 | mmc5_pulse2 | 1.0 |
| SCC5 | arp | pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.95 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis2_stage_4_bgm

Nemesis 2 0x31, music; 3421 frames (57.0 s), loops to frame 42 (row 7); 6 frames per row (93 % of the onsets on the grid); 234 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG2 | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | echo of SCC2 | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.91 | mmc5_pulse2 | 1.0 |
| SCC4 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.937 | mmc5_pulse1 | 1.0 |
| SCC5 | lead | pulse1 | 1.0 | pulse1 | 1.0 |

### nl.music.nemesis2_stage_6_bgm

Nemesis 2 0x32, music; 3841 frames (64.0 s), loops to frame 0 (row 0); 1 frames per row (100 % of the onsets on the grid); 262 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG2 | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | echo of SCC2 | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | double of SCC4 | merged into pulse1 (double of SCC4 (onsets 0.91, delay 0 frames, +0 semitones)) | 1.0 | merged into pulse1 (double of SCC4 (onsets 0.91, delay 0 frames, +0 semitones)) | 1.0 |

### nl.music.nemesis2_stage_7_bgm

Nemesis 2 0x33, music; 2561 frames (42.7 s), loops to frame 320 (row 40); 8 frames per row (99 % of the onsets on the grid); 179 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG2 | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC3 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC4 | double of PSG3 | merged into triangle (double of PSG3 (onsets 0.88, delay 0 frames, -12 semitones)) | 1.0 | merged into triangle (double of PSG3 (onsets 0.88, delay 0 frames, -12 semitones)) | 1.0 |
| SCC5 | counter | pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis2_boss_theme

Nemesis 2 0x34, music; 1537 frames (25.6 s), loops to frame 384 (row 128); 3 frames per row (100 % of the onsets on the grid); 113 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG2 | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | double of SCC4 | merged into pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames) (double of SCC4 (onsets 0.80, delay 0 frames, +0 semitones)) | 0.883 | merged into mmc5_pulse1 (double of SCC4 (onsets 0.80, delay 0 frames, +0 semitones)) | 1.0 |
| SCC3 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC4 | arp | pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames) | 0.883 | mmc5_pulse1 | 1.0 |
| SCC5 | lead | pulse1 | 1.0 | pulse1 | 1.0 |

### nl.music.nemesis2_boss_interior_final_core_theme

Nemesis 2 0x35, music; 793 frames (13.2 s), loops to frame 6 (row 6); 1 frames per row (100 % of the onsets on the grid); 86 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG2 | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | double of SCC3 | merged into pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) (double of SCC3 (onsets 1.00, delay 0 frames, +12 semitones)) | 0.977 | merged into mmc5_pulse1 (double of SCC3 (onsets 1.00, delay 0 frames, +12 semitones)) | 1.0 |
| SCC3 | arp | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.977 | mmc5_pulse1 | 1.0 |
| SCC4 | pad | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | pad | pulse2 | 1.0 | pulse2 | 1.0 |

### nl.music.nemesis2_secret_stages_bgm

Nemesis 2 0x36, music; 3050 frames (50.8 s), loops to frame 12 (row 2); 6 frames per row (98 % of the onsets on the grid); 63 instruments. no bass voice; the triangle takes SCC5.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG2 | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3 | arp | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC2 | double of PSG3 | merged into pulse2 (double of PSG3 (onsets 0.82, delay 0 frames, -36 semitones)) | 1.0 | merged into pulse2 (double of PSG3 (onsets 0.82, delay 0 frames, -36 semitones)) | 1.0 |
| SCC3 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC4 | double of SCC3 | merged into pulse1 (double of SCC3 (onsets 0.97, delay 0 frames, +0 semitones)) | 1.0 | merged into pulse1 (double of SCC3 (onsets 0.97, delay 0 frames, +0 semitones)) | 1.0 |
| SCC5 | counter | triangle (octave down) | 1.0 | triangle (octave down) | 1.0 |

### nl.music.nemesis2_interior_ending

Nemesis 2 0x37, jingle; 674 frames (11.2 s), loops to frame 0 (row 0); 1 frames per row (100 % of the onsets on the grid); 4 instruments. no bass voice; the triangle takes SCC5.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | counter | triangle (octave down) | 1.0 | triangle (octave down) | 1.0 |

### nl.music.nemesis2_final_core_destroyed

Nemesis 2 0x39, jingle; 629 frames (10.5 s), loops to frame 0 (row 0); 4 frames per row (100 % of the onsets on the grid); 24 instruments. notes below A1 lifted by an octave on the pulses (pulse1: 182, pulse2: 42, mmc5_pulse1: 84).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| SCC1 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | parallel of SCC1 | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC3 | arp | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 0.347 | mmc5_pulse1 | 1.0 |
| SCC4 | arp | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC5 | double of SCC4 | merged into pulse2 (double of SCC4 (onsets 1.00, delay 0 frames, -12 semitones)) | 1.0 | merged into pulse2 (double of SCC4 (onsets 1.00, delay 0 frames, -12 semitones)) | 1.0 |

### nl.music.nemesis2_boss_beaten

Nemesis 2 0x3A, jingle; 879 frames (14.7 s), loops to frame 205 (row 205); 1 frames per row (100 % of the onsets on the grid); 11 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG3 | bass | triangle | 0.565 | triangle | 0.565 |
| SCC1 | pad | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC4 | double of SCC1 | merged into pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) (double of SCC1 (onsets 0.86, delay 0 frames, +0 semitones)) | 1.0 | merged into mmc5_pulse1 (double of SCC1 (onsets 0.86, delay 0 frames, +0 semitones)) | 1.0 |
| SCC5 | pad | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 | 1.0 |

### nl.music.nemesis2_boss_event_piece_blows_up

Nemesis 2 0x3B, jingle; 193 frames (3.2 s), no loop (ends); 9 frames per row (50 % of the onsets on the grid); 4 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | bass | triangle | 0.565 | triangle | 0.565 |
| PSG2 | double of PSG1 | merged into triangle (double of PSG1 (onsets 1.00, delay 0 frames, +0 semitones)) | 0.565 | merged into triangle (double of PSG1 (onsets 1.00, delay 0 frames, +0 semitones)) | 0.565 |
| SCC1 | double of SCC2 | merged into pulse1 (double of SCC2 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 | merged into pulse1 (double of SCC2 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 |
| SCC2 | pad | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC3 | double of PSG1 | merged into triangle (double of PSG1 (onsets 1.00, delay 0 frames, +0 semitones)) | 0.565 | merged into triangle (double of PSG1 (onsets 1.00, delay 0 frames, +0 semitones)) | 0.565 |
| SCC4 | double of PSG1 | merged into triangle (double of PSG1 (onsets 1.00, delay 0 frames, +0 semitones)) | 0.565 | merged into triangle (double of PSG1 (onsets 1.00, delay 0 frames, +0 semitones)) | 0.565 |

### nl.music.nemesis2_metalion_flies_off

Nemesis 2 0x3C, jingle; 162 frames (2.7 s), no loop (ends); 2 frames per row (100 % of the onsets on the grid); 13 instruments. no bass voice; the triangle takes SCC5.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| SCC2 | pad | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | pad | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC4 | pad | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC5 | pad | triangle | 1.0 | triangle | 1.0 |

### nl.music.nemesis2_metalion_destroyed

Nemesis 2 0x3D, jingle; 111 frames (1.9 s), no loop (ends); 3 frames per row (98 % of the onsets on the grid); 29 instruments. notes below A1 lifted by an octave on the pulses (pulse1: 1, pulse2: 1, mmc5_pulse1: 1, mmc5_pulse2: 3).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| PSG2 | echo of PSG1 | pulse1 (echo in the lead's rests) | 0.607 | pulse1 (echo in the rests of PSG1) | 0.607 |
| PSG3n | drums | noise | 1.0 | noise | 1.0 |
| SCC1 | counter | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 1.0 | mmc5_pulse2 | 1.0 |
| SCC2 | counter | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC3 | bass | triangle | 0.933 | triangle | 1.0 |
| SCC4 | pad | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.933 | mmc5_pulse2 (folded: arpeggio with SCC1, and in its rests) | 1.0 |
| SCC5 | counter | pulse2 | 1.0 | pulse2 | 1.0 |

### nl.music.nemesis2_game_start

Nemesis 2 0x3E, jingle; 355 frames (5.9 s), no loop (ends); 2 frames per row (96 % of the onsets on the grid); 101 instruments. notes below A1 lifted by an octave on the pulses (mmc5_pulse2: 1).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | pad | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 (folded: arpeggio with SCC3, and in its rests) | 0.917 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | pad | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 (folded: arpeggio with SCC3, and in its rests) | 1.0 |
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC1 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | pad | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 0.905 | mmc5_pulse2 | 1.0 |
| SCC4 | double of SCC5 | merged into pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) (double of SCC5 (onsets 0.80, delay 0 frames, +0 semitones)) | 1.0 | merged into mmc5_pulse1 (double of SCC5 (onsets 0.80, delay 0 frames, +0 semitones)) | 1.0 |
| SCC5 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis2_story

Nemesis 2 0x3F, music; 8529 frames (142.2 s), no loop (ends); 10 frames per row (0 % of the onsets on the grid); 521 instruments. notes below A1 lifted by an octave on the pulses (pulse1: 1, pulse2: 6, mmc5_pulse2: 4).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | bass | triangle | 0.989 | triangle | 0.989 |
| PSG2 | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3 | double of PSG1 | merged into triangle (double of PSG1 (onsets 0.98, delay 0 frames, -12 semitones)) | 0.989 | merged into triangle (double of PSG1 (onsets 0.98, delay 0 frames, -12 semitones)) | 0.989 |
| SCC1 | pad | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.991 | mmc5_pulse2 (folded: arpeggio with SCC4, and in its rests) | 1.0 |
| SCC2 | pad | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | pad | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC4 | pad | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.991 | mmc5_pulse2 | 1.0 |
| SCC5 | pad | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 0.999 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis2_interlude_after_stage_7

Nemesis 2 0x40, music; 6123 frames (102.0 s), no loop (ends); 5 frames per row (94 % of the onsets on the grid); 154 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG2 | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | double of SCC3 | merged into pulse1 (double of SCC3 (onsets 0.85, delay 0 frames, +0 semitones)) | 1.0 | merged into pulse1 (double of SCC3 (onsets 0.85, delay 0 frames, +0 semitones)) | 1.0 |
| SCC3 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC4 | arp | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC5 | arp | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis2_true_ending

Nemesis 2 0x41, music; 6066 frames (101.1 s), no loop (ends); 10 frames per row (77 % of the onsets on the grid); 229 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | bass | triangle | 1.0 | triangle | 1.0 |
| PSG3 | double of PSG2 | merged into triangle (double of PSG2 (onsets 1.00, delay 0 frames, -12 semitones)) | 1.0 | merged into triangle (double of PSG2 (onsets 1.00, delay 0 frames, -12 semitones)) | 1.0 |
| SCC1 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC2 | double of SCC1 | merged into pulse1 (double of SCC1 (onsets 0.90, delay 0 frames, +0 semitones)) | 1.0 | merged into pulse1 (double of SCC1 (onsets 0.90, delay 0 frames, +0 semitones)) | 1.0 |
| SCC3 | echo of SCC1 | pulse1 (echo in the lead's rests) | 0.838 | mmc5_pulse2 | 1.0 |
| SCC4 | parallel of SCC5 | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC5 | pad | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis2_game_over

Nemesis 2 0x42, jingle; 347 frames (5.8 s), no loop (ends); 4 frames per row (100 % of the onsets on the grid); 51 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | bass | triangle | 1.0 | triangle | 1.0 |
| PSG2 | double of PSG1 | merged into triangle (double of PSG1 (onsets 1.00, delay 0 frames, +12 semitones)) | 1.0 | merged into triangle (double of PSG1 (onsets 1.00, delay 0 frames, +12 semitones)) | 1.0 |
| PSG3 | pad | pulse2 (folded: in the rests of SCC1; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC1 | parallel of SCC2 | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC2 | pad | pulse2 (folded: in the rests of SCC1; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 | 1.0 |
| SCC3 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC4 | double of SCC3 | merged into pulse1 (double of SCC3 (onsets 0.99, delay 0 frames, +0 semitones)) | 1.0 | merged into pulse1 (double of SCC3 (onsets 0.99, delay 0 frames, +0 semitones)) | 1.0 |

### nl.music.salamander_stage_2

Salamander 0x1C, music; 3361 frames (56.0 s), loops to frame 1152 (row 144); 8 frames per row (87 % of the onsets on the grid); 318 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | double of PSG2 | merged into triangle (double of PSG2 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 | merged into triangle (double of PSG2 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 0.985 | mmc5_pulse1 | 1.0 |

### nl.music.salamander_stage_4

Salamander 0x1D, music; 1695 frames (28.2 s), loops to frame 336 (row 48); 7 frames per row (86 % of the onsets on the grid); 134 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 0.901 | mmc5_pulse1 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | double of SCC4 | merged into pulse1 (double of SCC4 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 | merged into pulse1 (double of SCC4 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 |

### nl.music.salamander_hidden_item_result

Salamander 0x22, music; 1936 frames (32.3 s), loops to frame 653 (row 65, +3 frames); 10 frames per row (76 % of the onsets on the grid); 147 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.999 | mmc5_pulse1 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | echo of SCC4 | pulse1 (echo in the lead's rests) | 0.708 | mmc5_pulse2 | 1.0 |

### nl.music.salamander_boss_destroyed

Salamander 0x24, jingle; 283 frames (4.7 s), no loop (ends); 1 frames per row (100 % of the onsets on the grid); 71 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| SCC1 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC2 | arp | pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC3 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC4 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC5 | double of SCC4 | merged into triangle (double of SCC4 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 | merged into triangle (double of SCC4 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 |

### nl.music.salamander_take_off

Salamander 0x28, jingle; 122 frames (2.0 s), no loop (ends); 2 frames per row (95 % of the onsets on the grid); 18 instruments. notes below A1 lifted by an octave on the pulses (pulse2: 1, mmc5_pulse2: 1).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.732 | mmc5_pulse2 (folded: arpeggio with SCC4, and in its rests) | 1.0 |
| PSG2 | bass | triangle | 1.0 | triangle | 1.0 |
| PSG3n | drums | noise | 1.0 | noise | 1.0 |
| SCC1 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC4 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 1.0 | mmc5_pulse2 | 1.0 |
| SCC5 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 1.0 | pulse1 (merged: never sounds with SCC1) | 1.0 |

### nl.music.salamander_story_opening_tune

Salamander 0x2E, jingle; 5350 frames (89.2 s), no loop (ends); 7 frames per row (95 % of the onsets on the grid); 159 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | double of SCC2 | merged into triangle (double of SCC2 (onsets 1.00, delay 0 frames, +0 semitones)) | 0.99 | merged into triangle (double of SCC2 (onsets 1.00, delay 0 frames, +0 semitones)) | 0.99 |
| SCC2 | bass | triangle | 0.99 | triangle | 0.99 |
| SCC3 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | echo of SCC4 | pulse1 (echo in the lead's rests) | 0.645 | mmc5_pulse1 | 1.0 |

### nl.music.salamander_between_stages

Salamander 0x2F, music; 1769 frames (29.5 s), loops to frame 616 (row 616); 1 frames per row (100 % of the onsets on the grid); 101 instruments. notes below A1 lifted by an octave on the pulses (pulse1: 14, pulse2: 14).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | double of PSG2 | merged into triangle (double of PSG2 (onsets 1.00, delay 0 frames, +12 semitones)) | 1.0 | merged into triangle (double of PSG2 (onsets 1.00, delay 0 frames, +12 semitones)) | 1.0 |
| SCC3 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC4 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC5 | parallel of SCC4 | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.86 | mmc5_pulse1 | 1.0 |

### nl.music.salamander_ending_without_nemesis_2

Salamander 0x30, music; 3475 frames (57.9 s), loops to frame 1170 (row 1170); 1 frames per row (100 % of the onsets on the grid); 181 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | double of SCC3 | merged into triangle (double of SCC3 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 | merged into triangle (double of SCC3 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 |
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | echo of SCC4 | pulse1 (echo in the lead's rests) | 0.574 | mmc5_pulse1 | 1.0 |

### nl.music.salamander_good_ending

Salamander 0x31, music; 4129 frames (68.8 s), loops to frame 2592 (row 648); 4 frames per row (89 % of the onsets on the grid); 329 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC4 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 0.992 | mmc5_pulse1 | 1.0 |
| SCC5 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.986 | mmc5_pulse2 | 1.0 |

### nl.music.salamander_intro_window

Salamander 0x34, jingle; 48 frames (0.8 s), no loop (ends); 5 frames per row (88 % of the onsets on the grid); 11 instruments. no bass voice.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| PSG3 | counter | pulse2 (folded: in the rests of PSG2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 | 1.0 |
| SCC1 | counter | pulse2 (folded: in the rests of PSG2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |

### nl.music.salamander_the_ship_leaves

Salamander 0x48, jingle; 176 frames (2.9 s), no loop (ends); 1 frames per row (100 % of the onsets on the grid); 102 instruments. notes below A1 lifted by an octave on the pulses (pulse2: 5, mmc5_pulse2: 3).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | bass | triangle | 1.0 | triangle | 1.0 |
| PSG2 | counter | pulse2 (folded: in the rests of SCC1; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 | 1.0 |
| PSG3n | drums | noise | 1.0 | noise | 1.0 |
| SCC1 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC2 | counter | pulse2 (folded: in the rests of SCC1; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC3 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC4 | arp | pulse2 (folded: in the rests of SCC1; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 (folded: arpeggio with PSG2, and in its rests) | 0.333 |
| SCC5 | echo of SCC4 | pulse2 (folded: in the rests of SCC1; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 (echo in the rests of SCC4) | 0.968 |

### nl.music.nemesis3_at_the_start_of_stages_3_and_5

Nemesis 3 0x04, music; 4321 frames (72.0 s), loops to frame 424 (row 106); 4 frames per row (91 % of the onsets on the grid); 267 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | arp | pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames) | 0.724 | mmc5_pulse2 | 1.0 |
| SCC2 | bass | triangle | 0.837 | triangle | 0.837 |
| SCC3 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC4 | counter | pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames) | 0.697 | mmc5_pulse1 | 1.0 |
| SCC5 | lead | pulse1 | 1.0 | pulse1 | 1.0 |

### nl.music.nemesis3_the_bosses

Nemesis 3 0x05, music; 3066 frames (51.1 s), loops to frame 255 (row 255); 1 frames per row (100 % of the onsets on the grid); 127 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | echo of SCC4 | pulse1 (echo in the lead's rests) | 0.573 | mmc5_pulse2 | 1.0 |
| SCC2 | bass | triangle | 0.966 | triangle | 0.966 |
| SCC3 | pad | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.965 | mmc5_pulse1 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | counter | pulse2 | 1.0 | pulse2 | 1.0 |

### nl.music.nemesis3_stage_1

Nemesis 3 0x06, music; 3361 frames (56.0 s), loops to frame 7 (row 1); 7 frames per row (90 % of the onsets on the grid); 227 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | echo of SCC4 | pulse1 (echo in the lead's rests) | 0.839 | mmc5_pulse2 | 1.0 |
| SCC2 | bass | triangle | 0.982 | triangle | 0.99 |
| SCC3 | arp | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.933 | mmc5_pulse1 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | counter | pulse2 | 1.0 | pulse2 | 1.0 |

### nl.music.nemesis3_stage_2

Nemesis 3 0x07, music; 4225 frames (70.4 s), loops to frame 384 (row 64); 6 frames per row (92 % of the onsets on the grid); 299 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | echo of SCC3 | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.994 | mmc5_pulse2 | 1.0 |
| SCC2 | bass | triangle | 0.87 | triangle | 0.87 |
| SCC3 | arp | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.994 | mmc5_pulse1 | 1.0 |
| SCC4 | pad | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | pad | pulse2 | 1.0 | pulse2 | 1.0 |

### nl.music.nemesis3_stage_3

Nemesis 3 0x08, music; 5345 frames (89.1 s), loops to frame 776 (row 194); 4 frames per row (94 % of the onsets on the grid); 462 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC2 | bass | triangle | 0.888 | triangle | 0.889 |
| SCC3 | arp | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 0.992 | mmc5_pulse2 | 1.0 |
| SCC4 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC5 | counter | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.969 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis3_stage_5

Nemesis 3 0x0C, music; 2908 frames (48.5 s), loops to frame 144 (row 48); 3 frames per row (87 % of the onsets on the grid); 282 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | echo of SCC4 | pulse1 (echo in the lead's rests) | 0.554 | mmc5_pulse2 | 1.0 |
| SCC2 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC3 | counter | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.964 | mmc5_pulse1 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | counter | pulse2 | 1.0 | pulse2 | 1.0 |

### nl.music.nemesis3_stage_9

Nemesis 3 0x0D, music; 3025 frames (50.4 s), loops to frame 7 (row 1); 7 frames per row (92 % of the onsets on the grid); 274 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC2 | bass | triangle | 0.853 | triangle | 0.876 |
| SCC3 | counter | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 0.91 | mmc5_pulse2 | 1.0 |
| SCC4 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC5 | counter | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.75 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis3_stage_11

Nemesis 3 0x0E, music; 2738 frames (45.6 s), loops to frame 2513 (row 359); 7 frames per row (63 % of the onsets on the grid); 154 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | double of SCC4 | merged into pulse1 (double of SCC4 (onsets 0.95, delay 0 frames, +12 semitones)) | 1.0 | merged into pulse1 (double of SCC4 (onsets 0.95, delay 0 frames, +12 semitones)) | 1.0 |
| SCC2 | bass | triangle | 0.729 | triangle | 0.738 |
| SCC3 | arp | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.918 | mmc5_pulse1 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | counter | pulse2 | 1.0 | pulse2 | 1.0 |

### nl.music.nemesis3_game_over

Nemesis 3 0x3D, jingle; 499 frames (8.3 s), no loop (ends); 9 frames per row (97 % of the onsets on the grid); 83 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | echo of SCC2 | pulse1 (echo in the lead's rests) | 0.85 | mmc5_pulse2 | 1.0 |
| PSG2 | echo of SCC5 | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 1.0 | pulse2 (echo in the rests of SCC5) | 0.889 |
| PSG3 | echo of SCC4 | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.992 | mmc5_pulse1 (echo in the rests of SCC4) | 0.585 |
| SCC1 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC3 | echo of SCC2 | pulse1 (echo in the lead's rests) | 0.652 | pulse1 (echo in the rests of SCC2) | 0.695 |
| SCC4 | counter | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC5 | counter | pulse2 | 1.0 | pulse2 | 1.0 |

### nl.music.nemesis3_the_story

Nemesis 3 0x3E, music; 9521 frames (158.7 s), no loop (ends); 1 frames per row (100 % of the onsets on the grid); 761 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | pad | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.983 | mmc5_pulse2 (folded: arpeggio with PSG3, and in its rests) | 1.0 |
| PSG3 | pad | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 0.981 | mmc5_pulse2 | 1.0 |
| SCC1 | bass | triangle | 0.971 | triangle | 0.971 |
| SCC2 | double of SCC3 | merged into pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) (double of SCC3 (onsets 0.83, delay 0 frames, +12 semitones)) | 0.985 | merged into mmc5_pulse1 (double of SCC3 (onsets 0.83, delay 0 frames, +12 semitones)) | 1.0 |
| SCC3 | counter | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 0.985 | mmc5_pulse1 | 1.0 |
| SCC4 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC5 | lead | pulse1 | 1.0 | pulse1 | 1.0 |

### nl.music.nemesis3_the_on_board_computer_and_the

Nemesis 3 0x3F, music; 2148 frames (35.8 s), loops to frame 24 (row 6); 4 frames per row (99 % of the onsets on the grid); 129 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | arp | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| PSG2 | echo of PSG1 | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 (echo in the rests of PSG1) | 0.524 |
| PSG3 | echo of SCC1 | pulse1 (echo in the lead's rests) | 0.933 | pulse1 (echo in the rests of SCC1) | 0.913 |
| SCC1 | parallel of SCC4 | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC2 | bass | triangle | 0.991 | triangle | 0.991 |
| SCC3 | double of PSG1 | merged into pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) (double of PSG1 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 | merged into mmc5_pulse1 (double of PSG1 (onsets 1.00, delay 0 frames, +0 semitones)) | 1.0 |
| SCC4 | pad | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC5 | arp | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 | 1.0 |

### nl.music.nemesis3_the_ending

Nemesis 3 0x40, music; 1747 frames (29.1 s), loops to frame 18 (row 2); 9 frames per row (98 % of the onsets on the grid); 44 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | pad | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| PSG3 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC1 | double of PSG3 | merged into triangle (double of PSG3 (onsets 1.00, delay 0 frames, -12 semitones)) | 1.0 | merged into triangle (double of PSG3 (onsets 1.00, delay 0 frames, -12 semitones)) | 1.0 |
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | pad | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | echo of SCC4 | pulse1 (echo in the lead's rests) | 0.918 | pulse1 (echo in the rests of SCC4) | 0.918 |

### nl.music.nemesis3_the_ending_2

Nemesis 3 0x41, music; 4613 frames (76.9 s), loops to frame 2304 (row 256); 9 frames per row (98 % of the onsets on the grid); 268 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | echo of SCC2 | pulse1 (echo in the lead's rests) | 0.897 | mmc5_pulse2 | 1.0 |
| SCC1 | bass | triangle | 0.981 | triangle | 0.974 |
| SCC2 | pad | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC3 | pad | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC4 | arp | pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames) | 0.999 | mmc5_pulse1 | 1.0 |
| SCC5 | echo of SCC4 | pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames) | 0.999 | mmc5_pulse1 (echo in the rests of SCC4) | 0.641 |

### nl.music.nemesis3_the_ending_3

Nemesis 3 0x42, music; 5645 frames (94.1 s), loops to frame 1056 (row 132); 8 frames per row (77 % of the onsets on the grid); 585 instruments. notes below A1 lifted by an octave on the pulses (pulse2: 2, mmc5_pulse2: 2).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | echo of SCC4 | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 0.986 | pulse2 (echo in the rests of SCC4) | 0.938 |
| PSG3 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC1 | pad | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 | 1.0 |
| SCC2 | bass | triangle | 0.844 | triangle | 0.844 |
| SCC3 | arp | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 0.984 | mmc5_pulse2 (folded: arpeggio with SCC1, and in its rests) | 1.0 |
| SCC4 | pad | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC5 | pad | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 0.989 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis3_stage_6

Nemesis 3 0x44, music; 4855 frames (80.9 s), loops to frame 1432 (row 716); 2 frames per row (76 % of the onsets on the grid); 399 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC2 | bass | triangle | 0.964 | triangle | 0.964 |
| SCC3 | counter | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 0.992 | mmc5_pulse2 | 1.0 |
| SCC4 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC5 | counter | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 0.996 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis3_stage_7

Nemesis 3 0x45, music; 7355 frames (122.6 s), loops to frame 670 (row 95, +5 frames); 7 frames per row (92 % of the onsets on the grid); 268 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC2 | bass | triangle | 0.94 | triangle | 0.96 |
| SCC3 | arp | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) | 0.863 | mmc5_pulse2 | 1.0 |
| SCC4 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC5 | counter | pulse2 (folded: in the rests of SCC4; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.912 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis3_stage_8

Nemesis 3 0x46, music; 4609 frames (76.8 s), loops to frame 12 (row 3); 4 frames per row (88 % of the onsets on the grid); 215 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | echo of SCC4 | pulse1 (echo in the lead's rests) | 0.775 | mmc5_pulse2 | 1.0 |
| SCC2 | bass | triangle | 0.968 | triangle | 0.968 |
| SCC3 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | counter | pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames) | 0.811 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis3_stage_10

Nemesis 3 0x47, music; 4903 frames (81.7 s), loops to frame 1126 (row 187, +4 frames); 6 frames per row (87 % of the onsets on the grid); 317 instruments.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | echo of SCC4 | pulse1 (echo in the lead's rests) | 0.664 | mmc5_pulse2 | 1.0 |
| SCC2 | bass | triangle | 0.918 | triangle | 0.918 |
| SCC3 | counter | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.732 | mmc5_pulse1 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | counter | pulse2 | 1.0 | pulse2 | 1.0 |

### nl.music.nemesis3_ending

Nemesis 3 0x49, music; 9123 frames (152.1 s), loops to frame 3907 (row 781, +2 frames); 5 frames per row (87 % of the onsets on the grid); 541 instruments. notes below A1 lifted by an octave on the pulses (pulse2: 32).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | drums | noise | 1.0 | noise | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | echo of SCC2 | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.876 | mmc5_pulse2 (echo in the rests of SCC2) | 0.885 |
| PSG3 | pad | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.915 | mmc5_pulse1 | 1.0 |
| SCC1 | bass | triangle | 0.898 | triangle | 0.912 |
| SCC2 | pad | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.872 | mmc5_pulse2 (folded: arpeggio with SCC3, and in its rests) | 1.0 |
| SCC3 | pad | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.88 | mmc5_pulse2 | 1.0 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | counter | pulse2 | 1.0 | pulse2 | 1.0 |

### nl.music.nemesis3_the_story_2

Nemesis 3 0x4A, music; 2861 frames (47.7 s), loops to frame 220 (row 20); 11 frames per row (53 % of the onsets on the grid); 135 instruments. notes below A1 lifted by an octave on the pulses (pulse2: 2).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | double of SCC1 | merged into triangle (double of SCC1 (onsets 0.93, delay 0 frames, +0 semitones)) | 1.0 | merged into triangle (double of SCC1 (onsets 0.93, delay 0 frames, +0 semitones)) | 1.0 |
| PSG2 | pad | pulse1 | 1.0 | pulse1 | 1.0 |
| PSG3 | pad | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC1 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC2 | pad | pulse2 (folded: in the rests of PSG3; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC3 | pad | pulse2 (folded: in the rests of PSG3; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 | 1.0 |
| SCC4 | pad | pulse2 (folded: in the rests of PSG3; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 (folded: arpeggio with SCC3, and in its rests) | 1.0 |
| SCC5 | echo of SCC3 | pulse2 (folded: in the rests of PSG3; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 (echo in the rests of SCC3) | 0.918 |

### nl.music.nemesis3_ship_destroyed

Nemesis 3 0x4B, jingle; 234 frames (3.9 s), no loop (ends); 1 frames per row (100 % of the onsets on the grid); 86 instruments. notes below A1 lifted by an octave on the pulses (pulse1: 6, pulse2: 5, mmc5_pulse1: 22, mmc5_pulse2: 23).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| PSG3 | double of PSG2 | merged into pulse2 (double of PSG2 (onsets 1.00, delay 1 frames, +0 semitones)) | 1.0 | merged into pulse2 (double of PSG2 (onsets 1.00, delay 1 frames, +0 semitones)) | 1.0 |
| SCC1 | echo of SCC2 | pulse2 (folded: in the rests of PSG2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.207 | mmc5_pulse2 (folded: arpeggio with SCC4, and in its rests) | 1.0 |
| SCC2 | bass | triangle | 1.0 | triangle | 1.0 |
| SCC3 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC4 | pad | pulse2 (folded: in the rests of PSG2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.16 | mmc5_pulse2 | 1.0 |
| SCC5 | counter | pulse2 (folded: in the rests of PSG2; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.643 | mmc5_pulse1 | 1.0 |

### nl.music.nemesis3_a_boss_falls

Nemesis 3 0x4C, jingle; 160 frames (2.7 s), no loop (ends); 1 frames per row (100 % of the onsets on the grid); 83 instruments. notes below A1 lifted by an octave on the pulses (pulse1: 7, pulse2: 45, mmc5_pulse1: 40, mmc5_pulse2: 5).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | bass | triangle | 0.949 | triangle | 0.949 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| PSG3 | counter | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 | 1.0 |
| SCC1 | pad | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 1.0 | mmc5_pulse2 (folded: arpeggio with PSG3, and in its rests) | 0.789 |
| SCC2 | echo of SCC3 | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.857 | mmc5_pulse1 (echo in the rests of SCC3) | 0.612 |
| SCC3 | counter | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC4 | pad | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.83 | mmc5_pulse2 (folded: arpeggio with PSG3, and in its rests) | 1.0 |
| SCC5 | counter | pulse2 | 1.0 | pulse2 | 1.0 |

### nl.music.nemesis3_the_secret_weapon_blueprint

Nemesis 3 0x4F, music; 9385 frames (156.4 s), loops to frame 0 (row 0); 2 frames per row (100 % of the onsets on the grid); 20 instruments. notes below A1 lifted by an octave on the pulses (pulse2: 522).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| SCC2 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC3 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC4 | counter | pulse2 (folded: in the rests of SCC3; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC5 | bass | triangle | 1.0 | triangle | 1.0 |

### nl.music.nemesis3_the_ship_leaves_at_the_end_of

Nemesis 3 0x50, jingle; 155 frames (2.6 s), no loop (ends); 1 frames per row (100 % of the onsets on the grid); 8 instruments. no bass voice.

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| SCC1 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC2 | counter | pulse2 | 1.0 | pulse2 | 1.0 |
| SCC3 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC4 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 | 1.0 |
| SCC5 | counter | pulse2 (folded: in the rests of SCC2; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse2 (folded: arpeggio with SCC4, and in its rests) | 1.0 |

### nl.music.nemesis3_title

Nemesis 3 0x51, jingle; 62 frames (1.0 s), no loop (ends); 1 frames per row (100 % of the onsets on the grid); 25 instruments. notes below A1 lifted by an octave on the pulses (pulse1: 2, pulse2: 3).

| MSX voice | role | APU | cov | MMC5 | cov |
|---|---|---|---|---|---|
| PSG1 | counter | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 0.5 | mmc5_pulse2 (folded: arpeggio with SCC2, and in its rests) | 1.0 |
| PSG1n | drums | noise | 1.0 | noise | 1.0 |
| PSG2n | drums | noise | 1.0 | noise | 1.0 |
| PSG3n | drums | noise | 1.0 | noise | 1.0 |
| SCC1 | counter | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) | 1.0 | mmc5_pulse1 | 1.0 |
| SCC2 | counter | pulse2 (folded: in the rests of SCC5; arpeggio on its notes of 8+ frames) + pulse1 (in the lead's rests) | 0.983 | mmc5_pulse2 | 1.0 |
| SCC3 | bass | triangle | 0.804 | triangle | 0.804 |
| SCC4 | lead | pulse1 | 1.0 | pulse1 | 1.0 |
| SCC5 | counter | pulse2 | 1.0 | pulse2 | 1.0 |

## Pilot

The pilot (nl.music.nemesis2_stage_1_bgm, nl.music.nemesis3_stage_1, nl.music.salamander_stage_2: a Nemesis 2 SCC stage tune, a Salamander stage tune, a Nemesis 3 stage tune) was made first; the rules were then refined on it (octave-equivalent doubles, echoes whose delay changes by section, accompaniment detection, note grid, exact loop point, remix folding) and `pilot/` was regenerated with the final tools, so its files equal the main ones.
