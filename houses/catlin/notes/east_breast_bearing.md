# RM-M-LIVING fireplace surround — bearing, and the floor it passes through

**House:** catlin
**Structure:** `W-M-FIRE-STUB-S/-M/-N`, `-PLINTH`, `-JAMB-S`, `-JAMB-N`, `-HEAD` (the 3 5/8" brick wythe — `brown-brick` since 2026-09-13, washed white, `white-brick` before that; five walls on one axis since 2026-09-06 so the firebox opening is a real void, SEVEN since 2026-09-19 so the joist pockets are too), `FIREPLACE_BRICK_WYTHE` (its
assembly), `W-B-E1` (the 12" pour it stands on), `FS-M-EAST` (the floor it passes through —
no opening in it any more; the subfloor cut round the piers is DERIVED,
`resolve/through_deck.py`), `EQ-M-FIREPLACE` (the appliance in it),
`SB-M-FIRE-MANTEL` (the shelf that caps it).
**Written:** 2026-09-06, by hand.
**Oracle for:** no engine calculation — **this note is the whole basis.** Nothing in
`typehaus/engineering/` grades a masonry surround, and nothing in `haus check` looks at this
detail at all (§6). The geometry it rests on is pinned only by the model itself.
**Companions:** `notes/sunken_garden_veneer_beam.md` — the house's other freestanding brick
wythe, and the pattern this note follows; `notes/mixed_deck_movement_joint.md` — the
FS-M-EAST / SL-M-DECK boundary this opening sits south of.
**What is asked of the reviewer:** §4. The load path in §2-§3 is trivial by design. **As of
2026-09-19 this note asks nobody to open a manufacturer's book** — the floor opening that
required one is gone, and with it the last Source line this note could not supply.

> ⚠ **The brick does not bear on the floor, and the whole design depends on that.** It
> starts on `W-B-E1`'s pour at −1'-1 7/16" and rises **through** `FS-M-EAST`. If anyone
> "simplifies" this by starting the wythe on the subfloor, §3's 50 plf limit is exceeded
> roughly four-fold and the detail needs an engineer. That change would look like a
> one-line edit to `Wall.base_elevation` and it is not.

> ⚠ **The pockets are CLEARANCE, not bearing, and two site habits would undo that.** The
> 3/4" either side of each joist stays **open and un-mortared** — mortar in a pocket puts
> brick on a joist and turns this detail back into an engineered one — and the plinth course
> gets a **bond break** (sill seal or building paper) over each slot before it goes up.
> Without one the plinth's bed joint bridges subfloor over ~29 in², worth ~43 plf against
> §3's 50: inside the limit, but unverifiable once the plinth is up. Nothing is cut from any
> joist, so IRC R502.10 does not engage at all — which is why the joist maker's header table,
> the hangers and the web stiffeners are all gone from this detail.

> ⚠ **Keep the appliance ELECTRIC.** `EQ-M-FIREPLACE` is `EQ-T-FIREPLACE-EL`, a 1.5 kW
> electric unit. IRC **R1001.2** requires a *masonry fireplace* to have a 12" concrete
> footing on undisturbed earth below the frost line, with **no wood-floor exception**.
> Keeping it electric keeps R1001 off the table entirely. Put a real firebox in this
> surround and no part of this note survives.

---

## 1. Geometry

| term | working | value |
|---|---|---|
| wythe thickness | `FIREPLACE_BRICK_WYTHE`, one STRUCTURE layer | **3 5/8"** |
| face plane (x) | authored axis 35'-1 11/16" less half the wythe | **34'-11 7/8" = 419.875"** |
| back plane (x) | face + 3 5/8" | **35'-3 1/2" = 423.5"** |
| room finish face (x) | `W-M-E1` interior gwb | 35'-5 3/8" = 425.375" |
| gap behind the wythe | 425.375 − 423.5 | 1 7/8" (ties, and the firebox's framing) |
| panel width (y) | 29 1/2" masonry opening + 8" each side | **45 1/2"**, y 81.25"–126.75" |
| base | `W-B-E1` bearing seat | **−1'-1 7/16" = −13.4375"** |
| top | mantel underside, 5'-4" **AFF** (finished floor is +15/16") | **64.9375"** |
| height | 64.9375 − (−13.4375) | **78 3/8"** |
| `W-B-E1` pour (x) | `BASEMENT_12`, outer face on the 36'-0" line | **420"–432"** |

