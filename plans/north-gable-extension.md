# Catlin house — the extruded-gable north connector

**Study date:** 2026-09-08
**Status:** options report only; no plan or code changes are authorized by this study.
**Companion:** `plans/north-entry-options.md` (2026-09-07), whose Option 3 this borrows from.

## Conclusion

The idea is sound and the roof form is better suited to it than the brief realised. Four
findings decide the shape of it.

1. **A 4'-0" extrusion is buildable with no new concrete in the slot at all**, as an
   engineered cantilever off the garage's south gable end. That is the cheapest useful
   version and it answers the excavation worry completely.
2. **A 6'-0" extrusion is geometrically impossible where the garage stands.** Six feet south
   of the garage cladding face lands at y = 34'-7 3/4"; the house cladding face is at
   36'-7 1/4". It would end up **1'-11 1/2" inside the house.** Six feet requires moving the
   garage north, and **2'-0" is not enough — 2'-2" is the minimum and 2'-6" is the number.**
3. **The excavation problem is real, it is not caused by this proposal, and it is already
   built into the model.** The garage's own south footing fails IBC §1809.6's 30°
   adjacent-footing line by 13.7"–25.8" and, on a realistic 1.5:1 excavation slope, bears
   about 16" inside the house excavation's backfill wedge. Nothing in `haus check` grades it.
   The extrusion does not create this; it makes it impossible to keep ignoring, because
   everything the new roof weighs lands on that footing. **The fix is to step that footing
   down to about -8'-9" (1'-9" deeper), or to move the garage north, and to pour it while the
   house excavation is still open.**
4. **The 1–2" gap should be 4–6".** It buys nothing in code terms, nothing in snow terms, and
   in a Minnesota winter it ice-bridges under an 18-foot drift and stays bridged for months.
   The sunken garden's 5" is the precedent and it is the right number.

**Recommendation.** If the garage can move, move it **2'-6" north** and build the 6' version
on four helical piles: it is the only way 6' exists at all, it closes the footing finding for
free, it retires the standing `code.R311_3_exterior_landing` ERROR and the half-door-over-a-
drop condition as side effects, and it buys the wider gap as well. If the garage cannot move,
build the **4'-0" cantilevered version** — which needs no new foundation at all — and **fix
the existing footing separately by stepping it down to about -8'-9"**.

**On excavation specifically, since it was the question asked:** the scheme *reduces* concrete
work in the congested slot. The breezeway it replaces needs eight separate small pours — four
pads and four piers — between two foundations 3'-8" apart. The 4' extrusion needs **none**;
the 6' extrusion needs four driven piles with no excavation and no concrete. The one piece of
new below-grade work either version implies is **fixing a condition that is already there**,
and the cheapest moment to do it is while the house hole is still open.

