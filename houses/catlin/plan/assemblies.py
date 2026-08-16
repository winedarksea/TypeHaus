# haus: editable
# Catlin house assemblies — ported from catlin-house ifcplot (WP3.1).
# Layer order is interior → exterior. The exterior wall family is one 2x6 stack on every
# framed storey (sheathing / WRB / 2" polyiso / 2" EPS / furring / standing seam), so the
# sheathing plane and every control layer are continuous with no stud-depth jog.
from typehaus import (
    Assembly,
    AssemblyInterface,
    CavityFill,
    ConstructionRule,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerFunction,
    MasonrySpec,
    Material,
    inch,
)
from typehaus.model import PartitionLayout
from library import INT_2X4_PARTITION, STARTER_MATERIALS

# Named face roles the junction solver binds mixed-assembly corners/tees to (#44). The
# ``bearing`` role names the load-bearing layer whose face carries structural continuity
# through a return, so two walls are "continuous" when they publish the same bearing
# material (concrete↔concrete, SPF↔SPF) regardless of the finish/insulation around it —
# never by layer name or index. Variants inherit these from their base assembly.
_CONCRETE_BEARING = AssemblyInterface(role="bearing", layer_name="concrete", outboard=False)
_STUD_BEARING = AssemblyInterface(role="bearing", layer_name="stud", outboard=False)
_CMU_BEARING = AssemblyInterface(role="bearing", layer_name="cmu", outboard=False)

# Painted gypsum lining. Paint comes FIRST (interior->exterior order) because it is the
# room-side face and so the assembly's warm-side vapour retarder in the Glaser walk (IRC
# R702.7/.7.1: latex over gypsum is Class III, 1.0-10 perm). Bare gypsum reads ~30 perm —
# no retarder — which is not the wall that gets built.
# Colour lives on the `latex-paint` material, not on the Layer (no colour slot): a
# different wall colour is a different Material. `latex-paint-accent` + `ACCENT_GWB_LINING`
# below are that mechanism's accent-wall instance, swapped in per room/wall via
# `Room.wall_lining`/`wall_lining_exceptions` (see RM-S-BED1 in storeys/second.py).
_PAINT_FINISH = Layer(name="paint", material_ref="latex-paint", thickness=inch(0.01),
                      function=LayerFunction.FINISH,
                      control={ControlLayer.VAPOR})

# The accent film. Same name ("paint"), same thickness, same Class III vapour job — only the
# material (and so the colour) differs, which is what keeps an accent wall's Glaser walk and
# lining inset identical to its neighbours'.
_PAINT_FINISH_ACCENT = Layer(name="paint", material_ref="latex-paint-accent",
                             thickness=inch(0.01), function=LayerFunction.FINISH,
                             control={ControlLayer.VAPOR})

# The same film named per face, for partitions that carry their gypsum in `layers` and so
# have two room faces rather than one lining. `-a`/`-b` match the `gwb-a`/`gwb-b` each sits on.
_PAINT_FINISH_A = Layer(name="paint-a", material_ref="latex-paint", thickness=inch(0.01),
                        function=LayerFunction.FINISH,
                        control={ControlLayer.VAPOR})
_PAINT_FINISH_B = Layer(name="paint-b", material_ref="latex-paint", thickness=inch(0.01),
                        function=LayerFunction.FINISH,
                        control={ControlLayer.VAPOR})

_GWB_LINING = (
    _PAINT_FINISH,
    Layer(name="gwb-int", material_ref="gwb", thickness=inch(0.625),
          function=LayerFunction.FINISH),
)

# The accent-wall lining: `_GWB_LINING` with the accent film in place of the off-white one.
# Same gypsum sheet, same total thickness, so swapping it via `Room.wall_lining` /
# `wall_lining_exceptions` moves no face and changes no clear-floor inset — only the colour.
ACCENT_GWB_LINING = (
    _PAINT_FINISH_ACCENT,
    Layer(name="gwb-int", material_ref="gwb", thickness=inch(0.625),
          function=LayerFunction.FINISH),
)

# --- exterior wall family -----------------------------------------------------
# One 2x6 exterior wall type for main, second and attic. Storey nuance that is a
# purchasing note rather than a different assembly: the MAIN storey's studs are LSL
# (straightness under the 9' first-floor glazing/cabinet runs); second + attic are
# standard dimensional 2x6 SPF. Same 5.5" depth either way, so one assembly tells
# the truth about the geometry and the source string records the material split.
CATLIN_EXT_2X6 = Assembly(
    tag="CATLIN_EXT_2X6",
    layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", sill_gasket=inch(0.25)),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="sheathing", material_ref="struct-1-plywood", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        Layer(name="wrb", material_ref="air-barrier", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="polyiso", material_ref="polyiso", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="eps", material_ref="eps", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="furring", material_ref="spf", thickness=inch(0.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="1x4", direction="vertical")),
        Layer(name="cladding", material_ref="standing-seam", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ),
    interfaces=(_STUD_BEARING,),
    default_lining=_GWB_LINING,
    source="catlin-house ifcplot/catlin_house.py wall siding stack; main-storey studs are LSL, second/attic standard dimensional 2x6",
)

