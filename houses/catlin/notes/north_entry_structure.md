# North entry — the bearing map

**House:** catlin. **Basis:** the entry as built on 2026-11-14 (`EAST_POST_SYSTEM = "kdat"`, the 2026-10-31
wind). Implements [the selected concept](../../../plans/north-gable-extension.md).
**This note is the bearing map: what carries what, and what the drawings must say that the model cannot.** It has
no oracle role. The arithmetic lives in `notes/north_entry_piers.md` (`engineering/roof_beam.py`, the pier and
deck-tie calcs), `notes/canopy_west_band.md` (the west line, heads, bases, headers) and
`notes/north_entry_canopy_lateral.md` (the generic collector, anchorage and torsion arithmetic).

The garage keeps its 24-foot square frost-depth ICF foundation. The passage between house and garage is its own
roof on its own structure, not a cantilever off the garage's gable.

## 1. The canopy — freestanding for gravity

`RF-BW-CANOPY` is **three** 24'-span trusses at 24" o.c. on two headers, each header on **two** posts of its own.
It is ONE truss with `RF-GARAGE`: 23'-10 3/4" out to out of bearing, bottom chord across the full 5 1/2" at both
ends, SBCA standard heel 3.9393" at the OUTSIDE face of bearing, so the two roofs are one plane. `CANOPY_ROOF` is
`GARAGE_ROOF`'s structure with **no insulation and no ceiling**: an open outdoor bay has no thermal boundary to
hold, and billing one would order 144 sf of R-38 blown fiberglass and 5/8" gypsum nobody installs.

> ⚠ **Three trusses, not four.** `roof_gable.build_truss_layout` forces a last truss station onto the end of the
> bearing so a gable wall never ends up with the field stopping short of it; these headers stop at the north
> posts, so that forced station would stand a fourth truss 1 1/2" off `W-G-S`, out of module and back to back
> with `RF-GARAGE`'s own gable truss, in the plane the fire/draft closure and the garage's south cladding need
> clear (§5). The roof authors `gable_ends=()` and the engine drops an off-module end station that is not a gable
> line. The deck bridges about 2'-0" from truss 3 to `RF-GARAGE`'s gable truss.
>
> **That last bay is the one place a little gravity does cross.** The bridging sheathing hands the gable truss
> half a 2'-0" bay over 24 feet: roughly **2,000 lb** under 73.7 psf drift snow plus 10 psf dead, inside the
> 9.8' drift zone off the house gable. It lands on a frame bearing **continuously** on `W-G-S`, so it spreads to
> about **84 plf** on a 2x6 wall already carrying half a garage bay. Trivial, and real: §1a's "never gravity" is
> about the **strap line**, not the deck edge.

> ⚠ **The headers do not bear on `W-G-W` / `W-G-E`.** A reaction of about 3,130 lb on the END of a stud wall wants
> a bearing post through the plate, the stud bay, the sill and the ICF stem; `bearing_refs` naming a wall is this
> engine's idiom for a beam landing ALONG it and grades nothing about a terminus. The canopy carries its own
> gravity to its own piers and shares nothing structural with the garage but the sheathing plane.

| Member | Support | What the drawings must say |
|---|---|---|
| `RF-BW-CANOPY` | `BM-BW-RW`, `BM-BW-RE` | Sheathing runs **continuous** across the garage south wall line, no seam at the garage gable. Two `Roof` elements, one diaphragm: the canopy's connection to the garage. |
| truss-to-header | `CN-BW-TRTIE-W1..3`, `-E1..3` | One **stainless `H2.5ASS`** each end of every truss (six). Not the galvanized H2.5A the rest of the house buys: these land on treated glulam at an entry that is salted every winter. |
| `BM-BW-RW` / `-RE` | `PT-BW-CW`/`-CNW` and `PT-BW-RE`/`-RNE` | 5-1/2" x 11-7/8" treated glulam (24F-V4 DF), top at +7'-4" = the garage plate, **65-1/4" long, post face to post face, no tails**, 4'-11 3/4" between posts, centred on the garage's truss lines (x 6'-3 3/8" / 29'-8 5/8"). The deck, not the header, oversails (south 1 3/8", north 6 1/8") to reach the garage wall; open air at both beam ends (8" to the house cladding, 5 1/4" to the garage cladding). **The two headers do not land on the same thing.** |
| `PT-BW-CW` / `-CNW` | `PT-BW-W` / `PT-BW-GW` | The WEST pair: 6x6 KDAT, 7'-8 5/16", the chords of `W-BW-SCREEN`. `ACE6Z` end cap at the header, one `A35Z` across the beam, cast-in `CBSTQ66Z-SDS2` base in a 14" round pier. `PT-BW-CW` shares its pier with the house-side seat beam and `PT-BW-CNW` with the garage-side one. |
| `PT-BW-RE` / `-RNE` | `PT-BW-PE` / `-PNE` on `PD-BW-RE` / `-RNE` | The EAST pair, selected by `EAST_POST_SYSTEM`: **6x6 KDAT, 6'-2 1/8"**, `ACE6Z` cap, one `A35Z`, cast-in `CBSTQ66Z-SDS2` in 14" round piers whose tops are 3'-0" over grade, with drained, accessible PVC column wraps (a finish, no capacity). `"steel"` (pinned HSS 4x4x1/4 on the same piers) and `"cast"` (the full-height fixed cast columns) remain graded alternatives. `canopy_garage_diaphragm.md` §5a grades the wood. |

