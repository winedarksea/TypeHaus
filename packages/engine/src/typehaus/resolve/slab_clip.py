"""A pour slab stops at the footings and walls it is cast against.

A strip footing whose top stands inside a pour slab's depth (catlin's basement: footing tops
flush with the slab top) is poured first, and the slab is placed against its sides. Drawing
the slab's authored outline through it bills that concrete twice, and the slab's base course
and board under it with it. So the slab's plan is its outline less every footing that shares
its concrete's height; its sub-slab layers inherit the clipped plan (``slab_layers``).

A wall whose body runs the slab's whole depth owns that band (#43: a wall spans floor to
floor and the floor butts into it): catlin's ``SL-M-DECK`` stops at ``W-M-E1``'s rim-band
body instead of running under it. A wall standing on the slab shares only a finish depth.

A slab cast ONTO a footing ledge (footing top at or below the slab's underside) shares no
height with it and is left whole, which is the reading ``structural.concrete_interference``
documents for continuous work.

What a slab is as a FLOOR (the ground the hole bottoms on, a heated footprint over interior
footings, where a foot or a sill plate lands) is still its authored plan: a footing flush in
the floor is floor. Those readers take :func:`floor_plan`.
"""

from __future__ import annotations

from dataclasses import replace

from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from typehaus.findings import Finding, unknown
from typehaus.resolve.model import ResolvedModel, ResolvedSolid, Ring
from typehaus.resolve.overlay import difference, intersection, union_all
from typehaus.resolve.slab_layers import FINISH_CATEGORY
from typehaus.resolve.solid_categories import is_pour_slab

#: Shared height below this is a coincident face, not a slab running through a footing.
_HEIGHT_TOL_M = 1e-4
#: Shared plan area below this is an abutment.
_AREA_TOL_M2 = 1e-4


def floor_plan(model: ResolvedModel, solid: ResolvedSolid) -> tuple[Ring, tuple[Ring, ...]]:
    """``(outline, voids)`` of the floor a solid presents: a clipped slab's authored plan."""
    # getattr: test doubles of the model and its solids carry neither field.
    plan = getattr(model, "slab_floor_plans", {}).get(getattr(solid, "uid", None))
    if plan is None:
        return solid.outline, tuple(solid.voids)
    outline, authored_voids, clipped_voids = plan
    # Voids cut after the clip (a sump, a drain) are the floor's too.
    return outline, (*authored_voids, *(v for v in solid.voids if v not in clipped_voids))


def floor_outline(model: ResolvedModel, solid: ResolvedSolid) -> Ring:
    return floor_plan(model, solid)[0]


def _plan(solid: ResolvedSolid):
    """Outline less voids. Not ``Polygon(outline, voids)``: authored voids may touch or lap."""
    voids = [Polygon(void) for void in solid.voids]
    return difference(Polygon(solid.outline), union_all(voids)) if voids else Polygon(solid.outline)


def _footings_through(slab: ResolvedSolid, footings: list[ResolvedSolid],
                      plan) -> list[Polygon]:
    shapes = []
    for footing in footings:
        if (footing.z1_m <= slab.z0_m + _HEIGHT_TOL_M
                or footing.z0_m >= slab.z1_m - _HEIGHT_TOL_M):
            continue
        shape = Polygon(footing.outline)
        if shape.intersects(plan) and intersection(shape, plan).area > _AREA_TOL_M2:
            shapes.append(shape)
    return shapes


def _walls_through(slab: ResolvedSolid, model: ResolvedModel, plan) -> list:
    """Each wall's layers whose band spans the slab's whole depth, where they lap its plan."""
    shapes = []
    for wall in model.walls:
        if wall.z0_m > slab.z0_m + _HEIGHT_TOL_M or wall.z1_m < slab.z1_m - _HEIGHT_TOL_M:
            continue
        parts = []
        for layer in wall.layers:
            z0, z1 = layer.band(wall)
            if z0 > slab.z0_m + _HEIGHT_TOL_M or z1 < slab.z1_m - _HEIGHT_TOL_M:
                continue
            if len(layer.polygon) >= 3 and (part := Polygon(layer.polygon)).area > 0.0:
                parts.append(part)
        if parts and (body := union_all(parts)).intersects(plan) and (
                intersection(body, plan).area > _AREA_TOL_M2):
            shapes.append(body)
    return shapes


def clip_pour_slabs(model: ResolvedModel) -> list[Finding]:
    """Replace each pour slab (and its top finish) by its plan less what it is cast against."""
    footings = [s for s in model.solids if s.category == "footing"]
    findings: list[Finding] = []
    for slab in [s for s in model.solids if is_pour_slab(s.category) and not s.derived]:
        plan = _plan(slab)
        shapes = (_footings_through(slab, footings, plan)
                  + _walls_through(slab, model, plan))
        if not shapes:
            continue
        cut = union_all(shapes)
        clipped = difference(plan, cut)
        if clipped.geom_type != "Polygon" or clipped.is_empty:
            findings.append(unknown(
                "integrity.slab_clip",
                f"slab {slab.tag}: what it is cast against splits it into "
                f"{clipped.geom_type}; it is drawn and billed whole", (slab.tag,)))
            continue
        clipped = orient(clipped)  # counter-clockwise shell, as authored outlines are
        outline = [tuple(point) for point in clipped.exterior.coords[:-1]]
        voids = tuple(tuple(tuple(point) for point in ring.coords[:-1])
                      for ring in clipped.interiors)
        model.slab_floor_plans[slab.uid] = (list(slab.outline), tuple(slab.voids), voids)
        prefix = f"{slab.uid}-"
        model.solids[:] = [
            replace(s, outline=list(outline), voids=voids)
            if s.uid == slab.uid or (s.category == FINISH_CATEGORY and s.uid.startswith(prefix))
            else s
            for s in model.solids]
    return findings