**The whole footprint stands over the pour, bar 1/8".** The wythe runs 419.875"–423.5" and
the pour 420"–432"; the 0.125" of brick west of the pour's inner face is a mortar line, not
a cantilever. This is the reason the surround is minimal: the earlier 10 3/8"-deep breast
put its centroid 9" inboard of the pour and fully onto the joists. **Minimalism here is not
an aesthetic, it is what puts the brick on the foundation.**

## 2. The load, and where it goes

| term | working | value |
|---|---|---|
| panel volume | 45.5 × 78.375 × 3.625 in³ = 12,927 in³ | **7.48 ft³** |
| masonry density | `brown-brick`, 1,920 kg/m³ | **119.9 pcf** |
| panel weight | 7.48 × 119.9 | **≈ 897 lb** |
| as a line load | 897 lb ÷ 3.79 ft of panel | **≈ 236 plf** |

**The mineral silicate wash adds nothing to this, and that is a modelled fact rather than a
rounding.** The surround gained a 1/8" white wash on its room face 2026-09-13. Its `Material`
authors no `density` and no `areal_density_kg_m2` — correct for a `coating=True` film, which has
no plane of its own — so it contributes **0 plf** to the line load above and this note's numbers
stand unchanged. By hand it would be on the order of 10-15 lb over 20.4 SF, or ~4 plf, against
236. The panel volume row is still the brick's 3 5/8" and not the stack's 3 3/4", deliberately:
the wash is not masonry and must not be weighed as if it were.

That 236 plf goes **brick → mortar bed → `W-B-E1`'s 12" pour → `FT-B-*` → soil.** There is
no wood in the path. `W-B-E1` is a 12" wall carrying `SL-M-DECK`'s 414 SF cast edge; 236 plf
on 12" of concrete is 0.16 psi of added bearing and is not worth a calculation.

