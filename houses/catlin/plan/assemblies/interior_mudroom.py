# haus: editable
# The mudroom's coat-nook wall: open bays with oak shelves below seven feet, painted gypsum
# above. Heights are off the storey datum, which this file treats as the floor; the LVP
# stands +0.9862", so each is about 1" less above the finished floor.

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

# Gypsum starts at the 7' cap's underside.
_OPEN_BAY_HEIGHT_IN = 84
_CEILING_HEIGHT_IN = 108
# Courses are measured from the sole plate's TOP (1 1/2"); editable plans forbid arithmetic.
# Bench support course, 15"-16 1/2": the bench board bears on it, seat top at 18".
_BENCH_COURSE_ABOVE_SOLE_PLATE_IN = 13.5
# 6' shelf, 70 1/2"-72": top at 72", a 12" clear cubby under the cap.
_SHELF_COURSE_ABOVE_SOLE_PLATE_IN = 69
# 7' cap, 84"-85 1/2": underside at 84", where the gypsum starts.
_CAP_COURSE_ABOVE_SOLE_PLATE_IN = 82.5
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
                          blocking_heights=(inch(_BENCH_COURSE_ABOVE_SOLE_PLATE_IN),
                                            inch(_SHELF_COURSE_ABOVE_SOLE_PLATE_IN),
                                            inch(_CAP_COURSE_ABOVE_SOLE_PLATE_IN)),
                          blocking_material_ref="white-oak-8-4",
                          # Boots drip snowmelt on the plate exposed in every bay.
                          sole_plate_material_ref="kdat")),
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
    source="W-M-STRW mudroom coat nooks: exposed Douglas-fir Select Structural studs, open bays to 7 ft; 1/2 in. painted gypsum from 7 ft to the 9 ft ceiling. Three flat white-oak 8/4 courses dressed to 1 1/2 in. span each bay: the bench support course (top at 16 1/2 in.), the 6 ft shelf (top at 72 in.) and the 7 ft cap (underside at 84 in., closing the stud depth behind the gypsum's lower edge). The sole plate is KDAT southern pine, fastened with HDG or stainless (IRC R317.3), because boots drip snowmelt onto it; LVP butts the plate rather than running flush, since a bearing wall keeps a nominal 2x bottom plate (IRC R602.3.4).",
)
