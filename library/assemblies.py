"""Starter assemblies ported from ifcplot/assemblies.py (→ 02 migration table, WP1.3)."""

from __future__ import annotations

from typehaus.model import (
    Assembly,
    CavityFill,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerFunction,
    MasonrySpec,
    PartitionLayout,
    inch,
    r_us,
)

_GWB_LINING = (
    Layer(name="gwb-int", material_ref="gwb", thickness=inch(0.625),
          function=LayerFunction.FINISH),
)

# 2x4 wall with 1" continuous exterior insulation.
HOUSE_WALL_2X4_WITH_CI = Assembly(
    tag="HOUSE_WALL_2X4_WITH_CI",
    layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x4"),
              control={ControlLayer.THERMAL},
              cavity=CavityFill(material_ref="fiberglass")),
        Layer(name="osb", material_ref="osb", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        Layer(name="wrb", material_ref="air-barrier", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="ci", material_ref="polyiso", thickness=inch(1.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        # Furring + cladding as separate layers (the catlin-house siding-stack pattern):
        # the furring is a drained-and-back-vented rainscreen cavity open to outdoor air,
        # so the Glaser walk truncates there and the fiber-cement (no published ASTM E96
        # rating) never blocks a permeance verdict for the wall behind it.
        Layer(name="furring", material_ref="spf", thickness=inch(0.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="1x4", direction="vertical")),
        Layer(name="cladding", material_ref="fiber-cement", thickness=inch(0.3125),
              function=LayerFunction.CLADDING),
    ),
    default_lining=_GWB_LINING,
    source="Adapted from catlin-house ifcplot/assemblies.py",
)

# 2x6 wall with ZIP-R exterior sheathing (the PGH envelope).
HOUSE_WALL_2X6_WITH_ZIPR = Assembly(
    tag="HOUSE_WALL_2X6_WITH_ZIPR",
    layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6"),
              control={ControlLayer.THERMAL},
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="zip-r", material_ref="zip-r", thickness=inch(1.5),
              function=LayerFunction.SHEATHING,
              control={ControlLayer.AIR, ControlLayer.WATER, ControlLayer.THERMAL}),
        # Furring + cladding split, same rationale as HOUSE_WALL_2X4_WITH_CI above.
        Layer(name="furring", material_ref="spf", thickness=inch(0.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="1x4", direction="vertical")),
        Layer(name="cladding", material_ref="fiber-cement", thickness=inch(0.3125),
              function=LayerFunction.CLADDING),
    ),
    default_lining=_GWB_LINING,
    source="Adapted from catlin-house ifcplot/assemblies.py",
)

