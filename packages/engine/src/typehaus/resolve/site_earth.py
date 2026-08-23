"""Where the site earth sheet is cut away by the structures standing on it.

The translucent "site earth" plane is a single sheet at grade. Anything that has been
excavated out of the soil must punch a hole in it, or the sheet slices through the interior
spaces it should have been dug away for.

The rule is derived, not enumerated per structure: **soil is displaced wherever a floor slab
finishes at or below grade**. A slab is the one element that is by definition both a surface
people stand on and the bottom of an excavation, so its plan outline is exactly the ring the
earth is missing. That covers the house basement, a freestanding garage on its own slab, and
an open-air sunken garden alike — none of which share a storey, a room set, or a wall loop.

Consumers: the IFC site pad (``emit/ifc/site.py``), the serialized UI contract
(``server/model_json_document.py`` → ``site.earth_voids``), and the three.js site sheet.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import Polygon
from shapely.ops import unary_union

from typehaus.resolve.model import ResolvedModel, ResolvedSolid, Ring

# A slab-on-grade tops out level with the finished exterior grade, and rounding through
# feet → meters leaves it a hair either side. Treat that band as "at grade": the slab still
# sits in a hole that was dug for it.
EARTH_PLANE_SLAB_TOP_TOLERANCE_M = 0.02

_EARTH_DISPLACING_SLAB_CATEGORY = "slab"
_MINIMUM_RING_VERTICES = 3


def site_grade_elevation_m(model: ResolvedModel) -> float:
    """Elevation of the site earth sheet (the authored grade; main-floor datum if absent)."""
    grade = model.plan.project.site.grade
    return grade.meters if grade is not None else 0.0


def earth_plane_void_rings(model: ResolvedModel) -> list[Ring]:
    """Plan rings the site earth sheet must be cut by, as disjoint outer boundaries.

    Slab footprints stack (a main-floor deck slab over the basement slab it shares a
    footprint with) and abut, so they are unioned first: ``IfcArbitraryProfileDefWithVoids``
    and the three.js ``Shape`` hole list both take *non-overlapping* inner rings, and a
    doubled hole reads there as no hole at all.
    """
    grade_z = site_grade_elevation_m(model)
    ceiling = grade_z + EARTH_PLANE_SLAB_TOP_TOLERANCE_M
    footprints = []
    for solid in sorted(model.solids, key=lambda item: item.uid):
        if solid.category != _EARTH_DISPLACING_SLAB_CATEGORY:
            continue
        if solid.z1_m > ceiling:  # a raised deck sits *on* the earth, it does not displace it
            continue
        if len(solid.outline) < _MINIMUM_RING_VERTICES:
            continue
        polygon = Polygon(solid.outline)
        if polygon.is_valid and polygon.area > 0.0:
            footprints.append(polygon)
    if not footprints:
        return []
    merged = unary_union(footprints)
    parts = merged.geoms if merged.geom_type == "MultiPolygon" else [merged]
    # Interior holes in the merged footprint are earth the excavation left standing, so only
    # the outer boundary of each part cuts the sheet.
    return [[(x, y) for (x, y) in part.exterior.coords[:-1]] for part in parts]


# How far an open excavation reaches sideways before it stops governing a footing's frost
# cover. IRC R403.1.4.1 measures the required depth from the **lowest adjacent finished
# grade** and never publishes a distance at which "adjacent" stops mattering, so this is a
# stand-in with a physical basis rather than a code citation: frost drives into the ground
# from every exposed face, so an excavation within roughly the frost depth of a footing has
# removed the soil column that was supposed to protect it. Callers pass their own profile's
# frost depth; this is the fallback for a profile that declares none.
DEFAULT_EXCAVATION_REACH_M = 42 * 0.0254


def _is_a_floor(model: ResolvedModel, solid: ResolvedSolid) -> bool:
    """Is this ``slab`` a surface something stands on, or a buried layer of the ground?

    A frost-protection wing is authored as a thin ``Slab`` because a horizontal band of rigid
    foam has no other element kind to be — ``Layer.extent`` measures from ``WALL_BASE`` /
    ``WALL_TOP`` / ``GRADE`` and is vertical-only, so it cannot describe a skirt reaching out
    sideways under a floor. Read as a floor, such a wing is a *lower* excavation floor than
    the garden slab it is buried under, and it would drop the derived grade another 3-1/2"
    for every footing beside it.

    An assembly says which it is: ``role="band"`` is the buried case. A slab with no
    assembly at all has said nothing and stays a floor, which is what keeps SL-SG-FLOOR —
    authored bare — the excavation floor it is.
    """
    if solid.assembly is None:
        return True
    assembly = model.plan.library.resolve_assembly(solid.assembly)
    return assembly is None or assembly.role != "band"


def _conditioned_room_footprint(model: ResolvedModel) -> Any | None:
    """Union of every conditioned room's clear face, in plan."""
    faces = []
    for room in model.rooms:
        if not room.conditioned or len(room.clear_face) < _MINIMUM_RING_VERTICES:
            continue
        polygon = Polygon(room.clear_face)
        if polygon.is_valid and polygon.area > 0.0:
            faces.append(polygon)
    return unary_union(faces) if faces else None


