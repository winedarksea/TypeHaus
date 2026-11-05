# haus: editable
# Catlin assemblies — the framed walkout at the sunken garden.
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    Assembly,
    CavityFill,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerFunction,
    Substitution,
    inch,
    inside_of,
    layers,
)
from library import (
    CONCRETE_BEARING,
    STUD_BEARING,
)
from .interior import _SAUNA_LINER
from .mixes import BURIED_MIX


# SAUNA_LINER_ON_BASEMENT_8_GARDEN was RETIRED when W-B-S2 became a 7 1/4" curb under a
# framed wall, on the grounds that the liner-on-a-full-height-pour case had no instance
# left in this house. It came back briefly as SAUNA_LINER_ON_BASEMENT_8 when the sauna
# rotated onto the garden wall (2026-09-05) and its south face landed on W-B-S1B, the
# 3'-10" of buried 8" pour west of the excavation. **Both are retired again**: the same
# day's shrink pulled the sauna's west wall east to x=8'-10", the excavation edge, so its
# whole south face is W-B-S2's garden curb and SAUNA_LINER_ON_GARDEN_CURB carries it alone.
# The pattern is recoverable from git if a future room ever straddles the line again.

# --- the framed walkout at the sunken garden --------------------------------------
# W-B-S2-FR and W-B-S3-FR: the 19'-2" of south wall that stands *inside* the sunken garden
# court, from x=8'-10" (where the excavation starts) to x=28'-0" (where grade comes back
# up). It retains nothing — `unbalanced_fill` is `ft(0)` on both segments
# — so it was 8" of formed concrete holding back air, with a 5'-0" french door and a sauna
# window formed through it.
#
# What the estimate cannot see is the better half of the argument:
# `takeoff/wall_structure.py` bills wall volume NET of openings and adds nothing back for
# the buck or the extra forming, so the model actually books a CREDIT for those two holes
# where forming two openings in a pour is the very cost this swap removes. The modelled
# saving is the floor, not the number.
#
# **The stack is the concrete one with studs where the pour was**, not EXT_2X6: the
# outboard face has to stay exactly where it is. The waterproofing and the 4" of XPS continue
# from W-B-S1 and W-B-S4 either side, and W-B-BRICK stands 1.94" off its foam with two
# arched reveals dimensioned to it. `alignment=face("sheathing-ext")` puts the sheathing's
# outboard face on the node line exactly where `face("concrete-ext")` put the pour's, so the
# whole outboard tail lands on the plane it always did. (The parge was once a third layer
# of that tail; the brick's cavity is 1-1/2" clear now rather than 1", which is the veneer
# standing still while the wall behind it got thinner.) The rooms inside gain
# 1 3/8" (8" of pour becomes 6 5/8" of stud and gypsum), and the 6" curb below leaves only
# the gypsum's own 5/8" oversailing it, which is what drywall over a curb does everywhere.
#
# NO "INT" token here, and that is not an oversight: this is an envelope wall between
# conditioned space and open air, and `mn_energy._is_interior_assembly` must NOT skip it.
# R-21 of mineral wool between the studs plus the same continuous 4" of XPS the pour
# carried reads better than the 8"-concrete stack it replaces.
_GARDEN_FRAMED_OUTBOARD = (
    Layer(name="sheathing", material_ref="cdx-plywood", thickness=inch(0.5),
          function=LayerFunction.SHEATHING),
    Layer(name="waterproofing", material_ref="waterproofing", thickness=inch(0.06),
          function=LayerFunction.MEMBRANE,
          control={ControlLayer.AIR, ControlLayer.WATER}),
    Layer(name="xps-a", material_ref="xps", thickness=inch(2.0),
          function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    Layer(name="xps-b", material_ref="xps", thickness=inch(2.0),
          function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    # ** NO EPS SINCE 2026-11-04. ** The 2" EPS (2026-09-05) braced an engineered anchor
    # across a 4" cavity. W-SG-BRKBM now sits flush on the house strips, so the brick's back
    # is at -6.0", 6 1/2" off the studs (IRC 2024 Table R703.8.4(1) W2.8: <= 6 5/8") and
    # 1.94" off this foam (notes/sunken_garden_veneer_beam.md §6k). With the EPS there
    # would be no cavity at all.
)

_GARDEN_FRAMED_STUD = Layer(
    name="stud", material_ref="spf", thickness=inch(5.5),
    function=LayerFunction.STRUCTURE,
    # Peel-and-stick under the plate: this is the envelope's air barrier crossing onto the
    # curb, and with no cladding layer of its own the wall would otherwise get plain foam.
    framing=FramingSpec(member="2x6", spacing=inch(16), sill_gasket=inch(0.0625),
                        sill_gasket_product="sill-seal-peel-stick", layout_origin="line"),
    cavity=CavityFill(material_ref="mineral-wool"))

# The curbs the framed run stands on: W-B-S2 and W-B-S3, 7 1/4" of pour on the existing
# footings. **6" and not the 8" the rest of the south wall is**, and the reason is a plane
# and not a load: 6" of concrete is exactly stud-plus-sheathing, so the curb's outboard
# face lands on the node line where the sheathing's does — keeping the waterproofing, the
# XPS and W-B-BRICK's cavity on one plane top to bottom — AND its inboard
# face lands where the studs' does, so there is no shelf inside the room to collect water.
# An 8" curb would have bought a 2" ledge on the wet side of a sauna wall. The curb
# retains nothing (`unbalanced_fill=ft(0)`), so no table asks it for thickness.
#
# The three outboard layers are restated rather than sliced off
# FOUNDATION_WALL_8_XPS4_CORE: this file is `# haus: editable` and the dialect allows no
# subscripting. They are the same waterproofing and 2 x 2" of XPS, in the same order.
_GARDEN_CURB_CORE = (
    Layer(name="concrete", material_ref="concrete", thickness=inch(6.0),
          function=LayerFunction.STRUCTURE, concrete=BURIED_MIX),
    Layer(name="waterproofing", material_ref="waterproofing", thickness=inch(0.06),
          function=LayerFunction.MEMBRANE,
          control={ControlLayer.AIR, ControlLayer.WATER}),
    Layer(name="xps-a", material_ref="xps", thickness=inch(2.0),
          function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    Layer(name="xps-b", material_ref="xps", thickness=inch(2.0),
          function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    # No EPS since 2026-11-04: see `_GARDEN_FRAMED_OUTBOARD`.
)

GARDEN_CURB_6 = Assembly(
    tag="GARDEN_CURB_6",
    layers=(
        *_GARDEN_CURB_CORE,
    ),
    interfaces=(CONCRETE_BEARING,),
    source="catlin sunken-garden curb (W-B-S3), 2026-08-28: 6 in. of the south pour kept 7 1/4 in. above the slab under the framed walkout, on its own waterproofing and 4 in. XPS, bare to the brick cavity since the 2026-09-02 stucco retirement",
)

# The same curb under the sauna's south face. The liner runs DOWN over it — it is not
# banded off at the curb top — because the hot side's foil-faced polyiso is the room's
# vapour control and a 7 1/4" strip of bare concrete at the bottom of it is a hole in that
# control, which is exactly what `building_science.humid_room_liner` said the moment the
# curb was authored without it. With the curb at 6" the liner faces above and below the
# joint are flush, so this is one continuous plane and not a return.
SAUNA_LINER_ON_GARDEN_CURB = Assembly(
    tag="SAUNA_LINER_ON_GARDEN_CURB",
    variant_of="GARDEN_CURB_6",
    substitute=(
        Substitution(span=inside_of("concrete"), replacement=_SAUNA_LINER),
    ),
    source="catlin sunken-garden curb under the sauna (W-B-S2), 2026-08-28: GARDEN_CURB_6 with the sauna liner carried down over its face so the hot side's vapour control is continuous to the slab",
)

GARDEN_FRAMED_2X6 = Assembly(
    tag="GARDEN_FRAMED_2X6",
    layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.5),
              function=LayerFunction.FINISH),
        _GARDEN_FRAMED_STUD,
        *_GARDEN_FRAMED_OUTBOARD,
    ),
    interfaces=(STUD_BEARING,),
    source="catlin basement south walkout (W-B-S3-FR), framed 2026-08-28: 2x6 spf at 16 in. o.c. with mineral wool, on the same outboard tail the curb below it carries (waterproofing, 4 in. XPS, bare to the brick cavity since the 2026-09-02 stucco retirement) so the sunken garden's finished face does not move",
)

# The sauna's south face, on the framed run: GARDEN_FRAMED_2X6 with the liner in place of
# its gypsum leaf. The liner's own band stops it at the room's 7'-6" ceiling; the curb's
# liner below carries the first 7 1/4".
SAUNA_LINER_ON_GARDEN_FRAMED = Assembly(
    tag="SAUNA_LINER_ON_GARDEN_FRAMED",
    variant_of="GARDEN_FRAMED_2X6",
    substitute=(
        Substitution(span=layers("gwb-a", "gwb-a"), replacement=_SAUNA_LINER),
    ),
    source="catlin basement sauna south wall (W-B-S2-FR), framed 2026-08-28: the sauna liner over GARDEN_FRAMED_2X6's studs and outboard tail",
)