# ICF garage foundation/wall — layered solid + arithmetic unit takeoff (#23).
GARAGE_ICF = Assembly(
    tag="GARAGE_ICF",
    layers=(
        Layer(name="eps-ext", material_ref="icf-eps", thickness=inch(2.625),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="concrete", material_ref="concrete", thickness=inch(6.0),
              function=LayerFunction.STRUCTURE,
              masonry=MasonrySpec(unit_size="ICF-6", core_fill=True,
                                  rebar_spacing=inch(16))),
        Layer(name="eps-int", material_ref="icf-eps", thickness=inch(2.625),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    default_lining=_GWB_LINING,
)

HOUSE_ROOF = Assembly(
    tag="HOUSE_ROOF",
    layers=(
        Layer(name="rafter", material_ref="spf", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x12"),
              control={ControlLayer.THERMAL},
              cavity=CavityFill(material_ref="mineral-wool", framing_factor=0.1)),
        Layer(name="deck", material_ref="osb", thickness=inch(0.625),
              function=LayerFunction.SHEATHING),
        Layer(name="membrane", material_ref="air-barrier", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="roofing", material_ref="standing-seam", thickness=inch(0.06),
              function=LayerFunction.CLADDING),
    ),
    default_lining=(
        Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
)

# STC-rated interior partition presets (#50).  STC is always a published test result,
# never a value calculated from the layers below.  Preserve each source's framing and
# lining configuration when selecting one; substitutions require a new tested rating.
INT_2X4_PARTITION = Assembly(
    tag="INT_2X4_PARTITION",
    layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x4"),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    stc=36,
    source=("ROCKWOOL, How to Soundproof a Room: 2x4 wood studs at 16 in. o.c., "
            "3.5 in. Comfortbatt, 5/8 in. gypsum both sides, STC 36; "
            "https://www.rockwool.com/north-america/advice-and-inspiration/blog/"
            "using-acoustic-insulation-to-soundproof-a-room/"),
)

INT_2X4_RC = Assembly(
    tag="INT_2X4_RC",
    layers=(
        Layer(name="gwb-resilient", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="resilient-channel", material_ref="resilient-channel", thickness=inch(0.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="25 ga. resilient channel", spacing=inch(24),
                                  direction="horizontal")),
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16)),
              cavity=CavityFill(material_ref="fiberglass")),
        Layer(name="gwb-direct", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    stc=48,
    source=("USG/UL U305, USG-US-CA-EN-W-P-1-08: 2x4 wood studs at 16 in. o.c., "
            "3.5 in. fiberglass, 1/2 in. resilient channel at 24 in. o.c., 5/8 in. "
            "gypsum each side, STC 48; "
            "https://assemblies-tools.usg.com/content/usgcom/en_CA_east/design-studio/"
            "wall-assemblies/assembly-detail.30235.html"),
)

INT_2X4_RC_DOUBLE_GWB = Assembly(
    tag="INT_2X4_RC_DOUBLE_GWB",
    layers=(
        Layer(name="gwb-a-outer", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="gwb-a-inner", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="resilient-channel", material_ref="resilient-channel", thickness=inch(0.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="25 ga. resilient channel", spacing=inch(24),
                                  direction="horizontal")),
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16)),
              cavity=CavityFill(material_ref="fiberglass")),
        Layer(name="gwb-b-inner", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="gwb-b-outer", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    stc=54,
    source=("USG/UL U301: 2x4 wood studs at 16 in. o.c., 3.5 in. fiberglass, 1/2 in. "
            "resilient channel at 24 in. o.c., two 5/8 in. gypsum layers each side, STC 54; "
            "https://assemblies-tools.usg.com/content/usgcom/en/design-studio/"
            "assemblies/assembly-detail.30269.html"),
)

INT_2X4_STAGGERED_DOUBLE_GWB = Assembly(
    tag="INT_2X4_STAGGERED_DOUBLE_GWB",
    layers=(
        Layer(name="gwb-a-outer", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="gwb-a-inner", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="staggered-studs", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16), plate_member="2x6",
                                  layout=PartitionLayout.STAGGERED,
                                  stagger_gap=inch(1.5)),
              cavity=CavityFill(material_ref="fiberglass", thickness=inch(3.5))),
        Layer(name="gwb-b-inner", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="gwb-b-outer", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    stc=52,
    source=("USG/GA WP 5530: 2x4 wood studs staggered on 2x6 plates (16 in. o.c. per "
            "face, 8 in. combined rhythm), "
            "3.5 in. fiberglass, two 5/8 in. gypsum layers each side, STC 52; "
            "https://assemblies-tools.usg.com/content/usgcom/en/design-studio/"
            "assemblies/assembly-detail.30226.html"),
)

INT_2X4_DOUBLE_STUD_MINERAL_WOOL = Assembly(
    tag="INT_2X4_DOUBLE_STUD_MINERAL_WOOL",
    layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.5),
              function=LayerFunction.FINISH),
        Layer(name="double-studs", material_ref="spf", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16),
                                  layout=PartitionLayout.DOUBLE,
                                  stagger_gap=inch(1)),
              cavity=CavityFill(material_ref="mineral-wool", thickness=inch(3.5))),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.5),
              function=LayerFunction.FINISH),
    ),
    stc=52,
    source=("ROCKWOOL Acoustic Wall Assemblies Catalog, IWS-11 / NGC 2010072: 2x4 "
            "wood double-stud wall at 16 in. o.c. with a 1 in. air gap, 3.5 in. "
            "Comfortbatt per row, 1/2 in. gypsum each side, STC 52; "
            "https://www.rockwool.com/syssiteassets/o2-rockwool/documentation/technical-guides/"
            "commercial/acoustic-wall-assemblies-catalog-techincal-guide.pdf"),
)

STARTER_FLOOR = {"subfloor": "plywood-subfloor", "joist": "11.875 I-joist"}

# Assemblies whose R-value / card should render for M1 acceptance.
ALL_ASSEMBLIES: tuple[Assembly, ...] = (
    HOUSE_WALL_2X4_WITH_CI,
    HOUSE_WALL_2X6_WITH_ZIPR,
    GARAGE_ICF,
    HOUSE_ROOF,
    INT_2X4_PARTITION,
    INT_2X4_RC,
    INT_2X4_RC_DOUBLE_GWB,
    INT_2X4_STAGGERED_DOUBLE_GWB,
    INT_2X4_DOUBLE_STUD_MINERAL_WOOL,
)
