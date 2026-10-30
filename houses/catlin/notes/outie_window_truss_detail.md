---
title: "Outie Window in a Truss Wall — detail and build order"
applied_to:
  - detail: outie_window_truss_detail
  - assembly: EXT_2X6
  - assembly: PLANT_EXT_2X6_HUMID
  - transition: TR-CATLIN-FRAMED-OPENING
tags:
  - wall
  - window
  - insulation
  - air-barrier
  - water-management
  - sequencing
source:
  - plan/assemblies.py EXT_2X6
  - resolve/framing/truss_wall.py
  - resolve/framing/truss_girts.py
  - resolve/framing/truss_common.py
  - emit/draw/detail_components/opening.py outie_window_truss
  - notes/catlin_truss_engineering.md
---

# Notes

## Sheet notes

### General
- Wall: 2x6 studs, 1/2" plywood, 4" of 2 lb closed-cell foam in one pass.
- Girts: KDAT 2x4 laid flat, horizontal, 24" o.c., on three-ply 4-1/2" KDAT blocks.
- Blocks land on every other stud, 32" o.c. from the layout line.
- One 8" TimberLOK TLOK08 per crossing, 1-1/2" into the stud. 1,131 total.
- Cladding faces off sheathing: E/W PBR 7-1/4"; N/S BBD75 6-3/4".
- Block stands 1/2" proud of the foam. That gap is the drainage plane.
- Window mount plane is the girt face, 6" outboard of the sheathing.
- Everything outboard of the sheathing is KDAT. No WRB; the foam is the water plane.

