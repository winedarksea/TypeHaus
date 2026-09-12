# North entry — the bearing map, 2026-09-10

Implements [the selected concept](../../../plans/north-gable-extension.md). **This note is
the bearing map: what carries what, and what the drawings must say that the model cannot.**
The arithmetic lives in `notes/north_entry_piers.md`, which is the oracle for
`engineering/roof_beam.py` and the pier calcs.

> ⚠ **This file described a schematic on 2026-09-10 and no longer does.** Every "off-model
> structural package", "custom fabrication" and "sizes provisional" phrase it carried was
> describing structure that did not exist. The six-foot south roof extrusion stood on
> nothing; the landing hung off the house basement walls on six invented connectors with a
> part number in no catalog; and two engine escapes converted the whole of that into five
> tidy UNKNOWNs and two priced rows. All of it is now built and graded.

The garage keeps its 24-foot square frost-depth ICF foundation. What changed is that the
passage between house and garage is **its own roof on its own structure**, not a cantilever
off the garage's gable.

## 1. The canopy — freestanding

`RF-BW-CANOPY` — **three** 24'-span trusses at 24" o.c. on two headers, each header on
**two** columns of its own. `CANOPY_ROOF` is `GARAGE_ROOF`'s structure with **no insulation
and no ceiling**: an open outdoor bay has no thermal boundary to hold, and billing one over
it would order 144 sf of R-38 blown fiberglass and 5/8" gypsum nobody installs.

> ⚠ **It was four until 2026-09-11, and the fourth was an artefact of the layout rule.**
> `roof_gable.build_truss_layout` forces a last truss station onto the end of the bearing so
> a gable wall never ends up with the field stopping short of it. These headers run 8" past
> their north columns to reach the garage wall, so that forced station stood a fourth truss
> **1 1/2" off `W-G-S`, out of module** — back to back with `RF-GARAGE`'s own gable truss,
> two 24' frames in 3 inches, in exactly the plane the fire/draft closure and the garage's
> south cladding need clear (§5). The roof now authors `gable_ends=()` and the engine drops
> an off-module end station that is not a gable line. The deck bridges the last **1'-9 3/8"**
> to `RF-GARAGE`'s gable truss, which is shorter than every other bay on the roof.
>
> **The last bay is the one place a little gravity does cross, and it is worth stating.**
> That bridging sheathing lands on `RF-GARAGE`'s gable truss and hands it half a 1'-9 3/8"
> bay over 24 feet: roughly **1,800 lb** under the 73.7 psf drift case the headers are sized
> for, about 900 lb balanced. The whole canopy sits inside the 9.8' drift zone off the house
> gable, so the drift number is the one that governs here, not the balanced one. It lands on
> a frame bearing **continuously** on `W-G-S` — a gable-end frame is supported that way or it
> is not one — so it spreads to about **75 plf** on a 2x6 wall already carrying half a garage
> bay. Trivial, and real. §1a's "never gravity" is about the **strap line**, not about the
> deck edge; do not read it as absolute.

> ⚠ **The headers bore on `W-G-W` / `W-G-E` until 2026-09-10 and that was never a detail.**
> A ~3,130 lb point reaction on the END of a stud wall wants a bearing post through the
> plate, the stud bay, the sill and the ICF stem, and no such post was authored, drawn or
> billed. `bearing_refs` naming a wall is this engine's idiom for a beam landing ALONG a
> wall; it grades nothing about one landing on a wall's terminus. **The canopy now carries
> its own gravity load to its own piers and shares nothing structural with the garage but
> the sheathing plane.**