def open_excavation_floors(model: ResolvedModel) -> list[tuple[str, Any, float]]:
    """``(tag, plan polygon, top elevation)`` for every open excavation floor below grade.

    Returned as a list rather than reduced to one number because the caller wants to name
    the surface that governed: "8" below the sunken-garden floor" is a finding an owner can
    act on; "8" below grade" is one they would read as fine. See :func:`_below_grade_floors`
    for what makes an excavation *open*.
    """
    return _below_grade_floors(model)[0]


def heated_floor_footprint(model: ResolvedModel) -> Any | None:
    """Union of the below-grade floor slabs that lie under conditioned rooms, or ``None``.

    The other half of the same split. Where :func:`open_excavation_floors` is the ground a
    footing beside it is measured *down from*, this is the ground a footing standing *on*
    it is sheltered by: an interior footing under a heated basement floor is "otherwise
    protected from frost" in IRC R403.1.4.1's own words, which is why nobody digs the
    columns of a heated basement 42" below its slab.
    """
    footprints = _below_grade_floors(model)[1]
    return unary_union(footprints) if footprints else None


def _below_grade_floors(
    model: ResolvedModel,
) -> tuple[list[tuple[str, Any, float]], list[Any]]:
    """Split every below-grade slab into ``(open excavation floors, heated floors)``.

    A slab is the bottom of a hole — that is the doctrine the earth-plane void above runs
    on — but only some holes stay *open*. The basement slab is the floor of conditioned
    rooms: the soil beside its footings was replaced by a wall and backfilled against, so
    the ground surface over those footings is still the site grade plane. A below-grade slab
    with **no conditioned room over it** is the other case — the sunken garden — and it is
    open ground at its own elevation. Weather reaches it, frost drives down from it, and a
    footing beside it is measured from *that* surface, not from the plane 6'-6" above.
    """
    grade_z = site_grade_elevation_m(model)
    ceiling = grade_z - EARTH_PLANE_SLAB_TOP_TOLERANCE_M
    conditioned = _conditioned_room_footprint(model)
    open_floors: list[tuple[str, Any, float]] = []
    heated: list[Any] = []
    for solid in sorted(model.solids, key=lambda item: item.uid):
        if solid.category != _EARTH_DISPLACING_SLAB_CATEGORY:
            continue
        if solid.z1_m >= ceiling:  # at or above grade — not an excavation that lowers grade
            continue
        if len(solid.outline) < _MINIMUM_RING_VERTICES:
            continue
        if not _is_a_floor(model, solid):
            continue
        polygon = Polygon(solid.outline)
        if not polygon.is_valid or polygon.area <= 0.0:
            continue
        if conditioned is not None and polygon.intersection(conditioned).area > 0.5 * polygon.area:
            heated.append(polygon)  # the floor of a heated room, not of a hole left open
            continue
        open_floors.append((solid.tag, polygon, solid.z1_m))
    return open_floors, heated


def local_grade_elevation_m(
    model: ResolvedModel,
    outline: Ring,
    reach_m: float = DEFAULT_EXCAVATION_REACH_M,
    floors: list[tuple[str, Any, float]] | None = None,
    sheltered_by: Any | None = None,
) -> tuple[float, str | None]:
    """The lowest exterior ground surface over or beside ``outline``, and what set it.

    ``(site grade, None)`` where nothing has been dug beside it, which is every footing in
    a house with no sunken court, walkout or window well — so this is a strict refinement of
    the single global plane, never a different answer for an undisturbed site.

    ``sheltered_by`` (normally :func:`heated_floor_footprint`) is the exception that keeps
    this from over-reaching *inward*. The Catlin basement's central spine footing sits 10"
    north of the sunken garden in plan and 9'-2" under a heated slab, and a bare distance
    test reads that 10" and lowers its grade by 6'-6". It is an interior footing inside the
    heated envelope; the excavation is on the far side of an insulated foundation wall from
    it, and no exterior ground surface is anywhere over it. Centroid rather than any
    overlap, because a perimeter footing straddles the line by half its width and belongs
    on the outside of it.
    """
    grade = site_grade_elevation_m(model)
    if len(outline) < _MINIMUM_RING_VERTICES:
        return grade, None
    here = Polygon(outline)
    if not here.is_valid or here.area <= 0.0:
        return grade, None
    if sheltered_by is not None and sheltered_by.contains(here.centroid):
        return grade, None
    lowest, governing = grade, None
    for tag, polygon, top_m in (open_excavation_floors(model) if floors is None else floors):
        if top_m >= lowest:
            continue
        if here.distance(polygon) <= reach_m + 1e-9:
            lowest, governing = top_m, tag
    return lowest, governing
