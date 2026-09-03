# Uplift load path — roof to footing (2026-08-28)

The house had connectors at the ends of the load path and nothing in the middle. The sill was
anchored (MASA at 4' o.c.), the studs were tied to their top plates (SP6), the stacked corners
were strapped (CS16), and the *hung* member ends carried hangers (LSSR at the ridge beam, LUS
and HUCQ in the sunken garden). Between those, every joint where a member **bears** on
something was gravity and nails: 56 roof rafters birdsmouthed onto the attic top plate, ~290
floor-joist bearings across five floors, 34 garage truss heels, and every beam landing on a
post outside the breezeway.

The target is a continuous path with commodity parts — roughly FORTIFIED-Home detailing, not
an engineered wind design. Cost-effectiveness was the constraint that picked the parts.

## What is derived now

`packages/engine/src/typehaus/takeoff/uplift.py`, rules in `takeoff/hardware_config.py`
(`UpliftTieRules`). Nothing below is authored in this house — it follows the geometry, so a
wall that moves takes its hardware with it.

| Joint | Part | Count | Rule |
|---|---|---|---|
| Rafter / truss heel on its bearing wall | H2.5A | 56 + 34 | one per seated end |
| Floor joist on its bearing line | H2.5A | 258 | one per bearing joint (a lap is one joint) |
| Beam landing on a wood post | KBS1Z | 18 | one per beam end |
| Bottom plate of a framed wall on a framed floor band | LTP4 | 108 | 4' o.c., min 2 per wall |
| Across the floor band where framed walls stack | CS16 | 72 straps (2 coils) | 8 at the corners + 64 along the runs at 4' o.c. |
| Wood post standing on concrete | ABU44 | 2 | one per 4x4 that declares a bearing |
| Cast-in bolt under a post base landing on concrete | AB-058-10-SS | 10 | one per base, authored or derived |

Roughly **$590–1,160 of material** on a house whose hardware line was already $11.9k, plus
**$120–280** for the ten post-base anchors and **$44–80** for the two ABU44s the second pass
added. That ratio is the argument for doing it: it is the cheapest structural money in the
estimate.

The strapping row is an *extension* of a rule that already existed, not a new one. It used to
fire only at stacked framed-exterior corners, which gave this three-storey house **eight**
straps — two per 36 ft facade, with the middle thirty-two feet of every elevation holding the
storey above it on rim-board nailing. That is where uplift is largest on a 4:12 roof.
`WallTieRules.wall_strap_pitch_ft` is the run term, set to 4 ft so the mudsill anchors, the
tie plates and the straps all read as one rhythm rather than three schedules a framer has to
hold apart.

## The decisions, and why

**H2.5A everywhere a member bears, not a bigger tie.** The catalog already stocked it and
`prices.toml` already priced it. A heavier tie (H10A, or H2.5A in pairs) is the obvious
upgrade and it is one config field away — `UpliftTieRules.ties_per_bearing` — but it doubles
the largest count in the whole job, and the cheap tie at *every* joint buys far more than an
expensive tie at some of them.

**KBS1Z, not PC6Z, at a post/beam joint.** Cheaper and, per the manufacturer's tables,
stronger. PC6Z is catalogued (`ROLE_POST_CAP`) for the joints that want a true seated cap —
the round central column, a 6x6 under an attic-level beam — and is authored, never derived.

**One strap per beam end, not the matched pair.** A pair only fits where the beam stops at the
post. The balcony beams run past their pillars and have one reachable face. This is the same
correction `KneeBraceRules` already carries, where a pair rule billed twelve unbuildable
braces.

**LTP4 only where a wall stands on a *framed* floor band.** A wall standing on concrete is a
sill, and its MASA anchors already make that connection. Including it billed 179 plates
instead of 108, 71 of them a second anchor at a joint that was already paid for.

**No anchor bolts.** `ConnectorKind.ANCHOR_BOLT` and the `AB-050-10-BP` catalog record exist
now, and S-100 can schedule a diameter and an embedment for one. This house does not use them:
MASA at 4' o.c. already exceeds IRC R403.1.6's 6' maximum on every sill run, and bolting the
same plate again would be double-anchoring. The parts are there for a house that wants bolts.

## The 2026-08-28 second pass — the open items, closed

The first pass left four joints reported as **not evaluable** and a note saying so. Three of
them were a modelling gap and are now closed; the fourth is not a gap and is staying open on
purpose. A fifth thing turned up on the way, and it was the largest of the five.

**The three stairwell posts had a bearing all along.** `P-M-STRWELL-S`/`N` and
`P-M-STRLAND-SE` (plan/storeys/main.py) declared no `supported_by`, so the check could only
say it could not look. Their own comment had described what they stand on in prose since
2026-08-24 — the basement slab under the two columns, `W-B-CN` under the landing block — and
the field was simply never filled in. Filling it in did three things:

* **It found a cut-length error.** With the field unset the resolver hangs a post's TOP at
  the storey datum and lets its bottom fall where `height` puts it. `ft(9, 4)` put it at
  -9'-4", which is 2 9/16" **inside** a 3 1/2" slab whose top is at -9'-1 7/16". Nothing
  reported it, because nothing had been told the post was meant to reach the slab. Both are
  9'-1 7/16" now, and `structural.landing_post_bearing` was the check that noticed — it
  looks for a column topping out at the landing post's base, and the wrong length moved the
  top 2 9/16" off it. The same 1/16" correction applied to the block: the hole is 13 7/16",
  it was cut at 13.4", and its comment said 13 3/8".
* **The two columns now derive an ABU44** — the 4x4 rung of the same ladder the ten ABU66SS
  outside sit on, ZMAX rather than stainless because a basement slab is dry.
* **The block does not, and that is a rule now.** `UpliftTieRules.blocking_max_height_ft`
  reads a `Post` under 2'-0" as a squash block: a short piece filling a joist bay to carry a
  point reaction into concrete. It bears, and bearing IS its connection. 2'-0" is
  DCA6-2015 p.10's own threshold, the height above which a post needs bracing — i.e. where
  the industry already says a stick starts behaving like a column. The check reports the
  block as covered by direct bearing rather than as un-gradeable.

**The cast columns stay not evaluable, and that is the right answer.** There are six of
them, not two — `PR-BW-1..4` as well as `PT-SG-COL` and `PT-SG-FCOL` — and every one is a
concrete pour on a concrete pour. That joint is a doweled lap into the pier's own bar cage;
there is no connector to specify and no part to leave out. It is not even unpriced: the
`[concrete]` table's `column:PIER_CONCRETE_12` rate is struck itemised and names a four-bar
cage with ties inside it — **#5, not #4**, on all five 12" piers since 2026-09-03, and #4
only on the pre-2026-08-30 strike this sentence used to quote. What the model lacks is rebar as an *element*, which is a
much larger question than this work, and the `Dowel` primitive it does have is built for a
horizontal bar across a footing thermal break, not a vertical column lap. Reporting the joint
as broken would hand the reader an ABU that does not fit a 12" round pour; reporting it as
covered would claim a check on something never modelled. Un-gradeable is the honest third
answer, and the message now says the lap is inside the pier rate rather than just saying the
model has no rebar.

**And the one that was missed: every post base was billed without its bolt.** An ABU is a
stirrup with a hole in it. Simpson's published uplift and lateral values are taken *through*
a 5/8" anchor, and they ship none — "anchor bolt by others". Ten ABU66SS had been on the BOM
for two years with no anchor under any of them, which is a schedule that reads as complete
while being short the part its capacity is measured through. `post_base_anchor_rows` bills
one per base landing on concrete: ten of the twelve.

The two it skips are the point of the rule. `PT-SG-BR2`/`BF2` stand on **`FS-SG-PORCH`** —
the porch deck, not a pour — and a base on framing is bolted or screwed to it, fixings that
live inside the framing rate exactly as a joist hanger's nails do. That is why this is a
derivation over joints and **not** a `StructuralHardware.requires_role` on the base, which is
the mechanism that already puts an S-5! clamp under every CanDuit ring: `requires_role` is a
flat property of the *part*, and whether a base needs a cast-in bolt is a property of the
*joint*. The four sonotube piers are the same trap from the other side — `CN-BW-BASE-*` names
both members of its joint, so the authored-connector guard returns `PR-BW-1..4` alongside the
posts on them, and a first cut of this rule bought four bolts for four piers that have no
base at all.

The bolt is **304 stainless**, and that is not gold-plating: ten of the twelve fasten an
ABU66SS at grade, and a hot-dip bolt under a stainless stirrup in standing water corrodes
preferentially — the anchor, not the stirrup. The two on the dry basement slab can take a
galvanised bolt at $3-7. That is a ~$25 purchasing swap, filed with the MiTek ones below
rather than split into a second product for one role.

## What is still authored by hand

The derived rules skip any joint an authored `Connector` already names — that guard is what
keeps the sunken garden's and the breezeway's twenty connectors from being bought twice.

- 6 × ABU66SS under the balcony pillars, 4 × under the breezeway posts (`params/`)
- 4 × KBS1Z at the breezeway **roof** beams (its floor beams are derived)
- 4 × HUCQ410-SDS into the sunken garden's concrete beam pockets
- 2 × HGAM10 masonry gusset angles at the two cast columns (`H2.5A` until 2026-08-28)
- 4 × STHD holdowns at the exterior door jambs (main storey)

## What the model still cannot answer

`structural.uplift_load_path` reports every joint as covered or broken, and reports these as
**not evaluable** rather than pretending either way:

- **The six cast columns** on their cast footings — see the second-pass section above. The
  joint is a doweled lap, priced inside the pier rate, and there is no connector to name.
- **A lateral system for the porch and balcony.** `plans/TODO.md` carries this as an open
  question and it is *not* an uplift item, but it is the one thing that would put new
  hardware on `PT-SG-FCOL`. Today nothing bolts to that column: two beams land on its top and
  an authored HGAM10 gusset angle on the bearing plane holds them down. The MPB66Z moment base the TODO
  weighs is the only detail that would want the 5" of side cover the old 16" square section was
  chosen for, and it is not specified. Worth knowing before anyone reshapes that column, and
  The 16" round section left 3.76" and forecloses the MPB66Z there — priced, not overlooked,
  since a square section cost $478-1,327 against $304-633 for a fibre tube of the same
  height. The column is 20" round now, because it became the shared bearing for the two
  front beams AND `PT-SG-BF2` when the balcony's front pillar row moved 12" south, and 16"
  and 18" have no solution at that overhang. So the side cover came back as a side effect: a 20"
  round gives **5.76"** at a centred 6" plate's corners, more than the square had, on a
  $478-967 fibre tube. The option is open again; nothing is bolted to the column that uses
  it, and the four pillars that actually want an MPB66Z are still the corner ones on 12"
  concrete wall tops.
- **The SKU at the two beam-on-column bearings.**
  `CN-SG-TIE-COL` and `CN-SG-TIE-FCOL` sit on the bearing plane (the beam soffit = the
  column top) and were authored `H2.5A`, which `structural.uplift_load_path` accepted as
  coverage. But an H2.5A is a **wood-to-wood** tie — its own catalog record says so,
  "rafter/joist-to-plate", and its published values are taken through nails into lumber on
  both legs. At these two joints one leg has a 3-ply KDAT 2x12 to nail into and the other has
  a cast concrete column top, which it cannot reach. What the tie did as drawn was splice the
  two beam ends to each other across the pour; it did not hold either of them *down* to it.

  Both are now **HGAM10**, the part the raw hardware notes were pointing at all along: a
  masonry gusset angle, #14 screws into the wood leg and Titen Turbo into the concrete, with
  a 1½" minimum edge distance that both rounds satisfy as cast (6" to centre on the 12"
  round, 8" on the 16"). `library/hardware.py` stocks it under the new
  `ROLE_MASONRY_GUSSET_ANGLE`, and `prices.toml` carries a `[hardware]` row for it — the two
  things the open item was waiting for. It is its own role and not a second product on
  `ROLE_HURRICANE_TIE` because `hardware_for_role` holds exactly one item per role.

  **This is a correctness change, and it moves no finding.** `takeoff/uplift.py` keys the
  beam-to-post link on `ConnectorKind`, never on `Connector.size`, so every uplift finding is
  byte-identical either way; what changed is the BOM, where `authored_connector_rows` groups
  by `(kind, size)`. And the two Connectors were retyped, never deleted: `_is_concrete(seat)`
  is true at both and `"12 round"`/`"16 round"` are not stocked post sizes, so removing them
  would send all four beam-end links to `hardware=None` — four FAILs.

  Not the CCQM/CCTQM embedded column-cap family, which Simpson publish for solid concrete
  piers a minimum of 14" **square** with (4) #7 verticals; `PT-SG-COL` is a 12" round (113 in²)
  on a **(4) #5** cage (1.24 in², ACI 318-19 §10.6.1.1's 1% floor — it was #4 until
  2026-08-30, and this line said so until 2026-09-03). `PR-BW-1..4` are the same section on
  the same cage.

  Still open from that same raw notes list — an STHD on each axis with an SM1 holder, a
  KGLB5B beam seat, isolation between column and wood — is a menu for the lateral design
  above, not an outstanding uplift item.

  Worth saying what this does **not** affect: the column-to-footing joint below is the
  doweled lap already described, and every H2.5A left in the house (348, all derived, at
  rafter, truss-heel and floor-joist bearings) lands wood-on-wood exactly as published.
  After this change there are no authored H2.5A ties at all.