**Why the east wall was already the right wall.** `params/main_deck.py` frames `FS-M-EAST`
with `JoistSpec(direction="x", bearing_refs=("W-B-CS", "W-B-CS3", "W-B-E1"))` — the joists
span **east–west and bear on `W-B-E1`**. Load standing near that wall is carried in near
direct shear rather than in bending. The sensitivity, for a point load at distance *a* from
a support on a simply supported span *L* (resolved joist span 214 3/4", east bearing face at
x = 430.75"):

| a | a/L | induced midspan moment `2a/L` | midspan deflection `(a/L)(3 − 4(a/L)²)` |
|---|---|---|---|
| 9 1/16" (this brick's centroid) | 0.042 | **8.4%** | **12.6%** |
| 9 3/8" (the deeper breast that was rejected) | 0.043 | 8.7% | 13.0% |
| L/2 (mid-room) | 0.500 | 100% | 100% |

Both rows are hypothetical: **as built, none of the brick's weight reaches a joist at all.**
The table is here because it is the argument for choosing this wall, and because it bounds
what an accidental floor-borne fraction would cost.

## 3. The 50 plf question does not arise

`preferences.toml` `max_guard_dead_load_on_wood_plf` is **50 plf**. A floor-borne full-brick
surround of this size would run:

| case | working | value |
|---|---|---|
| full panel on wood | 897 lb ÷ 3.79 ft | 236 plf — **4.7×** |
| only the part above the floor | 45.5 × 64 × 3.625 in³ = 6.11 ft³ × 119.9 ÷ 3.79 ft | 193 plf — **3.9×** |

Either way it fails by a wide margin, which is exactly why the brick starts on the pour.
**Result: zero brick dead load on wood, and no engineered item.**

## 4. Going around the joists — and the premise that was never true

**REWRITTEN 2026-09-19.** Until this date this section read: *"The brick face at x = 419.875"
cuts them short of that bearing, so over the panel's 45 1/2" of y no joist can reach its east
support."* **That is false, and everything built on it was framing for a problem that did not
exist.** The joists' ends bear on the mudsill at x 426"–431 1/2". The brick is **3 5/8"
thick**, running x 419 7/8"–423 1/2", and the mudsill starts 2 1/2" east of its back face. A
joist passes *through* the panel and reaches its seat intact. The panel never needed a
joist-free strip; it needed **two holes**.

So the buried stub is **three piers** and the pockets are **real gaps between them** — the
same idiom `plan/storeys/main.py` already uses for the firebox ("the gap between the four
elements, not a subtraction from one"), and the thing that makes the geometry *true*: the
joists run through open air, not through a masonry layer no check can see.

### The stations

Joist axes land on y = **96.000"** and **112.000"** exactly (16" o.c. off y = 0). The stub
line runs y 81 7/8"–126 1/8" and the brick x 419 13/16"–423 7/16".

| | y | length |
|---|---|---|
| `W-M-FIRE-STUB-S` | 81 7/8" → 94" | **12 1/8"** |
| pocket (joist 006) | 94" → 98" | 4" |
| `W-M-FIRE-STUB-M` | 98" → 110" | **12"** |
| pocket (joist 007) | 110" → 114" | 4" |
| `W-M-FIRE-STUB-N` | 114" → 126 1/8" | **12 1/8"** |

Four clearances, and `structural.through_deck_clearance` measures every one of them off the
resolved members: **5/8" / 3/4" / 3/4" / 5/8"**, against a 1/2" threshold. The 5/8" pair are
joists **005** (y = 80") and **008** (y = 128"), which need no pocket at all — and that 5/8"
is *residue*, a 44 1/4" panel laid out on a 16" module, not a margin anybody chose. Read a
future FAIL there as information about whatever widened.

The joist tail continues **2 1/2" past the back of the brick** to the mudsill and keeps its
full 4 3/4" seat under R502.6. Nothing is cut from any joist — the hole is in the brick — so
R502.10 never engages, and R317.1's triggers are ground, weather and below-grade contact,
none of which reaches an interior pier over a conditioned basement.

### What holds the brick over a 4" pocket

`W-M-FIRE-PLINTH`'s own first course, with a foot of bearing either side:

| term | working | value |
|---|---|---|
| course over the slot | 4" clear span, 2 2/3" course, 3 5/8" wythe | — |
| moment | w·L²/8 on the course's own weight | **27.6 in-lb** |
| section modulus | 3.625 × 2.667² / 6 | **3.06 in³** |
| stress | 27.6 / 3.06 | **9 psi** |

Against ~40 psi allowable flexural tension normal to bed joints — and it arches before it
bends. **No steel, no cast ligature.** Bearing on the piers is ~5.5 psi over 36 1/4" × 3 5/8"
of pier; two orders of magnitude of margin, and not an argument in either direction.

**Watch the TMS 402 pier/column line if the pockets ever widen.** A masonry member becomes a
*column* at a horizontal dimension ≤ 3t = 10 7/8", where an 8" minimum least dimension and
minimum vertical reinforcement both bite and a 3 5/8" wythe fails outright. The middle pier
is 12" and has 1 1/8" of room. Do not widen the slots past ~4 1/2" without re-checking.

### The bond break, and the two things that must not be done

- **A bond break — sill seal or building paper — over each pocket before the plinth goes up.**
  Without it the plinth's bed joint bridges subfloor over ~29 in², worth ~43 plf against
  `preferences.toml`'s 50. Inside the limit, but spending most of the margin on a condition
  nobody can inspect once the plinth is up.
- **The pockets stay open and are NOT pointed up.** They are *clearance*, not bearing.
- The sequence is the framer's, and he owes this detail nothing else: joist spacing is
  unchanged and there is no header, trimmer, hanger, stiffener or special layout in it.
  `framer sets joists → mason lays 3 piers to the as-built lines → framer sheets, cutting the
  subfloor around the piers → (later) mason returns for plinth, jambs, head`. All three piers
  land inside a joist bay, each reachable from above through a 13 1/2" clear bay while the
  deck is open.

### What went away with `FO-M-FIRE`

The opening framed a 47 3/4" × 12 5/8" hole: a 2-ply LVL header (`HEADER-FO-M-FIRE-0`), four
full-span 17'-11" trimmer plies, two LUS and two HHUS410 hangers, and I-joist web stiffeners.
Measured off `haus takeoff`: **1.75x11.875 LVL 284 → 204 LF**, **2-1.75x11.875 LVL 16 → 8
LF**, **I-joist 2348 → 2388 LF** (the two cut joists run whole again), **LUS −2**, **HHUS410
−2**, and **plywood-subfloor 3181.8 → 3184.6 SF**, still 100 sheets — the three derived pier
cuts take out less plywood than the one hole did. Brick falls 20.4 → **19.6 SF**.

**Nobody authors the subfloor cut.** `resolve/through_deck.py` derives it from the wall's own
footprint plus a 1/2" saw clearance, less every member footprint, and
`ResolvedFloor.through_walls` carries the pairs so the check and the cut cannot disagree
(decision #78).

### The trimmer erratum this section used to carry, kept because it is a live trap

The opening was first drawn at the brick's own 45 1/2" — the natural thing to write, "the
hole is the size of the thing going through it", and not buildable. `resolve/floors.py` puts
the **first trimmer ply's axis on the opening edge**, so a ply centred there reaches half its
own width *into* the hole at each end, and the brick's last inch at each end stood in the
same air as a trimmer for the full 11 7/8" of joist depth. Nothing caught it:
`structural.member_interference` walks framing against framing, and a wall's masonry layer is
not a member, so the clash sat at 0 FAIL until the resolved member boxes were read by hand.
**`structural.through_deck_clearance` catches that class of clash now** — reconstructed
synthetically it FAILs on a *trimmer*, at 29× the area tolerance, which is why the check is
scoped to every resolved member and not to joists. The trap itself is recorded on
`FO-M-ERV-OA` in `plan/storeys/main.py`, along with `header_size`'s `w_ft <= 4.0` float
boundary, because those two outlive this opening.

**ERRATUM (2026-09-19), kept for the record.** Before the rewrite this section also said
*"below, in `RM-B-GYM`, no brick shows"* and *"this opening cuts [the gym's gypsum]"*. Both
were wrong, in opposite directions. The stub runs to −13 7/16"; the joist soffit is at
−11 7/8" and `FS-M-EAST.ceiling_below` hangs 5/8" under it, so the ceiling plane is −12 1/2"
and **15/16" of brick stands below it** in the gym's corner. And the chase never cut the
gypsum: `resolve/ceiling_over.deck_void_face` reads a mostly-*filled* chase as no void, so
`RM-B-GYM`'s 234 SF and 90 SF planes were identical with and without it. What was cut — then
and now — is the **subfloor**, which is what the three `BASEMENT_12`/`EXT_2X6` section
goldens re-blessed on 2026-09-06 actually recorded. What is built below is board run through
and cut to the wythe with the residue packed.

### 4.1 The mantel overturns under its own weight unless it is held down

**The mantel has a body as of 2026-09-06.** `SB-M-FIRE-MANTEL` used to be hosted on the wall
itself, and a `ResolvedShelfBank` carries width, depth, thickness and a count and **no
position** — no emitter reads `model.shelf_banks`, so the board existed in the cut list and
nowhere else in the engine. It is hosted on `FURN-M-FIRE-MANTEL` (`FT-MANTEL-WALNUT-46`)
now, which puts a real 45 1/2" × 11 1/2" × 2 1/4" solid at **64"–66 1/4" AFF**, sitting on
`W-M-FIRE-HEAD`'s top. The free body below is unchanged, and **still nothing grades it** —
no check tests a cantilevered placeable's tie-back — so this section and the note in
`plan/millwork.py` remain the only record of the hold-down.

`SB-M-FIRE-MANTEL` is a 45 1/2" × 11 1/2" × 2 1/4" walnut board. It bears on the 3 5/8"
wythe, spans the 1 7/8" gap behind it and dies on `W-M-E1`'s gwb at x = 35'-5 3/8",
projecting **6"** into the room. Take moments about the brick's front bearing edge,
x = 34'-11 7/8":

| term | value |
|---|---|
| board volume | 45.5 × 11.5 × 2.25 = 1,177 in³ |
| walnut at 610 kg/m³ | **25.9 lb** |
| centroid, relative to the bearing edge | **0.25" in FRONT of it** |
| net self-weight moment | **−6 in-lb, i.e. overturning** |

**It does not need a load on it. It needs only to not be held down.** At the 10" depth this
was first authored at, the centroid fell 1/2" *behind* the edge and a 2.5 lb tip load
cancelled it — no better in any way that matters. The board must be screwed down at its back
edge into flat blocking laid in `W-M-E1`'s stud bay behind the wythe, and that blocking has
to exist **before** the brick goes up.

The forces are trivial once that line exists. The lever from the bearing edge back to the
gwb is 5 1/2", so 100 lb leaned on the front lip is **109 lb** of tension in the fasteners.
And the board itself is never the question: S = 45.5 × 2.25²/6 = 38.4 in³, so the same 100 lb
at 6" is 600 in-lb and **16 psi** against walnut's ~1,000 psi Fb — a factor of 60. All of the
margin is in the hold-down; none of it is in the wood.

**Nothing in the engine can see any of this.** A `ResolvedShelfBank` carries width, depth,
thickness and a count — no position and no elevation — so the mantel has no geometry
anywhere: it is absent from the 3D and from every section, and no interference, clearance or
bearing check can reach it. This note and the comment on `SB-M-FIRE-MANTEL` are the only
record.

## 5. What is NOT graded here

- **The ties.** The wythe stands 1 7/8" off `W-M-E1`'s gwb and must be tied back to its
  studs. Nothing here designs that tie. At 45 1/2" × 6'-5" of panel it is a light and
  ordinary condition, unlike `W-B-BRICK`'s ~10" reach through foam
  (`notes/sunken_garden_veneer_beam.md` §5.1), but it is not designed.
- **The lintel** over the 29 1/2" × 20 3/8" firebox opening — a rowlock course or a steel
  angle. It carries 11 5/8" of brick to the mantel and nothing else. Not sized here.
- **The mantel's hold-down** — but the *need* for it is worked below in §4.1, because it is
  not a refinement. The fastener count and the blocking are not designed here.
- **Differential movement** between a brick panel bearing on concrete and the wood floor it
  passes through. The floor shrinks and the brick does not. The 1 7/8" behind the wythe and
  a soft joint at the mantel are where that goes; no calculation is offered.
- **Seismic / out-of-plane.** Not considered. SDC A, an interior panel 6'-5" tall.

## 6. What `haus check` looks at, and what it still does not

Stated positively, because a clean report here was silence and not a verdict until
2026-09-19, and is now one verdict and a great deal of silence:

- `structural.masonry_guard_bearing` (`checks/structural/guards.py`) walks **`Wall.guard`
  walls only**. No `W-M-FIRE-*` wall is a guard, so that check never sees it.
- `checks/code/mn_residential/profile.py` **explicitly disclaims IRC R1001–R1004**, the
  fireplace and chimney chapter.
- `building_science.condensation` screens on `any(layer.function == "cladding")`;
  `FIREPLACE_BRICK_WYTHE`'s single layer is STRUCTURE, so it is out of the Glaser scope —
  correctly, since this is an interior panel and not an envelope assembly.
- `structural.floor_opening_header` and `structural.member_interference` **no longer look
  here at all.** There is no floor opening and there are no trimmers, headers or hangers for
  either of them to grade. (For the record: `floor_opening_header` never did emit on
  `FO-M-FIRE` — it appends a finding only past its 8'-0" prescriptive span — so the claim
  this bullet carried until 2026-09-19, that it *"does grade `FO-M-FIRE`, and passes"* and was
  *"the only automatic opinion anything in the engine has about this detail"*, was wrong twice
  over. `member_interference` **did** FAIL four times while the opening ran to the 36'-0" wall
  line and drove all four trimmers through the rim; that is what set the east edge at
  35'-10 3/4", and it is worth knowing the check caught a real framing error here.)
- **`structural.through_deck_clearance` is the one automatic opinion this detail now has, and
  it is a real one.** Six findings, all PASS: a clearance verdict and a bearing verdict per
  pier. The clearance half measures each pier against **every resolved member** of
  `FS-M-EAST` — joists, sisters, blocking, trimmers, headers, rims — and governs at 5/8"
  against a 1/2" threshold. The bearing half is what turns this note's lead ⚠ into a rule:
  start the wythe on the subfloor and it FAILs at ~236 plf against
  `max_masonry_dead_load_on_wood_plf`, instead of relying on somebody reading a box.

**A 0-FAIL report on this house used to mean nothing looked. Since 2026-09-19 something
does** — `through_deck_clearance` — but only at the joist pockets and the bearing. The ties,
the lintel, the mantel hold-down, differential movement and the out-of-plane case are all
still ungraded, and §5 is the list.

## Sources

- IRC 2018 §R502.6 — joist bearing: 1 1/2" minimum on wood or metal. The joists keep their
  full 4 3/4" mudsill seat, because nothing is cut.
- IRC 2018 §R502.10 / R502.10.1 — framed openings in floors. Cited only to record that it no
  longer applies: there is no framed opening in `FS-M-EAST` any more.
- IRC 2018 §R1001.2 — masonry fireplace footings: 12" of concrete on undisturbed earth,
  below the frost line, with no wood-floor exception.
- IRC 2018 §R703.8.4 — masonry veneer drainage cavity (cited for contrast: this is an
  *interior* panel and takes no cavity).
- NFPA 211 — chimneys, fireplaces, vents and solid-fuel appliances. Cited to record that an
  electric firebox is **outside** its scope, which is why no hearth extension is drawn.
- Amantii BI-30-XTRASLIM (BI-X190030-1) installation manual, 2022 CSA revision — rough
  opening 29 × 20 3/8 × 4 1/2", 120 V / 1500 W / 5,118 Btu/h, hardwireable, mantel 4" from
  the trim, combustible facing allowed, no floor clearance and no air-intake slot. **The
  pre-2022 manual under the same model number states 1465 W / 5,000 Btu/h and contains no
  mantel and no hardwire section at all** — confirm which revision ships.
- **DELETED 2026-09-19: "Joist manufacturer's I-joist framing guide — the document §4
  requires and this note does not have."** No joist is cut or headed any more, so no such
  document is required. That deletion is the headline of this change: it retires the one
  outstanding document in the whole detail.
- TMS 402 §5.3 / §5.4 — masonry pier and column limits (cited in §4 for the 3t = 10 7/8" line
  the 12" middle pier must stay above), and §5 for anchored veneer ties, not designed here.
