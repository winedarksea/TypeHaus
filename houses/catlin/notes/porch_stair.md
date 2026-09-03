# The porch stair to grade — ST-SG-PORCH

Model: `params/sunken_garden.py` (`PORCH_STAIR`, `PORCH_STAIR_RAILS`,
`PORCH_STAIR_THRESHOLD_RAILS`, `_PORCH_STAIR_*`, `_PORCH_GUARD_PATH`, `HP_PAD`),
`plan/electrical.py` (the two disconnects), `plan/lighting.py` (`ED-M-STAIR-LT`),
`plan/site.py` (the pad's fall), `prices.toml`. Authored 2026-09-03. The heat pumps that
share its pad and had to turn to make room are `notes/heat_pump_ground_pad.md`.

## Why

The porch floor sits at 0'-0" and grade east of it at -2'-10", and until now there was **no
way down**. You reached the porch through `D-M-BALC`, the French pair at x 21'-4", and
`RL-SG-PORCH` railed all three open edges. The owner wanted a stair off the east edge into
the yard pocket — which is where `EQ-M-HP1-OD` and `EQ-M-HP2-OD` had stood since the
2026-09-02 move off the balcony. Turning both condensers to face south freed the pocket's
whole north strip, and that strip is exactly a straight flight with no landing and no turn.

## The flight

`ST-SG-PORCH`: **5 risers at 6.60", 4 treads at 11" with no nosing, 36" wide, KDAT** — the
`ST-G-SERVICE` pattern in `plan/storeys/garage.py`, which is the same five-riser
0'-0"-to-grade flight and is already priced and tested.

| | |
|---|---|
| run | x 28'-6"..32'-2" (`start` is the FOOT, at the east end; the flight climbs west) |
| width | y -0'-10"..-3'-10" |
| base | `_HP_PAD_TOP`, -2'-8" — the pad top |
| top | `_porch_walking_surface`, +0'-1" — the composite plank, not the 0'-0" joist top |
| rise | 2'-9" = 33" over five risers |

Both elevations are **stated on the element**, because neither is a storey datum:
`from_storey` and `to_storey` are both `main`, which is the step-down-within-one-storey case
`floor_opening=None` exists for. 6.60" is inside R311.7.5.1's 7 3/4" and the 11" going leaves
R311.7.5.2's 10" minimum with an inch to spare. No `bearing_refs`: the stringers bear on the
`W-SG-E1` wall top at the head and on `SL-SG-HPPAD` at the foot, and a `bearing_refs` tag
that names no wall on `from_storey` is an `integrity.stair_bearing` error rather than a
permission.

### The 12" wall top is a threshold, not a tread — and it is NOT MODELLED

`W-SG-E1`'s top is 0'-0", **one inch below the porch plank**. A flight springing from the
wall's west face at x 27'-6" would want its first tread 5.6" *below* the concrete it has to
cross. So the flight starts at the wall's **east** face, x 28'-6", and the 12" of wall top
between the porch plank and the head of the flight is decked flush at +0'-1" with a
**3'-0" x 12" board of the porch's own composite plank** — 3 sf.

That board is trim over 12" of concrete with nothing to frame under it, so no element models
it and no takeoff row would find it. It is priced with the plank instead: `prices.toml`
`[sheet_goods] "composite-deck"`, where the material rides inside the 6 sheets already
bought (192 SF against 184.1 net) and +$20–45 of labour was added for the cut-in and the
anchoring. **An unmodelled detail that is not written down is just a missing detail** — this
is the same call the framed-wall line-set sleeve got.

## Guards and the handrail

`RL-SG-PSTAIR-S` and `RL-SG-PSTAIR-N`, one each side, Williams aluminium (ICC-ES ESR-3485
black, the `RAILING-EXT-ALUMINUM-SURFACE` product `RL-SG-PORCH` uses), 36" with
`role="guard_and_handrail"`, `serves_stair="ST-SG-PORCH"`, `top_height=inch(36)` and a
`graspable_profile` — the `RL-G-SERVICE` authoring in `plan/storeys/garage.py`.

One 36" run with a graspable top rail answers two rules at once. The total rise is 33" > 30",
so `code.R312_1_1_stair_open_side` wants a guard on each open side, and 36" clears
R312.1.2's 34" stair minimum measured off the nosing line; five risers is over R311.7.8's
four, so the flight wants a handrail, and 36" is inside R311.7.8.1's 34"–38". A 36" tread
past two 1 1/2" sections leaves **33" clear** against R311.7.1's 27" for two rails (the check
measures 34.50", which is the same number with the rail lines on the tread edges).

**The north side needs its own guard even though `W-M-S2` stands 5" away.** That wall's band
starts at 0'-0" and every nosing but the last runs below it, so
`code.R312_1_1_stair_open_side` — which asks whether a wall's own z band brackets the nosing
— will not credit it, and neither would a person falling off that side.

### The threshold's two cheeks

`RL-SG-PTHRESH-S` and `RL-SG-PTHRESH-N`, 1'-0" each, **level** at 42" to match `RL-SG-PORCH`,
on the wall top between the porch plank and the head of the flight. That foot of walking
surface is 33" above the pad on **both** its north and south sides, and nothing in the engine
asks for a guard there:

- `code.R312_1_1_stair_open_side` measures the FLIGHT, whose top tread is only 26.4" over the
  pad — under the 30" trigger. It reports PASS on this stair with or without any guard at all.
- `code.R312_1_guard_height` tests `RL-SG-PORCH` against the deck edge **segment** with a
  plain `LineString` distance (`_railing_runs_edge`,
  `checks/code/mn_residential/fall_protection.py`), and the east edge's midpoint stays
  guarded, so the 3'-0" opening reports PASS either way. Recorded in `plans/TODO.md`.

The guard return at an opening is on the author, and these are it. They are separate elements
rather than 12" more on the two stair rails because a `serves_stair` `Railing` is **raked
along the nosing line for its whole authored path** — a foot of level wall top on the end of
one resolves at 0" above the (absent) nosings and fails R311.7.8.1 outright. Two elements is
not a workaround: one raked handrail-guard on the flight, one level guard on the wall top, is
the true statement.

### And the porch guard just gets shorter

`_PORCH_GUARD_PATH`'s last point moves from `_y_in_n` (-0'-10", where the east leg already
terminated) to `_PORCH_STAIR_Y1` (-3'-10"). One path edit — **no split, no degenerate stub**
— and the east leg loses 3'-0". `RL-SG-PORCH` goes 36.3 LF to 33.3. The three
`_PORCH_STAIR_*` constants are shared by the flight, the opening and the guard so the three
cannot drift apart. `_PORCH_GUARD_SOUTH_STATIONS` reads the *middle* path segment and is
unaffected.

## Electrical

**The two disconnects moved**, from x 30'-0" / 35'-0" at 5'-0" to **x 34'-3 1/2" / 35'-7" at
3'-6"**, and the stair is half the reason:

- NEC 110.26(A) working space cannot be a stairway, and the flight now runs under the old
  x 30'-0" station. East of `WIN-M-LIV-S1` (x 31'-5"..33'-11") the 36" working depth falls
  over the flight's level step-off instead.
