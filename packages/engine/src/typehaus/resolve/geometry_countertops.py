"""Countertop slab prisms shared by the viewer (model.json) and the GLB.

A slab is drawn in its own material, the way a window stool is, so a cantilever with no
cabinet under it shows and an oak top reads as oak. A host that draws its own counter round
a basin (``SINK_SYMBOLS``) keeps it: the slab is cut back to that host's footprint, or it
would bury the bowl. Every other host stops drawing its grey symbol counter.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import Polygon

from typehaus.resolve.geometry_ir import GPrism
from typehaus.resolve.model import ResolvedCountertop, ResolvedModel
from typehaus.resolve.overlay import union_all

#: Plan symbols whose own counter is cut round a bowl; the slab leaves their footprint alone.
SINK_SYMBOLS = frozenset({"sink-base", "vanity"})

_PLACEABLE_TYPE_COLLECTIONS = ("furniture_types", "fixture_types", "appliance_types",
                               "equipment_types")


def _plan_symbols(model: ResolvedModel) -> dict[str, str | None]:
    return {item.tag: getattr(item, "plan_symbol", None)
            for name in _PLACEABLE_TYPE_COLLECTIONS
            for item in getattr(model.plan.library, name)}


def slab_hosts(model: ResolvedModel) -> dict[str, str]:
    """Placeable tag -> the countertop that replaces its symbol counter (sink hosts omitted)."""
    symbols = _plan_symbols(model)
    objects = {obj.tag: obj for obj in model.canvas_objects}
    hosted: dict[str, str] = {}
    for top in sorted(model.countertops, key=lambda item: item.tag):
        for tag in top.hosts:
            obj = objects.get(tag)
            if obj is not None and symbols.get(obj.type_ref or "") not in SINK_SYMBOLS:
                hosted.setdefault(tag, top.tag)
    return hosted


def countertop_prisms(model: ResolvedModel, top: ResolvedCountertop,
                      symbols: dict[str, Any] | None = None) -> tuple[GPrism, ...]:
    """The slab as prisms: its outline less any sink host, topped at the hosts' highest body."""
    symbols = symbols if symbols is not None else _plan_symbols(model)
    objects = {obj.tag: obj for obj in model.canvas_objects}
    hosts = [objects[tag] for tag in top.hosts if tag in objects]
    tops = [obj.body_z1_m for obj in hosts if obj.body_z1_m is not None]
    if len(top.outline) < 3 or not tops or top.thickness_m <= 0:
        return ()
    z1 = max(tops)
    z0 = z1 - top.thickness_m
    slab = Polygon(top.outline)
    sinks = [Polygon(obj.footprint) for obj in hosts
             if symbols.get(obj.type_ref or "") in SINK_SYMBOLS and len(obj.footprint) >= 3]
    if sinks:
        slab = slab.difference(union_all(sinks))
    parts = [slab] if slab.geom_type == "Polygon" else list(getattr(slab, "geoms", ()))
    return tuple(
        GPrism(ring=tuple((float(x), float(y)) for x, y in part.exterior.coords[:-1]),
               z0_m=z0, z1_m=z1,
               voids=tuple(tuple((float(x), float(y)) for x, y in hole.coords[:-1])
                           for hole in part.interiors))
        for part in parts
        if part.geom_type == "Polygon" and not part.is_empty and part.area > 1e-6)
