"""Countertop slab prisms shared by the viewer (model.json) and the GLB.

A slab is drawn in its own material. Explicit fixture cutouts replace a sink base's
schematic centred counter; other basin hosts keep their own cut-out counter and the slab
leaves their footprints clear. Viewer and GLB consume the same rings and holes.
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
    """Placeable tag -> its replacement slab, including bases with explicit fixture holes."""
    symbols = _plan_symbols(model)
    objects = {obj.tag: obj for obj in model.canvas_objects}
    hosted: dict[str, str] = {}
    for top in sorted(model.countertops, key=lambda item: item.tag):
        for tag in top.hosts:
            obj = objects.get(tag)
            if obj is not None and not _keeps_symbol_counter(obj, top, symbols):
                hosted.setdefault(tag, top.tag)
    return hosted


def _keeps_symbol_counter(obj: Any, top: ResolvedCountertop,
                         symbols: dict[str, Any]) -> bool:
    symbol = symbols.get(obj.type_ref or "")
    if symbol == "sink-base" and any(
        Polygon(ring).intersects(Polygon(obj.footprint)) for ring in top.cutouts
    ):
        # An explicitly placed opening replaces the cabinet's centred schematic hole.
        return False
    return symbol in SINK_SYMBOLS


def countertop_prisms(model: ResolvedModel, top: ResolvedCountertop,
                      symbols: dict[str, Any] | None = None) -> tuple[GPrism, ...]:
    """Slab outline less fixture openings and retained basin hosts, at host counter height."""
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
             if _keeps_symbol_counter(obj, top, symbols) and len(obj.footprint) >= 3]
    sinks.extend(Polygon(ring) for ring in top.cutouts)
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