- NEC 404.8(A) caps an operating handle at 6'-7" above the standing surface. `Mount.elevation`
  is storey-relative, so `ft(5)` on a main-floor wall put the handles **7'-10"** above the
  grade you operate them from. 3'-6" reads 6'-4". Nothing in the engine was measuring this.

**`ED-M-STAIR-LT`**: `code.R303_8_exterior_stairway_illumination` requires a light at the top
landing on the stair's `to_storey`, and looks for one within 4'-0" of the flight's plan
outline. Nothing already authored reaches — `ED-M-PORCH-FAN` and `ED-M-PORCH-FLOOD` are both
at x 18'-0", ten feet west. So a full-cutoff exterior sconce goes on `W-M-S2`'s exterior face
at (30'-0", -0'-8 7/8"), 7'-0" storey-relative (9'-10" over the pad), no `room=` — the
`ED-M-PORCH-FAN` / `ED-G-EXT-LT` precedent that makes `electrical.wet_location` and
`advisory.dark_sky_lighting` read it as exterior.

`ED-T-LT-SCONCE-EXT` rather than a freshly minted downlight type, deliberately: it is the
same full-cutoff wet-rated fitting as `ED-G-EXT-LT` and it is **already priced**. A new
`LuminaireType` with no `prices.toml` row is silently dropped from the takeoff, so minting
one would have bought a fixture the bill never showed. It is switched from
`ED-M-PORCH-FLOOD-SW` rather than a third switch — NEC 210.70(A)(2)(b) wants the exterior
light switched from inside, that switch already is, and the flood and the stair light are
wanted on the same errand.

## What this cost

+0.34 cy of concrete (the pad, 0.36 → 0.70), +6.4 LF of `RAILING-EXT-ALUMINUM-SURFACE` net
(−3.0 on `RL-SG-PORCH`, +7.4 over four new runs), the KDAT flight (32 LF of 2x12 stringer,
32 LF of 11x1.5 tread, shared with `ST-G-SERVICE` in the BOM's kdat groups), one exterior
sconce, 3 sf of unmodelled composite threshold board, and ~8 LF of line set inside the
existing lump allowance. **No new engineered item** — the flight is wood on grade and the pad
is still not a foundation.

## What is not modelled

- **The threshold board** — above, priced with the plank.
- **The raked stair-post premium.** Every post in the `RAILING-EXT-ALUMINUM-SURFACE` rate
  stands on a 12" concrete wall top and arrives welded to a 5x5 baseplate. A post on a 2x12
  KDAT stringer is a different baseplate on a different substrate, through-bolted rather than
  anchored, and it wants a rake-adjustable post-and-rail kit. Flagged on the price row
  against the two raked runs; it is not in the numbers.
- **The raked runs' true length.** The BOM bills a `Railing` by the PLAN length of its path,
  so 3.7 LF of plan is 4.6 LF of rail on a 33"-in-44" rake — the two `PSTAIR` runs read ~1.9
  LF light between them. Noted on the price row.
