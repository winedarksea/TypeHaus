# haus: editable
# The mudroom's coat-nook wall: open below six feet, painted gypsum above.

from typehaus import (
    Assembly,
    FramingSpec,
    Layer,
    LayerBound,
    LayerDatum,
    LayerExtent,
    LayerFunction,
    Substitution,
    inch,
    inside_of,
    layers,
)

_OPEN_BAY_HEIGHT_IN = 72
_CEILING_HEIGHT_IN = 108
# 72" floor clearance less the 1 1/2" sole plate; editable plans forbid arithmetic.
_BLOCKING_HEIGHT_ABOVE_SOLE_PLATE_IN = 70.5
_UPPER_CLOSURE_EXTENT = LayerExtent(
    bottom=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(_OPEN_BAY_HEIGHT_IN)),
    # Platform resolution lifts the skin above the ceiling into the joist bay.
    top=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(_CEILING_HEIGHT_IN)),
)

INT_2X6_BRG_MUDROOM_UPPER_GWB = Assembly(
    tag="INT_2X6_BRG_MUDROOM_UPPER_GWB",
    variant_of="INT_2X6_BRG_EXPOSED_PLY",
    substitute=(
        Substitution(
            span=layers("stud", "stud"),
            replacement=(
                Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                      function=LayerFunction.STRUCTURE,
                      framing=FramingSpec(
                          member="2x6", spacing=inch(16), sill_gasket=inch(0.0625),
                          layout_origin="line",
                          # Courses are measured from the sole plate's TOP; the visible
                          # underside of this flat cap must be six feet above the floor.
                          blocking_heights=(inch(_BLOCKING_HEIGHT_ABOVE_SOLE_PLATE_IN),),
                          blocking_material_ref="df-select-s4s")),
            ),
        ),
        Substitution(
            span=inside_of("stud"),
            replacement=(
                Layer(name="paint-mudroom-upper", material_ref="latex-paint",
                      thickness=inch(0.01), function=LayerFunction.FINISH,
                      extent=_UPPER_CLOSURE_EXTENT),
                Layer(name="gwb-mudroom-upper", material_ref="gwb", thickness=inch(0.5),
                      function=LayerFunction.FINISH, extent=_UPPER_CLOSURE_EXTENT),
            ),
        ),
    ),
    source="W-M-STRW mudroom coat nooks: exposed Douglas-fir studs below 6 ft; 1/2 in. painted gypsum from 6 ft to the 9 ft ceiling. Flat 2x6 Select Structural S4S Douglas-fir bay caps have their underside at 6 ft, closing the stud depth behind the gypsum's lower edge.",
)
