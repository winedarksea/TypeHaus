# Balcony heat pumps — mounting, and the eight holes

Model: `params/sunken_garden.py` (`_HP_STAND_AT`, `HP_STAND_LEGS`,
`HP_STAND_ANCHORS`, `FS-SG-DECK.reinforcements`), `plan/electrical.py` (the two units),
`plan/mep_drainage.py` (`HP_CONDENSATE`). Graded by `mep.deck_equipment_support`.
Companion to `notes/beam_water_protection.md`, whose cap-on-tape order this must not violate.

## What had to be decided

`EQ-M-HP1-OD` (Gree Vireo GEN3) and `EQ-M-HP2-OD` (Multi 30k) stand on `FS-SG-DECK` at
+10'-0". That deck is a **watertight aluminium plank that is also the roof of an occupied
porch**, and before this change it had **zero penetrations** — both guards are
`METAL_FASCIA_MOUNT`, hung off `TR-SG-FASCIA`, which was deliberate.

The units cannot stand loose:

- **The manufacturer says bolt it down.** Gree's service manual §8.6: *"Fix the foot holes of
  outdoor unit with bolts… make sure the support can withstand at least four times the unit
  weight."* IRC M1401.4 adopts the manufacturer's instructions, so this is code. M1401.4 also
  says supports *"shall prevent excessive vibration, settlement or movement"* in its own right.
- **Wind, not weight, governs.** Indicative ASCE 7-22 §29.4.1 numbers at Minneapolis's 107 mph
  put overturning at 2,147 in-lb (Exposure B) to 3,202 (C) against ~1,047 in-lb of self-weight
  — it **tips at 2.1–3.1x, and slides**. Ballasting instead would need ~256 lb of added dead
  weight per unit. **These numbers are unsealed.** A PE owns the exposure call and the anchor
  design; the model deliberately encodes none of it (see "what the check does not do").
