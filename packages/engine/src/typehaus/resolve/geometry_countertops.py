"""Countertop slab prisms shared by the viewer (model.json) and the GLB.

A slab is drawn in its own material. Explicit fixture cutouts replace a sink base's
schematic centred counter; other basin hosts keep their own cut-out counter and the slab
leaves their footprints clear. Viewer and GLB consume the same rings and holes.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import Point, Polygon

from typehaus.model.canvas import model_symbol_for
from typehaus.model.placeable_symbols._solid_surface_vanity import deck_height
from typehaus.resolve.fillet import filleted_ring
from typehaus.resolve.geometry_ir import GPrism
from typehaus.resolve.model import ResolvedCountertop, ResolvedModel
from typehaus.resolve.overlay import union_all

#: Plan symbols whose own counter is cut round a bowl; the slab leaves their footprint alone.
SINK_SYMBOLS = frozenset({"sink-base", "sektion-axstad-kitchen-sink", "vanity"})

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
    if symbol in {"sink-base", "sektion-axstad-kitchen-sink"} and any(
        Polygon(ring).intersects(Polygon(obj.footprint)) for ring in top.cutouts
    ):
        # An explicitly placed opening replaces the cabinet's centred schematic hole.
        return False
    return symbol in SINK_SYMBOLS


def countertop_top_z(model: ResolvedModel, top: ResolvedCountertop) -> float | None:
    """The slab's top: the highest host counter (a vanity's deck, not its spout)."""
    objects = {obj.tag: obj for obj in model.canvas_objects}
    types = {item.tag: item for name in _PLACEABLE_TYPE_COLLECTIONS
             for item in getattr(model.plan.library, name)}
    tops = []
    for tag in top.hosts:
        obj = objects.get(tag)
        if obj is None or obj.body_z1_m is None:
            continue
        product_type = types.get(obj.type_ref)
        symbol = model_symbol_for(product_type)
        if symbol in {"solid-surface-vanity", "sektion-vanity", "sektion-vanity-indy"}:
            # Overall fixture height includes the spout; the overhang meets the bonded deck.
            tops.append(obj.body_z1_m - product_type.height.meters
                        + deck_height(product_type.height.meters,
                                      "indy" if symbol.endswith("-indy")
                                      else "genta"))
        else:
            tops.append(obj.body_z1_m)
    return max(tops) if tops else None


def countertop_prisms(model: ResolvedModel, top: ResolvedCountertop,
                      symbols: dict[str, Any] | None = None) -> tuple[GPrism, ...]:
    """Filleted slab less fixture openings, drilled holes and retained basin hosts.

    The corners are ``resolve/fillet.py``'s, the same arcs ``haus countertops`` cuts.
    """
    symbols = symbols if symbols is not None else _plan_symbols(model)
    objects = {obj.tag: obj for obj in model.canvas_objects}
    hosts = [objects[tag] for tag in top.hosts if tag in objects]
    z1 = countertop_top_z(model, top)
    if len(top.outline) < 3 or z1 is None or top.thickness_m <= 0:
        return ()
    z0 = z1 - top.thickness_m
    radii = top.corner_radii_m if len(top.corner_radii_m) == len(top.outline) else ()
    slab = Polygon(filleted_ring(top.outline, radii) if radii else top.outline)
    sinks = [Polygon(obj.footprint) for obj in hosts
             if _keeps_symbol_counter(obj, top, symbols) and len(obj.footprint) >= 3]
    sinks.extend(Polygon(ring) for ring in top.cutouts)
    sinks.extend(Point(hole.center).buffer(hole.diameter_m / 2.0, quad_segs=4)
                 for hole in top.holes)
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