### Keyed
- [K1 @ host#layer:outer-girt:out] Jamb post: KDAT 2x4 flat, inner face on the RO edge, 3-1/2" past each end.
- [K2] Head and sill courses: KDAT 2x4 flat, post inner face to post inner face.
- [K3] Block each course the post crosses, at 24" max, and across the RO.
- [K4] Field courses stop 3-1/2" clear of each RO.
- [K5] Fluid-applied pan on the buck: dam on a strip, 1/4"/ft, over the sill course.
- [K6 @ host#layer:spray-foam:out] Steel head cap from the foam face over the course, face leg over 58114XX; panel end on a perforated strip. Strip in.
- [K7 @ host#layer:cladding:out] Sealant at the cladding-to-frame joint, at the mount plane, under the drip.

### Spec 06 10 00
- Mark the stud line across the girt face as each girt is laid; the screw is blind through 6" of wood into a 1-1/2" target.
- Set the window bucks before spraying the foam.

### Spec 07 21 00
- Spray the foam in one application; the blocks are the only thing crossing it.

### Spec 06 17 53
- RF-BW-CANOPY end truss top chords are the deck's N-S diaphragm chords.
- Peak chord splice: 595 lb tension, on top of the gravity and drift case.
- Design assumes splice slip of 0.03" max: 30% of the deck's N-S deflection.
- That slip sets the rigid/flexible call, at 0.68x of the 2.0 threshold.
- Fabricator to confirm 0.03" max or state its value before fabrication.

## What the wall is

`EXT_2X6` is a **catlin truss wall**, ONE girt tier.
Outboard of the 2x6 studs and their 1/2" plywood sheathing there is 4" of 2 lb closed-cell
spray foam, and the cladding stands off on **one tier of flat horizontal girts on 4-1/2"
blocks** — all 2x4 stock, all laid flat, nothing on edge:

| piece | what it is | where |
|---|---|---|
| block | **KDAT**, three loose 2x4 offcuts, 3-1/2" along the wall × 3-1/2" tall × 1-1/2" thick each, stacked to 4-1/2" | on the sheathing over every OTHER stud, under every girt course, 0 → 4-1/2" |
| girt | **KDAT** 2x4 flat, horizontal, 24" o.c. | on the blocks, 4-1/2" → 6", standing in free air; the cladding nailer and the window mount plane |
| jamb post | KDAT 2x4 flat, vertical | at every RO edge, inner face ON the edge |
| head/sill course | KDAT 2x4 flat | spanning the RO between the two posts |
| cladding | PBR / BBD75 | girts at 6"; face 7-1/4" E/W, 6-3/4" N/S |

Foam total 4", in ONE application, crossed only by the blocks. The block stands **1/2" proud**
of the foam face, and that proud half inch is the **vented gap** behind every course — the
drainage plane. It is continuous, and together with the 20-1/2" of open foam face between
courses it is the 2" drained, back-vented cavity the bug screen at the base of the wall closes.

**The inner girt tier is deleted.** It would sit directly on the sheathing, giving its own
screw no thermal break, and would cost a 10.9 % framing fraction in the first 1-1/2" of foam
while holding up nothing but the tier above it. The foam needs no backing — ESR-4073 §4.4.2
permits 7-1/4" on a vertical surface with nothing in it — and ccSPF's racking contribution is
its bond to the sheathing face. See `notes/catlin_truss_engineering.md` §1 and §7.

**Everything outboard of the sheathing is KDAT**, and there is no exposure rule to apply: the
girt is a 3-1/2"-deep horizontal ledge behind the cladding that will wet-cycle for the life of
the wall, and the block plies stand in the same foam-face plane at every crossing.

**The blocks are on the STUD module, the girts on their own — and the block module is every
OTHER stud.** A girt course climbs a 24" elevation module measured from the storey's floor
datum (see the phase below); the blocks under it carry it back to the framing, so they land
at whole multiples of **32"** from the wall's LAYOUT LINE, on the same phase the studs take.
32" x 24" is the crossing tributary every load in the engineering note is derived from.

> The phase is solved for the BLOCK module, not the stud module, and that is not pedantry:
> a phase is only line-locked modulo the spacing it was solved for, so a wall standing 16"
> along its line has stud phase 0 mod 16 but block phase 16 mod 32. Reusing the stud phase
> puts half of a facade's wall segments on the opposite 32" parity from the rest — every block
> faithfully on a stud, and the facade's grid different storey to storey.

**One 8" FastenMaster TimberLOK (TLOK08) per crossing**, through the girt (1-1/2"), the three plies (4-1/2") and
the sheathing (1/2"), 1-1/2" into the stud. One fastener pass, no nails, and it is the entire
load path: the block bears the cladding's gravity in direct compression on the sheathing, so
the screw is a pure withdrawal element. It is wood-to-wood with continuous lateral support
over its whole through-length, never bearing on foam. **Mark the stud line across the girt
face as it is laid** — the screw is otherwise blind through 6" of wood into a 1-1/2" target.
See `notes/catlin_truss_engineering.md` §3 and §6.

## What this replaced, and how to go back

The retired **Swinburne truss wall** was a three-piece chiral pack — a 2x4 flat block on the
sheathing, a 1/2" plywood tab, and a KDAT 2x4 **outrigger on edge**, vertical, 16" o.c.,
lap-screwed to the tab.

`resolve/framing/truss_frame.py` and its branch of the pass are untouched and still selected
by their own predicate (`laid="edge"` + vertical); the girt frame is a SIBLING selected by
`standoff="block"`; the corner box is still there; and the old layer tuple is kept verbatim in
`plan/assemblies.py` as **`EXT_2X6_SWINBURNE`**, referenced by nothing, like
`glazed-green-brick`. Reverting is three edits:

1. give `EXT_2X6` and `PLANT_EXT_2X6_HUMID` that assembly's layer tuple;
2. restore `_WALL_OUTBOARD_IN` (`params/roof_trim.py`) and `HOUSE_CLADDING_Y_FT`
   (`params/breezeway.py`) to their 5.5"-proud values, and the garage lines 1" south;
3. uncomment the Swinburne rows in `prices.toml` (`2-2x4`, `5x0.5 panel`, `5x0.375 panel`,
   `3-2x4`, `3.5x3.5 panel`, `SDWS22400DB`) and comment the girt ones.

## ** THE WRB IS GONE. THE FOAM IS THE WATER PLANE. **

There is no housewrap and no sheet membrane anywhere in this wall. Closed-cell foam is the
air barrier, the water barrier, the vapour retarder (4" ≈ 0.4 perm, Class II) and the
insulation in one bonded, seamless application. `plan/transitions.py` names `spray-foam-ext`
as the water and thermal continuity face for exactly this reason.

**That makes the build order part of the detail, not a preference.** The whole frame goes
together BEFORE any foam exists, on the flat wall, and the sprayer comes once to a finished
frame. With the girt standing 1/2" clear of the foam face there is no pocket, and the
applicator reaches the whole plane from outside through the 20-1/2" between courses.

1. Frame the wall, flat on the deck. Sheathe it. Cut the rough openings.
2. **Set the bucks.** 3/8" plywood lining each RO on all four sides, from the sheathing face
   out to the mount plane — **6"**, unchanged — square and plumb. Non-structural: it closes
   the foam at the reveal, gives the reveal a face, and carries the pan and the head flashing.
   **Then raccoon each opening (2026-10-30)**: FastFlash on the buck's wall-side face, over
   its front edge, and a 4" band onto the sheathing round the RO, before any block or post
   (BSI-048). Photograph it for the inspector before step 4 covers it. The foam laps over it
   at step 8 — shingle order, and the only tie between the foam and the opening
   (`opening_flashing_spec.md` §3 step 0).
3. **Mark the 24" course lines off the sole plate** and snap the stud lines across them.
4. **Drop three offcuts at each crossing**, on every other stud line. Loose — no tack. The
   girt screw clamps them; the block is the screw's spacer, not its anchor.
5. **Lay the girt over them, mark the stud line across its face, and drive the 8"
   TimberLOK (TLOK08).** Head seated FLUSH, not recessed and not proud: the panel bears on
   this face, and the screw's 6" of plain shank is what draws girt and block down onto the
   sheathing. If the head will not pull down, the screw is wrong — check the thread length
   before reaching for the impact driver.
6. **Jamb posts and head/sill courses at each RO**, on their own blocks, screwed at ≤ 24".
7. **Tilt.**
8. **Foam: one 4" application**, sprayed through the clear between courses and behind them.
   **Fillet against the block sides** (BSI-048) rather than butting square — planed lumber
   shrinks, and a square cold joint at a block is where the crack goes. **Shave to a gauge
   1/2" behind the block's outer face**; the blocks stand proud at every crossing and are the
   gauge.
9. **Flash the opening — ONE CONTINUOUS PERIMETER APPLICATION, IN ONE VISIT.** Sill, both
   jambs and head are one monolithic fluid-applied band over the buck's RO face, meeting the
   raccoon at the buck's front edge — **never lapped onto the foam**, which at a jamb is the
   back of the 1/2" slot behind a post set at step 6. Joint filler into every inside corner
   first, then the sill **heavy** with its drip coat down the sill course face and under it,
   then jambs and head run into the sill's corners without stopping, then a 2" band on each
   post's outer face where the flange and J-receiver bear. The posts' sides and backs stay
   bare and dry to the cavity. That is the whole reason the
   membrane is fluid-applied here — splitting it into a "sill pan" operation and a "jamb
   flashing" operation re-introduces the lapped corner the liquid exists to remove, and
   invites two trades onto one opening. One arrival, one opening finished. Spec, qualifying
   products and the open substrate item: `notes/opening_flashing_spec.md`.
   Then, in order: jamb trim, window, 58114XX head trim, K6 head cap (face leg over the
   58114XX back leg) and its strip-in, the perforated strip, cladding.

**Inspect the screw pattern from the ground before the sprayer arrives.** It is a single load
path and this is the last moment it can be seen.

Spraying before the bucks go in leaves a cut edge of foam at every reveal, which is a
discontinuity in the water plane that no sealant closes honestly. Do not do it.

## The window is OUTIE

The unit sits in the **mount plane, 6" outboard of the sheathing** — the outer face of the
girt, which is also what the cladding lands on — with its flanges bearing on the jamb posts
and on the head and sill courses. It is not in the stud plane, and no window in this house
carries a depth dimension: the mount plane is derived from the outermost furring layer's
outer face. The 6" comes out of the stack as a 4-1/2" block plus a 1-1/2" girt, and the stack
is what the mount plane is read from.

**Jamb bearing is no longer a question of luck.** A girt wall has **no field member at a jamb
at all** — the field courses are horizontal — so every opening gets its own frame, always:

| piece | where | material |
|---|---|---|
| jamb post | inner face ON the RO edge, 3-1/2" of wall outboard of it, from 3-1/2" below the sill to 3-1/2" above the head | KDAT |
| head course | post inner face to post inner face, `z_head … z_head + 3-1/2"` | KDAT |
| sill course | post inner face to post inner face, `z_sill − 3-1/2" … z_sill` | KDAT |
| blocks | under every course elevation the post crosses (so at ≤ 24"), and under the head and sill courses at every module station across the RO | KDAT, three plies |

**No doubling anywhere.** The girt head course is blocked back to the framing at every stud
station under it — landing on the cripples above the header, ordinary wall, not the void — so
its span is the block module regardless of how wide the opening is. `prices.toml`'s `2-2x4`
row is retired for the same reason, and so is the jamb filler, since a post set to the RO edge
never leaves a gap to fill. (`3-2x4` is the three-ply BLOCK, not a jamb filler.)

All of it is derived, not authored: `resolve/framing/truss_girts.py` places it, and
`structural.truss_wall_opening_support` FAILs if any RO jamb ends up further than a flange's
bearing (1") from wood **that exists at that opening's own elevation**. That check reads the
OUTER band's posts on a girt wall and the outriggers on a Swinburne one — one check, one
constant, two walls — and it is what keeps this table true after the next window moves.

**Field courses stop clear of the frame.** `furring.OPENING_MARGIN_IN` holds every field
course one piece width (3-1/2") clear of each RO, in both axes, so a course never lands in
the plan a jamb post or a head course already occupies. Beyond that margin the courses simply
resume.

## Window elevations against the girt courses

This is the one thing a horizontal stand-off asks of a facade that a vertical one does not,
and it was checked rather than assumed.

**The finding is unchanged: no window needs to move.** Measured on the built model, the
largest clear gap between two adjacent nailer courses anywhere beside an opening — above a
head course or below a sill course — is **20-1/2"**, which is exactly the field's own clear
(24" o.c. less the 3-1/2" board). The median beside an opening is **9-3/4"**. The girt field
around every opening in the house is as regular as the field away from it, and at 24" it is
regular at a finer pitch than the 32" band managed. 39 openings, 220 courses.

Any window taller than 24" necessarily interrupts some courses; that is inherent to a
horizontal girt and is not a defect, because the courses it interrupts are replaced by the
opening's own head and sill courses at the same job.

### The course phase, and why it is where it is

Two fields on the band's `FramingSpec` say where the module counts from
(`resolve/framing/furring.course_phase`):

```python
spacing=inch(24), course_datum="framing-base", course_offset=inch(0),
```

`course_datum="framing-base"` is `rw.base_ref_z_m` — **the datum a sill height is measured
from**. It is not the wall base: `platform.py` extends a main-storey wall 13-7/16" down over
the floor rim band, and the courses would otherwise count from the bottom of that lap while
every sill in the same wall counts from the floor.

`course_offset` is **zero**, and that is a swept result rather than a default left in place.
The whole 1/8" sweep from −16" to +8" was re-run against all 39 openings on girt walls,
counting two things: **exact hits** (an opening's own head or sill course landing on a field
course line, where the two are one board and nothing extra is cut) and **conflicts** (a field
course whose bottom is within 7" of one, which is two nailers inside one board face — either
half-lapped or separated by a gap too narrow to be worth a board).

| module | phase | conflicts | exact hits | widest bay |
|---|---|---|---|---|
| 24" from the wall base | — | 38 | 8 | 24" |
| 32", framing-base | −3-1/2" | 19 | 16 | 32" |
| **24", framing-base** | **0** | **30** | **13** | **24.00"** |
| 24", framing-base | −3-1/2" | 24 | 9 | **24.75"** ← fails |
| 24", framing-base | −16" / +8" | 38 | 14 | 24.00" |
| 24", framing-base | −7" to −8-1/2" | 25 | 0 | 24.00" |

**Two things constrain the choice.** The −3-1/2" phase the 32" module used is *not available
at 24"*: it opens a **24.75"** bay on nine walls, because the forced top course pops the
module course under it (`furring.course_elevations`), and `structural.girt_course_spacing`
FAILs on any bay wider than the authored spacing. Of the phases that keep every bay at or
under 24.00", **zero carries the most exact hits by a clear margin** — the runners-up trade
5 fewer conflicts for all 13 of them, which is a bad trade: a conflict is a sliver, an exact
hit is a whole board not cut.

**30 conflicts against the 32" band's 19 is not worse layout, it is more course.** A third
more courses fall within 7" of an opening edge no matter what the phase is. Per course the
rate is unchanged.

**Zero is not reachable.** The second storey carries sills at 152" and at 156" — 4" apart, on
different walls but on one module. Any phase that lands exactly on one group is 4" off the
other, and 4" is inside the 7" window.

**THE DESIGN RULE FLIPPED WITH THE SIGN.** At −3-1/2" a course TOP landed on the sill datum;
at zero a course BOTTOM lands on the framing-base module. So for a NEW opening: land the
**HEAD on a 24" multiple above the sole plate** (24", 48", 72", 96"), or the **SILL 3-1/2"
above one** (27-1/2", 51-1/2", 75-1/2", 99-1/2"). Either makes that opening's own head or
sill course the field course. `haus build` then shows it, and
`test_truss_girt_courses.py` counts it; a miss costs a redundant board, not a defect.

## Water at the head and the sill

Drawn by the `outie-window-truss` recipe
(`emit/draw/detail_components/opening.py::outie_window_truss`), which is a sibling of the
innie `window-head-jamb-sill` rather than a variant of it — the innie measures both pieces
from the sheathing face, and on this wall neither piece is anywhere near it.

- **Sill pan.** Lies ON the sill buck (the buck lines the RO, 3/8" in), over a tapered shim
  that falls 1/4"/ft outward, its back dam turned up a rigid strip at the sheathing face. It
  runs out to the mount plane and turns **down over the buck's front edge**, at the outer girt
  face: the buck spans the 1/2" vent gap, so the water runs down past the sill course face and
  the cladding's back, hidden behind the sill trim (owner, 2026-10-16). Since 2026-10-30 the
  turn-down is a **drip coat over the whole sill course face and its underside** back to the
  slot, across both posts' end grain (was a 3/4" drop covering 3/8" of the course), the
  splash-zone exception of `board_batten_girt_span.md` §7.10. It discharges *behind*
  the cladding. An outie pan carried out to a visible drip would put a metal lip under every
  window on the facade, which is not what this house looks like. **Leave the window's sill
  flange unsealed** over the pan (spec §3).

  **Fluid-applied, and the ponding paper a reader will find does not govern it.** RDH's 2017
  study (Wilkinson/Tatara/Finch) ponded seven liquid membranes on wood sills for 42 days and
  measured 25-40% moisture content against a <20% threshold; Holladay's independent test
  agreed. Two things keep that off this detail. The permeable self-adhered CONTROL failed
  identically at ~35-40%, so the paper's own conclusion is that there is "no discernable
  drying benefit to liquid applied membrane flashings over impermeable self-adhered
  products" — not that liquids are worse than tapes. And every one of those failures was a
  **ponding** failure. This pan does not pond: it falls 1/4"/ft over 6" and turns down over
  the buck's front edge, so what reaches it leaves it. A pan that drains has no puddle to sit under for 42
  days. Where the finding still bites is DURING CONSTRUCTION, before the cladding and its
  vent gap exist — flash, then close in, and do not leave an opening standing full of
  meltwater. Build the sill heavy regardless (Tremco publishes 60 mils at sills against 20
  elsewhere). The full argument, the permitted impermeable-self-adhered hybrid and the open
  item — Amrize's written approval for OnePass sprayed over cured FastFlash, with a mock-up —
  are in `notes/opening_flashing_spec.md`.
- **Jambs: raccoon and post band (2026-10-30).** Nothing laps onto the foam face at a jamb;
  that face is the back of the slot behind the post. The membrane is the pre-foam raccoon on
  the buck's wall side and the sheathing (step 2), the reveal on its RO face (step 9), and a
  2" band on the post's outer face under the flange and J-receiver
  (`resolve/opening_raccoon.py`).
- **Head cap (2026-10-29).** On a metal wall the head is a steel **cap**, not a drip head:
  a 2" upstand on the **foam face** (the water plane, so lapping onto it is what makes the
  head continuous), a top across the cavity and the head course falling outward, and a face
  leg down the girt plane lapping the 58114XX back leg by 1" (`opening_flashing_spec.md`
  §3 step 4a, the hand count there). It floors the cavity above the window, so what runs
  down the cavity leaves over the 58114XX and the 1/2" pocket behind the course stays dry.
  The panel ends in the 58114XX channel on a bare perforated strip. Brake-formed
  steel in the house dark, bedded on the membrane over the course top and face, 3/4" end dams,
  RO + 7" long, its upstand stripped in. Sealant at the cladding-to-frame joint sits at the
  mount plane, under the 58114XX. Before this, the cavity above every head exited only down
  the rib voids into a closure taped into the 58114XX throat, and the pocket behind the
  course was sealed in on the membrane: no drain, no exit.

One number told the recipe which wall it is on: the head course is **3-1/2"** tall here (a 2x4
laid flat) against the Swinburne wall's **1-1/2"** (the same board on edge), so the flashing's
upstand starts two inches higher. Everything else — the mount plane, the foam face, the vent
depth — the recipe already read off the resolved stack and needed no telling.

- **Jamb and head trim (2026-09-12; the panel is BBD75-1212 from 2026-09-14, and the trim
  kit is the same brake-formed set).** The Metal Sales kit's **Sill/Jamb Trim** is
  a J-shaped receiver: it runs up each jamb to the head and takes the panel's cut end at the
  reveal. Without it, the cut edge IS the finish. **Head Trim** 58114XX goes over it, under
  the head cap's face leg. Both are brake-formed flat stock from the same kit as the corners and the
  starter, which is why nothing new bills for them — `prices.toml` puts the whole trim kit
  inside the panel's $/SF rate (TRIM IS PARITY), and `[basis_notes] envelope_layers` forbids
  counting a piece against a concealed row. The build order is in "Sequence" step 9: the
  opening is flashed in one continuous pass, then jamb trim, window, head trim, head cap,
  strip, cladding. (The trim now bills by part under `[cladding_trim]`, 2026-10-27.)

  **Not yet a keyed callout.** A `[K8]` row would put the detail's notes onto a second sheet
  (`integrity.sheet_note_legibility`, 36 rows to a page, and this sheet sits on 36). Drawing
  it means retiring a note that is already there, which is a sheet decision and not a
  fastener one.

The buck, the head/sill courses and the girts themselves are **not** drawn as convention
linework. They are resolved members, so the cut carries them as the solids they are; drawing
them again would be a second, disagreeing picture of the same wood.

## Insect closure (2026-10-10, re-struck 2026-10-29)

The 2" cavity (1/2" vent gap + 1-1/2" girt band) is a sheltered void with the ccSPF face
exposed in it. Carpenter ants excavate the foam, wasps and mud daubers nest in voids, and
mice chew it. Minnesota is a slight termite zone, so IRC R318.4 does not apply; this is
durability, not code. The only protection is physical: every way into the cavity is closed
with corrosion-proof perforation (3 mm holes, under 1/8"; 33% open) or with solid metal.
The cavity breathes in at the base and, on the N/S walls, out at the band; heads drain and
are not outlets (owner, 2026-10-28). At an opening that means:

- **Head (derived, billed).** The K6 cap floors the cavity above the head; the panel end
  sits on a perforated strip in the 58114XX channel (`resolve/rainscreen_strips.py`), billed
  in `[bug_screens] PANEL_END_STRIP`. There is no head screen any more: the head drains
  through the strip, and its vent area is negligible, as intended.
- **Jamb (HOLD POINT).** The 1/2" gap behind each jamb post is closed by the raccooned buck
  return, which the foam laps. Walk every jamb before the cladding goes on: the foam must meet
  the raccoon on the buck's wall side with no daylight, and any gap gets low-expansion foam —
  never membrane run into the slot behind the post.
- **Sill (closed).** The pan discharges over the buck's front edge onto the sill course face
  and the cladding's back, behind the sill trim; whatever reaches the cavity drains to the
  base. Only the J-receiver joint needs sealing; seal it at the mount plane. Sills keep
  their profile closure.
- **Penetrations (sealed).** Hose bibs, exterior lights, the ERV hoods, the hydrants and
  `VR-M-STACK` sleeve through the cavity; seal each sleeve to the foam and to the panel
  (`[allowances] envelope-exterior-hoods-and-flashing`).

**Closure inventory** (recorded, no geometry change): jamb buck returns, hold point; sills,
closed; eaves and rakes, closed by the roof deck oversailing the girt face; outside corners,
closed by the Wide Outside Corner; ERV, hydrant and `VR-M-STACK` sleeves, sealed;
`D-S-DECK-E`'s head is its catalog unit's (no kit head trim, so no strip): a hold point.

The base (inlet), the band (outlet) and the panel-end strips are in `metal_trim_kit.md`,
"Wall base stack" and "Band outlet".

## Why the change, honestly

**Not R-value, and the model's own card overstates it.** `haus explain EXT_2X6 --card`
reads **R-43.5**; the honest number is **≈ R-39.8** wood-only, or **≈ R-37.9** once the girt
screws are counted the same isothermal-planes way the blocks are — the blocks are framed by
the resolver rather than authored as a `CavityFill`, so band A reads as unbroken foam, and the
girt is credited its own R-1.4 although it stands outboard of a vented gap and is thermally
outside the envelope. See `notes/catlin_truss_engineering.md` §7.

Deleting the inner girt tier is worth about **+2.5 R** (37.3 -> 39.8 wood-only; 36.1 -> 37.9
with fasteners). **`preferences.toml wall_r = 40` is effectively met on the wood-only basis**
— 39.85 against 40 — and is 2.1 short with fasteners counted. Code minimum is R-21, so there
was never risk in either direction; do not read the card as saying the target is met.

**§7.1 of the engineering note is the comparison this wall type exists to win**: against a 4"
polyiso + furring wall with the same studs, sheathing and 8" screws, this wall is about
**+3 R** — ccSPF's R/inch over cold-derated polyiso (+4), half the screw density because the
block carries gravity in bearing (+1), less the blocks themselves (−1.6).

The case is **buildability and the cladding**:

- **A horizontal nailer for a vertical seam.** The standing-seam clips had nothing horizontal
  to land on before. More to the point, the girts are exactly the substrate a vertical
  **exposed-fastener ribbed panel** wants — which the owner is considering.
- **No tab, no chirality, no corner box, no jamb filler.** Every piece is the same 2x4 turned
  one of four ways.
- **ONE fastener pass, and one fastener.** 1,128 eight-inch SDWS. Every screw is still
  wood-to-wood with continuous lateral support, and every one of them is driven on the flat
  wall before the foam exists. **The cost is that there is no redundancy left** — see the
  engineering note §3 and §10.
- **Everything outboard of the sheathing is KDAT** — the girt, the jamb posts, the head/sill
  courses and all three block plies — a ledge in a vented cavity.