- **Capacity, everywhere.** The check reports coverage as UNKNOWN, never PASS. The model
  carries no design wind speed (`sheet.roof_framing.design_loads` says so), so "there is
  hardware here" is the only claim being made.

## Purchasing

Parts are catalogued as Simpson because that is what `library/hardware.py` and the published
load tables it cites already use. MiTek sells an equivalent for every one of them and is
usually cheaper:

| Simpson | MiTek | Joint |
|---|---|---|
| H2.5A | H2.5 | rafter / joist to plate |
| HGAM10 | — (masonry angle family) | wood beam down to a cast column top |
| LTP4 | TP37 class | plate to band |
| KBS1Z | — (use the strap tie family) | beam to post |
| ABU66 / ABU44 | ABU-equivalent standoff base | post to pier |
| AB-058-10-SS | any 5/8 in cast-in anchor + nut/washer | post base to concrete |
| MASA | MA-series mudsill anchor | sill to concrete |

Swapping is a purchasing decision, not a modelling one: `prices.toml` can carry the cheaper
number under the Simpson key. Changing the catalog would mean two products per role, which
`hardware_for_role` refuses by design.

## The beam-cap interaction

Anything added at a KDAT beam top has to respect `beam_water_protection.md` §2: AWC DCA6, no
aluminium against copper-treated lumber, and the formed caps are bedded **on** the butyl tape.
The 18 derived KBS1Z straps land on the pillar faces, not the beam tops, so they do not
disturb that order — but a future cap or seat at a beam top would.
