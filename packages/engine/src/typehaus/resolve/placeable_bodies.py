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


def part_outline(part, obj: ResolvedCanvasObject):
    """A generated part's local bounding box, placed in plan."""
    from shapely.geometry import Polygon

    from typehaus.model.placeable_symbols import place_local

    x, y, _ = part["center"]
    w, d, _ = part["size"]
    return Polygon(place_local(((x - w / 2, y - d / 2), (x + w / 2, y - d / 2),
                                (x + w / 2, y + d / 2), (x - w / 2, y + d / 2)),
                               obj.position, obj.rotation_degrees))


def installation_prisms(obj: ResolvedCanvasObject, product) -> list[tuple[str, object, float, float]]:
    """(label, plan shape, z0, z1) for installation parts drawn outside the cabinet body.

    The pan is one envelope (sheet walls alone would vanish under a touch tolerance); each
    drain part is its own box, so a pipe crossing the trap is not hidden by the feeder.
    """
    spec = getattr(product, "air_handler_installation", None)
    symbol = getattr(getattr(product, "model_representation", None), "symbol", None)
    if spec is None or symbol is None or obj.z_m is None:
        return []
    from typehaus.model.placeable_symbols import model_parts
    from typehaus.model.placeable_symbols._flexx_installation import DRAIN_ROLES, PAN_ROLES
    from typehaus.resolve.overlay import union_all

    parts = model_parts(symbol, *(v.meters for v in (*product.footprint, product.height)),
                        air_handler_installation=spec)

    def band(group):
        return (obj.z_m + min(p["center"][2] - p["size"][2] / 2 for p in group),
                obj.z_m + max(p["center"][2] + p["size"][2] / 2 for p in group))

    out = []
    pan = [p for p in parts if p.get("role") in PAN_ROLES]
    if pan:
        out.append(("emergency pan", union_all([part_outline(p, obj) for p in pan]).envelope,
                    *band(pan)))
    for part in parts:
        role = part.get("role")
        if role in DRAIN_ROLES:
            out.append((role.removeprefix("flexx:"), part_outline(part, obj), *band([part])))
    return out
