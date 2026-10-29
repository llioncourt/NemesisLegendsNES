# CP0016 - chapter flow through the campaign module, scene placeholder, asset bible

Private ROM `build/native/Nemesis_Legends_CP0016.nes`, 786448 bytes, sha256
`c10f9928e49b9612aad51f9fc75fe79e8f94eafeeaae56e422b44f9f8f2eb45b`. The work
started on 2026-10-27 and stopped before it was pinned; on 2026-10-28 the same
ROM was rebuilt from the CP0014 private package plus `main` (byte identical) and
`python tools/checkpoint.py test` passed.

## Runtime

- The campaign module numbers chapters from 0; the runtime numbers them from 1.
  The cheat menu stores `chapter-1` in the module and `AdvanceStage` restores
  `chapter+1`, so the Nemesis 3 maps no longer request an out-of-range scene.
- Chapters without ported stage logic (2-4) end a map at the descriptor's
  source scroll end (`ChapterMapEnd`) and the campaign module decides the next
  map, the return trip or a scene.
- Mode 4 is a scene placeholder screen (`SceneOpen`/`SceneFrame`): it names the
  scene the campaign module asked for and continues through the real
  `EVENT_SCENE_DONE` path on START.
- `tools/test_chapter_flow.py`: 8 structural hops (Nemesis 2 map 1 -> 2,
  Nemesis 3 map 1 -> 2, Nemesis 3 map 3 -> interlude -> map 4, Nemesis 2 map 7
  -> turn scene -> map 6).

## Asset bible (Nemesis)

`tools/asset_bible.py` -> `manifests/asset_bible.json`, `docs/ASSET_BIBLE.md`:
60 game objects, MSX side proven from the Z80 code, NES side from OAM captures
of Gradius (US). Independent QA: 57 PASS, 3 UNRESOLVED. The private evidence
zip has QA rounds 1-3; the final round's verdicts exist only inside
`manifests/asset_bible.json`.

## Limits

Structural progression only for chapters 2-4 (no enemies, bosses, weapons,
music). The ROM still draws MSX conversions everywhere. See `docs/DECISIONS.md`
for the scope that the next checkpoints follow.
