"""What a masonry wall weighs, and what is under it — the reading two checks share.

Extracted from ``checks/structural/guards.py``, which asked both questions of a parapet, the
moment ``checks/structural/through_deck.py`` needed the same two of a wall standing in a
floor deck. The question is the same either way and there must be one answer to it: a guard
and a fireplace pier that disagreed about what "bears on wood" means would be two rules
wearing one number.

The load is derived from the wall's *own* assembly — every layer's thickness times its
material's density, times the wall's height — rather than from a magic number, so a lighter
wall prices itself out of a finding automatically and a heavier one prices itself in. Air
gaps carry nothing and are skipped; a solid layer whose material states no ``density`` makes
the whole answer ``None``, because a load computed from a partial stack is not a load.

** THAT WEIGHER NOW LIVES IN ``resolve/assembly_weight.py`` AND IS RE-EXPORTED HERE. **
``engineering/pier_basis`` needs the same number to turn a wall standing on a beam into a
line load on the posts under it, and ``engineering`` may not import ``checks``
(``tests/test_package_leaves.py`` walks the AST for exactly that). ``resolve`` is where a
check and a calculation may both reach. The name stays put so ``guards.py`` and
``through_deck.py`` need no edit, and so there is still one answer to "what does this wall
weigh".
"""

from __future__ import annotations

from typing import Any

from typehaus.model.enums import LayerFunction
from typehaus.resolve.assembly_weight import KG_PER_M_TO_PLF, dead_load_plf
from typehaus.resolve.solid_categories import is_pour_slab

#: A support's top is "under" the wall when the two are this close in Z. Same slop the rest
#: of the stacking logic uses — a storey's walls land exactly on the one below.
BEARING_Z_TOL_M = 0.05
#: How far off a support's own axis the wall's line may sit and still bear on it. Half the
#: support's thickness plus this: a wall is aligned to a face, not to a centreline.
BEARING_PLAN_TOL_M = 0.10
#: Material hatch families that carry masonry without further thought. ``concrete`` is the
#: catalog's family for both poured concrete and masonry units (cmu, brick all hatch
#: concrete), which is the distinction that matters here — they are all hard bearing.
_HARD_SUPPORT_HATCHES = frozenset({"concrete", "masonry", "metal"})


def support_at(ctx: Any, wall: Any, point: tuple[float, float]) -> tuple[str | None, str | None]:
    """``(kind, name)`` under one station of ``wall``'s run, at its base elevation.

    ``kind`` is ``"hard"`` (concrete, masonry, steel, a footing), ``"wood"`` (a framed floor
    deck), or ``None`` where nothing is modeled under that station.
    """
    from shapely.geometry import LineString, Point, Polygon

    base = wall.z0_m
    probe = Point(point)
    for other in ctx.model.walls:
        if other.tag == wall.tag or abs(other.z1_m - base) > BEARING_Z_TOL_M:
            continue
        reach = other.thickness_m / 2.0 + BEARING_PLAN_TOL_M
        if LineString(other.axis).distance(probe) > reach:
            continue
        return (wall_support_kind(ctx, other), other.tag)
    for solid in ctx.model.solids:
        if not (solid.category in ("footing", "pad") or is_pour_slab(solid.category)):
            continue
        if abs(solid.z1_m - base) > BEARING_Z_TOL_M or len(solid.outline) < 3:
            continue
        if Polygon(solid.outline).covers(probe):
            return ("hard", solid.tag)
    for floor in ctx.model.floors:
        if (not floor.deck_outline
                or abs(floor.deck_top_at(probe.x, probe.y) - base) > BEARING_Z_TOL_M):
            continue
        if Polygon(floor.deck_outline).covers(probe):
            return ("wood", floor.tag)
    return (None, None)


def wall_support_kind(ctx: Any, wall: Any) -> str:
    """A supporting wall's bearing class, read off its structure layer's material hatch.

    The hatch family is the catalog's own answer to "what is this made of", and it is the
    one that separates hard bearing from framing: every masonry unit and every pour hatches
    ``concrete``, steel hatches ``metal``, and a stud wall's structure layer is lumber.
    """
    materials = {material.tag: material for material in ctx.plan.library.materials}
    for layer in wall.depth_layers():
        if layer.function != LayerFunction.STRUCTURE.value:
            continue
        hatch = getattr(materials.get(layer.material_ref or ""), "hatch", None)
        return "hard" if hatch in _HARD_SUPPORT_HATCHES else "wood"
    return "wood"


__all__ = ["BEARING_PLAN_TOL_M", "BEARING_Z_TOL_M", "KG_PER_M_TO_PLF", "dead_load_plf",
           "support_at", "wall_support_kind"]