# --- hot roof (unvented; no batten framing grows — → 30 §WP3.11) --------------
CATLIN_ROOF = Assembly(
    tag="CATLIN_ROOF",
    layers=(
        Layer(name="rafter", material_ref="spf", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="11.875 I-joist"),
              # Target R-60 total, carried mostly by the 6" continuous exterior polyiso, not
              # the cavity batt. 5.5" batt tight to the ceiling side leaves 6.375" unfilled
              # against the deck deliberately — the continuous polyiso keeps the deck above
              # dew point, so that unfilled depth is the condensation margin, not a shortfall.
              cavity=CavityFill(material_ref="mineral-wool", thickness=inch(5.5),
                                framing_factor=0.07)),
        Layer(name="deck", material_ref="struct-1-plywood", thickness=inch(0.75),
              function=LayerFunction.SHEATHING),
        Layer(name="membrane", material_ref="air-barrier", thickness=inch(0.25),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="polyiso", material_ref="polyiso", thickness=inch(6.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="roof-membrane", material_ref="air-barrier", thickness=inch(0.25),
              function=LayerFunction.MEMBRANE, control={ControlLayer.WATER}),
        Layer(name="batten-gap", material_ref="spf", thickness=inch(0.75),
              function=LayerFunction.AIRGAP),
        Layer(name="roofing", material_ref="standing-seam", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ),
    default_lining=(
        _PAINT_FINISH,
        Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    source="catlin-house ifcplot/assemblies.py HOUSE_ROOF (hot roof, 4:12)",
)

# --- concrete family -----------------------------------------------------------
CATLIN_BASEMENT_12 = Assembly(
    tag="CATLIN_BASEMENT_12",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE),
        Layer(name="damp-proof", material_ref="air-barrier", thickness=inch(0.05),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="xps-a", material_ref="xps", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="xps-b", material_ref="xps", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        # Parge coat over mesh (2026-08-01): exposed XPS degrades under UV/impact, and here
        # the exposure runs the full south wall from the sunken garden floor to the
        # main-storey siding — bare pink foam was reading as the wall's finish. Reuses the
        # porch railing's Portland-cement stucco; rides outboard of everything so the
        # concrete face (the footings/damp-proofing/drain-tile datum) is untouched.
        Layer(name="parge", material_ref="stucco", thickness=inch(0.5),
              function=LayerFunction.FINISH),
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="catlin-house basement: 12\" wall + 2x2\" exterior XPS + parge",
)

# Basement slab-on-grade: 3" XPS below the slab (R-15 @ 40 psi compressive — rated for
# slab loading, not the lighter foundation-wall grade) breaks direct slab-to-clay contact.
CATLIN_SLAB_FLOOR = Assembly(
    tag="CATLIN_SLAB_FLOOR",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE),
        Layer(name="xps-below", material_ref="xps", thickness=inch(3.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    source="catlin-house basement slab: 3\" below-slab XPS, R-15 @ 40 psi compressive",
)

# Main-floor structural deck: 9" cast concrete over the (conditioned) basement, so it is an
# interior floor, not an envelope slab, and carries no insulation. The "INT" tag token is
# the codebase's signal for that (see CATLIN_CONC_12_INT, INT_2X6_PLUMBING) — it tells the
# prescriptive-energy table to skip this deck instead of holding it to the R-10 slab minimum.
CATLIN_DECK_9_INT = Assembly(
    tag="CATLIN_DECK_9_INT",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(9.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="catlin-house main-floor deck — 9\" cast structural slab over the basement",
)

CATLIN_CONC_12_INT = Assembly(
    tag="CATLIN_CONC_12_INT",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
)

CATLIN_CONC_8_INT = Assembly(
    tag="CATLIN_CONC_8_INT",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
)

# Freestanding sunken-garden / porch / balcony structure — exposed concrete.
SUNKEN_GARDEN_WALL = Assembly(
    tag="SUNKEN_GARDEN_WALL",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="catlin-house sunken_garden_retaining_wall_detail.py",
)

# The porch "front" (arched) cross-wall is 16" so it reads as three piers + an arched
# beam AND gives the porch-floor joists 3.5" of bearing on top of the sill plate.
SUNKEN_GARDEN_ARCH_16 = Assembly(
    tag="SUNKEN_GARDEN_ARCH_16",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(16.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="catlin-house porch arched front wall — 16\" for joist bearing (3.5\") + arch piers",
)

# Masonry "railing" / parapet on top of the porch front + side walls. The balcony 6x6
# pillars land in the grout-filled CMU cores. Layer order interior (porch/deck side) ->
# exterior (garden side): stucco on the CMU back, grout-filled CMU, air gap, white face brick.
PORCH_RAILING_MASONRY = Assembly(
    tag="PORCH_RAILING_MASONRY",
    layers=(
        Layer(name="stucco", material_ref="stucco", thickness=inch(0.5),
              function=LayerFunction.FINISH),
        Layer(name="cmu", material_ref="cmu", thickness=inch(7.625),
              function=LayerFunction.STRUCTURE,
              masonry=MasonrySpec(unit_size="8x8x16 CMU", core_fill=True,
                                  rebar_spacing=inch(48))),
        Layer(name="air-gap", material_ref="air-barrier", thickness=inch(1.0),
              function=LayerFunction.AIRGAP),
        Layer(name="brick", material_ref="white-brick", thickness=inch(3.625),
              function=LayerFunction.CLADDING),
    ),
    interfaces=(_CMU_BEARING,),
    source="catlin-house porch railing — white brick / air gap / grouted CMU / stucco",
)

# Glazed-brick veneer over the exposed basement wall (sunken garden excavated against it).
# Two layers only, on purpose: unlike PORCH_RAILING_MASONRY there is no CMU backer wythe,
# because the existing CATLIN_BASEMENT_12 concrete (damp-proofing + 4" XPS + parge already
# outboard) IS the backer — this wall stands 1" off it on masonry ties. No STRUCTURE layer
# either (`structure_index()` returns None, not an error) — a fictional backer would
# double-count concrete already modeled by W-B-S2/W-B-S3. No `interfaces`: non-bearing.
BASEMENT_BRICK_VENEER = Assembly(
    tag="BASEMENT_BRICK_VENEER",
    layers=(
        Layer(name="air-gap", material_ref="air-barrier", thickness=inch(1.0),
              function=LayerFunction.AIRGAP),
        # STRUCTURE, not CLADDING: this wythe has nothing behind it in this assembly (the
        # backer is a *different wall*), so it has to be the structure layer or
        # integrity.assembly_layers finds none. Same precedent as RETAINING_BLOCK_12.
        Layer(name="brick", material_ref="glazed-green-brick", thickness=inch(3.625),
              function=LayerFunction.STRUCTURE),
    ),
    source="basement south veneer over the sunken garden — glazed green brick, 1\" airgap, corrugated masonry ties back to the existing CATLIN_BASEMENT_12 wall (no CMU backer: the basement concrete is the backer, unlike PORCH_RAILING_MASONRY)",
)

# Raised-garden outer face: dry-stacked segmental retaining-wall block, one unit deep. No
# core fill and no rebar — an SRW wall of this height is held by unit weight, batter and
# the granular backfill behind it, which is exactly why it is the *outer* face here while
# the sunken-garden retaining wall (cast concrete) takes the inner one.
RETAINING_BLOCK_12 = Assembly(
    tag="RETAINING_BLOCK_12",
    layers=(
        Layer(name="srw-block", material_ref="retaining-block", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE,
              masonry=MasonrySpec(unit_size="12x6x18 SRW block", coursing=inch(6.0),
                                  core_fill=False)),
    ),
    source="raised garden (brief.md follow-up) — outer face, dry-stacked SRW units",
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
    source="catlin-house porch floor — composite decking on PT 2x8 joists",
)

# --- breezeway enclosure -------------------------------------------------------
# Two glazing assemblies, deliberately without insulation, membrane or deck layers: the
# breezeway is an unheated shelter between two heated buildings, so its envelope only sheds
# water/cuts wind and must not fall inside an energy check. Single-layer sheet assemblies
# because the sheet *is* the whole construction — the 2x6 rafters are real Beams
# (params/breezeway.py, on their own drainage-wedge elevations) rather than a framing layer
# here, so a rafter layer would frame nothing and would mislabel the polycarbonate "spf" in
# every consumer that reads an assembly's structure layer (GLB colour, viewer, cut detail).
BREEZEWAY_ROOF_GLAZING = Assembly(
    tag="BREEZEWAY_ROOF_GLAZING",
    layers=(
        Layer(name="glazing", material_ref="polycarbonate-multiwall", thickness=inch(0.63),
              function=LayerFunction.STRUCTURE),
    ),
    source="breezeway roof — two 4'x4' pieces of one 16mm 5-wall sheet on drainage wedges over 2x6 rafters",
)

# The east and west walls: one 4'x8' sheet each, standing in a U-channel at the deck and an
# F-channel at the beam, with no framing of its own — the 6x6 posts either end are the frame.
# The sheet is STRUCTURE here, not CLADDING: it is the whole wall and it spans the 4'-0"
# between those posts unaided, exactly as PORCH_DECK_COMPOSITE's single plank layer is the
# spanning walking surface. On the roof, where 2x6 rafters do the spanning, it is cladding.
BREEZEWAY_GLAZED_WALL = Assembly(
    tag="BREEZEWAY_GLAZED_WALL",
    layers=(
        Layer(name="glazing", material_ref="polycarbonate-multiwall", thickness=inch(0.63),
              function=LayerFunction.STRUCTURE),
    ),
    source="breezeway side walls — one 4'x8' 16mm multiwall sheet per side, bird-safety film",
)

BALCONY_DECK_ALUMINUM = Assembly(
    tag="BALCONY_DECK_ALUMINUM",
    layers=(
        Layer(name="aluminum-deck", material_ref="aluminum-deck", thickness=inch(1.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house balcony — Wahoo AridDeck-style aluminum plank on 2x8 joists",
)

# Finish-only assembly for the balcony 6x6 pillars so they render (glTF) and read (IFC) as
# white-painted rather than the default bare-wood post colour. Single 5.5" layer = the 6x6.
POST_WHITE_PAINT = Assembly(
    tag="POST_WHITE_PAINT",
    layers=(
        Layer(name="post-paint-white", material_ref="post-paint-white", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house balcony 6x6 pillars — white-painted finish",
)

# Guards were split off POST_WHITE_PAINT on 2026-08-01 (they shared it with the balcony's
# 6x6 pillars/knee braces, which must stay white) — same 5.5" body, only the colour differs.
# Metal, not painted PT: `_solid_color` reads the STRUCTURE layer's material, so
# metal-dark-exterior here is what darkens the railings in both renderers.
# The suite bedroom's four elm tudor posts (plans/TODO.md §Hardwood): same pattern as
# POST_WHITE_PAINT — the STRUCTURE material colours the solid and names the species for the
# wood_surfaces takeoff. 6.125" body = the custom timber, sheathing to drywall face, a
# deviation within W-S-W3's stud line, deliberately not a change to CATLIN_EXT_2X6.
ELM_TIMBER = Assembly(
    tag="ELM_TIMBER",
    layers=(
        Layer(name="elm-timber", material_ref="elm-timber", thickness=inch(6.125),
              function=LayerFunction.STRUCTURE),
    ),
    source="plans/TODO.md — suite tudor posts, elm 6-1/8\" square",
)

RAILING_DARK_METAL = Assembly(
    tag="RAILING_DARK_METAL",
    layers=(
        Layer(name="rail-metal", material_ref="metal-dark-exterior", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house guards — near-black painted metal, the house's one exterior dark",
)

# --- garage (freestanding: ICF stem + 2x6 wood wall) ---------------------------
# The form's two published dimensions, as constants rather than literals inside the layer
# stack: params/foundations.py aligns the stem off the EPS thickness (the exterior foam
# face has to land on the same node line the wood wall's zip-R face uses) and insets the
# slab off the whole 11" section. Repeating either number there would let the two drift.
GARAGE_ICF_EPS = inch(2.5)
GARAGE_ICF_CORE = inch(6.0)

GARAGE_ICF_6 = Assembly(
    tag="GARAGE_ICF_6",
    layers=(
        Layer(name="eps-int", material_ref="icf-eps", thickness=GARAGE_ICF_EPS,
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="concrete", material_ref="concrete", thickness=GARAGE_ICF_CORE,
              function=LayerFunction.STRUCTURE,
              masonry=MasonrySpec(unit_size="ICF-6", core_fill=True,
                                  rebar_spacing=inch(16))),
        Layer(name="eps-ext", material_ref="icf-eps", thickness=GARAGE_ICF_EPS,
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    source="catlin-house ifcplot/assemblies.py GARAGE_ICF (6\" core)",
)

GARAGE_WALL_2X6 = Assembly(
    tag="GARAGE_WALL_2X6",
    layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", sill_gasket=inch(0.25)),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="zip-r", material_ref="zip-r", thickness=inch(1.5),
              function=LayerFunction.SHEATHING,
              control={ControlLayer.AIR, ControlLayer.WATER, ControlLayer.THERMAL}),
        Layer(name="rainscreen", material_ref="spf", thickness=inch(0.375),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="1x4", direction="vertical")),
        Layer(name="cladding", material_ref="standing-seam", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ),
    default_lining=_GWB_LINING,
    source="catlin-house ifcplot/assemblies.py GARAGE_WALL",
)

# Garage slab-on-grade. It now carries the same 3" of below-slab XPS as CATLIN_SLAB_FLOOR —
# the owner wants the garage floor insulated even though the structure is detached and
# unheated, so the choice is authored here rather than inferred from "is it conditioned".
# Still a separate assembly from the basement slab: this one keeps the 1" perimeter thermal
# break at the slab edge, and the two are ordered and poured as different scopes.
GARAGE_SLAB_ON_GRADE = Assembly(
    tag="GARAGE_SLAB_ON_GRADE",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE),
        Layer(name="xps-below", material_ref="xps", thickness=inch(3.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    source="catlin-house detached garage floor — 3\" below-slab XPS on compacted base",
)

GARAGE_ROOF = Assembly(
    tag="GARAGE_ROOF",
    layers=(
        # Raised-heel trusses (2x4 chords + webs) with a 9.25" energy heel so full
        # insulation depth carries over the top plate; the truss carries the ridge, so no
        # ridge beam is required. `haus` frames the chords/webs/heel as first-class members.
        Layer(name="truss", material_ref="spf", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", roof_frame="truss",
                                  heel_height=inch(9.25),
                                  chord_member="2x4", web_member="2x4")),
        Layer(name="deck", material_ref="struct-1-plywood", thickness=inch(0.75),
              function=LayerFunction.SHEATHING),
        Layer(name="membrane", material_ref="air-barrier", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="roofing", material_ref="standing-seam", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ),
)

# --- interior ------------------------------------------------------------------
# These partitions carry gypsum in `layers` (not a lining), so paint is authored face by
# face as `paint-a`/`paint-b`. Both faces separate conditioned rooms, so there's no vapour
# drive to control — the paint is here purely for the finish takeoff. Deliberately unpainted
# elsewhere: SAUNA_* (T&G/foil-polyiso is already the vapour/air control, no paint in a
# löyly room), CATLIN_MUDROOM_INT_2X6_EXPOSED (exposed wood faces, already hardwax-oil
# finished), the masonry/concrete/deck/glazing assemblies (no gypsum face), POST_WHITE_PAINT
# (its own exterior-paint material), and INT_2X4_PARTITION (a tested STC assembly — see
# library/assemblies.py for why it doesn't get layers added).
CATLIN_INT_2X6_BRG = Assembly(
    tag="CATLIN_INT_2X6_BRG",
    layers=(
        _PAINT_FINISH_A,
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        _PAINT_FINISH_B,
    ),
    interfaces=(_STUD_BEARING,),
    source="catlin-house centerline bearing wall (2x6)",
)

INT_2X6_PLUMBING = Assembly(
    tag="INT_2X6_PLUMBING",
    layers=(
        _PAINT_FINISH_A,
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        _PAINT_FINISH_B,
    ),
    interfaces=(_STUD_BEARING,),
    source="wet wall — depth for 3\" stacks",
)

# Non-bearing wet walls: 2x4 studs staggered on 2x6 plates — same 5.5" pipe cavity as
# INT_2X6_PLUMBING (which stays for any *bearing* wet wall, needing continuous studs),
# but the staggered studs decouple the two faces for noise and leave a continuous
# cavity that never needs a stud bored on the way through.
INT_2X6_STAGGERED_PLUMBING = Assembly(
    tag="INT_2X6_STAGGERED_PLUMBING",
    layers=(
        _PAINT_FINISH_A,
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="staggered-studs", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", plate_member="2x6", spacing=inch(16),
                                  layout=PartitionLayout.STAGGERED,
                                  stagger_gap=inch(1.5)),
              cavity=CavityFill(material_ref="fiberglass", thickness=inch(3.5))),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        _PAINT_FINISH_B,
    ),
    interfaces=(_STUD_BEARING,),
    source="wet wall, non-bearing — 2x4 staggered on 2x6 plates per USG/GA WP 5530 (16\" o.c. per face, 8\" combined), 3.5\" fiberglass sound batt",
)

# --- energy storage closet -------------------------------------------------------
# The ESS closet's partitions (notes/backup_power.md, 2026-08-02), an owner decision not a
# code requirement (IRC R327 permits an ESS in an ordinary utility closet; that's why
# `advisory.ess_enclosure`, not the code check, grades it): steel studs (no combustible
# framing around the 14 kWh lithium pack), 5/8" Type X both faces (R302.6-style fire
# membrane, both directions — the fire may start *inside* this closet). No cavity fill on
# purpose: heat should reach AL-B-ESS-HEAT outside, not be insulated away from it.
# The "INT" tag token is load-bearing: `mn_energy._is_interior_assembly` and the IFC
# emitter's IsExternal both key off it to keep this out of the R-21 exterior-wall table.
INT_ESS_CLOSET_STEEL = Assembly(
    tag="INT_ESS_CLOSET_STEEL",
    layers=(
        _PAINT_FINISH_A,
        Layer(name="gwb-x-a", material_ref="gwb-x", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="steel-stud", material_ref="steel-stud", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16))),
        Layer(name="gwb-x-b", material_ref="gwb-x", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        _PAINT_FINISH_B,
    ),
    source="owner ESS-closet standard, 2026-08-02: 25 ga. steel C-stud at 16 in. o.c. with 5/8 in. Type X both faces (notes/backup_power.md). Not a code-required rated assembly and not claimed as one — no tested assembly number is cited.",
)

# --- sauna ---------------------------------------------------------------------
# The hot side of a sauna is its own wall type, not a lining override on a partition:
# the foil-faced polyiso is the vapour/air control layer and the T&G liner is a
# low-conductivity species chosen so the boards stay touchable at löyly temperatures.
# Per notes/sauna_basement_wall_detail.md.
_SAUNA_LINER = (
    Layer(name="tg-liner", material_ref="sauna-tg", thickness=inch(1.0),
          function=LayerFunction.FINISH),
    Layer(name="liner-furring", material_ref="struct-1-plywood", thickness=inch(0.5),
          function=LayerFunction.FURRING,
          framing=FramingSpec(member="1x4", direction="horizontal")),
    Layer(name="foil-polyiso", material_ref="polyiso-foil", thickness=inch(2.0),
          function=LayerFunction.INSULATION,
          control={ControlLayer.THERMAL, ControlLayer.VAPOR, ControlLayer.AIR}),
)

# Sauna partition: hot side liner, 2x4 framing, gwb on the cold side.
SAUNA_2X4 = Assembly(
    tag="SAUNA_2X4",
    layers=(
        *_SAUNA_LINER,
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x4"),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="gwb-cold", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    interfaces=(_STUD_BEARING,),
    source="catlin-house sauna_basement_wall_detail.py + notes/sauna_basement_wall_detail.md",
)

# Where the sauna's hot side lands on the center concrete wall there is no framing to
# fill — the liner stack applies directly to the concrete.
SAUNA_LINER_ON_CONCRETE = Assembly(
    tag="SAUNA_LINER_ON_CONCRETE",
    layers=(
        *_SAUNA_LINER,
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="catlin-house sauna_basement_wall_detail.py (liner on the center bearing wall)",
)

# --- mudroom exposed-stud wall ---------------------------------------------------
# W-M-STRW only. No default_lining, deliberately (like SAUNA_2X4): the mudroom face is a
# finished face made of the framing itself, not drywall left off. The open 2x6 bays are the
# coat nooks, so no cavity fill either — insulating them would fill the nooks, and both
# sides are conditioned anyway. Stair side closes with 3/4" cabinet plywood: stair finish
# and screw-anywhere hook backing at once. "INT" in the tag is load-bearing (see
# CATLIN_CONC_12_INT, INT_2X6_PLUMBING, _is_interior_assembly in mn_energy.py) — without it
# the uninsulated bays would fail as an exterior wall against R-21.
CATLIN_MUDROOM_INT_2X6_EXPOSED = Assembly(
    tag="CATLIN_MUDROOM_INT_2X6_EXPOSED",
    layers=(
        Layer(name="stud", material_ref="df-select-s4s", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="ply-stair", material_ref="cabinet-plywood", thickness=inch(0.75),
              function=LayerFunction.FINISH),
    ),
    interfaces=(_STUD_BEARING,),
    source="plans/TODO.md — mudroom coat wall: exposed Select Structural S4S 2x6 DF studs on the mudroom face (open bays = coat nooks), 3/4\" cabinet-grade plywood on the stair face",
)

MATERIALS = [
    *STARTER_MATERIALS,
    # --- accent wall paint -------------------------------------------------------
    # The house's one interior accent: deep spruce green-blue on RM-S-BED1's feature wall
    # (storeys/second.py). Physically identical to `latex-paint` (same film, same Class III
    # ~5 perm retarder, coating=True) — only the colour differs, so building science is
    # unchanged. Authored dark on purpose: the viewer's lighting lifts a dark albedo well
    # above itself (see metal-dark-exterior below for the same effect).
    Material(tag="latex-paint-accent", name="Interior latex paint, spruce accent",
             r_per_inch=0.0, vapor_permeance_perms=5.0, color="#2e4a44",
             finish="matte-latex", coating=True,
             source="same film as latex-paint (IRC R702.7.1 Class III over gypsum); only the colour differs — a second Material tag is how a wall says it is a different colour, since Layer has no colour slot"),
    # --- mudroom exposed-stud wall ---------------------------------------------
    # Appearance-grade framing, because in W-M-STRW the studs ARE the finish. Select
    # Structural S4S with eased corners: the grade buys straightness and a clean face, the
    # eased arris keeps a hand running along an exposed edge off a sharp corner. Douglas
    # fir-larch rather than SPF: it is the denser species (~32 pcf vs SPF's ~29), which is
    # why its R/inch is *lower* than spf's 1.24 — conductivity tracks density in wood.
    Material(tag="df-select-s4s", name="Douglas fir Select Structural S4S, eased corners",
             r_per_inch=1.00, density=530.0, perm_rating=2.9, hatch="lumber",
             color="#d9b077", finish="clear-satin-hardwax-oil",
             source="plans/TODO.md — exposed mudroom studs; DF-L R ~0.99-1.06/in (vs SPF 1.24-1.25) per the softwood density series, permeability shares the softwood midpoint used for spf"),
    # The stair face. 3/4" rather than the 1/2" a plain panel finish would take, because
    # this panel is structural backing: coat hooks and the closet rail screw straight into
    # it anywhere along the wall, with no blocking behind and no stud to hunt for.
    Material(tag="cabinet-plywood", name="Cabinet-grade hardwood plywood (3/4\")",
             r_per_inch=1.25, density=610.0, perm_rating=0.30, hatch="lumber",
             color="#c8a97a", finish="clear-satin-hardwax-oil",
             source="plans/TODO.md — mudroom wall's stair face; 3/4\" is structural backing so coat hooks screw directly into it (a 1/2\" panel would need blocking); permeability per the plywood series used for struct-1-plywood"),
    Material(tag="sauna-tg", name="Basswood/aspen T&G sauna liner (5/4)", r_per_inch=1.3,
             perm_rating=20.0, hatch="lumber", color="#e6d4ae",
             species="basswood", stock_bf_per_sqft=1.25,
             source="notes/sauna_basement_wall_detail.md — low-conductivity species (American basswood, Canadian poplar, aspen); 5/4 stock = 1.25 bf/sf"),
    # --- species wood finishes (plans/TODO.md §Hardwood, 2026-08-02) -----------
    # RM-M-STUDY wainscot to 36". 4/4 stock: board feet = square feet.
    Material(tag="walnut-tg", name="Black walnut T&G wainscot (4/4)", r_per_inch=1.1,
             density=610.0, hatch="lumber", color="#5d4433",
             finish="clear-satin-hardwax-oil", species="walnut", stock_bf_per_sqft=1.0,
             source="plans/TODO.md — first-floor study walnut paneling to 36\""),
    # The suite's four 6-1/8\" square tudor posts, ordered as 10' sections and cut down.
    Material(tag="elm-timber", name="Elm timber 6-1/8\" square, S4S", r_per_inch=1.1,
             density=560.0, hatch="lumber", color="#b08d5e",
             finish="clear-satin-hardwax-oil", species="elm",
             source="plans/TODO.md — suite bedroom tudor posts, 10' sections cut to fit"),
    Material(tag="polyiso-foil", name="Foil-faced polyisocyanurate", r_per_inch=6.0,
             perm_rating=0.03, hatch="rigid", color="#d9d2a8",
             source="foil facer is the sauna's vapour retarder as well as its CI"),
    # --- porch / balcony masonry + decking -------------------------------------
    Material(tag="brick", name="Face brick", r_per_inch=0.20, density=1920.0,
             perm_rating=1.0, hatch="concrete", color="#9c5a4a", finish="brick",
             source="red face brick — the catalog default wythe"),
    # White (whitewashed / white-fired) face brick laid with a grey mortar joint. Same clay
    # unit and R-value as the red brick; only the finish differs, and `finish` names the
    # recipe explicitly so no renderer has to infer "white" from the tag spelling.
    Material(tag="white-brick", name="White face brick (grey mortar)", r_per_inch=0.20,
             density=1920.0, perm_rating=1.0, hatch="concrete", color="#e9e6df",
             finish="white-brick",
             source="porch railing outer wythe — white brick, grey mortar (brief.md)"),
    # Glazed (fired-glaze) face brick in forest green — the sunken garden's south wall
    # veneer. Same clay unit, R-value and density as the red/white brick; only the finish
    # differs. Named explicitly so no renderer has to infer "green" from the tag: the glaze
    # is a ceramic coat, which is why it reads uniform and low-jitter like the white brick
    # rather than variegated like the red.
    Material(tag="glazed-green-brick", name="Glazed forest-green face brick",
             r_per_inch=0.20, density=1920.0, perm_rating=1.0, hatch="concrete",
             color="#1b4332", finish="glazed-green-brick",
             source="basement south veneer over the sunken garden — glazed brick, 1\" airgap off the existing concrete wall"),
    Material(tag="cmu", name="Grouted CMU (8\")", r_per_inch=0.11, density=2000.0,
             perm_rating=2.5, hatch="concrete", color="#b8b3ab", finish="cmu",
             source="porch railing inner wythe (grouted cores); concrete masonry ~2-3 perm-in"),
    Material(tag="grout", name="Masonry grout", r_per_inch=0.08, density=2240.0,
             perm_rating=2.5, hatch="concrete", color="#9a958c",
             source="fills the CMU cores for balcony post bases; cementitious grout ~2-3 perm-in"),
    # The house's one exterior dark (2026-08-01): every dark metal element on the
    # envelope — rake/eave/ridge trim coil, opening casings, guards — shares this value.
    # #1c1f24, not the #3a3d40 it started at: colour here is an albedo, and the viewer's
    # lighting (0.8 hemisphere + 0.9 key + 0.6 IBL) lifts a dark surface well above its
    # albedo — #3a3d40 arrived near #525252 (generic grey). Not pure black either: zero
    # albedo kills the shading that makes folds/posts read as solids.
    # Deliberately not named "*seam*" — renderers key the ribbed standing-seam finish off
    # that substring and this is flat brake-formed stock.
    Material(tag="metal-dark-exterior", name="Near-black painted metal (exterior)",
             r_per_inch=0.0, density=7850.0, perm_rating=0.0, hatch="metal",
             color="#1c1f24",
             source="RF-HOUSE rake/eave/ridge trim coil, opening casings, exterior guards"),
    Material(tag="stucco", name="Portland-cement stucco", r_per_inch=0.20, density=1900.0,
             perm_rating=10.0, hatch="concrete", color="#d9d2c4",
             # Two jobs, one product: the porch railing's CMU back-face finish, and the
             # basement wall's parge coat over its exterior XPS (CATLIN_BASEMENT_12).
             source="porch railing CMU back face; basement exterior-XPS parge coat"),
    Material(tag="composite-deck", name="Composite decking (capped PVC/wood)",
             r_per_inch=1.0, density=1000.0, perm_rating=0.5, hatch="lumber", color="#8a7f70",
             source="porch floor walking surface; PVC-capped composite ~0.5 perm-in (low)"),
    Material(tag="aluminum-deck", name="Aluminum deck board (Wahoo AridDeck-style)",
             r_per_inch=0.0, density=2700.0, perm_rating=0.05, hatch="metal", color="#b9bcc0",
             source="balcony waterproof aluminum plank; metal is effectively vapor-impermeable"),
    Material(tag="post-paint-white", name="White-painted PT lumber", r_per_inch=1.24,
             density=500.0, perm_rating=1.0, hatch="lumber", color="#f4f2ee",
             source="balcony 6x6 pillars, exterior white paint; painted softwood ~1 perm-in"),
    # --- raised garden ---------------------------------------------------------
    # Dry-stacked segmental retaining-wall (SRW) block. A precast concrete masonry unit, so
    # it renders on the existing "cmu" finish recipe rather than inventing a new one; the
    # split-face grey is a shade darker than the porch railing's grouted CMU.
    Material(tag="retaining-block", name="Segmental concrete retaining-wall block",
             r_per_inch=0.08, density=2200.0, perm_rating=2.5, hatch="concrete",
             color="#a8a49c", finish="cmu",
             source="raised garden outer face — dry-stacked SRW units, no mortar"),
    # --- breezeway glazing -----------------------------------------------------
    # 16mm five-wall polycarbonate. `color` is authored, not inferred: the palette's
    # substring-ordered family inference matches ("poly","rigid") first and would render this
    # as bright-yellow rigid foam otherwise. The alpha byte is what reads as glazing rather
    # than a solid panel (alphaMode BLEND below 1.0 in emit/gltf/scene.py).
    # Permeance ~0.012 perms, from EN 16153's 3.8e-5 mg/(m·h·Pa) converted and stored as
    # product permeance across the 16mm sheet (not divided again by thickness) — Class I.
    Material(tag="polycarbonate-multiwall", name="Multiwall polycarbonate glazing (16mm)",
             r_per_inch=1.54, density=1200.0, vapor_permeance_perms=0.012,
             hatch="glass", color="#cfe3e8b0",
             finish="polycarbonate",
             source="SABIC LEXAN THERMOCLEAR multiwall declaration EN 16153:2013+A1:2015 https://ff.sabic.eu/uploads/resources/DoP%20LT2UV329X38%20-%202023.pdf"),
    # Mill-finish extruded aluminium: the U/H/F channels, the glazing bars, and the panel
    # fasteners' washers. "alum" matches no needle in the family inference at all, so this
    # colour is authored for the same reason the polycarbonate's is.
    Material(tag="aluminum-extrusion", name="Extruded aluminium glazing bar / channel",
             r_per_inch=0.0007, density=2700.0, perm_rating=0.0, hatch="metal",
             color="#b6bac0",
             source="breezeway glazing trim — mill-finish 6063-T5 extrusion"),
]

# --- construction rules: pre-resolve returns at mixed-assembly junctions (#45) ----------
# Typed declarations of the physical returns the junction solver leaves for framing/takeoff
# (documented via a Transition overlay, never drawn; none mutate construction geometry):
# a PT sill where framed walls land on concrete, the sauna liner wrapping the center wall,
# foundation foam turning the corner, the masonry guard's corner return.
CONSTRUCTION_RULES = [
    ConstructionRule(
        tag="CR-CONC-TO-FRAMED-SILL",
        applies_to="wall:framed_on_concrete",
        kind="bearing_plate",
        dimension=inch(1.5),
        takeoff_category="pt-sill-plate",
    ),
    # The same physical return one element down: a joisted deck bearing on a concrete wall
    # rather than a framed wall doing so. FS-SG-PORCH lands on the sunken garden's 16" arch
    # wall, and without this the joists would butt a rim sitting on bare concrete — no PT
    # plate, no sill seal, no capillary break, and none of the three on the order.
    ConstructionRule(
        tag="CR-DECK-ON-CONCRETE-SILL",
        applies_to="floor:on_concrete_wall",
        kind="bearing_plate",
        dimension=inch(1.5),
        takeoff_category="pt-sill-plate",
    ),
    ConstructionRule(
        tag="CR-SAUNA-LINER-RETURN",
        applies_to="wall:sauna_liner_return",
        kind="blocking",
        dimension=inch(3.5),
        takeoff_category="sauna-liner-return",
    ),
    ConstructionRule(
        tag="CR-FOUNDATION-FOAM-RETURN",
        applies_to="wall:foundation_foam_return",
        kind="blocking",
        dimension=inch(24.0),
        takeoff_category="foundation-foam-return",
    ),
    ConstructionRule(
        tag="CR-PORCH-MASONRY-RETURN",
        applies_to="wall:porch_masonry_return",
        kind="blocking",
        dimension=inch(7.625),
        takeoff_category="masonry-corner-return",
    ),
    # Resilient channel under the living room only: bedrooms sit directly over it, and 5/8"
    # gypsum screwed straight to the I-joists would carry footfall as impact noise. Scoped to
    # RM-M-LIVING (a room decision, not FS-SECOND's) — the rest of that ceiling is screwed
    # direct. A full layered-ceiling assembly is deliberately deferred; this just bills the
    # channel (gypsum comes via FS-SECOND's `ceiling_below`).
    # KNOWN GAP: `construction_returns` isn't priced by `cli/prices.py::_SECTIONS`, so these
    # lineal feet show up in the BOM but never the cost estimate (true of every rule above too).
    ConstructionRule(
        tag="CR-LIVING-CEIL-RC",
        applies_to="floor:ceiling_channel",
        kind="furring",
        dimension=inch(16),
        takeoff_category="resilient-channel",
        scope_ref="RM-M-LIVING",
    ),
]

ASSEMBLIES = [
    CATLIN_EXT_2X6,
    CATLIN_ROOF,
    CATLIN_BASEMENT_12,
    CATLIN_SLAB_FLOOR,
    CATLIN_DECK_9_INT,
    CATLIN_CONC_12_INT,
    CATLIN_CONC_8_INT,
    SUNKEN_GARDEN_WALL,
    SUNKEN_GARDEN_ARCH_16,
    PORCH_RAILING_MASONRY,
    BASEMENT_BRICK_VENEER,
    RETAINING_BLOCK_12,
    PORCH_DECK_COMPOSITE,
    BREEZEWAY_ROOF_GLAZING,
    BREEZEWAY_GLAZED_WALL,
    BALCONY_DECK_ALUMINUM,
    POST_WHITE_PAINT,
    ELM_TIMBER,
    RAILING_DARK_METAL,
    GARAGE_ICF_6,
    GARAGE_WALL_2X6,
    GARAGE_SLAB_ON_GRADE,
    GARAGE_ROOF,
    CATLIN_INT_2X6_BRG,
    INT_2X6_PLUMBING,
    INT_2X6_STAGGERED_PLUMBING,
    INT_2X4_PARTITION,
    INT_ESS_CLOSET_STEEL,
    SAUNA_2X4,
    SAUNA_LINER_ON_CONCRETE,
    CATLIN_MUDROOM_INT_2X6_EXPOSED,
]