- **Non-penetrating supports do not fit.** MIRO / C-Port / Big Foot are commercial-only,
  publish no transferable wind rating (Big Foot's blanket figure is 90 mph, under our 107),
  top out at 12"–14 5/8", and cannot satisfy a bolt-down instruction anyway.

So: penetrate — the way Wahoo's own AridDek guardrail detail already does, a 3/8" lag through
the deck board into added timber blocking. **The design problem is making eight holes survive
a century.**

## The rule

> **A fastener that penetrates the waterproof plane lands only in a member that can be cut out
> and replaced from below. Never in a beam, never in a joist.**

This is the opposite of the instinct, and the temptation here is strong: both units sit
within an inch of the rear bearing line, so `BM-SG-BLC` is *inside*
`EQ-M-HP2-OD`'s footprint and `BM-SG-BLW` runs under `EQ-M-HP1-OD`'s west edge. A beam directly
over a pillar and its footing is the stiffest thing on the deck.

It is also the member that carries `TR-SG-CAP-BL*` and the butyl under it, whose ply seams are
the exact wet joint `notes/beam_water_protection.md` exists to close, and which cannot be
replaced without dismantling the balcony. Stiffness is not the scarce thing here.

## The layers, outermost first

1. **Few holes.** Two cross-rails per unit, four anchors per unit — not eight feet bolted
   individually.
2. **Holes in the high, dry third.** The units sit at the north end of the deck's 2"-in-8'-8"
   southward fall, so only ~3' of deck sheds across the penetrations.
3. **Sacrificial host.** Every lag lands in new full-depth 2x8 blocking
   (`FS-SG-DECK.reinforcements`, `plies=1` so it emits blocks and no sister plies). Sixteen
   blocks, two per anchor, one either side of the nearest joist line.
4. **Butyl under everything, for free.** `"blocking"` is already in
   `takeoff/member_protection._TAPED_CATEGORIES`, so every block inherits
   `FS-SG-DECK.top_protection` and tapes and bills itself. The butyl is under the base plate
   by construction.
5. **A sealed hole, not just a sealed surface.** Bonded EPDM washer on the shank, butyl gasket
   under the plate, and sealant in the pilot hole. A sealed surface over an unsealed hole is
   how this joint fails.
6. **One alloy problem, not three.** The stand is **aluminium** (`EQUIP_STAND_ALUM`) on an
   aluminium plank — no couple. The lag is **316 stainless** because it passes into
   copper-treated KDAT, which eats plain and galvanised steel (AWC DCA6). The butyl separates
   the stand from the wood.
7. **Drain the water away from the holes.** `PR-S-HP1-COND` / `PR-S-HP2-COND`, 3/4", south on
   the deck's own fall, air-gapping 1" over `TR-SG-GUTTER`'s rim — never into it.
8. **Keep it inspectable.** See below.

## Two things that make the odds good

**Nothing dries upward.** `aluminum-deck` is 0.05 perm — vapour-impermeable. Water that gets
into a penetration cannot dry up through the plank. Its only escape is downward.

**`FS-SG-DECK` has no `ceiling_below`**, so the joist bays are open to the porch. That is both
the drying path and the inspection path: a weeping anchor is visible from a chair on the porch
years before it is structural.

> ⚠️ **Never add a soffit under this balcony.** It would close the only drying path the
> penetrations have and hide the only warning they can give. This is a standing constraint,
> not a preference.

## Geometry, and why the legs are not under the feet

Gree publishes a foot-hole pattern per capacity, and it is not negotiable in one direction:
the cast foot's obround slot runs the **width** way, so width has about 1/4" of travel and
depth has none. Both drawings name the exact part number on the sheet.

| | `EQ-M-HP1-OD` | `EQ-M-HP2-OD` |
|---|---|---|
| part | `VIR24HP230V1R32AO` (Vireo **R32**) | `MUL30HP230V1R32AO` (Multi R32) |
| cabinet W x H x D | 37 23/32 x 25 63/64 x 15 53/64 | 40 5/32 x 32 33/64 x 16 13/16 |
| net weight | 92.6 lb | 145.5 lb |
| feet, width / depth | 22 7/16" / **14 39/64"** | 25" / **15 19/32"** |
| centre | x 9'-2", y -2'-10" | x 17'-6", y -2'-10" |
| **frame** | **14 5/8" x 22 7/16"** | **24" x 25"** |
| leg x | 8'-7", 9'-9" | 16'-6", 18'-6" |
| leg y | -2'-2", -3'-6" (bay centres) | same |
| nearest beam | `BM-SG-BLW` at 8'-0" | `BM-SG-BLC` at 18'-0" |
| clear of its axis | 7" / 21" | 18" / 6" |
| clear of a joist line | 8" | 8" |

**The frame is not the leg spacing, and conflating the two was the original error.** The legs
answer to the *deck* — bay centres, six inches off a beam — and the feet answer to the
*cabinet*. They cannot be the same four points: HP1's west foot line lands on `BM-SG-BLW`.
The frame is the part that reconciles them, which is why it has its own dimensions above and
why the rails under the feet must be continuous while the deck-facing members land only on
the eight legs. Leg spacing shorter than the foot pattern misses feet entirely — HP1's feet
sit at ±7.30" and HP2's at ±7.80", so anything under ~15.6" centres catches HP1 and misses
HP2. Cabinet dimensions and foot patterns are cited from the manufacturer's own drawings and
part numbers in the table above, with the document and page on the record in
`plan/electrical.py`. `EQ-M-HP1-OD` had been recorded as a Vireo **GEN3** — a different,
R410A product line with a different foot pattern and a slot running the other way, and 6"
too tall — and `EQ-M-HP2-OD` at 37" wide, the width of the cabinet's *top* rather than its
40 5/32" base; both are corrected in `plan/electrical.py`.

**Six inches from a beam axis is the floor, not four** — 1 3/4" of clear to the face of a
4 1/2" 3-ply is not room for a base plate and its gasket. `mep.deck_equipment_support` fails
anything closer.

**The reinforcement sits on the joist line; the anchors sit at the bay centres.** These are
deliberately different points. `_reinforcement_members` snaps each reinforcement to the
*nearest* joist line and blocks the bay either side at the load's own x — so one
reinforcement on the line yields two blocks, and one anchor goes at the centre of each. Four
reinforcements serve eight anchors. Authoring one per anchor instead needs eight, and where
two of them straddle a single bay it emits that bay's block **twice**, at the same x: double
lumber, double butyl, two coincident solids.

An anchor 3" off a joist line still sits inside the bay, with 2 1/4" of clear to the joist
face. Blocking being present is not the anchor being in it — the check measures the distance
to the joist lines directly.

## 12", and what it costs

The owner's number, against the 18"–24" a cold-climate guide would ask for; local experience is
that wind keeps this balcony's snow depth low in a way a ground-level stand cannot rely on.

What 12" still buys, and what the taller number was mostly for: **airflow**. A 12" stand under
a 32"/34" cabinet puts the coil at 44"/46", clear of the 42" guard, so neither unit sits in the
stagnation pocket behind it. That matters most in *heating*, where the outdoor coil is the
evaporator and recirculated cold discharge depresses apparent ambient, eats cold-climate margin
and triggers more defrost — which makes more of the water in §7.

What it trades away: less clearance over drifted snow, and less room to reach under and chip
ice. Accepted knowingly.

## Not in the model, and needed anyway

- **Heat trace down the leader.** `freeze_protection` is authored on both condensate runs
  (10.8 LF). `TR-SG-LEADER-SE` is a `Downspout`, not a `PipeRun`, so the cable the leader
  actually needs has nothing to hang off. **Add ~12 LF when quoting**, plus the base pans.
  A plugged leader overflows `TR-SG-DRIP` onto the porch.
- **A base pan heater.** The Multi's published "compressor with electric heater" is a
  *crankcase* heater, not a base pan heater. **Verify availability with Gree** — it is the
  single most important cold-climate accessory here and could not be confirmed.
- **Vibration isolation.** M1401.4 requires supports that prevent excessive vibration, and this
  deck is a lightweight, low-damping diaphragm over an occupied porch, freestanding so it has
  no house mass to borrow. **Do not use the $15 ribbed neoprene pads** — they are specified at
  60–120 psi and ≥3600 rpm and these units load them at ~3 psi. Size real spring isolators to
  ~44 lb/corner with ≥1" static deflection, and isolate the **line set**, which is the
  transmission path most often missed.
- **The 12" wall standoff is exactly Gree's minimum**, with zero margin.
- **Gree clearances are not authored** on either `EquipmentType`. `FurnitureType.clearance`
  (front/back/L/R) exists and `advisory.clearance_overlap` would grade it — but that check
  compares against other *placed items*, not walls or guards, so it would not catch the
  12" wall gap. Worth authoring anyway; recorded rather than done.
- Naming: the type is called "Multi Ultra" in `plan/electrical.py` but its `source` and price
  row both cite **MUL30HP230V1R32AO**, a Multi21+ R32. The −22 °F rating is right for that
  part; only the name is off.

## What the check does and does not do

`mep.deck_equipment_support` **grades coverage, not capacity** — the same discipline
`checks/structural/uplift_path.py` keeps. It reports FAIL for an unanchored unit, for an anchor
on a beam or on no blocking, for a heat pump with no condensate path, and for an untraced
condensate line. A fully covered unit reports **UNKNOWN, not PASS**, because nothing in this
model carries a design wind speed (`Site` has `ground_snow_load_psf` and no wind field), and
"there is an anchor here" is a different claim from "this anchor holds".

It also holds together a coupling no import can: the units are authored in
`plan/electrical.py`, the stand in `params/sunken_garden.py`, and those two modules cannot see
each other. The 12" in one and `_HP_STAND_HEIGHT_IN` in the other are one dimension written
twice. **Mind the datum** — `mount.elevation` measures from the storey datum (the joist tops),
while the stand bears on the plank 1 1/2" higher, so the authored mount is 13 1/2" for a 12"
stand. Authoring 12" put both cabinets below the tops of their own legs.

Both must stay storey-scoped, or the check reports confidently about geometry it has not
scoped, which is worse than no check:

* **The deck lookup.** The porch and the balcony share one plan footprint, so a whole-plan
  outline search would match both condensers to the porch ten feet below them, grading the
  *porch pillars'* post bases as the condensers' anchors.
* **The beam lookup.** The porch's back beams run east-west directly under the balcony's
  anchors, so an unscoped beam collector reports an anchor as landing on a beam no lag
  through this deck could reach.

Both are pinned by tests.

## Still open

* **Clearances are still not authored.** They are now known — Gree publishes air-outlet 78",
  above 20", to a wall 20", coil side 12" for the Vireo R32, and 200/50/50/30 cm for the
  Multi R32 — but `EquipmentType.clearance` is a `(front, back, left, right)` tuple and the
  cabinets are rotated 90°, so which published face maps to which tuple slot has to be
  established before authoring, not guessed. `advisory.clearance_overlap` would grade them
  for free once it is.
* **The two units face each other across 84".** Worth checking against the 78" air-outlet
  figure once the orientation above is settled.
* **The MUL30's expansion-screw count falls in a gap** in Gree's own ladder (it covers
  2300–5000 W, 6000–8000 W and 10000–16000 W; this unit is 8.3 kW). Eight is the defensible
  read. That ladder governs fixing the *support* to the structure, not the unit to the
  support — the unit-to-support connection is four bolts, one per cast foot, with no torque
  or size published for it anywhere in either manual.