> ⚠ **NEITHER END OF THE CANOPY IS A GABLE END.** A gable-end frame is plated with verticals at stud spacing, has no
> engineered web joints, and is supported **continuously by the wall or beam under its bottom chord**: it does not
> span, and it bills on its own row at a premium. All three canopy trusses are ordinary **field** trusses spanning
> 24' between the two headers, because there is no wall under either canopy end: the south end hangs over the open
> passage, and the north end's plate belongs to the garage. `RF-GARAGE` keeps its two, on `W-G-S` and `W-G-N`.

> ⚠ **No ladder framing anywhere at this joint.** `RF-GARAGE`'s south gable and both ends of `RF-BW-CANOPY` are
> **close rakes**: the roof deck cantilevers past the last truss and the fascia hangs on it (the garage's south
> projection is 1 9/16", the canopy's own south drip edge 3 3/8"). Neither is built with a 2x4 lookout and a 2x6
> barge rafter.

## 1a. The lateral system

The canopy braces two ways, each graded at **100% of the shear it delivers**, on purpose (a deliberate double
envelope, confirmed by the owner 2026-11-14): **across the tied joint into `RF-GARAGE`** and **through
`W-BW-SCREEN`**. The wind is `canopy_garage_diaphragm.md` §2's one derivation (q_h 18.149 psf, p 16.661 psf ASD);
the delivered shear is **670.77 lb E-W and 1,034.49 lb N-S**.

**North — the garage joint is a tie, and the two roofs move together.** Six `LSTA24` straps at 4'-0" o.c.
(`CN-BW-JOINT-1..3, -5..7`; none at the ridge), continuous deck panels nailed at 6" into the garage gable's top
chord, and seven `LTP4` gable clips (`CN-BW-GCLIP-1..7`) into `W-G-S` make the continuity a drawn, counted
connection, graded in `canopy_garage_diaphragm.md` §3-§4. **The movement joint that remains is at the HOUSE end**,
where two independently founded structures actually meet (§5).

