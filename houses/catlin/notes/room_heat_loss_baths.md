# Radiant floors as sole heat — RM-M-BATH2 and RM-S-BATH1

**House:** catlin
**Structure:** `FH-M-BATH2` in `RM-M-BATH2`, `FH-S-BATH1` in `RM-S-BATH1` — the two radiant
zones that are the only heat source in the room they lie in. `FH-M-DINING` is the third zone
and is **not** a subject here: `RM-M-LIVING` has an indoor head in it.
**Written:** 2026-09-12, by hand, before the calculation it oracles was encoded.
**Oracle for:** `checks/mep/room_heat.py`, reported by `mep.room_heat_source`; reproduced by
`tests/test_room_heat_source.py`.
**Companions:** `notes/erv_static_budget.md` — the other half of the same BLD-08 pass;
`notes/radiant_mat_wattage.md` conventions live in the zones' own comments in
`plan/storeys/main.py` and `plan/storeys/second.py`.
**What is asked of the reviewer:** §4 says `RM-M-BATH2` is 41 % short on the engine's own
room-scoped load and §5 says that load over-charges the room. **Decide whether to buy an
hour of Manual J for that one room, or to add a second heat source to it.** `RM-S-BATH1`
needs no decision.

> ⚠ **NEITHER ROOM IS A CODE SUBJECT, AND THAT IS NOT A LOOPHOLE.** IRC R303.10 — adopted
> unamended in Minnesota — requires heating capable of 68 °F three feet above the floor at
> the design temperature, and it says so of **habitable** space. R202 defines habitable space
> as a space for living, sleeping, eating or cooking, and its very next sentence excludes
> bathrooms and toilet rooms by name. Both of these rooms are bathrooms. The arithmetic is
> worth doing anyway — an unheated bathroom in Minnesota is a freezing-pipe problem before it
> is a comfort problem — but no inspector will ask for it, so nobody else is going to catch
> it.

> ⚠ **18.6 Btu/h/ft² IS THE WRONG NUMBER AND THIS HOUSE QUOTED IT IN TWO FILES.** It is
> Schluter's **82 °F example**, not their design point. BLD-08's own "25 to 30" is a guess at
> the other end. The number is **22.8**, derived in §2 from Schluter's own published
> relation.

---

## 1. Geometry and the product

| term | `FH-M-BATH2` | `FH-S-BATH1` |
|---|---|---|
| room | `RM-M-BATH2` | `RM-S-BATH1` |
| room floor area | 64.9 ft² | 73.3 ft² |
| heated zone polygon | **17.52 ft²** | **26.83 ft²** |
| fraction of floor heated | 27.0 % | 36.6 % |
| cable SKU | Schluter DITRA-HEAT-E-HK **DHEHK12016** | **DHEHK12027** |
| nameplate | 203 W, 1.7 A, 120 V, 16.0 ft² of coverage | 338 W, 2.8 A, 120 V, 26.7 ft² |
| spacing | 3 5/8" ("3-stud") | 3 5/8" |
| floor covering | porcelain tile over the cable's own uncoupling membrane | the same |

*Floor areas are between finish faces since 2026-09-24 (they read 74.4 and 84.9 ft² while
the room face was axis-derived); `FH-S-BATH1` moved its west edge to 2" off the wall's
finish face — at x=5" it had run 1 5/8" under the wall.*

**The heated area is the POLYGON, not the cable's rated coverage.** The surplus (1.52 ft²
and 0.13 ft² respectively) is Schluter's required buffer zone: it is warm floor, it is simply
not cable. Using 16.0 and 26.7 would understate both rooms.

**Why so little of each floor is heated.** Schluter's keepouts are manufacturer minimums, not
choices: 2" off every wall and fixed cabinet, 7" off the water closet's drain centreline (the
wax ring), and **nothing at all under a bathtub platform or a closed-toe vanity**, where
trapped air cooks the cable. Between the vanity, the WC, the shower pan and the tub deck,
what is left in `RM-M-BATH2` is 17.52 ft². That is the binding constraint in §4 and it is
worth knowing before reading the shortfall.

## 2. What the floor delivers — Schluter's own relation

Schluter publishes delivered output as a function of the difference between the floor surface
temperature and the room's operative temperature:

> Q = 8.92 · ΔT^1.1  (W/m², ΔT in °C)

At the recommended **84 °F floor over a 72 °F room**:

| term | working | value |
|---|---|---|
| ΔT | 84 − 72 | 12 °F = 6.667 °C |
| ΔT^1.1 | e^(1.1 · ln 6.667) = e^(1.1 × 1.8971) = e^2.0868 | 8.059 |
| Q | 8.92 × 8.059 | 71.9 W/m² |
| in Btu/h per ft² | 71.9 × 3.412 / 10.764 | **22.79 → 22.8 Btu/h/ft²** |