| Member | Support | What the drawings must say |
|---|---|---|
| `RF-BW-CANOPY` | `BM-BW-RW`, `BM-BW-RE` | Sheathing runs **continuous** across the garage south wall line. Two `Roof` elements, one diaphragm — and that diaphragm is the canopy's only connection to the garage. |
| truss-to-header | `CN-BW-TRTIE-W1..3`, `-E1..3` | One **stainless `H2.5ASS`** each end of every truss. Six, not eight, since the fourth truss went. Not the galvanized H2.5A the rest of the house buys: these land on treated southern pine at an entry that is salted every winter. |
| `BM-BW-RW` / `-RE` | `PT-BW-CW`/`-CNW` and `PT-BW-RE`/`-RNE` | 3-ply 2x12 KDAT, top at +7'-4" = the garage plate. 4'-11 3/4" between columns, running 8 7/8" past the north column so the roof plane reaches the garage wall. That tail carries **no truss** — it backs the deck edge and the fascia return and nothing else. **The two headers do not land on the same thing.** |
| `PT-BW-CW` / `-CNW` | `PT-BW-W` / `PT-BW-GW` | 6x6 KDAT, 7'-8 1/4", the WEST pair. `ABU66SS` standoff base on a cast-in `AB-058-10-SS`; `CCQ46SDS2.5` cap at the header. `PT-BW-CNW` shares its pier with the garage-side seat beam exactly as `PT-BW-CW` shares one with the house-side seat. |
| `PT-BW-RE` / `-RNE` | `FT-BW-RE` / `FT-BW-RNE` | The EAST pair, and they are **not** columns on piers — they are one 12" cast concrete pour each, footing to header soffit, **fixed at the base**. No wood on this side at all, so the top joint is an `SS316-SHIM-35` pack under an `HGAM10` gusset, never a post cap. |

> ⚠ **NEITHER END OF THE CANOPY IS A GABLE END, and the engine used to think both were.**
> A gable-end frame is plated with verticals at stud spacing, has no engineered web joints,
> and is supported **continuously by the wall or beam under its bottom chord** — it does not
> span, and it bills on its own row at a premium. All three canopy trusses are ordinary
> **field** trusses spanning 24' between the two headers, because there is no wall under
> either canopy end: the south end hangs over the open passage, and the north end's plate
> belongs to the garage. `RF-GARAGE` keeps its two, on `W-G-S` and `W-G-N`.

> ⚠ **No ladder framing anywhere at this joint, and there used to be thirty lookouts.**
> `RF-GARAGE`'s south gable and both ends of `RF-BW-CANOPY` are **close rakes** — the roof
> deck cantilevers past the last truss and the fascia hangs on it. The garage's south
> projection is 1 9/16", at a line where the roof does not even end, and the canopy's own
> south drip edge is 3 3/8". Neither is built with a 2x4 lookout and a 2x6 barge rafter, and
> the engine framed both until `_FLUSH_RAKE_TOLERANCE_M` went from 1/2" to 6".

## 1a. The lateral system (owner, 2026-09-10)

> ⚠ **This section said the canopy had no lateral system of its own and borrowed the
> garage's roof diaphragm. That is withdrawn, and it was indefensible on its own terms.**
> §5 of this note requires the house/garage joint to move, and §1 called the same plane a
> rigid shear transfer. A plane cannot be both. Three further objections a reviewer reaches
> in minutes: a diaphragm needs chords and a collector and none were drawn; the two
> structures are separately founded, so differential movement works the nails; and four
> standoff bases with two pinned caps gave the frame **zero** lateral stiffness in either
> direction — Simpson's own catalogue says a post base does not resist rotation and is not
> for an unbraced carport. The canopy braces itself now, and the garage joint is a tie.

**The demand.** ASCE 7-16 §27.3.2, pitched free roof, 4:12, h/L = 0.40, V_ult 115 mph
Exposure B: q_h = 16.40 psf, Gq_h = 13.94 psf. The governing east-west case is clear wind
flow Case A (C_NW +1.10, C_NL −0.17 interpolated to θ = 18.44°), giving **425 lb** of
horizontal roof thrust on the 24 sf projected area, plus column drag, for roughly **790 lb
strength / 470 lb at 0.6W** across the whole frame. ASCE 7-16 §27.1.5's 16 psf × A_f floor
gives 384 lb on the roof alone, so the computed value governs but not by much. **Uplift is
the larger number and is not the lateral question:** obstructed Case B reaches about
−2,350 lb on the roof, ~390 lb per column at 0.6W before dead relief.

