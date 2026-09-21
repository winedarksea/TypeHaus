# Catlin house — design record

Why the house is the way it is. Every entry here was once in `CLAUDE.md` and was moved out
so that file could stay a constraint index an agent can read in one sitting.

**This file is history, not instruction.** Nothing here is a rule, nothing here is
authoritative about the current model, and an entry may describe a design that has since
been replaced. `CLAUDE.md`, the plan source under `plan/`, and the notes under `notes/` are
the present state. Read this when you want to know *why* a number is what it is, what was
tried before, or which engine bug a rule exists to dodge — and when a decision here
contradicts the model, the model wins.

Sections match `CLAUDE.md`'s one for one, with one exception: **In-wall backing** at the
bottom has no constraint-index section of its own — the constraints live in
`notes/wall_backing.md` and in `plan/backing.py`'s own header.

## Site and the four structures

### Three of the north entry's six piers became pads, and the check had to learn the roof first (2026-09-14)

Six `spread_footing/` items sat in the register for six flat square bases on presumptive
soil. That is a table lookup, not a design — but `Pad`, the type that gets the lookup, is
graded by `structural.deck_footing_size` against an IRC **deck** table that knew nothing
about roof snow, and these carry a canopy. So they were authored `Footing` and the register
carried the consequence.

**The fix is in the check, not in the house.** `checks/structural/deck.py::_roof_borne_posts`
converts a post's roof-footprint share into R507.3.1's own currency —
`(DECK_DEAD_LOAD_PSF + Site.ground_snow_load_psf) / DECK_TOTAL_LOAD_PSF`, 1.2 on this site —
and hands it down the post chain, so the canopy's 40 ft² per column arrives at the table as
48 ft² of equivalent deck. It is a deliberate restatement of
`engineering/pier_basis._roof_fields`, because `engineering` is a leaf and the import that
would help runs the wrong way; **if one moves, move the other**, and
`test_pier_calcs.py` holds them together.

**`PT-BW-RE` and `-RNE` are why that had to come first.** They carry `BM-BW-RE`, a roof
header, and no deck at all — so they were in no deck's post list and this rule never reached
them. Not graded at zero: not graded. Their only coverage was the `spread_footing/` item
their Footing raised, and deleting it without the roof pass would have removed an item and
left nothing behind. Two further bugs fell out of the same pass, both of them the rule
answering one question twice:

* **A post standing on another post hands its load over, and that test now runs BEFORE the
  pad test.** It lived inside `_not_a_pad`, which is only reached when the chain does *not*
  end at a `Pad` — so the day `PT-BW-W` became a Pad, the wood column on it stopped being
  N/A and began reporting a PASS on that same pad, graded a second time against its own
  tributary and ignoring everything the first grading had put there.
* **A share handed down has to leave the post above.** `_handed_down` moves it, so the pier
  is sized with the column's load in it — which is what the N/A on the column promises.

**Three piers converted and three did not, and the split is the garage strip footing.**
`PD-BW-W`/`-E`/`-RE` bear at -9'-9 7/16" and clear everything. `PT-BW-GW`/`-GE`/`-RNE` bear
at -7'-0", on `FT-GF-S1`/`-S3`'s own plane, lapping about 7 1/2" into it — and a `Pad` is an
ISOLATED pour by definition, so calling them Pads asserts a pour standing clear of something
it is cast against. They cannot be pulled clear either: the pier line is 4 1/2" from that
footing's face and the shaft is a 12" round, so the column overhangs any pad stopping there.
One pour is the truth and `Footing.under` is how the model says it. **Three
`spread_footing/` items stay, as an open item rather than an oversight.**

The pads are 2'-6" x 1'-6" x 1'-0" rather than the 2'-0" square their Footings drew, and both
dimensions are forced. 18" north-south is what clears `FT-B-N1`..`-N4` on the same plane — a
24" square reached 2 1/8" into them, a lap that had always been there and had always been
invisible, because `concrete_interference` scopes every `Pad` and only a wall-less `Footing`.
30" east-west takes the area back to 3.75 ft² against `PT-BW-W`'s 2.48 ft² requirement. One
size for all three: three sizes are three rows in S-100's FOUNDATION SCHEDULE and that sheet
is one row from its schedule governing its height again. `prices.toml` gains a qualified
`pad:PIER_BASE_12` row — 0.35 cy, priced per yard rather than on the generic pad lump,
because these are sized and their excavation is open for the basement anyway.

- **Breezeway design (retired), in full.** Before the extruded garage gable superseded it, the fourth structure was an enclosed breezeway on freestanding 6x6 posts spanning the 4' gap door-to-door (`params/breezeway.py`), glazed in polycarbonate. The breezeway followed the doors, and nothing enforced that but one line: it was a 4'-6" enclosure centred on the midpoint of `D-M-ENTRY` (x 8'-0") and `D-G-SERVICE` (x 10'-0") — x 9'-0" as of 2026-09-09, once the two stopped being concentric. When either door moved, `_GLAZING_CENTER_X` and `_EW_FT` moved with it (`code.R311_3_exterior_landing` caught a shelter that drifted off its own door). Both doors opened onto the deck at 0'-0" and reached it from opposite directions: `D-M-ENTRY` from the house floor it shares, `D-G-SERVICE` up +1'-0" from a garage storey that sat at -1'-0". The breezeway deck did not move with grade — it was a bridge between two doors, and only its pads and piers followed the soil down. Only 7/8" of the garage's corrugated cladding panel projects past the sheathing plane, so it drips clear; the breezeway's own uncut 4' panel was measured off the cladding rather than the sheathing plane, and its core was 6" thick — a different alignment convention from the garage's. What survives of this design today is the foundation bridge (FS-BW-FLOOR, FS-BW-GARAGE), beams (BM-BW-*), a stair (ST-BW-ENTRY), a railing (RL-BW-ENTRY), and a slat screen (SC-BW-WEST); the posts, roof, and glazing described above are gone. The current design is recorded separately in notes/north_entry_structure.md.
- **Why grade sits 2'-10" below the main floor.** The basement-ceiling overhaul put a 12 5/8" deck where a 9" slab had been, and the house rose 4" rather than surrender the headroom under it — that 4" rise is folded into the 2'-10" figure.
- **Why the basement is 8'-0" even, not 9'-0".** The flat bearing seat lands the EPS deck's soffit on the same plane as the wood bays' mudsill: the deck is 14 3/8" deep and the FLOOR meets it there, so the house sits exactly where it was and the basement simply reads shallower as a result. `Storey.default_ceiling_height` still authors a fictional 9'-0" because nothing has gone back to correct it — `code.R305_ceiling_height` was changed instead to derive the real number.
- **Garage storey datum history.** The `garage` storey landed at -1'-0" "since the lifts" — i.e. after a revision raised the ICF stem's bearing reveal to `GARAGE_STEM_REVEAL` (1'-10") above grade. Before that revision, `D-G-SERVICE`'s framing and the breezeway deck it opened onto were coordinated differently; today the door's threshold is pinned at 0'-0" with the bridge deck rather than following the storey drop the way `D-G-OVERHEAD` does, which is why it needed its own +1'-0" sill and five 6.8" risers inside the garage instead of a curb-free opening.
- **Why the north entry headers stay 3-ply 2x12 KDAT, and why the exterior glulam was refused (owner asked 2026-09-12).** Capacity was never the question: `BM-BW-RE` and `BM-BW-RW` each carry 80 sf of `RF-BW-CANOPY` at 73.7 psf design snow plus 10 dead over a 5.719 ft node-to-node span, and `engineering/roof_beam.py` publishes bending 0.707 (4,787 against 6,766 lb-ft), shear 0.508 (99.2 against 195.2 psi) and live deflection 0.129 (0.0369" against L/240 = 0.286"). A 3-1/2" x 11-7/8" treated glulam would carry that with room to spare. **What decided it is that the glulam has nowhere to be graded.** `roof_beam.py`'s `_SECTION` is `^(?:(\d+)-)?2x(\d+)$` — a built-up sawn section and nothing else — so a `"3.5x11.875"` falls straight to `_incomplete("published design values for the section as sold")` and BOTH records go INCOMPLETE. These are the only two `roof_beam` items in the house, so that is the whole kind. And nothing downstream catches them: `engineering/glulam_beam.py` stopped being a registered kind on 2026-09-11 (the supplier publishes a deck table, so reading the row is a prescriptive act and `structural.deck_beam_span` grades it), and what remains there is deck arithmetic — 40 psf live at `C_D` 1.0, `DECK_TOTAL_LOAD_PSF` 50 — which cannot carry a 73.7 psf drift case even if it were still registered. Retyping would trade a published d/c of 0.71 for a hole in the register, and the engine is the reason rather than a preference. **The ply seam, the one durability argument that would have overridden that, does not reach these two beams.** Both headers ARE the canopy's eave bearing lines: the trusses land on their tops, so each seam sits inside the roof assembly under the deck, 1'-4" inboard of the drip line — `RF-BW-CANOPY`'s own `overhang=ft(1, 4)`. FPInnovations' mass-timber durability guidance is the standing authority on appressed plies and carves out exactly this case: avoid parallel beams appressed against each other creating a capillary to hold water **unless the beams are preservative treated**, and KDAT is. The same document finds top flashing has "extremely limited efficacy", and the IRC commentary to R317.1.5 says outright that capping an exposed glulam with metal is not sufficient — so the cap is not the strong half of the porch's argument either, and its absence here is not a gap. **Note this is NOT the porch's 2026-09-06 refusal repeated.** That one rested on butyl tape plus a formed aluminium cap over a beam in the open. This one rests on being under the roof. Neither argument transfers, and the record has to say so or the next reader will assume one covers both. **Cost confirms rather than drives**: from the house's own rows, `beam:BEAM_GLULAM_TREATED` is $30-41/LF material plus $12-20/LF to set against `beam:BEAM_KDAT`'s $9.67-15.97 plus $3.38-6.47, which is about $325-450 more over these 11.4 LF. The often-quoted "4x the material rate" is nearer 3x on those two rows.
- **Why every wood-on-concrete beam seat is a drained standoff and not a sill gasket (owner asked 2026-09-12).** The standoff was already there at all twelve such seats, so the answer is no change — but the question was worth answering in three parts. **First, which joint is even in question.** `BM-BW-RW` never touches concrete: it bears on 6x6 KDAT posts through `CCQ46SDS2.5` caps, and those posts stand on `ABU66SS` stainless bases. `BM-BW-RE` bears on the cast columns through `CN-BW-STDF-RE`/`-RNE`, an `SS316-SHIM-35` pack holding a 1/2"-1" gap; the `HGAM10` beside it is the tie, never the bearing. **Second, a gasket would be the wrong part.** A closed-cell sill gasket is a capillary break for a plate bolted tight to a slab, where the compression is what makes it work. At an exposed joint with nothing clamping it, it becomes the water-holding layer — the opposite of what is wanted, and the reverse of FPInnovations' own hierarchy, which prefers a drained gap to a membrane. **Third, wicking is the right mechanism to name and not the one that governs here.** Capillary rise in concrete is bounded by evaporation rather than by suction: published equilibrium heights are 100-480 mm and the building-science rule of thumb draws the line at 150 mm above soil. Nothing this part sits on is within reach of that: the north entry's pier tops stand 18 1/2" (470 mm) above grade, its two full-height canopy columns 9'-2 3/4", and the garden's porch columns rise 10'-0 15/16" out of the court floor. What actually wets a beam seat is rain standing on the column top plus end-grain uptake where a beam END lands there — which `BM-BW-RE`'s south end does — and the wash, the drip lip and the drained gap are aimed at that, correctly. **And no IRC provision requires either a barrier or a standoff at this joint**, which the record should state plainly because `library/hardware.py` claimed the opposite until 2026-09-12. R317.1 item (2) needs a foundation wall AND less than 8" to grade. R317.1.2 is embedment, not bearing. R317.1.4 governs wood COLUMNS, and its 1"/6"/8" projections are exceptions that *relieve* the treatment requirement rather than impose a clearance — the `ABU66SS` post base is the one part in this set that citation does fit. A treated beam on a concrete column top satisfies R317 with no barrier and no standoff; the standoff is a durability choice on top of the code, and that is the honest way to write it down. (Minnesota incorporates the 2018 IRC through the 2020 Residential Code; a 2024 MN amendment to R317 could not be sourced and none is asserted.)

## Shell: framing module and envelope

### Every interior partition top got a 3/4" deflection gap and an SDPW (2026-09-19)

The attic's seven partitions resolved **11-7/8" too tall** — `apply_to_roof_wall_tops` rakes a
`ToRoof` wall to the roof **deck** plane, so `W-A-STU-N` topped at 255"→315" where the TJI 230
rafter soffit is 243-3/8"→303-3/8", and the studs and the raked double top plate ran through
the whole rafter. `roof_underside_at` — docstring: *"what a wall below must reach"* — had been
in that module the whole time, read by three checks and wired into no wall top. The other 51
partitions carried the same error by the other route: `extend_walls_to_platform` lifts a wall
to the storey datum, which is the **top** of the joists.

Nothing caught it, and the reason is worth keeping: `checks/structural/interference.py`
clears a plate-against-rafter contact unconditionally as a birdsmouth seat, which on a bearing
wall it is.

The fix is not "tight to the structure" but **3/4" clear of it**, because a partition packed
against a deflecting deck is a prop carrying load it was never detailed for. That 3/4" is the
sleeve on a Simpson **SDPW19600 DEFLECTOR** screw, which restrains the wall laterally and
releases it vertically. 58 partitions, 188 screws. Full reasoning, the product table and the
two open documents: `notes/partition_top_deflection.md`.

Two things decided in passing that are easy to get wrong later:

* **Only the FRAMING top moved.** Cutting the body (`z1_m`) at the joist soffit as well was
  simulated and costs four new FAILs — a 12-5/8" slot in `ST-S2A`'s stair enclosure
  (`code.R312_1_1_stair_open_side`) and three basement risers standing outside their own wet
  wall (`mep.wet_wall_occupancy`). ~220 sf of gypsum is still billed through the joist band on
  the storey lines as a result. That is a design pass, not a resolve fix.
* **The part is the 6" screw and not because 6" reaches.** 4.50" is required and the 5"
  SDPW14500 clears it — but Simpson publish that screw for a single 2x or a built-up plate to
  2-1/4" and the SDPW19600 for the DOUBLE 2x this house frames. A different shank, pilot and
  driver (T-40) followed.

### The shortest stud on `W-A-STU-N` is 1-1/4", and that is a separate finding (2026-09-19)

Dropping the attic plates to the rafter soffit made `integrity.wall_shorter_than_plates` fire
UNKNOWN on `W-A-SN` and `W-A-STU-N` — both read **2-3/8"** against a 4.5" plate stack. Both are
false positives and the members prove it: `_wall_top_elevations` reads the rake at station 0,
and the framing on `W-A-STU-N` starts at station **6"** (its end stud is inset by the tee into
`W-A-W1`) and on `W-A-SN` at 3-3/8". Nothing frames to a negative length at an elevation no
member stands at, so the finding's own justifying docstring was false on that geometry. It now
grades `max(_wall_top_elevations(rw))`; a wall short at *both* ends still fires. Suppressing it
was rejected — `[checks] suppress` is for a debt with a number on it, and this was a wrong
finding hiding a real one.

**The real one, recorded here rather than fixed:** the shortest stud on `W-A-STU-N` really is
**1-1/4"**. That is a MEMBER-level finding, not a wall-level one (`short_post_findings` is the
precedent for the shape), and it will light up on walls this change never touched. ~~Not
done.~~ Closed 2026-09-20 — see below.

### The generator stops making the offcut (2026-09-20)

The four members the entry above deferred (`W-A-SN` `cripple-head-0-02` 2-1/8", `W-A-SN-EAST`
`stud-004` 1-1/4", `W-A-GC-S` `stud-005` 1-3/16", `W-A-STU-N` `stud-000` 1-1/4") are gone
because `resolve/framing/solver.frame_wall` no longer emits them. **No catlin geometry moved.**

* **The disagreement was the bug.** `openings._MIN_CRIPPLE_M` was **1.5"** — one plate — while
  `short_members.MIN_STUD_LINE_IN` was **3"**, the two plate thicknesses a cripple is actually
  nailed between. That is exactly how a 2-1/8" cripple got generated and then flagged. One
  minimum now; `openings` imports it.
* **One choke point, not four.** The gate is `frame_wall`'s `return`, where every vertical that
  frames into a wall already is. A guard per emitter is four rules wearing a disguise, and the
  return also makes index stability free: `child_key` is assigned before the filter, so the
  golden shows **8 key deletions and not one modified key**.
* **The wedge gets nothing, not a tapered block.** `FramedMember` can taper, so a filler was
  available. `W-A-GC-S`'s panel "tapers from 3'-6" at its west end to nothing at the eave"
  (`plan/storeys/attic.py`) — the wedge is intended, and `stud-005`'s top is *exactly*
  `plate-raked-1`'s low end. The sliver is the last 1-3/16" of a triangle already bounded by
  the sole plate below and the raked top plate above; gypsum lands on those two faces. A
  sub-3" tapered block is not a piece a framer cuts, and billing one would repeat the defect
  in a different category. The takeoff is ~5.8" of 2x4 lighter (638 → 634 pcs of 2x4; the
  ordered 4,672 LF does not move) and that is the right answer.
* **Refused, not vanished.** The finding stays as the assertion that the gate holds, and its
  message now says the piece *was refused* — an author whose legitimate sub-3" vertical is
  declined has to learn it was wanted and dropped.
* **The ulp trap.** `W-B-CE`'s three head cripples resolve at **exactly 3.0"** and cleared the
  old `<=` bound by 1.1e-16 m of float luck. Raising the minimum without also making the
  comparison `< min - 1e-9` would have deleted the very cripples this codebase cites as the
  legitimate passing case, and the golden would have blessed it silently.
