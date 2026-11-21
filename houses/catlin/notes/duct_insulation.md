# Duct insulation against MN 1322 Table R403.2.1 (hand-graded, 2026-11-21)

The oracle for `mep.duct_insulation`. Rule: Minn. R. 1322.0403 subp. 1, Table R403.2.1
(revisor.mn.gov, read 2026-11-21; whole table in the gitignored
`docs/local-code-notes/mn-1322-r403-2-1.md`). In short: outside the building R-8 + V + W;
attic/garage/vented crawl R-8 + V; outdoor-air intake or exhaust duct in conditioned space
R-3.3 + V; in a slab or the ground R-3.5 + V; anything else in conditioned space (including
a basement with insulated walls) none. Note a: inside conditioned space the requirement
holds only within 3 ft of the exterior or unconditioned space.

## Where each run is

Every catlin room a duct crosses is conditioned (the garage, the one unconditioned room,
has no duct). No duct is below the basement slab, and none is outside the walls except
where the two outdoor legs pass through the north wall to their hoods. So only note a's
3 ft can make a requirement, and only on a run that reaches the envelope.

## The two outdoor legs

Both wear `INSULATION_ERV_WRAP`: 1" AP Armaflex, R-4.2 (datasheet, R-4.2 per inch; 1" x
4.2 = 4.2, inside the 10% integrity band), closed-cell, its own vapour retarder.

- `DU-ERV-OA` (outdoor air). Hood end at y = 440"; the north wall's axis (W-M-N3B, the room
  cells' edge) is y = 432", so 8" is in the wall (the sealed penetration, `SP-M-ERV-OA-SEAL`,
  not graded here). From y = 432 the run goes 23.8" south to y = 408.2 at +5'-0", then drops;
  the 3 ft ends 36 - 23.8 = 12.2" down the drop. Required over those 3.0 ft: R-3.3 + V.
  R-4.2 >= 3.3, V yes: **PASS**. The rest of the run is more than 3 ft in: none required
  (it is wrapped end to end anyway, for condensation, budget s.10.4a).
- `DU-ERV-EA` (exhaust, downstream of the core). Discharge end at y = 440" on +17'-0";
  axis at 432", so 8" is in the wall (`SP-S-ERV-EA-SEAL`). 13.5" of the top leg (y 432 to
  418.5) then 22.5" down the NW chase riser make the 3 ft. Required: R-3.3 + V. R-4.2 and V:
  **PASS**. (The chase is no room on the second storey; the riser there reads off
  RM-M-MECH, the conditioned room it rises out of. Either way it is inside the envelope.)

The check measures these lengths in 2" steps, so it prints 2.9-3.0 ft.

## Everything else: N/A

- `DU-ERV-RISER-SUP` and `-EXH`: house air to and from the core (the exhaust riser is the
  stale-air side upstream of the core). The EXH riser grazes the NW corner's wall line for
  about 4" between two conditioned stretches; that is passing a wall's end, not leaving the
  envelope, so no 3 ft applies. **N/A.**
- `DU-B-WH-IN` / `-OUT`: transfer air between the workshop and the stair hall, both
  conditioned basement rooms. **N/A** (they carry R-6 for the HPWH's cold discharge, which
  the table does not ask for).
- The ERV branches and the heat-pump supplies and returns on every storey, the attic runs
  in the FollowRoof rooms included: indoor air, wholly in conditioned space. **N/A.**

No run is bare where the table asks, and no spec is missing its row: 2 PASS, 0 FAIL,
0 UNKNOWN, the rest N/A.
