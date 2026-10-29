# Music arrangement data format (engine-neutral)

Private files `music_arrange/<asset_id>.json` follow this format; a NES sound-engine converter reads them in phase 7.


One JSON file per Legends music asset whose source is MSX (`<asset_id>.json`). It is
engine-neutral: timing is in 60 Hz frames, pitch in MIDI note numbers plus per-frame cents,
volume in NES volume units. A converter for any NES sound engine (or a tracker) can read it
without knowing the MSX drivers. Written by `tools/arrange.py`; played by `tools/nesynth.py`.

## Top level

| key | meaning |
|---|---|
| `format` | `"nl-music-arrange/1"` |
| `asset`, `name` | Legends music asset id and name (`music_match/music_assets.json`) |
| `source` | MSX game and code, request value, `trace_frames`, `loop_frame` / `ram_loop_frame` (MSX frames), `ended` (the sound stops by itself), `first_note_frame` (MSX frame that is frame 0 here), `kind_in_catalogue` (music / jingle) |
| `tempo` | `hz` 60; `frames_per_row` (the note grid: gcd of the three most common onset gaps of the MSX voices); `common_gaps`; `onsets_on_grid` (share of events that start on a row) |
| `length_frames`, `length_rows` | length of the arranged pass (intro + one loop, or the whole sound) |
| `loop_frame`, `loop_row`, `loop_delay_frames` | where playback jumps back after `length_frames` (null: no loop; the sound ends). `loop_frame = loop_row * frames_per_row + loop_delay_frames`. The loop point is exact: the MSX output from there repeats frame for frame. |
| `apu` | the plain-APU version: channels `pulse1`, `pulse2`, `triangle`, `noise` |
| `mmc5` | the MMC5 version: the four APU channels plus `mmc5_pulse1`, `mmc5_pulse2` |
| `instruments` | instrument definitions used by the events of both versions |
| `waveforms` | the MSX SCC waveforms (32 signed samples) and their brightness, for reference |
| `voice_map` | per MSX voice: role, the channel in each version, how it was folded/merged, and `apu_coverage` / `mmc5_coverage` |
| `voices` | per MSX voice: role and statistics |
| `notes` | arrangement remarks |

## Events

Each channel is a list of events `[t, len, note, inst]`, sorted by `t`, never overlapping:

- `t`: start frame (0 = first note of the tune). Row = `t // frames_per_row`, delay inside the
  row = `t % frames_per_row` (a tracker writes it as a note delay, e.g. FamiTracker `Gxx`).
- `len`: frames the note sounds. After `len` frames the channel is silent until the next event
  (note cut / release). For the triangle this is the articulation (it has no volume).
- `note`: MIDI note number (A4 = 69) for pulse and triangle; for `noise` the NES noise period
  index 0-15 of the first frame (the instrument's `noise` macro has the per-frame index).
- `inst`: instrument id (key of `instruments`).

## Instruments

| key | meaning |
|---|---|
| `c` | `pulse`, `triangle` or `noise` |
| `duty` | pulse duty 0 = 12.5 %, 1 = 25 %, 2 = 50 %, 3 = 75 % |
| `vol` | volume macro, one value per frame from the note start (0-15); when the note is longer than the macro, the last value holds. Absent for the triangle. |
| `pitch` | pitch macro in cents relative to `note`, one value per frame, last value holds (vibrato, slides, sweeps, and the MSX tuning offset). Absent = 0. |
| `arp` | arpeggio: semitone offsets cycled one per frame from the note start (`[0, -10]`, `[0, 4, 7]`...). Absent = none. Added to `pitch`. |
| `noise` | noise period index macro (0-15), one value per frame, last value holds; noise is the long (32767-step) mode. |

Pitch of a frame `k` of an event: `note + pitch[min(k, len(pitch)-1)] / 100 + arp[k % len(arp)]`
semitones; frequency `440 * 2 ** ((p - 69) / 12)`; pulse timer `round(1789773 / (16 f) - 1)`,
triangle timer `round(1789773 / (32 f) - 1)`.

## Notes for an engine converter

- Macros are exact per-frame transcriptions of the MSX driver output, so they are long; an
  engine with smaller envelopes can loop the sustain part (last value holds) and quantise.
- Events off the row grid (`t % frames_per_row != 0`) are echoes, delayed voices or drum flams
  of the original; keep them as delays.
- Volumes are MSX levels mapped to NES units (SCC 0-15 as is; PSG log levels:
  `15 * sqrt(AY amplitude)`); the mix was checked with `tools/nesynth.py`, not on hardware.
- DPCM is not used.
