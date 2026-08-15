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

from shapely.geometry import Polygon
from shapely.ops import unary_union

from typehaus.resolve.model import ResolvedModel, Ring

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