* **Not covered, deliberately:** corner studs (category `corner`, outside
  `STUD_LINE_CATEGORIES` — catlin's shortest is 11-7/8", so a guard would be dead code) and
  cladding verticals from `furring`/`truss_wall`, which are appended *after* that return.
  Both are the coverage the finding already had; gate-set ≡ finding-set is the rule.

### The girt screw went engineered, and the screw itself was replaced (2026-09-12)

`plans/buildability.md` BLD-01b's first finding was that the crossing screw has thread
engaged in both members with no clamp-up, and that nothing in the house answered it. That
finding was right, and it had been right for eleven days.

**What nobody had written down is the thread length.** `notes/catlin_truss_engineering.md`
§3 hand-worked the withdrawal from NDS §12.2 and stopped there. It never stated how much of
the screw is threaded, never checked whether that thread could clamp anything, never checked
the head, and cited ESR-2236 — which is the report for the SDS, not the SDWS. The real
report is **IAPMO UES ER-192, and its Table 7 gives every SDWS22 a 3" thread whatever the
overall length.**

**The audit's 6-1/2" was wrong, and the right number is 6.0".** The clamped stack is the
girt (1-1/2") and the block (4-1/2") — the members being drawn together. The 1/2" plywood is
nailed to the stud, so it is on the stud's side of the joint; counting it as something the
screw has to clamp is counting the anchor as part of the load. At 6.0" the arithmetic is
unambiguous: an 8" SDWS leaves 5" of plain shank and stands **1" of thread inside the
stack**, which jacks the girt off its blocks instead of pulling it down. No amount of driver
fixes that, and it would have been discovered in the field as "the heads will not pull
down".

**So the screw left.** FastenMaster **TimberLOK 8" (TLOK08), ICC-ES ESR-1078** (reissued
2026-01): 2" thread at every length (Table 1A), so 6" of plain shank spans the 6.0" stack
exactly and the thread starts where the stud does — 1-1/2" of it embedded, above the
report's 1.25" minimum. Its coating is rated for ACQ-D at or below 0.40 pcf (§4.1.7 /
Table 6), which the KDAT girt needs. It is also cheaper, which is a coincidence and not the
reason. Rejected: SDWS221000DB (10" restores the engagement; the owner wants an 8" screw),
Rothoblaas HBS/TBS 8 mm (3-1/8" thread at every length, and ESR-4645 is dry service only),
HECO TOPIX-plus (no US report). **HeadLOK 8" (HLGM8) is the recorded alternate** — same 2"
thread, flat head, 600 lb head pull-through against TimberLOK's 200 — and it is not
specified only because ESR-1078 Table 2 wants 2.0" of embedded thread for it, which needs
the 1/2" ply counted and the report is silent on sheathing. A reviewer willing to count it
should take HeadLOK.

**And the calculation became an item.** `girt_screw/W-A-N1` grades three states — thread
engagement, withdrawal from the stud, head pull-through of the girt — plus NDS §12.1.4.6's
6D penetration as an input check, over all 36 `standoff="block"` walls as one design. Head
pull-through governs at d/c 0.487. It is **register-only**, the `wall_panel` precedent: no
`engineered()` bridge, no `PermitItemSpec`, no permit ratchet, because the screw is a
component of an assembly no prescriptive table reaches and there is no prescriptive check
for an engineered record to answer.

Two choices inside it are worth knowing. **Capacities are read, not derived**: ESR-1078's
tested 170 lb/in and 200 lb come off the girt band's own `FramingSpec`
(`standoff_fastener_*`), because `engineering/` may not import the hardware catalog, and
NDS's `W = 2850 G² D` (95.0 lb/in at G 0.42) is printed only as a cross-check. **C_D is
1.0**, not NDS Table 2.3.2's 1.6 for wind: that factor belongs to the code equation, and
applying it to a tested allowable whose report nobody has read would inflate the capacity by
60% on an assumption. The reviewer is asked to restore it if ESR-1078 §4 permits.

**BLD-01a is not a change.** The panel was already a named Metal Sales product with a named
`open_framing_source`, the twenty INCOMPLETE items were already one draft group item at
bending d/c 0.31, and the cladding screw was already 2". The audit was reading a house that
had moved. (Two of those three have since moved again — see "The metal skin went one gauge,
one colour and one product number", 2026-09-14: the panel is BBD75-1212, the screw is back
to 1", and withdrawal governs.)

### Three requirements left the engineering register without anybody stamping them (2026-09-11)

`haus engineering` listed a garage-door header, the house roof's I-joist rafters and the
three balcony glulams as ENGINEERED. All three were there on the same reasoning: the IRC's
table stops, so an engineer owns it. That reasoning has a hole in it. The IRC is not the
only body that publishes a table, and for all three the member's own maker publishes one —
Weyerhaeuser's header schedule, TJ-4000's horizontal clear spans, Anthony/Canfor's deck
guide. Reading a published row is a document a reviewer opens, which is the same act as
reading IRC Table R602.7(1) and nothing a professional seal adds to. The PBR cladding had
already set the precedent: it stays out of the register on the strength of three published
wall span tables.

So the read moved into the model. `PublishedSpan` carries the source, the row in the
table's own words, the member it is for, the span, and the conditions the row assumes that
this engine does not check — printed on the finding, because a prescriptive PASS whose
conditions nobody stated is a claim rather than a read. Four of its fields are drift
guards: retype the member, change the spacing, grow the carried span, or push the check's
own demand past the row's load basis, and the finding goes UNKNOWN naming the mismatch
instead of printing a PASS off a quotation that has stopped describing the building.

Two house errors came out in the wash and are corrected rather than carried. The **19'-3"**
rafter allowable quoted in five places was an interpolation to this site's 35 psf between
two published rows — exactly the move `snow.py` refuses for its own table, with the comment
that interpolating between rows is not a lookup but a design. The honest read is **18'-4"**,
and the roof passes by 6-1/4" instead of by an imagined 17-1/4". And the rafter check had
been comparing the **sloped** length against a table indexed by the **horizontal** run,
which at 6:12 is 11.8% pessimistic and gets worse as the pitch steepens.

One thing deliberately did not go away. The deck guide's values are dry-use and every
balcony beam stands in weather, so the NDS wet-service arithmetic still runs beside the
published row as an advisory — `engineering/glulam_beam.py` is now a pure module with no
registered kind. And one thing is left open rather than smoothed: TJ-4000's high-end support
note is transcribed two contradictory ways in this house, and since these joists hang off
the ridge rather than bearing on it, ForteWEB owns the last word either way. It is written
on the element's own `condition` string.

The register went 41 items to 36, unfinished 9 to 7. Both permit lines flipped to
BLOCKING in the same commit, so the staged count did not move — which is why
`MAX_NON_BLOCKING_ITEMS` carries a note saying so.


### Board & batten: the product got a name, and the item got a seal (2026-09-11)

The north and south elevations were clad in "24 ga board & batten, 20" net coverage" —
a description, not a product. Its 58 psf allowable was borrowed from a Metal Sales table for
a panel nobody had chosen, its open-girt permission rested on a Western States sentence, and
the limit state that actually governs a concealed panel, withdrawal of the hidden leg's
screws, was recorded as published by nobody. Twenty `wall_panel/*` engineering items sat
INCOMPLETE, and they were the only thing in the register that could never be closed by
work — they were waiting on a document.

Two moves closed it. **The product is now Metal Sales BB75-1111**, 11" coverage, whose own
install guide says the panel is designed for open framing over "Lumber – 1x or thicker" —
which is exactly this wall's 1-1/2" KDAT girt — so the substrate is on-label in the maker's
words and the 58 psf is that product's own number. And **the withdrawal allowable is now
computed** from NDS 2018 §12.2 rather than waited for: `W = 2850 G² D` at the girt's own
G of 0.55, adjusted by C_D 1.6 and C_M 0.7, over the thread penetration left after the
flange and the tapered tip. That is a rational design, and IAPMO UES ER-309 states in as
many words that a design professional may do exactly this. The equation reproduces
ER-309's own published DFL row to within a pound, which is the check that it is being
applied correctly to the row that is not published.

Three things followed. The screw went **1-1/2" → 2"**: not for capacity, which all three
lengths have, but because Metal Sales asks for 1/2" past the inside face of the support and
in a 1-1/2" girt nothing shorter can give it. **That reasoning was withdrawn on 2026-09-14
and the screw is back to the guide's stocked 1"** — see the entry below; leaving this
paragraph standing so the history reads as a correction rather than a silent revert. The
twenty items became **one group item**, `wall_panel/W-A-N1` — one panel, one girt spacing,
one demand is one design, and twenty identical sheets were twenty chances for a reviewer to
stamp nineteen. And the panel count roughly doubled, because 11" is real coverage where 20"
was not, so the labour rate moved to the top of its researched band.

The register went from 60 items with 29 unfinished to 41 with 9. Nothing about the wall
moved; what moved is that a reviewer now has two graded limit states to confirm instead of
an absence to be told about.

### The metal skin went one gauge, one colour and one product number (2026-09-14)

Four owner rules drove this and they are worth stating because they settle every trade-off
below: **~100-year service life; cheapest installed that credibly reaches it; a
high-reflectance white, to bounce daylight into the tree-shaded rear gardens; and the "best
look" — concealed fasteners — on the north and south faces only.**

**The house was specifying a panel it could not buy.** The E/W walls and the garage were
authored as "26 ga PVDF". At Metal Sales, PVDF *is* a 24 ga product — the 24 ga colour guide
is the PVDF palette and the 26 ga guides are MS Colorfast45, which is SMP. So both are now
24 ga, under two new house-local tags, `pbr-panel-24` and `corrugated-panel-24`; the 26 ga
rows stay at 0 SF as the documented revert. A tag reads the gauge, which is why those two had
to move and `board-batten-24` did not. Hail is the secondary argument (Twin Cities corridor,
insurers exclude cosmetic denting, 24 ga dents and oil-cans less) and it should be read as
an appearance-and-claims argument: **gauge has zero effect on corrosion.**

**The colour is PVDF Linen White (81), SRI 89** — SR 0.73 / TE 0.86, the highest in the whole
Metal Sales line, ahead of Snowdrift White's 78 and the 26 ga SMP white's 79. One colour on
every face also neutralises St Paul §63.110's advisory that street-facing sides use materials
similar to the principal facades. Two honest caveats: SRI is NIR-weighted and the garden fill
light wants visible LRV, which Metal Sales does not publish (peer whites run ~74-75); and it
is not marked Low Gloss, and there is no matte white in the palette. The "reflected light
scorches plants" cases are all concave low-e glass — a flat wall cannot focus — so that is a
non-issue.

**The batten panel was the wrong member of its own family.** BB75-1111, named on 2026-09-11,
is the CLIP-fastened panel; BBD75-1212 is the direct-fastened one. The two guides' cover
pages say so, and the wall-base details prove it: BB75's asks for a panel clip and two
fasteners per clip, BBD75's for one panel fastener at the nail strip. **The house's own
withdrawal model has always been one screw per panel per girt — BBD75's detail.** So the
correction makes the existing engineering item true rather than adding to it, and it is
cheaper besides: 12" coverage instead of 11" (~9% fewer panels, laps and screw lines) and
~840 screws with no clips against ~2,000 screws and ~1,000 clips. What it gives up is the
Florida approval (scoped over sheathing, so it never reached this wall) and the clip's
thermal-movement slip, immaterial at an 11.1 ft storey band.

**The 2" screw comes out, and this is the reversal of 2026-09-11 above.** That entry gave
the 2" one leg to stand on — Metal Sales asks that fasteners "extend 1/2" or more past the
inside face of the support" — and the leg does not hold. The girt *is* the support, and
behind it is a vent gap and then ccSPF, so a protruding tip buys no withdrawal, no bearing
and no redundancy. The rule cannot be a wood-engagement criterion either: the same stocked 1"
screw yields **0.034"** of thread on the guide's own 7/16" OSB row against **0.596"** in this
girt, ~18x. And the load table footnotes fasteners and support material out by name — which
is exactly why this is an ENGINEERED record — so IRC R703.1.2's design-analysis path governs
the fastener, and on NDS §12.2 every candidate length passes. The spec is the guide's own
stocked **1"**: d/c 0.334 on an allowable that already carries NDS's 5:1, and one fewer
special length on a PO already custom for the 316 SS / A153-D coating. 1-1/2" is recorded as
the no-cost margin. **2" is affirmatively rejected**: its tip stands 0.476" into a 0.500"
vent gap, 0.024" off the ccSPF, so ~840 tips are one thin girt or one overdrive from the
foam.

**Two consequences that had to be handled rather than discovered.** The governing limit
state **flips to withdrawal** — 0.334 against bending's 0.315, where at 11"/2" it was 0.12
against 0.315 — so `test_bending_governs_and_the_item_is_finished` was false by its own
title and is renamed and inverted rather than loosened. The two states are 6% apart, so a
later coverage or wind change can flip them back with no physical meaning; the note says so.
And the seal fingerprint moves, on the ratio as well as the inputs.

**The one real gap the exercise found is a code-coverage gap, not a capacity one.** IRC
R703.1.2 names three failure modes — "bending rupture of siding, fastener withdrawal and
fastener head pull-through" — and this house graded two. **A third limit state,
`pull_through`, is added**, AISI S100's `Pnov = 1.5 t d'w Fu` on the 24 ga flange with a
0.40" pancake head at A792 Grade 50's 65 ksi: 310.7 lb allowable against 36.5 lb, d/c 0.118.
It passes at 8.5x and it is in the record because the code names it. `BASIS_VERSION` went
2 → 3.

**And the substrate question, which prompted the whole sweep, is CLOSED — by the code, not
by a letter.** An earlier draft treated a CTR summary badge as a blocker. That was wrong.
R703.1.2 asks for a wind-load path by ASTM E330 test or by design analysis and says nothing
about a solid substrate; BBD75-1212 lists an ASTM E 330 Load Test on its own design page; and
the allowable table is indexed on FASTENER SPACING from 2'-0" (the narrowest column) out to
6'-0", so a table built that way is a spanning-between-supports table by construction and a
24" girt sits at its strong end. The badge is a copy artifact: the same icon row reads
`10" & 12" COVERAGE` on a sheet showing one panel at 11", because a single 12/2024 sheet was
split in two and the row copied onto both. No Tech Services letter was needed.

**Two drawing bugs fell out of the scoping, both the same class.** `_BATTEN_PITCH_M` was
0.508 m — **20"**, authored against no named panel and never re-struck when one was named —
so every elevation drew battens at nearly twice their pitch; it is 0.3048 m. And
`_CORRUGATED_LAP_M` was 0.8128 m, **32"**, which is the 7/8" corrugated ROOF coverage where
the WALL is 34-2/3"; it is 0.8805 m. Both drew a line where no joint is. The ui's
`ribHalfWidth` is a fraction of the module, so it was re-struck with the pitch to keep the
drawn cap at 2".

**Recorded and not taken: AEP Span Flex Series 1.2FX20-12d**, which supersedes the Flush
Panel entry in the note's §7.9 and is better than it — a genuine batten profile covered by
IAPMO UES ER-309 Table 7.2 "Over solid substrate or over open framing" at **89 psf ASD** over
"Lumber (DFL) 1" min", which would take `wall_panel/W-A-N1` out of the register as a
`PublishedSpan` at no cost to the appearance. Not taken for three reasons that have nothing
to do with load: no Midwest plant against Metal Sales' Rogers MN, the report **expires
2026-09-30**, and AEP's own guide spec says to avoid contact with treated lumber — every girt
here is KDAT.

**Which is the other thing researched and settled: keep the KDAT girts.** The measured
dataset (USDA FPL GTR-227) is unambiguous that moisture content is the whole mechanism —
"when the wood is dry, embedded metals do not corrode" — and the frightening study (U.S.
Steel TBP 2005.19) ran ACQ-D in a continuously damp test simulating near-contact with
standing water, which is not this vented cavity. MCA's 09/2025 bulletin adds that "if panels
are coated on both sides, a moisture barrier may not be needed"; this panel is coated both
sides. The actions are cheap and none is a girt swap: **read the end tag before ordering**
(micronized → change nothing; soluble CA-C or ACQ → change the order, while it is a phone
call), **upgrade the coil's BACKER coat** — the ~0.5 mil unspecified polyester facing the
treated wood is the highest-leverage 100-year item in the assembly — specify painted-head 316
screws, and do NOT cap the girts with a self-adhered strip, which converts a two-sided drying
ledge into a one-sided one punctured at every screw. Honest against it: nobody publishes a
detail showing treated girts in a vented rainscreen, and no study tests a vented cavity
either way. That is a hole in the literature, not evidence of safety.

**The ranked 100-year limiter list, since that was the owner rule.** (1) the exposed
fasteners' EPDM washers, 15-40 yr — annual look, washer campaign ~yr 30-40, painted heads on
the order; (2) the base-of-wall salt and snow zone, where 18-24" grade clearance and a
separately replaceable bottom band are the answer and `haus check` grades neither;
(3) copper-treated wood contact, above; (4) sealants; (5) paint appearance, recoverable by a
~$1-3/SF Kynar Aquatec field recoat at year 40-50. **Painted Galvalume itself is last** — USS
warrants AZ50 painted at 50 yr and the MCA/ZAC field study projects 60-375. The 316 screw
shank is not on the list at all.

Open, and nothing waits on it: a real Rogers MN quote for BBD75-1212 24 ga PVDF Linen White
(lead time, stocked or coil run, $/SF) — Linen White is a standard no-upcharge colour but the
Rogers stock charts are 29/26 ga SMP, so treat it as a made-to-order coil run. Two questions
to ask while quoting: which BBD75 load table is current, the install guide's 58 psf outward
at 2'-0" or the 07/2026 CTR's 75 (the model uses 58 either way, the conservative half of an
irreconcilable pair), and the CRRC 3-year aged SRI for Linen White, which Metal Sales does
not publish.


- The current CATLIN TRUSS WALL is the third wall stack. It replaced the Swinburne
  truss — a chiral block + plywood tab + KDAT outrigger *on edge* at 16" o.c. — which had
  in turn replaced a sheet WRB + 2" polyiso + 2" EPS + 1/2" furring on 537 eight-inch screws.
- The inner girt tier was deleted, and the reason is not economy. Bands B and C used to
  carry a plain SPF 2x4 flat buried in the foam, with the outer tier's blocks bearing on it
  and a second 5" screw into it. It sat directly on the sheathing, so it gave its own screw
  no thermal break at all, and it cost a 10.9% framing fraction in the first 1-1/2" of the
  insulation to hold up nothing but the tier above it. Removing it was worth +2.5 R.
- The screw-as-sole-load-path is defensible specifically because the block bears the
  cladding's gravity in direct compression on the sheathing, making the screw a pure
  withdrawal element rather than a shear/bearing one — that's what keeps utilisation to
  54%/38% rather than something structural failing outright.
- The build order used to be two lifts: framing/screws in one pass, then foam sprayed in
  two separate lifts around the wall's erection sequence. It is now one 4" lift sprayed
  through the 20-1/2" clear between courses and behind them, after all wood and the whole
  screw pass happen on the flat wall pre-tilt.
- Why the course datum had to be the sills, not the wall base: on a main-storey wall the
  two datums are 13-7/16" apart (`platform.py` extends the wall down over the floor rim
  band), and that mismatch used to leave a field course a half inch off an opening's own
  head or sill course before the datum was corrected.
- The girt-course phase sweep: at the old -3-1/2" phase, the opening rule was head/sill
  mirrored from the current one, and that phase is no longer available — at 24" it opens a
  24.75" bay on nine walls and `structural.girt_course_spacing` fails it. Phase zero is the
  swept winner among phases that keep every bay at or under 24.00": 13 opening edges land
  exactly on a course line, 30 sit in the 7" shadow of one. Full sweep in
  `notes/outie_window_truss_detail.md`.
- Why no window moved when the stack changed: the mount plane is the outermost furring
  layer's outer face, and the 6" stack simply comes out a different way now (a 4-1/2" block
  plus a 1-1/2" girt instead of four 1-1/2" layers) — the outer face didn't move even though
  its makeup did.
- The cladding swap was 1/2" of exposed snap-lock standing seam to 1-1/4" of exposed-fastener
  PBR panel — that 3/4" delta is what pushed `_WALL_OUTBOARD_IN` to 7.25" and dragged
  `roof_trim.py`, `breezeway.py`, the garage wall lines, and exterior electrical with it.
  Only the cladding return depth at a jamb changed with the swap; interior geometry did not,
  because walls align on `face("sheathing-ext")`.
- The garage only moved 3/8" of that same delta, because `params/breezeway.py` was also
  carrying a 3/8" rainscreen furring on the garage face that `GARAGE_WALL_2X6` dropped — a
  correction, not a rounding error.
- Mineral wool was swept from most stud bays by an owner cost review: mineral wool costs 2x
  installed versus fibreglass, reads the same 116 perm-in either way, and published STC
  tables separate assemblies by mass and decoupling, not by which wool sits in the bay. The
  batt itself is worth $4,500-6,300 for 0.9 of the 2.7-point `wall_r` shortfall; the other
  1.8 points were never in the bay to begin with.
- A sibling cladding assembly (rather than the per-wall `layer_materials` override) was the
  obvious first move and was rejected: it would have stripped the oak window stools from
  every window on a board-and-batten wall (`plan/millwork.py` scopes them to
  `("EXT_2X6",)`), minted new `opening_perimeter:` / `wall_roof:` / `wall_foundation:` keys
  and goldens, broken the exact-key star overrides in `plan/transitions.py`, and added a key
  to every table keyed by assembly. `W-S-S1` is `PLANT_EXT_2X6_HUMID` while `W-S-W4` on the
  other cladding line is too — the plant room straddles the split, and the per-wall override
  handles that without forking either assembly.
- Delivered cost of the board-and-batten-on-two-elevations switch: +$2,200 to +$5,600,
  measured line-to-line against an all-PBR baseline.
- A `corner_style_end="4-stud"` override authored on only one incident wall used to never
  take effect, and this was a real bug, not a documentation gap: the exterior loop is a CCW
  chain, so every wall's `end` is the *next* wall's `start`, and `resolve/topology.py` gave
  L-corner ownership to whichever wall *starts* there. A style authored on the wall that only
  ever *butts* the corner could never reach the pack. The fix — `resolve/framing/
  solver.py::frame_model` now resolving a corner's style from BOTH incident walls — is what
  makes an override on either wall take effect.
- The APA/BASC objection to a solid 4-stud corner post is that it is an insulable void with
  nothing in it. It doesn't apply on this house specifically because the primary insulation
  is the continuous exterior closed-cell foam, outboard of the post — the post itself never
  needed a cavity to hold batt in the first place, unlike a conventional insulated-cavity
  wall.
- The retired corner detail was the Larsen/Swinburne corner box (FHB, Jan 2024): two 1/2"
  OSB rips per corner per storey (24 total), one along each wall's own outrigger band,
  meeting at the true building corner to close both outboard faces of the ~5"x5" full-height
  void that band's own 45° mitre left standing open. A girt band has no such void — the
  courses are horizontal and butt at the corner, so each course closes its own band as it
  goes and there is nothing full-height left to cap.
- IRC R703.15's through-foam furring table is not the applicable provision for the girt/
  block crossings: every fastener there is wood-to-wood with continuous lateral support and
  nothing bears on foam, which is the condition that table is written for.
- The board-and-batten appearance's ten registrations, name by name: `BOARD_BATTEN_PROFILE`
  + the `metalPanelProfileForFinish` branch (`ui/src/three/materials.ts`), `FINISH_BASE`
  (`ui/src/nordic/palette.ts`), `_FINISH_BASE` and `_METAL_PANEL_FINISHES`
  (`emit/gltf/palette.py`), `DETAIL_FILL` + `DETAIL_HATCH` (`emit/draw/palette.py`), the
  mirrored `DETAIL_FILL` (`ui/src/components/DetailCanvas.tsx`), and `_BATTEN_PITCH_M` with
  a finish-first branch (`emit/draw/elevation_finish.py`).
- The layout-grid-struck-from-the-corner finding was an audit result, not a change: it was
  already correct and the audit did not touch it. It survived the catlin truss because the
  girts are horizontal, so what phase-locks to the 16" module now is their blocks rather
  than the band itself — the promise (the screw lands on the stud) is the same one as before.

## Bearing lines and floor decks

### The firebox got a pocket, and the pocket got the engine a blind `RoughOpening` (2026-09-20)

Three things were wrong with `EQ-M-FIREPLACE` and one of them caused the other two. It was
**fan-forced**, not infrared — the Amantii BI-30-XTRASLIM's manual names a `MOTOR HEATER 19W`
and warns against covering the *fan outlet*, and the words "infrared" and "quartz" appear
nowhere in it — and the owner wanted radiant warmth. It was **sole-source**, which this
house's own sweep said in as many words: *"EVERY UNIT ON THE MARKET THAT IS 26-32" WIDE AND
≤ 6" DEEP AND HARDWIREABLE IS AN AMANTII."* And its head was a deliberate cut course.

**The 4 1/2" recess was the sole-source constraint and nothing else was.** Depth is what buys
brands in this class — 6"→8" adds one, 8"→10" adds four brands and twelve units, 10"→11 1/2"
adds one more — while brand coverage is FLAT from 29 1/2" to 36" of width. So the change is
almost entirely *behind* the brick, where the material is wood framing: the pocket went to
**11 1/2" off the brick face**, which is the building's hard ceiling (brick + tie gap + gwb +
stud cavity, stopping at the sheathing's inner face). Deeper means moving the panel west off
`W-B-E1`'s pour and onto the joists at 236 plf against a 50 plf limit — refused, and it is
`notes/east_breast_bearing.md`'s lead ⚠. Roughly ten brands accept the pocket now against two
before it, and the infrared tier is among them.

**The premise check, made once and then dropped.** Both fan-forced and infrared units in this
class are capped at 1500 W / ~5,118 Btu/h; every "infrared" unit here still has a blower; and
ordinary glass is opaque above ~3 µm, so the radiant fraction leaves through a louver *below*
the glass at shin height. A quartz tube is 60-75% radiant against 40-60% for a sheathed
element — real, and smaller than the marketing. **The deeper pocket is worth building on
supplier redundancy alone. Infrared is a bonus it happens to unlock.**

Height was then the only free variable, and one value was much better than its neighbours:
**24"**, which puts the head at 48" AFF = **18 courses exactly**, the sill already at 9, the
panel top already at 24, and the spandrel to the mantel at 6. The deliberate cut course
disappears. It was only reachable because of the depth: at 4 1/2" the appliance sat FLUSH and
the brick opening WAS its frame, so ~1" of daylight over a trimless unit had nothing to hide
behind; at 11 1/2" the unit sits BEHIND the aperture and the same difference reads as a shadow
in a four-sided reveal. **An aperture that reveals is more forgiving than one that frames.**

**What it cost the engine: `RoughOpening.depth`.** A blind recess was not authorable — and
`plan/mep_supply.py` records the schema change being considered and declined once already,
for the wall hydrants' 12.5 sq in of over-cut gypsum. A fireplace pocket is a much better
reason: authored as a through hole it would have deleted 4.9 SF of sheathing, ccSPF, girt and
cladding to the east yard, counted as east glazing in `wwr`, billed as a window at
`preferences.window_u` in the block load, and raised an `integrity.reveal_concentric` UNKNOWN.
`depth_from` came with it, because the two real cases open on opposite faces: a firebox pocket
opens into the room, a hydrant bore opens on the yard and stops at its seat inside the cavity.
**The change paid for itself twice** — both hydrants are blind now and the over-cut is closed.

**The one consequence nobody predicted:** a blind bore no longer punches a hole in a wall's
ELEVATION silhouette, because that silhouette is the union of every layer's projection and the
layer behind the recess is whole. That is geometrically right — from the yard the wall really
is solid behind the bore, and what a viewer sees is a recess — but it means the two hydrant
holes reach the south elevation through their own symbols rather than through a void. The
outermost layer is still cut; `test_e11_wall_penetrations` pins both halves.

**The appliance, twice.** The first selection was an Innoflame 28" on one argument — the only
unit in the field with a manual-grade hardwire procedure. The owner looked at it and it is an
ugly appliance. **That argument had already died**: the cavity carries a recessed receptacle
AND a hardwire J-box on the one dedicated circuit (owner's call), so "can it be hardwired"
stops being a selection criterion and looks become one. The unit is a **ClassicFlame
28II042FGL** — infrared quartz, better made, and carrying a GENUINE CSA certification rather
than the word "CSA" in a listing, which closes the biggest plan-review risk in the change. It
is **cord-only and must stay cord-only**: its safety story is the Safer Plug thermal-sensing
plug. Material $1,450-1,650 → $360-460, and the saving is a side effect of no longer being
sole-sourced, not the reason for any of it.

### The fireplace stub became three piers, and `FO-M-FIRE` went with it (2026-09-19)

`W-M-FIRE-STUB` rose from `W-B-E1`'s pour at −13 7/16" through `FS-M-EAST`'s joist zone to the
finished floor. To let it through, `FO-M-FIRE` framed a 47 3/4" × 12 5/8" hole — a 2-ply LVL
header, four full-span 17'-11" trimmer plies, two LUS, two HHUS410 and I-joist web stiffeners.

**The premise all of that rested on was never true.** `notes/east_breast_bearing.md` §4 said
the brick *"cuts them short of that bearing, so no joist can reach its east support"*. The
brick is 3 5/8" thick and stands 2 1/2" clear of a 5 1/2" mudsill: a joist passes *through* it
and reaches its seat intact. The panel never needed a joist-free strip; it needed two holes.

So the stub is three piers — 12 1/8" / 12" / 12 1/8" — and the pockets are real gaps between
them, on joists 006 (y = 96") and 007 (y = 112"), 3/4" clear of each 2 1/2" flange. That is
the same idiom the firebox opening already used one level up: *the gap between elements, not a
subtraction from one*. It is what makes the geometry true — the joists run through open air,
not through a masonry layer no check can see.

Four things were considered and rejected, and the reasons are worth keeping:

- **A `DeckPenetration` element.** Owner: *"not as a DeckPenetration. The items should go
  around joists when possible, and this just leaves a gap in the subfloor."* The engine change
  is a derived cut plus a clearance check, not a new model element.
- **A notch in one wall.** The engine has no `voids` path on a `Wall` short of a `Window` or a
  `Door`, and an invisible notch is exactly the condition that earned a `masonry_slot`
  engineering deferral. Three piers make the deferral unnecessary; the NOTE in
  `engineering/deferred.py` says so, so nobody re-derives it.
- **Steel or a cast ligature over the pockets.** The plinth's own first course spans each 4"
  gap with a foot of bearing either side: 27.6 in-lb on S = 3.06 in³ = **9 psi** against
  ~40 psi allowable flexural tension normal to bed joints, and it arches before it bends.
- **Re-rating the brick $/SF down** to match 19.6 SF. Three piers laid to a framer's as-built
  joist lines is fussier per SF than one 44 1/4" stub, so that would deduct twice.

What it bought, measured off `haus takeoff`: 1.75x11.875 LVL **284 → 204 LF**,
2-1.75x11.875 LVL **16 → 8 LF**, I-joist **2348 → 2388 LF** (the two cut joists run whole
again), LUS **−2**, HHUS410 **−2**, brick **20.4 → 19.6 SF**, plywood-subfloor **3181.8 →
3184.6 SF** — still 100 sheets. And it retired the last Source line in
`notes/east_breast_bearing.md`: *"Joist manufacturer's I-joist framing guide — the document §4
requires and this note does not have."* That deletion is the headline.

The engine side is decision **#78**. `resolve/through_deck.py` derives the sheet cut from the
wall's own footprint plus a 1/2" saw clearance, less every member footprint; nothing enters
`opening_boxes`, so no joist is clipped and no chase is offered to a riser.
`structural.through_deck_clearance` grades the pairs. Two traps cost real time: the predicate
must read FRAMING extents (`base_ref_z_m` / `plate_top_z_m`) — on body extents `W-M-E1`
qualifies and every platform-framed exterior wall subtracts a 6" strip of subfloor along its
run — and the footprint must be *contained* in the deck outline, because a deck outline runs
to the axis of the line it dies into and `W-G-S` overlaps the two breezeway landings by 59 and
285 sq in that way.

Four errata were fixed first, in their own commit, all verified against the model: two joists
were cut and headed, not "three or four"; the opening cut the **subfloor**, not `RM-B-GYM`'s
gypsum (`deck_void_face` reads a mostly-filled chase as no void); `structural.floor_opening_header`
never emitted on it at all; and 15/16" of brick does stand below the gym's ceiling plane.


- `INT_2X6_BRG_PLUMBING` was chosen over bare `INT_2X6_PLUMBING` specifically to keep the
  5 1/2" fiberglass batt the staggered wall's cavity had — the swap doesn't silently strip
  the insulation.
- `BM-S-BATH-E`'s ply count: the demand at this beam is ~600 lb; two plies of
  1.75x11.875 LVL carry it many times over and would satisfy bending alone, but two plies
  is only 3.5" wide, and the 4.77" attic partition standing on the beam would overhang
  0.65" each side. Three plies (5.25") was chosen to match the bearing width, not because
  bending demanded it — it happens to land on the same section as `BM-S-HALL`, one LVL
  depth on the job.
- `SL-M-DECK` is what is left of the old 1,233 SF cast deck. The deck's soffit lands on the
  shared bearing seat, and so does the underside of the gasket under the wood bays' shared
  2x6 mudsill. The seat and depth constants sit in `params/main_deck.py` rather than the
  editable storey file precisely because they are not something a UI edit should be able
  to move.
- The basement's mixed ceiling used to be tuned to one *depth* (12 5/8") rather than one
  *seat*. That depth matched the finished floors but left the I-joists resolving inside the
  top foot of the pour, with nothing between wood and concrete. It was changed to a shared
  flat bearing seat at -13 7/16" instead, giving one plate for studs and joists and no step
  in the forms. `structural.mixed_deck_bearing_seat` was written to hold this.
- The 2 1/16" step between the two gypsum ceiling faces at the `RM-B-GYM` boundary breaks
  down as 1/2" (the EPS deck form's steel rib) + 1 9/16" (the deck being deeper than the
  wood bay). The model states only the 1 9/16" it can derive from geometry — the rib's 1/2"
  belongs to the EPS form, and EPS is never modelled in this engine, so that portion is not
  represented even though the physical step is real.
- The derived finish band (`_BAND_Y`) carried a sheet-vinyl hall band, then briefly a
  solid-oak south bay for part of it. Both were deleted rather than replaced: the hall now
  takes the room's field `lvp`, and `RM-M-BATH1`/`RM-M-LAUNDRY` were retyped onto the same
  plank so `vinyl-sheet` has left this storey entirely; the south bay is that same plank.
- The two mudroom closet doors are `D-M-MECH` (on `W-M-MECH-S`) and `D-M-MUDC` (on
  `W-M-MUDC-N`); both open into the mudroom, which is what settled their tile.
- The mudroom suite (`RM-M-MUDROOM`, `RM-M-MECH`, `RM-M-MUD-CLOSET`) took LVP for a few
  hours on 2026-09-05, before the doorway adjacency to `D-M-MECH`/`D-M-MUDC` was checked
  against the hall. Correcting it to porcelain cost +$298 to +$627 delivered.
- The two flush walking-plane legs run `y=13'` (17.9 lf) and `x=18'` (13.6 lf). The oak bay
  along the `y=13'` leg was tried and withdrawn the same day (2026-09-05). Oak finishes at
  +1 1/2"; against the cap's +15/16" that leg would have needed a 9/16" reducer,
  which could not be designed out because `structural.mixed_deck_bearing_seat` only gives
  the cap 1/16" of lift, not 9/16". The height mismatch was undesirable, so the bay
  reverted to plank: -$1,980 to -$2,751 delivered, and the `oak` price row fell back under
  its sand-and-finish mobilisation minimum. Oak survives only in the two studies, where
  nothing meets a cap.
- Bug (fixed 2026-09-05): the finish zone's outline was deliberately drawn over-extended
  past the room on three sides, on the documented promise that `resolve/rooms.py` clips a
  zone. It clipped the AREA calculation but not the drawn ring, so the living-room floor
  rendered a foot outside the east and south walls at 0 FAIL. The engine fix makes an
  authored zone draw clipped, the way a derived one always did.
- `notes/mixed_deck_movement_joint.md`'s "no fibres" clause for the polished cream mix was
  superseded 2026-09-03: it now runs micro-monofilament PP at ~1.5 lb/cy (`DECK_CAP_MIX`, named
  `POLISHED_MIX` until 2026-09-12).
  Macro fibre and steel remain excluded — the distinction between "no fibres" and "no
  macro/steel fibres" is the whole finding.
- `FS-S-EAST` is unchanged from the old whole-floor `FS-SECOND`; only the west field became
  open-web truss. Both fields were kept at 11 7/8" deliberately, same depth and same
  stiffness class, so the split needs no movement joint and no finish break, unlike the
  basement's concrete/wood boundary.
- The second floor's shared x=18' plate used to be split on the centreline between the
  truss and I-joist fields. That shorted the truss's seat, since an open-web floor truss
  wants 3" of bearing where an I-joist is satisfied with 1¾" — hence the deliberate
  3½"/2" asymmetric split now in `params/second_deck.py`.

## Attic and roof

- **Knee walls to a hot roof.** The attic used to be 5'-0" knee walls at 4:12, from a
  MISREADING of R305 — that every square foot of a sloped-ceiling room needs 5'-0" of
  headroom. Minn. R.1309.0305 R305.1 Exception 1 and IRC R304.1/R304.3 scope both clauses
  to the *required* floor area (70 sf), not the whole room, and R304.3 says floor under
  5'-0" simply doesn't count rather than disqualifying the room.
  `code.R305_ceiling_height` used to grade the whole room; it was fixed in the same pass
  that removed the knee walls. With the knee walls gone the pitch was free to be whatever
  the headroom wanted, and 6:12 is the shallowest standard pitch that carries the rooms.
  - The building got 1'-9 1/2" SHORTER (ridge 32'-0 5/8" → 30'-3"), the envelope lost ~572
    sf of `EXT_2X6` for +89 sf of roof, and six windows came out. Measured, not asserted:
    `haus takeoff --csv` before/after puts the redesign at -$19,400 to -$36,200. The same
    before/after run also moved by three PRICING fixes found in passing and unrelated to
    the attic — an `icf-eps` double-bill removed, and the missing
    `closed-cell-spray-foam:1.0` and `WT-2748`/`WT-2748-T` rows added — netting +$3,100 of
    previously invisible cost. The all-in line-to-line delta between the two CSVs is
    therefore -$17,200 to -$32,300; the attic itself is the bigger number.

- **`RM-A-STUDIO` floor finish history.** The room carried `floor_finish=None` over a
  `plywood-underlayment-sanded` deck until 2026-09-09: a sanded plugged panel is walkable,
  not finished, so it needed a sealer allowance with no BOM row. Sheet vinyl retires both
  — `FS-ATTIC` drops to plain `plywood-subfloor`, the sealer allowance is deleted, and
  ~357 SF joins the house's existing `vinyl-sheet` buy at ~$4-8/SF. Seamless and
  waterproof, which a room with a wet bar wants.

- **R303.1's literal-reading risk, in full.** R303.1 says "the floor area of such rooms"
  and does not cite R304.3; R304.3's own operative words are scoped to R304.1's 70 sf. On
  the literal reading this room owes 8% of its whole 356 sf, is short, and is back on
  Exception 1. The finding prints BOTH areas and the section for exactly that conversation
  — see `_r303_floor_area` in `checks/code/mn_residential/ventilation.py`, which carries
  the argument and its two known limits. `ResolvedRoom.head_limited_area_m2` measures to
  the roof UNDERSIDE (146 sf), which is why it disagrees with `code.R305_ceiling_height`'s
  190 sf off the rafter TOP.

- **Why the ERV hoods left the north gable.** Two passes moved them along the gable trying
  to get the intake off `FO-A-HALL`'s open well, and the gable was never survivable:
  `DU-ERV-EA`'s 18'-0" leg at +23'-0" ran through the rough openings of both north-gable
  windows, 8" above a 22'-0" sill in a 25'-0" head, across 2'-6" of each unit — and
  `CD-A-DATA-NE`, rerouted into the same band, crossed `WIN-A-N2` too. They ended up
  stacked on the west face at the NW chase instead.

- **The 0.4" vs 0.2" misconception on the PLANT run.** `DU-M-ERV-R-PLANT`'s route is
  LONGER, not shorter — 55'-8" against a 47'-5" straight-line estimate (9'-4" of the
  difference is rise, which an eyeballed estimate misses) — and is affordable only because
  the machine's rating point is 0.4" w.g., not the 0.2" several older comments still
  quote. The terminal being HIGH SIDEWALL rather than CEILING never gave up the height
  argument: humid air stratifies, so the extract must sit in the warm wet air at the top
  of the room, and 8'-6" is six inches under the ceiling — the argument was about height,
  not which direction the boot arrives from. Separation from `REG-S-HP-PLANT` improved
  again on 2026-09-04 when that supply moved from x=6'-8" to x=9'-4", giving 9'-2" across
  the 159 sf room.

- **Prior roof stack.** It was a vented batten roof, then a screwed nailbase stack: 1/2"
  taped ZIP → self-adhered deck vapour barrier → 3" + 3" polyiso → 5/8" OSB top deck on
  539 ten-inch SDWH screws → vapour-permeable synthetic underlayment → 1/4" ventilated mat
  → metal. R-55.1 at 19.9" deep, to clear a code minimum of R-49. The flash-and-batt
  replacement is 6.81" (perpendicular) thinner at R-53.2/13.1".
- Cost: -$12,200 to -$24,500 on the construction subtotal, of which $3,400-6,000 is a
  known phantom (roof sheathing is billed twice, in `envelope_layers` and again in
  `sheet_goods`; `also_in_sheet_goods` exists and `cli/prices.py::estimate_costs` never
  reads it). The honest saving is $8,800-18,500.

- **Ridge beam depth history.** The same plumb-cut arithmetic at 4:12 gave 13.10" and put
  the answer at 14" (`2-1.75x14 LVL`); before that the beam reached 11.875"
  (`3-1.75x11.875`), leaving the hanger seat and bottom flange 1.52" past the soffit. A
  ridge sized by bending rather than by the plumb cut would want 5 1/4" wide and the full
  LSSR header nail, rather than the 3 1/2" that takes the short one. **Re-sourced 2026-09-14:
  the short nail needs no ER-280 §3.2.2 penetration reduction** — C-C-2026 p. 178 publishes
  (14) 0.148 x 1-1/2 sloped-only on DF/SP at 1,175 lbf outright, and on a TJI the governing
  number is the joist's end bearing (1,090 lbf, TJ-4000 p. 15) either way.
- The beam is ordered as three 12s rather than one 36' stick: same lineal feet, no offcut
  at 36', and a 106 lb ply instead of a 317 lb one (36' at 8.8 lb/ft/ply — this section's
  own weight, not `notes/ridge_beam_detail.md`'s 7.7 lb/ft/ply, which was struck for the
  retired 14" depth; scale by depth, width is unchanged — a 20' ply at the same rate is
  176 lb). Every piece at any depth this beam has been is a two-framer carry — no ply of
  this beam has ever needed a crane, including the 36' one-piece alternative it avoids.

## Windows and facade

**RO ladder.** 36" is the next rung up from the 27"/30" caps and breaks THREE studs (two on
a bay centre), which is why the 42" `WT-4248` sat on a bay centre until it was retired.

**Width/height family derivations.**

The juliet family (`WIN-A-S-JUL-W`/`-E`) was the house's longest-running off-module
exception. It centred on a stud line at 18" wide; widening to 24" could only go outward —
the 14" bearing pier under the ridge pins the inboard jambs — so each centre landed 3" off
module and `structural.window_framing_module` reported both. What ended the exception was
not a fifth attempt at the width but the grid moving under it: once the exterior assembly
began laying out from the layout line, 16'-0"/20'-0" became stud lines 5" further out, and
the pair fit with no retype. A further widening from 24" to 27" grew each unit 1 1/2" per
side, so the centres did not move at all; the clear bearing pier under `RB-HOUSE`'s south
bearing point closed from 24" to 21" against a 14" requirement — spent slack, not a new
constraint. At 6:12 the rake gives 7'-6 3/4" over the outer jambs, and a 64" unit on the
gable's 2'-8" sill wants 8'-2" — so the pair retyped to the width-identical WT-2754 (WT-2764
stayed catalog-only).

`WT-2748`'s sill/head datums were claimed as 2'-6"/6'-6" in this document until
**2026-09-06**. Commit `c2ed5b9d` ("Close the sunken garden's structural loop") moved all
three east sills 2'-6"→2'-8" in one silent hunk of a retaining-wall change, and every
comment quoting the old pair went stale at once. The corrected 6'-8" head — the house's own
door-head line — is a better fact than the one it replaced, not merely a correction.

**What ONE GRID PER FACADE retired.** Unifying the grid dissolved five separate defects that
had all been the same problem in different costumes: node moves made purely to buy phase
(`N-A-V1` to 22'-8" for the south gable, four more in the E/W pass); the "spent" 31'-4" west
column; the east knee band's 4" miss; the north gable's asymmetry; and the juliet pair's
accepted 3" off-module exception. All five dissolved when the grid was unified, at a cost of
20 windows moving 3"–8". The interior centreline used to run three storeys on three
different phases, each of its twelve segments restarting the module at its own start node,
before it opted into `layout_origin="line"`.

**Columns.**

The west face's four lower stations (5'-4", 10'-8", 20'-0", 24'-8") shifted 4" together
when the face re-hung on the house grid.

The west face's fifth column (31'-4") was recovered after having been spent: the second
storey's mechanical chase took its south corners 3 1/8" south so its face lands on
`FX-S-BATH1-SH`'s apron line; `N-S-CH3` moved with them; and `W-S-W1`'s grid re-phased out
from under `WIN-S-BATH-W`, which rode south to the bay centre that move created. With one
grid per line there is no per-segment phase left for a node move to disturb, so the window
returned to 31'-4" under `WIN-M-MUD` and the chase kept its 3 1/8". The 10'-8" suite header
used to cross the top ladder-backing rung at `W-S-W3`'s tee (the solver had omitted that one
nonstructural rung); the 4" the window moved took the header off it, and the backing is
complete again.

The north face used to carry a column at x=29'-4" (`WIN-M-KITCH`/`WIN-S-HALL-N`, moved there
from x=28'-0" to bring `WIN-M-KITCH` onto `FURN-M-KIT-SINKBASE` below). It was a
three-storey column until the 6:12 rake pulled `WIN-A-N2` off 29'-4" and inboard to the
gable, leaving a two-storey stack. On **2026-09-06** `WIN-S-HALL-N` moved west to 24'-0" and
the stack went with it, trading that column of two for the rectangle of four now described
in keep5.md — a precedent, not a general rule.

