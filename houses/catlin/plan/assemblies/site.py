# haus: editable
# Catlin assemblies — the sunken-garden court, its walls, slab, stoop and steps.
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    Assembly,
    ControlLayer,
    Layer,
    LayerBound,
    LayerDatum,
    LayerExtent,
    LayerFunction,
    inch,
)
from library import (
    CONCRETE_BEARING,
)
from .mixes import EXPOSED_MIX, _WASH_FILM


# Freestanding sunken-garden / porch / balcony structure — exposed concrete, WASHED WHITE on
# the court face since 2026-09-13.
#
# ** THE WASH IS A DAYLIGHTING DEVICE, NOT A DECORATION, AND NOTHING IN THE ENGINE GRADES IT. **
# The court is a light well: a U of 12" walls enclosing the only thing the basement's south
# glazing looks at. Bare grey concrete has a diffuse reflectance of roughly 23-35%, so most of
# the daylight that reaches the court is absorbed there instead of delivered inside. An untinted
# white mineral silicate wash raises that to ~90% LRV. No check reads reflectance, albedo, LRV
# or SRI, so a 0-FAIL report says nothing whatever about whether this works — the reasoning is
# in DESIGN-LOG.md and the intent is here.
#
# ** IT IS LAYER 0 AND THAT IS THE COURT FACE, WHICH HAD TO BE VERIFIED RATHER THAN ASSUMED. **
# `resolve/topology.py` places layer 0 on the `-outward_sign * normal(start->end)` side, and
# the note in params/sunken_garden.py used to claim this component had lost its only closed
# loop and so took `UNRECOVERABLE_WINDING_OUTWARD_SIGN = +1`. That claim is STALE: `W-SG-ARCH`
# is a cast concrete Beam on the N-SG-MW -> N-SG-ME pair, which `resolve/orientation` counts as
# a loop edge, so it closes the walk
# ME->SE->SW->MW->ME, and `resolve_storey_windings(plan, "court-low")` resolves the `N-SG-ME`
# component to **-1.0**. With sign -1 layer 0 lands on the +normal side, which is the court
# side for all five walls (W1, E1, W2, E2 and S) — the consistency the params note means by
# "both side walls wind the same way around the garden". Re-run that diagnostic before moving
# any of these walls' nodes; it is the only thing holding the face down.
#
# ** THE WALL TOPS STAY BARE ON PURPOSE. ** A layer sits on a FACE. W-SG-E1's top is a walked
# threshold, and a mineral coating on a walked surface wears and is a slip question — the same
# reason SL-SG-FLOOR and the porch treads are out of scope.
#
# ** THE SILANE IS GONE WHERE THIS WASH GOES ** (see SUNKEN_GARDEN_COLUMN_12 below). A
# silane/siloxane repellent makes concrete hydrophobic and non-absorbent, which is the one
# condition a potassium silicate cannot bond to. They are alternatives, never a stack.
# ** THE OUTBOARD FACE IS DRAINED, NOT WATERPROOFED (2026-09-16). ** A standard 5/16" dimpleboard
# (DELTA-MS class, dimples to the wall) gives soil water a path down to the footing beds' tile
# at the footing, and it is the element `engineering/retaining_wall`'s "the drainage behind the
# wall works perfectly" names. The 60-mil membrane that sat under it is gone: both faces of every
# court wall are exterior, there is no occupied space to keep dry, the steel is galvanized, and
# nothing in the retaining calculation reads a membrane. The bonded-fabric drainage composite that
# preceded the dimpleboard was a premium over the standard sheet for no graded benefit. `LayerFunction.DRAINAGE`, not AIRGAP: a
# rainscreen dries a cladding, a drainage plane carries soil water down.
#
# ** TWO TAGS, ONE STACK DEPTH. ** W-SG-W2/E2/S are buried their whole height, so the board
# runs full height. W-SG-W1/E1 are exposed above the yard and carry ED-M-HP2-DISC and
# ED-M-STAIR-LT on that face, so their board stops at GRADE in `slot="retained-face"`: the
# row keeps its depth (both walls share `_COURT_AXIS_SHIFT` and the pour stays on the grid) and
# nothing is built above grade, so the exposed face is bare concrete. An unslotted band would
# still occupy the row full height and push the device face out.
_COURT_POUR_LAYERS = (
    Layer(name="wash", material_ref="silicate-wash-white", thickness=_WASH_FILM,
          function=LayerFunction.FINISH),
    Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
          function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
)
_COURT_DRAINAGE_IN = 0.3125  # `params/sunken_garden._SG_RETAINED_FACE_IN` transcribes this

