# haus: editable
# Catlin assemblies — retaining block, decks, entry screen, railings and flatwork.
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    Assembly,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerBound,
    LayerDatum,
    LayerExtent,
    LayerFunction,
    MasonrySpec,
    inch,
)
from .mixes import EXPOSED_MIX, _WASH_FILM


# Raised-garden outer face: Allan Block AB Stones (8"H x 12"D x 18"L, 12° setback), one unit
# deep, dry-stacked on 8" courses with the hollow cores filled with wall rock. No rebar — a
# gravity SRW is held by unit weight, setback and the drained backfill. The 12" layer is the
# unit's nominal depth; the free body reads AB's design depth off `srw=` in
# params/raised_garden.py. Tag kept (prices, trade rules, tests key on it).

# The SAME wall, washed white on its OUTBOARD (yard) face — the three perimeter legs only.
#
# ** WHY A VARIANT AND NOT A LAYER ON THE ASSEMBLY ABOVE. ** `params/raised_garden._APRON`
# shares one assembly across all five legs, and only three of them HAVE a yard-facing face.
# The RG graph is `WB-NW-SW-SE-NE-EB`, an open chain with no cycle (the U is open to the north
# and there is no north wall), so `_closed_walks` returns empty and the sign genuinely is
# `UNRECOVERABLE_WINDING_OUTWARD_SIGN = +1.0`. With sign +1 layer 0 lands on the -normal side,
# which for the three perimeter legs is exactly the yard:
#
#     W-RG-BLOCK   SW->SE, east   layer 0 south   yard is south of -33'-4"   OK
#     W-RG-WEST    NW->SW, south  layer 0 west    yard is west of x 4'-0"    OK
#     W-RG-EAST    SE->NE, north  layer 0 east    yard is east of x 32'-0"   OK
#
# The two 3'-6" balcony returns (`W-RG-WEST-BALCONY`, `W-RG-EAST-BALCONY`) are NOT part of that
# perimeter: they run east-west at y -10'-6" closing the U against the court walls, retaining
# terrace fill to the south with the court and the balcony underside to the north. They have no
# lawn-facing face at all, layer 0 on them would land in the FILL, and they sit in deep shade
# under the balcony. So they stay on plain `RETAINING_BLOCK_12` — a faithful reading of
# "exterior side, to reflect more light into the lawn", not a narrowing of it.
#
# ** THE BAND IS WALL_BASE + 8", AND IT MUST NOT BE "SIMPLIFIED" TO GRADE. ** Only the exposed
# 3'-4" gets coated; the buried 8" of embedment is backfill, not a reflector.
# `LayerDatum.GRADE` resolves to `plan.project.site.grade` — the SINGLE GLOBAL site grade,
# authored at -2'-10" — and the yard this wall actually stands in is -3'-4", so a GRADE band
# would sit 6" too high. That is the "grade cannot see a terrace" problem. The wall-relative
# datum is exact here instead: the wall runs 0'-0" to -4'-0", so WALL_BASE + 8" lands precisely
# on the authored -3'-4" yard.
#
# ** THE MATERIAL IS THE `-block` TAG, AND THAT IS A RENDER DECISION. ** Same product, same
# price, same pail as `silicate-wash-white` on the court's cast concrete; the split tag exists
# because a thin silicate film over dry-stacked SRW units telegraphs the unit module and the
# open joints straight through, where over as-cast concrete it reads as one flat plane. See
# library/materials/.
#
# ** THE SRW UNITS ARE THE WEAKEST SUBSTRATE IN THIS SCOPE AND THE RISK IS REAL. ** Dry-cast,
# integrally coloured units are far less absorbent than cast-in-place and frequently carry an
# INTEGRAL WATER REPELLENT — the one condition a potassium silicate cannot bond to. A test panel
# on a spare block precedes 245 SF, the open dry-stacked joints will take it unevenly,
# efflorescence driven out of the granular backfill can lift or stain it, and many SRW
# manufacturers void warranty on coatings. None of that is gradeable; it is in DESIGN-LOG.md.
RETAINING_BLOCK_12_WASHED = Assembly(
    tag="RETAINING_BLOCK_12_WASHED",
    layers=(
        Layer(name="wash", material_ref="silicate-wash-white-block", thickness=_WASH_FILM,
              function=LayerFunction.FINISH,
              extent=LayerExtent(
                  bottom=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(8)))),
        Layer(name="srw-block", material_ref="retaining-block", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE,
              masonry=MasonrySpec(unit_size="AB Stones 8x12x18 SRW unit", coursing=inch(8.0),
                                  core_fill=True)),
    ),
    source="raised garden — the three PERIMETER legs (W-RG-BLOCK/WEST/EAST), dry-stacked Allan Block AB Stones units washed white with an untinted mineral silicate (2 coats) over the exposed 3'-4\" only, to bounce light down onto a partially-sunny lawn; the two balcony returns keep plain RETAINING_BLOCK_12 because they face no lawn",
)