The face got a column back the same day, at the other end, for a different reason:
`WIN-S-BED3-N` was built to complete the north-east corner pair with `WIN-M-KITCH-N`/
`WIN-M-KIT-E` below (each unit 2'-0" off the corner). It also took `RM-S-BED3` off R303.1
Exception 1 (12.2 sf glazed/6.1 sf openable against 10.32 sf required) — a shortfall the
withdrawn 23'-4" unit below had also fixed and the moves had given back. Where a shortfall
and a composition want the same window, take both.

**The window built and withdrawn (2026-09-06).** A fourth window, also initially tagged
`WIN-S-BED3-N`, was built as a WT-1436 at x=23'-4" to fill the north gable's lower-east
corner, and withdrawn the same day in favor of the moves above — 23'-4" was the only station
the module and node `N-S-B5` allowed, 8" off the ideal and aligned with no column. Its one
lasting mark: `FURN-S-BED3-WARD` and `FURN-S-DESK3` swapped slots to clear the north wall in
`placeables.py`, and the swap is still needed today, because the wardrobe stood over x
22'-1.5"..24'-1.5" and `WIN-S-HALL-N`'s RO is 22'-10 1/2"..25'-1 1/2". The desk that took
its slot has a 30" top, which the 2026-09-10 sill drop put 2 1/2" UNDER — a desk under a
window, the way the Study 2 table sits under `WIN-S-STUDY1`, and ungraded either way. The
tag was reused within
hours for the WT-1424 at x=34'-0" that stands now — a different wall of the same room, a
different argument entirely.

**Rows.**

The east second storey used to run a perfect 9'-0" beat sitting 10" north of the centreline
(5'-4" of wall south, 3'-8" north). Centring it first took `N-S-E2` to 17'-8" and `N-S-E3`
to 26'-8" to buy phase, and the bedroom bays became 8'-8"/9'-0"/9'-4" to pay for it —
shrinking BED1 (whose R303.1 margin is 0.05 sf) and growing BED3 (which has two windows).
Those node positions are now incidental (the grid no longer depends on them), but the room
sizes they set are real and still govern. The inner pair then moved 4" outward onto the
unified grid, giving the row the even 9'-4" beat, three times over, described in keep5.md.

`WIN-M-LIV-E2` moved 12'-0" → 13'-4" on **2026-08-27** (one stud line north, to stack under
`WIN-S-BED1`); this passage said 12'-0" until **2026-09-06**. `N-M-E1` and `W-M-E2` were
removed when the wall was merged for `WIN-M-EAST-MID`, and `WIN-M-DIN-E2` (the window the
blank stretch was originally measured north of) was retired with them.

**2026-09-06:** the pier between `WIN-M-LIV-E1` and `WIN-M-LIV-E2` became the fireplace — an
eight-unit BESTA relayout (three south, five north of it) with the seating turned onto it.

**2026-09-11, the sill went up and came back down the same day.** The morning's decision
raised the firebox sill 24" → 32" AFF; the owner looked at it and reversed it by evening.
The 32" case was sound and is worth keeping on the record, because it will be made again:
`plans/pattern_language_review.md` C9 wanted fire at seated eye level, the retired SE-corner
unit's top sat at 28" (a foot under it, and unraisable there — `WIN-M-LIV-E1`'s rough
opening was directly over it), 32" bought a 14" rise onto that old top, it landed on course
12 exactly, and it put the firebox sill on the east window row's own 2'-8" line so one datum
served four openings. What beat it was not an error in any of that. At 32" the opening reads
as a picture hung on a wall rather than as a hearth; 32" of blank plinth under a 20 5/8" hole
makes the 45 1/2" panel top-heavy; and the seated sightline the rise was bought for is met
from the armchairs at 5'-2" regardless. **A preference overruled a design argument.** The
reversal costs the shared sill line with `WIN-M-LIV-E1`/`-E2` and drops the flame centre from
42 3/16" to 34 3/16" AFF, ~12" below a seated eye instead of ~5".

Two things held it flat. The 8" the plinth lost went into `W-M-FIRE-HEAD` (11 3/8" → 19 3/8"),
not into the panel, so the top stayed at 64 15/16" absolute — mantel still on the brick, the
hand-measured 0" BESTA gaps still true, brick still 20.4 SF. And the opening HEIGHT never
moved, so the head stayed a cut course (19.7 modular courses at the old sill, 16.7 at the
new) and the 24" sill is 9 courses exactly, as 32" was 12.

**The lintel stopped being prose.** It had been named in `plan/storeys/main.py`,
`plan/electrical.py` and `houses/catlin/CLAUDE.md` and modelled in none of them. There is no
lintel element type in the engine and `FIREPLACE_BRICK_WYTHE` carries no `MasonrySpec`, so
the schema choice was a `Beam` or a priced allowance. The `Beam` went in — `BM-M-FIRE-LINTEL`,
`N-M-FIRE-JS-S`→`N-M-FIRE-JN-N` so the two jamb piers' existing `open_end` nodes give it 8"
of bearing each end with nothing invented. Two things about it are compromises rather than
facts: `size="3.5x3.5"` is the L3-1/2 x 3-1/2 x 1/4 angle's BOUNDING BOX, because
`resolve/framing/profiles.cross_section` parses that spelling and silently falls to a 1.5x5.5
rectangle for `"L3-1/2x3-1/2x1/4"` or anything with a trailing word; and a `Beam` bills
through its `assembly` as a cubic-yard `beam · <assembly>` row, which is the wrong shape for
an angle, so this one carries no assembly, bills $0, and wants an `[allowances]` lump instead.
The real steel is named in `engineering_note` (a `Beam` has no `source` field).

**The `Mount.elevation` datum was settled by reading the resolver, not the comments.**
`plan/placeables.py`'s mantel note says the datum is the framing floor and `plan/electrical.py`
described `EQ-M-FIREPLACE`'s `inch(32)` as 32" AFF; both could not be right.
`resolve/placeables.py::_floor_elevation` returns `room_finished_floor_elevation(...)` and
`resolved_mount_elevation` adds the mount to it — **the FINISHED floor** — with the structural
plane kept only for what a ceiling mount hangs from. The resolved model agreed: the fireplace
came out at 32 15/16" absolute for an authored 32". So the equipment was right and the mantel
comment is stale, and the mantel, authored `inch(64.9375)` on the old reading, resolves to
65 7/8" absolute and **would float 15/16" off the brick it is supposed to cap, at 0 FAIL**.
Fixed the same day in a separate pass, since `plan/placeables.py` was not this change's to
edit: it authors `inch(64)` now, and the resolved model puts the mantel base and
`W-M-FIRE-HEAD`'s top at the same 1.6494125 m. The lesson worth keeping is that the bug was
INVISIBLE to every gate — a placeable is graded against clearance zones and doors, never
against the wall it is mounted on, so a stale datum comment is the only thing that was ever
wrong and the only thing that could have caught it.

Before the fireplace was a real modelled void, `SB-M-FIRE-MANTEL` was a `ResolvedShelfBank`
with no position, and no emitter reads `model.shelf_banks` — so it was a cut list and
nothing else, absent from the 3D and from every clearance check. It was replaced by the
wall-mounted placeable (`FURN-M-FIRE-MANTEL`/`FT-MANTEL-WALNUT-46`) described in keep5.md.

The old note claiming `FO-M-FIRE`'s span "crosses IRC R502.10's 4'-0" line" was an erratum
twice over: `haus check` grades floor-opening headers at EIGHT feet, and R502.10.1 is a
sawn-lumber rule the engine now gates on a sawn-joist profile — the I-joist opening was
never on that line to begin with.

The knee band deletion removed ~572 sf of `EXT_2X6`, along with four window units, four
bucks, four flashings, and eight jamb returns.