SUNKEN_GARDEN_WALL = Assembly(
    tag="SUNKEN_GARDEN_WALL",
    layers=(
        *_COURT_POUR_LAYERS,
        Layer(name="dimple-board", material_ref="dimple-board",
              thickness=inch(_COURT_DRAINAGE_IN), function=LayerFunction.DRAINAGE,
              control={ControlLayer.DRAINAGE}, slot="retained-face",
              extent=LayerExtent(top=LayerBound(datum=LayerDatum.GRADE))),
    ),
    interfaces=(CONCRETE_BEARING,),
    source="catlin-house W-SG-W1/E1 — the porch box's side walls: court face washed white, outboard face dimpleboard below grade only (2026-09-16), exposed concrete above it",
)

SUNKEN_GARDEN_WALL_DRAINED = Assembly(
    tag="SUNKEN_GARDEN_WALL_DRAINED",
    layers=(
        *_COURT_POUR_LAYERS,
        Layer(name="dimple-board", material_ref="dimple-board",
              thickness=inch(_COURT_DRAINAGE_IN), function=LayerFunction.DRAINAGE,
              control={ControlLayer.DRAINAGE}),
    ),
    interfaces=(CONCRETE_BEARING,),
    source="catlin-house W-SG-W2/E2/S — the retaining U: court face washed white, outboard face dimpleboard full height; the 60-mil membrane and bonded drainage composite were replaced 2026-09-16 (both faces exterior, galvanized steel)",
)

# W-SG-ARCH, the BURIED grade beam / strut on the MW-ME line: the identical 12" court pour off
# the identical ticket, and the ONLY difference is that it carries no wash.
#
# ** IT SHARED SUNKEN_GARDEN_WALL UNTIL 2026-09-13 AND THE WASH IS WHAT SPLIT THEM. ** Sharing
# was right while the assembly was one bare concrete layer: same thickness, same EXPOSED_MIX, same
# $/cy. It stopped being right the moment layer 0 became a white mineral silicate wash, because
# this beam's own note says what it is — "its TOP is the rim slab's underside, so the court floor
# bears on it and NOTHING OF IT SHOWS". A wash on it is 3.6 SF of paint billed on a face that is
# under the court slab, cannot be reached, cannot be seen and cannot reflect anything. It went in
# silently: no check grades whether a FINISH layer is reachable, and `test_elevation_goldens.py`
# caught it only because the wash added a sixth `layer:wash` key where the court has five walls.
#
# ** THE BEAM MOVED AND THE COURT WALLS DID NOT, WHICH IS THE CHEAP DIRECTION. ** Five walls keep
# `SUNKEN_GARDEN_WALL`, so every test, condition gate and price key already written against that
# tag still names the same five subjects; one buried beam takes a new tag. The reverse split would
# have retagged five.
#
# Everything else is deliberately IDENTICAL — 12", EXPOSED_MIX, CONCRETE_BEARING — because it is
# literally the same pour off the same ticket (prices.toml: "one ticket for the whole court and
# entry"). Its `prices.toml` [wall_structure] row is split off at the SAME rate for that reason.
# This assembly is NOT the place to reconsider the mix; `unbalanced_fill=inch(0)` on the wall is
# where the fact that it retains nothing is already recorded.
SUNKEN_GARDEN_GRADE_BEAM_12 = Assembly(
    tag="SUNKEN_GARDEN_GRADE_BEAM_12",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
    ),
    interfaces=(CONCRETE_BEARING,),
    source="catlin-house W-SG-ARCH — the buried grade beam / strut on the N-SG-MW/N-SG-ME line, the same 12\" EXPOSED_MIX court pour off the same ticket as SUNKEN_GARDEN_WALL and split off it 2026-09-13 for one reason only: it carries NO mineral silicate wash, because its top is the rim slab's underside and nothing of it shows",
)