**East — two fixed cast columns.** `PT-BW-RE` and `PT-BW-RNE` run unbroken from footing to
header soffit, 12" round on the same `(4) #5 + #3 @ 10"` HDG cage as the piers, fixed at the
base. This is the balcony's own lateral system repeated: `notes/balcony_moment_columns.md`
§4 works the same section, and φM_n is ≈ 24,900 lb-ft at these columns' own axial load.

> ⚠ **This paragraph claimed for a day that the engine graded them, and it did not.** The
> sentence read "`structural.lateral_racking` grades them through `engineering/deck_post.py`
> and both publish a real d/c" while every path into that module's moment machinery was
> gated on a **deck** — a canopy column carries a roof header — so both records actually
> read `SCREENING: axial only, no moment and no lateral case.` A column the house calls its
> lateral system, graded axially, is the worst kind of wrong answer: confident, specific,
> and about the wrong limit state. Fixed 2026-09-11 in the commit that made it true.

**It is true now, and the engine's number is not the 2,200 lb-ft this section used to
quote.** `engineering/roof_moment.roof_base_moments` will not read Fig. 27.3-4's `C_N` —
copyrighted, and this repository holds no cell of it — so it bounds the demand instead,
taking the roof's vertical projection as a solid sign at Fig. 29.3-1's Case A/B ceiling.
That is **2.1x** the §27.3.2 hand pass below in the same direction, and it grades the
north-south case rather than this one. `PT-BW-RE` lands at **d/c 0.71** magnified and
`PT-BW-RNE` at **0.55**, both OK, on the ACI minimum cage and with no section change.
`notes/north_entry_piers.md` §8 is the hand pass and §8c is the arithmetic of the gap.

**West — a sheathed shear panel.** `W-BW-SCREEN`, KDAT 2x4 at 16" o.c., deck to +4'-0",
6'-6 3/4" long. Aspect ratio 1.63:1, inside SDPWS's 3.5:1. It is also the guard and the
closure over the deck framing. **The shear rests on the WEST face alone** — 5/8" CDX under
7/8" corrugated. The east face is a 5/8" APA Rated Siding 303 MDO panel, which is a rated
wood structural panel and could be counted; it is not, which is conservative and needs no
new number. The panel was sheathed and clad on both faces until 2026-09-11, and the second
skin was already described there as free shear, so nothing the capacity rests on moved.

**North — the garage joint is a tie, and the two roofs move together.** Sharing a roof plane
and a sheathing course while being free to move apart was the odd part, not the tie. Seven
`LSTA24` straps at 4'-0" o.c. (`CN-BW-JOINT-1..7`) make the continuity a drawn, counted
connection against a collector demand near 18 plf — nominal continuity, deliberately, since
the canopy no longer depends on it. **The movement joint that remains is at the HOUSE end**,
which is where two independently founded structures actually meet (§5).

> ⚠ **NOT GRADED HERE, and both belong to the engineer of record.** (1) The fixed-base
> assumption itself: `PT-BW-RNE` has 4'-2" of embedment below grade against roughly 5'-6"
> that IBC 1807.3.2.1's non-constrained formula wants for this moment in presumptive sand,
> and the 2'-0" pad's contribution is not in that formula at all. (2) Slenderness as a SWAY
> column: k·l_u/r is about 74 on the 9'-2 3/4" exposed length, where the pier calc's
> non-sway reading was taken. Neither changes the section; both change how much of it is
> spent.

## 2. The landing

`FS-BW-FLOOR` retains uid `BWFS01AAAA`. Finished surface 0" at both thresholds; framing one
inch lower for the composite. Five exterior rises from −34" are exactly 6.8".

**The landing touches nothing on the house.** Grep `params/breezeway.py` for `W-B-` and
expect nothing but comments. Its house-side bearing is two cast piers on the pier line at
y=37'-6", not brackets standing off the basement concrete.

| Member | Support | What the drawings must say |
|---|---|---|
| `BM-BW-HOUSE-SEAT` | `PT-BW-W`, `PT-BW-E` | 3'-7" between two 12" round piers (5'-6" until 2026-09-11, when the deck's east edge came in to `D-G-SERVICE`'s jamb at x=9'-7"), soffit −1'-3 1/2". `SS316-SHIM-35` pack under it (bearing, and the dielectric off the pour), `HGAM10` gusset (the tie). |
| `BM-BW-GARAGE-SEAT` | `PT-BW-GW`, `PT-BW-GE` | Identical span, elevation and detail. |
| `BM-BW-SCSILL` | Both seat beams | The screen panel's sill and the deck's west rim in one member, on the column line at x=6'-0" where the joist field cannot reach. |
| `BM-BW-FC` / `-FE` | Both seat beams **and** `PT-BW-IC` / `-IE` | Continue into the garage to the interior landing, under `D-G-SERVICE`'s sill and 3 3/4" over the continuous ICF stem (`W-GF-S-DR` is full stem since 2026-09-11; its door gap dated from when the door opened at the slab). The west one is sistered to the deck's second joist at 7'-3 3/4"; the east one's face is on the RO's east jamb at 9'-7". The tips are POSTED. |
| `FS-BW-FLOOR` joists | Both seat beams | 2x8 at 12" o.c. running **north-south**, bearing on top, cantilevering 9 1/2" south and 7 1/4" north. Joist tape, stainless fasteners. |

> ⚠ **ONE TIER OF BEAMS, and it was two until 2026-09-10.** This landing was framed pier →
> seat beam (east-west) → floor beam (north-south) → joist (east-west) → board: three tiers
> of framing under a 5'-6" × 4'-11 3/4" square, with beams running both ways, and the middle
> tier carrying nothing the seats could not carry directly. The joists turned to run
> north-south straight on the seats and `BM-BW-FW` went. `BM-BW-FC`/`-FE` stayed because they
> are not a tier — they sit in the joist plane, parallel to the joists, and do the one thing
> no joist can do here, which is reach the interior landing through a door opening.
>
> **The seats are the tier that survives, and the alternative does not fit.** Putting the
> north-south beams straight on the piers instead fails on one line: x=6'-0" is occupied at
> both y stations by a canopy column standing on that same pier and rising through the deck
> band. The columns own x=6'-0"; the seats get the piers.

> ⚠ **`PT-BW-IC`/`-IE` bear on `SL-G-FLOOR` as cast — no thickening, and no anchor bolt
> (owner, 2026-09-11).** A "thicken to 10" over a 2'-0" square, monolithic" note stood here
> for a day. The slab never wanted it: 8.1 ft² tributary at IRC R507.1's 50 psf is ~405 lb per
> post, ~600 lb with the stair's top reaction, which under a 3 1/2" square is a lighter load
> at a lower contact pressure than one tire of the car that parks on this slab. Spread through
> the 3 1/2" pour it reaches the 1" under-slab XPS at about 5 psi against a 40 psi board.
>
> **What wanted the 10" was the bolt.** `AB-058-10-SS` is 5/8" × 10" and needs something like
> 8" of embedment; the slab is 3 1/2" on foam, so the bolt could not live in it and dragged a
> thickening along to house itself. The bases are now authored `anchored=False`: download
> crosses the plate into the pour, which is bearing and needs no bolt, and the joint claims
> **no uplift and no lateral**. That is outside ESR-1622's tabulated configuration, which is
> measured through the anchor — and ESR-1622 §5.8 puts the anchor and the concrete support
> outside its own scope, which makes it the designer's call rather than the report's.
> The order is 4 `AB-058-10-SS`, not 6.
>
> ⚠ **AND HERE IS WHAT NOBODY GRADES.** With no base anchor these two are leaning columns:
> they carry gravity and lean on the braced system for stability. `RL-BW-GARAGE-E`'s 200 lb
> guard load has to reach ground through the landing into the seat beams and down
> `PT-BW-GW`/`GE`, whose `ABU66SS` bases ARE anchored. **No check in this engine follows that
> path.** `structural.uplift_path_coverage` now reports these two NOT_APPLICABLE and says
> why, which is honest about the joint and silent about the diaphragm. If a reviewer wants it
> closed, the cheap answer is one anchor back in the east base, not the thickening back.
>
> `structural.deck_footing_size` still reports NOT_APPLICABLE and correctly: R507.3.1 sizes a
> spread footing over soil and no soil is in this load path. A `Pad` stays the wrong element
> for any future thickening — one pour with the slab has no element that says "monolithic",
> and an isolated pad reports a `concrete_interference` lap with the slab it is part of.
>
> **They are 4x4 KDAT, 25 3/4" tall, on `ABU44` standoff bases, unanchored (owner,
> 2026-09-11).** The 1" standoff is the reason the part is here and it is not a dry-location
> nicety: `SL-G-FLOOR` is authored `EXPOSED_MIX` for ACI exposure class **C2** on the
> house's own reasoning that chloride arrives on the car and pools on a floor nobody rinses,
> and this corner is 3'-0" inside the service door where plowed snow is walked in. The
> standoff keeps the post's end grain out of that water. The first pass authored 6x6s sized off the PIER top, so they
> stopped at −1'-3 1/2" under carriers whose soffit is −0'-8 1/4" — a 7 1/4" gap nothing
> graded. `structural.deck_post_size` reads Table R507.4's 6'-9" for a 4x4 against 2'-1 3/4".

> ⚠ **Hold the deck boards 1/2" off the house cladding and let the gap drain.** Boards run
> tight to a rainscreened wall dam the drainage plane and hold water against it. Abutting is
> not bearing, so this costs the "touches nothing" rule nothing — but it must be DRAWN,
> because a carpenter will otherwise close it.

The garage-side floor system is the structural zone inside the door, not a second concrete
landing; a 1/4" drainage/movement break separates its board field at the threshold. It
extends three clear feet beyond the ICF stem's finished inside face (x=6'-11 5/8" — the 11"
ICF plus its 5/8" `gwb-stem` board), `ST-G-SERVICE` arrives at its north edge flush to that
face, and `SL-G-STEP-0` is retired. **Since 2026-09-11 it stands in the garage's SW corner**:
sheet x 6'-7"..9'-11 5/8", a quarter inch off `W-G-W`'s gyp face, so the wall is its west
guard (`RL-BW-GARAGE-W` is deleted) and `RL-G-SERVICE` is a wall-mounted handrail on
`W-G-W` — one bracket on a stud at the landing end, one on 2x12 blocking (`BK-G-W-RAIL-FOOT`,
`plan/backing.py`) at the foot.

## 3. The tiers — four cast pours on a compacted base

`SL-BW-TIER1..4`, 18" going, one riser (6.8") thick each, **wedding-caked**: tier *i* runs
from the landing edge east to the front of its own tread, so every tier above the first is
fully bedded on the one below it and nothing here spans. EXPOSED_MIX (ACI 318-19 F3 + C2),
broom finish, 1/4" per foot of cross-fall east. `ST-BW-ENTRY` carries the flight's *code*
geometry — rise, going, width, the guard it serves — and frames nothing (`carriage="cast"`).

This is the third scheme and the two it replaced are worth keeping, because each failed for
a reason that is easy to walk back into.

**A cut stringer failed three ways.** An 8'-0" horizontal span against DCA 6 Fig. 28 / IRC
R507.13.1's 6'-0"; a 4.71" throat against its 5"; and treads wanting supports closer than
12". Narrowing the going to 18" fixes the span and does *not* fix the throat — notch depth
is driven by the long going, so a flatter pitch removes *more* material, and holding 5" at
6.8:18 would want an 11.54"-wide member.

**KDAT box frames on eight 42"-deep piers failed on the piers.** They were laid out running
east from the stair foot at x=17'-6" while the flight runs **west** to x=11'-6" (the landing
edge then; 15'-7" and 9'-7" since 2026-09-11), so all eight stood under open ground
carrying nothing at all. Nothing in the check tree noticed,
because nothing grades whether a pier is under the thing it names.

> ⚠ **These are NOT frost-founded and that is a decision, not an oversight.** Minn. R.
> 1303.1600 puts Zone II at 42"; these bear about 6" down on compacted washed rock. The
> tiers will move with the ground. A monolithic pour moves **as one piece**, so what a
> winter costs is the joints at the two ends, not the risers in between — and riser
> uniformity has only 3/8" of tolerance (R311.7.5.1). At the bottom the pavers are a
> flexible field and nothing depends on them. **The joint that matters is at the TOP**,
> where the fourth tier meets a deck landing standing on piers that will not move. Draw it,
> and expect to shim or re-pour that one riser once.
>
> The framed alternative on the same base would have been worse, not equal: a settling box
> turns the flight into a cantilever off `BM-BW-FE`, which nothing in that assembly can do.
> And the prescriptive route to a shallow section does not exist here — IRC R403.3 applies
> only to buildings kept at 64°F or warmer and says outright it "shall not be used for
> unheated spaces such as porches", Minnesota's Rules 1309.0403 amendment carries no
> exceptions, and ASCE 32 is a stamped engineered submittal. **This is an owner's decision
> to accept movement on an unheated exterior terrace, taken knowingly.**

## 4. The screen — a solid shear panel with a slat clerestory over it

**Bottom, deck to +4'-0": `W-BW-SCREEN`.** KDAT 2x4 at 16" o.c. It runs the full deck edge,
house cladding to garage wall, on its own 2x8 sill (`BM-BW-SCSILL`) spanning the two seat
beams between the two columns. It does three jobs: the canopy's north-south shear panel
(§1a), the guard, and the closure over the deck framing.

**The two faces are not the same, and that is the 2026-09-11 decision.** WEST takes 5/8" CDX
under 7/8" `corrugated-panel-26` — the garage's own panel, because the two structures already
share a roof plane and a different profile on the one wall standing under that joint would
read as a mistake. EAST takes one 5/8" APA Rated Siding 303 panel with an MDO face, doing
shear and finish together. That face stands **under the canopy roof**: it is a finish problem,
not a weather problem, and buying the house's exposed-fastener steel for a sheltered face is
paying weather money for it. The shear is taken on the west face alone.

The wall carries `alignment=face("stud-ext", offset=inch(-1.75))` so its 2x4s stay centred on
the `PT-BW-CW`/`-CNW` column line at x=6'-0". Without it the stack re-centres when the east
skin comes off and slides every plate 7/16" east off the two 6x6s, which
`structural.member_interference` reports six times over — and it slides the west corrugated
face off the plane it shares with the garage panel, which is the one plane here that is not
free to move.

**`W-BW-SCREEN-SKIRT`, −0'-1" down to −1'-2 1/2".** The same corrugated sheet, carried 13 1/2"
further down over `BM-BW-SCSILL`, the two seat beams and the `ABU66SS` standoff bases under
the two columns. An earlier pass left that band bare on purpose — treated stock and stainless
bases "meant to be seen and reachable to inspect" — and this reverses it: keeping bulk water
off the column bases off a 4'-0" wall with no gutter over it is worth more than the access,
and the bases are still reachable from the east, where nothing covers them. **The bottom edge
stays open**, 1" clear of the cast pier tops, so the flutes drain and the band vents. A 13 1/2"
drop off a continuous sheet is a cantilever, not a span, so there is no bottom girt to trap
water. It is its own element with its own node pair rather than a lower base on the panel:
`Layer.extent` is clamped to its wall, and the framing solver takes its plate elevation from
the wall base regardless of any band, so dropping the panel's base would put a sole plate on
the pier tops and re-open the seat-beam clash §4 already records.

**Top, +4'-0" to the header soffit: `SC-BW-WEST`.** 2'-4 3/4" of on-edge 2x4 slats at a 1 1/2"
clear gap, sitting on the panel's top plate and restrained at the header soffit. In-fill only,
`role="screen"`.

> ⚠ **Why the slats are not the guard, and why nothing is asking them to be.** IRC Table
> R301.5 puts **200 lb concentrated** on a guard (the 50 plf line load is IBC §1607.8.1, not a
> residential provision), and a 2x4 on edge cantilevered 36" off a deck is d/c 1.34 at C_D 1.6.
> The base is worse than the member: Virginia Tech's full-scale tests behind DCA 6 measured
> 178 lb ultimate for 1/2" lag screws and 237 lb for 1/2" bolts, while resolving that base
> moment wants ~1,700 lb of tension per slat. The solid panel takes the load; the slats above
> it carry only Table R301.5 footnote f's 50 lb over one square foot, which also makes them
> **immune to the 2018-vs-2021 "in any direction" question** that would otherwise decide the
> whole detail.

> ⚠ **Two elements retired here, and one nearly-shipped detail.** `RL-BW-WEST` went first
> (1 1/2" off the screen line, a plan clash). `RL-BW-SCREEN`, the metal guard that replaced
> it, went on 2026-09-10 when the panel closed the same edge — one element where there were
> two, and no aluminium product bought for an edge closed by KDAT. And an intermediate pass
> put two 2x6 cross rails on the column line at +1'-0" and +3'-0" to carry the guard load
> into `PT-BW-CW`/`-CNW`; the solid panel superseded both, and they were deleted rather than
> left buried inside its studs.

> ⚠ **Two openings to check that are NOT the sphere between slats**: the gap under the bottom
> of the panel to the deck surface, and the end gaps where it meets the house and the garage.
> Both are openings in a required guard and both count.

> ⚠ **Field-treat inside the panel before it is closed.** Every cut end, notch and hole in
> that KDAT framing gets 2% copper naphthenate per AWPA M4 (§6), and nothing reaches it once
> the second skin is on.

## 5. The joint at the house, drainage, and snow

The canopy's south edge leaves a **7 3/8" gap** to the house cladding. A positively sloped
closure attaches to the **canopy only**, dying at the house in a replaceable compressible or
brush seal, inspectable from below, never filled with rigid foam or sealant. The two
buildings move independently and the joint has to. Maintain the house rainscreen.

> ⚠ **This is the ONLY movement joint, and §1a is why.** The same sentence used to be written
> about the garage joint as well, at the same time as §1 called that plane the canopy's entire
> lateral system. The garage joint is now a tied, drawn connection and the two roofs move
> together; this one, at the house, is where two independently founded structures really do
> meet.

Provide fire/draft closure at the original garage south gable plane, retain garage gypsum,
and confirm the service door's rating and self-closing requirement with the AHJ. **That plane
is clear now**: nothing of the canopy stands in it since the fourth truss went (§1), so the
garage's south cladding and its insulation run full height to the deck underside, which is
the face the entry actually sees. **The
movement joint is not a fire separation.**

**Drainage, and the margin is worth stating rather than discovering.** Both garage eaves
carry a 5" trough falling north to a single 3" leader each; `params/roof_trim.py` works
~425 sf per 3" leader at the 8 in/hr design intensity. Each slope shed ~290 sf before this
change and now sheds ~366 sf, so the margin falls from about 47% to about 17%. Still inside.

**The canopy's eaves are on the same trough, and that is the point.** `RF-BW-CANOPY` carried
no eave trim at all until 2026-09-10 — bare sheathing edges on both eaves, no fascia, no
gutter, over the one walking surface between the two buildings. It takes the garage's own
fascia stack now, and the channel runs continuous from the canopy's south end to the garage's
north end, falling north to the same two leaders. **No leader at the canopy's south end**: it
would discharge onto the entry landing and the four cast tiers, which is the exact discharge
the garage's own leaders were moved north to avoid. **No soffit**, and that one piece
deliberately does not continue: there is no wall under either canopy eave for a soffit to die
into, an open canopy's underside is exposed framing by design, and the garage's white PVC
soffit is there to feed a vented attic this roof does not have.

Snow retention is required along the east/west roof zones over the screen, tier approach and
equipment circulation; the supplier sizes crossbars and clamps for the **drift** case, not
the ground load. **Wind seam clamps are not a substitute for snow retention.**

## 6. KDAT longevity — the house-wide spec (owner, 2026-09-10)

Stated once here and carried onto the drawings by `AN-BW-KDAT`, because it applies to every
treated member in this assembly and repeating it per element invites drift.

- **304 stainless fasteners.** IRC R317.3.1 also permits hot-dip galvanized to ASTM A153,
  silicon bronze and copper, and FPL-GTR-220's hygrothermal model puts Minneapolis in the
  bottom third of its nine cities for corrosion depth (12 µm, against 45 in Hilo) precisely
  because the wood is below freezing ~2,500 hours a year. **So 304 is a durability and
  appearance choice, not a code requirement, and 316 buys chloride resistance this site does
  not need** unless the treads get salted. Never mix stainless and galvanized in one joint.
- **Butyl joist tape** over every beam and rim top (`top_protection`). Butyl or acrylic, not
  asphalt: bitumen cold-flows at deck temperatures and its oils migrate into flexible PVC.
  **There is no code hook and no independent study** showing a service-life gain — DCA 6
  never mentions joist tape — so this is durability insurance, bought for the fastener
  penetrations. In Minnesota watch the install temperature: Trex Protect wants 50°F, while
  G-Tape and PRO-Tac go to −40°F and below.
- **AWPA M4 field treatment** of every cut end, notch and drilled hole, 2% copper naphthenate.
  **This one is not advice**: IRC R317.1.1 says "shall", and R507.2.1 repeats it for decks.
- **A pigmented penetrating oil**, applied on installation. **NOT a silicate.** Sodium and
  potassium silicate are masonry densifiers — they work by reacting with free lime, which
  wood has none of. The only credible decay result (Chen 2009, FPL, Wood and Fiber Science
  41(3)) required pressure impregnation followed by acid gelation; brush-applied, silicate
  leaches (~50% in a year of weathering), *raises* moisture uptake, and effloresces. It also
  carries no pigment, and per FPL "Finishes for Wood Decks" pigment is the single largest
  driver of service life on a deck. Expect a **2–3 year recoat on the treads and landing**;
  the risers and rails, being vertical, run 2–3x that. Never a film-forming finish here.
- **KDAT changes one thing and it is the timing.** It arrives at ~19% moisture content, so
  it can and should be finished immediately on installation rather than waiting weeks for
  wet-treated stock to dry. FPL: "most decks are retired because of cracks and checks that
  mostly could have been avoided by timely finishing." A KDAT landing left bare through one
  Minnesota winter has thrown away the advantage it was bought for.

## 7. Excavation and release conditions

> ⚠ **Sequencing, and it is worth more than any dimension in this note.** All five north
> entry piers bottom at −9'-9 7/16", the same elevation as the house footing, about ten
> inches away. Cast in the open basement excavation — the owner's stated premise, and the
> only reason reaching that depth is cheap — that is a non-issue. Cast **after** the house
> footing is in and backfilled, a shaft ten inches away bearing at the same depth is
> **undermining**, and the answer becomes benching the excavation or bearing the piers
> higher and lengthening the columns.

Excavate and waterproof the deeper house first while access is open. Confirm native garage
bearing before backfill; form garage footings and stem and coordinate sleeves while the
house cut remains accessible, then compact backfill in controlled lifts.

Still external deliverables, not model checks: the survey and zoning determination for the
complete roof projection, an actual soils report (2,000 psf is presumptive and no boring log
exists), and the truss fabricator's design — **quoted against the drift case, not the ground
snow**. See `notes/north_entry_piers.md` §7 for what the calculations themselves exclude.
