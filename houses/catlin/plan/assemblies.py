# haus: editable
# Catlin house assemblies — ported from catlin-house ifcplot (WP3.1).
# Layer order is interior → exterior. The exterior wall family shares one siding stack
# (sheathing / WRB / 2" polyiso / 2" EPS / furring / standing seam) so the #43 stack jog
# (2x6 → 2x4) keeps the sheathing plane and every control layer continuous.
from typehaus import (
    Assembly,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerFunction,
    MasonrySpec,
    Substitution,
    inch,
    layers,
)
from library import INT_2X4_PARTITION, STARTER_MATERIALS

_GWB_LINING = (
    Layer(name="gwb-int", material_ref="gwb", thickness=inch(0.625),
          function=LayerFunction.FINISH),
)

# --- exterior wall family (the #43 motivating stack) --------------------------
CATLIN_EXT_2X6 = Assembly(
    tag="CATLIN_EXT_2X6",
    layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="batt", material_ref="mineral-wool", thickness=inch(5.5),
              function=LayerFunction.INSULATION),
        Layer(name="sheathing", material_ref="osb", thickness=inch(0.625),
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
    default_lining=_GWB_LINING,
    source="catlin-house ifcplot/catlin_house.py wall siding stack",
)

# Second storey + attic: same envelope, shallower studs (#43 stack-width change).
CATLIN_EXT_2X4 = Assembly(
    tag="CATLIN_EXT_2X4",
    variant_of="CATLIN_EXT_2X6",
    substitute=(
        Substitution(
            span=layers("stud", "batt"),
            replacement=(
                Layer(name="stud", material_ref="spf", thickness=inch(3.5),
                      function=LayerFunction.STRUCTURE,
                      framing=FramingSpec(member="2x4")),
                Layer(name="batt", material_ref="mineral-wool", thickness=inch(3.5),
                      function=LayerFunction.INSULATION),
            ),
        ),
    ),
)

# --- hot roof (unvented; no batten framing grows — → 30 §WP3.11) --------------
CATLIN_ROOF = Assembly(
    tag="CATLIN_ROOF",
    layers=(
        Layer(name="rafter", material_ref="spf", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="11.875 I-joist")),
        Layer(name="cavity", material_ref="mineral-wool", thickness=inch(11.875),
              function=LayerFunction.INSULATION),
        Layer(name="deck", material_ref="osb", thickness=inch(0.75),
              function=LayerFunction.SHEATHING),
        Layer(name="membrane", material_ref="air-barrier", thickness=inch(0.25),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="polyiso", material_ref="polyiso", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="eps", material_ref="eps", thickness=inch(4.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="roof-membrane", material_ref="air-barrier", thickness=inch(0.25),
              function=LayerFunction.MEMBRANE, control={ControlLayer.WATER}),
        Layer(name="batten-gap", material_ref="spf", thickness=inch(0.75),
              function=LayerFunction.AIRGAP),
        Layer(name="roofing", material_ref="standing-seam", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ),
    default_lining=(
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
    ),
    source="catlin-house basement: 12\" wall + 2x2\" exterior XPS",
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

CATLIN_CONC_12_INT = Assembly(
    tag="CATLIN_CONC_12_INT",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE),
    ),
)

CATLIN_CONC_8_INT = Assembly(
    tag="CATLIN_CONC_8_INT",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE),
    ),
)

# Freestanding sunken-garden / porch / balcony structure — exposed concrete.
SUNKEN_GARDEN_WALL = Assembly(
    tag="SUNKEN_GARDEN_WALL",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house sunken_garden_retaining_wall_detail.py",
)

# --- garage (freestanding: ICF stem + 2x6 wood wall) ---------------------------
GARAGE_ICF_8 = Assembly(
    tag="GARAGE_ICF_8",
    layers=(
        Layer(name="eps-int", material_ref="icf-eps", thickness=inch(2.5),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="concrete", material_ref="concrete", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE,
              masonry=MasonrySpec(unit_size="ICF-8", core_fill=True,
                                  rebar_spacing=inch(16))),
        Layer(name="eps-ext", material_ref="icf-eps", thickness=inch(2.5),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    source="catlin-house ifcplot/assemblies.py GARAGE_ICF (8\" core)",
)

GARAGE_WALL_2X6 = Assembly(
    tag="GARAGE_WALL_2X6",
    layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="batt", material_ref="mineral-wool", thickness=inch(5.5),
              function=LayerFunction.INSULATION),
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

GARAGE_ROOF = Assembly(
    tag="GARAGE_ROOF",
    layers=(
        Layer(name="rafter", material_ref="spf", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="11.875 I-joist")),
        Layer(name="deck", material_ref="osb", thickness=inch(0.625),
              function=LayerFunction.SHEATHING),
        Layer(name="membrane", material_ref="air-barrier", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="roofing", material_ref="standing-seam", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ),
)

# --- interior ------------------------------------------------------------------
CATLIN_INT_2X6_BRG = Assembly(
    tag="CATLIN_INT_2X6_BRG",
    layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    source="catlin-house centerline bearing wall (2x6)",
)

INT_2X6_PLUMBING = Assembly(
    tag="INT_2X6_PLUMBING",
    layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    source="wet wall — depth for 3\" stacks",
)

MATERIALS = STARTER_MATERIALS
ASSEMBLIES = [
    CATLIN_EXT_2X6,
    CATLIN_EXT_2X4,
    CATLIN_ROOF,
    CATLIN_BASEMENT_12,
    CATLIN_SLAB_FLOOR,
    CATLIN_CONC_12_INT,
    CATLIN_CONC_8_INT,
    SUNKEN_GARDEN_WALL,
    GARAGE_ICF_8,
    GARAGE_WALL_2X6,
    GARAGE_ROOF,
    CATLIN_INT_2X6_BRG,
    INT_2X6_PLUMBING,
    INT_2X4_PARTITION,
]
