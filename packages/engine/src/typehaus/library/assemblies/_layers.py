"""Shared layers and interfaces the library's assemblies, and a house's, are built from.

Plain ``set`` controls, not ``frozenset``, so an editable house file may spell the same."""

from __future__ import annotations

from typehaus.model import (
    AssemblyInterface,
    ControlLayer,
    Layer,
    LayerFunction,
    inch,
)

# The load-bearing face the junction solver binds a concrete↔concrete return on (#44):
# the pour's inboard face, named by LAYER, not index, so an outboard skin may be added
# without invalidating the transition.
CONCRETE_BEARING = AssemblyInterface(role="bearing", layer_name="concrete", outboard=False)

# The same mechanism for a stud wall: two framed walls are "continuous" through a
# corner/tee when they publish the same bearing material (SPF↔SPF), regardless of the
# finish either side of it.
STUD_BEARING = AssemblyInterface(role="bearing", layer_name="stud", outboard=False)

# Painted gypsum lining. Layer order is interior → exterior everywhere the lining is
# consumed (``list(default_lining) + list(layers)``), so the paint is *first*: it is the
# room-side face, and that position is what makes it the assembly's warm-side vapour
# retarder in the Glaser walk (IRC R702.7 / R702.7.1 Class III, → checks/building_science).
PAINT_FINISH = Layer(name="paint", material_ref="latex-paint", thickness=inch(0.01),
                     function=LayerFunction.FINISH,
                     control={ControlLayer.VAPOR})

GWB_LINING = (
    PAINT_FINISH,
    Layer(name="gwb-int", material_ref="gwb", thickness=inch(0.625),
          function=LayerFunction.FINISH),
)

# The same film named per face, for partitions that carry their gypsum in ``layers``.
PAINT_FINISH_A = Layer(name="paint-a", material_ref="latex-paint", thickness=inch(0.01),
                       function=LayerFunction.FINISH,
                       control={ControlLayer.VAPOR})
PAINT_FINISH_B = Layer(name="paint-b", material_ref="latex-paint", thickness=inch(0.01),
                       function=LayerFunction.FINISH,
                       control={ControlLayer.VAPOR})
