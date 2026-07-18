"""Starter assemblies ported from ifcplot/assemblies.py (→ 02 migration table, WP1.3)."""

from __future__ import annotations

from typehaus.model import (
    Assembly,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerFunction,
    MasonrySpec,
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
              control={ControlLayer.THERMAL}),
        Layer(name="batt", material_ref="fiberglass", thickness=inch(3.5),
              function=LayerFunction.INSULATION),
        Layer(name="osb", material_ref="osb", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        Layer(name="wrb", material_ref="air-barrier", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="ci", material_ref="polyiso", thickness=inch(1.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="cladding", material_ref="fiber-cement", thickness=inch(0.3125),
              function=LayerFunction.CLADDING,
              framing=FramingSpec(member="1x4", direction="vertical")),
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
              control={ControlLayer.THERMAL}),
        Layer(name="batt", material_ref="mineral-wool", thickness=inch(5.5),
              function=LayerFunction.INSULATION),
        Layer(name="zip-r", material_ref="zip-r", thickness=inch(1.5),
              function=LayerFunction.SHEATHING,
              control={ControlLayer.AIR, ControlLayer.WATER, ControlLayer.THERMAL}),
        Layer(name="cladding", material_ref="fiber-cement", thickness=inch(0.3125),
              function=LayerFunction.CLADDING,
              framing=FramingSpec(member="1x4", direction="vertical")),
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
              control={ControlLayer.THERMAL}),
        Layer(name="batt", material_ref="mineral-wool", thickness=inch(11.875),
              function=LayerFunction.INSULATION),
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

# STC-rated interior partition preset (#50) — value is an empirical lab-test lookup.
INT_2X4_PARTITION = Assembly(
    tag="INT_2X4_PARTITION",
    layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x4")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    stc=34,
    source="Generic single-stud 1/2\" GWB both sides (GA-600 class). Generic assumption.",
)

STARTER_FLOOR = {"subfloor": "plywood-subfloor", "joist": "11.875 I-joist"}

# Assemblies whose R-value / card should render for M1 acceptance.
ALL_ASSEMBLIES: tuple[Assembly, ...] = (
    HOUSE_WALL_2X4_WITH_CI,
    HOUSE_WALL_2X6_WITH_ZIPR,
    GARAGE_ICF,
    HOUSE_ROOF,
    INT_2X4_PARTITION,
)
