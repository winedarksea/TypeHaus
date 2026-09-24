"""The starter roof assembly and floor system."""

from __future__ import annotations

from typehaus.library.assemblies._layers import (
    PAINT_FINISH,
)
from typehaus.model import (
    Assembly,
    CavityFill,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerFunction,
    inch,
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
        PAINT_FINISH,
        Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
)

STARTER_FLOOR = {"subfloor": "plywood-subfloor", "joist": "11.875 I-joist"}
