# Native campaign progression - CP0002

`src/campaign.s` is real 6502 code, linked and executed in FCEUmm by
`tools/test_campaign_native.py`. It is a production module, not a full game,
not a stage viewer, not a timer-driven imitation of combat, and not an emulator
of the MSX CPU. Only the future real stage/actor systems may issue its events.

The module owns 16 state bytes and two temporary zero-page bytes. The unit-test
cartridge uses NROM only as an instruction-test fixture; it does not select the
production game's mapper or replace the planned MMC5 runtime. The measured
CODE segment, including the mailbox test driver, is 1,023 bytes. This is not a
whole-game memory or frame-time estimate.

## Source-derived routes

All references below use the pinned byte-exact original disassemblies listed
in `evidence/source_catalog.json`.

- Nemesis: eight main stages, bonus IDs 9-12. Targets in 2/3/4/7 lead to 9/10/11/12;
  the bonus returns are 3/4/5/8. References: `acaba_la_fase` $6D53,
  `salta_a_la_fase` $6FB9, target flag $E1C0 and return table $418F.
- Nemesis 2: outbound 1..7, the halfway ending, then inbound 6..0; interior 8
  returns to the saved next stage. Secret routes 3->9 and 6->10, optionally
  10->11, preserve the outbound/inbound return destination. References:
  p01:$7AB4, $7AC2, $7B67, $7BFD, $7C1C and $7C59.
- Salamander: 1->2, then planets 3/4/5 in any order, then final 6; with the
  discovered Crystal Breeze, Operation X (7) is inserted before 6. References:
  p10:$8B7B, $988A, $9A43 and ending condition p10:$8F7F. A no-crystal run must
  not silently acquire the crystal or claim the good ending.
- Nemesis 3: 1..11, computer interludes after 3 and 4; after 9, the three maps
  are checked. Missing-map priority is stage 5, then 7, then 8. Revisits return
  to the computer; all maps unlock stage 10 and clear the revisit flag.
  References: p00:$4599/$45B3/$45CA/$45E3, p26:$7F7A/$7FC8. Secret type $0B
  in stage 10 sets $E396 and affects the ending (p27:$8786). The module calls
  these normal/secret endings rather than inventing a good/bad classification.

## Deliberate anthology integration, not an original Konami rule

After each completed chapter's ending, the next historical chapter starts
without a four-game selection screen. Nemesis 2's halfway ending is NOT treated
as completion: it leads into the complete return journey.

A Salamander bad ending is shown and produces an explicit retry request;
accepting that request restarts this chapter while preserving completed earlier
chapters. This is the chosen anthology policy to avoid silently claiming a
canonical victory after a failed mission. Neither the retry UI nor any cutscene
renderer is implemented by this progression module. Both Nemesis 3 endings
remain valid final outcomes, and secret equipment is not granted automatically.

## Verification boundary

288 native event/route checks cover the six planet permutations with and without
the crystal, both Nemesis 2 traversal directions and all eight map combinations.
The tests inspect real NES RAM after the compiled function returns and verify
that the hardware stack does not leak. A negative control mutates the native
bonus table from stage 9 to stage 8 and confirms that the expected-route check
can distinguish the wrong code.

These checks do not validate enemies, shooting, collisions, scrolling, boss
fights, rendering, audio, playable stages or end-to-end campaign completion.
Those systems are still separate implementation gates.