**One unforced trade to put in front of the owner now:** the full 24' width puts
`WIN-M-KITCH` (x = 29'-4") under the roof. Stopping the extrusion near x = 27'-0" saves the
kitchen window and costs 3'-0" of shelter.

## What the current plan gives us

Project frame, +y north, main-floor top-of-joist = 0'-0", grade = -2'-10".

| Existing fact | Consequence |
|---|---|
| Garage x 6'-0"..30'-0", y 40'-8 5/8"..64'-8 5/8", centred on the house ridge at x = 18'. | The extrusion is 24' wide and symmetrical about the house's own centreline. |
| Clear slot: house cladding 36'-7 1/4" to garage cladding 40'-7 3/4" = **4'-0 1/2"**. | 4'-0" is the whole available depth. 6' needs the garage to move. |
| `RF-GARAGE`: GABLE, 4:12, `ridge_direction="y"`, bearing `W-G-E`/`W-G-W`, 16" overhang. | **The south edge is a rake.** Extruding it is a gable extension, not a lean-to. |
| Resolved: bearing +7'-4", eave +7'-11.4", **ridge +12'-4 3/4"**. | Implies a 1'-0 3/4" raised heel, and reproduces the verified rake undersides exactly. |
| `RF-HOUSE`: GABLE, 6:12, `ridge_direction="y"`, **`overhang=ft(0)`**. | The house's north face is a **vertical gable end rising to +30'-3"** — 33'-1" above grade — with no overhang. The slot is a canyon, not a gap between eaves. |
| Neither building's gutters face the slot; both shed E and W. | No new water direction is created. This is the form's biggest single advantage. |
| `D-M-ENTRY` centre x = 8'-0", pinned by the `W-M-STRW` bearing tee. `D-G-SERVICE` centre x = 10'-0". | 2'-0" out of line; half the garage leaf opens onto air over a 2'-10" drop. A standing ERROR. |
| Existing headroom 7'-3 1/4" clear, but roof beams soffit at **+6'-3 1/2"** — below a 6'-8" door head. | Anyone reaching for either glazed wall ducks. |
| `EQ-M-HP3-OD` stands in the slot, discharging north with 25 11/16" of clear air. | In the way, and already short of its own manufacturer's figure. |
| Parcel y -60'..105', 30' FRONT setback on the north edge → build line y = 75'. Garage north wall at 64'-8 5/8". | **10'-3 3/8" of slack to move the garage north.** The setback is not the constraint. |

Controlling sources: [garage plan](../houses/catlin/plan/storeys/garage.py),
[breezeway](../houses/catlin/params/breezeway.py),
[foundations](../houses/catlin/params/foundations.py),
[site](../houses/catlin/plan/site.py),
[HP3 pad](../houses/catlin/params/hp3_pad.py),
[roof trim](../houses/catlin/params/roof_trim.py).

## The scheme

### Why the rake already faces the right way

The 2026-09-07 decision to turn the garage ridge to `"y"` and centre the garage on x = 18'
was taken for the driveway and the facade. It happens to be what makes this proposal work.
Because the ridge runs north-south, extruding it south **keeps the slopes facing east and
west**. The extension sheds into the existing troughs; nothing discharges into the slot; and
the south edge is a rake, so only a thin film runs along the edge nearest the house. Every
lean-to or shed-canopy scheme over this slot fails on exactly that point.

It also threads the facade. Roof underside over the slot is
`z(x) = 8'-4 3/4" + (x - 6')/3` for 6' <= x <= 18', mirrored about the ridge:

| x | roof underside | over the +0'-0" floor |
|---|---|---|
| 6'-0" (west plate line) | +8'-4 3/4" | 8'-4 3/4" |
| **8'-0" (`D-M-ENTRY`)** | **+9'-0 3/4"** | **9'-0 3/4"** |
| **10'-0" (`D-G-SERVICE`)** | **+9'-8 3/4"** | **9'-8 3/4"** |
| 18'-0" (ridge) | +12'-4 3/4" | 12'-4 3/4" |

Against today's 6'-3 1/2" beam soffit that is **+2'-9 1/4" at the house door and +3'-5 1/4"
at the garage door**, and — because the only deep members sit at the extreme edges, x = 6'
and x = 30' — **nothing crosses the 4'-0 1/2" walk at all.** The two beams that currently
crowd the space disappear with the breezeway.

Above, the extrusion passes cleanly under the whole second storey: the ridge at +12'-4 3/4"
lands in the blank facade band that `WIN-S-STAIR-N` (x = 12') and `WIN-S-HALL-N` (x = 24')
leave, with 3'-1 1/4" of clear wall below both sills.

### The cost on the main storey

`WIN-M-KITCH` at x = 29'-4" has its head at +6'-6". The roof underside there is about
+7'-6 1/4". **The kitchen sink window ends up entirely under the canopy** and loses its north
sky. Nothing grades this — `code.R303_1` counts glazing area, not obstruction, and the IRC has
no daylight-obstruction rule for a window under a porch roof.

`WIN-M-KITCH-N` at x = 34'-0" is east of the roof edge at 31'-4" and survives.

**Stopping the extrusion at x = 27'-0" saves the window and costs 3'-0" of shelter.** This is
a real choice and it belongs with the owner, not in a soffit detail. It is the same trade
`north-entry-options.md` identified for Option 1, arriving from a different direction.

### The floor, and the ERROR it closes

A single gallery floor at +0'-0" running x 6'..30' gives each door **48 1/2"** of landing
depth against R311.3's 36" (6'-0 1/2" in the moved-garage variant), full width, flush with
both thresholds. It retires the out-of-line doors as a problem: two doors 2' apart on a 24'
gallery is not a collision, it is the 90-degree turn the entry wanted. `code.R311_3_exterior_landing`
accepts an `ImperviousSurface`, a slab, a `deck_outline` or a stair landing, so this closes
the standing ERROR with no structural gymnastics.

It costs a stair. 34" of rise is five ~6.8" risers; four treads at 10" plus a 36" top landing
is 76" of run, which fits at roughly x 22'..28' descending east, under roof, with 11'+ of
headroom. A guard is needed at the open edges of the stair (`structural.deck_guard`).

**Deleting the breezeway without re-authoring a landing does not clear the ERROR — it makes it
worse**, leaving `D-G-SERVICE` opening onto a 2'-10" drop with no deck at all.

### The west wall

In the plane of the garage's west wall at x = 6'-0", full slot depth, floor to roof underside
= **8'-4 3/4" tall**. The 16" rake overhang oversails it to x = 4'-8", keeping its head dry.

`BREEZEWAY_GLAZED_WALL` transfers directly — same 16 mm multiwall, same U/F/H extrusion
vocabulary, same weeped sill on a curb 1"–2" proud of the floor so boot-melt never stands in
the channel. The head meets a framed deck rather than a roof sheet, so it wants an F-channel
under a formed closure, not the existing shared H.

8'-4 3/4" does not come out of a 4'x8' sheet, so the uncut-sheet discipline that governs
`params/breezeway.py` is spent either way. One 4'x10' sheet cut once, flutes vertical.

**Specify opal, and drop the bird film.** `SOLYX BSF-DB35` is on the existing walls because
vertical glazing is where a strike happens — but a strike needs a see-through condition, and
the existing breezeway has two parallel glazed walls with sky through both. Here there is one
end wall with a solid building behind it. Opal diffusing multiwall designs the problem out
rather than filming over it, and it hides dirt, webs and dust while diffusing the west light.
That deletes a surface treatment and a line item.

## Foundations and excavation

This is the section the owner asked for. It contains **three separate problems**, only one of
which is caused by this proposal, and each has a different fix. The short version:

| # | Problem | Fix | Cost |
|---|---|---|---|
| **P1** | The **existing** garage south footing sits too close and too high beside the house excavation — 30° rule missed by 13.7"–25.8", ~16" of it in the backfill wedge. | **Deepen it to about -8'-9"** (a stepped footing, 1'-9" deeper), **or** move the garage 2'-6" north, **or** engineered backfill with a geotech's sign-off. | ~1 cy of concrete + 3 cy of dig, or free if the garage moves anyway |
| **P2** | **No new frost-depth footing can ever go in the slot** — at any garage position, at any slot width. | **Don't put one there.** 4' version: cantilever off the garage, zero new foundation. 6' version: four helical piles bearing *below* the house excavation. | $0 / $5–9k |
| **P3** | **Construction congestion** — three different bearing depths within 4'-0 1/2", the last two placed on the first one's backfill, in a trench beside a 33-foot wall. | **One excavation, one pour sequence**, and delete the eight small pours the breezeway puts in the tightest place on site. | net saving |

**The proposal makes P3 better, not worse.** That is the answer to the owner's original worry
and it deserves to be said first: the existing breezeway needs **four pads and four piers —
eight separate small pours** — in the 4'-0 1/2" slot. The 4' cantilevered extrusion needs
**none**, and the 6' version needs four driven piles with no excavation and no concrete at
all. **The scheme takes concrete work out of the congested zone rather than adding it.**


### The rule, stated properly

The repo reasons in a **45° influence line** (the `FX-G-HYDRANT` clear zone off `FT-GF-W`).
The adopted model code is stricter. [IBC §1809.6](https://up.codes/s/location-of-footings):

> Footings on granular soil shall be so located that the line drawn between the lower edges of
> adjacent footings shall not have a slope steeper than **30 degrees** with the horizontal…

30° means the required horizontal is `dz x 1.732`, not `dz x 1.000`.

| pair | dz | 45° needs | **30° needs** | have | 30° margin |
|---|---|---|---|---|---|
| House footing bottom (-117.44") vs garage footing (-84") | 33.44" | 33.44" | **57.91"** | 44.20" | **-13.71" FAIL** |
| House **bedding** underside (-124.44") vs garage footing | 40.44" | 40.44" | **70.04"** | 44.20" | **-25.84" FAIL** |
| House bedding vs a **new slot footing** at -76" | 48.44" | 48.44" | **83.90"** | <= 4.2" | catastrophic |

And a second check nobody has run. The house was dug first. A safe open cut in GM is 1:1 to
1.5:1. From excavation bottom -124.44" at y = 440.088", a **1.5:1** slope reaches y = 500.74"
at the garage's bearing plane. The garage south footing spans y 484.288"..504.288".
**About 16.4" of it is inside the house excavation's backfill wedge.** At 1:1 it clears by
3.8", with no margin for over-dig and no `FootingBedding` under it to make the point moot.

> **F-1.** The garage's south footing, as built in the model today, fails IBC §1809.6 by
> 13.7"–25.8" and probably bears partly on the house's backfill. This is a **pre-existing
> condition, not something the extrusion introduces** — but the extrusion lands its whole
> weight on it. Nothing in `haus check` grades footing against footing; the engine's only
> 45° reasoning is `checks/mep/plumbing_concrete.py`, which grades pipes against footings.

**The corollary that settles the whole question.** The controlling geometry is measured from
the *house* footing, which does not move. So **there is no y-coordinate anywhere in the slot,
at any garage position and any slot width, where a new frost-depth (-76") footing satisfies
§1809.6.** Its south face would have to be at y >= 43'-8" — inside the garage. Shallow
foundations in the slot are not a design choice that failed; they are unavailable.

### Fixing P1 — the footing that is already there

Three routes, and the choice depends on whether the garage moves.

**(a) Deepen the garage's south footing. The fix that keeps the garage where it stands.**
The 30° rule is about the *difference* in bearing elevation, so lowering the higher footing
shrinks the demand. With 44.20" of clear, the geometry permits `dz <= 25.52"`:

| garage footing bottom | dz to bedding | 30° needs | margin | 1.5:1 wedge margin |
|---|---|---|---|---|
| **-7'-0" (today)** | 40.44" | 70.04" | **-25.84"** | **-16.5"** |
| -7'-8" | 32.52" | 56.32" | -12.12" | -4.6" |
| -8'-3" | 25.52" | 44.20" | +0.00" | +5.9" |
| **-8'-9" (recommended)** | 19.44" | 33.67" | **+10.53"** | **+15.0"** |

**Step the south wall line down to -8'-9"** — 1'-9" deeper than today — with the east and west
walls stepping down to meet it as they run south, per IRC R403.1.5 (steps not less than 2'-0"
horizontal, vertical not more than 3/4 of the horizontal; 21" of drop needs 28" of run, and
there is 24' to do it in). That clears both tests with real margin. It costs roughly **1 cy of
extra concrete and 3 cy of extra excavation on one wall line**, plus two or three more courses
of ICF — a few hundred dollars, not a redesign.

**(b) Move the garage 2'-6" north.** Closes P1 outright (74.20" of clear against the 70.04"
required) with no deepening at all, and buys the 6' slot, the wider gap and the pile access as
well. If the garage is moving anyway, **this is free** and (a) is unnecessary.

**(c) Engineered backfill plus a geotechnical sign-off.** §1809.6 itself provides the escape:
the rule applies *"unless the material supporting the higher footing is braced or retained or
otherwise laterally supported in an approved manner or a greater slope has been properly
established by engineering analysis."* Compacted structural fill in controlled lifts, tested,
with an engineer's letter, is a legitimate answer and is what many builders would do. It is
listed third because it converts a geometry problem into a *workmanship and paperwork*
problem, and this project has no soils report to start from.

**Whichever route is taken, the sequence is the same and it is the real point:** the garage
foundation must be formed and poured **while the house excavation is still open, or at least
before it is backfilled.** Digging an 8'-9" trench 3'-8" from a finished basement wall is a
shoring exercise; digging it as part of one open cut is a morning's work. That is the
"excavation and concrete simplicity" the owner asked about, and it is a scheduling decision
rather than a design one — which is exactly why it needs writing down now, since nothing in
the model or in `haus check` will ever mention it.

Two more obstructions in the same band, for completeness: `PR-G-HYDRANT-CW` crosses the
**entire width of the slot** at y = 38'-0", x 5'->11', at -8'-10", and its own note says that
band is "the only place it can be"; and `structural.concrete_interference` would not catch a
new pier in an influence cone anyway, because it tests 3-D volume overlap, never proximity.

### Fixing P2 — what will not carry the new roof

- **A bent on the garage's south stem, cantilevering.** Overturning needs a ~4'-6" wide
  footing to stay inside 1,500 psf; its south face would land 21.5" from the house footing
  against the 70" required. Dead end.
- **Extending `W-G-E`/`W-G-W` south on footings.** Structurally the cleanest and the only
  answer the *engine* likes — but those footings land ~0.9" from the house footing, 41" above
  its bottom, in backfill. Fails by 69".
- **Reusing the four breezeway piers.** Three independent reasons. They sit in a 4' cluster at
  x 6'..10' and cannot carry a 24' roof. The famous d/c 0.006 is the *concrete section*; the
  governing capacity is the 16"x16" **pad** at 1,500 psf = **2,670 lb**, against ~4,800 lb of
  service reaction per line. And `PD-BW-1/2` are themselves the F-1 condition — bearing on the
  house's backfill, lapping its footing footprint by 1 3/4".
- **A frost-protected shallow foundation.** [IRC R403.3](https://codes.iccsafe.org/s/IRC2018P7/part-iii-building-planning-and-construction/IRC2018P7-Pt03-Ch04-SecR403.3)
  says FPSF "shall not be used for unheated spaces such as porches… garages and carports."
  [ASCE 32](https://amplify.asce.org/asce32) does cover unheated buildings, but at Ramsey
  County's air-freezing index it wants 5–6 ft of horizontal wing on both sides. Impossible in
  a 4' slot, and half of it would lie over the house's drain tile.

### Fixing P2 — what will

**Option A — cantilever off the garage's south gable end. Works at 4'-0". No new concrete.**

Outlookers at 24" o.c. on 2'-0" tributary, designed for the drift of the next section:

- M at the root ≈ **1,662 ft-lb**; V ≈ 803 lb
- 2x8 SPF #2: 18,250 in-lb capacity against 19,940 in-lb demand — **fails, d/c 1.09**
- **2x10 SPF #2: 27,230 in-lb — passes, d/c 0.73**
- Backspan >= 2x the cantilever = **8'-0"**, so each outlooker notches into **dropped top
  chords on five trusses**; uplift at the back bearing ≈ 208 lb each, ~2,700 lb total.

At 6'-0" the same scheme needs a 1.75x11.875 LVL on a 12' backspan across seven dropped-chord
trusses with 3,900 lb of uplift — re-engineering the garage roof to buy 2 feet.

**This is a sealed-engineering item, not a detail.** AWC's WFCM permits cantilevered
outlookers to 24" and ladder framing to 12" ([Simpson SE Blog](https://seblog.strongtie.com/2016/09/designing-overhangs-gable-ends/),
[IRC R802.3.2 / R609.4.5](https://up.codes/s/gable-overhang)). A 4' rake overhang is twice the
cantilevered limit, and there is no prescriptive IRC path for a wood rake overhang of any
depth. It is nonetheless an ordinary thing — post-frame buildings do it routinely.

**Option E — helical piles. The answer for the 6' version.**

A helical pile inverts the §1809.6 geometry: the helix bears **below** the house footing's
plane, the shaft develops nothing in the backfill it passes through, and **there is no
excavation in the slot at all** — no trench beside a 33-foot wall.

- Helix at **-12' to -15'**, 20–30" below the house excavation bottom, into undisturbed till.
- A 2-7/8" or 3-1/2" shaft with a 10"–12" lead is routinely torque-verified at 20–30 kip in
  Des Moines-lobe till ([ICC-ES ESR-4892](https://cdn-v2.icc-es.org/wp-content/uploads/report-directory/ESR-4892.pdf)).
  Four piles under the 6' scheme is ~3,431 lb each — d/c ≈ 0.13.
- Frost is satisfied by bearing depth; sleeve the shaft through the 42" heave zone.
- **Access is the catch, and it is what ties this to the garage move.** A hydraulic drive head
  wants ~6' of working room. In a 4'-0 1/2" slot beside a 33' wall it does not fit. In a
  6'-6 1/2" slot it is a normal day's work.
- ~$1,000–1,600/pile installed plus a Minnesota-licensed engineer's sealed design: **$5–9k**.
- Bearing lines at x ≈ 6'-6" and x ≈ 29'-6" clear the water lateral; anything between x = 9'
  and x = 13' does not.

### The garage-move-north variant, and why 2'-0" is not enough

| move | slot | garage ftg south face | clear to house ftg | vs 30°/bedding (70.04") | vs 1.5:1 wedge |
|---|---|---|---|---|---|
| 0 | 4'-0 1/2" | 484.288" | 44.20" | **-25.84"** | **-16.45"** |
| 2'-0" | 6'-0 1/2" | 508.288" | 68.20" | **-1.84"** | +7.55" |
| 2'-2" | 6'-2 1/2" | 510.288" | 70.20" | **+0.16"** | +9.55" |
| **2'-6"** | **6'-6 1/2"** | 514.288" | 74.20" | **+4.16"** | +13.55" |

> **F-2.** 2'-0" clears the repo's own 45° convention with 27.8" to spare and then misses the
> 30° line by under two inches. The minimum is **2'-2"**; the number to build is **2'-6"**,
> which also happens to give the 6'-0" ask plus room for a real gap and a pile drive head.

After a 2'-6" move the garage's north wall is at 67'-2 5/8" — 7'-9 3/8" inside the build line.
(`code.site_setback` measures wall-axis endpoints only, so the 16" overhang is ungraded either
way; not a problem here, worth knowing before anyone moves it further.)

**What the move buys:** F-1 closed; 6' possible at all; helical piles installable; the R311.3
ERROR and the half-door-over-a-drop retired; HP3's discharge slot restored; and the 4–6" gap
for free.

**Blast radius.** Most of it derives. `GARAGE_Y_SOUTH`/`NORTH` are the two numbers that move,
and since the 2026-09-07 pass `params/foundations.py` derives every node, all nine stem walls,
all nine footings, the slab and the landing from them. The walls, roof, cladding cuts and the
76.5 LF of Z-flash are a pure y-translation. **The 24" stud-module constraint does not apply
to a y-move** — that constraint is measured along `W-G-S` — which is why this is cheaper than
the September x-move was.

Hand-maintained, and must be edited: **`TR-G-LEADER-E`/`-W`**, which are authored absolute and
whose own comment says they "have to follow it by hand" (`test_drainage_elements.py` holds
them); `PR-G-HYDRANT-CW`'s north leg and `FX-G-HYDRANT` (+2'-6" of PEX, ~$40); the two north
spot elevations, of which **(32', 45') needs re-checking** against a grading check that passes
"by only 0.6 points"; and every prose comment restating "4' north of the house". The September
note found two coordinates in its *own* section stale by 6'-0" for exactly this reason.

Consequential rather than mechanical: **`params/breezeway.py` is retired, not edited** — its
entire argument is an uncut 4'-0" sheet in a 4'-0 1/2" slot, and at 6'-6 1/2" that argument is
gone, taking `notes/breezeway_piers.md` and `tests/test_pier_calcs.py` with it. And check the
golden set count: `resolve/stacking.py::stack_width_change` fires on a 0.5" tolerance, and the
three garage details that gained `FS-BW-FLOOR` in September lose it.

**Cost.** The September move — bigger, in x, carrying doors — netted -$88 to -$139. A pure
y-translation should be smaller. Retiring the breezeway removes four piers, four pads, four
posts, a deck and three polycarbonate sheets. There is no `Driveway` element in the model and
never has been, so the apron cost is prose, not quantity. **The move is very likely
cost-negative before the new roof is priced.**

## Snow — the load in the model is roughly half right

### Balanced

`Site.ground_snow_load_psf = 50`, and the house prints `Pf = 0.7 x 50 = 35 psf` at
fully-exposed heated defaults. **Neither default applies to this canopy.** It is an
**unheated, open-air structure** (`Ct = 1.2`) and, depending on how sheltered a 4–6' slot
between two taller buildings is judged to be, `Ce` is 1.0 to 1.2. That puts the balanced load
at **42–50 psf**, not 35. The 4:12 slope earns no `Cs` reduction because a gutter is an
obstruction.

### Drift — and this is what is actually missing

The extension is a low roof standing essentially **zero distance** from a 36'-wide wall rising
18–22 ft above it. That is a textbook drift case, and ASCE 7-16 **§7.7.2** exists precisely to
catch a small separation: where `s < 20 ft` and `s < 6h`, the lower roof takes the §7.7.1
drift. Here `s ≈ 1–2 inches`. Neither limiter bites.

With `gamma = 0.13(50) + 14 = 20.5 pcf`, leeward `l_u = 36 ft`:
`h_d = 0.43(36)^(1/3)(60)^(1/4) - 1.5 = 2.45 ft`, so `p_d = 50.3 psf` at the house wall,
falling linearly to zero **9.81 ft** north — which is **wider than the extension is deep, so
the whole bay carries surcharge and there is no unloaded portion.**

| station | balanced | drift | total |
|---|---|---|---|
| at the house wall | 50.4 | 50.3 | **~101 psf** |
| 4 ft north | 50.4 | 29.8 | 80 psf |
| >= 9.81 ft north | 50.4 | 0 | 50 psf |

Design the extruded bay for **90–101 psf** — roughly **2.2x** what the rest of the garage roof
carries — and note that the drift piles **at the far tip of the cantilever**, which is the
worst possible place for it. Uplift on a one-end-closed open roof at V_ult 115 mph, Exposure B
is a separate governing case with no help from the house across the gap.

> **F-3.** Deliberately not touching the house **buys nothing in snow terms.** §7.7.2 is
> written for exactly this gap.

> **F-4, and it applies retroactively.** `GL-BW-ROOF` — the existing 4'x4' polycarbonate
> canopy sheet — sits half an inch from that same 33-foot wall, and `notes/breezeway_piers.md`
> loads it at **50 psf flat**, declining any C-factor as "a screening load on a pier at
> d/c 0.006." That reasoning is sound *for the pier* and unsound *for the sheet*. The correct
> load is **~101 psf (~490 kg/m2)**, against multiwall span tables that treat ~31 psf as the
> heavy-snow case. The sheet spans 12–16" between rafters, which may well save it — but the
> question has never been asked, and the answer is a manufacturer span chart, not a judgement.
> Re-running the piers at 101 psf leaves them at d/c 0.007. **The piers were never the risk.**

### Sliding snow

**No new target in the slot, and the September reasoning holds.** The extension's slopes still
face E and W. `RF-HOUSE` is a zero-overhang gable end on the north — a vertical wall sheds no
snow. `structural.sliding_snow`'s silence is the design fact, not a blind spot.

**But the extrusion drags both discharge bands 2'-8" south, onto the arrival route.** The east
band lands over `ED-M-HP1-DISC` at x = 32'-5" — the disconnect that already has no NEC 110.26
working space — and 1'-8" from `EQ-M-HP1-OD`. HP1's siting argument ("nothing sheds onto it")
stops being true; the cabinet did not move, the roof came to it.

**Reinstate snow retention on the east and west eaves of the extruded bay**, y ≈ 36'-9"..42'-0",
two rows of S-5! ColorGard per slope. This is not a resurrection of the deleted canopy row —
it is a new requirement in a new place, protecting people and a disconnect rather than a
polycarbonate sheet. The crossbar bills its seam clamps automatically through
`StructuralHardware.requires_role`, so the census stays self-maintaining.

## Water

### The leaders must reverse

Extruding the roof extends both 5" troughs south by 2'-8"; tributary goes 290 -> 338 sf per
slope (362 sf at 6'). **The existing 3" leaders stay adequate** — 3" clears ~425 sf at the
design intensity, so margin is 15–20%. No upsizing.

The problem is the low point. Both troughs fall **1/16 in/ft south**, so extruded, both
leaders land at y ≈ 36'-9" — **1 3/4" from the house cladding.** A 3" downspout does not fit in
the gap; it would stand inside the room. And each landing is worse than that: the west leader
lands 16" from HP3's proposed new site and beside the polycarbonate wall's foot; the east
leader lands **1'-1 3/4" west of `ED-M-HP1-DISC`**, in the 14" band that already has no working
space. Both would discharge beside the house's own 4" leaders (648 sf each, at y = 35'-6") onto
ground with **no spot elevation at all**.

**Reverse the fall. Slope both troughs north and move both leaders to the garage's north
corners**, y ≈ 41'-0", splash blocks in the north yard on the existing convention. This takes
~340 sf of concentrated runoff out of the un-surveyed slot entirely. It costs 6'-0" more fall
on each trough — check the trough's back-leg depth, or run 1/32 in/ft. It also re-argues the
September "both at the south end, and that is the fall, not a habit" decision, deliberately.

### At the gap

Three sources arrive at that line and they are not equal.

- **The extension's own roof: almost nothing** — the south edge is a rake, so only the film
  within a few inches of the barge runs along it. Detail it as a **water stop, not a drip
  edge**: a hemmed, upturned 1" leg that kicks the film back onto the field.
- **The house wall: this is the real load.** `RF-HOUSE` has zero overhang, so every drop that
  hits a 36'-wide gable rising to +30'-3" runs down the wall to grade. Today it lands on
  gravel. It would land on the closure, as a sheet, over 24'.
- **Wind-driven rain**, which even 1/4"–3/8" gaps admit
  ([BSD-013](https://buildingscience.com/documents/digests/bsd-013-rain-control-in-buildings)).
  Acceptable only if what is under the gap is a drained trough returning water to the roof.

### At grade

The extrusion **roofs 97 sf (or 145 sf)**, which is the good news: less water reaches the slot
than today. But three things need authoring. Two hardscape spot elevations must be reinstated
in the slot — as `ImperviousSurface` rows, which `code.R401_3_impervious` reads at 2%, not as
new soil stations in a perimeter ring whose margin is 0.6 points. The "front walk" apron
changes role from exposed walk to the gallery's ground and should extend x 6'..30', keeping its
4.2% east fall, now as the drainage path for what enters the east mouth. And it needs the
**controlled east outlet with a removable boot tray** that `north-entry-options.md` already
specified, rather than an interior drain whose freeze protection is unresolved.

## The gap detail

### It should be 4–6", not 1–2"

**What a 1–2" gap can do:** be a nominal separation on paper, keep the extension's own roof
water out (a genuine gift of the ridge direction), take a brush lip, close against insects in
summer.

**What it cannot:**

- **Survive a winter open.** At the base of an 18-ft drift it fills and freezes into a
  continuous ice bridge for the full 24'. Once bridged, the "movement joint" transmits load
  and movement through ice — the opposite of its purpose — and meltwater enters under head.
- **Be serviced.** A 24'-long, 1–2"-wide, 4–6"-deep slot cannot be reached, cleaned or
  inspected. Leaves and grit accumulate with no way out.
- **Have a real fall.** At 1–2" of reach, 1:12 is 1/12"–1/6" of drop. That is a tolerance, not
  a slope. It will hold water and freeze.
- **Absorb the movement it was drawn for.** A full basement on one side and piles on the other,
  plus 24' of thermal length in a 130°F annual swing, is plausibly more than 1–2".
- **Handle the house wall's runoff** — 36' of overhang-free gable above a 1 3/4" catchment.

**Widen it to 4–6", matching the sunken garden's 5".** That precedent works because 5" is
enough to slope a closure ~1/2" and to reach it. **The 2'-6" garage move buys this for free** —
spend 2" of the extra 24" on the joint and still keep 5'-10" of passage. If the garage cannot
move, take it out of the garage side: build 3'-8 1/2" of extension instead of 3'-10 1/2". The
cost is 2" of floor; the gain is a joint that can be built and maintained.

### The detail, following `TR-SG-SLOT`

Three pieces, one fastener line:

1. **Barge water stop** — hemmed upturned leg on the extension's south rake, fixed to the last
   rafter.
2. **The slot closure** — `TR-SG-SLOT` inverted. A formed aluminium tray, `TrimKind.BUG_SCREEN`,
   hosted by the extension, cantilevering south across the gap, **falling NORTH ~1:12 to drain
   back onto its own roof field**, dying on the house cladding through a **compressible
   closed-cell foam or nylon brush lip that bears and does not penetrate.** Screwed to the
   extension's rim only, exactly as `PORCH_SLOT_CLOSURE` screws to the porch deck's north rim
   only. The sunken garden's note has the reason right: *"a compressible seal tolerates the
   differential movement a rigid one would tear itself apart on."*
3. **A house-side deflector**, fixed only into the board-and-batten's **batten** fastener line,
   oversailing the closure by 1 1/2" to throw the wall sheet clear.

**Do not lap a counterflashing under the house cladding.** A correction to the brief's premise
first: the house's north wall is **`board-batten-24`**, a concealed-fastener rainscreen — the
*corrugated* panel is the garage. Sliding a cover leg up behind it means lifting or slitting
the cladding and setting a leg in the drained cavity, which needs a fastener in the house wall,
risks damming the cavity's own weep at exactly the wrong line, and creates an upward-facing
capture for everything the gable washes down. The sunken garden was granted *"no permission to
fasten into the house wall assembly"* and that discipline should hold here.

**Exclusion sizing:** the lip must close to **<= 1/4"** along its whole length — a mouse passes
1/4", a rat 1/2". Where mesh is needed use 19-gauge 1/4" stainless hardware cloth, and never
across the closure's drainage path.

## Fire

The owner's goal is stated as reasonable effort, not a design basis: that an EV fire can be
contained without taking the house with it. This section is scoped to match.

### The code's test is a distance, not the word "detached"

The IRC never defines "attached" or "detached", and R302.6 does not use either word. Its
fourth row governs *"garages located less than 3 feet from a dwelling unit on the same lot"*.
**Detachment does not exempt a garage; distance does**, and the threshold is 3 feet. Catlin's
4'-0 1/2" clears it by **12 1/2 inches**.

So the code risk is narrow and specific: the extrusion does not move the garage wall, but it
puts garage-borne roof structure 1–2" from the dwelling and **invites an official to measure
the 3 feet to the new roof edge.** Ask before committing, in writing, and lead with the
4'-0 1/2" measurement rather than with the word "detached" — it is the code's own test and it
is the argument the owner wins.

**If the ruling goes badly, the consequence is small.** `GARAGE_WALL_2X6` already carries 5/8"
gypsum and `GARAGE_ROOF` a 5/8" ceiling where the table asks 1/2", and the garage is already on
frost-depth footings. Three live exposures:

1. **`D-G-SERVICE` declares no core and no rating.** `DT-EXT-SWING36` is **shared with
   `D-M-ENTRY`**, so rating it means minting a sibling type, not editing this one. Worth doing
   regardless: the 2018 IRC deleted the self-closing requirement, 2021/2024 restores it, and MN
   DLI's TAG has recommended the 2024 IRC with enforcement likely late 2026 / early 2027. ~$300.
2. **Attic continuity** — R302.11 item 2, an interconnection between concealed spaces.
3. **The polycarbonate wall.** MN deletes all IRC appendices except K and Q, so Appendix H
   (Patio Covers) does not exist here; a light-transmitting plastic panel in an unenclosed
   accessory structure lands under Minn. R. 1300.0110 alternate materials — which is how the
   existing breezeway got built.

`R302.1` does not change: Exception 2 exempts walls of a dwelling and its accessory structures
on the same lot, and the commentary treats them as one building.

### Does roofing the slot make containment worse?

Probably yes, at the margin, and for one specific reason: **the roof plane, sheathing and
concealed attic volume crossing the slot all belong to the garage**, and today the slot vents
straight to sky. The mitigation is the same detail the code question wants and is the highest-
leverage item in this section:

> **A fireblocked gable-end closure in the plane of the garage's existing south wall**, sealed
> to the roof sheathing with mineral wool. The roof still reads as continuous; the concealed
> volume is severed at the garage face. Do it regardless of any ruling. ~$200–600 and a day.

The 1–2" gap itself is not a fire measure and should not be claimed as one. A gap at the far
end of a continuous roof plane interrupts nothing.

### What actually buys containment, ranked

1. **Move where the car charges.** There are two EV receptacles: `ED-G-EV-620` (3,840 VA) on
   the **west** wall at y = 56'-0 3/4", far from the house, and **`ED-G-EV-1450` (9,600 VA) —
   the fast one — at (19'-11 3/8", 41'-5 3/8") on `W-G-S`'s interior face, the wall shared with
   the slot.** Charging on the far wall is nearly free and is plausibly worth more than
   anything done to the canopy frame.
2. **The gable-end draftstop above.**
3. **The rated, self-closing service door** — needed by 2027 anyway.
4. **Detection**, which the garage already has (a heat detector, correctly, not smoke).
5. **The canopy's own material.** Honestly: **very little.** The fire's path is the air gap and
   the two wall assemblies, not the canopy's frame.

## Structure — the three materials

| | works here? | engine cost | fit with the house |
|---|---|---|---|
| **Framed + noncombustible skin** | **yes at 4'**; needs a tip beam at 6' | **~zero** | **it is the house's language** |
| Treated glulam / mass timber | yes; earns its place only as the 6' tip beam | small | already in the vocabulary |
| Steel pole-barn | best engineering by a distance | **large, and fails silently today** | native but industrial |

**Framed and skinned is the recommendation.** It *is* the cantilever scheme of Option A, the
cheapest thing on this page. `GARAGE_ROOF`, `GARAGE_WALL_2X6` and `POST_KDAT` all exist;
mineral wool is already priced. Finish it in the garage's own 7/8" corrugated panel on KDAT
girts and **the extension reads as a continuation of the garage rather than an attached
thing** — which is the entire premise of "extruded gable", and the only option that delivers
it without a visible material change at the gable end. Build to the published Minneapolis
"Detached Garage Protected Wall" recipe (5/8" exterior gypsum inside and out, soffit and
fascia included) so any alternate-materials conversation is a paperwork exercise rather than
a debate.

**Glulam for the 6' tip beam only.** A 3-1/2 x 16-1/2 24F-V4 treated glulam spans the full 24'
at d/c 0.59 and L/320 — but it is a 440 lb, 16-1/2"-deep member hanging in a 6'-6" slot. Three
8' bays on two intermediate pile posts drop the moment ninefold and a 3-1/2 x 9-1/2 does it.
The material and assembly already exist and `"3.5x9.5"` parses correctly through `_RE_ACTUAL`.
The one real engine gap: **`engineering/glulam_beam.py` only reaches deck-joist bearing beams,
so a glulam roof beam draws, bills, and is never calculated.**

**Steel: buy it as a sealed off-model insert, or not at all.** A W8x15 on HSS 4x4x1/4 columns
would span 24' at d/c 0.61, set in an afternoon, and as a moment frame would provide lateral
stability without the west wall having to be a shear wall — which matters with an open east
end. But `resolve/framing/profiles.py` has **no W-shape, HSS or purlin pattern**: `"W8x15"`
matches neither `_RE_NOMINAL` (it carries a letter) nor `_RE_ACTUAL` (no decimal point) and
falls through to `_FALLBACK_ACTUAL_IN = (1.5, 5.5)`. **The model would draw a 1-1/2 x 5-1/2
stick, bill it as lumber, and report nothing.** Doing it honestly means a regex plus an AISC
shape table, a structural steel material (steel exists today only as cladding), two
assemblies, a cost code, and a `[steel]` price section on a **per-pound** basis the takeoff's
unit plumbing has never seen. Multi-day work across five modules for one beam and two columns.

## HP3

### It cannot stay, and the reason is not the roof height

The cabinet's base is at -1'-2" and it tops out near +0'-8"; the roof above it would be at
about +9'-3" — **8'-7" of clear air**, four times the manufacturer's 24" overhead figure. A
roof 8–9 ft above a grade-mounted mini-split is not the recirculation mechanism. Four other
things are:

1. **The discharge clearance was already failing.** Dealer literature for the Sapphire line
   gives **78" of discharge**; the unit has **25 11/16"** — 33% — at a parallel wall. (The OEM
   SAP09 diagram could not be sourced; the dealer sheet is secondary evidence, but it is the
   only number available and the shortfall is not marginal.)
2. **In heating mode the discharge is colder than ambient** — the outdoor coil is the
   evaporator — so the plume sinks and pools rather than rising. Roofed above and closed at the
   west end, the slot's only outlet is the east mouth at grade. The jet hits the garage wall
   25 11/16" away and returns as a wall jet; **the intake is 8" behind the machine.** Even 30%
   recirculation at an 8°F depression pushes the coil deeper into the frosting regime, and
   frost costs 30–57% of heating capacity before defrost recovers it.
3. **More defrost means more meltwater, now on the entry floor.** NEEP's cold-climate guidance
   is explicit about siting away from walkways where refreezing meltwater causes slips. The
   machine has no drain pan by design, and its pad falls onto the ground people would walk on.
4. **Acoustics** — 58 dBA becomes a reverberant number in a hard-surfaced 4' corridor 6'-6"
   from the house door.

**At 6' the discharge only grows to 49 11/16", still under two-thirds of 78", and (2)–(4) are
unchanged. HP3 leaves the slot in either variant.**

### Where it goes

**Site B — house north face, west of the extension. Recommended.** Cabinet at
x 0'-6"..3'-4 3/8", back 8" off the cladding, `rotation=deg(180)` discharging **north** into
open front yard with unlimited throw. Because:

- It is on a **true gable end with zero overhang** — the only such face the house has, and the
  condition GBA recommends. Nothing above it sheds anything.
- **Shortest line set of any option**: a punch through `W-M-N3B` into `RM-M-MECH`, then east
  inside conditioned space to the indoor head — ~10–13 ft, all interior, thermally better than
  today's exterior run.
- **`ED-M-HP3-DISC` does not move.** It is already at (4'-0", 36'-8 7/8"), 8" east of the
  cabinet's east face, within sight, handle at 6'-4" over grade (inside 404.8(A)'s 6'-7"), and
  **NEC 110.26 working space is genuinely available** — nothing north of it for 28'.
- `CKT-HP3` does not move; the mount elevation stays -14" with the other two cabinets.
- It is west of the wind wall, in a corner nobody walks through, and its meltwater lands on its
  own pad in soil rather than on the arrival route.

Two conditions, both required anyway: the west leader must move north (above), and the
extension's west slope needs snow retention (above).

**Site A — house west face, y 31'-2"..34'-7 3/8". Fallback.** Discharges west into open side
yard, gets afternoon sun (a real defrost advantage over the shaded north face), clears the
meter's working space by 2". But it sits under a **6:12 standing-seam eave 30 ft up**, and it
is 11" from `TR-RF-LEADER-W`'s splash zone at y = 35'-6" — downhill of 648 sf. It would need
snow retention across the house's west eave, which is new scope on the main roof.

**Site C — east face. Rejected.** Same eave problem, on the arrival side, with a 26'+ line set
across the whole house, into the already-hopeless HP1 zone.

Moving HP3 also retires, for free, the three ungraded conflicts nobody has had to solve:
`SL-M-HP3PAD` overlapping `PR-BW-2` by 52.2 in2 with a full z overlap, plus the pad and post
laps — because the pad and the piers both leave.

## Ventilation and drying

The house's standard for this room is already set: cold, screened, drying, fed no house air.
The geometry helps — a 24' room under a gable whose ridge runs the long way has 12'-4 3/4" of
stack height over the walk and a 24' ridge line, which is a large, free, wind-independent
driver.

- **Outlet: a vented ridge over the extruded bay**, baffled and 1/4"-meshed. It exhausts the
  *room*, not an attic — a clean separation and a bonus.
- **Mandatory: the draftstop at y = 40'-8 5/8"** (the same piece the fire section wants).
  Without it the slot's cold, salty air is continuous with the garage's insulated attic through
  the truss space, and one ridge vent serves two very different volumes. **This is the detail
  most likely to be missed.**
- **Intake: the open east mouth**, plus a screened, weeped band at the base of the west wall so
  the west end is not a dead pocket. Keep the under-floor open and screened — the existing
  breezeway's instinct that everything down there should "be exposed and to dry" is right; the
  skirt should block wind, not drying.
- **The lined sloped soffit must be vapour-open and drained to the ridge, not a sealed metal
  pan** — or it becomes a 24' condensing surface directly over the walk. This is the detail
  that most repays a section drawing.
- **No house air, no heat.** Which also means the gallery floor is a freestanding slab for
  `checks/code/mn_energy.py`'s purposes — the same trap `SL-M-HP3PAD` fell into.
- Lighting per the north-entry study: sealed 2700 K task light at each lock and on the stair,
  plus a sparse recessed 2200–2400 K layer behind a wipeable lens, dimmed and curfewed. The
  lever for insects is output and duration, not colour temperature.

**Honest limit.** With the west end closed and only the east open, this room will be
noticeably calmer than the yard and noticeably colder and damper than the garage, and it will
collect drifted snow at its east mouth in a north-east wind. It is a wind shelter and a dry
route, not a warm room.

## What the engine can and cannot express

> **F-6. The recommended scheme is the one the engine draws perfectly and understands not at
> all.** `resolve/framing/roof_gable.py:104-125` runs truss stations from the **bearing walls'
> own endpoints** along the ridge, not the roof footprint. `W-G-E` and `W-G-W` end at
> y = 40'-8 5/8", so **no truss is ever generated south of that line.** A 4'-0" south
> `edge_overhangs` extrudes the plane, the deck, the membrane and the metal with only rake
> outlookers under it. Nothing sizes a rake outlooker; nothing knows 4'-0" is twice the AWC
> limit. **The model would build this and stay green while saying nothing true about it.**

Also not expressible: dropped top chords, structural outlookers and backspans (`FramingSpec`
has no such concepts); **bearing a `Roof` on posts or beams** (`resolve/envelope.py:380-414`
resolves `bearing_refs` strictly through `model.wall(tag)`, so the honest bent-with-an-open-
east-end can only be drawn as a wall with a very large opening); **helical piles** (the closest
expressible thing draws the right geometry with the wrong material, bills concrete, and gets
graded as a cast pier with an ACI cage — worse than silence); **steel**; and a 24' ridge beam.

Silences worth knowing, each a finding in itself:

| | why it says nothing |
|---|---|
| **snow drift** | There is no drift check anywhere in the repo. `checks/structural/snow.py` does sliding discharge and rafter spans only and hands drift to the engineer. The ~101 psf will never appear in `haus check`. |
| **footing influence** | Nothing implements §1809.6 or any 30°/45° rule. It exists in the repo only as prose. |
| `structural.concrete_interference` | 3-D volume overlap on isolated pours. `PD-BW-1/2` lap the house footing **in plan** but bear 41" above it — no shared volume, no finding. **This is why F-1 has stood at 0 FAIL.** |
| `structural.cantilever_point_load` | Walks floor systems. A cantilevered roof is invisible. |
| `code.R302_5_garage_separation` | Decides detachment by 18" wall proximity; **a roof connection is invisible to it.** It will keep saying "detached" whatever is built. Its 18" also under-implements Table R302.6's 3 feet — a blind spot this house's geometry happens to clear. |
| rake-overhang limit | Does not exist. |
| the polycarbonate sheet's snow capacity | There is no glazing structural check of any kind. |

If the connector is ever modelled, **claim it `UNCONDITIONED`** — honest, and it keeps the
garage out of the separation check's scope.

## Decision gates

1. **Decide whether the garage can move 2'-6" north.** Everything else follows from it: it is
   the only route to 6', and it closes P1 for free. If it cannot move, **commit instead to
   stepping the garage's south footing down to about -8'-9"** — the two are alternatives, and
   one of them has to happen whatever is built over the slot.
2. **Fix the sequence before the fix.** Whichever route closes P1, the garage foundation has
   to be poured while the house excavation is still open. Nothing in the model or in
   `haus check` will ever say so, so it belongs in the construction documents now.
3. **Commission a soils report.** Every number here rests on presumptive `soil_class="GM"` at
   1,500 psf, and `plan/site.py:85-89` already says no investigation has been done. A helical
   pile design is torque-correlated and needs one; so does any honest statement about F-1.
4. **Put the kitchen window trade to the owner** — full 24' width, or stop at x = 27'-0".
5. **Get the R302.6 ruling in writing** before design money is spent, leading with the
   4'-0 1/2" dimension against the 3-foot threshold. Ask the zoning planner the same day
   whether a roofed connector makes the garage part of the principal building for setback and
   lot-coverage — that may be the more expensive answer.
6. **Re-check `GL-BW-ROOF` against ~101 psf now**, whatever is built. It is a span-chart
   question with a yes/no answer and it is currently unasked (F-4).
7. **Engage the engineer early.** The 4' cantilever is twice the prescriptive outlooker limit,
   the bay carries ~2.2x the rest of the roof, and the uplift case on an open one-end-closed
   roof is separate. None of it is exotic; all of it needs a seal.
8. **Do not author steel profiles into the model** — they resolve silently as 1-1/2 x 5-1/2
   lumber (F-6).

### Suggested decision rule

- **Garage can move:** 2'-6" north, 6'-0" extrusion on four helical piles, framed and skinned
  in the garage's own panel, 4–6" gap, HP3 to Site B, leaders reversed north.
- **Garage cannot move:** 4'-0" cantilevered extrusion on 2x10 outlookers, **no new concrete
  in the slot at all**, 3'-8 1/2" of extension to leave a 4" gap, same HP3 and leader moves —
  **plus stepping the garage's south footing down to about -8'-9" to close P1**, poured while
  the house excavation is open.
- **Neither is acceptable:** the existing freestanding breezeway is the version of this that
  needs no argument at all, and a larger, better freestanding pavilion solves the weather and
  headroom complaints without spending the fire argument or touching the footing question.