# The veneer grade beam W-SG-BRKBM: the same 12" court pour, plus the 2" isolation board
# that is the entire point of it.
#
# ** THE FOAM IS A LAYER WITH A POLYGON, NOT TWO ANNOTATIONS THAT DISAGREED. ** The wythe
# used to bear on FT-B-BRICK, a plinth cast on FT-B-S2/S3's own toe, and the break between
# the two was stated TWICE, inconsistently, and drawn never:
#
#   * FT-B-BRICK carried `assembly="FOOTING_FPSF_20"`, whose 2" `xps-bearing` layer DID
#     bill — 16.0 SF of xps:2.0 through `takeoff/envelope.py`'s `_LAYERED_SOLID_SCOPES`; and
#   * FB-B-BRICK dug a 2" `undercut` for that same 2" of space, which billed as 0.1 cy of
#     ASTM C33 #57 washed crushed stone, with `cast_foam_in_aggregate=True` beside it — a
#     bool with no thickness, no material and no R-value that emits nothing at all.
#
# One order of foam and one order of stone for one gap. A Footing resolves to a single
# extruded blob (`structural_solids_takeoff` bills its VOLUME keyed on the STRUCTURE layer),
# so neither claim had a polygon and the only thing actually occupying the 2" in the model
# was a void. Nothing grades a thermal break for continuity, so both spellings sat at
# 0 FAIL under 129 SF of brick standing in open air on both faces.
#
# A WALL's layers do resolve to real polygons, on real faces, in a stated order. That is why
# the break moved here: it can now be pointed at, measured, and pinned by a test.
#
# 15 psi (ASTM C578 Type X, basis 6), as everywhere else in this court: the board is a form
# face and a bond breaker here, not a bearing layer — the beam spans to W-SG-W1/E1 and
# delivers nothing to it, so `engineering/veneer_beam.py` never reads its grade.
SG_VENEER_BEAM_14 = Assembly(
    tag="SG_VENEER_BEAM_14",
    layers=(
        # Concrete first, board second — the same order every other foundation wall in this
        # house states (W-B-S2 runs concrete, waterproofing, xps-a, xps-b). Authored the other
        # way round `code.R316_4` FAILs it: the innermost layer is what that rule reads as
        # facing a room, and a bare 2" of XPS there needs a thermal barrier. It is also
        # simply the truth about the pour: the board is a form face applied to a side of the
        # concrete, not something the concrete sits on.
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
        Layer(name="xps-break", material_ref="xps", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    interfaces=(CONCRETE_BEARING,),
    source="sunken-garden veneer grade beam (2026-09-05): the court's own 12\" exposed pour, spanning W-SG-W1 to W-SG-E1 to carry W-B-BRICK clear of the house footing, with a 2\" 15 psi XPS isolation board (ASTM C578 Type X) on its north face against FT-B-S2/S3's trimmed toe — the same product as the court's IsolationBoards TB-SG-*, expressed as a layer so it resolves, bills and draws",
)

# The FIVE 12" round cast columns of the garden frame: PT-SG-FCOL (carrying the porch's
# two front beams) and the four balcony corner columns PT-SG-BR1/BR3/BF1/BF3, which
# replaced painted 6x6 wood pillars on pinned standoff bases in 2026-09-03's redesign.
# One assembly serves all five because they are one product — the same tube, the same mix,
# the same cage and the same top detail — and a second tag saying the same thing twice is
# a second place for the mix to drift.
#
# **THE FOUR CORNERS ARE THE BALCONY'S ENTIRE LATERAL SYSTEM.** They are FIXED at the base
# — doweled into the 12" wall tops of W-SG-W1/E1 — and the eight knee braces and two brace
# rails that used to do this job are gone with them. That is why the cage is not optional
# trim: see notes/balcony_moment_columns.md, which works the base moment by hand.
#
# **Why 12", and not the 10" first drafted or the 20" this replaced.** Cover, in one word.
# ACI 318-19 §20.5.1.3's 1-1/2" is a code minimum and not a hundred-year number; MnDOT uses
# 2.5-3" in the same salt regime. 2" of cover on a #5 cage inside #3 ties needs a 6-5/8"
# bar circle, and that needs a 12" round. 12" also drops klu/r and buys the beam seat its
# edge distance for nothing: the beam tie's anchor lands ~3-3/4" or more from the face where a
# 10" round left 2-3/4" against Simpson's 1-1/2" minimum. Centred on a 12" wall the round
# is flush with BOTH wall faces — no ledge to pond on, no interference with BF3's east
# leader, which keeps 1-1/2" clear.
#
# **Exposure is F3 + C2, not the F2 the 20" column carried.** Deicing salt reaches the
# porch below and planter runoff reaches the balcony above, which is external chloride on
# a freeze-thaw member: w/cm <= 0.40, f'c >= 5,000 psi, 6% +/-1.5 air, SCM caps per
# §19.3.3.4. IRC R402.2 asks the same of a salt-exposed porch. Do not reuse the 20"
# column's 4,000 psi / w/cm 0.45 mix here.
#
# **Galvanized bar, not epoxy and not stainless** (owner, 2026-09-02). Epoxy delaminates;
# stainless buys a century independent of cover but at 4-6x and with an austenitic thermal
# coefficient (~16e-6/C) that fights concrete's ~10-12e-6. HDG bar (ASTM A767 class 1,
# chromate-passivated, or A1094 continuous) already sacrifices zinc at any coating break.
#
# **NO GROUT ISLAND.** An exposed non-shrink grout island is a 10-20 year element — not
# air-entrained, and sitting at the wettest point on the column. The top is cast to line
# under the beam footprint with the wash screeded around it, and tolerance is taken up in
# the stainless standoff's shim pack. If a levelling bed proves unavoidable it is an EPOXY
# grout confined under the standoff plate, never a cementitious island with exposed
# shoulders. PIER_CONCRETE_12 carried its island until 2026-09-12 and says NO GROUT ISLAND
# now too; the follow-up this sentence opened is closed, and closed at the source rather than
# by a retype that only moved it.
#
# The assembly is required, not cosmetic: ``emit/draw/section.py::_solid_material`` would
# hatch a "12 round" correctly on the size string alone, but what the assembly does is put
# ``structure_material="concrete"`` on the BOM row so the [concrete] price table's material
# guard admits it — the same job PIER_CONCRETE_12 does for the six north-entry pours. It is a
# SEPARATE tag from PIER_CONCRETE_12 at the same diameter because the cage and the seat are
# different; billing them from one row would price an F3/C2 galvanized column at a
# sonotube's rate. That split stays, and since 2026-09-10 it runs between the COURT and the
# NORTH ENTRY — PIER_CONCRETE_12 is the six north-entry piers and nothing else.
#
# ** ALL FOUR OF THE COURT'S 12" ROUNDS (the balcony corners) ARE ON THIS TYPE. ** PT-SG-COL and
# PT-SG-FCOL retired with the centre line (2026-09-22); the history below is theirs.
# PT-SG-COL, the back-beam
# column, was on PIER_CONCRETE_12 while PT-SG-FCOL — the same 12" round, the same
# 120 15/16" height over the same z range, four feet away, holding up the other end of the
# same frame — was on this one. One tube order, one cage, one row.
#
# ** THE SPLIT WAS PRINTING THE FRONT COLUMN AS THE WEAKER OF THE TWO, WHICH IS BACKWARDS. **
# PIER_CONCRETE_12 names EXPOSED_MIX and this type named its mix in prose only, so
# `resolve/concrete.concrete_spec_for` returned None here and every calc on PT-SG-FCOL fell
# back to the presumptive 3,000 psi while PT-SG-COL was graded on the 5,000 both actually
# get. They are poured from the same truck on the same day. The `concrete=EXPOSED_MIX`
# below is that prose made readable; the source text is unchanged and still carries the
# detailing.
#
# ** IT DOES NOT CLOSE THE GROUT-ISLAND FOLLOW-UP, AND IT LOOKED LIKE IT DID. ** Retyping
# PT-SG-COL moved it off an island, but the island lived on PIER_CONCRETE_12, which is still
# a live type -- so the island rode the assembly to PT-BW-RE and PT-BW-RNE, the north entry's
# own beam seat. Struck at the source on 2026-09-12; PIER_CONCRETE_12 now says NO GROUT
# ISLAND as well, which is what the paragraph above wanted all along.
SUNKEN_GARDEN_COLUMN_12 = Assembly(
    tag="SUNKEN_GARDEN_COLUMN_12",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
    ),
    interfaces=(CONCRETE_BEARING,),
    # (single literal: the editable dialect forbids concatenated strings)
    # The 1/2"-1" STANDOFF is what holds exposed wood clear of the pour so the joint drains
    # and dries (AITC/WoodWorks). It must be STAINLESS, or hot-dip with an isolator — these
    # beams are treated glulam and will corrode plain steel. The standoff is at the beam
    # SOFFIT, so it does not touch the cap-and-butyl-tape order at the beam TOP
    # (TR-SG-CAP-*); those are two different joints on the same member.
    source="catlin-house garden columns (the four balcony corners PT-SG-BR1/BR3/BF1/BF3) — 12\" round cast concrete, FIXED at the base: the cage is a FABRICATED 8-INCH UNIT, not a field-bent detail — (4) #5 verticals with #3 rings @ 10\" o.c. at 2\" cover, 8\" out-to-out of rings, one of ten identical cross-sections house-wide (four court columns, six north-entry pours), lengths per pour, tied not welded; galvanized (ASTM A767 after fabrication, or A1094 coated stock bent after coating) — the fabricator's choice, NAMED ON THE ORDER; lapped class B ~30\" onto (4) #5 galvanized dowels cast with the wall pour below; wall-top cold joint roughened to 1/4\" amplitude with laitance removed and a bentonite or crystalline waterstop strip set inside the dowel circle (it is the wettest, saltiest elevation on the column and a documented chloride path); Sonotube Finish Free form seated in a plywood saddle collar screwed to the wall FACES (a flush tube leaves no wall top to anchor a collar to) and kicked to the porch framing, stripped to the form line; 5,000 psi, w/cm <= 0.40, 6% +/-1.5 air at 3/4\" or 3/8\" aggregate with SCM caps per ACI 318-19 §19.3.3.4 (class F3 + C2 — chloride tracked into a court that drains only to DRW-SG-MAIN and cannot shed it, plus planter runoff above; NOT washoff from the drive, which is 96 ft away north of the garage; IRC R402.2), air verified at the point of placement, 12-18\" lifts vibrated in the core and never on the cage; top CAST TO LINE under the beam footprint with a >=15 degree wash and >=1\" drip lip screeded around it (BIA Tech Note 36A) and NO grout island — tolerance taken in the SS316-SHIM-35 standoff shim pack (modeled at CN-SG-STDF-*, and its catalog record carries the detailing) or, if a bed is unavoidable, epoxy grout confined under the standoff plate; beam held down by a pair of HETA20Z embedded anchors cast into the column top, one each beam face, straps nailed with HDG 16d and isolated from the standoff with EPDM or HDPE; broom or float finish on the wash, never steel-trowelled (NRMCA CIP 2); wet-cure 7 days protected from freezing to 3,600 psi (ACI 306); NO SILANE/SILOXANE REPELLENT — all four columns are WASHED WHITE instead, with an untinted mineral silicate (2 coats) over the full cylindrical face, which is itself vapour-open weather protection and is the conventional alternative to a repellent on exposed concrete; a silane makes the pour hydrophobic and non-absorbent, which is the one condition a potassium silicate cannot bond to, so the two are alternatives and never a stack, and the ~10-YEARLY RECOAT OBLIGATION GOES WITH IT; the wash also matches the white centre posts (POST_WHITE_PAINT_DF / BEAM_WHITE_PAINT) this court already carries, which is what the old \"optional mineral paint\" line was reaching for; applied after the pour has cured and the court is backfilled, by the coating trade on its own arrival, never by the concrete sub",
)

# --- frost-protected shallow foundation, sunken-garden side -----------------------------
#
# The condition: the sunken garden's floor is at -9'-4" and the south house strips
# FT-B-S1/S2/S3 bottom out at -10'-0" — 8" of cover against MN Rules 1303.1600's 42" for
# Ramsey County (Zone II). Frost depth is measured from the LOWEST ADJACENT grade (IRC
# R403.1.4.1), and beside those footings that is the garden floor, not the -2'-10" site
# grade plane. `structural.frost_depth` derives a local grade per footing and names these
# three rather than comparing every footing to one global scalar. (A fourth, the veneer
# plinth FT-B-BRICK, sat here with 2" of NEGATIVE cover until 2026-09-05; it is retired —
# W-B-BRICK bears on the spanning grade beam W-SG-BRKBM now and touches no soil at all.)
#
# The answer is R403.3 — a frost-protected shallow foundation — under **Figure R403.3(3)**
# specifically: a heated building adjoining a slab-on-ground that is *not* maintained at
# 64 deg F, which is exactly a heated basement beside an open sunken court. Deepening the
# strips is the alternative and it is still not the move, though the reason changed: the
# plinth that used to lean on FT-B-S2/S3's 10" south toe is gone, but that toe now carries
# SG_VENEER_BEAM_14's isolation board at -8"..-10", so re-centring these strips still means
# re-deriving what stands beside them.
#
# Design air-freezing index **AFI 2500** (Minneapolis-St Paul; MN Rules 1303.1600 and the
# IRC's own Figure R403.3(2) put the Twin Cities near 2,500 F-days). Table R403.3(1) at
# AFI 2500 asks for:
#
#     vertical            R-6.7
#     horizontal, walls   R-1.7        dimension B = 24"
#     horizontal, corners R-4.9        dimension C = 40"
#
# The **vertical leg is already built**: the south basement walls compose off
# FOUNDATION_WALL_8_XPS4_CORE, 4" of XPS = R-20 against the table's R-6.7, and the core
# carries that face full height from -9'-0" to 0'-0" — the XPS itself was never the banded
# layer, only the skin over it was. Only the horizontal band is new.
#
# Both wings are specified far over the table rather than at it. R-5 and R-10 against R-1.7
# and R-4.9 is not generosity: 1" is the thinnest XPS anyone stocks, the labour and the
# excavation are identical at either thickness, and a band sitting exactly on a table minimum
# has nothing left if the design AFI is revised upward. 40 psi, the same slab-bearing grade
# as SLAB_FLOOR's, because the garden slab is cast on top of it.


# The footings the wings protect are plain strips on their stone bedding (FOOTING_EXPOSED_20); no foam under a footing (owner: creep).
# The 20x8 strip under every house and garage wall that is NOT one of the four
# sunken-garden-face runs. It carried no assembly at all until 2026-09-03, which meant its
# pour had nowhere to state a mix and ``structural_solids`` grouped it with every other
# bare pour under one blended $/cy. Naming it costs nothing in the estimate — ``[concrete]``
# keys on the solid CATEGORY qualified by assembly, and ``cli/prices.candidate_keys`` falls
# ``footing:FOOTING_20`` back to ``footing`` — and it is what lets the mix be said.
#
# No reinforcement, deliberately. These are plain strips under IRC Table R403.1, which is a
# prescriptive answer to a prescriptive question; a 4-6" projection on an 8" depth satisfies
# ACI §13.3 trivially, and a second, engineered authority on the same number buys nothing.
# The sunken-garden court's three retaining strips — 8'-0" x 1'-0", a different pour from
# the 20x8 house strip in every way that matters: wider, deeper, reinforced top and bottom
# (`_RETAINING_FOOTING_MAT` in params/sunken_garden.py), and poured from the EXPOSED mix
# rather than the buried one because it is the same concrete, the same day, as the wall
# standing on it. That last point is why `retaining_basis.footing_states` grades the footing
# on the WALL's specified f'c: a wall and its footing are one pour sequence off one ticket,
# and two mixes on one truck is not a thing that happens.
# The sunken-garden court floor and the garage's exterior service-door landing. Both poured
# bare until 2026-09-03 — no assembly at all, so no mix, no exposure class, no bar coating.
#
# The EXPOSED mix, and the F3 is earned rather than inherited: the court floor is at
# -9'-1 7/16", open to the sky, and it collects and holds every thaw; the garage landing
# takes salt off the drive directly.
#
# ** ONE LAYER EACH, AND DELIBERATELY NO BASE COURSE. ** Both of these certainly bear on
# stone in reality, and the obvious thing is to draw the 4" open-graded base its siblings
# carry. That would add 541 SF of `capillary-break-stone` and about $950 to the estimate —
# a real quantity change riding in on what is meant to be a specification change, and one
# nobody asked for. What these pours needed was somewhere to state their MIX. Whether their
# base course should be modelled is a separate question with its own money attached, and it
# should be answered on its own.
# ** THE THREE INTERIOR 12" BEARING WALLS KEEP `library.FOUNDATION_WALL_12_INT`, WHICH
# CARRIES NO MIX — a deliberate stopping point, not an oversight. ** Restating that assembly
# house-locally so it could name a house mix was written and then dropped: the
# three walls' tag appears in `plan/transitions.py` condition keys
# (`wall_foundation:FOUNDATION_WALL_12_INT|INT_2X6_BRG` and the storey-stack rim), so
# retagging them moves detail keys and the section-card goldens with them. Against that: the
# walls are inside the conditioned envelope with soil on neither face, so there is no
# chloride, no freeze-thaw, and black bar at the code-minimum mix is the right answer anyway.
# The blast radius is real and the durability gain is nil.
# Re-derived and kept on 2026-09-03, when the sweep that gave every other assembly-less
# pour in this house a mix reached these three. Same answer, plus one new reason to be
# comfortable with it: `structural.concrete_cover_meets_minimum` grades a pour's cover
# only where a `ReinforcementSpec` says there is bar to cover, and these three carry
# none, so the rule that would have cared is not being deprived of a subject.
GARDEN_COURT_SLAB = Assembly(
    tag="GARDEN_COURT_SLAB",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
    ),
    source="sunken-garden court floor: 3 1/2\" unconditioned slab, sky-exposed and saw-cut, F3+C2 mix. Its base course is not modelled",
)

