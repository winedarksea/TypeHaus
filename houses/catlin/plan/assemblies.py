# haus: editable
# Catlin house assemblies — ported from catlin-house ifcplot (WP3.1).
# Layer order is interior → exterior. The exterior wall family shares one siding stack
# (sheathing / WRB / 2" polyiso / 2" EPS / furring / standing seam) so the #43 stack jog
# (2x6 → 2x4) keeps the sheathing plane and every control layer continuous.
from typehaus import (
    Assembly,
    CavityFill,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerFunction,
    MasonrySpec,
    Material,
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
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6"),
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
    default_lining=_GWB_LINING,
    source="catlin-house ifcplot/catlin_house.py wall siding stack",
)

# Second storey + attic: same envelope, shallower studs (#43 stack-width change).
CATLIN_EXT_2X4 = Assembly(
    tag="CATLIN_EXT_2X4",
    variant_of="CATLIN_EXT_2X6",
    substitute=(
        Substitution(
            span=layers("stud", "stud"),
            replacement=(
                Layer(name="stud", material_ref="spf", thickness=inch(3.5),
                      function=LayerFunction.STRUCTURE,
                      framing=FramingSpec(member="2x4"),
                      cavity=CavityFill(material_ref="mineral-wool")),
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
              framing=FramingSpec(member="11.875 I-joist"),
              # I-joist webs are thin, so the framing fraction is far below a stud wall's.
              cavity=CavityFill(material_ref="mineral-wool", framing_factor=0.07)),
        Layer(name="deck", material_ref="struct-1-plywood", thickness=inch(0.75),
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

# The porch "front" (arched) cross-wall is 16" so it reads as three piers + an arched
# beam AND gives the porch-floor joists 3.5" of bearing on top of the sill plate.
SUNKEN_GARDEN_ARCH_16 = Assembly(
    tag="SUNKEN_GARDEN_ARCH_16",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(16.0),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house porch arched front wall — 16\" for joist bearing (3.5\") + arch piers",
)

# Masonry "railing" / parapet on top of the porch front + side walls. The balcony 6x6
# pillars land in the grout-filled CMU cores. Layer order interior (porch/deck side) ->
# exterior (garden side): stucco on the CMU back, grout-filled CMU, air gap, face brick.
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
        Layer(name="brick", material_ref="brick", thickness=inch(3.625),
              function=LayerFunction.CLADDING),
    ),
    source="catlin-house porch railing — brick / air gap / grouted CMU / stucco",
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
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6"),
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

GARAGE_ROOF = Assembly(
    tag="GARAGE_ROOF",
    layers=(
        Layer(name="rafter", material_ref="spf", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="11.875 I-joist")),
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
    source="catlin-house sauna_basement_wall_detail.py (liner on the center bearing wall)",
)

MATERIALS = [
    *STARTER_MATERIALS,
    Material(tag="sauna-tg", name="Basswood/aspen T&G sauna liner (5/4)", r_per_inch=1.3,
             perm_rating=20.0, hatch="lumber", color="#e6d4ae",
             source="notes/sauna_basement_wall_detail.md — low-conductivity species (American basswood, Canadian poplar, aspen)"),
    Material(tag="polyiso-foil", name="Foil-faced polyisocyanurate", r_per_inch=6.0,
             perm_rating=0.03, hatch="rigid", color="#d9d2a8",
             source="foil facer is the sauna's vapour retarder as well as its CI"),
    # --- porch / balcony masonry + decking -------------------------------------
    Material(tag="brick", name="Face brick", r_per_inch=0.20, density=1920.0,
             perm_rating=1.0, hatch="concrete", color="#9c5a4a",
             source="porch railing outer wythe"),
    Material(tag="cmu", name="Grouted CMU (8\")", r_per_inch=0.11, density=2000.0,
             hatch="concrete", color="#b8b3ab",
             source="porch railing inner wythe — cores grouted for pillar anchorage"),
    Material(tag="grout", name="Masonry grout", r_per_inch=0.08, density=2240.0,
             hatch="concrete", color="#9a958c",
             source="fills the CMU cores that receive the balcony post bases"),
    Material(tag="stucco", name="Portland-cement stucco", r_per_inch=0.20, density=1900.0,
             perm_rating=10.0, hatch="concrete", color="#d9d2c4",
             source="porch railing CMU back-face finish"),
    Material(tag="composite-deck", name="Composite decking (capped PVC/wood)",
             r_per_inch=1.0, density=1000.0, hatch="lumber", color="#8a7f70",
             source="porch floor walking surface"),
    Material(tag="aluminum-deck", name="Aluminum deck board (Wahoo AridDeck-style)",
             r_per_inch=0.0, density=2700.0, hatch="metal", color="#b9bcc0",
             source="balcony walking surface — waterproof aluminum plank"),
    Material(tag="post-paint-white", name="White-painted PT lumber", r_per_inch=1.24,
             density=500.0, hatch="lumber", color="#f4f2ee",
             source="balcony 6x6 pillars — exterior white paint finish"),
]

ASSEMBLIES = [
    CATLIN_EXT_2X6,
    CATLIN_EXT_2X4,
    CATLIN_ROOF,
    CATLIN_BASEMENT_12,
    CATLIN_SLAB_FLOOR,
    CATLIN_CONC_12_INT,
    CATLIN_CONC_8_INT,
    SUNKEN_GARDEN_WALL,
    SUNKEN_GARDEN_ARCH_16,
    PORCH_RAILING_MASONRY,
    PORCH_DECK_COMPOSITE,
    BALCONY_DECK_ALUMINUM,
    POST_WHITE_PAINT,
    GARAGE_ICF_8,
    GARAGE_WALL_2X6,
    GARAGE_ROOF,
    CATLIN_INT_2X6_BRG,
    INT_2X6_PLUMBING,
    INT_2X4_PARTITION,
    SAUNA_2X4,
    SAUNA_LINER_ON_CONCRETE,
]