**Head lines.** `WIN-S-BED3`'s own source note in `second.py` claimed a 3'-0" head until
**2026-09-06**; the authored value was `ft(4)` (4'-0") the whole time. Correcting the prose
moved nothing.

**The west face's 14" family left the 6'-0" head line for the 4'-6" centre line
(2026-09-12, owner's call on the facade).** Four leaves — `WIN-M-BATH1-W`, `WIN-M-MUD`,
`WIN-S-VANITY-W`, `WIN-S-BATH-W`, every WT-1424 on the west face — went from a 4'-0" sill to
**3'-6"**. The arithmetic is exact, which is why it is a rule and not a nudge: a 27" unit
spans 36"..72" off its 3'-0" sill and is centred at **54"**; a 24"-tall unit at a 3'-6" sill
spans 42"..66" and is centred at **54"** as well. At the old 4'-0" sill the small units
shared the 6'-0" head and sat 6" high of the family's centre, so each one carried a deep
blank sill below it and the face read as two unrelated bands.

The trade is a real one and is worth stating: the house gains a composed facade and loses
the single head datum that made every west-face head one dimension. Three tests encoded the
old datum and were re-swept rather than suppressed — the facade-column test now asserts
6'-0" for the 27" units and the 4'-6" centre for the 14" units, so the new rule is pinned as
tightly as the one it replaced. Two tripwire counts moved with the sills and neither is a
design fact: girt-course exact edge hits fell **12 → 8** (a 3'-6" sill and a 5'-6" head land
between courses where 4'-0"/6'-0" landed on them) and the truss-block count rose
**1127 → 1131** (four openings' jamb stations re-packed). `structural.girt_course_spacing`
still passes and no course moved — the offset is still zero.

**It was committed by accident, in `92e7495a` ("concrete column refinement"), with no prose
and no test update**, and surfaced as three failing tests a commit later. The change itself
is kept; only its record was missing. The lesson is the one this log already carries about
silent drift: four windows moved 6" and every comment beside them still argued for the sill
they had left.

**Gables.**

The north gable's history: `WIN-A-N1` moved 7'-4"→8'-0", mirroring `WIN-A-N2` at 28'-0"
about x=18', then to 6'-8"/29'-4" when the three-storey column moved to bring `WIN-M-KITCH`
onto the sink below (`WIN-A-N1` moved with it to hold the mirror). The rake then moved it
again: a 36" unit on the gable's 2'-0" sill puts the head at 5'-0", needing 2×(60+2)=124"
of clearance to the outer jamb, and 6'-8" gives only 65" — landing the pair at
12'-0"/24'-0". It
went one bay further in to 13'-4"/22'-8" on **2026-09-03** and came back out to
12'-0"/24'-0" on **2026-09-06**, where it now sits.

**The return outboard is what squares the facade:** with `WIN-S-STAIR-N` moved to 12'-0" and
`WIN-S-HALL-N` in from 29'-4" to 24'-0", both gable units stack exactly on a second-storey
partner and the north face reads as one rectangle of four.

The 145" clearance once quoted for the rake-binding note was the slack the inboard
13'-4"/22'-8" pair had; at the current 12'-0"/24'-0" station the true figure is 130 1/2"
against 124" needed. `WIN-A-N1` was rehosted from `W-A-N2` to `W-A-N2B` on an earlier move.

**The rectangle narrowed to one width (2026-09-10).** All four north units were WT-3036, and
30x36 is 1:1.2 — square enough to read as a mistake in `elev_north.png`. The gable pair took
**WT-2736** and the second-storey pair **WT-2748** at a **3'-4" sill**, so the facade is
now two stacks of one 27" rough opening, 48" tall below and 36" above. Nothing moved: the
centres stay on 12'-0"/24'-0", but every offset had to grow 1 1/2" to keep them there,
because `from_node` resolves to the opening's near JAMB and not its centre
(`resolve/pipeline.py`'s `_opening_center`). That is the trap to know before any retype on
this facade — a pure type swap silently walks the whole rectangle sideways.

Three things settled the numbers. The attic could not grow taller with the pair below: a 48"
unit there needs 148" of run against 130 1/2" available, and buying the height off the sill
instead puts it under R312.2's 24".

The second-storey sill took two passes and the second one is the interesting half. The
girt rule asks for a head on a 24" multiple or a sill 3-1/2" above one, and the first pass
took the sill half at 2'-3 1/2". It was an exact hit and it sat visibly too low on the
facade. Going back to it turned up the real constraint: **a 48"-tall unit on a 24" module
cannot take either half cleanly.** The head half wants a 24" or 48" sill; the sill half
wants 27-1/2" or 51-1/2"; the two sets never intersect, so whichever edge lands on a
course, the other edge lands within 7" of one and casts a sliver. Both 2'-3 1/2" and 4'-0"
score 14 exact against 33 slivers — one board saved, one board wasted, net nothing.

So the pair was placed clear of every course rather than on one. The clear band is
2'-10 1/2" to 3'-5", and **3'-4"** is its top even inch: head at 88" with 8" to the 96"
course, sill datum at 36-1/2" with 11-1/2" to the 48" course. Four sliver edges became
zero, and the whole-house count went 33 → 31 at 12 exact hits. The lesson worth keeping is
that the NEW-OPENING RULE is a means, not the end — the end is no redundant board, and
when a unit's height puts the rule's two halves out of reach of each other, the gap
between courses is where it belongs. 3'-4" also keeps a full 16" over R312.2's trigger,
which is real margin rather than paper margin: `sill_m` is measured off the SUBFLOOR, so
an authored 24" would be 23 1/16" to an inspector's tape.

The narrowing paid out at the gable as well. Both jambs came inboard 1 1/2", so the rake
margin went 5" → 6 1/2", the radon riser's clearance to `WIN-A-N1` 9 5/8" → 11 1/8", and the
PV junction box's 5" → 6 1/2". None of those three is graded; a later rewidening spends all
of them back at once.

**The north second storey was never on the 6'-0" head line.** `CLAUDE.md` and `second.py`
both said it was until 2026-09-10. Commit `5487fd79` had raised both sills ft(3) → ft(3, 6)
in a silent hunk of another change, putting the head at 6'-6" against `WIN-S-BED3-N`'s
6'-0", and no prose followed. The retype leaves them at 7'-4", the highest heads on the
storey. The face is a row of three on one rectangle with a 14" corner unit outboard, and it
is now documented as one.

This document claimed the stair window sat at 12'-8" and argued an 8" miss, until
**2026-09-06**; that was never true — the authored offset always resolved to 13'-4", and
correcting the prose moved nothing. The move to 12'-0" is the one real change.

The south gable used to carry SIX openings; the corner pair (`WIN-A-S1`/`S4` at
3'-4"/32'-8") has since been deleted — 21 1/2" of roof over the floor there. The flankers
moved inward and shortened (WT-1448→WT-1436); the juliets underwent a width-identical
retype (WT-2764→WT-2754), so their centres, `from_node` offsets, and the 21" clear pier
were all untouched by that move.

Mirroring the east half of the south gable once required moving `N-A-V1` from 22'-4" to
22'-8", because `W-A-S4`'s bay centres were 4" out of phase with a mirror of `W-A-S1`'s;
that node no longer sets any grid, so the move is now only a wall-segmentation choice.

**WT-1424** used to also serve the 5' knee walls, where its 2'-0" height was the only one
that cleared the plate; those walls are 1 1/2" rafter plates now and carry no glazing at
all.

**East bearing wall (BED1/BED2) — the 30" exception and its reversal.**
`WIN-S-BED1`/`BED2` used to carry a 30" RO in a bearing wall, with `max_window_ro_bearing_in`
set to 30 to allow it. The reason given at the time: R303.1 wants 9.95 sf of glazing, a
27x36 gives only 6.75 sf, and "27" cannot reach it at any height that fits under the 9'-0"
plate."

That last clause was never checked, and it was false: R303.1 binds on area (width x
height), so the width cap only binds if height has run out — and it had not. 27x54 gives
10.125 sf / 5.063 sf openable, clearing BED1 (119.66 sf, needing 9.573/4.786) by +0.55/+0.28
and BED2 (124.32 sf, needing 9.945/4.973 — the binding room) by +0.18/+0.09 — wider margins
than the 30x48 it replaced (+0.43/+0.21 and +0.055/+0.027). On the shared 3'-0" sill the head
lands at 7'-6", leaving 18" to the 9'-0" top of wall; the built framing puts a 2-2x8 header
at 7'-6"→8'-1¼" under a plate whose underside is 8'-9", leaving 7¾" of cripple — there was
never a plate conflict to design around.

Both rooms are now `WT-2754`/`WT-2754-T`, and the preference reverted to 27" for the east
bearing wall, matching every other bearing wall in the house.

## Ventilation, ducts and soffits

### The ERV hoods went to the north wall, and the chase was the wrong question (2026-09-15)

`DU-ERV-OA` had been stuck at 6" for weeks. `notes/erv_static_budget.md` §7 priced the 8"
upsize Broan's manual asks for at ~4.5 cfm delivered against a code margin of 0.7, and the
answer was always "blocked on the chase": at the riser's station an 8" envelope overran the
shaft's east face by an inch, and a four-step proof showed no ordering of four risers packed
out of it. That proof was correct and it answered the wrong question.

`DU-ERV-OA` runs main to basement only. It is the one leg in this system that never needed a
continuous basement-to-attic shaft, and it was in the shaft **solely because its hood was on
the WEST facade with the shaft in between**. Moving the hood to the north wall of `RM-M-MECH`
put the riser in the open closet at x=3'-4", where 8" is not tight. The upsize followed for
nothing, took the term 0.1318 -> 0.0315, and handed the governing side back to extract.
`DU-ERV-EA` went the same way and lost its jog: riser and hood now share one station.

**What the measurement found on the way there is the more useful half.** The original scan
was duct-against-duct and reported four interpenetrations in the chase. Re-run against pipes
as well, the two outdoor legs carried **twelve** — including `DU-ERV-EA`'s basement leg
running *inside* `PR-B-KITCH-DRAIN` for 4'-3", and its riser skewered at five separate
elevations by the six-vent bundle that crosses the chase westward at y=34'-6". None of that
had ever been graded, because nothing in this engine pairs a duct against a pipe. Both runs
are now clear of every duct and pipe in the house and of each other; the NW column's total
fell 45 -> 37, and the 37 that remain are plumbing's, not the ERV's.

**Three things this turned up that outlive it.** `ResolvedConduit` carries no per-vertex
elevations, only a start and an end, so the chase's nine conduits resolve as two-point
schematics — `CD-B-ATTIC-RISER` "rises" 24 ft while travelling 5'-6" horizontally. That, and
not the schematic radial plane, is what actually blocks `mep.duct_interference`. `haus route
--run` refuses every duct, though `routing/trades/duct.py` exists and the repo guide
advertises the flag. And `FS-M-MECH` had carried four risers through its joist field with no
floor opening declared at all; `FO-M-ERV-OA` and `FO-M-ERV-EA` are the first two drawn, and
the vents, the radon riser and the conduits still are not.

**ERV outdoor hoods moved off the north gable.** They used to sit at 8'/28' on the north
gable, and the argument for the gable did not survive measurement. It said "RM-M-MECH is
5'-11" x 2'-7", so no pair of hoods near the shaft can make ten feet" — the room is really
5'-3" x 1'-11" (`resolve/rooms.py` polygonizes from wall AXES and insets only by the lining,
so an exterior-wall room reads 6" past its own interior face), and the conclusion was only
ever true of a HORIZONTAL pair. It also said the main storey was too low at "20"-34" above
grade" — that is the 13 7/16" RIM BAND, not the 10'-0" wall; the interior band is
2'-10"..11'-10" above grade. Moving them to the stacked west-face siting saved 52.6 LF of R-8
wrapped 6" duct (`DU-ERV-OA` 32.3'→8.3', `DU-ERV-EA` 49.6'→21.0'), because both used to climb
24'-6" to the attic; it also empties the chase above the second storey, where four ducts used
to run and now two do. IRC M1506.3 independently waives the ten-foot rule "where the exhaust
opening is located not less than 3 feet above the air intake opening" — the engine does not
implement that exception and does not need to, but it is the second, independent reason the
exhaust must stay the upper hood. The gable mirror about x=18'-0" no longer applies to the
hoods (a facade rule for a gable, and they are not on one); `test_catlin_erv.py` now pins the
stack order instead.

**The soffit-occupancy check found two real errors on its first run, both in
`EQ-S-HP1-AH`.** It was resolving at the 9'-0" storey ceiling — a CEILING mount with no
elevation fell back to `default_ceiling_height`, which is now soffit-aware — and its case
resolved 43" across the hall instead of 21" along it, because `EquipmentType.footprint` wins
over the element's own and `EQ-T-GREE-SLIM24` stated (43, 21). It needed `rotation=deg(90)`.

**And then the case itself turned out to be fiction.** `EQ-T-GREE-SLIM24` was an explicit
"REPRESENTATIVE PLACEHOLDER … TODO verify datasheet"; the only real 43 3/8" cabinet matching
it was Gree's discontinued low-static `DUCT24HP230V1AD`, which tops out at 589 cfm against
the 750 cfm this whole duct system is sized to. So the packing this check so carefully graded
was a fit for a machine that does not exist, and the 4 7/8" slivers it left either side were
what kept `DU-S-HP-SOUTH` riserless for a fortnight. The real `EQ-T-GREE-DUC24`
(44 1/2 x 29 11/16 x 11 13/16, 0.8" ESP) needed a new box, `SF-S-HP1` in `RM-S-STUDY2`'s
ceiling; it needed no `rotation`, because the type now stated the cabinet the way it was
installed.

**And the verified type was itself wrong — `EQ-T-GREE-FLEXX-ULTRA-24-AH`/`-OD` replaced it.**
The DUC24/VIR24 record's own `source=` claimed 577-1030 cfm; the pair's real ceiling is 736 at
0.8" w.c., under the 750 this duct system is sized to. Its 13,500 Btu/h at design was an
interpolation (the read value is 14,606) and either way sat under the zone's 15,410 Btu/h
(15,164 when this entry was written; re-measured after the 2026-09-18 block-load correction,
which did not change this entry's conclusion)
block load — `mep.heating_capacity` passed only by crediting a strip heater the DUC24 has no
aux-heat terminal to interlock with. Gree's FLEXX Ultra answers all three: 760 cfm at 1.0"
w.c., 21,000 Btu/h read at -15 F (136% of load, unaided), 24 VAC control with a factory heat
kit, HSPF2 9.0 → 10.0, and ENERGY STAR Cold Climate (AHRI 215213329) where the Vireo is not.
**The 21,000 at -15 F is itself unverified to a column** (`# TODO verify datasheet`): the AHRI
certificate number is not a capacity table, no published capacity at 5 F or -13 F was found,
and "reliable heating to -22 F" is an operating range rather than a rating. Given the
paragraph above, that is exactly the error this entry is about — resolve it before the
heat-loss calculation is called closed.
It costs depth — 18 1/8" against 11 13/16" — which is what took `SF-S-HP1` from a 17" drop to
21" and its underside to 7'-3". The generalisation of the generalisation: a verified datasheet
number is only as good as the column it was read from, and three of these were read from the
wrong one.

**`SF-S-HP1` moved to `RM-S-NCLOSET`'s ceiling on 2026-09-04, and the whole system reversed
with it.** The air handler is at the north end of the storey now, the trunk runs SOUTH out of
it, `DU-S-HP-SOUTH-RISE` is a collinear reducer at the trunk's south cap instead of a dogleg
round the machine, and `EQ-M-HP1-OD` crossed to the north face on its own pad
(`params/hp1_north_pad.py`).

The passage this replaces described the box as it stood in `RM-S-STUDY2`'s ceiling, arguing
for a seam that no longer binds anything: the seam is now at y=27'-8" for a different reason
(abutting `SF-S-DUCT`'s north end), and the 35"-wide box, topping out at x=21'-5 1/2", never
reaches the old wall face 14" further north.

**The return, `EQ-S-ERV-MIX`, was a mixing box for a few hours, and the register lapped three
things at once before the plenum fix.** A 30 x 16 ceiling grille split its 336 in² face
three ways: 240 in² into `DU-S-HP-RET`, 120 in² into the box, and 120 in² into bare soffit
cavity. `mep.register_duct_match` grades the pair in PLAN only and a boot is unmodelled by
convention here, so it passed anyway. The three plenum dimensions are each a clearance: 12" is
the east lane less the 2" `HANGER_GAP_M` off `DU-S-HP-SUP`; 29 1/2" stops the plenum clear of
the cabinet's south face (overlap it ALONG by an inch and the pair grades ACROSS, where the
gap is 7/8"); 18" fills the 18 1/4" cavity.

**The wall-grille alternative on `W-S-C4B` was investigated in full before being rejected.**
Its studs resolve at y 369 / 384 / 400 / 416 / 424 5/8 with a double top plate at 225..228, so
the one bay overlapping the plenum band (400 3/4..415 1/4) is blocked by the cabinet below
y=408, leaving 7 1/4" of clear bay. Cutting a stud puts that plate over a ~31" span at
~1,600 plf: f ≈ 1,940 psi against Fb ≈ 1,310. Moving the air handler does not help — the wall
is the problem, not the cabinet.

**The trade behind the 7'-3" ceilings**, made with open eyes: `RM-S-NCLOSET` and about 7'-9"
of the north hall drop to 7'-3", and `RM-S-STUDY2` gets ~29 sf back to full height with the
remainder 7" higher.

**The air-side review that followed (2026-09-04) found three more things, and two of them
nothing grades.** The balance itself was sound — 750 leaves the machine and
80+80+80+50+35+175+250 comes off it, exactly — but:
- Four supply grilles (`REG-S-HP-BED1/2/3`, `REG-S-HP-STAIR`) were authored at 8'-0" on the
  strength of a stale comment reading "9'-0" ceiling less the 12" drop". `SF-S-DUCT` actually
  drops 14" and stops at x=21'-5 1/2"; the grilles sit at 22'-6", past the box, and
  `RM-S-BED1/2/3` carry no soffit at all (0.0 sf) — they finish at 8'-11 1/2".
- `REG-S-HP-STAIR` was a short circuit: 50 cfm blown straight down 6'-2" from a 650 cfm
  return in the same room, with the return the *lower* of the two (7'-3" against 8'-0"). Fixed
  as a sidewall grille throwing west across 12'-7" of landing; its 97 1/8" elevation is
  derived from the trunk centreline at 100 1/8" less half a 6" face, not chosen.
- `REG-A-HP-STUDY`'s 100 cfm floor boot at (26'-0", 3'-4") stood inside
  `FURN-A-STUDY-CHAIR2` (x 25'-8"..27'-4", y 3'-3"..5'-1"). Moved to 25'-0", which clears both
  chairs and shortens `DU-S-HP-SOUTH` by a foot, though it is still under the legged 36" table
  — every station on that bay line from x 21'-0" to 27'-3" is under furniture.
- `DU-S-HP-SOUTH` came in at both ends, 19'-4" to 15'-8", the west by most: 6'-8" → 9'-4".
  The old west station's "centred between the two south windows" argument counted only two of
  the room's three (x 4'-0" / 9'-4" / 14'-8"); 9'-4" is the centroid of all three, so one
  terminal washes the whole south wall.
- The riser cannot shortcut up through the joists, which would have given `RM-S-STUDY2` back
  7 ft of 14" box — the obvious saving that doesn't work. 250 cfm wants ~51 in² for Manual
  D's 700 fpm, and the largest hole entertained that close to a bearing wall is ~6 1/2" round
  = 1,090 fpm.

**The return path arithmetic**, in full: at a conventional 3/4" undercut a 30" leaf passes
42 cfm at the 3 Pa ACCA/ASHRAE ceiling, so `RM-S-BED1/2/3` sit at 11 Pa and `RM-A-STUDY` at
17 Pa without the wider undercuts specified. Full arithmetic and the acoustic/carpet costs of
those undercuts: `notes/system1_return_path.md`.

**`SF-S-HP1` ran under `ST-S2A`'s flight in its old `RM-S-STUDY2` siting, and that was allowed
but bounded.** The stair climbs west along `W-S-SS2`, so over the box's north-east corner its
underside sat at or above the box's own 7'-3" face and the two finished as one plane. The
seam was placed at y=7'-6" rather than at the wall face 14" further north specifically to
avoid lapping the stringer ledger.

**`W-M-HS4` pocket door — why the cavity crossing a node is legal.** Wall segmentation at a
tee is an authoring convention (`resolve/framing/pockets.py`), so `D-M-LAUN`'s pocket can
cross node `N-M-E3` where `W-M-LS` tees in without breaking anything: a pocket occupies floor
to 6'-8" only, so the band's plates run continuously over and under it and only its vertical
edge floats. `W-M-HS4` hosted nothing when this was built, which is the only reason a 4'-0"
pocket was possible there at all.

## Basement

- **THE SAUNA'S FIBRE-OPTIC LIGHTING IS CUT; TWO 24V UNDER-BENCH RUNS REPLACE IT
  (2026-09-13).** The room's only light was `ED-B-SAUNA-LT`, a single point fixture on
  `ED-T-LT-SAUNA-VT` (mark V) — a Cariitti Premium Glass Fiber 8-spot kit with a remote
  dimmable projector, billing **$1,500-2,250 installed**. That was, by a wide margin, the
  most expensive luminaire in the house, for one 92 SF room, and the owner cut it
  (`plans/TODO.md`).
  - **The replacement is not a new idea; it is what the notes always said.**
    `notes/sauna_basement_wall_detail.md` and `notes/sauna_shower_basement_detail.md` both
    specify "set light strips under the lower bench lip; keep drivers and transformers out
    of the hot zone". The **fibre kit was the departure**, in a 2026-09-06 re-spec that was
    answering a real constraint (see below) and answered it expensively.
  - **The 2026-09-06 reasoning was not wrong, it was aimed at a harder problem.** Nothing
    sold in the US is both IP65 and 125 C — LED sconces top out at 60-93 C — so a fixture in
    the CEILING of a 194 F löyly peak really does have only one construction available, and
    fibre optic is it. Under a bench the problem is different: a sauna is stratified, the
    peak is a ceiling number, and the air at an 18" foot bench runs 40-60 F below it. The
    LEDsupply sauna tape publishes **-30 C to +90 C**, which is enough there and would not be
    enough on a wall. That temperature rating is the whole reason this tape and not the
    Armacost cove tape (`PROD-ARMACOST-RIBBONFLEX-COB`, an ordinary 60 C part).
  - **Mark V stays in the catalog at 0 ea, and its LETTER is not freed.** The
    `glazed-green-brick` / `EXT_2X6_SWINBURNE` / mark N convention: a deleted row is a revert
    nobody can cost. The E-602 schedule is keyed on the mark, so the new type took **X**
    (`W` is `ED-T-LT-LINEAR-EXT`). `PROD-CARIITTI-VPL30-G211` stays too. The one live risk if
    the revert is ever taken is unchanged and is a PERMIT risk: Cariitti and Harvia are
    CE-marked, not NRTL-listed. Mark X has no such exposure — it is 24V Class 2 tape.
  - **uid `AEYMMW1KDG` IS RETIRED and must never be reused** (the `SGS503AAAA` precedent).
  - **TWO runs, because the benches are not a U.** The west foot bench (54") and the south
    foot bench (48") butt at x=10'-9 13/16" and form an L; the two-tier bench stands alone
    across the room with a y 66"..74 3/16" gap of open floor. `LR-B-SAUNA-BENCH-L` is a
    3-point path (west leg → SW corner → south leg, 7'-1/2") and `LR-B-SAUNA-BENCH-N` a
    2-point path (5'-0"). `light_run_materials` derives connectors from `len(path) - 2`, so
    the pair bills 4 end caps and **1 corner connector** — which is the physical truth; one
    run across the floor would have billed none and drawn tape over open floor.
  - **The paths are the bench FRONT FACES, not the liner** — the strip mounts to the fascia,
    20"-42" out from the wall. The west leg starts at y=2'-5 1/2" and not at the bench's own
    south end, because south of that line the west bench's fascia is behind the south bench.
  - **16" AFF is one elevation for the whole path, and a `LightRun` cannot rake.** It works
    only because every bench this tape touches is 18": the two foot benches are stated 18"
    and the 2T-60's LOWER tier derives at half its declared 36" (`library/placeables/
    furniture.py`). It clears `REG-B-EXH2`'s 4" AFF stale pickup behind the west bench.
  - **The PSU size was the binding constraint and it landed with room to spare.** 12'-1/2"
    at 3 W/ft is 36.1 W; x1.25 continuous is 45.2 W, **75.3% of `ED-T-LT-PSU-60`'s
    nameplate** — inside the OMNIDRIVE X's own "load to <=80%" instruction with no run
    shortening needed. `ED-T-LT-PSU-200` was never available: a PSU sums into the backup
    tier at its **RATING**, not the tape's draw, so 200 VA on `CKT-LT-BACKUP` (ALWAYS_ON)
    costs 1.40 kWh over 48 h against a 0.84 kWh solar surplus and flips
    `cycle_48h.sustains_always_on` to False — the identical trap that withdrew the basement
    cove. **Measured before and after**: CKT-LT-BACKUP 791 → 845 VA (−6 for the deleted
    fixture, +60 for the driver), 48-hour always-on surplus +0.84 → **+0.44 kWh**,
    battery-only autonomy 41.2 → 40.1 h, `sustains_always_on` still True.
    `test_backup_calc.py` passes.
  - **The driver is a SURFACE box on the workshop face of `W-B-SA-N`**, at (10'-0",
    10'-6 13/16"), 48" AFF — x=10'-0" keeps the 8" box 6 3/16" clear of `W-B-SA-W`'s corner
    and well west of `PR-B-ERV-COND`'s drop at x=13'; the centre is 3" north of the 10'-3
    13/16" face because a device footprint is a plan rectangle CENTRED on `position`.
    Surface and at reach height rather than buried in the cavity, which is what the
    OMNIDRIVE X's "accessible and ventilated" asks for — a driver is the part that dies and
    a plastered-in one is a demolition job. **It does breach W-B-SA-N's foil-faced polyiso**,
    the very barrier `plan/fixtures.py` routes the sauna's plumbing through `W-B-CS` to
    protect; the trade is taken deliberately, because what crosses is one 24V Class 2 pair
    through a single gasketed grommet sealed both faces, not a 2" drain.
  - **`ED-B-SAUNA-SW` retyped `ED-T-SWITCH` → `ED-T-SWITCH-DIM`** and did not move. The
    fibre kit dimmed at its projector; losing the dimmer in the swap would have been a quiet
    downgrade in the one room read by firelight standards. Pair it with a Lutron DVELV-300P
    reverse-phase control, never the DVCL-153P the cans use.
  - **The tape is priced by an `[allowances]` lump, and that is a DELIBERATE departure from
    the other three 24V strip types.** E / E1 / U bill per lineal foot through
    `light_run_materials`, which `prices.toml` declares an **unpriced view** — so a fourth
    type on that convention would have contributed **$0**, and the takeoff would have
    reported the whole $1,500-2,250 as saved. That is not true: a sauna-rated silicone IP68
    tape plus channel is a real purchase. `electrical-sauna-under-bench-strip` is a driven
    allowance on `light_run_materials.quantity[type=ED-T-LT-STRIP24-SAUNA,item=channel]`,
    the same vehicle and for the same reason as `electrical-garage-exterior-linear`.
  - **What was deliberately given up:** the star-field effect. What replaces it is a
    functional under-bench wash in the coolest part of a stratified room, at roughly a tenth
    of the cost, with no electronics and no line voltage inside the hot room at all. The
    ceiling LED-star option the TODO also floated was not taken — it puts emitters back at
    the hottest point and back through the vapour barrier.
  - **Mark V does NOT print a 0-count E-602 row, and that is correct.**
    `takeoff/lighting.py::luminaire_schedule` iterates `set(counts) | set(run_feet)` — types
    that are *actually installed* — not the whole catalog, so a catalog-only type simply
    leaves the schedule. That is the right behaviour: an electrician's schedule should not
    carry a fixture nobody is buying. The revert lives in `prices.toml` (0 ea, rate intact)
    and in the type catalog, which is where a revert belongs. Mark X shows `count: 0` beside
    E / E1 / U / W for a different reason — a `LightRun` has no unit to count, so those five
    report lineal feet instead.
  - **Verified, not assumed:** `code.R303_1_light_and_ventilation` does not regress, because
    it never graded this room — its population excludes `Occupancy.BATHROOM`, which
    `RM-B-SAUNA` is, and `code.R303_3_local_exhaust` is what covers it. The whole check
    report moved by exactly three lines (`lighting_controls` 140 → 141 luminaires,
    `wet_location` 29 → 30, `light_run_psu` 14 → 16 runs), 0 FAIL before and after.
  - The 2026-09-05 entry below (the room getting its first light at all) is history and
    stays.

- **MINNESOTA DOES NOT PERMIT DAMPPROOFING, AND THE LAYER WAS MODELLED AS
  HOUSEWRAP (2026-09-12).** Two owner questions — "review the basement
  dampproofing, good quality and good value" and "review the protection board"
  — were researched together. The second was already answered and stale; the
  first had a code floor nobody in this repo knew about.
  - **Minn. R. 1309.0406 subp. 1: "Section R406.1 is deleted in its
    entirety."** Subp. 2 replaces it: exterior foundation walls that retain
    earth and enclose below-grade interior spaces, floors **and crawl spaces**
    "shall be waterproofed ... from the top of the footing to the finished
    grade". **There is no high-water-table precondition** — the IRC's
    "dampproof unless R406.2 applies" ladder does not exist here, and its
    bottom rung is not a choice a Minnesota house may take. So "what is a good
    value dampproofing product" has no legal answer, and the `$0-12.50/SF`
    allowance ladder whose first rung read "damp-proofing only, IRC R406.1
    minimum" was offering something the state struck.
  - **The engine was grading the section Minnesota deleted.**
    `code.R406_1_dampproofing` cited IRC R406.1 and PASSed — on PRESENCE of a
    WATER control layer. It is `code.MN_1309_0406_waterproofing` now, it cites
    the Minnesota rule the way `rules.py` already cites 1309.0305, and it grades
    the layer's MATERIAL against subp. 2's eight-item list. Presence was exactly
    what the defect below satisfied.
  - **The modelled membrane was Tyvek HomeWrap at 54 perms.** `damp-proof`
    pointed at `material_ref="air-barrier"`, 400x looser than every document
    that reasoned about it (this log said "~0.13 perm"; the wall detail note
    said "liquid-applied membrane"; `prices.toml` described the XPS mastic as
    bonding to "the liquid-applied damp-proofing"). It also priced under **one
    key shared by three products** — the foundation sheet, the roof underlayment
    and the framed-wall WRB — so the Glaser walk, the money and the drawings all
    read a layer nobody had chosen.
  - **The selection: 60-mil rubberised-asphalt peel-and-stick sheet** —
    Bituthene 3000, with Polyguard 650 and Carlisle MiraDRI 860 as equals. Subp.
    2's item 5, and the strongest published numbers of the eight: **0.05 perm,
    300% elongation, crack-cycled 100x at -25 F unaffected, 200 ft hydrostatic
    head, 50 lb puncture**. GCP states it "is capable of bridging shrinkage
    cracks in the concrete and will accommodate minor differential movement."
    Material is sourceable at $0.80-0.87/sf; the INSTALLED half is the weak one
    and wants three metro quotes (see `prices.toml`).
  - **THE CONDENSATION VERDICT IMPROVED, WHICH IS NOT OBVIOUS AND WAS
    MEASURED.** The membrane is INBOARD of the foam, so tightening it 54 -> 0.05
    perm moves the wall's vapour resistance to the warm side of the control
    plane rather than trapping moisture behind it. `BASEMENT_8`'s monthly gate
    went from **69 Pa below saturation (worst month January, xps-b at 79% RH)**
    to **105 Pa (December, 75% RH)**; `BASEMENT_12` from 73 Pa to 105 Pa. The
    cold-snap screen is the bigger move: both walls read **"dew point reached at
    xps-b"** at -15 F before and read **"no dew-point crossing, 12 Pa below
    saturation"** after. A 0.05-perm layer means the wall dries INWARD only,
    which is the intended cold-climate behaviour — and it is why the interior
    face must stay vapour-open. It is: the check reports "no rated warm-side
    vapour retarder" on both. **No poly, no vinyl wallpaper in this basement.**
  - **The layer order does not change.** GCP's own instruction is "Insulation,
    if used, must be applied over the membrane", which is what
    `FOUNDATION_WALL_XPS4_OUTBOARD` already did. Thickness went 0.05" -> 0.06"
    for the real 60 mil; the face moves 0.01", far inside `resolve/stacking.py`'s
    0.5" `_TOL`, and no junction detail appeared or vanished.
  - **NO DIMPLE MAT, and the reason is buildability rather than money.**
    Delta-MS wants its head mechanically fastened and sealed to the wall, and
    outboard of 4" of XPS bonded with mastic there is nothing in reach to fasten
    into — the one genuinely unsolved detail in this design. Skipping it also
    leaves the layer stack and the outboard face untouched. **Free-draining
    stone against the lower wall** does the drainage instead: 12" of #57 washed
    stone up 4'-0" from the footing bedding, geotextile-lined, 18.6 cy. It was
    already on the drawing and missing only from the model. It is NOT authored
    as a `FrenchDrain` — there is no element kind for a VERTICAL drainage column,
    and a perimeter FrenchDrain over the trench the footing bedding already
    derives would bill the same stone twice.
  - **The "protection board" question was stale.** The 1/2" aluminium-faced
    board became a 1/8" trowel-applied acrylic coating on 2026-09-04, because a
    butted board's installed permeance is its joints and nothing in that class
    publishes an ASTM E96 number. **Do not revert it.** Anchoring was answered
    at the same time: mastic to the membrane, head under the rainscreen
    Z-flashing, foot buried 6", backfill below — and the board it replaced was
    pinned into the FOAM, never through to concrete, so the swap gave up
    nothing. The one clarification it was missing: **that coating is the
    ABOVE-GRADE exposed-XPS band only**, 276.3 SF of ~1,016 SF, a UV and impact
    skin rather than a below-grade protection board. Below grade there is no
    protection course at all, which is why backfill **in controlled lifts** is
    now an `insp/foundation_backfill` item rather than an assumption.
  - **It was filed on the wrong trade and scheduled after the roof was on.**
    `takeoff/envelope.py` scopes a foundation wall's layers as `"foundation
    wall"`, which was not in `emit/trade_rules._POUR_SCOPES`, so the membrane
    fell through to `"siding"` — despite the comment one line above naming
    damp-proofing as what the `concrete` branch is for. Merged with the roof
    underlayment under one `air-barrier` key, `_one_trade_per_row` forced the
    lot into `task/walls/building`, which `depends_on` framing and roof. Meanwhile
    `insp/foundation_backfill` is literally "Waterproofing, drainage and
    backfill". One word fixed it. The **second** inversion was the allowance:
    it sat in `task/concrete/building/flatwork`, which `depends_on
    insp/foundation_backfill`, and deleting the allowance deleted it outright.
  - **The allowance is gone and the layers are priced.** `[envelope_layers]
    "waterproofing"` at **$2.80-5.35/SF installed** over 1,136.9 SF (1,016.4 of
    below-grade face plus the two framed court tails), and
    `foundation-damp-or-waterproofing`'s $0-12,705 is deleted. The double-bill
    `plans/TODO.md` had carried open is closed the same day: `BASEMENT_8` and
    `BASEMENT_12`'s all-in $/cy rates were struck by the $7-18/LF of
    damp-proofing their own derivation note says they absorb. **The estimate's
    low end rises and its high end falls, and that is the point of modelling it
    directly** rather than holding a $0-12.50/SF band open beside a real layer.
  - **NO MEMBRANE ON THE SUNKEN-GARDEN COURT WALLS, and it is not a cost cut.
    DO NOT "CORRECT" THIS.** 1309.0406 subp. 2 scopes to walls that retain earth
    **and** enclose below-grade interior space; no `W-SG-*` wall has a room
    behind it, and `_retaining_walls()` already implements exactly that test —
    its docstring records that screening on fill alone "reported four FAILs
    against walls neither section is addressed to." `SUNKEN_GARDEN_WALL` is
    `EXPOSED_MIX`: w/cm 0.40, f'c 5,000, 6% air, ACI F3/W1/C2 with HDG bar,
    which is a better long-term moisture barrier than an asphalt coat.
    - **What those walls get instead is the drained backfill the free-body note
      says nothing in the model provides.** `notes/sunken_garden_court_free_body.md`:
      "No drainage or hydrostatic case — and NOTHING IN THE MODEL MAKES THE
      DRAINAGE WORK. ... A saturated backfill roughly doubles the thrust and
      would take the system well under 1.0. ... It is the single largest
      unpriced assumption in §9." `engineering/retaining_wall.py` says the same
      in its own voice. So the money on these walls belongs in stone that
      relieves the thrust, not in a coat that relieves nothing: 12" of #57 up
      7'-0" over W-SG-W2 / E2 / S, 52.6 LF, geotextile-lined, discharging to the
      4" socked tile their footing beddings already carry.
    - **THIS DOES NOT FIX THE R404.4 FAILURE.** Sliding FS is ~0.57 against
      1.50 and still needs the consultant
      `notes/sunken_garden_retaining_screening.md` was written for. Drained
      backfill relieves the hydrostatic case the engineering explicitly does not
      run. Nothing here should make the report look better than the building is.
  - **Three conditions carried into the spec**, each answering a known failure
    mode, all in `notes/basement_to_framed_wall_detail.md`: **cold weather**
    (standard Bituthene 3000 needs 40 F; spec `Bituthene Low Temperature`, 25-60
    F, with `Primer B2` or `B2 LVC` — otherwise the membrane gates the whole
    foundation on a warm week); **seams**, which is the failure mode rather than
    the field (BSC BA-1015: walls "ostensibly 'waterproof' ... have been
    documented to fail at poorly connected seams" — 2" laps rolled firmly, 2-ply
    reinforced corners over a 3/4" cant fillet, every penetration detailed); and
    **Primer B2 is solvent-based and attacks polystyrene** (it sits between
    concrete and membrane so the XPS never touches it, but require full flash-off
    or specify B2 LVC). Also into the drawings: cold-joint treatment at the
    footing/wall joint, positive flashing and weeps at `W-SG-BRKBM`'s brick
    ledge, and **backfill within 30 days** — the UV limit on this product class.
  - **Open, and outside the model:** three metro quotes for installed
    peel-and-stick on NEW construction (published installed figures are
    retrofit-weighted), the pour season, and MN DLI's 2024-IRC rulemaking, which
    is mid-cycle with no effective date and may or may not move 1309.0406.

- **THE SLABS WERE THINNED, and the psi grade is stated per use.** The
  basement slab went 3" -> 2" XPS at **>=25 psi** (R-16.1 -> R-11.1 whole-assembly, against
  an owner target of R-10; still PASSes `code.energy_prescriptive`'s R-10 slab row), and the
  detached garage slab 3" -> **1" at 40 psi** — 40 because that is the one slab in the house
  carrying VEHICLE wheel loads, and a loaded wheel is a contact patch, not a distributed
  floor load. `RM-GARAGE` is `conditioned=False`, so nothing grades it and every number
  there is an owner choice. Three things follow:
  - **The psi grade is NOT PRICED.** `library/materials.py` has one `xps` tag with no
    compressive field, and `prices.toml` keys XPS on THICKNESS alone — so the 40 psi board
    and the 25 psi board carry one rate here and do not in the yard (40 psi runs ~20-35%
    over). Fixing that properly means a psi-bearing material tag, not another price key.
  - **XPS IS THICKNESS-QUALIFIED IN `prices.toml`, AND IT HAD TO BE.**
    `envelope_layers` qualifies its price key on `thickness_in` (`cli/prices.py`), and the
    file carried only the bare `"xps"` key — so 1", 2" and 3" board all priced at one $/SF
    blend, which made any change of foam THICKNESS cost exactly $0 in the estimate. A cost
    model that cannot see a design decision is not decision-useful. The three qualified rows
    are DERIVED from the researched blend ($0.372-0.744 per inch-SF) with labour held flat
    across thicknesses, which is the conservative reading.
  - The basement's return to 2" retired a `DECLARED_DIVERGENCES` entry in
    `test_catlin_reference_parity.py` — catlin and the reference detail agree again.

- **THE BASEMENT'S WEST HALF WAS REPLANNED ON 2026-09-05, AND WHAT IT BOUGHT IS
  CIRCULATION.** Two doors were formed through 12" interior pours — `D-B-GYM` in `W-B-CS2`
  and `D-B-NE` in `W-B-CN` — and they were the house's only openings through concrete. The
  money was small (a buck-and-blockout allowance, $500-1,200 the pair, and
  `prices.toml`'s `concrete-window-bucks-and-blockouts` row now drives to zero and is kept
  under the `glazed-green-brick` convention). The defect was that from the stair foot the
  only route to the furnace room was **stair → playroom → gym → aisle → workshop →
  furnace**. Both doors are gone. Nothing on the x=18' bearing grid moved and no concrete
  wall moved.
  - **The sauna rotated onto the south (garden) wall**, long axis east-west, and then
    **shrank east to x=8'-10" the same afternoon — see the round-two entry below.** As
    rotated it ran x 4'-8"..18'-0" by y 0'-0"..9'-5", a 12'-2" x 8'-2" clear box against the
    8'-1" x 12'-7" it was, and its south face crossed two substrates with a **2" jog between
    the two liner faces at x=8'-10"** that nothing in the model drew. The `W-B-S1B` segment
    and the `SAUNA_LINER_ON_BASEMENT_8` assembly that carried it both existed for one
    afternoon and are gone. What survives the rotation: the room keeps `WIN-B-SAUNA` and is
    entered **from the gym** through framed `W-B-CS`, a short walk from `D-B-PATIO` and the
    sunken garden, which is what the brief asks the room for.
  - **x=4'-8" was a footing's doing, and it went away with the split.**
    `structural.frost_depth` lowers a footing's local grade by any open excavation within a
    frost depth (42") of the footing SOLID, and a footing follows its wall. At the 5'-0"
    split the plan was drawn at, `FT-B-S1` — the west half — sat **exactly 42.0"** from
    `SL-SG-FLOOR`'s rim: inside the reach by floating point, and outside `SL-SG-FROST-W`'s
    own 42" shielding radius. 4'-8" bought 46" of clear. With the split retired, `FT-B-S1`
    is one strip beside the court again and the wings protect it as they always did.
  - **The bathroom rotated** north-south along the framed stair wall
    (`W-B-STR3B`/`W-B-STR2`), **3'-3 15/16" x 7'-1 1/4" clear** (3'-5 1/4" until round two
    slid its east wall 1 5/16" west). Its **wet wall is `W-B-BA-E`**,
    a new `INT_2X6_STAGGERED_PLUMBING` east partition carrying the shared vent riser at
    (13'-10 11/16", 19'-3") — and `W-B-BA-N`, which used to be the room's only stud cavity, dropped to
    a dry `INT_2X4_PARTITION` when the plumbing left it. `D-B-BATH` swings out into the
    hall, and **on this wall that takes `flip_swing=True`**: the leaf's default side follows
    the host's direction and `W-B-BA-E` runs north-to-south where `W-B-BA-N` ran west-to-east.
  - **A hall** runs west of `W-B-CN2` from the stair foot south — 3'-3 15/16" clear, part of
    `RM-B-STAIR`'s own loop, no new `Room`. It stopped at the y=18' line and crossed into the
    workshop through `O-B-HALL`, a cased opening in `W-B-CW2B`; **on 2026-09-07 it runs the
    rest of the way to the sauna's north wall** and both of those are gone (next bullet).
  - **THE HALL REACHED THE SAUNA WALL, 2026-09-07 — and it retired the replan's "accepted
    consequence".** That consequence read: the playroom is reached only via the gym
    (stair → hall → workshop → gym → `D-B-PLAY`), and the workshop is the through-route from
    the stair to the gym. Running the hall south from y=18' to y=10' on the **same
    x=13'-10 11/16" well-partition centreline** `W-B-BA-E` and `W-B-WELL` already stand on
    buys three things for the length of one partition, `W-B-HALL-W`:
    - **`D-B-GYM` lands on the hall**, not on the workshop — same uid, same position, same
      32" leaf, retyped to `DT-INT-SWING32-GLAZED`. Circulation is
      stair → hall → gym → `D-B-PLAY`, one room shorter. The glazing is not decoration: the
      hall has no window and the gym's south daylight is the only light it can borrow.
      **It stays 32"** — `W-B-CS3` offers 42 3/16" of framed run and a 36" RO leaves 3/16"
      for two jamb packs.
    - **The workshop is a room, not a corridor**, with `D-B-SHOP` — 3'-0", in `W-B-HALL-W`,
      `flip_swing=True` so the leaf goes west into the shop, hinged at the north jamb. Its
      RO centres on `D-B-GYM`'s at y=12'-3 7/16" so the equipment path is straight through.
    - **The equipment route is the hall**: 3'-0" at `D-B-FURN` (widened, position unmoved —
      it is still pinned west by `PR-B-ERV-COND`) and at `D-B-SHOP`, off a 3'-5 1/16" flight.
    - **`W-B-CW2B` and `O-B-HALL` are deleted.** The note on that wall said it *had* to exist
      or the workshop and stair loops would merge into one room. True, and now deliberate:
      the merge IS the hall. `RM-B-STAIR` goes 114.8 → 147.7 sf and keeps one seed.
    - **`W-B-SA-N` splits at `N-B-HALL-S`**; `W-B-SA-N2` is the east 4'-1 5/16", and
      `WP-B-SAUNA-SPLASH`'s second span re-datums onto it at 9 5/16".
    - **`W-M-CLN2` now stacks on nothing, and that is authored.** `W-B-CW2B` was the only
      wall under it; what is left below is `W-B-CW2`, which overlaps its x 13'-4"..18'-0" run
      by 6 11/16" — short of the 2'-0" minimum, so there is one candidate count of ZERO and
      no `integrity.stack_ambiguous` to arm (the `W-M-STRW2` precedent). The load goes into
      the deck instead: two `JoistReinforcement` blocking entries in `params/main_deck.py` at
      x=14'-6"/16'-9", `at` y=**217"** rather than 216" because `at` snaps to the nearest
      joist line and 216" is exactly equidistant from 208" and 224". They must stay LAST in
      `_WEST_FLOOR_REINFORCEMENT`.
    - **The hall inherited the workshop's service ceiling, and that is the one thing the
      change actually cost.** `RM-B-WORKSHOP` is UTILITY, which is in
      `EXPOSED_SERVICE_OCCUPANCIES`, so nothing graded a pipe in its air. `RM-B-STAIR` is
      not, and `mep.run_in_finished_volume` (3" tolerance) called three runs the moment the
      hall grew: `DU-B-ERV-R-GYM` at 8.4", `PR-B-SAUNA-VENT` at 10.7" and `PR-B-HW-SAUNA` at
      3.8". The first two are not reroutable — the gym register is east of the x=18' bearing
      line and the ERV is west of the hall, so ANY route between them crosses it — so they
      are boxed out by **`SF-B-HALL`**, a full-width bulkhead at the hall's south dead end
      (x 170.0725"..212.615", y 123.8125"..133.4375", underside 85 15/16" storey-relative,
      7'-1 15/16" clear). **[2026-09-13: that bulkhead is retired. `Room.exposed_services`
      landed on 2026-09-13 and `RM-B-STAIR` now says in words what the box said in board —
      the owner accepts exposed services in the basement, and the hall's south end is
      circulation, not a room anybody sits in. Nothing about the paragraph above was wrong;
      it was the best answer the model could hold at the time. Both runs still clear the
      6'-8" headroom line on their own numbers, so no route was re-solved for the deletion.
      `SF-B-GYM`, built on the same argument six days later, went with it — and so did
      `SF-S-SUITE` upstairs, on `RM-S-SUITE`'s own declaration. Three boxes, one idea: a
      soffit authored to answer a check was the engine's notion of a ceiling standing in for
      the owner's.]** The third was a
      modelling artefact worth fixing rather than boxing:
      `PR-B-HW-SAUNA` was **stacked 1 3/16" under `PR-B-CW-SAUNA`** on the same x=17'-4"
      line, which is not how a supply pair gets hung. They are side by side now — x=17'-4"
      and 17'-3", both at 7'-10 5/8" — and both clear at 2.55". There is no elevation pair
      that fixes a stacked one: two 1/2" lines need 5/8" of separation and the band between
      the ceiling and the 3" limit is 3" deep.
    - **Lighting and outlets.** Three more `ED-T-LT-CAN3` on `CKT-LT-BACKUP` at x=190",
      y=19'-6"/15'-0"/11'-6" — 27 VA against the ~52 VA of ALWAYS_ON headroom the withdrawn
      play-room cove was measured against, so `cycle_48h.sustains_always_on` holds
      (`test_backup_calc.py`). The middle one is at 15'-0" and not the ladder's 15'-6"
      because `PR-B-HW-SAUNA` crosses there 2 9/16" below the ceiling and a recessed trim
      wants that plane. `ED-B-WORKSHOP-SW` moves onto `W-B-HALL-W`'s workshop face 5" north
      of `D-B-SHOP`'s north jamb — **the hinge side, and the only side**: the latch jamb has
      5 5/8" of wall to `W-B-SA-N2` and no box fits in it. `ED-B-HALL-RC1` is new, on
      `CKT-RC-BSMT` at y=16': NEC 210.52(H) wants it and `electrical.receptacle_spacing`
      walks {BEDROOM, LIVING, KITCHEN, DINING, OFFICE} only, so nothing will ever ask.
  - **Two things the replan cost that are worth knowing before the next edit.** S-100's
    ARCH D scale went **3/16" → 1/8"** — one new foundation assembly is one more row in the
    FOUNDATION WALL SCHEDULE, that column already carried all three schedules (the sheet has
    no width left to open a fourth with), and the scene passed the 3/16" height by 0.18".
    **Round two handed the scale back** by deleting that assembly, and the 0.18" of margin
    is still all there is: the next `FoundationWall` assembly tag anywhere in this house
    steps ARCH D down again.
    And `test_upper_storey_studs_stand_over_studs` went 112/247 → 124/255, all of it two
    walls: `W-M-C1` (the x=18' line has three basement segments under it now and `stacks_on`
    names one, so `W-B-CS3`'s studs are invisible to the metric though they share its layout
    line) and `W-M-CLN2` (forced onto `W-B-CW2B`, which restarts its module 8" off because
    `INT_2X4_PARTITION` is deliberately not on the interior grid). **`W-M-CLN2` came back off
    that stack on 2026-09-07 when `W-B-CW2B` was deleted** — it stacks on nothing now, and
    `test_catlin_contract_m3.py` moved with it.
  - **`ED-B-GYM-RC1`/`RC2` were on the wrong side of the x=18' line and nobody noticed.**
    They were authored 1" WEST of `W-B-CS`'s west face — inside the sauna, a 120V
    convenience receptacle in a 190 °F room — and `electrical.receptacle_spacing` accepts a
    device within 0.5 m of a room's clear face **regardless of which side it is drawn on**,
    so the gym counted them and nothing said so. Both are on the gym face now, and there are
    three: the line is broken by two doors, and NEC 210.52(A)(2) measures wall space between
    doorways. `ED-B-GYM-RC8` stands in the 15" of `W-B-CS3` north of `D-B-GYM`, because
    everything past `N-B-C1` is `W-B-CS2`'s pour.

- **ROUND TWO, THE SAME DAY: one substrate under the sauna, one plane beside the stair, and
  a closet in the dead space.** The replan above fixed the circulation and left three things
  that read wrong on a drawing. All three had one answer.
  - **The sauna's west wall moved from x=4'-8" to x=8'-10", onto `N-B-S1`.** ~8'-3 15/16" x
    8'-3 11/16" clear, and its south face is now **one plane on `W-B-S2`'s garden curb** —
    the 2" jog is gone, `W-B-S1B` is deleted, `SAUNA_LINER_ON_BASEMENT_8` is unregistered,
    `FT-B-S1` is one unsplit strip and `structural.frost_depth` still passes. The workshop's
    west bay took the four feet: 3'-8 3/16" → **7'-10 3/16"** clear, and
    `ED-B-WORKSHOP-PANEL1` went back to its centre. The 8'-6" two-tier bench does not fit an
    8'-4" room whose north wall gives up 3'-0" to the shower pan, so
    `FURN-SAUNA-BENCH-2T-60` was minted beside it in `library/`; the heater and its junction
    box crossed to the **south-east corner**, the only stretch of south liner clear of the
    window, the benches and the door. **`EQ-T-SAUNA-HEATER`'s 9 kW was always sized for this
    room** — the "~513 cf" in `electrical.py` matched the pre-rotation box and the shrunk one
    (519 cf), not the 745 cf the rotation grew it to.
  - **`W-B-BA-E` slid 1 5/16" west onto the stair well's partition centreline** at
    `inch(166.6875)`. Two nearly-collinear planes an inch and a third apart became one, and
    everything that references `N-B-BA-NE`/`N-B-BA-SE` rode along. The wet-wall risers did
    NOT — they are absolute coordinates in `mep_venting.py`, `mep_supply.py` and
    `mep_supply_devices.py` — and neither did `ED-B-BATH-SW`, which stood 1 5/16" inside the
    studs until `test_wall_mounted_devices_resolve_against_a_wall_face` caught it. **No
    `haus check` rule grades a wall device's depth.**
  - **`W-B-WELL` gives the well partition faces, not framing.**
    `resolve/stairs/u_split.py` already GENERATES the 2x4 plates and studs between the two
    flights — the plan this was written from said it emitted nothing, and the first build
    answered with twelve `structural.member_interference` FAILs. So
    `STAIRWELL_PARTITION_4H`'s structure layer carries **no `FramingSpec`**, which
    `framing/solver.frames_as_members` reads as monolithic — so the wall lands in
    `[wall_structure]` billing 0.47 cy of "placed spf", and `prices.toml` prices it at
    **zero** and says why. Its thickness must stay locked to
    `resolve/stairs/common._WELL_PARTITION_THICKNESS_M` (4 1/2"): `INT_2X4_PARTITION`'s
    4 3/4" pushes 1/8" into each inner stringer.
  - **`RM-B-UNDERSTAIR`, 17.5 sf that nobody could reach** — *superseded by round three
    below, which deleted `W-B-CL-N` and the room with it.* The volume under the arriving
    flight was inside `RM-B-STAIR`'s polygon, so the model called it floor. `W-B-WELL` closes
    the east side, `W-B-CL-N` the north (**47" tall, not the 52" the stringer allows — the
    upper landing's ledger is the lower obstruction and it starts at 47 5/8"**), and
    `D-B-CLOSET` opens it west into the furnace room. `RM-B-STAIR`'s seed had to move out of
    the new partition's footprint.
    - **Do not author `Room.ceiling` here and do not put a `Soffit` under the flight.** The
      real head rakes 96.7" → 54.8" and no field says that; `_clear_head` reads decks and
      soffits, a stringer is neither, so `clear_height_m` resolves to the main-floor deck and
      passes R305.1.1 honestly. An authored 53" ceiling would be taken verbatim and FAIL.
    - `DT-INT-CLOSET24` is **2'-0" x 6'-0"** and the far jamb is why: at y=28'-4" there is
      76.5" of head, a 6'-8" leaf plus header wants 82", a 6'-0" one wants 74".
    - `W-B-STR3` was retyped to `STAIRWALL_INT_2X6_BRG_UNDERSTAIR` — 5/8" Type X in
      place of the 3/4" stair plywood, per R302.7. **That cost the exposed-plywood stair face
      on this segment** (a `Wall` carries one leaf) and moved `FO-M-STAIR`'s west edge to
      `ft(10, 3.25)`, exactly as that opening's own comment predicted it would have to.
  - **The engine changed twice.** `illumination._gypsum_finishes` matched the literal
    `"gyp"`, which **no layer in this catalog contains** — every gypsum layer is `gwb*` on
    `gwb`/`gwb-x` — so `code.R302_7_under_stair_protection` could never verify protection,
    only fail or find nothing to protect. And `topology._through_pair` chose a four-way
    node's through run **alphabetically**, which at `N-B-ESS-SE` picked the two partitions
    over the bearing wall running through and reported a mixed-assembly junction; it prefers
    a continuous bearing pair now, tag order as the tie-break.
  - **`D-B-FURN` is at `ft(3, 3)` and the condensate line fixed it there.** A UI drag had put
    it at 1'-6 1/16" — `from_node` offsets the NEAR JAMB — across `CD-B-SPA`,
    `CD-B-DATA-SHOP` and `PR-B-ERV-COND`. None of the three can move (a `ConduitRun` has one
    flat elevation and `CD-B-SPA`'s south end is sleeve-pinned at -4'-0"), so the door did.
    The king stud's west face lands 0.475" off the condensate pipe: **any move of that door
    east re-opens the clash.**
  - **Two rooms had no light at all and nothing graded it.** `RM-B-SAUNA` and the new closet
    now have one each (`ED-T-LT-SAUNA-VT`, a 125 °C sauna-listed fixture with its switch
    OUTSIDE the hot room; `ED-T-LT-SPOT-SW`, integral-switch). There is **no NEC 210.70 check
    in this engine** — a missing lighting outlet is invisible to `haus check`.
  - **`EQ-B-HP2-GYM` was 5 1/2" into the ceiling and the UI drag did not do it.** Mounted at
    7'-6" AFF, a 10 53/64" cabinet tops out at 100 13/16" in a room `code.R305_ceiling_height`
    measures at 95 3/8". It is at 6'-6" now. The drag itself was kept: it is on `W-B-S3-FR`
    throwing north across the room's 18' depth, which is the better wall.
  - **`LR-B-STAIR-RAIL` still lies under the flight rather than along it** — one `Mount`
    elevation for a whole `LightRun`, measured off the slab, so it cannot rake. Pre-existing,
    now visible because the volume it runs through is a named closet. `PA-B-BFP-SAUNA`'s
    `room=` said `RM-B-SAUNA` and never was (it is 6'-7" north of the sauna); fixed.
  - **Still unresolved and not this change's:** `CD-B-SPA`'s east leg at y=1'-0", 61" over
    the slab, appears to run **through** the rotated sauna.

- **ROUND THREE, THE SAME DAY: the under-stair closet loses its north wall, and the sauna
  takes 7" off the workshop.** Two owner calls, and between them they say something about
  this model worth keeping: **both changes are bounded by things no check grades.**
  - **`W-B-CL-N` is deleted and `RM-B-UNDERSTAIR` with it.** The storage under the arriving
    flight runs the full length of it now and on under the landing deck, instead of stopping
    at y=31'-0". `W-B-WELL` keeps the east side and its north end is free — `open_end=True`
    on `N-B-CL-NE`, which is what `integrity.wall_loop_open` is for and the only honest way
    to say a partition dies in the middle of a stair well.
    - **The `Room` could not survive it.** With nothing closing the north side both seeds
      land in ONE face, and `RM-B-STAIR` and `RM-B-UNDERSTAIR` each resolved the **same
      114.8 sf polygon** — the whole shaft counted twice in every area, finish and load that
      walks rooms, at 0 FAIL. So the closet gives up its label and keeps its use:
      `D-B-CLOSET` still opens it to the furnace room, `ED-B-CLOSET-LT` still lights it (its
      `room=` is `RM-B-STAIR` now, the fixture did not move), and `EQ-B-HP2-GYM`'s
      `zone_rooms` drops the tag.
    - **`W-B-STR3` is NOT retyped back.** `code.R302_7_under_stair_protection` now passes on
      "no enclosed usable space" — the check keys on a room's occupancy and `STAIR` is not in
      `_UNDER_STAIR_OCCUPANCIES` — but the reason for the Type X did not go away with the
      label. The code hook went quiet; the wall stays as built.
  - **`W-B-SA-N` went north 9'-5" → 10'-0", and `D-B-GYM` is what stops it there.** The room
    is 8'-3 15/16" x **8'-10 11/16"** clear, 555 cf against `EQ-T-SAUNA-HEATER`'s 600 cf
    rating — 45 cf of margin, so a deeper sauna from here is a bigger heater and a bigger
    circuit, not a free change. The workshop's north strip pays for it: 8'-7" → 8'-0".
    - **The binding constraint is an opening, and nothing grades it.** The east end of this
      wall lands on `W-B-CS3`, the 4'-5" of framed x=18' line between the sauna and the
      y=13'-10" pour, and `D-B-GYM`'s rough opening starts at y=10'-11 7/16". At 10'-0" the
      wall's north face leaves 7 5/8" for the jamb pack. At **10'-6" the two overlap
      outright and `haus check` says nothing** — no rule tests a tee wall landing beside an
      opening. The coupling runs both ways: if `D-B-GYM` goes back south, this wall follows.
      **It is also why `D-B-GYM` stayed 32" when the hall reached it on 2026-09-07**: 42 3/16"
      of framed run less two jamb packs is a 32" leaf, and a 36" one would spend the 7 5/8"
      this bullet is about.
    - **Everything dimensioned off the north liner moved 7" with it**, and none of it would
      have been reported: `FURN-B-SAUNA-BENCH-E`, `FX-B-SAUNA-SH` (the pan stays in its
      corner), `FX-B-SAUNA-FD`, both `SP-B-SAUNA-*` sleeves, `PR-B-SAUNA-DRAIN`'s first
      three vertices, `PR-B-SAUNA-FD-DROP`, both condensate air gaps and
      `PR-B-SAUNA-VENT`'s riser. `D-B-SAUNA` is `from_node("N-B-SA-NE", …)` and DID report:
      it rode the node north and `structural.door_framing_module` FAILed on the stud module
      within the same build. Its offset grew 7" to hold the leaf still.
  - **A third bench, on the south liner: `FURN-B-SAUNA-BENCH-SW`, and the heater moved to
    let it grow.** `EQ-B-SAUNA-HTR` stood in the middle of the south liner and left
    3'-7 15/16" of it, which is a 2'-6" bench. On the **east liner** — `rotation=deg(270)`,
    18" face to the wall, 16" depth into the room, 2" off both liners as before — it leaves
    4'-7 15/16" and the bench is **4'-0"**. `ED-B-SAUNA-JB` came east with it and butts its
    west face; `REG-B-SUP3` and `DU-B-ERV-R-SAUNA-SUP`'s east leg followed, because "over
    the stones" is a position, not a label.
    - **What stops the bench is `ED-B-SAUNA-JB`**, not the wall: the box's base is at 18"
      AFF, exactly the bench top, so a 4'-6" carcass would reach under it and put a fixed
      seat in front of a live 9 kW junction box. 4'-0" leaves 7 15/16" to the box and
      1'-1 15/16" to the heater. Raising the box over the bench would buy that back and is
      the wrong trade in a room that stratifies.
    - **The heater is deliberately not pushed north against `D-B-SAUNA`'s jamb**, which
      would free another 1'-6" of bench and put a 30" stove at the doorway. Nothing grades
      any of this: `EquipmentType` carries no `clearances` and no rule tests a placeable
      against a wall device or an equipment footprint against a door approach.
    - `FURN-SAUNA-BENCH-48` was minted in `library/` and priced in `prices.toml` — **an
      unpriced type is silently dropped from the takeoff.**

- **Four basement assemblies, and every split is a condition, not a preference.** Two
  independent axes cross here: what covers the exterior XPS, and how thick the pour is.
  All four compose off `library/`'s `FOUNDATION_WALL_{8,12}_XPS4_CORE` plus a house-local
  skin layer, so the core cannot drift between them.
  - *The skin, and there is only one.* `BASEMENT_12`/`_8` cover the
    XPS with a 1/8" `foundation-coating-acrylic` banded from 6" below grade to the top of
    the wall — a trowel-applied acrylic coat over reinforcing mesh, authored as a
    `Layer.extent` off the `GRADE` datum, so a grade lift grows it without an edit here.
    **It was a 1/2" `foundation-protection-panel` until 2026-09-04, and the swap bought a
    verdict, not a saving.** A butted board's installed permeance is its joints, nothing in
    that product class publishes an ASTM E96 number for it, and
    `building_science.condensation` reported UNKNOWN on both assemblies for as long as it
    was authored; a seamless lamina is gradeable and both walls now PASS. Installed, the
    coating bills slightly *above* the board. The board and its price row survive as the
    named alternate, so the revert is one `material_ref` edit.
    `W-B-S1`/`W-B-S4` are on `BASEMENT_8`, which
    retired the stucco: their exposure genuinely *is* a grade band (6'-4" of fill,
    2'-2 9/16" out of the ground), so they get ~37 SF of coating. The court segments in
    between get **no skin at all** — their XPS is inside `W-B-BRICK`'s ventilated cavity,
    with no UV and no impact on it, and 273.7 SF of parge was buying a plasterer's
    mobilization to finish a surface nobody sees. `BASEMENT_8_GARDEN` and
    `_GARDEN_PARGE` survived unreferenced for a week and were **deleted 2026-09-12** under
    decision #72 — an unreferenced assembly saves no consumer any churn, because every
    consumer in this house derives from *walls*, so all it preserved was reasoning, and
    reasoning is what git is for. `plan/assemblies.py` keeps a short pointer; the revert is
    the two `assembly=` edits plus a `git show`.
  - *The pour.* 12" used to be earned wherever a cast concrete deck landed on the
    wall top beside the sill plate and needed a bearing seat inboard of it. After the
    basement-ceiling overhaul the only cast deck left is `SL-M-DECK`, which bears on the
    east wall and the centre line — so `W-B-E1/E2` stay `BASEMENT_12` and the other
    nine segments are 8" carrying `#5 @ 41" o.c.` vertical steel, which IRC Table
    R404.1.2(8) requires at 8" where 12" reads NR (it was `#6 @ 48"` before the flat
    bearing seat made the pour exactly 8'-0", which is the table's 8'-unsupported row
    rather than the 10' row a 9'-4" wall rounds up to). **The "12" is earned only where a cast
    deck lands beside the sill plate" rule is now obsolete** — with a flat seat nothing
    competes for wall-top width, and the 12" segments that are left are left as built for
    reasons written on the walls themselves, not for bearing. `W-B-STR` and `W-B-STR3` are
    2x6 bearing stud walls — `unbalanced_fill`
    is `ft(0)` on both, and what they carry is joists and a wall stack, which is a
    stud-wall job on a footing. `W-B-CS` is the same — it
    carries wood on both faces — leaving `W-B-CS2`/`W-B-CN`/`W-B-CN2` as the interior pour
    that remains. Drop that string on any of the nine and
    `structural.foundation_unbalanced_fill` FAILs, correctly.
  The banded walls carry 4.175" outboard of the concrete face over the band and 4.05" below
  it; the court walls carry 4.05" throughout. `N-B-BRICK-W`/`-E`'s stand-off is
  `inch(-4.05)`, on the court walls' bare XPS, and the veneer's clear cavity is **1-1/2"**
  (IRC R703.8.4 wants 1" minimum). **It was `inch(-4.55)` until 2026-09-04 and that was a
  bug**: the node was struck on the old parge's finished face and did not follow the parge
  when it was deleted, so a 1/2" void sat between the XPS and the veneer's 1" `air-gap`
  layer with no layer describing it — the model said 1" where the build had 1-1/2". Moving
  the node onto the foam and growing `air-gap` to 1-1/2" cancels at the gap's outboard face,
  so the wythe, the arched reveals and the veneer's footing all stay exactly where they
  were. That is why thinning the *wall* did not move the brick, and why changing a
  *skin* thickness moves the cavity rather than the wythe. Because
  the walls align on `face("concrete-ext")`, the 4" came off the INSIDE face: the furnace
  room and the workshop each gained 4" of clear (the model still reports the old number —
  `clear_face` is inset from the wall axis, which did not move). See
  `notes/basement_to_framed_wall_detail.md`.

## Decks and the garage

- **Deck-plank-as-sheet conversion, and the breezeway's part in it (RETIRED structure).**
  As of 2026-09-03, `FS-SG-PORCH` (composite, 3bf2f48), `FS-SG-DECK` (aluminium), and
  `FS-BW-FLOOR` (composite, at the time a deck joist field) all carried their boards as
  `subfloor=DeckLayer(...)`; the `SL-SG-PORCH`, `SL-SG-DECK`, and `SL-BW-DECK` slabs that
  used to stand beside the framing were deleted, and all three planks moved from billing by
  the cubic yard out of `[concrete]` to the square foot in `[sheet_goods]`. The balcony
  converted term for term because its joists cantilever 6" and the deleted slab's outline
  *was* that cantilever.
  - **The breezeway needed an engine change, and it was one field.** At that time its plank
    oversailed the joist rim 2 3/4" at each end onto `D-M-ENTRY`'s and `D-G-SERVICE`'s
    thresholds, and a floor system's sheet used to be exactly its joist field
    (`resolve/floors.py`) — so converting it either FAILED `code.R311_3_exterior_landing` on
    both doors or laid a joist through the (now-retired) roof posts `PT-BW-1..4`.
    `JoistSpec.cantilever*` could not help: a bearing line is a span boundary, so a
    cantilever is a joist-AXIS quantity and this oversail was on the perpendicular one.
    `FloorSystem.subfloor_outline` — an authored sheet polygon that replaces the derived
    corners and touches nothing else (not the joist solver, not `deck_voids`, not the
    elevations) — is the fix, and it survives the rewrite as a general engine capability
    (see keep8.md).
  - **Bound it.** `structural.subfloor_oversail` grades an authored sheet against
    `[framing] bearing_plan_tolerance_in` (8"), because past that the uplift pass finds
    neither a derived tie nor a hanger and FAILs every member under the deck, reported
    nowhere near the deck. The old breezeway's worst edge was 3 5/8".
  - **The take-off had to move with it.** `sheet_goods_takeoff` computed area from the
    bounding box of `floor.members`, so a wider sheet would have drawn wide, passed R311.3,
    and still billed the joist field. The subfloor now reads `deck_outline`; `ceiling_below`
    keeps the framed extent, because a ceiling is nailed to the joists.
  - This entire narrative — `PT-BW-1..4`, `SL-BW-DECK`, and the breezeway-specific numbers
    above — describes the pre-rewrite breezeway structure. It is retired: the north entry is
    now a foundation bridge (`FS-BW-FLOOR`, `FS-BW-GARAGE`), beams `BM-BW-*`, a stair
    `ST-BW-ENTRY`, a railing `RL-BW-ENTRY`, and a slat screen `SC-BW-WEST`. See
    `notes/north_entry_structure.md` for the current structure; a proper rewrite of this log
    section is coming in a separate pass.
- **The garage wall rebuild, 2026-09 — four decisions moved at once.** `GARAGE_WALL_2X6` was
  2x6 @16" o.c. with empty bays and 1.5" Zip-R doing the whole thermal job (owner's choice),
  clad in 26 ga concealed nail-strip. It became 2x6 @24" o.c. / 2" ccSPF in the bays / 5/8"
  CDX / 7/8" corrugated exposed-fastener panel, and the trusses went to 24" o.c. with the
  studs (`GARAGE_ROOF`, framing factor 0.09 -> 0.0625 = 1.5/24; the two must move together or
  the R-38 blow is under-credited). Everything here is an owner choice, not a code minimum:
  `RM-GARAGE` is `conditioned=False`, exempt from `code.energy_prescriptive`,
  `building_science.condensation`, and the MN prescriptive table alike.
  - **The card read R-14.3 and was lying.** With no `CavityFill`, `analysis._layer_rsi`
    billed the 5.5" STRUCTURE layer as SOLID SPF over the full area; the honest whole-wall
    was R-7-8. It reads R-13.2 now — lower on the card, roughly double in the building. The
    shape of the whole change: ccSPF spends about a third of what the cladding and spacing
    save, and buys a real air seal.
  - There is no WRB, and that is a decision (IRC R703.2's exception for an unconditioned
    detached accessory building). The ccSPF is the air/water/vapour plane —
    `TR-CATLIN-GARAGE-OPENING` names `stud-cavity` for all four controls, not the house's
    `sheathing-ext`/`spray-foam-ext` tuple — so bucks before foam, as on the house. The CDX
    carries no `control` set for exactly this reason: bare sheathing claiming those layers
    would be a WRB nobody is buying.
  - There is no furring, and the corrugation IS the rainscreen — 7/8" of continuous open
    flute behind every sheet, more free area than the 3/8" 1x4 the wall carried before. What
    makes that drain rather than pond is the closures, ~192 LF, vented at the base and solid
    at the head. Priced as `[allowances] envelope-garage-corrugated-closure-strips`, not
    through `bug_screen:GARAGE_WALL_2X6` (which reads a rainscreen cavity depth out of the
    layer stack and therefore reads 0 SF). Do not "activate" that row by authoring a 7/8"
    airgap layer — it would add 7/8" on top of the 7/8" cladding and move both wall faces.
  - The whole 24'x24' moved 3/8" north, `GARAGE_GAP_FT` 4.6875 -> 4.71875, always for one
    reason: 3/8" more panel standing proud of the node line is 3/8" less breezeway slot. The
    uncut 4'-0" polycarbonate panel (RETIRED — see the breezeway rewrite note above) kept its
    1/2" reveal at the time. The Zip-R -> CDX swap moved nothing in that chain — the wall's
    `alignment` puts whichever sheathing it carries on the node line — so do not recess the
    sheathing to hold the cladding face still, which re-opens the old rain shelf.
  - No 16" zone at the overhead door, and it was investigated. `W-G-E` is NONBEARING (the
    ridge runs E-W; the trusses bear on `W-G-S`/`W-G-N`) and the 16'-0" opening is carried by
    its own 2-ply 14" LVL on jamb packs the solver sizes from the opening. Field studs beside
    a nonbearing opening carry nothing extra. It would also not be a local override:
    `FramingSpec.spacing` lives on the ASSEMBLY, so a closer-spaced zone is a second assembly
    tag, a second `prices.toml` row, a second `condition_gates` key, and fresh section
    goldens.
  - Three openings re-stationed onto the 24" grid, and one deliberately did not. `WIN-G-N1`
    1'-5" -> 2'-5" and `WIN-G-S1` 21'-5" -> 20'-5" (a 14" RO wants a BAY CENTRE, 12 + 24n
    along `W-G-W`); `SERVICE_DOOR_OFFSET` 5'-10" -> 6'-6", which puts that leaf's centre on
    8'-0" — the same station as `D-M-ENTRY`, so at the time the two doors the breezeway
    spanned were CONCENTRIC and `_GLAZING_CENTER_X` (RETIRED) was simply their shared centre.
    `D-G-OVERHEAD` stays at 4'-0" and its advisory stays suppressed: every legal station
    moves the ICF grade beam and makes the two brick piers 5'-0" and 3'-0".
  - The 16 garage-wall `S-5-N` seam clamps are gone (`plan/wind_clamps.py`), the exact
    precedent of the 48 house-wall `S-5-S` clamps — an N clamp closes on a nail strip's bulb,
    and a corrugated panel has no seam. Corner uplift is carried by the panel's own 640 face
    screws. The `S-5-N` price row stays: the garage ROOF is still nail strip and still
    carries 12.
  - `GARAGE_WALL_WIND_CLAMPS` survives as an empty list, and `standing-seam-nailstrip-26` and
    `zip-r` keep their price rows at 0 — the `glazed-green-brick` convention. The revert is
    layer material refs plus re-authoring sixteen constructors.
- **The overhead door orientation flip, 2026-09-07.** The garage sat with its overhead door
  facing east on `W-G-E` for a lot to the SOUTH with a driveway round the east side — a
  premise that survived in two prose comments and no `Driveway` element, and that had never
  agreed with `plan/site.py`'s own `SetbackSpec(edge=2, "FRONT")` on the NORTH edge or with
  the water service entering from the north. The ridge turned with it (`ridge_direction` "x"
  -> "y", bearing on `W-G-E`/`W-G-W`), the stem gap moved east -> north, both eaves now carry
  gutters and a leader, and the six south-slope snow guards are gone because south is a rake
  and nothing discharges over `GL-BW-ROOF` (RETIRED canopy) any more. The footprint did not
  rotate — the garage is square, the windows stayed on `W-G-W` and `D-G-SERVICE` on `W-G-S`.
  Then it moved 6'-0" east onto the house ridge: garage x 6'-0"..30'-0", centre x=18'-0".
  `GARAGE_X_WEST`/`GARAGE_X_EAST` are published beside the two y lines and the stem, the
  slab, and the landing all derive from them.
  - **The move cost the concentric doors, and the (now-retired) breezeway absorbed it,
    2026-09-09.** `D-G-SERVICE` had to travel with its wall — the move is in 24" steps (a 36"
    RO must land on a stud line measured from the wall's own start) and at x=8'-0" its king
    stud would stand 5/8" inside the corner pack, which owns the first 3 5/8" of wall. Its
    centre became x=10'-0". `D-M-ENTRY` could not follow: its east jamb was already 6" west
    of `N-M-N2` at x=10'-0", the tee where `W-M-STRW`'s bearing stack lands and runs to the
    footings, and a 36" RO cannot straddle it. So the two doors the breezeway spanned were
    2'-0" out of line, so the breezeway straddled them instead of sitting on a shared centre
    that no longer existed: `_EW_FT = 4.5` (RETIRED constant) centred on their midpoint at
    x=9'-0", glazing x 6'-9"..11'-3" (RETIRED glazing). `code.R311_3_exterior_landing` passed
    both doors (entry 90.9%, service 91.7%, bar 85%). 4'-6" was the smallest half-foot module
    clear of the 4'-1 15/32" bare tangent. The instruction not to answer any of this by moving
    the garage back still holds for the current structure.
    - **It cost the brief's E-W term and a heat pump move.** The "8 x 4 x 4" brief was retired
      in E-W and the (now-retired) roof sheet was cut to 4'-6" instead of being an exact half
      sheet (the N-S 4'-0" was still the literal uncut sheet in the 4'-0 1/2" slot). And
      `EQ-M-HP3-OD` moved 2'-4" east, to x 12'-4"..15'-2 3/8": its west face had been at
      x=10'-0", exactly the old east glazing line, and cabinet and glass interpenetrated by
      5/16" at 0 FAIL — nothing grades an Equipment against a deck or a clearance envelope,
      so only hand measurement found it. It now clears the glass by 12 11/16" (Gree's 12"
      lesser-side minimum). `SL-M-HP3PAD` went with it to x 12'-1"..15'-5", which pushed the
      front walk's west edge to x=15'-9" (a zero-clearance cabinet would still have reached
      it, at 14'-4 11/16"). These final positions are current and carry forward past the
      breezeway retirement (see keep8.md).
    - **HP3's y-axis clearances are still short, and that is a deferred owner decision.** Gree
      publishes 12" air inlet and 6'-6" discharge; this position has 8" and 25 11/16". The
      48 1/2" slot can never give more than 33 11/16" front+back to a 14 51/64"-deep cabinet,
      at any position or rotation — the fix is re-siting system 3's outdoor unit out of the
      slot. `params/hp3_pad.py::_BACK_CLEAR_IN` carries the measured numbers and is the only
      record; no check will ever mention it.
  - `EQ-M-HP1-OD` moved 6'-6" east and `ED-M-HP1-DISC` went to the WEST of it. That cabinet's
    whole siting argument is that it stands east of the garage's plan extent; the garage
    moved under it. It now oversails the house's NE corner by 3" to keep its 14" clearance to
    the garage's east gutter face (31'-10" to 36'-0" is 50"; cabinet plus clearance is 53"),
    and its disconnect is a 6 1/2" can in the 14" slot with no NEC 110.26 working space and
    nothing grading it. Both are hard bounds: that machine cannot move further either way on
    this face. `EQ-M-HP3-OD` did not move — it sits south of the garage's roof edge, in the
    48 1/2" slot, which is its documented condition.
  - Aligning `ST-G-SERVICE` under its own landing fixed a standing FAIL. The flight ran
    x 5'..8' under a landing at 6'-6"..9'-6", a stale offset nothing graded;
    `code.R312_1_guard_height`'s unguarded-edge FAIL on `SL-G-STEP-0` went with the fix.
  - `ED-G-SW` / `ED-G-EXT-SW` sit inside `D-G-SERVICE`'s rough opening — a pre-existing defect
    translated faithfully rather than silently re-sited. Nothing grades a wall device against
    an opening; the fix is ~12'-0"/12'-6", east of the real east jamb.
  - `notes/garage_orientation_lot.md` is the whole before/after and the revert recipe,
    including that a genuine south-lot revert must also flip `SetbackSpec` edges 0 and 2,
    which this change deliberately did not touch.
- **The garage wainscot deletion, 2026-09-03.** The garage had no wainscot before this
  entry's date range either — its base skin is the 24" band on the ICF stem, uniform on all
  four walls, and that is a deletion rather than a substitution. A 4'-0" wainscot had stood
  on the two 4'-0" strips of east wall flanking the overhead door, wrapped 4'-0" around each
  of the SE/NE corners — four `W-G-WAIN-*` FoundationWalls on `GARAGE_METAL_WAINSCOT`, six
  local nodes, four cap flashings at a round 4'-0". It was Glen-Gery Columbia Roman Maximus
  soldier brick until 2026-09-02 and PVDF-painted aluminium sheet after. All of it is gone,
  along with `GARAGE_BRICK_WAINSCOT`, `GARAGE_ICF_6_BRICKLEDGE`, `off-white-brick`, and both
  `_BRICKLEDGE` dicts in `params/foundations.py` — deleted outright, not kept unreferenced,
  so git history is the revert path and not a one-line `assembly=` swap.
  - **Nothing replaced it, and the piers lost nothing.** `GARAGE_ICF_6`'s `coil-gap` +
    `coil-ext` band — 2" below grade to the stem top, on a 1/4" vented standoff — always ran
    BEHIND the wainscot, deliberately: that wainscot was a vented, drained rainscreen open at
    its base, so water reached the foam behind it by design. Those two east segments
    therefore keep exactly the protection the other three walls always had. 156.2 SF is
    unchanged by the deletion, which is the check that this was a saving and not a transfer:
    the wainscot's own `[wall_structure]` row (65 SF, $1,430-2,730) and 15.5 LF of cap simply
    left the bill.
  - **The stock sheet stayed 48" x 120" and the gauge stayed 0.040-0.050", and that is the one
    counter-intuitive call here.** With only a ~24" band left, 24" trim coil is the obvious
    buy. It is the wrong one: a 48" sheet rips into exactly two 24" bands with no waste, so
    the heavier architectural sheet costs nothing per SF over coil, and the band is still the
    plow-and-shovel splash zone the gauge was chosen for. There is no backer — the sheet
    spans its fixings and never touches the foam — so dent resistance is gauge and fixing
    spacing, nothing else. Second best, only on a supply failure: 0.024" heavy-gauge 24" trim
    coil, the thickest that product line reaches. Never 0.019", which takes a permanent
    dimple from a shovel corner.
  - **The stem-top Z is new scope, not a leftover of the wainscot.** The band's top and the
    corrugated panel's base both land on the stem top, and until this change that junction
    was modelled by nothing at all — it lived in a `source=` string. `STEM_TOP_Z_FLASHING`
    (`plan/storeys/garage.py`) is six `DRIP_FLASHING` runs, 76.5 LF, broken at both stem gaps
    (the 16'-0" overhead door and the 3'-0" service door, where the stem drops to a grade
    beam and there is no band to flash). `DRIP_FLASHING` is a bent angle — flat leg plus
    outboard turn-down — which is what a Z is; `WRB_COUNTERFLASHING` is a flat pan and would
    not do. The inboard kick-out leg cannot be a second bend on the same run and is carried in
    prose, exactly as the deleted caps carried it.
  - **The Z is authored as one counter-clockwise loop and every run is `back_side="left"`.**
    Walked south W->E, east S->N, north E->W, west N->S, each wall's left-hand normal
    (`normal(d) = (-dy, dx)`) points inboard, so the turn-down hangs outboard on all six.
    Nothing grades `back_side` — get one direction wrong and the drip points at the wall at 0
    FAIL. `test_garage_base_skin_is_the_stem_band_alone_and_its_top_is_flashed` pins it;
    confirm it in the viewer too.
  - **The Z exposed an engine bug and the fix is in `emit/draw/detail_components/eave.py`.**
    `_water_anchor` picked the eave's drip-edge label by plan proximity with no elevation
    filter, so a `flashing` solid 114" below the eave, on the same wall line, was averaged
    into the anchor — the garage's `detail_wall_roof` leader for "drip edge lies ON the top
    deck" pointed at the ground. It now takes only candidates within `_ANCHOR_Z_WINDOW_IN`
    (36") of where the label is expected to land. Generous on purpose: the authored piece and
    the schematic fallback genuinely sit at different elevations, and the window rejects
    another STOREY's flashing, not a few inches of lap order.
  - **Aluminium over aluminium, and no check grades it.** `corrugated-panel-24` above the band
    is 26 ga PVDF-coated steel; the band and the Z are aluminium. They must never lap
    metal-to-metal — sealant or EPDM between, the Z's upper leg behind the corrugated — and
    aluminium must never touch concrete or fresh mortar (alkali strips the oxide film). In a
    salted splash zone that contact line is where the detail fails. Naming
    `aluminum-flat-pvdf` on the Z rather than the envelope's `metal-dark-exterior` steel trim
    coil is the whole enforcement, and it keeps band and Z one colour and one coil order.
  - `OVERHEAD_DOOR_OFFSET`'s 4'-0" lost its defence and is now an open question. The
    `structural.door_framing_module:D-G-OVERHEAD` suppression in `preferences.toml` was
    carried on the wainscot: moving the door 12" would have made its two piers 5'-0" and
    3'-0", a visibly asymmetric facade bought with one stud. That argument is gone — the base
    band is uniform and does not care where the door sits. What remains is a cost of moving,
    not a reason not to: the offset gaps the ICF stem into a grade beam, so the gap nodes,
    two stem segments, their footings, two Z break stations, and a water-service sleeve all
    travel with it. Left suppressed so the report stays clean while it is decided. Do not
    quietly re-decide it either way.
  - `W-GF-S3` / `W-GF-N2` are a kept fossil. Those stem splits exist only because the brick
    returns once needed ledged stem under them. Both halves are plain `GARAGE_ICF_6` and
    nothing stands on them, but un-splitting would churn four wall uids and four footing uids
    to express no geometric change; the census in `test_wall_and_room_counts_by_storey` and
    `test_wall_structure_takeoff` pins the count so a cleanup cannot do it by accident.
- **The garage colour history, and the green machinery kept alive.** `W-G-E` briefly carried
  Western States Metal Roofing "Classic Green"
  (westernstatesmetalroofing.com/classic-green) nail-strip and was reverted; all four garage
  walls are `GARAGE_WALL_2X6` in white today — and that white is `corrugated-panel-24`, not
  the nail strip this paragraph's machinery was built for. The machinery is unchanged and
  still works; the green revert would now be a `corrugated-panel-24`-based colourway, or a
  return to nail strip first. `standing-seam-nailstrip-26-green` is still in the catalog,
  referenced by nothing — the same convention `glazed-green-brick` is kept under, so going
  green again is a one-line `layer_materials=` change rather than a re-derivation. Two things
  were built to make it work, both still live:
  - `Wall.layer_materials` (`model/refs.py::LayerMaterial`) swaps the material of ONE named
    layer on ONE wall. Before it, a colour change *was* a duplicate Assembly restating one
    `material_ref` — and a duplicate assembly tag is also a new `prices.toml` row, a new
    `condition_gates` key, and fresh section goldens, all to say "same wall, different paint".
    It is a TUPLE of constructors, not a mapping, because `Wall` is a movable element and the
    editable dialect has no mapping literal. Appearance only — thickness, function, framing
    and banding all stay the assembly's; a layer that needs a different thickness is a
    different wall and wants its own assembly. A typo in either half is otherwise silent (the
    wall just resolves unchanged), so `integrity.wall_layer_material` FAILs on an unknown
    layer name or material tag.
  - Both renderers hardcoded the coil white and had to stop. Every metal skin authors
    `color="#6b7076"` — that is the drawing hatch tone, not the paint — so the viewer and the
    GLB emitter both painted seam cladding 0xE8E8E2 unconditionally, and no panel could ever
    state its own colour. Both now consult the material's declared `finish` first (the
    mechanism `metal-dark-exterior` already used): `classic-green-seam` -> `#2f5233` in
    `FINISH_BASE` (ui/src/nordic/palette.ts) and `_FINISH_BASE` (emit/gltf/palette.py), kept
    in step BY HAND. The green material keeps "seam" in its tag so it still gets the seam
    normal map, and keeps `skin_family="standing-seam"` so the roof edge still reads the
    garage as one continuous skin.
  - The gable triangle above a wall comes along for free: `resolve/roof_edge.py` builds the
    wall->roof closure from the host wall's own layers, so an override picks up in the
    closure with nothing authored for it.
- **The garage roof edge colour history.** The garage wore "Copper Penny" PVDF metallic here
  from 2026-08-26 to 2026-09-08, and was the one place on the site departing from the house's
  single exterior dark. It no longer is: the garage's own accents are now the Classic Green
  door wall and the Charcoal Gray stem band. `metal-copper-penny` is kept and referenced by
  nothing, the way `metal-fascia-regal-blue` is, so coming back is a one-word swap in the two
  places (fascia + `edge_trim_material`).
  - The fascia's SUBSTRATE changed with the 2026-08-26 colour, and that half must not be
    reverted. The weather face was 5/4 cellular PVC; a dark trim colour on cellular PVC is
    the classic failure — PVC's thermal movement forces a solar-reflective vinyl-safe coating
    and trim makers cap the LRV outright, and `#1c1f24` is further past that cap than the
    metallic was. Formed metal over a wood nailer has neither problem and is the ordinary
    detail on a metal-roofed building.
  - Tag-keyed in the two renderer palettes, not keyed by a declared `finish`: a fascia and a
    ridge cap are framed MEMBERS, and `memberColor` is handed the palette and no catalog, so
    a material's authored `color` is invisible to it and only the tag lookup reaches.
    `_FINISH_BASE` (`emit/gltf/palette.py`) and `FINISH_BASE` (`ui/src/nordic/palette.ts`),
    kept in step by hand. `metal-dark-exterior` already had its rows, so this swap added
    none — and the `metal-copper-penny` rows stay while that material does.
  - Neither tag contains "seam", deliberately: both renderers key the ribbed standing-seam
    finish off that substring and this is flat formed stock. Trim carries no `skin_family`
    either — that field is about the wall/roof continuous-skin reading at a zero-overhang
    edge, and trim is not skin.
- **The garage ICF stem's second face, added 2026-09-02.** `notes/garage_wall_detail_side.md`
  has always asked for protective covering on both sides of the exposed EPS; only the inside
  was built until this date.
  - Inside, `code.R316_4`: a 5/8" gypsum layer banded from the `GRADE` datum up — the 2.5" of
    interior EPS had stood bare from the slab to the stem top, ~176 SF of foam plastic facing
    an occupied space. It continues the board `GARAGE_WALL_2X6` already lines with, so it is
    the same detail, not a new one.
  - Outside, new: `coil-gap` + `coil-ext`, a PVDF-painted aluminium band
    (`aluminum-flat-pvdf`) from 2" below grade to the stem top, on a 1/4" vented standoff,
    fixed with 316 stainless gasketed screws into the ICF webs. 156.2 SF, $781-1,562. Since
    2026-09-03 this is the garage's entire base skin (see the no-wainscot entry above), and
    its top is flashed by `STEM_TOP_Z_FLASHING`.
  - **The standoff is not optional and it is not about drainage.** A painted sheet is 0
    perms. Laid flat on `eps-ext` it is a Class I retarder on the COLD side of the stem, and
    `building_science.condensation` immediately found a January dew point at the concrete —
    a crossing against a monthly MEAN, i.e. a plane that runs wet for weeks. That was a real
    FAIL on the first build of this change, not a modelling artifact. The 1/4" gap restores
    the outward drying path. Delete it and the FAIL comes straight back.
  - It ran BEHIND the east wainscot too, deliberately: that wainscot was a vented, drained
    rainscreen open at its base, so water reached the foam behind it by design and that foam
    needed the same continuous protection as the foam beside it. The wainscot was a wear
    layer over this band, never a substitute for it — which is exactly why deleting it on
    2026-09-03 took nothing away from the two east piers, and why 156.2 SF did not move.
  - Both bands are banded, not full height: below grade there is no interior to separate
    anything from, and the exterior band's 2" of bury seals its own termination rather than
    leaving a lip for water to stand on. The band pushes the stem's exterior face 0.30" east,
    which nicks the "stem and wood wall are coplanar on the outside" promise — inside
    `_axis_match`'s 1/2" and physically true. Do not recess the EPS to hold the face still;
    that re-opens the old rain shelf.
- **`D-G-SERVICE` into the SW corner, and what the move surfaced (2026-09-11).** The door
  sat at x=10'-0" because `garage.py` said a 36" RO "must sit on one of GARAGE_WALL_2X6's 24"
  stud lines" and that 2'-6" was "the MINIMUM this offset can be". Neither was an engine
  rule: `structural.door_framing_module` counts interrupted studs, and the resolved framing
  of `W-G-S` showed the corner pack ending at 6'-3 5/8", a lone stud at 8'-0" and the king at
  8'-3 3/4" — so a RO at 6'-7"..9'-7" interrupts the same single stud and clears the corner by
  3/8". The owner saw the free bay in the 3D view and chose the corner: the flight goes
  against `W-G-W`, the handrail becomes brackets on ordinary blocking, the west guard goes,
  and the exterior landing shrinks to one door jamb (3'-7") instead of covering two offset
  36" patches (5'-6"). Owner calls the same day: 4x4 KDAT posts on 1" ABU44 standoffs, sized
  to reach the beams; handrail on 2x blocking as `WallBacking` bands; no furring band and no
  guard at the stem ledge.
  - **The stem's finished face is 6'-11 5/8", not the 6'-11" the plan assumed.** GARAGE_ICF_6
    carries a 5/8" `gwb-stem` board from grade up, and a stringer authored at the ICF's foam
    face would have stood inside that board along its whole length at 0 FAIL. Everything
    derives from `GARAGE_STEM_INSIDE_X_FT` now.
  - **The gwb board also squeezed the west carrier into the deck's joist grid.** Between
    that board (6'-11 5/8") and `FS-BW-FLOOR`'s second joist (west face 7'-3") there is 3 3/8"
    for a 3" beam; the plan's "2" inside the stem face" put the beam 1/8" into the joist and
    `structural.member_interference` said so. The carrier is sistered to the joist instead,
    3/8" off the board, and a module-level assert keeps its 4x4 post outside the board.
  - **The landing narrowing could not be its own commit.** With the deck still at 11'-6" the
    joist field's 12" o.c. layout puts a joist at 9'-3 3/4", inside the new east carrier at
    9'-4"..9'-7"; only `LANDING_EAST_FT` following the jamb in (so the field ends at 9'-3 1/4"
    with its rim touching the carrier) clears it. The owner's "separate commit" was traded for
    a green tree, deliberately, and recorded here.
  - **The 7 1/4" post gap.** `PT-BW-IC`/`-IE` were authored `height=BEARING_TOP_FT -
    SITE_GRADE` — the PIER top — under carriers whose soffit is `SEAT_TOP_FT`; 6x6 squash
    blocks stopping short of the thing they hold, and nothing in `checks/` grades a post that
    does not reach its beam. `INTERIOR_POST_HEIGHT_FT = SEAT_TOP_FT - SITE_GRADE` (25 3/4").
  - **Their bases take no anchor, and no thickening under them (owner, same day).** The first
    pass gave each a cast-in `AB-058-10-SS` and a "thicken `SL-G-FLOOR` to 10" over a 2'-0"
    square, monolithic" note, and the note's stated reason — punching shear — was not the real
    one. The slab was never close: `deck_post_size` prints 8.1 ft² tributary, which at IRC
    R507.1's 50 psf is ~405 lb per post, ~600 lb with `ST-G-SERVICE`'s top reaction. Under a
    3 1/2" square that is a THIRD the load of one tire of the car that parks on this slab, at
    a LOWER contact pressure, and spread through the 3 1/2" pour it reaches the 1" under-slab
    XPS at roughly 5 psi against a 40 psi board — only ~1 psi of it the sustained dead load
    that creep cares about.

    **What actually wanted the 10" was the bolt.** An `AB-058-10-SS` is 5/8" × 10" and needs
    something like 8" of embedment; the slab is 3 1/2" on foam, so the bolt could not live in
    it and dragged the thickening along to house itself. Dropping the bolt dropped the
    thickening with it. The bases are authored `Connector.anchored=False` — a new field —
    and the joint transfers download by bearing while claiming no uplift and no lateral. Both
    are nil here: the posts stand inside a garage under a landing heavier than any wind on it.
    This is outside ESR-1622's tabulated configuration, which is measured THROUGH the anchor,
    and §5.8 puts the anchor and the concrete support outside the report's own scope, which is
    what makes it the designer's call rather than the report's. Anchor order 6 → 4.

    What is ungraded, and is recorded rather than claimed: with no base anchor these are
    leaning columns, so `RL-BW-GARAGE-E`'s 200 lb guard load reaches ground through the
    landing into the seat beams and down `PT-BW-GW`/`GE`, whose `ABU66SS` bases ARE anchored
    — and no check in this engine follows that path.
  - **Both stainless connectors stopped being "unrated" (2026-09-11).** `ABU66SS` and
    `H2.5ASS` carried `allowable=None`/an empty record on the strength of having read the code
    reports and stopped there: ESR-1622 Table 2 lists no stainless ABU, ESR-2613 no stainless
    H2.5A, and the figures in circulation for the tie were materially LOWER than the carbon
    part's (a 440/75/70 row against 700/110/110). Simpson engineering letter **L-F-SSNAILS**
    resolves both at once, and explains the puzzle rather than overruling it: a stainless
    connector carries the CARBON connector's published allowables, the one mechanism that
    reduces them is that stainless SMOOTH-shank nails withdraw less than carbon ones, and the
    letter's substitution chart recovers full values with Strong-Drive SCNR ring-shank nails.
    **The 440/75/70 row is real — it is the stainless smooth-shank table.** It was the answer
    to a different installation.

    Two conditions ride with it and both are drawing items, because nothing in the model can
    see which fastener was driven. The tie's 700 lbf is conditional on **SSA8D**; every
    fastener at a stainless connector is stainless, the 1/2" through-bolts at the ABU66SS
    included, not only the anchor. And the letter read is `L-F-SSNAILS23`, which states it is
    "valid until 12/31/2024" — 21 months stale, with no later revision retrievable on
    2026-09-11. It is recorded because it is the manufacturer speaking about its own part,
    which is exactly what the old note held out for, but a submittal should re-pull it.
  - **The rail's landing-end bracket landed 1/4" off a stud, in a window bay.** `W-G-W`'s
    studs are 24" o.c. from `N-G-NW`; stud-010 is at y=47'-2 5/8" and the landing edge at
    47'-1 5/8". A backing band there resolved 5 3/4" long — `WIN-G-S1`'s rough-opening
    exclusion clips backing to the far side of that stud — and still missed the station. The
    rail runs 1" past the landing edge onto the stud and needs no blocking there; the foot
    station, 5" from a stud, keeps its 2x12 band (`height` must equal the profile's 11 1/4",
    `integrity.wall_backing_ref`).
  - **`code.R303_8_exterior_stairway_illumination` had been passing on a pantry light.**
    `ED-M-PANTRY-LT`, a wall fixture INSIDE `RM-M-PANTRY`, sat 3'-10" from `ST-BW-ENTRY`'s
    tiers in plan and the rule's 4'-0" ring has no opinion about walls. Moving the tiers 1'-11"
    west dropped it out and produced the first honest reading: no exterior light at the north
    entry at all. `ED-M-ENTRY-LT` (mark R, the garage-door sconce type) on `W-M-N2`'s bay
    centre and `ED-M-ENTRY-SW` on `W-M-STRW`'s mudroom face — inside the dwelling, per
    R303.8.1 — are the fix; the garage's `ED-G-EXT-SW` is the wrong building for it.
  - **Garage switches were 12" above the landing.** `Mount.elevation` on a garage device is
    off `room_floor_elevation` — the slab at -2'-10" — so `inch(46)` resolved to +1'-0"
    absolute against a landing at 0'-0". 80" over the slab is 46" over the landing.
  - **The goldens were 80 scenes stale at HEAD before this change**: `SL-D-NORTH-BRIDGE` had
    been authored without a blessed golden, so every later sheet number was off by one and
    the set-membership assertion masked the content drift. Blessed whole, with that slice's
    cut moved to the door's new centreline (x=8'-1").
  - Pre-existing red tests NOT touched here (all red at HEAD in a detached worktree):
    `test_garage_service_door_opens_onto_the_breezeway_deck_not_the_slab` (looks for the
    retired `SL-G-STEP-0`), `test_stairs_resolve_with_code_risers` (`ST-BW-ENTRY`'s 18"
    going), `test_ifc_emission_when_available` (duplicate GUIDs on `SC-BW-WEST` slats).

## Exterior colour, balcony and veneer

### BLD-02 answered: the cage became a part, and the bar spec became a goal (2026-09-12)

`plans/buildability.md` BLD-02 graded the freestanding sunken-garden concrete HIGH · OWNER
CALL on four findings from outside the model. Two were rebutted and two were acted on. The
owner's read: the engineering already checks out — every court column, wall and pier is a
`draft` record with a published d/c, and the only thing a seal really adds is base fixity,
which is already two named **deferred** items (`column_support/W-SG-W1`/`E1`).

- **Findings 1 and 2 got an answer, not a change.** The permit/stamp cost is BLD-01a's line
  item, not a second scope. And the "cantilevered-column system at R = 1.25" argument does
  not reach this site at all: Minnesota's S_S ≈ 0.04 g / S_1 ≈ 0.02 g puts the lot in
  **SDC A** under ASCE 7 §11.4.2, and §11.7 sends an SDC A structure to §1.4 alone —
  F_x = 0.01 W ≈ **50 lb per column** against the **153 lb** wind shear already carried. No
  R, no 15%-axial limit, no overstrength foundation case. *The mapped values are statewide;
  the lot's own coordinates still have to be run through the ASCE Hazard Tool, and both the
  buildability file and `balcony_moment_columns.md` §9 say so.*
- **Finding 3 was right, and it turned into the win: the cage is now a PART.** Out-to-out of
  ties the authored cage is **8.0"** (6.625" bar circle + 0.625" + 2 × 0.375", i.e. 12" less
  2 × 2" cover) — the trade's "8-inch cage", not the 12-inch cage the finding priced (a 12"
  cage in a 12" column is zero cover; wrong part). The catalog **stock** 8" cage was checked
  and **fails twice**: (4) #4 = 0.80 in² against §10.6.1.1's 1.131 in² floor, and #3 ties @
  12" against §25.7.2.1's 16d_b = 8.0" for a #4. The authored #3 @ 10" is *exactly* 16d_b
  for a #5. So it is a **custom 8" cage in a stock format, one cross-section, TWELVE OFF** —
  the six court columns and the six north-entry pours, which were already carrying the
  identical cage. Cost floor $49–77 (the stock row); budget ~$90–140 each galvanized.
  Rebarfab (New Brighton) or a Bolsinger custom.
- **Finding 4 was exaggerated, and the fix was to restate the GOAL.** "HDG is an unpublished
  special order" is wrong on both routes: **ASTM A1094** (CMC GalvaBar) is stocked and
  **bends after coating**, and the **A767** after-fabrication route has two Minnesota plants
  (AZZ Winsted, AZZ NE Minneapolis). ACI 318-19 §20.2.1.7.2 lists both; ψ_e = 1.0 either
  way. The spec now leads with the **goal** — long-term durability of exposed concrete in
  F3 + C2, which the mix meets on its own at w/cm ≤ 0.40 / 5,000 psi / 6% ± 1.5 air / 2"
  cover — and puts the **ladder** under it: *galvanized either standard (fabricator's
  choice, named on the order) → black bar at the stated cover and mix as a documented
  written exception → epoxy and stainless refused.* Galvanizing is the owner's margin, not a
  code requirement, so the spec can flex on schedule without losing what it was for.
- **In the model, one struct replaced two.** `_CAST_COLUMN_CAGE_HDG` existed only because
  `SUNKEN_GARDEN_COLUMN_12` once carried no `ConcreteSpec` for a coating to live on. It
  carries `EXPOSED_MIX` now, `takeoff/reinforcement.py::_pour_coating` reads
  `bar_coating` from it, and `ENTRY_PIER_CAGE`'s per-bar coating went the same way. **The
  model literal stays `hdg-a767`** — the BOM key (`#5:hdg-a767`) and the BAR COATING line on
  the structural notes are unchanged, `[reinforcement]` is empty, and no pound and no dollar
  moved. The "either" lives in prose; the model states the heavier baseline. All six court
  columns also now spell **one** cage string (`SPEC.corner_column_cage`), because one part
  should read as one part on the drawing.
- **Three of BLD-02's own numbers did not survive verification** and are corrected in place:
  **six** cast columns not four (only the four balcony corners are saddle-collar formed;
  `PT-SG-COL`/`PT-SG-FCOL` are tubes in a hole), **10'-4"** of retained height per
  `sunken_garden_court_free_body.md`, and **twelve** identical cage sections not eight — all
  six north-entry pours share `ENTRY_PIER_CAGE`, not only the two roof columns.
- **Still open: BLD-12.** The belling precondition has no soils report behind it, and it
  gates the two augered piers. It is cited, not folded in.

- **Why `#1c1f24` and not the `#3a3d40` it started at.** An authored colour is
  an albedo. The viewer lights with 0.8 hemisphere + 0.9 key + 0.6 IBL, over
  unit irradiance, so a dark surface leaves the shader well above its albedo —
  `#3a3d40` arrived near `#525252` and read as generic grey.
- A gutter/downspout could only say "I am category gutter" until
  `ResolvedSolid.material` was added, which is why the eaves stayed mill grey
  while the rakes went black.
- The balcony's guards used to be `POST_WHITE_PAINT` too, until it was split
  off as `RAILING_DARK_METAL`. It was six pillars and eight knee braces until
  2026-09-03; the four corners are cast concrete now and the braces are gone
  (see the balcony structure passage below).

- **The balcony's structure: four cast columns, two wood posts, three glulam
  beams** (2026-09-03; `houses/catlin/notes/balcony_moment_columns.md` is the
  design, and it supersedes `superseded/balcony_lateral_bracing_design.md`).
  - The eight 2x6 knee braces and two E-W brace rails the corner columns
    replaced are deleted outright. This was the longest-running open item in
    `plans/TODO.md`, and it closed against metal rather than for concrete: no
    catalog metal moment base survived the search. The only stock base with a
    published base moment is Simpson's MPB66Z, for a WOOD post, and its
    wet-service cap (2,610 lb-ft, ESR-3050 Table A) is *below* the 2,502 lb-ft
    R301.5 guard case on one column before any wind.
  - **12", not 10", and cover is the whole reason.** ACI 318-19 §20.5.1.3's
    1-1/2" is a code minimum, not a hundred-year number; MnDOT uses 2.5-3" in
    the same deicing regime. 2" of cover on a #5 cage inside #3 ties needs a
    6-5/8" bar circle, which needs 12". Centred on a 12" wall the round is
    flush with both faces — no ledge to pond on, and BF3's 3" east leader keeps
    1-1/2" clear.
  - Exposure is class F3 + C2, not F2, and the mix must not be reused from the
    retired 20" column: deicing salt below and planter runoff above is external
    chloride on a freeze-thaw member. Bar is hot-dip galvanized — the owner's
    call over epoxy (delaminates) and stainless (4-6x cost, and an austenitic
    thermal coefficient that fights the concrete).
  - **The beam seat is cast to line, with no grout island**, because an exposed
    non-shrink grout island is a 10-20 year element, not air-entrained and
    sitting at the wettest point on the column. The shim pack (`SS316-SHIM-35`,
    priced at `CN-SG-STDF-*`) is a modelled, priced part since 2026-09-03, one
    per wood-on-concrete beam seat. **That follow-up closed on 2026-09-12, and
    not where it was expected to**: retyping `PT-SG-COL` on 2026-09-10 did not
    close it, it rode the island over to `PT-BW-RE`/`-RNE` at the north entry.
    `PIER_CONCRETE_12` says NO GROUT ISLAND now, and twelve seats house-wide
    carry the pack with none.
  - **The two centre pillars stay wood 6x6**, bearing directly on the porch
    framing through a ~9"-square plank cut-out — Trex says plainly that
    composite decking bears nothing, and the cut has to clear a 5-1/2" post
    plus the `L50Z` angle legs beside it — on a 3-ply bearing pack (the
    authored joist plus two full-length sisters) with squash blocks at the beam
    line. `PT-SG-BF2` moved north onto the deck, which is what let `PT-SG-FCOL`
    shrink from a 20" round to a 12" one, and then the last 3" onto the front
    beam axis itself, where it doubles as the `RL-SG-PORCH` south-leg guard
    post at x 18'-0". A `CCQ46SDS2.5` column cap closes the uplift path at each
    — a 3-1/2" beam on a 6x6 is the unequal-width case the PC6Z is not
    published for.
  - The porch joists crossing both beams since 2026-09-03 takes both bearing
    planes at `PT-SG-BF2` out of NDS §3.10.4's END case (d/c 0.76 -> 0.35)
    without moving the pillar. The composite sheet followed the framing, so the
    plank now ends 2-3/4" outboard of `RL-SG-PORCH`'s guard line — a deliberate
    setback, since the guard blocking sits in the bay north of the beam and a
    guard on the new edge would bolt into cantilevered tips.
  - **No standoff post base at either pillar.** The `ABU66SS` went on
    2026-09-03: every published value an ABU has is measured bearing on
    concrete through a 5/8" cast-in anchor (ESR-1622 §5.6 puts even that anchor
    outside its own scope), and the 1" standoff was cited to IRC R317.1.4,
    which governs wood on concrete. Neither pillar has stood on concrete since.
    Five elements for two pillars, ~$25 the lot, 1,408 lbf at BR2 and 1,033 lbf
    at BF2 wet-derated against a hand-worked ~285 lb net uplift. An inverted
    `CCQ4.62-5.50SDS` cap stood here for one day and could not be built: at BF2
    the rim, joist tips, beam axis and post centre are one line, and at BR2 the
    squash blocks occupy the bays its side plates would hang in — and it was
    ~20x the demand. The bearing that replaced the ABU is graded, oracled in
    `notes/centre_pillar_bearing.md` — at `plies=1` and against a DRY Fc-perp
    both pillars were over, at 0 FAIL, until that calculation existed.
  - **DF-L, not SPF, and the species is a connector requirement.** ESR-2604
    §3.2.2, ESR-2330 §3.2.2, ESR-2105 §3.5.2 and ESR-3096 §3.2.2 are the same
    sentence — SG >= 0.50 at MC <= 19%. At SPF 0.42 nothing at either end of
    these two posts had a published value — the `CCQ46SDS2.5` cap on top
    included. DF-L at 0.50 fixes both ends for ~$180-450 of lumber. The clause
    being family-wide is why that call survived four base parts in one day:
    only the citation moves. Both reports' §4.1 send wet service to the NDS
    factor, so C_M 0.70 is already inside the recorded values — do not derate
    again. A `DTT2Z` stood here for part of 2026-09-03 and was superseded
    unbuilt — one-sided, no lateral value, and it did not touch the species
    problem.
  - The three beams are engineered items (`deck_beam/BM-SG-BL*`) because
    R507.5(1) publishes sawn plies only.
  - **The front row did not move when the corners changed.** A 12" column's top
    runs 3-1/4" past the beam end there, and that is a concrete top with a wash
    and a drip lip, not the exposed end grain the 2-3/4" offset was written
    for. Re-solving the row would move the deck edge, the fascia, the drip, the
    gutter and `BALCONY_FRONT_AXIS_Y_FT`.
  - **The fallback, written down:** New Castle Steel's stock HDG 6x6x3/16" post
    with a welded base plate (~$458/10') if forming and caging four tall tubes
    proves too much labour. Its base still needs a fabricated saddle on a 12"
    wall top, which is a shop drawing nobody has made.

- **Guards.** Williams Architectural Products, ICC-ES ESR-3485, 42" black
  (Menards; Eagan MN, the Ultralox factory), with Fortress Al13 Home as the
  alternate — the same alloys and coating as Trex Signature at ~$30-45/LF
  material against $72-98.
  - `RL-SG-PORCH`'s west and east legs run along 12" concrete wall tops, which
    take ESR-3485's four 1/4" x 3" baseplate anchors directly and buy no
    bracket kit. Its south leg has no wall under it, so those posts bolt
    through the plank into blocking in the joist bay north of the beam — never
    through `TR-SG-CAP-FRW/FRE` and its butyl, which is the dielectric between
    an aluminium cap and copper-treated framing.
  - `RL-SG-BALCONY` staying fascia-mounted is a roofing decision:
    `FS-SG-DECK`'s aluminium plank is the porch roof and has carried no
    penetrations since the heat pumps went to grade; surface posts would put
    ~36 holes through the only waterproof plane here. Brackets through-bolt the
    PVC fascia and the 2x8 rim per Ultralox's own instructions (four 5/16" x 4"
    bolts, nuts on the rim's inside face), landing in rim blocking authored in
    `FS-SG-DECK.reinforcements`.

- **The veneer stands on a grade beam, not on the house footing** (2026-09-05).
  `W-B-BRICK` is 129 SF of masonry exposed on both faces at the bottom of an
  open court, so it runs at outdoor temperature all winter. It used to bear on
  `FT-B-BRICK`, a 10"x5" plinth cast on `FT-B-S2`/`FT-B-S3`'s own projecting
  toe — putting that cold in series with the footings whose underside is level
  with the court floor and whose only frost protection is the R403.3 wings. It
  now bears on `W-SG-BRKBM`, a 12" x 17-3/4" beam spanning the court's 19'-0"
  between `W-SG-W1` and `W-SG-E1`. Basis: `notes/sunken_garden_veneer_beam.md`.
  - **The break was ordered twice and placed never, and that is the lesson.**
    `FT-B-BRICK` carried `assembly="FOOTING_FPSF_20"`, whose 2" `xps-bearing`
    layer *did* bill — 16.0 SF through `takeoff/envelope.py`'s
    `_LAYERED_SOLID_SCOPES` — while `FB-B-BRICK` dug a 2" `undercut` for that
    same 2" of space which billed as 0.1 cy of washed crushed stone, with
    `cast_foam_in_aggregate=True` beside it carrying no thickness, no material
    and no R-value. A `Footing` resolves to ONE extruded blob, so neither claim
    ever had a polygon. One order of foam and one order of stone for one gap
    sat at 0 FAIL for a fortnight.
  - **A better bed was not available — the geometry says so.** The wythe sits
    inside the footings' 10" toe, and any separate pour bearing on soil has to
    stay outside the 45° line off their bearing edge, at y = -12.76". That
    pushes the brick to -15.95" and opens an 11.9" slot to the house: a
    19-ft-long, 11.5-ft-deep snow trap with no way to reach the bottom. A beam
    that spans needs no soil bearing, so that constraint does not apply — which
    is the whole reason this shape was chosen and the reason the gap can be 6".
  - **It reinforces nothing, and do not let anyone say it does.** The tempting
    story is that a beam closing the court's north end props the side walls. It
    does not: `W-SG-W1`/`E1` are already restrained top and bottom (porch beams
    pocketed in HUCQ410-SDS hangers, the deck diaphragm, the garden slab at
    their feet) and PASS `structural.foundation_unbalanced_fill` on the last
    published row of IRC Table R404.1.2(8). This beam earns its ~1.05 cy on the
    thermal argument alone.
  - **The 2" board is a `Layer`, on a wall, and the face is asserted.** A
    wall's layers resolve to real polygons on real faces in a stated order,
    which a Footing's do not — that is the whole reason it moved here. The face
    is not reliable on its own: the beam is its own open wall-graph chain, so
    it takes the fallback outward sign, and sign x layer-order decides whether
    the board builds north or south. Authored the wrong way the concrete lands
    hard against `FT-B-S2/S3` and looks perfect in every view.
  - **`FT-B-S2`/`FT-B-S3` gave up 2" of south toe, by `offset` and not by
    width.** The strips keep all 20" of bearing and simply sit further under
    the house; since they carry a 7-1/4" curb and three storeys of framed wall
    standing at y = 0..+9-1/2", moving toward the load *reduces* the
    eccentricity they already had.
  - **The wythe moved 4-1/2" south and the reveals did not move at all.** On
    2026-09-04 the 6" was taken entirely in `BASEMENT_BRICK_VENEER`'s `air-gap`
    thickness with the nodes held still; on 2026-09-05 the EPS moved the
    backup's face and `N-B-BRICK-W`/`-E` followed it to -8.05" while `air-gap`
    came down to 2", the opposite bookkeeping. Either way the invariant is the
    brick's own y, which the beam fixes. The reveals are safe under both
    because `AO-B-BRICK-WIN`/`-DOOR` are placed `from_node` along the wall axis
    — a y-move leaves them concentric and `integrity.reveal_concentric` still
    passes. `N-B-BRICK-E` did have to come in from 28'-0" to 27'-6": 28'-0" is
    `W-SG-E1`'s axis, and the move walked the wythe's east 6" *inside* that
    retaining wall — 4.25 SF of brick billed into solid concrete, at 0 FAIL,
    because nothing grades masonry against a pour.
  - **2" of EPS went into that cavity 2026-09-05, and it is on the backup wall,
    not in `BASEMENT_BRICK_VENEER`.** The 6" is fixed — the beam's north face
    cannot pass -10" — so the only question was how to split it, and it is now
    2" EPS + 4" of drained air. The foam is a layer of
    `_GARDEN_CURB_CORE`/`_GARDEN_FRAMED_OUTBOARD`, the two outboard tuples the
    four backup walls share and nothing else uses, so the blast radius is
    exactly those four walls. Putting it in the veneer's own stack would have
    been worse than untidy: `code.energy_prescriptive` grades one assembly at a
    time, so foam parked there earns the wall no R and the check keeps reading
    R-37.0. It reads R-45.0 now (R-58.4 sauna, R-29.3/R-43.3 curbs), each
    exactly +8.0.
    - **The energy is a rounding error and is not the reason.** The backup was
      already R-37/R-50 framed, not the R-21.5 a `BASEMENT_8` reading suggests
      — about $2/year at 124.9 SF. The $250-487 buys a *designable anchor*: the
      beam already forced a ~10" brick-to-stud reach, and 6" of that was
      unbraced air. Now 6" is foam and 4" is cavity. The anchor is still
      engineered — see the note, §5.1.
    - **EPS and not more XPS, deliberately.** The stack is already 4" XPS plus
      the 60-mil self-adhered membrane at 0.05 perm and can only dry inward
      (the "~0.13 perm" this entry claimed until 2026-09-12 was a guess about a
      layer that was in fact modelled as 54-perm housewrap); EPS at ~2 perms over
      2" adds R without adding a second vapour shutter and lets the wall dry
      out into the vented cavity. It also beats XPS in long-term ground
      contact, and this run's foot is in a court that can pond.
    - **`IRC R703.15`'s 4" foam limit does not govern here, and the trap is
      real**, because `plans/cost-options.md` §6 kills a different foam swap in
      this house on exactly that limit — and this wall now carries 6". R703.15
      covers cladding whose dead weight hangs on a fastener in bending, and it
      explicitly excepts anchored masonry veneer to R703.8. This wythe stands
      on the beam; its anchors take wind only.
    - **2" and not 4", and nothing graded either bound.** 4" was built first
      and sat at 0 FAIL. It was wrong twice over. (a) `EXT_2X6` stands on this
      wall's seat with its cladding face at -7.25"; 4" put the basement's face
      at -8.05", 0.8" proud of the wall above, turning the Z-flashing lap that
      the basement skin is supposed to tuck under into an upward-facing ledge.
      2" lands at -6.05", a 1.2" setback. (b) `resolve/stacking.py` fires
      `stack_width_change` on |total thickness| against a 0.5" `_TOL`, so any
      thickness added here reshuffles which junctions get a detail drawn: 4"
      pushed `GARDEN_CURB_6` inside the tolerance and 3" pushed
      `GARDEN_FRAMED_2X6` inside it, each silently deleting a live junction's
      drawing. 2" is the only purely additive value — every HEAD golden
      survives and the two sauna walls gain the detail they now warrant. The
      golden SET drift is what caught this; no check did.
    - **`eps:2.0` is a new price key, for labour not thickness.** 2" is what
      the bare `eps` row was already researched at, so the material rate
      carries across untouched; what does not is open-wall CI labour. This
      board is set in a slot behind a wythe laid after it, held by the veneer
      anchors, its bottom course worked out of an 11-1/2 ft hole: $1.10-2.10.
  - **Do not anchor the wythe to `W-SG-W1`/`W-SG-E1` to cut the anchor count.**
    It cannot carry: unreinforced 3-5/8" brick spanning 18'-8" horizontally
    runs ~400 psi of flexural tension at 20 psf against ~50 psi allowable
    parallel to the bed joints. And it is the wrong detail regardless — brick
    grows, concrete shrinks, and BIA TN 18 puts ~0.15" of movement across that
    run. Those two ends want a soft joint, not an anchor.
  - **Two engine bugs fell out of this and are fixed.**
    `local_grade_elevation_m` sheltered a footing whose CENTROID sat inside the
    heated slab, so trimming a perimeter toe 2" walked it over the line and
    turned 3/4" of frost cover into a reported 83" — whole-polygon containment
    now. And `_exterior_shells_by_storey` filled every interior ring, which was
    invisible only while the court was a *disjoint* polygon; the beam connects
    it to the house, and 610 sf of open sky became basement floor area until
    holes over an open excavation floor were kept.


## Sunken garden court

### The two centre pillars came back down onto concrete, and a register entry closed (2026-09-14)

`haus engineering houses/catlin` listed `post_bearing/PT-SG-BF2` and `post_bearing/PT-SG-BR2`
— wood-on-wood Fc-perp crushing under a 6x6 carrying a third of a balcony. The question was
real, the calculation was right, and **the question only existed because the pillars stood on
framing**. `engineering/post_bearing.py` enumerates on exactly one predicate — a `Post` whose
`supported_by` names a `FloorSystem` — so both records leave the moment those two name a post
instead. Register 37 → 35, and `structural.deck_post_bearing` now reports NOT_APPLICABLE,
earned: "37 post(s) resolve, all of them on a pad, a footing, a wall, or inside one".

**This reverses the 2026-09-03 decision, and the thing that makes it affordable is the
hangers.** That entry moved `PT-SG-BF2` off `PT-SG-FCOL`'s top because standing on the column
made the pillar 19 1/2" longer than its five neighbours and forced that column to a 20" round
— one pour had to span from the beams' north face to the pillar's south face. It does not have
to any more: **the four porch beams hang off the pillars' east and west faces** on `HU212-3`
face-mount hangers instead of being seated beside them, so each column carries a pillar and
nothing else and both stay 12" round. `HU212-3` rather than `HUC212-3` — the HUC is the
concrete part, its published loads are Titen-into-a-pour loads, and its one advantage is a
concealed flange a 5 1/2" post has nowhere to host.

`PT-SG-BR2` moved 3" north onto the column axis with it. Its `_REAR_PILLAR_SOUTH_OF_COL_IN`
offset bought one thing — keeping a deck-borne pillar out of `cantilever.py::_band`'s epsilon
— and that pillar is not deck-borne any more. What the offset would have COST on concrete is
real: a 5 1/2" post centred 3" off a 12" round puts two corners 3/8" outside the pour.

Three things had to be built for it, and each is a fact the model did not hold before:

* **A framed chase at each pillar.** `FO-SG-BF2`/`-BR2`, 9" square, `CHASE`: the joist line at
  x=17'-10" is cut and headed, and the post passes up through it. (This said "headed off the
  two lines 16" either side" until 2026-09-15. The resolver frames the authored opening's own
  edges, so the trimmers stand at 17'-7 1/2"/18'-4 1/2" and each bears 4 1/2" on the beam
  below — a sleeve on the beam, which is the better detail and the reason the opening was not
  widened to match the sentence.) **No hanger on the post's north or south faces** — four connectors will not fit on a
  5 1/2" face, and the two beams already have the east and west. The porch joists' south
  oversail went 2 3/4" → 4 1/4" so the front rim band clears the pillar it used to run through.
* **A post is the WOOD, not the clear distance between its bearings.** `StructuralHardware`
  gained `bearing_standoff_in` / `seat_thickness_in` and `resolve/envelope.py::_resolve_post`
  insets the member from the parts a plan authors on it: the `ABU66SS`'s 1 3/16" standoff
  (Simpson's published 1" over the stirrup's own 7 ga base plate) off the bottom, the
  `CCQ46SDS2.5`'s 7 ga seat off the top. That is 1 3/8" a mill does not cut, a take-off should
  not bill and IRC Table R507.4 does not cap. It moves every ABU-based post in the house.
* **The drainage fall became the authored number.** `SPEC.rear_pillar_rise_in = 2.0` is retired
  for `SPEC.balcony_fall_in_per_ft = 0.25` — 1/4" per foot, the trade standard for a walking
  deck and twice AridDek's published minimum, where the flat 2" worked out to 0.27 in/ft over
  this run. A slope survives a bearing row moving; a rise does not.

**What the change buys is a PRESCRIPTIVE read, not silence.** Both pillars are now graded by
`structural.deck_post_size` against IRC Table R507.4 — a 6x6 at 48.3 ft² tributary, capped at
10'-0" — and pass at 9.99' and 9.83'. `PT-SG-BR2` has **5/32"**, so raising the fall again
spends it at 1/64" of post per 1/64 in/ft. catlin holds 0 FAIL.

The deck-borne arrangement is kept in place and referenced by nothing, the `EXT_2X6_SWINBURNE`
convention: `_DECK_BORNE_PILLAR_BEARINGS`, `_DECK_BORNE_PILLAR_REINFORCEMENTS` (the two 3-ply
packs) and `_DECK_BORNE_BASE_TIE` (the five-part `MSTA12Z` + `L50Z` tie). The 2026-09-03 block
above them is verbatim. `notes/centre_pillar_bearing.md` stays on disk and un-archived — a
registered kind must name a live note, and the arithmetic is what the check would use the day
a post stands on framing again; `notes/balcony_differential_movement.md` §6 is voided, because
its cross-grain shrinkage argument has no cross-grain path left.

**First pass — the court went back to one flush surface (2026-09-05).** It had been dropped
7 1/4" on 2026-09-03 as a flood step, which put four elevations into a 19' court: the court
itself, a 23.7 sf stoop a riser above it, `W-SG-ARCH` standing 3 3/4" proud as a mow strip,
and the veneer beam. The owner called it back to one flush plane.

- The trade taken: water now climbs 7 1/4" to the threshold instead of 14 1/2" — 298 cf of
  ponding over the court rather than 597, against ~177 cf of direct 100-year/24-hour rain, so
  about 1.7x where it had been 3.4x with the drywell assumed fully failed. (All three volumes
  scale with the court's plan area and fell when it shortened to 26'-0" on 2026-09-10; the
  1.7x and the 3.4x do not move, because both terms of each scale together.) The case to watch
  is not summer rain but snowmelt over a frozen grate, where `DRW-SG-MAIN` contributes
  nothing by definition — the 7 1/4" curb is the entire dam.
- 7 1/4" was not a preference; it was the ceiling. R311.3.2 allows one riser of 7 3/4"
  (`_MAX_NONREQUIRED_STEP_DOWN`) at a non-required, inward-swinging door. A lower court needs
  a landing — which is exactly what `SL-SG-STOOP` had been, for two days, before it was
  retired (uid `SGS503AAAA`, never reuse). `code.R311_3_exterior_landing` now reads
  "D-B-PATIO lands on SL-SG-FLOOR, 7.3" below the threshold".
- `W-SG-ARCH` did not move: it carries Pu 62,051 lb and closes the walls' loop before
  backfill, and dropping its top to the rim underside gives phi-Pn 60,712, d/c 1.02. Its top
  and `_rim_underside_in` are now the same expression, so the rim bears on it, and
  `FO-SG-ARCH` retired along with the stoop. `W-SG-BRKBM`, by contrast, carries nothing
  structural — it is the veneer's thermal foundation only.
- Two values had been pinned rather than left to follow the court up; one was un-pinned.
  - `_pier_bell_bottom_ft` was pinned for a day, then made derived again (owner's call, later
    the same day, 2026-09-05): `(_court_top_in - frost_depth_in) / 12`, giving both bells 42"
    of cover rather than the 49 1/4" the pin had left them with. The pin's argument — saving
    0.1 cy of shaft against re-opening every hand-worked term in
    `notes/sunken_garden_piers.md` — was real but was overruled: a pinned literal is exactly
    what silently drifts the next time the court moves, which is how it reached 49 1/4" in the
    first place. The note and both pier test modules were reworked; shafts came back to
    128.1875", what they had been before the flood step.
  - `_veneer_beam_bottom` had been the garden slab's underside — flush, that gives a 10 1/2"
    beam over a 19'-0" span, under ACI 318-19 Table 9.3.1.1's L/16 = 14 1/4" minimum depth.
    It was held instead at -120 3/16" so the graded 17 3/4" section survives; the beam is
    simply buried. This one stays held.
- Frost got quietly better: `FT-B-S2`/`S3`'s cover below `SL-SG-FLOOR` went from 1" to 8". The
  R403.3 wings still do the work, but no longer on a fingernail.
- `plan/site.py`'s two garden spot elevations had to follow, -9'-8 11/16" → -9'-1 7/16". The
  comment beside them claiming "nothing structural reads spot elevations — they are drafting
  annotation" was false: `engineering/balcony_wind.ground_below_ft` takes the lowest spot on
  the site, and these two win it, setting `z` for the balcony columns (h 23.3' → 22.7', q_h
  18.8 → 18.6 psf, wind base moment 1,395 → 1,385 lb-ft). Safe direction, no column resized,
  and the 2,502 lb-ft guard case governs regardless — but `notes/balcony_moment_columns.md`
  and `test_pier_calcs`'s schedule both had to move with it.
- A latent bug in `space_summary` surfaced here: the interior-hole filter added 2026-09-04
  kept a ring only if it `contains(floor.representative_point())` — one point per floor — so
  a floor spanning several rings anchored only one. `W-SG-ARCH` splits the court into two
  bays, both `SL-SG-FLOOR`, and the retired stoop happened to anchor the second bay;
  retiring it dropped 281 sf of open court onto the basement's gross area. Fixed by making it
  an area-overlap test, which asks the question actually meant.

**Second pass — the porch side joins the lift, the run caps at 36" above grade, and the well
ties to the footings that feed it (2026-09-05, after the re-levelling above).** Four separate
defects, all found by looking at the model rather than by any check — none had been a FAIL,
and none could have been.

- `SPEC.retaining_top_ft` is now derived from grade, `(site_grade_in + 36)/12` = +0'-2". It
  had been +0'-6", i.e. 40" out of the -2'-10" yard. One constant does two jobs, because
  `params/raised_garden.py` reads it through `RETAINING_WALL_TOP_FT` as its apron TOP and
  derives BASE as `TOP - drop_ft`: capping the top at 36" lands the SRW base on -34", site
  grade exactly, where it used to float 4" in the air. Nothing grades a freestanding wall's
  base against the ground plane, so five `W-RG-*` legs had stood on nothing at 0 FAIL while
  the comment beside them claimed "their base is grade".
- `W-SG-W1`/`E1` now bottom on `_wall_bottom` like everything else, and
  `_PORCH_FOOTING_THICKNESS_IN` is gone. They had been held back when the three retaining
  strips rose, to keep IRC Table R404.1.2(8)'s last published row (10'-0") and to stop the
  two 13"-thick footings' undersides moving. Both arguments turned out weaker than they
  looked: 10'-0" is a ceiling, not a target — a shorter braced wall over less fill sits
  further inside the same row, and the check still passes at 9'-1 7/16" — and the frost
  answer at this edge was never cover but ASCE 32 soil replacement, the same 42" of stone
  whatever elevation the footing starts at. Holding them had left the whole under-porch dig
  9" deeper than the identical stack ten feet south, for nothing.
  - `FO-SG-TOE-N-W`/`-N-E` void the rim over them, as `W`/`E`/`S` do over the other three.
  - `FO-SG-TOE-W`/`-E` had been cut to the field's north edge while the footings ran 6" past
    it, leaving each a 4'-0" x 0'-6" tongue of footing under 3 1/2" of rim — 2.0 sf of
    concrete billed twice and cast into itself, at 0 FAIL, because
    `structural.concrete_interference` grades only ISOLATED pours and every `FT-SG-*` carries
    `under=`. The toes are now cut to `_y_ax_mid`. The assertion kept: the net rim polygon's
    intersection with every `FT-SG-*` footprint is 0.000 sf.
- `DRW-SG-MAIN` now sits on the wall beds again, with two lead runs making the tie visible.
  The well's top had been pinned to the deepest bed, correct while every bed shared one
  underside; after the lift it left the five tiles that actually feed it discharging 9" above
  the top of the stone, into undisturbed clay. `drainage.discharge_consistency` resolves the
  tag and never asks where the pipe goes, so it passed anyway. `_SG_DRYWELL_TOP` is now
  `_SG_WALL_BED_BOTTOM`, and `FD-SG-LEAD-W`/`-E` carry the ring across the 3'-0" of open
  ground into the well at that invert — two leads, not seven, because the five wall beds abut
  into one connected body of stone (W1 to W2 at y = -11.0', W2 to S through the corner lap,
  mirrored east). `FB-SG-ARCH` takes none: its bed bottoms 9" below the well and stops 2"
  from the shaft in plan, so it feeds the column through its side and a lead there would run
  uphill.
- The dowels had been above the footing they dowel into: `_dowel_z` read
  `-(basement_depth + 0.75) + footing_thickness/24` — mid-height of a garden footing whose
  underside was -118 7/16", two elevation changes prior. The bars resolved at -112 7/16" with
  the garden footing's top at -117 7/16": three #5 GFRP bars sitting 5" of open air above the
  concrete they were meant to develop into, and a 12" foam block straddling a joint that was
  not there. Nothing grades a `Dowel` against the two footings it names. Now derived off the
  joint instead — mid-way through the 8" face the two footings actually share, with the foam
  block that same 8" so it fills the joint instead of standing proud into the slab bed.
- What it was worth: 2.32 cy of concrete (151.10 → 148.78) and 9" off the whole under-porch
  excavation and the well shaft. Every yard of it had been concrete poured on top of
  something. The engineering all moved the safe way: stem 9.62' → 9.2865', system FS 1.71 →
  1.77, stem flexure 0.72 → 0.65, toe flexure 0.61 → 0.56.
  `notes/sunken_garden_court_free_body.md` §4/§6/§7 were reworked term by term rather than
  recomputed from the engine.

**Third pass — the closure's thermal break was 21" long in an 84" joint (2026-09-05).** The
two porch side walls meet the house only through a 2" XPS board on -6 3/16"..-4 3/16", and
the intent written at `DW-SG-*-STEM` was one continuous board from the house footing's
underside to the top of the porch wall. It was not continuous, in two independent ways that
hid each other, and nothing in the engine grades a thermal break for continuity, so it had
read as a designed detail at 0 FAIL.

- The block had been sized against the wall, not the footing. `_resolve_dowel` derives a foam
  block's length along the joint from the bar row — `max(row_span + 8*dia, 12")` — exactly
  right for the stem block (12", flush with a 12" wall's end face) but wrong for the footing
  block, which separates an 84"-wide strip. Three bars at 8" gave 21", leaving 63" of
  footing-to-footing concrete running from a heated basement footing into a wall standing in
  an open court. `Dowel.foam_length` is new for this: unset, it derives as before, so nothing
  else in the repo moved. The two blocks are deliberately not unified — they are sized
  against different pours.
- Where the board was missing there had been no room for it. `FT-SG-W1`'s 84" north end faces
  `FT-B-S1` over its outer 52" and `FT-B-S2` over its inner 32". S1/S4 took a 6" toe trim on
  2026-09-05 and cleared it by 2 3/16"; S2/S3 kept the 2" `offset` bought for `W-SG-BRKBM`'s
  isolation board and lapped it by 1 13/16" of solid concrete — a plan lap until the porch
  footings rose to the court plane, a real 0.406 sf x 8" volume after. Which strip a given
  inch of that joint faces had been an accident of where `W-B-S1` stops at x = 8'-10"; no
  thermal detail should turn on that. All four south strips are now on one face at -4",
  `_TOE_TRIMMED` is empty and `_SOUTH_TOE_TRIM` is superseded.
- The beam's own board was not weakened by the retreat: it still separates the veneer pour
  from the house pour across 4" of bedding stone in series with the same 2" of XPS, and
  `W-SG-BRKBM` bears nothing on that toe — it spans between the side walls. What the 2" was
  genuinely load-bearing for is the beam's north face at -10", a fact about the beam that did
  not move.
- Frost was re-checked after the trim, because moving a footing north is exactly how a false
  pass gets bought: all four still read "8" below SL-SG-FLOOR" on the R403.3 branch, not the
  ~86" `sheltered_by` answer. `test_the_veneer_beam_isolates_the_house_footing` now pins the
  84" board, the full 8" depth, and a zero plan lap against every house strip — both halves,
  because each had passed on its own while the pair was broken.
- `prices.toml`'s `thermal_break` row was rebased with it: it had priced three ~0.3 SF
  structural bearing pads that no longer exist, and now bills the four closure boards
  (27.6 SF of 2" 40 psi XPS) at $90-210 each. The four are not the same size, so check totals
  against SF rather than count.
- Concrete did not move for any of this — worth knowing before reading a takeoff diff across
  this date: the toe trim is an `offset`, so each strip slides north with its full 20" of
  bearing intact. Measured by ablation against HEAD, every assembly row was identical, total
  149.31 cy either way, with the thermal break the only quantity that changed, 3.43 → 4.60 cf.
  Any concrete delta seen across this date belongs to another change, not this one.

**The court, the columns and the garden blocks are washed white (2026-09-13).** The sunken
garden is a light well: a U of 12" as-cast concrete walls enclosing the only thing the basement's
south glazing looks at. Bare grey concrete has a diffuse reflectance of roughly 23-35%, so most of
the daylight that reached the court was absorbed there rather than delivered inside. Every
interior face of the court now carries two coats of an untinted white mineral silicate wash, for
three purposes: **daylight into the basement** (a 3-4x increase in the bounced component reaching
the south glazing, and a softer bounce when the sun is high and off-axis); **light into the south
yard**, where the raised-garden terrace's SRW blocks get the wash on their outboard face to bounce
light down onto a lawn that is only partially sunny; and **appearance** — the court already carries
white-painted wood (`POST_WHITE_PAINT_DF`, `BEAM_WHITE_PAINT`) and the house a white metal skin, so
the wash unifies the concrete with them. `SUNKEN_GARDEN_COLUMN_12.source` had already contemplated
exactly this: "optional mineral paint to match the white centre posts".

- **The brief said "high SRI" and SRI is the wrong metric.** SRI (ASTM E1980) blends solar
  reflectance with thermal emittance to predict how hot a *roof* gets — a heat-island number, not
  this. The two that govern here are **LRV / diffuse visible reflectance** for daylighting and
  **broadband solar/PAR reflectance** for the planting. They track together for an untinted white,
  so the product choice is unaffected; what matters is that the finish stays **matte**, so the
  reflection is diffuse rather than a specular hot spot. Both Beeck products publish "dull matte"
  at 85° (EN ISO 2813) and Romabio publishes <5 gloss, so all three candidates clear that. High
  albedo also keeps the wall itself cooler, which is the right outcome for anything planted
  against it.
- **Product comparison, and why the substrate decided it.**

  | | Beeckosil C-102 White | Romabio Masonry Flat | Beecko-SOL |
  |---|---|---|---|
  | binder | unmodified potassium silicate, VOB/C DIN 18363 2.4.1, pure potassium water glass | D-SILICATE **modified with an organic dispersion** — not 2.4.1 | silica-sol modified silicate emulsion, still 2.4.1, <5% organic |
  | substrate | raw, absorbent, mineral; **no primer** if so | **MicroGrip primer REQUIRED on concrete and concrete block** | tolerates "critical, semi-water repellent and synthetic-resin coated" facades |
  | coverage | 200-275 sf/gal/coat on cast concrete of average texture, 150-200 on split-face/heavy texture | 200-260 | 300-350 |
  | LRV | **90** (C-101 Off-White is 60) | not published | not published |
  | permeance | 75-85 perms ASTM E96; s_d 0.01-0.02 m | — | 75-85 perms; s_d 0.01 m, class V1 |

  The owner's own constraint — an **untreated** substrate — is what chose Beeckosil for the cast
  concrete: Romabio requires MicroGrip on poured concrete and block, which fails that constraint
  outright. Note Beeckosil's TDS publishes a *different* headline coverage (300-350) for smooth,
  normally-absorbent substrate; the 200-275 figure is the substrate-specific one and is what
  as-cast and SRW actually are.
- **The permeance derivation, and the number that was nearly authored instead.** The first pass was
  going to convert EN 1062-1's class threshold: class **V1** ("high") is s_d < 0.14 m, and with
  s_d = δ_air/W, δ_air ≈ 2e-10 kg/(m·s·Pa) and 1 US perm = 5.72e-11 kg/(m²·s·Pa), that threshold is
  W ≈ **25 perms**. That is the class FLOOR, not this product, and it would have understated the
  film by more than 3x. Both TDS in fact publish **75-85 perms by ASTM E96**, and s_d 0.01-0.02 m —
  an order below the class limit. `library/materials.py` authors **80.0**, the published range's
  midpoint, per the file's own stated convention. The two published figures do not reconcile with
  each other (s_d 0.01-0.02 m computes to ~175-350 perms); that is different methods and cup
  conditions, it is recorded in `source` rather than averaged away, and the ASTM number wins
  because it is the test this field's unit is defined by. At 80 perms this becomes the most
  vapour-open material in the library (`air-barrier` is 54, `latex-paint` 5.0), which is the right
  ordering for a non-film-forming mineral coating — and it must never carry `ControlLayer.VAPOR`.
- **Reflector ranking, for the record.** A wall bounces light onto the ground in front of it, so of
  the three raised-garden perimeter legs the south leg `W-RG-BLOCK` (28', facing south over the
  yard) does most of the work; the east and west legs each catch half a day. All three are in
  scope, but that is the order if the scope is ever cut.
- **The winding diagnosis, which was the real risk in the whole change.** A layer's side is
  derived, not authored: `resolve/topology.py` places layer 0 on the `-outward_sign * normal(start
  →end)` side. `params/sunken_garden.py` claimed the court component had lost its only closed loop
  when the arched cross-wall was retired and so took `UNRECOVERABLE_WINDING_OUTWARD_SIGN` (+1),
  latent "ONLY because every `SUNKEN_GARDEN_WALL` is one centred concrete layer" — and a wash layer
  is exactly the second layer that would end that. **The claim was stale.** `W-SG-ARCH` is a live
  `FoundationWall` on the N-SG-MW/N-SG-ME pair, so the walk ME→SE→SW→MW→ME closes and
  `resolve_storey_windings(plan, "court-low")` resolves the component to **-1.0** — the value the
  comment said it wanted. (Walks from the other nodes escape up the dangling W1/E1 legs and never
  close, which is presumably how the stale reading arose; and the storey is `court-low`, not
  `basement`, which is the other thing the old note got wrong.) With -1, layer 0 lands on the
  +normal side, and that is the court face for **all five** walls — the consistency
  `params/sunken_garden.py` means by "both side walls wind the same way around the garden". No
  engine change was needed and `resolve/orientation.py` was not touched.
  - The raised garden is the genuine unrecoverable case and it is **not** a bug. Its graph is
    `WB–NW–SW–SE–NE–EB`, an open chain with no cycle (the U is open to the north and there is no
    north wall), so `_closed_walks` returns empty and the sign really is +1. With +1, layer 0 lands
    on the -normal side, which for the three perimeter legs is exactly the yard. The two 3'-6"
    balcony returns are not on that perimeter — they run east-west at y -10'-6" closing the U
    against the court walls, retaining terrace fill to the south with the balcony underside to the
    north — so they have no lawn-facing face at all and layer 0 on them would land in the fill.
    Hence `RETAINING_BLOCK_12_WASHED` as a variant, and hence only three of the five legs. That is
    a faithful reading of "exterior side, to reflect more light into the lawn", not a narrowing,
    and it avoided all model surgery because those three are exactly the walls where layer 0
    already lands right.
- **The wash re-centred the pour, and that was the largest single consequence of the change.**
  A layer stack is centred on the node line, so adding 1/8" of film to a 12" wall slid the
  concrete 1/16" off the structural grid. Three things broke on that 1/16" and **only one was
  caught by a check**: `SP-SG-W1-CD-SPA` fell out of its own host (`integrity.sleeve_in_opening`,
  a FAIL), while the corner columns stopped being flush with the walls they stand on and the
  raised garden stopped closing on the court walls — both at 0 FAIL, found only by test. The fix
  is `Wall.alignment`, whose own docstring names this exact case: `FaceRef.offset` "is what lets a
  layer be added to one side of an existing wall without moving the layer that actually holds the
  datum". `face("center", offset=±_WASH_FILM/2)`, positive where the wash is layer 0 and negative
  where it is last, puts the pour back on 90"–102" and lets the film oversail outward — which is
  what actually gets built: a 12" pour on the grid, painted.
  - The same class of drift reached the levelling pads. `resolve/envelope.py` centred a
    `FootingBedding`'s band on **every** layer's polygon, so the wash pulled the stone 1/16" off
    the block it sits under. It now reads STRUCTURE layers only: a bed is placed by what bears on
    it. That is an engine change, small and general, and it falls back to every layer where an
    assembly declares no structure layer.
  - And the corollary for anyone reading geometry out of this model: **a wall's faces are no
    longer `axis ± thickness_m/2`.** On a washed wall `thickness_m` is 12 1/8" while the pour is
    12". Read the structure layer's polygon.
- **`W-SG-ARCH` was silently washed, and the goldens are what caught it.** It shared
  `SUNKEN_GARDEN_WALL` with the five court walls — right while that assembly was one bare concrete
  layer, wrong the moment layer 0 became paint, because the arch is the BURIED strut: its top is
  the rim slab's underside, the court floor bears on it, and its own note already said "nothing of
  it shows". Painting it billed 3.6 SF on a face under a slab, and no check grades whether a
  FINISH layer is reachable. `test_elevation_goldens.py` reported six `layer:wash` keys where the
  court has five walls, which is the only reason it was found at all. It now carries
  `SUNKEN_GARDEN_GRADE_BEAM_12` — identical pour, identical mix, identical ticket, identical
  `$/cy` row, split on appearance alone. The beam moved rather than the five walls because that is
  the cheap direction: every test, gate and price key already written against `SUNKEN_GARDEN_WALL`
  still names the same five subjects.
- **A conduit was found running tangent to a wall face with zero cover.** `CD-B-SPA`'s southward
  leg was authored at x 8'-6", which is exactly where `W-SG-W1`'s pour used to face, so the leg and
  both its sleeves grazed a polygon boundary and "crossed" two walls by touching them — passing
  only because `integrity.sleeve_in_opening` buffers by 1e-6. The wash's 1/16" is what exposed it.
  The leg moved 1/8" west into the pour; the tangency, not the wash, was the defect.
- **Decided: accept the telegraphing.** As-cast concrete under a thin translucent wash shows form
  seams, tie holes and bugholes rather than hiding them — bugholes read slightly darker because the
  coating thins over the lip and pools in the void, and KEIM describe their own concrete coating as
  one that "retains original concrete appearance". `SUNKEN_GARDEN_WALL` specifies no form finish and
  none is being added. A chalky white wash over visible form texture reads as deliberate rather than
  as a defect and costs nothing extra. **This is a choice, recorded so a later pass does not read
  the telegraphing as a defect and "fix" it** by adding a concrete-finisher or sack-rub line that
  was deliberately not bought. Expect first-coat patchiness generally: both manufacturers warn in
  their own instructions about flash-drying, roller ridges and lapping being visible in glancing
  light. Mottle is characteristic, not a defect, and the SRW style's `jitterHSL` lightness term is
  raised above `WHITE_BRICK_STYLE`'s for exactly that reason.
- **Risks the model cannot express**, all of them on the SRW blocks, which are the weakest
  substrate in the scope:
  1. Dry-cast, integrally coloured units are far less absorbent than cast-in-place and frequently
     carry an **integral water repellent** — the one condition a potassium silicate cannot bond to.
     NCMA/CMHA TEK 19-7 says of such units that "the most important characteristic of the unit may
     be its compatibility with the type of coating used… some coatings may not be able to bridge
     open pores or fill all surface irregularities". Beecko-SOL is the answer, and Beeckosil's own
     TDS additionally asks for Quartz Filler or a Bonding Coat over the whole face as a CMU
     pretreatment. **A test panel on a spare block precedes 245 SF** — that is the manufacturers'
     own instruction ("the only way to precisely predict application rates is with a trial
     application"), not a precaution added here.
  2. Open dry-stacked SRW joints will take the wash unevenly.
  3. Efflorescence driven out of granular backfill through a retaining wall's face can lift or
     stain a mineral coating. Keystone's own manual calls efflorescence on an SRW face expected and
     aesthetic-only; Romabio warns that masonry in constant contact with damp "may absorb excessive
     moisture or salt nitrates which can cause rapid deterioration of masonry substrates and its
     coatings", and that Masonry Flat is not a stain-blocking paint. Drainage and capping behind
     the wall is the real control.
  4. **"SRW manufacturers void warranty on coatings" could NOT be sourced** and is recorded here as
     unverified rather than as a finding: Keystone's maintenance chapter and Versa-Lok's FAQ never
     mention paint or coatings, and the only warranty language found is generic. Ask the specific
     block manufacturer in writing before committing.
  5. Horticultural: a white wall raises leaf temperature, water demand and reflected UV for
     anything planted tight against it. Good for compactness, a scorch risk for tender transplants.
- **The colour is derived, not published, and it is authored under its target.** No measured sRGB
  or spectral value exists for any of these whites; the only anchored number is LRV 90. That is
  Y = 0.90 → **#f3f3f3** as an ideal full-hiding chip, which is too bright for a render: a
  photographed two-coat white silicate over as-cast grey loses 5-15% to mottle, thin-spot substrate
  bleed and matte micro-shadowing, landing near **#ebe8e1** and reading very slightly warm.
  `#e9e6df` is authored under that, per the albedo rule this file already applies to
  `brown-brick` — and it is deliberately the same hex as `WHITE_BRICK_STYLE.base`, because this
  house already tuned that value for a whitewashed masonry face in this renderer. Note the wash is
  a **new visible surface, not a recolour**: the substrate materials cannot be retinted, because
  `material_ref="concrete"` on the STRUCTURE layer is what the `[concrete]` price table's material
  guard admits, so the white has to come from the wash layer's own `Material.color` drawn in front
  of the substrate.
- **The render took three tries, and the first two were the wrong kind of fix.** The wash draws a
  real plane — `Material.coating=True` only stops a room FLOOR finish from drawing — and a plane
  that thin z-fights: Panel3D's 24-bit depth buffer on `PerspectiveCamera(50, 1, 0.05, 500)`
  resolves about `z² × 1.19e-6` m, which is 0.48 mm at 20 m and 3.2 mm at 52 m, so the viewer
  flashed grey concrete through the white. The first response was to thicken the layer: 0.01" →
  1/16" → 1/8", each time computing the distance at which it would clear and each time still
  shimmering in practice. **That was a losing race and the wrong mechanism** — it traded an honest
  number for a renderer's convenience, and the renderer kept winning. `polygonOffset` is what the
  problem actually calls for: it wins the depth test deterministically at any camera distance,
  costs nothing, and hands the thickness back to the builder. 1/8" is kept now on build grounds
  (two coats, plus the whole-face filler coat the TDS requires on block) and because it is what
  `foundation-coating-acrylic` has carried since 2026-09-04 — not because of the depth buffer.
  The one cost: glTF has no `polygonOffset`, so an exported `.glb` in a third-party viewer can
  still shimmer where the live viewer does not.
- **And a flat fill was the wrong picture anyway.** The wash now gets a procedural texture, on the
  same argument the metal skins and the masonry already make in this codebase: one shared 4-ft
  tile of low-frequency mottle plus a matching roughness map, world-scaled so a 10' court wall and
  a 20 SF fireplace panel show the same cloud at the same size. What it draws is exactly what the
  manufacturers warn about and what was accepted rather than paid to avoid — flash-drying, roller
  laps, slight pooling in bugholes. The roughness swing is deliberately tiny: this finish is dead
  matte everywhere (Beeck publish "dull matte" at 85°, Romabio <5 gloss) and a glossy patch would
  be a lie about a non-film-forming coating.
- **Two materials for one product, and the reason is the renderer.** `silicate-wash-white` renders
  as one flat chalky plane, which is right over as-cast concrete. `silicate-wash-white-block` is the
  same pail at the same price on the SRW legs, and exists because a thin non-film-forming silicate
  hides the grey without levelling anything: the 18" x 6" unit module and the open dry-stacked
  joints telegraph straight through. `Material.finish` is the field that declares appearance, so it
  takes two tags; `SILICATE_WASH_BLOCK_STYLE` in `ui/src/three/materials.ts` clones `CMU_STYLE` onto
  the SRW module with the near-white base. The tag carries "block" deliberately, so `family_of`
  reads it as masonry, which is the gate `builders/walls.ts` gives the coursing path. The fireplace
  takes the flat variant and **accepts** losing brick coursing on the washed face; coursing still
  shows on the 3 5/8" reveal returns.
- **The tag avoids three substring matchers.** `mineral` maps to the **batt** family in both
  `emit/draw/palette.py` and `ui/src/nordic/palette.ts`, so "mineral-silicate-wash" would render and
  hatch as mineral wool. `limewash`/`whitewash` are matched by `_is_white_brick` and
  `isWhiteBrickRef` and would hand the material brick **coursing** — wrong on concrete and on SRW
  block. `silicate-wash-white` does contain "white", which those same matchers also catch, but it
  never reaches them: the authored catalog colour is consulted first in both surfaces, and
  `family_of` returns None for this tag. The `_FINISH_BASE` tables were deliberately NOT given
  rows, because they are keyed on the material **ref** rather than the finish, so a row named
  "silicate-wash" would be dead weight that no lookup could ever hit.
- **One brick blend house-wide, washed at the fireplace only.** The court ordered `brown-brick`
  (124.9 SF) and the fireplace `white-brick` (20.4 SF). The fireplace moved to the court's blend and
  takes the wash, so it still reads white — from the coating, not the body. What that removes is a
  **third cube** of special-order brick: modular face brick is 6.75 units/SF and a cube is 480-534
  units ≈ 71-79 SF, so 21.42 SF ordered a cube of which ~53 SF is never laid ≈ **$420-850** at this
  row's own $8-16/SF, plus the 1.5-2x special-order premium and lead time, plus a second colour for
  the mason to lay to a line. Consolidated, 152.57 SF is still two cubes plus a strap. **The
  estimate moves $0 on brick and must** — both rows price $/SF of face laid, so none of that cube
  arithmetic is in this model; re-rating the material half down to book the saving would move the
  total ~$19-29 and misdescribe where the money went. The white was never a designed choice:
  `assemblies.py` sourced it to the retired porch parapet and `brief.md` says only "white metal
  skin", never brick. The whole `white-brick` chain stays live-and-unreferenced on the
  `glazed-green-brick` convention.
- **The 129.2 → 124.9 SF reconciliation, and what it costs.** 124.9 is what the takeoff has always
  reported (18'-8" x 102 7/16" = 159.3 SF gross, less 1.94 and 32.5 for the two reveals). No dollar
  moves — but the LOW rate of $19/SF was chosen *because* $19 x 129.2 = $2,455 cleared this file's
  own "$2,500-4,000 mason mobilisation floor" where the market's $16 did not, and $19 x 124.9 =
  $2,373 does **not** clear it. The honest resolution is the consolidation itself: court + firebox
  on one call-out is $2,842-4,889, which lands on the floor for real. Bumping the rate to rescue a
  documentation error was rejected.
- **Sequencing is a real constraint, not a note.** The wash is a **separate trade and a separate
  arrival** from the mason. On the exterior it wants the court backfilled and the forms long gone;
  on the fireplace it wants the room framed and the heat on. Romabio's own guidance is to leave the
  absorbent substrate **damp**, and Masonry Flat needs 14 days before cleaning — neither of which
  composes with a cold, wet, still-being-poured court. Book it late.
- **No `notes/` entry, deliberately.** `notes/` holds hand-worked **oracles** for calculations. There
  is no calculation here — no check reads reflectance, albedo, LRV or SRI, confirmed by grep over
  `checks/` — so a note would name no oracle and `routing/oracle.py`-style lints would have nothing
  to bind. The wash is a `Material.color` decision with a rendering convention and a BOM row behind
  it; the intent lives in `plan/assemblies.py` and the derivation here.

**The veneer's material history (2026-09-04).** `W-B-BRICK` has worn three faces: first a
flat field of `glazed-green-brick` (`#1b4332`); then the Ishtar Gate — a lapis field with
golden-yellow register bands over an unglazed brown plinth; then, since 2026-09-04, the
plinth's own brick run full height. The glaze was dropped. What is on the wall now is
`brown-brick` `#a07c5c`, ordinary ASTM C216 Grade SW face brick, the cheapest face that had
ever been on it and the only one a Twin Cities yard stocks off the shelf.

- The swap also settled a spec conflict: [BIA Tech Note 13](https://www.gobrick.com/media/file/13-ceramic-glazed-brick-exterior-walls.pdf)
  says glazed brick "should not be used in locations where they are likely to be saturated."
  The Ishtar scheme had complied only because the unglazed plinth kept the glaze above the
  splash line. An all-unglazed SW field is unconditionally right for a Minnesota sunken
  court, which is a rain sump with walls.
- `glazed-green-brick`, `glazed-lapis-brick` and `glazed-gold-brick` remain in the catalog,
  referenced by nothing, in case either scheme is wanted again — a material's appearance is
  a three-place change (`Material`, `MasonryStyle` in `ui/src/three/materials.ts`,
  `_FINISH_BASE` in `emit/gltf/palette.py`) and a revert has to find all three. Their
  `prices.toml` rows are commented out rather than removed for the same reason.
- The jitter had to move with the job, and it was the one thing that did. A material's
  appearance is `Material` + `MasonryStyle` + `_FINISH_BASE`, and `#a07c5c` was unchanged in
  all three — it is already authored a step under its target for the albedo reason above,
  and re-darkening it would be a mistake. `BROWN_BRICK_STYLE.jitterHSL` was not unchanged: it
  had been `[0.004, 0.015, 0.04]`, the glazes' near-zero, because the reason for that setting
  was a 28 SF plinth beside a glaze, where the red brick's full variegation read as mixed
  pallets with near-black units through it. The field is now 129 SF with no glaze to
  contrast against, and one flat brown at near-zero reads as a printed sheet. It became
  `[0.008, 0.035, 0.09]` — deliberately intermediate, roughly double a glaze and half of
  `BRICK_STYLE`'s `[0.02, 0.08, 0.16]`, which is the failure mode in the other direction and
  one this material had already been in once. Mortar stayed `#cfc8ba` (tan), the unglazed
  pairing. `haus render` cannot show this and never could: the CLI emitters carry only the
  flat de-jittered `_FINISH_BASE` hex (`emit/gltf/palette.py` annotates `_BROWN_BRICK_BASE` as
  exactly that), and `--view elevation` emits east/west while this wall faces south. Judge it
  in the headless viewer, or compute the recipe's extremes directly: the per-unit jitter is
  `new THREE.Color(base).offsetHSL(±j[0]/2, ±j[1]/2, ±j[2]/2)`, so a five-line node script
  prints the darkest and lightest unit a setting produces.
- The wythe became one layer — no `slot`, no `extent`. It had been five `slot="wythe"`
  regions sharing a single 3 5/8" depth position (without the slot the assembly resolves to
  an 18 1/8" wythe and shoves the wall into the garden). With one region there is nothing to
  co-locate and nothing to band, so it is the ordinary case: a plain full-height STRUCTURE
  layer taking the wall's own base and top. `Layer.slot` remains a live feature that catlin
  no longer exercises — the machinery, and the emitter regression it exists to catch, are now
  guarded on a synthetic fixture in `packages/engine/tests/test_emitter_band_parity.py`.
  Anything that had been true about band heights on the 2 2/3" course, `applyMasonryWallUv`,
  or the upper register riding `D-B-PATIO`'s head line at 88" is history, not a constraint.
- It had to stay a STRUCTURE layer, not CLADDING — the backer is a different wall, so this
  has to be the structure layer or `integrity.assembly_layers` finds none. Same precedent as
  `RETAINING_BLOCK_12`. One BOM row resulted, `BASEMENT_BRICK_VENEER:brown-brick`, 129.2 SF.
- The rate could not carry over, and that is the interesting part of the money. The old
  $15-28/SF was the standard-veneer market taken at its low end because the plinth was 24"
  off the ground — no scaffold. A full 8'-5" field needs scaffold for its upper 6', so it
  became $19-30/SF: $2,455-3,876 against the Ishtar wall's $2,573-5,467. The $19 low sits
  above the $16 the market alone would say, because 129 SF is a minimum-mobilisation masonry
  job and `prices.toml` elsewhere says a mason will not set up scaffold under ~$2,500-4,000.
  The saving is roughly $120-1,590 — real, modest, and never the point.
- Both brick reveals ended up shorter than the openings they front, and the door reveal's
  height became a free variable. `AO-B-BRICK-DOOR` went 88" → 84" → 78" and `AO-B-BRICK-WIN`
  26" → 20", all by eye and all against the gold register at 88" that no longer exists. 78"
  was kept because it still looks right — nothing requires it, and 84" is available if more
  of the door head should be covered. The overlap itself is deliberate: a masonry reveal in
  front of a rectangular hole is meant to overlap it, so the door's head is covered across
  its full width and the sauna window loses its top 6". Neither opening is a daylight or
  egress subject.
- A reveal must stay concentric with the opening it reveals, and for five days one was not.
  `AO-B-BRICK-DOOR` had been authored against `D-B-PATIO`'s position; on 2026-08-30 the door
  moved 6" west off a different node on a different wall and the reveal did not follow.
  `haus check` reported 0 FAIL the whole time, because the two are individually correct and
  nothing compared them. `integrity.reveal_concentric` now grades that — every rough opening
  with a wall standing behind it, against the nearest door or window in that wall, at a 1"
  tolerance — and `test_catlin_contract_m3` pins both pairs.
- Both arched reveals turn a voussoir ring, `ui/src/three/builders/archRing.ts`. Masonry here
  is a texture, so the arch heads had been running bond sliced by a curve; the ring is an
  annulus with polar UVs into that same tile, turning its rectangular bricks into wedges. One
  header deep (3 5/8") and 3/16" proud on every face (the proud offset exposes the skewback
  end caps; at 3/8" each had read as a black shard off the springline). The door's extrados
  crowns at 81 5/8", the window's at 52 5/8". Viewer-only; an exported `.glb` still shows the
  plain spandrel.


**Fourth pass — the smallest workable court, and a footing that was a fossil (2026-09-10).**
The owner asked what the smallest workable sunken garden is, against five goals: daylight
into the basement gym and sauna, an outdoor space four people can do yoga in without feeling
trapped, the foundation for the porch and balcony, a private place to lie down and look at
stars, and room for a water lily bowl and plants. Two findings shaped the answer, and only
one of them was about length.

- **Court length is not the lever it looks like.** Daylight is governed by the 8'-8" porch
  overhang, not by the south wall — moving the south wall north does not brighten the gym.
  And the structural cost is one-sided: shortening removes base friction from the capacity
  and **nothing** from the demand, because `W-SG-W2` and `W-SG-E2` cancel identically and
  the resultant is the south wall's thrust alone, over the court's WIDTH. There is a hard
  floor at **23'-11"** clear where the friction under the remaining run stops reaching it —
  and that floor is a function of the strip width, so it MOVED with the narrowing: it was
  23'-3" at 8'-0". Taking the width first raised the floor under the length, which leaves
  about **2'-1"** rather than the 2'-8" the width cut alone would have bought. The two cuts
  are not independent and the floor must be re-derived, never quoted.
  The saving is $700-1,300 per foot. `plans/cost-options.md` had a row pricing 28' → 16' at
  $9,700-16,600; that row is not available as written — 16' fails sliding in all four soil
  corners.
- **The footing was a fossil.** `notes/sunken_garden_court_free_body.md` §3 records that the
  eccentricity check forced the strip 7'-0" → 8'-0". It did, at a retained height of
  11.3698'. Three height cuts have since brought that wall to 10.1198', and at 7'-0" centred
  the resultant lands 0.800' off centre against a kern of 1.167' — a **31% margin**. The
  note's discipline of adding a table row after each height cut was applied to §6's stem bar
  schedule and never to §3's width. The rejected row had crossed sides, exactly as `#6 @ 16"`
  and `#5 @ 10"` did.
- **The outboard edge does not move, which is the one thing that may not.** At 96" with a 6"
  inboard offset the outboard reach is `96/24 − 6/12 = 3.5'`; at 84" centred it is
  `84/24 = 3.5'`. The raised garden's apron measures its 3'-0" clear off that edge — the
  owner's own figure from the brief — and it does not move. The whole 12" comes off the TOE,
  on the court side, so **the planted field grows from 147 sf to 160 sf while the court gets
  shorter.**
- **Never cut the heel.** A foot of toe is 150 plf out of 5,578 and costs 0.05 of system FS.
  The same yard of concrete off the heel takes the 9'-1 7/16" soil column with it and costs
  **0.21**. The heel is held at 3'-0" and always should be.
- **The mat and the width are one decision.** Narrowing removed 22% of the toe moment, which
  is what lets the mat come down `#6 @ 10"` → `#5 @ 12"` (0.90 at 8'-0", 0.70 at 7'-0").
  `#4 @ 12"` is not available below it: 0.200 in² fails flexure and falls under ACI 318-19
  §7.6.1.1's `0.0018 Ag = 0.259`. The "one bar, one spacing" half of §6's rejection of
  `#6 @ 16"` on the stem dissolves with this — the pour carries two bar sizes now — and that
  rejection survives on its own 3% margin.
- **What it costs, stated rather than discovered.** System sliding FS **1.80 → 1.63**, from
  20% over the code minimum to 8.6% over it; the no-stone sensitivity at μ = 0.25 **1.29 →
  1.16**; overturning 2.94 → 2.41; `e`/kern 0.387/1.333 → 0.800/1.167; q_max 899 → 1,307 psf
  against 3,000 allowable. Both of the first two were already the design's stated exposure.
  The highest-value purchase before pouring is still a geotechnical boring — §5 says it would
  change the answer more than any amount of concrete, and that is true twice over now.
- **Two real problems the change created, and both are fixed here.** `DRW-SG-MAIN` was
  derived from the court's north-south midpoint in two independent places, so shortening
  walked it 1'-0" north and put the north edge of its 5'-0" shaft inside `FB-SG-ARCH`'s bed
  band — which nothing grades (`structural.concrete_interference` sees isolated pours and
  every court footing is `under=`-hosted; `drainage.discharge_consistency` resolves tags and
  never asks where the pipe goes). It is now one expression pinned off `_y_ax_mid` with a
  stated clearance. And two `SpotElevation` stations in `plan/site.py` recorded the top of
  `W-SG-S` at y = −29; that axis moved to −27.3333, leaving both out in the apron. They feed
  `balcony_wind.ground_below_ft`. Moved with the wall.
- **Three factual corrections went in alongside, agreed separately.**
  `engineering/retaining_basis.py`'s docstring said the toe is buried 6 1/2" and contributes
  under 1%; the toe is buried **0"** (the court floor is the footing top and the rim carries
  `FO-SG-TOE-*` voids over it), so `toe_embedment_ft = 0.0` is correct for a different reason
  than the one stated — and the stated one is what a later reader would "fix" in the unsafe
  direction. IBC Table 1610.1's **GM** active row is **40 psf/ft**, not the 45 the notes cite;
  45 is the GC and SM row, the direction is safe, and the frozen screening note is flagged
  rather than edited. And §8 ranked sequencing as the strongest objection to a slab strut: it
  is the weakest, because footnote g is satisfied by ordering. What kills the strut is that
  `SL-SG-FLOOR` is a 3 1/2" rim around a gravel field with seven voids in it — **there is no
  continuous concrete path across the court for a strut to be.**
- **One gap closed while here.** The "net rim polygon intersects every `FT-SG-*` at 0.000 sf"
  invariant existed only as a comment, and this pass moved both of its inputs at once. It is
  asserted now (`test_retaining_court.py::test_the_net_rim_laps_no_footing`), scoped to the
  five wall strips — the two belled pier bases top out 2'-6" lower and a plan lap there is
  not a lap.
- **And the 2026-09-10 flush tops, which had no entry.** All five court walls came flush with
  the porch datum at 0'-0" earlier the same day: one form height, one strip-and-set, one
  continuous top line, no 2" jog at the porch corner. `SPEC.retaining_top_ft` is `porch_top_ft`
  now rather than a figure derived off grade, so the owner's 36"-out-of-the-yard is a RESULT
  (40" against the -3'-4" yard the site authors) and not the constraint. The tops fell 2",
  stem 9.2865' → 9.1198', which took sliding 1.77 → 1.80 for free.


## Electrical service

### BLD-06 answered: the service went Class 320 and load management left the house (2026-09-12)

**The reviewer's premise held, and their arithmetic did not.** BLD-06 said the 191.4 A
220.82 demand only fit the 200 A service because four `LoadManagement` groups credited
18,240 VA, and that the devices behind three of them were not listed for it. Checked against
the 2026 NEC — which Minnesota adopted for electrical permits filed on or after 2026-08-17,
and which `inspections.toml [permit]` already declares as `nec_edition = "2026"` — the
premise is right:

- Article 750 became **Article 130**; 220.70 became **120.7** (a PCS setpoint must be <= 80%
  of the monitored OCPD and set by a qualified person); **130.2** requires an energy
  management system to be listed, and one providing overload control to be listed as a
  **power control system (UL 3141)**. **625.42(A)** now points EV supply equipment at a PCS
  under Article 130 Part II.
- Emporia's certification page lists UL 61010-2-030 and UL 2808 for the Vue; the charger's
  spec sheet lists UL 2594 / 2231 / 991. **No UL 3141, no EVEMS listing.** So `LM-EV`,
  `LM-WELLNESS` and `LM-WH` — Emporia throttling, an Emporia contactor shed and an ESPHome /
  EcoNet automation — were crediting amps none of them could earn.

**Where the reviewer erred, in both directions.** Too optimistic on the EV group: under 2026
625.42(A) the EV controller must itself be a PCS, so all three software credits were exposed,
not two. Too pessimistic on the strip-heat lockout: **220.82(C)(2)/(4) credits a controller
that prevents a compressor and its supplemental heat from operating at the same time**
directly, and that is the FLEXX Ultra's own outdoor-thermostat lockout — no Article 130
device, no listing, nothing to buy. `LM-HP1-AUX` was earnable all along.

**The four options, measured on this model rather than estimated.**

| | demand | what it needs |
|---|---|---|
| unmanaged | **267.4 A** | nothing |
| keep only the code-native HVAC interlock | 248 A | an outdoor thermostat (already specified) |
| + a listed EV PCS | 216 A | SPAN / Lumin / Eaton / Schneider hardware, ~$2.1-3.5k + install |
| + a hardwired spa/sauna interlock under 220.60 | 198 A | contactors, and an AHJ judgement, for **1.9 A** of margin |

The standard method (Part III) is worse still at 344 A. So the choice was a whole-house PCS
or a bigger service.

**Class 320 won, and the cost gap is not what the review said.** Xcel's MN residential
standards carry two socket sizes — 200 A and 320 A continuous — both heavy-duty lever bypass
(Landis+Gyr HQ, Square D, Milbank HD, Eaton MSL), with no CT cabinet required below 320 A
continuous. **There is no 225 A service class and no 400 A one**: the trade says "400 A"
because 320 / 0.8 = 400, and this house's 225 A is `ED-T-PANEL`'s busbar. On a NEW BUILD the
increment is the meter-main delta over a plain 200 A socket, a second 200 A load centre, and
two short 4/0 Al SER feeders on the same wall — **~$2.5-5k**, priced in `prices.toml` as
`ED-T-METER`, `ED-T-PANEL-2` and the `electrical-service-feeders-4-0-al-ser` allowance. The
review's $10-15k is retrofit pricing: a service change on a finished house pays for a mast,
a re-pull and a utility disconnect this project pays for once anyway. Against that, a listed
PCS is $2-3k of hardware plus install **and** a permanent software dependency inside the load
calculation, on a house that already declines that dependency everywhere else.

**So load management left entirely.** `load_managements=()`. None of the four groups was a
backup item — backup shedding lives on `Circuit.backup_tier` plus the Shelly relay and its
contactors — so nothing about the microgrid moved. What survives, demoted to what it always
was: the aux-heat lockout is an HVAC control setting on `CKT-HP1-AH`, and the water heater's
Heat-Pump-Only automation is a **backup reserve** measure beside `backup_tier=SHED`.

**The Emporia charger stays.** It is a listed EVSE (UL 2594 3rd ed., Energy Star). What it
lacks is a PCS listing for PowerSmart throttling, which a 320 A service does not need.
Contingency only: if dynamic EV charging is ever to be credited again, the path is a UL 3141
PCS, not a different charger.

**Two engine consequences, both real bugs the decision exposed.**

1. `code.NEC_705_12_interconnection` borrowed the METER's `service_amps` as its main-breaker
   term. At 320 A that would have graded 320 + 50 = 370 A against a 225 A bus's 270 A
   allowance — a FAIL on a panel whose main is 200 A, or, had the bus been larger, a silently
   **loosened** allowance. The check now reads the panel type's own `service_amps` first and
   falls back to the service size only where a panel states none, so both panels declare
   `service_amps=200` and the finding still reads "200A main + 50A source ... 20A spare".
2. With the load split across two mains the service total proves nothing about either half.
   `electrical.panel_feeder_load` (ADVISORY, on the final-electrical inspection) runs the
   220.82 term structure over one panel's circuits against that panel's main. It is labelled
   an **estimate**: a subpanel feeder is properly NEC 220 Part III, and applying the
   first-10-kVA-at-100% step per panel over-counts. ED-B-PANEL 157.5 A, ED-B-PANEL-2 117.7 A.

**And the engine stopped accepting a credit on trust.** `LoadManagement.strategy` was free
text; it is now `"hvac_interlock" | "noncoincident" | "pcs"` with a `listing` field, and
`takeoff/electrical.py::_credit_refusal` refuses a `pcs` with no listing, a `noncoincident`
with no source, and an `hvac_interlock` reaching anything but heat-pump circuits. A refused
group FAILs `electrical.service_load` and its excess stays in the demand. The old spelling
would have let exactly this house's four groups through again.

## Kitchen: the IKEA SEKTION ladder

**The decision was already made; the model had not heard.** `PROD-IKEA-SEKTION` and
`PROD-IKEA-VOXTORP-WH` were registered 2026-09-06 and `prices.toml` priced the whole kitchen
as SEKTION with VOXTORP fronts, arguing the Section 232 case for it — 25% on wooden cabinets
from 2025-10-14, the scheduled 50% delayed to 2027-01-01, SEKTION's carcasses made in the US
and insulated from it. Meanwhile every box in `plan/placeables.py` was a generic `CASE-*`
type whose four governing constants — 13" upper depth, 42" upper height, 96" tall frame, 12"
stacker — are **all four absent from SEKTION**. The estimate was priced against boxes nobody
sells.

**The leg is the only free variable, and it is what closes a ceiling.** Every SEKTION frame
height is a multiple of five, so a stack totals a multiple of five and 108" is not reachable
from a 4 1/2" leg: `4.5 + 90 + 15 = 109.5` and `4.5 + 80 + 20 = 104.5`. The owner chose to
shorten the legs rather than fill at the ceiling, and one leg height has to serve both runs
or the toe kick steps where the east tall bank meets `N3`. **3" closes both exactly** —
`3 + 90 + 15` tall, `40 + 15` hung at 53 for the uppers — at the cost of 1 13/16" of sub-top
under the 3 cm quartz to keep the counter on 36". That build-up is invisible under the stone
and ordinary fabrication; the legs are screw-adjustable feet behind a cut board.

**Four numbers moved and they moved together.** Uppers 54 → 53, stacker 96 → 93, over-cold
75 → 78, mixer garage top box a new 76. Backing rails followed at their authored 2" below
(`plan/backing.py`), and so did the under-cabinet tape (`plan/lighting.py`) — which also
shifted 2" into the room, because a 15"-deep upper's front face is 2" nearer than a 13" one.

**What 2" of depth cost: `FURN-M-KIT-WE3`.** The 12" box over `WIN-M-KITCH-N` sat in a
12 3/8" slot between `E2`'s east end and `WN1`'s return. At 15" deep that return reaches 2"
further west and the slot is 10 3/8"; IKEA's narrowest wall cabinet is 12". It is a scribed
filler panel now, built in the plane of the upper fronts so `LR-M-KIT-N-WE3` still has
something to fasten to. This restores rather than breaks the corner rule the kitchen header
states — east claims the inside corner, north yields at 33'-4" — which is what the base run
already did; WE3 was the one box that crossed it, and it only fit on 2" it no longer has.

**Four boxes became two over the cold run.** A 30" frame at 78" lands on 108" by itself, so
the `CASE-TS3278-12` stackers went with the 32 7/8" over-cabinets and there is no joint at
8'-0" on that wall at all. 78" also gives the Frigidaire hinge 5 1/2" where the old 75" gave
2 1/2". The bay's 5 3/4" of remainder is split 2 7/8" at each end against a tall cabinet,
with the two boxes ganged on the appliance joint — not left as one gap floating between them
where every eye in the room lands.

**The one filler the ladder forces.** The mixer garage wants 72" from a 36" counter to a
108" ceiling. No sum of 15/20/30/40 reaches 72; the best below is 70. `SEKT-TW24-40` at 36"
under `SEKT-TW24-30` at 76" tops at 106" and the last 2" is a scribed panel. One element,
one wall, written down in `notes/ikea_sektion_ladder.md` so nobody tries to close it.

**MAXIMERA stayed out of the model, on purpose.** The engine has one solid carcass per
cabinet and no drawer vocabulary, so adding drawers would have meant inventing geometry to
carry a purchasing fact. It is `PROD-IKEA-MAXIMERA` instead, and which boxes are drawer
stacks is prose beside the instances and in the SEKTION price block.

## In-wall backing

**The wet walls' plywood band became three 2x courses, 2026-09-12, and money is not why.**
Decision #68 gave this house 17 wet-wall bands: one continuous 3/4" Structural 1 plywood
sheet each, 48" tall, 32"–80" above the floor, 106 LF ordered, about 13 sheets. The
reasoning was sound and is still in `notes/wall_backing.md` §4 — 48" is half a sheet ripped
the long way, it covers every anchor a bathroom will ever want in one piece, and blocking
placed only where today's screws land pins the house to today's model forever.

**What it never answered is how the sheet meets the wall.** Every one of those 17 walls puts
5/8" gypsum straight on the studs. A 3/4" board laid on the stud face stands 3/4" proud of
the finish plane, which is not buildable; the alternative is to let it in, and
`notes/wall_backing.md` §5 claimed exactly that — "built let-in flush with the stud face,
which is how CRC R328.1.1 specifies it". That claim is true of a 2x8 block and false of a
48"-tall band: letting in a 48" sheet means routing a 3/4" × 48" dado across roughly 65
studs. Nothing in the engine draws that dado, nothing in `prices.toml` prices it, and no
check would have said a word either way. The owner read the model in the viewer and asked
the question the record could not answer.

**Three courses instead**, laid flat and fitted *between* the studs, which is what this
house's kitchen rails have always meant by "2x8 flat": 2x8 at 32" (CRC R328.1.1's grab-bar
band, verbatim), 2x10 at 44", 2x8 at 72". Nothing stands proud, nothing is dadoed, and the
framer cuts to the bay.

**The coverage lost is real and is written down rather than glossed.** The band was
continuous 32"–80"; the courses leave 39 1/4"–44", 53 1/4"–72" and everything over 80 1/4"
bare. The policy did not change — those are three standard anchor heights authored where a
screw *might* land, not a fit to today's fixtures. What made the trade affordable is that
**only one modelled body in the whole house sat inside the old band at all**
(`FURN-M-BATH2-CAB` at 48" on `W-M-HS1`), so the band was pure future-proofing and its
height was a policy choice rather than a measurement. The 44" course still covers it.

**Three of the four anchors the old prose named were never this file's business.** Valve
body, tub spout and shower arm are the plumber's rough-in blocking, set with the rough-in.
Only the grab bar is finish backing.

**What the courses gain beyond not being dadoed**: a per-bay 2x can be omitted or shifted at
the one bay a shower valve and its risers occupy. A continuous sheet cannot, and §5 of the
note already flagged that overlap as ungraded — the engine has no member-versus-`PipeRun`
check, so the old band ran through the valve plane at 0 FAIL.

**Cost is a wash and was measured, not assumed**: $674–1,086 for the three courses against
$647–1,128 for the retired band, against price rows that assume no dado. `prices.toml` keeps
`"0.75x48.0"` and `"0.75x24.0"` at 0 LF under the `glazed-green-brick` convention, because
this question will be asked again and a deleted row is a row re-derived from scratch.

**Two authored defects went with it, both at 0 FAIL and both found by eye.**
`BK-G-W-RAIL-FOOT` was a 12" block in a 24" o.c. bay: its north end lapped a stud by 1/4"
and its south end floated 10 1/4" clear of anything, so the block could be nailed at one end
only. It is cut to fill the bay now, 192 3/4"–215 1/4", and the handrail bracket at 197"
sits 4 1/4" inside it. And `W-M-E1`'s four cabinet bands carried no `start`/`length`, which
`backing_panels.py` reads as the wall's whole 36 ft — roughly 59 LF of 2x8 running south
into the living room to back nothing. They start at station 20'-0" now, in the gap between
the last BESTA unit and the first pantry, on `WIN-M-LIV-E2`'s north jamb pack so the run
begins on framing. `BK-M-E1-ROD` keeps its full run: at 82" it backs the two living-room
curtain rods, which are exactly what the other four gave up.

**The engine gained one check, not a model change.** `advisory.wall_backing_bearing`
requires both ends of every resolved band run to land within 1" of a stud face or at the
wall's own end. It found exactly one finding across 62 runs on the model as it stood — the
garage block — and no false positives, which is the whole argument for it: a rule that
reported nothing, or reported everywhere, would have been the wrong rule. The wall's own
ends are exempt, since the plates and corner pack close them and without the exemption every
full-run band reports.

**The file split rather than grew.** 17 elements became 50 and `plan/backing.py` would have
run past `AGENTS.md`'s 500 lines, so the wet courses moved to `plan/backing_wet.py` with the
course constants, following the `plan/lighting_attic.py` precedent — split by SUBJECT here
rather than by storey, because these 50 are one decision and the rest of the file is a dozen
unrelated ones. An editable file cannot `from plan import ...`, so `plan/manifest.py`
composes.

**Left out as scope.** `FURN-M-BATH2-CAB` is 60" tall from 48", so its top rail lands near
104" — above every course, old and new. A fourth course on `W-M-HS1` alone (2x8 flat at 98",
topping at 105 1/4", on a 120" wall) would close it.

## The interior pass: lighting, switching, quiet walls, the suite's north wall

2026-09-15. A reviewer noticed `RM-M-BED` has no room for a bedside table on the side the
doors are. Investigating it turned up a pattern rather than one bad dimension: **the
furniture in this house exists to satisfy clearance checks, not to plan rooms**, and the
lighting was struck against a can grid rather than against where people sleep and read. The
house priorities do not move — noise, air quality, thermal performance — and nothing below
touches a plumbing stack, a bearing line, a window station or an envelope detail.

**The mudroom had no light at all.** `RM-M-MUDROOM` is the front door and carried zero
luminaires; both devices standing in it switched lights somewhere else. Nothing reported it,
because `electrical.room_lighting` walks habitable rooms and this one is
`Occupancy.STORAGE`. Only half its ceiling was available: every `JOIST_BAY` duct on
`FS-S-WEST` — all thirteen `DU-M-ERV-R-*` radials — fans out through the WEST band, over the
bench and the window, and a 5" `ED-T-LT-CAN3` does not go there. So the cans went on the
east walk (on `D-M-ENTRY`'s and `D-M-MUD`'s shared RO centreline, both mid-bay on the truss
module) and the bench got a mark H sconce instead. The switch is a dimmer banked against
`ED-M-ENTRY-SW`, **not** on the north wall: `D-M-ENTRY` fills `W-M-N3` to within 6" of both
ends, which is the same reason that switch is where it is.

**`D-M-BED` moved 16" east and that was the only lever.** `from_node` resolves to the near
jamb, so the RO was x 154"..186" and the king's east face is at 143 7/8" — 10 1/8", against
a 24" nightstand. The bed cannot solve it by moving: west blocks `D-M-BATH2`, south and west
are the glazed walls, and the east wall carries `D-M-BED2`. One stud bay east keeps the
residue mod 16 and opens 26 1/8". The hinge stays at the east jamb so the leaf tucks into
the corner instead of sweeping the new nightstand.

**`ED-M-BED-RC2` stays behind the headboard, and that is the finding.** Relocating it east
with everything else opened an `electrical.receptacle_spacing` FAIL. The north wall's middle
space is 115 3/8" between the two ROs, so the single box that keeps every point within 6'
has to stand between x=98" and x=126 5/8" — and the bed covers all of it. 210.52(A) measures
wall, not furniture. The answer was a second box for the nightstand, not a move.

**Three quiet walls.** `W-M-BDN1`, `W-S-SBS` and `W-S-C2B` all had an empty cavity and no
channel; `INT_2X4_PARTITION` has been uninsulated since 2026-08-31, so there was not even a
batt to fall back on. All three went to a resilient-channel assembly, STC 34 → 48. `W-S-C2B`
is the one the docs never named — the 2026-08-30 pass walked the bedroom *partitions* and
this is a bearing wall. It is also the only one of the three collinear `W-S-C2*` segments
that could move alone: both its ends are tees, so the channel's 1/2" is absorbed at two
inside corners and no face steps in the open. `W-S-C2C` and `W-M-C2` are recorded as
accepted gaps for exactly that reason.

**Door widths, and a correction to the plan that prompted this.** `D-M-BED2` 2'-6" → 3'-0"
(still trimless — `trimless` lives on the DoorType, so `DT-INT-SWING36-TRIMLESS` had to be
minted, and it *replaced* the 30" rather than joining it, which would have left a catalog
entry this house does not hang). `D-M-BATH2` 2'-6" → 2'-8", growing **east**: the plan said
widen west, but this RO's west jamb is flush against `FX-M-BATH2-SINK` — the deliberate
2026-09-09 detail — and widening west would have put the opening into the vanity. 32" and
not 36" because `FURN-M-BED`'s west face is the binding dimension, not the wall run.
`D-M-BATH1` 2'-0" → 2'-6", with a `door_framing_module` suppression beside `D-M-BATH2`'s:
a 30" RO on `W-M-BAE` cuts a fourth stud at *every* station, so it is not a move that
moving can fix, and both legal stations are worse for the room.

### The laundry is not acoustically treated, by decision

`RM-M-LAUNDRY`'s ceiling gets nothing, and this is a decision recorded rather than a gap.
The LG WashTower sits under `RM-S-SUITEBATH` for 71.7% of the laundry footprint and under
`RM-S-SUITE` — the sleeping room — for the other 26.3%. `FS-S-WEST` has **no cavity
insulation** (`FloorSystem` has no field for it; it cannot even be expressed), **no
resilient channel**, and one 5/8" gypsum layer screwed direct to **open-web** trusses.

The house bought 522.2 LF of ceiling channel under exactly this argument —
`CR-LIVING-CEIL-RC` (`plan/assemblies.py`), scoped to `RM-M-LIVING` because bedrooms sit
over it. The laundry did not get it, and the structure is no excuse: it stands on
`FS-M-WEST`, a joisted deck, exactly like the living room does. The argument for leaving it
is scheduling and use, not construction — the machine runs when people are awake, and the
room is a dead-end off the hall behind a shut door, where the living room is the space the
household sits in of an evening under a bedroom. **Left as is, 2026-09-15**, and it is the
weaker half of the pair on its own merits.

The fix, if it is ever wanted, is one more `ConstructionRule` with
`applies_to="floor:ceiling_channel"` and `scope_ref="RM-M-LAUNDRY"` — the same shape as
`CR-LIVING-CEIL-RC`, and nothing else has to move for it.

`RM-B-ESS`, the 20 sf battery closet, also has no luminaire. Not in this pass's scope —
recorded so it reads as a choice rather than an oversight.

## 2026-09-16 — BM-SG-BLC goes flush; R507.4 is a flat 14' for a 6x6

The balcony is the porch roof, and flat roofs hang their joists. **Only the centre glulam went
flush.** The joists hang either side of it on LUS28Z hangers and still bear on top of BLW/BLE,
so the 9" drip cantilever and the four cast corner columns (and the moment arm in
`notes/balcony_moment_columns.md`) do not move. PT-SG-BR2/BF2 grow the joist depth to
10.59'/10.44'.

That was only possible because the "10'-0" at 48.3 ft², 5/32" of room" recorded on 2026-09-14
(above) was an **engine table bug**. `deck_tables.DECK_POST_HEIGHT_FT` stepped by tributary
area, and the 2018 IRC Table R507.4 that MN adopts is one height per size: 4x4 6'-9", 4x6 8',
6x6 14', 8x8 14', measured to the underside of the beam. Two engine gaps closed with it:
- A joist that crosses its bearing and cantilevers more than 8" past it was never tied. That
  left 0 ties on BLW/BLE and on the porch back beams, at 0 FAIL, and
  `uplift_path_coverage` now grades every declared bearing line.
- A derived face-mount hanger into a treated carrier is ZMAX and sized (LUS28Z).