# The sunken-garden court's open centre: 160 sf of turf inside the SL-SG-FLOOR rim
# (params/sunken_garden.GARDEN_FIELD). It is a USGA putting-green profile, built to the
# *Recommendations for a Method of Putting Green Construction*, 2018 revision, Steps 3-5.
#
# ** The stack is five courses, not four, and the fifth is why it is 18" and not 16". **
# USGA's cut is 16" where the gravel bridges the rootzone directly (Table 1). No gravel sold
# in this market bridges against a USGA rootzone, so this profile takes the Table 2 route —
# a 2-4" intermediate "choker" sand between rootzone and gravel — and USGA's depth for that
# build-up is 18-20". 18.00" is the shallow end, and 11.48 + 0.02 closes the stack on it
# exactly: `integrity.slab_thickness_matches_assembly` wants a top-down prefix summing to
# the authored thickness, and 11.48" is inside USGA's 12" +/- 1" rootzone.
#
# ** There is no fabric between rootzone and gravel, and its absence is the design. ** USGA
# Step 3 permits geotextile only "as a barrier between the subsoil and the gravel layer",
# and warns that "under no circumstances should geotextile fabric cover the drainage pipes
# or trenches". Fabric at the rootzone/gravel interface is a permeability discontinuity that
# fouls with fines and perches water; that interface is made by particle bridging, or by the
# choker sand when it cannot be. The one membrane here is at the BOTTOM, against the clay
# subgrade, which is the position USGA actually allows.
#
# ** `role="band"`, the same as the frost wings, and it costs nothing here. ** A band is "a
# buried layer of the ground, not a thing that holds anything up" — which is exactly what
# 18" of sand, stone and fabric is. It carries no STRUCTURE layer, and `integrity.assembly_layers`
# requires an `enclosure` to have one, so the two facts agree rather than fight.
#
# What a band costs elsewhere is that `resolve/site_earth._is_a_floor` stops reading it as an
# excavation floor — and here that is free, because SL-SG-FLOOR's outline spans the WHOLE
# court (site_earth reads `outline` and ignores voids), so the court is one excavation floor
# at one elevation either way. It also removes a hazard: with the field invisible to that
# derivation, no frost finding can ever name SL-SG-FIELD instead of SL-SG-FLOOR, whatever
# happens to the two `top_elevation`s.
#
# No `ConcreteSpec` on any layer and no `reinforcement`, because there is no concrete here.
# That is what keeps the field out of `concrete_mix_matches_exposure` (it drops from
# `with_spec`, and that check's UNKNOWN branch only fires when NO pour in the house states a
# mix) and out of `concrete_cover_meets_minimum`. Every layer is a `_BILLABLE` function, so
# all 160 sf of each bills through `envelope_layer_takeoff`; prices.toml carries a zero
# `slab:GARDEN_PUTTING_GREEN` row so `structural_solids_takeoff` does not ALSO order 8.15 cy
# of concrete that does not exist. Irrigation is an `[allowances]` line, not a layer.
GARDEN_PUTTING_GREEN = Assembly(
    tag="GARDEN_PUTTING_GREEN",
    role="band",
    layers=(
        Layer(name="turf", material_ref="kbg-sod", thickness=inch(0.5),
              function=LayerFunction.FINISH),
        # 11 1/2" nominal; the 0.02" the subgrade fabric takes comes out of here so the
        # build-up closes on a round 18" and `integrity.slab_thickness` has a boundary to
        # land on. 11.48" is inside USGA's 12" +/- 1".
        #
        # SHEATHING, not STRUCTURE, and the reason is billing as much as mechanics:
        # `takeoff/envelope._BILLABLE` deliberately excludes STRUCTURE (that layer's
        # quantity is the pour's own cubic yards, and this assembly's $/cy key is zeroed), so
        # a rootzone filed as structure would bill NOTHING — 12" of sand, the biggest single
        # line of this build-up, silently free. Same function the two granular courses below
        # carry, for the same reason: they are placed courses measured by the SF.
        Layer(name="rootzone", material_ref="rootzone-sand", thickness=inch(11.48),
              function=LayerFunction.SHEATHING),
        Layer(name="choker", material_ref="usga-choker-sand", thickness=inch(2.0),
              function=LayerFunction.SHEATHING),
        Layer(name="drainage-gravel", material_ref="usga-bridging-gravel", thickness=inch(4.0),
              function=LayerFunction.SHEATHING),
        Layer(name="subgrade-separation", material_ref="geotextile-separation", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE),
    ),
    source="sunken-garden court field: USGA Recommendations for a Method of Putting Green Construction (2018), Steps 3-5 — 12\" rootzone over a 2\" intermediate choker sand over 4\" bridging gravel, on a subgrade separation fabric, underdrained by FD-SG-FIELD into FB-SG-ARCH's soakaway course. 18\" is USGA's depth for the intermediate-layer build-up",
)

