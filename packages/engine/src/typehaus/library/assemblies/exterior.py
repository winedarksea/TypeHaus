"""Exterior wall assemblies: framed walls with continuous insulation, ICF, a glazed wall."""

from __future__ import annotations

from typehaus.library.assemblies._layers import (
    CONCRETE_BEARING,
    GWB_LINING,
)
from typehaus.model import (
    Assembly,
    CavityFill,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerFunction,
    MasonrySpec,
    inch,
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
    default_lining=GWB_LINING,
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
    default_lining=GWB_LINING,
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
              masonry=MasonrySpec(unit_size="ICF-6", core_fill=True)),
        Layer(name="eps-int", material_ref="icf-eps", thickness=inch(2.625),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    interfaces=(CONCRETE_BEARING,),
    default_lining=GWB_LINING,
)

# A glazed wall with no frame of its own: one 16mm multiwall polycarbonate sheet standing
# in a U-channel at the sill and an F-channel at the head, spanning post to post unaided.
# The sheet is STRUCTURE, not CLADDING, because it IS the wall — the same reading a single
# plank layer gets on a deck. Under rafters that do the spanning it would be cladding, and
# that is a different assembly.
#
# Span is the whole question and the sheet answers it: SABIC publishes wall spans for
# THERMOCLEAR 16mm, and a house that stands one further apart than the published table
# allows is authoring a ``PublishedSpan``, not this tag.
GLAZED_WALL_MULTIWALL_16MM = Assembly(
    tag="GLAZED_WALL_MULTIWALL_16MM",
    label="16mm multiwall polycarbonate glazed wall",
    layers=(
        Layer(name="glazing", material_ref="polycarbonate-multiwall", thickness=inch(0.63),
              function=LayerFunction.STRUCTURE),
    ),
    source="SABIC LEXAN THERMOCLEAR 16mm five-wall sheet, self-spanning between posts in "
           "U-channel (sill) and F-channel (head) glazing profiles",
)