**Check the 18.6 against the same relation**, because that is how it is shown to be the wrong
row rather than merely a different one. At 82 °F floor over 72 °F, ΔT = 10 °F = 5.556 °C:
8.92 × 5.556^1.1 = 8.92 × 6.606 = 58.9 W/m² = **18.7 Btu/h/ft²**. So 18.6 is Schluter's
82 °F **example**, arrived at correctly and read at the wrong station — the same class of
error as reading a fan curve at 0.2 in. w.g. (`notes/erv_static_budget.md`). The design point
is 84 °F, and 84 °F is what a tile floor with no surface-temperature cap will actually run.

**Two ceilings bound the delivered figure and both must be applied:**

> delivered = min( heated area × 22.8 , nameplate watts × 3.412 )

The floor cannot deliver more heat than the cable draws, and it cannot deliver the cable's
whole draw over more floor than is actually heated. In this house the **area** term binds in
both rooms, which is the finding of §4.

| | area term | watts term | binding | delivered |
|---|---|---|---|---|
| `FH-M-BATH2` | 17.52 × 22.8 = 399.5 | 203 × 3.412 = 692.6 | **area** | **399 Btu/h** |
| `FH-S-BATH1` | 26.83 × 22.8 = 611.7 | 338 × 3.412 = 1,153.3 | **area** | **612 Btu/h** |

## 3. What each room loses

Two passes, and they disagree. Both are given because the disagreement is the finding.

**Pass A — the envelope by hand, at MN 1322's −15 °F design temperature** (confirmed as the
governing value for this site; `plan/site.py` carries it). Interior setpoint 70 °F, so
ΔT = 85 °F.

`RM-M-BATH2` has exactly one exterior surface and one window; its ceiling and floor are both
interior, and three of its four walls bound conditioned space.

| surface | area | U or R | working | Btu/h |
|---|---|---|---|---|
| west wall, `EXT_2X6` | 76.4 ft² | R-40.7 | 76.4 × 85 / 40.7 | 160 |
| `WIN-M-BATH2`, WT-2736-T | 6.75 ft² | U-0.25 | 6.75 × 0.25 × 85 | 143 |
| ceiling, floor, three walls | — | interior | no ΔT | 0 |
| | | | | **303** |

**Pass B — the engine's room-scoped block load**, `estimate_block_load(rooms={room})`:

| room | pass A (envelope only) | pass B (engine) | difference |
|---|---|---|---|
| `RM-M-BATH2` | 303 Btu/h | **556 Btu/h** | +253 |
| `RM-S-BATH1` | not worked by hand | **606 Btu/h** | — |

**\*\* 2026-09-24: 567 -> 556 and 619 -> 606. \*\*** The room areas became finish-face
areas, which shrinks the conditioned volume and each bath's share of the air-side terms; pass A is conduction
through the same exterior wall and window and does not move.

**\*\* BOTH PASS-B FIGURES MOVED 2026-09-18, AND THEY MOVED IN OPPOSITE DIRECTIONS. \*\***
They were 673 and 591. The block-load correction changed five terms at once and the net
per room depends on which of them that room's share is dominated by:

* **down** — the raked gable walls stopped being billed as prisms, and the walkout walls'
  above-grade band stopped being charged a soil ΔT while their buried band gained the
  soil-path resistance. `RM-M-BATH2`'s volume share of a smaller whole-house air term
  falls with it.
* **up** — the below-grade ΔT went from 23 °F to 45, the heating design hour takes 1.5×
  Sherman's annual-average infiltration, and the envelope scope gained the two framed
  walkout walls.

That a total can absorb five corrections of 0.5–2.0 kBtu/h each and move 1% is the whole
argument for writing the components down rather than the sum.

**The remaining 264 Btu/h is air, and it is charged by volume share.** Pass A is envelope conduction
only. Pass B adds the two air-side terms — blower-door infiltration and ERV ventilation air
— apportioned by this room's share of the house's conditioned volume, which is the method
`estimate_block_load`'s own docstring describes and calls approximate.

## 4. The comparison

| | delivered | load (engine) | margin | verdict |
|---|---|---|---|---|
| `RM-M-BATH2` | 399 Btu/h | 556 Btu/h | **−157 (28 % short)** | UNKNOWN |
| `RM-S-BATH1` | 612 Btu/h | 606 Btu/h | **+5 (0.9 % over)** | PASS |

*(2026-09-24: the margin is +5 Btu/h on the finish-face loads above — the 2" standoff
cost 11 Btu/h of delivery and the smaller volume took 13 off the load; the paragraph below
records the 2026-09-18 state and its argument still holds.)*

**`RM-S-BATH1` still carries its room, and its margin is now 0.6 %, not 5 %.** The verdict
did not change and the decision it supports did: 31 Btu/h of slack on a 591 Btu/h load was a
real margin, and 4 Btu/h on a 619 Btu/h load is arithmetic landing on the line. What keeps
this a PASS rather than a coin toss is §5's argument, which applies to `RM-S-BATH1` exactly
as it does to `RM-M-BATH2`: the engine's room-scoped load over-charges a small interior
bathroom on continuous extract, so 619 is the high end of a range. It is worth re-reading if
anything about this floor, its covering or the house's air-tightness moves again.

