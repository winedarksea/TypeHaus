"""Concrete foundation walls, per IRC Table R404.1.2."""

from __future__ import annotations

from typehaus.library.assemblies._layers import (
    CONCRETE_BEARING,
)
from typehaus.model import (
    Assembly,
    ControlLayer,
    Layer,
    LayerFunction,
    inch,
)

# --- cast concrete foundation walls ----------------------------------------------
#
# The generic 8"/12" family. A house draws the pour from here rather than re-minting it,
# and adds its own outermost protective skin (parge, panel, veneer) on top of a ``_CORE``
# tuple where it wants one — that skin is a colour and exposure decision, which is a house
# decision, while the pour, the waterproofing, the two staggered 2" XPS courses and the
# bearing face are not.
#
# **8" vs 12" is a soil/height question, never a default.** IRC Table R404.1.2(8) is what
# decides it: at 45 psf/ft equivalent fluid density, a 10' wall retaining 7' of unbalanced
# fill takes 12" plain but 8" reinforced #6 @ 48" o.c. vertical. The 12" members here exist
# for the cases the table (or a cast deck bearing on the wall top beside the sill) actually
# earns them; picking one without reading the row for the wall's own height, backfill and
# soil class is how an unreinforced 8" wall gets built where the table required steel.
# ``structural.foundation_unbalanced_fill`` grades this from the STRUCTURE layer, so the
# thickness authored here is the thickness that gets checked.

_R404_SOURCE = ("IRC Table R404.1.2(8), plain and minimally reinforced concrete "
                "foundation walls: 45 psf/ft equivalent fluid density, 10 ft maximum "
                "wall height, 7 ft unbalanced backfill")

# Bare pours for interior cross / bearing walls — soil on neither face.
#
# **The ``INT`` token is load-bearing and must stay underscore-delimited.**
# ``mn_energy._is_interior_assembly`` is literally ``"INT" in tag.split("_")``; without it
# a bare concrete wall between two conditioned rooms is graded as basement envelope and
# fails on R-1.5. The token must not lead the tag either — ``INT_*`` is the acoustic
# namespace, whose test demands a published STC and a URL, and a cast wall has no lab test
# to cite.
FOUNDATION_WALL_8_INT = Assembly(
    tag="FOUNDATION_WALL_8_INT",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(CONCRETE_BEARING,),
    source=_R404_SOURCE + "; 8 in. requires #6 at 48 in. o.c. vertical",
)

FOUNDATION_WALL_12_INT = Assembly(
    tag="FOUNDATION_WALL_12_INT",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(CONCRETE_BEARING,),
    source=_R404_SOURCE + "; 12 in. reads NR (no vertical reinforcement required)",
)

# Below-grade envelope cores, interior→exterior from the pour outward: whatever is inboard
# of the concrete is the consuming house's business, and so is whatever protects the foam
# outboard of it. Exported as bare layer tuples so a house can splat one and append its own
# skin without re-typing the pour — ``FOUNDATION_WALL_*_XPS4`` below are the skinless
# assemblies for a house that wants the core as-is.
#
# 2 x 2" rather than one 4" board: staggered joints, and 2" is the stocked thickness.
# Waterproofing outboard of the pour and inboard of the foam is where Minn. R. 1309.0406
# subp. 2 puts it, and it is also GCP's own instruction: "Insulation, if used, must be
# applied over the membrane."
#: Everything OUTBOARD of the pour, published separately because a house that states its own
#: mix has to author its own concrete layer and cannot splat one that carries somebody else's.
#: A ``ConcreteSpec`` is a purchase decision — one ticket from one plant — so it belongs to
#: the house, and the library must not put one in a shared core. Slicing this out of the core
#: at the point of use is not open to a house either: ``plan/*.py`` is the constrained
#: editable dialect, which forbids subscripting.
FOUNDATION_WALL_XPS4_OUTBOARD = (
    Layer(name="waterproofing", material_ref="waterproofing", thickness=inch(0.06),
          function=LayerFunction.MEMBRANE,
          control={ControlLayer.AIR, ControlLayer.WATER}),
    Layer(name="xps-a", material_ref="xps", thickness=inch(2.0),
          function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    Layer(name="xps-b", material_ref="xps", thickness=inch(2.0),
          function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
)

FOUNDATION_WALL_8_XPS4_CORE = (
    Layer(name="concrete", material_ref="concrete", thickness=inch(8.0),
          function=LayerFunction.STRUCTURE),
    *FOUNDATION_WALL_XPS4_OUTBOARD,
)

FOUNDATION_WALL_12_XPS4_CORE = (
    Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
          function=LayerFunction.STRUCTURE),
    *FOUNDATION_WALL_XPS4_OUTBOARD,
)

# 8" + waterproofing + 4" XPS = 12.06" total, ~R-21.8.
FOUNDATION_WALL_8_XPS4 = Assembly(
    tag="FOUNDATION_WALL_8_XPS4",
    layers=FOUNDATION_WALL_8_XPS4_CORE,
    interfaces=(CONCRETE_BEARING,),
    source=_R404_SOURCE + "; 8 in. requires #6 at 48 in. o.c. vertical. Exterior "
                          "insulation 2 x 2 in. XPS over waterproofing per Minn. R. "
                          "1309.0406 subp. 2, which deletes IRC R406.1",
)

# 12" + the same tail = 16.06".
FOUNDATION_WALL_12_XPS4 = Assembly(
    tag="FOUNDATION_WALL_12_XPS4",
    layers=FOUNDATION_WALL_12_XPS4_CORE,
    interfaces=(CONCRETE_BEARING,),
    source=_R404_SOURCE + "; 12 in. reads NR (no vertical reinforcement required). "
                          "Exterior insulation 2 x 2 in. XPS over waterproofing per "
                          "Minn. R. 1309.0406 subp. 2, which deletes IRC R406.1",
)