# D-B-PATIO's landing: the piece of the old flush garden floor the door still stands on,
# now a 7 1/4" block cast on the dropped court (params/sunken_garden.GARDEN_STOOP).
#
# Its own assembly rather than GARDEN_COURT_SLAB because `integrity.slab_thickness` wants a
# layer boundary at the authored thickness, and 7 1/4" is not 3 1/2". Same mix, same
# exposure, same reasoning as the court floor — this is the same pour on the same day.
GARDEN_STOOP = Assembly(
    tag="GARDEN_STOOP",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(7.25),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
    ),
    source="sunken-garden court: D-B-PATIO's landing, one 7 1/4\" riser above the court and 7 1/4\" below the threshold (IRC R311.3.2). Sky-exposed, F3+C2 mix; its base is the court floor",
)

GARAGE_STEP_6 = Assembly(
    tag="GARAGE_STEP_6",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(6.0),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
    ),
    source="the garage service door's exterior landing (IRC R311.7.6): 6\" outdoors, salt-splashed off the drive, F3+C2 mix. Its base course is not modelled",
)

# ** THE NORTH ENTRY'S FOUR CAST TIERS, WHICH REPLACED EIGHT DRILLED PIERS. **
# The terrace was framed KDAT boxes on eight 42"-deep piers until 2026-09-10. The piers were
# both wrong and unnecessary -- laid out east of a flight that runs WEST, so all eight stood
# under open ground -- and the owner's call is the ordinary detail: four solid pours,
# wedding-caked, on a compacted base. One riser thick each, EXPOSED_MIX because they are
# sky-exposed at a salted entry (ACI 318-19 F3 + C2), and every tier above the first is fully
# bedded on the one below it, so nothing here spans.
#
# ** THIS IS NOT FROST-FOUNDED AND THAT IS A DECISION, NOT AN OVERSIGHT. ** Minn. R.
# 1303.1600 puts Zone II at 42", and these bear about 6" down. The tiers will move with the
# ground; a monolithic pour moves as one piece, so what a winter costs is the joint at the
# TOP -- between the fourth tier and the deck landing, which is on piers and will not move --
# and the joint at the bottom to the SL-WK-C walk, which is on grade beside it. Riser uniformity
# (R311.7.5.1, 3/8") is the thing to watch at the top joint. A framed tier on the same base
# would have been worse: it settles into a cantilever off BM-BW-FE, which nothing in that
# assembly can do.
ENTRY_STEP_TIER = Assembly(
    tag="ENTRY_STEP_TIER",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(6.6),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
    ),
    source="north entry terrace: one cast tier, 6.8\" = one riser of the 34\" rise in five. Sky-exposed and salted, F3+C2 mix; bears on a compacted washed-rock base that is not modelled (notes/north_entry_structure.md Sec 3)",
)