**`RM-M-BATH2` does not, on this load, and a bigger cable cannot fix it.** This is the part
worth writing down plainly: the DHEHK12016 already **draws** 693 Btu/h, more than the room's
whole load. What it cannot do is get that heat out through 17.52 ft² of floor. Covering
567 Btu/h at 22.8 needs **24.9 ft² of heated floor** in a room that has 74.4 ft² total and
whose vanity, water closet, shower pan and tub deck take the difference. **The constraint is
square feet, not watts**, and no cable in the ladder changes it.

The three real options, in the order they should be considered:

1. **Work the room by hand (Manual J).** §5 says the 567 is over-charged; if the true load
   is nearer 400 the room is already covered and nothing is bought.
2. **Add a second heat source** — a small panel, a toe-kick heater, or a supply register off
   `EQ-M-HP2-BED`'s branch, which already claims this room in `zone_rooms` but reaches it
   only through a door.
3. **Accept it** on the operating argument: run the floor above 84 °F on design mornings.
   Tile has no cap and the room is occupied in bursts. This is the do-nothing option and it
   should be a decision, not a default.

**What was rejected: shrinking the load to make the check green.** The 303 figure is a real
hand pass and it is in §3 for the reviewer, but pass A omits air entirely and is not the
answer either.

## 5. Why the engine's load over-charges a small interior bathroom

`estimate_block_load`'s docstring states the approximations; this section names which way
each one pushes for *this* room, which is what decides that the verdict is UNKNOWN rather
than a failure.

- **Ventilation air is apportioned by volume share, and this room is where it leaves.**
  `RM-M-BATH2` carries `REG-M-EXH2` on `DU-M-ERV-R-BATH2`, a 20 cfm continuous **extract**.
  The ventilation term of the block load is the cost of tempering incoming fresh air, and
  this room receives none — it is charged a pro-rata slice of a load that is paid at the
  supply terminals in other rooms. Over-charged.
- **Infiltration is apportioned the same way.** A room with one exterior wall and no exterior
  door gets its share of a whole-house blower-door number. Over-charged.
- **There are no room-level internal gains at all.** A bathroom in use has a person, a
  luminaire or two, and an 8 gpm hot shower dumping heat into the room. Under-credited.
- **There are no per-room ceiling planes**, and this room's ceiling is interior.

All four push the same way. The honest statement is that `RM-M-BATH2`'s load is somewhere
between 303 and 567 Btu/h and nothing in this model can say where — which is why
`mep.room_heat_source` prints both numbers and returns UNKNOWN rather than converting an
approximation into a verdict.

## 6. What is NOT graded here

- **Transfer through doorways.** Both rooms open onto heated space, and warm air moving
  through an undercut door is real heat that this model cannot see. `RM-M-BATH1`,
  `RM-B-BATH` and a dozen other rooms in this house are heated by nothing else at all, and
  `mep.room_heat_source` deliberately does not grade them: there is no term for it.
- **Floor surface temperature itself.** 84 °F is the design assumption, not a modelled
  result. `advisory.floor_finish_over_radiant` separately grades whether the covering can
  take it — which is why both of these rooms are tile and not plank.
- **Warm-up time.** A radiant floor under tile has hours of thermal lag. A room that is
  covered at steady state can still be cold at 6 a.m., and a setback schedule is a control
  decision nobody has made here.
- **The 68 °F at three feet that R303.10 actually asks for.** This compares Btu/h to Btu/h.
  A floor delivering its load holds the room, but the vertical temperature profile over a
  radiant floor is not something a block load speaks to — and as the banner says, R303.10
  does not reach a bathroom anyway.
- **`FH-M-DINING`.** It is supplemental in a room with a head in it, and it deliberately
  states no `delivered_btuh_per_ft2`: the delivered output of a floor under engineered plank
  in a 748 ft² room is not the question, the zone's margin is.
- **Electrical.** The circuits, GFCI protection and the uncuttable-cable ordering rule live
  in the zones' own comments and in `plan/circuits.py`.

## Sources

- Schluter-Systems **DITRA-HEAT-E** installation handbook and technical data: the delivered
  output relation Q = 8.92 · ΔT^1.1 W/m²; the recommended 84 °F floor / 72 °F operative
  design point and the 82 °F worked example; the 2" wall/cabinet and 7" WC-drain keepouts;
  the prohibition on cable under a bathtub platform or closed-toe vanity; the uncuttable
  fixed-length cable ladder and its buffer-zone rule. DHEHK12016 (16.0 ft², 203 W) and
  DHEHK12027 (26.7 ft², 338 W) nameplates.
- Schluter's own characterisation of DITRA-HEAT as a **secondary** heat source — which is
  what made this note necessary and which §4 does not overturn for `RM-M-BATH2`.
- **IRC R303.10** (heating facilities), adopted unamended in Minnesota; **IRC R202**,
  definition of *habitable space* and its exclusion of bathrooms and toilet rooms.
- **Minnesota Rules 1322** — the −15 °F heating design temperature for this site, confirmed
  as the governing value.
- `typehaus/checks/building_science/energy_load.py::estimate_block_load` — the room-scoped
  load of §3 pass B, and its own docstring's statement of the four approximations §5 works
  through.