**East — pinned posts.** With `EAST_POST_SYSTEM = "kdat"` the east posts are pinned at both ends and resist no
storey shear: each returns its own drag (23.59 lb) to the deck and to its pier. The canopy has no E-W line of its
own; its E-W shear crosses the joint into `RF-GARAGE`, `W-G-S` / `W-G-E` / `W-G-W`. The `cast` alternative is two
fixed full-height cast columns (12" round, `(4) #5 + #3 @ 10"`, fixed at the base) whose roof-thrust screen is
`north_entry_piers.md` §8: the engine bounds ASCE 7-16 Fig. 27.3-4's `C_N` with a solid-sign surrogate because
that figure is not held in this repository. The `cast` alternative's fixed-base embedment (IBC 1807.3.2.1) and sway
slenderness are the engineer of record's.

**West — a sheathed shear panel with a braced band over it.** `W-BW-SCREEN`: KDAT 2x4 at 16" o.c., deck to
+4'-0", flush with the chords' west faces, **read over its chords 5.4375' out to out: 190.3 plf vs 265 (0.718),
aspect 0.75 vs 3.5**. The shear rests on the WEST face alone (5/8" CDX under 7/8" corrugated, 8d at 4" edges);
the east face is finish only. The band over it, `SB-BW-BAND`, is one corner-to-corner 6x6 knee brace per bay, two
open-knee `KBS1Z` per end (742.8 lb vs 993.2, 0.748). The chords' hold-down over the full height reads 2,230 lb vs
3,060 (0.729), the base shear on one base 1,034 vs 1,270 (0.815), the eave collector's six `LTP4Z` 172.4 lb vs 450
(0.383). The deck's unit shear at the screen line, 172.4 plf vs 190 (0.907), governs. All of it:
`canopy_west_band.md` §3-§5.

## 2. The landing

`FS-BW-FLOOR` retains uid `BWFS01AAAA`. Finished surface 0" at both thresholds; framing one inch lower for the
composite. Five exterior rises from the entry walk `SL-WK-C` at -33" are exactly 6.6".

**The landing touches nothing on the house.** Grep `params/breezeway.py` for `W-B-` and expect nothing but
comments. Its house-side bearing is two cast piers on the pier line at y=37'-6", not brackets standing off the
basement concrete.

| Member | Support | What the drawings must say |
|---|---|---|
| `BM-BW-HOUSE-SEAT` | `PT-BW-W` (14"), `PT-BW-E` (12") | 3'-7" between two round piers, soffit -15.44" (-1'-3 7/16"). An `SS316-SHIM-35` pack under it (bearing, and the dielectric off the pour). The tie is a cast-in `HETA20Z` pair at `PT-BW-E` and the `LUS26-2Z` hanger on the `CBSTQ66Z-SDS2` post at `PT-BW-W` (`canopy_west_band.md` §5f). |
| `BM-BW-GARAGE-SEAT` | `PT-BW-GW` (14"), `PT-BW-GE` (12") | Identical span, elevation and detail. |
| `BM-BW-SCSILL` | Both west columns | The screen panel's sill and the deck's west rim in one 2x8, on the screen axis (1" west of the column line) where the joist field cannot reach; hung from both columns on `LUS28Z` (`CN-BW-HGR-SCS-*`). |
| `BM-BW-FE` | Both seat beams | A 3-ply 2x8 east edge beam on the RO's east jamb line, ending at the garage seat beam, so nothing crosses the stem or `W-G-S`. Its tip takes deck tie line 1 (two `HL43HDG` into `W-G-S`, `params/landing_tie.py`). |
| `FS-BW-FLOOR` joists | Both seat beams | 2x8 at 12" o.c. running **north-south**, bearing on top, overhanging 9 1/2" south and 7 1/4" north. Joist tape, stainless fasteners. |

> ⚠ **ONE TIER OF BEAMS.** Pier, seat beam (east-west), joist (north-south), board. `BM-BW-FE` is not a tier: it
> sits in the joist plane as the field's east edge. **The seats are the tier that fits:** putting north-south beams
> straight on the piers fails on one line, because x=6'-3 3/8" is occupied at both y stations by a canopy column
> standing on that same pier and rising through the deck band. The columns own that line; the seats get the piers.

> ⚠ **Hold the deck boards 1/2" off the house cladding and let the gap drain.** Boards run tight to a rainscreened
> wall dam the drainage plane and hold water against it. Abutting is not bearing, so this costs the "touches
> nothing" rule nothing, but it must be DRAWN, because a carpenter will otherwise close it.

There is no interior garage landing: `D-G-SERVICE` swings OUT onto this deck, and `ST-G-SERVICE` rises straight to
the threshold with its stringer heads seated on the `W-G-S` stem (`notes/garage_service_door_outswing.md`). A 1/4"
drainage/movement break separates the board field at the threshold.

## 3. The tiers — one stepped pour on a compacted base

`SL-BW-TIER1..4` are four `Slab` elements and **one placement**: side forms, riser boards hung, poured
monolithically off the walks' truck by the flatwork crew (`task/concrete/building/flatwork`), after backfill and
after the landing is framed and decked, so the top riser is set to the deck. Until then the entry takes a
temporary wood stair. 18" going, one riser (6.6") per tier, **wedding-caked**: tier *i* runs from the landing edge
east to the front of its own tread, so every tier above the first is fully bedded on the one below it and nothing
here spans. EXPOSED_MIX (ACI 318-19 F3 + C2), broom finish, 1/4" per foot of cross-fall east. `ST-BW-ENTRY` carries
the flight's *code* geometry (rise, going, width, the guard it serves) and frames nothing (`carriage="cast"`).

> ⚠ **These are NOT frost-founded and that is a decision, not an oversight.** Minn. R. 1303.1600 puts Zone II at
> 42"; these bear about 6" down on compacted washed rock. The tiers will move with the ground. A monolithic pour
> moves **as one piece**, so what a winter costs is the joints at the two ends, not the risers in between, and
> riser uniformity has only 3/8" of tolerance (R311.7.5.1). At the bottom the walk is on grade beside tier 1,
> across a 1/2" joint, and moves with it. **The joint that matters is at the TOP**, where the fourth tier meets a
> deck landing standing on piers that will not move. Draw it, and expect to shim or re-pour that one riser once.
> The prescriptive route to a shallow section does not exist here: IRC R403.3 applies only to buildings kept at
> 64°F or warmer and says outright it "shall not be used for unheated spaces such as porches", Minnesota's Rules
> 1309.0403 amendment carries no exceptions, and ASCE 32 is a stamped engineered submittal. **This is the owner's
> decision to accept movement on an unheated exterior terrace, taken knowingly.**

**Concrete kept over wood or brick (owner, 2026-11-03).** Each alternative still needs a pad poured with the walks,
then adds a return trip (a carpenter, or the mason, whose visit is early for the court veneer). PT framing with
composite treads and fascia risers lasts less on a wet, salted pad and grips worse in ice. Brick steps are a veneer
over this same concrete stair, plus mortar joints that salt and freeze-thaw take apart. The cast flight rides a
truck that is coming anyway.

## 4. The screen — a solid shear panel with a braced band over it

**Bottom, deck to +4'-0": `W-BW-SCREEN`.** KDAT 2x4 at 16" o.c. It runs the full deck edge, house cladding to
garage wall, on its own 2x8 sill (`BM-BW-SCSILL`). It does three jobs: the canopy's north-south shear panel
(§1a), the guard, and the closure over the deck framing.

**The two faces are not the same.** WEST takes 5/8" CDX under 7/8" `corrugated-panel-24`, the garage's own panel,
because the two structures already share a roof plane and a different profile on the one wall standing under that
joint would read as a mistake; it carries the shear. EAST is white painted 3/4" exterior MDO in three removable
panels screwed directly to the framing, 1 1/4" behind the exposed timber, with no WRB or ventilation cavity: a
finish under the canopy roof, no shear (`notes/entry_screen_mdo.md`). One solid KDAT 6x6 lower centre timber and five
2x4 edge nailers complete it.

The wall carries `alignment=face("stud-ext", offset=inch(-1.75))`, so its 2x4s stand flush with the west faces of
`PT-BW-CW`/`-CNW` (`SCREEN_AXIS_X_FT`, 1" west of the column line): the CDX laps the chords and the west
corrugated plane is the garage panel's own, the one plane here that is not free to move. Both columns carry
`within_wall`, so each plate course is cut flush at the column faces. The alignment rests on the cladding plane
alone.

**`W-BW-SCREEN-SKIRT`.** The same corrugated sheet carried further down over `BM-BW-SCSILL`, the two seat beams and
the `CBSTQ66Z-SDS2` bases under the two columns: keeping bulk water off the column bases off a 4'-0" wall with no
gutter over it is worth more than the access, and the bases are still reachable from the east, where nothing
covers them. **The bottom edge stays open**, short of the cast pier tops, so the flutes drain and the band vents;
a drop off a continuous sheet is a cantilever, not a span, so there is no bottom girt to trap water. It is its own
element with its own node pair because `Layer.extent` is clamped to its wall and the framing solver takes the
plate elevation from the wall base.

**Top, +4'-0" to the header soffit: `SB-BW-BAND`.** A 2x6 flat sill and top plate, a 6x6 centre post (two `A35Z` at
each end), and one 6x6 KDAT knee brace per bay running exactly corner to corner, chord to top plate, with two
open-knee `KBS1Z` at each brace end and eight `SDWS22400DB` through each plate: `canopy_west_band.md` §3.

> ⚠ **The solid panel is the guard.** IRC Table R301.5 puts **200 lb concentrated** on a guard (the 50 plf line load
> is IBC §1607.8.1, not a residential provision); the panel takes it. The band above carries only Table R301.5
> footnote f's 50 lb over one square foot, which also makes it **immune to the 2018-vs-2021 "in any direction"
> question** that would otherwise decide the detail.

> ⚠ **Two openings to check that are NOT a sphere between members**: the gap under the bottom of the panel to the
> deck surface, and the end gaps where it meets the house and the garage. Both are openings in a required guard
> and both count.

> ⚠ **Field-treat inside the panel before it is closed.** Every cut end, notch and hole in that KDAT framing gets
> 2% copper naphthenate per AWPA M4 (§6), and nothing reaches it once the second skin is on.

## 5. The joint at the house, drainage, and snow

The canopy's south roof edge leaves a **7 3/8" gap** to the house cladding. Keep this slot open: no closure, no
hood, no house attachment. Both beams end flush on their south posts, 5/8" behind the deck edge and 8" from the
house cladding, so the end grain sits under roof cover in open, inspectable air and is re-sealed by brush.
Maintain the house rainscreen.

> ⚠ **This is the ONLY movement joint, and §1a is why.** The garage joint is a tied, drawn connection and the two
> roofs move together; this one, at the house, is where two independently founded structures really do meet.

Provide fire/draft closure at the original garage south gable plane, retain garage gypsum, and confirm the service
door's rating and self-closing requirement with the AHJ. **That plane is clear**: nothing of the canopy stands in
it (§1), so the garage's south cladding and its insulation run full height to the deck underside, the face the
entry actually sees. **The movement joint is not a fire separation.**

**Drainage.** Both garage eaves carry a 5" trough falling north to a single 3" leader each; `params/roof_trim.py`
works ~425 sf per 3" leader at the 8 in/hr design intensity. Each slope sheds about 366 sf, so the margin is about
17%.

**The canopy's eaves are on the same trough, and that is the point.** It takes the garage's own fascia stack, and
the channel runs continuous from the canopy's south end to the garage's north end, falling north to the same two
leaders. **No leader at the canopy's south end**: it would discharge onto the entry landing and the four cast
tiers. **No soffit**: there is no wall under either canopy eave for a soffit to die into, an open canopy's
underside is exposed framing by design, and the garage's white PVC soffit is there to feed a vented attic this
roof does not have.

**Snow retention** is required along the **east eave over the entrance and tier approach**; the west side has no
entrance or walking route beneath it, so it needs none. Size crossbars and clamps for the **drift** case, not the
ground load. **Wind seam clamps are not a substitute for snow retention.**

The provisional 3D layout is **one continuous ColorGard 2.0 unpunched run**, `CN-BW-SNOW-E-1`, hosted by
`RF-BW-CANOPY`, with its clamp line at x = 31 ft (4 inches inside the roof eave). Four full S-5-N clamps follow
the shared garage/canopy panel seams; four VersaClip 2.0 attachments carry the profiled crossmember and
roof-matching 2-inch ColorStrip; three SnoClip 2.0 II clips have rubber feet on flat pan intervals between
striations. Roof pitch, layer depth and seam height determine elevation; there is no hand-set Z. The north rail
end is 2 inches inside the canopy rake. The south setback is **7-5/8 inches**: a 2-inch setback would leave a
13-9/16-inch cantilever from the first shared seam, over S-5!'s 8-inch limit; the modeled south cantilever is
7-15/16 inches. One 7-foot-8-inch stock crossmember is cut to the run; its supplied splice is unused. The
S-5-N bolts/setscrews and SnoClip securing screws come with those parts. Takeoff reports installed rail/strip
length and actual component counts.

**This is hardware geometry and provisional coverage, not a retention-capacity check.** The online-only
[S-5! review](s5_snow_retention_review.md) records profile evidence, SnoClip support, tributary-garage screening
and published component prices. Owner-supplied S-5! parallel load data establish **863 lbf allowable per full N on
Image II 24 ga steel at safety factor 2**: four clamps total **3,452 lbf allowable against the review's 3,839 lbf
tributary-wedge screening demand**, below it even with ideal load sharing. **One row is provisional**; the full
drift/tributary check, rail/end reactions and panel attachments remain unresolved, and the single row must not be
treated as sized. No supplier contact is requested.

## 6. KDAT longevity — the house-wide spec (owner)

Stated once here and carried onto the drawings by `AN-BW-KDAT`, because it applies to every treated member in this
assembly and repeating it per element invites drift.

- **304 stainless fasteners.** IRC R317.3.1 also permits hot-dip galvanized to ASTM A153, silicon bronze and
  copper, and FPL-GTR-220's hygrothermal model puts Minneapolis in the bottom third of its nine cities for
  corrosion depth (12 µm, against 45 in Hilo) precisely because the wood is below freezing ~2,500 hours a year. **So
  304 is a durability and appearance choice, not a code requirement, and 316 buys chloride resistance this site
  does not need** unless the treads get salted. Never mix stainless and galvanized in one joint; Simpson's ZMAX
  parts (`ACE6Z`, `A35Z`, `LTP4Z`, `CBSTQ66Z-SDS2`) take the hot-dip galvanized nails their schedules call for.
- **Butyl joist tape** over every beam and rim top (`top_protection`). Butyl or acrylic, not asphalt: bitumen
  cold-flows at deck temperatures and its oils migrate into flexible PVC. **There is no code hook and no
  independent study** showing a service-life gain (DCA 6 never mentions joist tape), so this is durability
  insurance, bought for the fastener penetrations. In Minnesota watch the install temperature: Trex Protect wants
  50°F, while G-Tape and PRO-Tac go to -40°F and below.
- **AWPA M4 field treatment** of every cut end, notch and drilled hole, 2% copper naphthenate. **This one is not
  advice**: IRC R317.1.1 says "shall", and R507.2.1 repeats it for decks.
- **A pigmented penetrating oil**, applied on installation. **NOT a silicate.** Sodium and potassium silicate are
  masonry densifiers: they work by reacting with free lime, which wood has none of. The only credible decay result
  (Chen 2009, FPL, Wood and Fiber Science 41(3)) required pressure impregnation followed by acid gelation;
  brush-applied, silicate leaches (~50% in a year of weathering), *raises* moisture uptake, and effloresces. It also
  carries no pigment, and per FPL "Finishes for Wood Decks" pigment is the single largest driver of service life on
  a deck. Expect a **2-3 year recoat on the treads and landing**; the risers and rails, being vertical, run 2-3x
  that. Never a film-forming finish here.
- **KDAT changes one thing and it is the timing.** It arrives at ~19% moisture content, so it can and should be
  finished immediately on installation rather than waiting weeks for wet-treated stock to dry. FPL: "most decks are
  retired because of cracks and checks that mostly could have been avoided by timely finishing." A KDAT landing
  left bare through one Minnesota winter has thrown away the advantage it was bought for.

## 7. Excavation and release conditions

> ⚠ **Sequencing, and it is worth more than any dimension in this note.** The three HOUSE-side north entry piers
> (`PT-BW-W`, `-E` and the east-line pier) bottom on the house footing's own plane (their 12" moment pads at
> -9'-11 7/16"), about ten inches away. Cast in the open basement excavation (the owner's stated
> premise, and the only reason reaching that depth is cheap) that is a non-issue. Cast **after** the house footing
> is in and backfilled, a shaft ten inches away bearing at the same depth is **undermining**, and the answer
> becomes benching the excavation or bearing the piers higher and lengthening the columns. The GARAGE-side piers
> (`PT-BW-GW`, `-GE` and the east-line pier) bear on the garage's own footing plane and are cast with the garage
> foundation.

Excavate and waterproof the deeper house first while access is open. Confirm native garage bearing before backfill;
form garage footings and stem and coordinate sleeves while the house cut remains accessible, then compact backfill
in controlled lifts.

## 8. The rest of the canopy's lateral path

The chord's delegation to the truss fabricator, the collectors, the generic hold-down anchorage and the torsional
term are in **`notes/north_entry_canopy_lateral.md`** (§8), the oracle for the collector, anchorage and torsion
rows of `engineering/lateral_system.py`. The one sentence that changes what §1a says: **"freestanding" holds for
gravity only.** The canopy's E-W and N-S shears are both delivered across the tied joint into `RF-GARAGE` (and
independently through `W-BW-SCREEN`), each graded at 100%, with no canopy member on the north line to land on.

## Not graded here / still open

- The truss fabricator's sealed design and reaction schedule, **quoted against the drift case, not the ground
  snow**; the survey and zoning determination for the complete roof projection; and an actual soils report (2,000
  psf is presumptive and no boring log exists). External deliverables, not model checks. See
  `notes/north_entry_piers.md` §7 for what the calculations themselves exclude.
- ColorGard snow retention: four clamps 3,452 lbf vs 3,839 lbf screening demand; one row is provisional (§5).
- The seat-beam `LUS26-2Z` on its 11/32" filler (Simpson publishes no filler installation): `canopy_west_band.md` §9.
- The screen's lower KDAT timber end connections are not released: `notes/entry_screen_mdo.md`.
- The tiers' movement (§3), accepted by the owner.
