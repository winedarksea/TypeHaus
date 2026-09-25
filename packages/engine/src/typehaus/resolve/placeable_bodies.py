"""A placeable's body as a solid: its plan footprint extruded over its resolved z band.

One reading shared by the geometry IR (``geometry_build`` emits Equipment as
``kind="equipment"``) and the checks (``structural.placeable_interference`` /
``structural.equipment_support``), so a drawing and a verdict never disagree on the box.
"""

from __future__ import annotations

from typehaus.resolve.geometry_ir import GPrism
from typehaus.resolve.model import ResolvedCanvasObject

#: The placeable kinds that join the collision set. Equipment first (decision: Phase 9).
BODY_KINDS: frozenset[str] = frozenset({"Equipment"})


def body_prism(obj: ResolvedCanvasObject) -> GPrism | None:
    """The body box, or ``None`` when the type states no height (or the footprint is empty)."""
    if obj.body_z0_m is None or obj.body_z1_m is None or len(obj.footprint) < 3:
        return None
    if obj.body_z1_m <= obj.body_z0_m:
        return None
    return GPrism(ring=tuple(tuple(p) for p in obj.footprint),
                  z0_m=obj.body_z0_m, z1_m=obj.body_z1_m)


def bodied(model) -> list[ResolvedCanvasObject]:
    """Every placeable of a :data:`BODY_KINDS` kind, bodied or not."""
    return [obj for obj in model.canvas_objects if obj.kind in BODY_KINDS]