# Deck walking surfaces (single-layer). The joists/beams under them are separate framing
# members; these are just the finished plank surface so the slab reads with the right
# material in plans/IFC.
PORCH_DECK_COMPOSITE = Assembly(
    tag="PORCH_DECK_COMPOSITE",
    layers=(
        # The plank is the spanning walking surface (STRUCTURE); the 2x8 joists beneath it
        # are separate framing members.
        Layer(name="composite-deck", material_ref="composite-deck", thickness=inch(1.0),
              function=LayerFunction.STRUCTURE),
    ),
    # Laid with a 3/16" gap between boards: the gaps ARE the drainage path, which is why no
    # deck on this assembly is pitched. Installation instruction, not a modelled fact —
    # there is no gap field and one would buy nothing.
    source="catlin-house porch floor — composite decking on PT 2x8 joists, gapped 3/16\"",
)

# The breezeway's own glazed side wall was deleted 2026-09-12 with the rest of the breezeway
# (#70: a tag nothing references is deleted). Its stack — one self-spanning 16mm multiwall
# polycarbonate sheet, STRUCTURE and not CLADDING because it IS the wall — was generic
# enough to promote, and lives in the library now as `GLAZED_WALL_MULTIWALL_16MM`.

BALCONY_DECK_ALUMINUM = Assembly(
    tag="BALCONY_DECK_ALUMINUM",
    layers=(
        Layer(name="aluminum-deck", material_ref="aluminum-deck", thickness=inch(1.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house balcony — Wahoo AridDeck-style aluminum plank on 2x8 joists",
)

# The balcony's three beams BM-SG-BLW/BLC/BLE — treated SYP structural glulam, 3-1/2" x
# 11-7/8" (Anthony Power Preserved / Boise 24F-V5M1/SP, stocked through Boise Cascade
# Lakeville), clear-finished rather than painted. They replaced three site-built 3-ply KDAT
# 2x12s in 2026-09-03's balcony redesign.
#
# **One layer at the full 3-1/2", not a ply.** BEAM_KDAT and BEAM_WHITE_PAINT author ONE
# PLY and let ``Beam.size``'s ply count build the section up, because that is how a
# site-built beam is bought. A glulam is not built up: it arrives as one member, and its
# size string ("3.5x11.875") is a true section rather than a ply count, so the layer here
# is the whole width. Author it as a 1-1/2" ply and the takeoff bills 43% of a beam.
#
# 11-7/8" over the slimmer 9-1/2" is the owner's planter margin (~31% bending against ~48%);
# notes/balcony_moment_columns.md records both. Clear-finished, not white: these are the
# one member in the garden frame bought as a manufactured product, and a glulam's laminations
# are what it looks like.

# The breezeway's four 6x6 posts. NOT POST_WHITE_PAINT: that assembly is white-painted and
# is shared with the balcony pillars and the stairwell posts, which stay white (CLAUDE.md,
# "One exterior dark"), so pointing these at it would either recolour six pillars or claim a
# paint finish nobody is applying. These are bare KDAT 6x6 with a clear water repellent —
# the breezeway reads as structure, not as trim. 5.5" is the true 6x6 section, matching
# POST_WHITE_PAINT's body.
# ** THE NORTH ENTRY'S WEST SCREEN, LOWER PANEL: THIS IS A SHEAR WALL, NOT A SKIRT. **
# `W-BW-SCREEN` closes the west side of the passage from the pier tops at -1'-3 1/2" up to
# +4'-0", with `SC-BW-WEST`'s slats carrying on above it to the header soffit. Three jobs,
# one element (owner, 2026-09-10):
#
#  1. **It is the canopy's north-south lateral system.** The canopy is freestanding, its two
#     east columns are cast concrete fixed at the base, and this panel is what answers the
#     west side. The WEST face carries the shear panel; the east siding ply is not counted,
#     which is conservative and needs no new calc (it is a rated panel and could be).
#  2. **It is the guard.** `Wall.guard=True`; a solid wall admits no 4" sphere, which is the
#     reasoning `code.R312_1_3_guard_opening_limit` already applies to a masonry parapet.
#  3. **It closes the deck framing.** The panel starts at the pier tops, so the joists, the
#     two seat beams and the whole -1" to -1'-3 1/2" band are behind it rather than on show.
#     That is also what puts the shear straight into the piers instead of through the deck.
#
# 2x4 KDAT at 16" o.c. and no insulation: this is an outdoor screen, there is nothing on
# either side of it to condition, and a cavity that cannot dry is the one thing to avoid
# here. It carries NO `control` set for the same reason -- there is no assembly behind it to
# keep water off, so nothing here is a WRB and nothing should claim to be.
#
# Corrugated on the WEST FACE ONLY, `corrugated-panel-24`, which is the garage's own panel:
# the two structures already share a roof plane and a sheathing plane, and a different profile
# on the one wall standing under that joint would read as a mistake. The 7/8" flute is the
# drainage and vent cavity exactly as it is on the garage (no furring), open at the bottom.
#
# The EAST face takes no corrugated panel (owner, 2026-09-11). It stands UNDER the canopy
# roof, so it is a finish problem, not a weather problem, and buying the house's
# exposed-fastener steel for a sheltered face is paying weather money for it. `siding-in` is
# one 5/8" APA Rated Siding 303 panel doing both jobs -- a rated wood structural panel that
# takes paint. It is NOT named `cdx-in`: a layer called CDX that is not CDX is how the next
# reader gets it wrong.
ENTRY_SCREEN_WALL = Assembly(
    tag="ENTRY_SCREEN_WALL",
    layers=(
        Layer(name="siding-in", material_ref="siding-303-mdo", thickness=inch(0.625),
              function=LayerFunction.SHEATHING),
        Layer(name="stud", material_ref="kdat", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16))),
        Layer(name="cdx-out", material_ref="cdx-plywood", thickness=inch(0.625),
              function=LayerFunction.SHEATHING),
        Layer(name="cladding-out", material_ref="corrugated-panel-24", thickness=inch(0.875),
              function=LayerFunction.CLADDING),
    ),
    source="north entry west screen, lower panel — KDAT 2x4 at 16in o.c.; WEST face 5/8in CDX under 7/8in corrugated, EAST face one 5/8in APA Rated Siding 303 panel doing shear and finish together. The shear rests on the west face alone; the east ply is not counted. Guard per IRC R312.1, and the closure over the deck framing. No cavity fill and no control layers: an outdoor screen wall, sheltered on the east by the canopy",
)

# ** THE SAME SHEET, CARRIED DOWN OVER THE DECK FRAMING (owner, 2026-09-11). **
# `W-BW-SCREEN` bottoms at -0'-1" on BM-BW-SCSILL, and below it sit that 2x8 KDAT sill/rim,
# the two seat beams, and the ABU66SS standoff bases under PT-BW-CW/-CNW, all the way to the
# pier tops at -1'-3 1/2". An earlier pass left that band deliberately bare. This closes it:
# the same `corrugated-panel-24` run down 13 1/2" more, stopping 1" above the cast tops so the
# flutes stay open at the bottom, water leaves, and the column bases dry. A 13 1/2" drop off a
# continuous sheet is a cantilever, not a span, so there is no bottom girt and nothing to rot.
#
# ** ONE LAYER, AND IT IS STRUCTURE, NOT CLADDING. ** `integrity.assembly_layers`
# (checks/integrity/checks.py) errors on an `enclosure` assembly with no STRUCTURE layer, and
# a self-supporting skin whose one layer IS the element is the case BASEMENT_BRICK_VENEER and
# RETAINING_BLOCK_12 already set. Two consequences, written here rather than discovered:
#
#   * It bills through `takeoff/wall_structure.py`, not `envelope_layers` -- its own row of
#     about 7.4 SF, keyed `ENTRY_SCREEN_SKIRT:corrugated-panel-24` in prices.toml.
#   * `takeoff/fasteners.py::_exposed_fastener_cladding_layer` reads only the outermost
#     CLADDING layer, so the skirt's own field screws are NOT counted. Small and knowable.
#     (That same function is why dropping ENTRY_SCREEN_WALL's inner panel changed no screw
#     count either: only the outermost cladding layer was ever read.)
#
# ** WHY IT IS A SECOND ELEMENT AND NOT A LOWER `base_elevation` ON THE PANEL. ** `Layer.extent`
# is clamped to its wall (resolve/layer_bands.py), so a layer cannot run below its wall's base;
# and the framing solver takes its plate elevation from `rw.base_ref_z_m`
# (resolve/framing/solver.py) regardless of any band, so dropping the panel's base would put a
# sole plate on the pier tops and re-open the `structural.member_interference` clash with both
# seat beams that params/breezeway.py records. Two model elements for one physical sheet is
# the price of that, and it is the cheaper of the two.
ENTRY_SCREEN_SKIRT = Assembly(
    tag="ENTRY_SCREEN_SKIRT",
    layers=(
        Layer(name="skirt-panel", material_ref="corrugated-panel-24", thickness=inch(0.875),
              function=LayerFunction.STRUCTURE),
    ),
    source="north entry west screen, SKIRT — one 7/8\" 26ga corrugated sheet, the same panel and the same plane as ENTRY_SCREEN_WALL's west face, carried from the deck joist plane at -0'-1\" down to 1\" above the pier tops. Closes the sill/rim, the two seat beams and the column standoff bases. Self-supporting single skin: the one layer IS the element, per BASEMENT_BRICK_VENEER and RETAINING_BLOCK_12. Open at the bottom edge so the flutes drain",
)

RAILING_DARK_METAL = Assembly(
    tag="RAILING_DARK_METAL",
    layers=(
        Layer(name="rail-metal", material_ref="metal-dark-exterior", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house guards — near-black painted metal, the house's one exterior dark",
)

# Garage slab-on-grade. It carries 1" of below-slab XPS — the owner wants the garage floor
# insulated even though the structure is detached and unheated, so the choice is authored
# here rather than inferred from "is it conditioned".
# Still a separate assembly from the basement slab: this one keeps the 1" perimeter thermal
# break at the slab edge, and the two are ordered and poured as different scopes.
#
# **1" (owner).** This is an UNHEATED, detached, unconditioned building:
# `RM-GARAGE` is `conditioned=False`, so no code check grades this slab and every number in
# it is an owner choice. 3" was buying R-15 under a box with no heat in it. 1" keeps what
# the foam is actually here for — a capillary and thermal break so the slab is not in
# direct contact with clay, and a floor that does not read as bare ground underfoot — and
# leaves the option open if the garage is ever heated.
#
# **40 psi here, where the basement takes 25.** This is the one slab in the house that
# carries VEHICLE wheel loads, and a loaded wheel is a small contact patch, not a
# distributed floor load. 40 psi (ASTM C578 Type VI, e.g. Foamular 400) is the same
# slab-bearing grade FROST_WING_XPS_1IN/2 carry, so it is a grade
# already on the order. See SLAB_FLOOR above for why the psi lives in `source=`:
# there is one `xps` material tag with no compressive field, and prices.toml keys XPS on
# THICKNESS alone — so a 40 psi board and a 25 psi board cost the same in this estimate and
# do not in the yard.
GARAGE_SLAB_ON_GRADE = Assembly(
    tag="GARAGE_SLAB_ON_GRADE",
    layers=(
        # ** THE EXPOSED MIX, ON A SLAB THAT IS INDOORS. ** ACI's C2 is "concrete exposed to
        # moisture and an EXTERNAL source of chlorides", and a Minnesota garage floor is that
        # every winter: the chloride arrives on the car, drips off it, and pools on the slab
        # in the one place in the house that is never rinsed. Grading this as an interior
        # pour because it is under a roof is the classic version of this mistake.
        Layer(name="concrete", material_ref="concrete", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
        Layer(name="xps-below", material_ref="xps", thickness=inch(1.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        # Same stack, same reasoning, as SLAB_FLOOR above. R506.2.3 exempts a garage
        # from the vapour retarder; the foam does not care and the stone under it is
        # required either way, and an insulated garage floor is being asked to stay dry for
        # the same reason a basement floor is.
        Layer(name="vapour-retarder", material_ref="polyethylene", thickness=inch(0.01),
              function=LayerFunction.MEMBRANE, control={ControlLayer.VAPOR}),
        Layer(name="capillary-break", material_ref="capillary-break-stone", thickness=inch(4.0),
              function=LayerFunction.SHEATHING),
    ),
    source="catlin-house detached garage floor — 1\" below-slab XPS at 40 psi (ASTM C578 Type VI; vehicle wheel loads) over a 10-mil ASTM E1745 Class A vapour retarder on a 4\" open-graded capillary break (IRC R506.2.2); 3\" until 2026-08-31",
)


# The heat-pump equipment pad in the yard pocket east of the porch, SL-SG-HPPAD.
#
# GARAGE_SLAB_ON_GRADE minus the XPS and the vapour retarder, and both omissions are the
# point rather than a saving. Nothing above this slab is conditioned, so there is no heat
# to break and no floor to keep dry — a retarder under an exterior pad traps the water that
# gets in from the top and has nowhere to send it. What survives is the part that matters
# outdoors: 4" of open-graded stone so the pad drains and does not sit on a frost-susceptible
# clay lens and heave the units out of level.
#
# UNREINFORCED AND UNFROSTED, deliberately. This is not a foundation: it carries 333 lb of
# cabinet on eight legs, it is free to move with the ground, and an equipment pad that lifts
# an inch in February and comes back in April has done nothing a line set cannot absorb. A
# frost-depth footing under a mini-split is a foundation for a 333 lb building.
#
# The top is at -2'-8", two inches PROUD of the -2'-10" site grade, which is the one
# dimension here taken from the manufacturer: Gree's outdoor-unit instruction says to
# "install 2 in above the expected snow line", and the pad's own freeboard is the first two
# of the 20" that EQUIP_STAND_ALUM's 18" legs then add.
HP_PAD_ON_GRADE = Assembly(
    tag="HP_PAD_ON_GRADE",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(4.0),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
        Layer(name="capillary-break", material_ref="capillary-break-stone", thickness=inch(4.0),
              function=LayerFunction.SHEATHING),
    ),
    source="catlin-house equipment/stair pads, FOUR POURS ON ONE SPECIFICATION — SL-SG-HPPAD, the pocket equipment pad, 8.96 SF (x 29'-0\"..32'-7\", y -3'-4\"..-0'-10\") = 0.11 CY, and SL-SG-STAIRPAD, the porch stair's pad, its R311.7.6 bottom landing and the walk's south end, 27.5 SF (x 27'-6\"..36'-7 7/8\", y -9'-0\"..-6'-0\") = 0.34 CY, running east to walk leg D since 2026-09-23; SL-M-HP3PAD, added 2026-09-04, the north-side pad under EQ-M-HP3-OD, 6.9 SF (x 9'-9\"..13'-1\", y 36'-10 1/4\"..38'-11\") = 0.08 CY, in the 4'-0 1/2\" slot between the house and the garage — that cabinet had stood at grade since it was authored with no pad, no stand and no mount elevation at all; and SL-M-HP1PAD, added the same day, the north-face pad under EQ-M-HP1-OD, 9.27 SF (x 26'-3 1/4\"..29'-11 3/4\", y 36'-10\"..39'-4\") = 0.11 CY, east of the garage where a 24k unit's 40\" discharge has open front yard in front of it. 52.6 SF and 0.65 CY over the four. All four are 4\" thick on a 4\" open-graded stone base, all topped at -2'-8\", 2\" proud of grade, each falling at least 2% away from the house. No below-slab XPS and no vapour retarder: nothing over either is conditioned and nothing under them has to stay dry. The 2\" freeboard is Gree's outdoor-unit instruction (\"install 2 in above the expected snow line\"), which the 18\" stands on top of the equipment pad then clear by an order of magnitude. HISTORY, because the quantity moved twice in two days: 29.4 SF / 0.36 CY until 2026-09-03, when the cabinets turned to face SOUTH and one 56.9 SF pour carried both them and the new flight; then split on 2026-09-04, when the row and the flight swapped halves of the pocket (PT-SG-BR3 stands on the wall top the flight springs from, and left no walkable threshold in the south half). Two pours rather than one L: they are 2'-8\" apart in y, and a rectangle spanning both would be 94 SF of concrete to serve 40 — at this size the second form is cheaper than the 54 SF it saves. SL-SG-HPPAD lost 10.6 SF on 2026-09-04 when EQ-M-HP1-OD crossed to the north face and SL-M-HP1PAD was poured for it. Isolation joints where SL-SG-STAIRPAD meets W-SG-E1 and SL-WK-D; SL-SG-HPPAD, SL-M-HP3PAD and SL-M-HP1PAD each touch nothing, stopping about 3\" short of the house cladding so there is no joint to detail and the wall's runoff lands in gravel"
)

# The sidewalk, params/landscape_walk.py: 4" of fibre-only concrete (macro-synthetic, no mesh)
# on 6" of compacted MnDOT Class 5. Exterior mix, sonotube planting pockets at 4' o.c. with
# control joints on the same stations. notes/sidewalk_layout.md works the quantities.
SIDEWALK_FRC_CLASS5 = Assembly(
    tag="SIDEWALK_FRC_CLASS5",
    role="flatwork",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(4.0),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
        Layer(name="base", material_ref="mndot-class-5-base", thickness=inch(6.0),
              function=LayerFunction.SHEATHING),
    ),
    source="catlin-house sidewalk: 4 in fibre-reinforced (macro-synthetic 4 pcy, no mesh) exterior concrete on 6 in of MnDOT 3138 Class 5 aggregate base compacted to 100% standard Proctor; 16 in sonotube planting pockets at 4 ft o.c. with control joints on the pocket stations",
)

# The driveway (params/driveway.py): the walk's section, on a deeper base for wheel loads.
DRIVEWAY_FRC_CLASS5 = Assembly(
    tag="DRIVEWAY_FRC_CLASS5",
    role="flatwork",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(4.0),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
        Layer(name="base", material_ref="mndot-class-5-base", thickness=inch(8.0),
              function=LayerFunction.SHEATHING),
    ),
    source="catlin-house driveway: vehicle flatwork, 4 in fibre-reinforced (macro-synthetic 4 pcy, no mesh) exterior concrete, the ACI 332 residential driveway minimum; on 8 in of MnDOT 3138 Class 5 aggregate base compacted to 100% standard Proctor; no foam under the slab; K8 joint at the garage grade beam is 1 in 40 psi XPS (ASTM C578 Type VI) under 1/2 in traffic-rated polyurethane sealant; one longitudinal control joint on the centreline and transverse sawcuts at 10 ft o.c. max",
)
