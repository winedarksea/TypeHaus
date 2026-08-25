"""IFC builders for a *run*: a section carried along a 3D polyline (→ resolve/sweep.py).

Two shapes, because IFC has two idioms and they are not interchangeable. A **round** section
is one ``IfcSweptDiskSolid`` over an ``IfcPolyline`` directrix, which is what a pipe and a
round handrail both are in IFC4 and is the only form that keeps a bend whole. Anything else
is one ``IfcExtrudedAreaSolid`` per leg, square-ended, because an extrusion runs along one
straight axis and cannot carry a mitre.

Either way the run is ONE element with ONE representation. Before this a drain arrived as a
squat box per plan segment and a raked handrail as 292 separate ``IfcRailing``s — one per
1-1/2" of fall — because ``ResolvedSolid`` could only extrude a plan ring straight up in Z.

Split from :mod:`typehaus.emit.ifc.lowlevel`, which re-exports both names.
"""

from __future__ import annotations

from typing import Any

Vec3 = tuple[float, float, float]


def add_swept_disk(f: Any, body_ctx: Any, *, points_m: list[Vec3],
                   radius_m: float) -> Any:
    """A round section carried along a 3D polyline — ``IfcSweptDiskSolid``.

    The IFC4 idiom for a pipe *and* for a round handrail, and the only one of them that keeps
    the run whole: a drain used to arrive as one squat box per plan segment and a raked rail
    as 292 separate ``IfcRailing``s, because ``IfcExtrudedAreaSolid`` cannot bend. The
    directrix is the run's own centreline — mitres, drops and all.
    """
    directrix = f.createIfcPolyline([f.createIfcCartesianPoint(p) for p in points_m])
    solid = f.createIfcSweptDiskSolid(directrix, radius_m, None, None, None)
    return f.createIfcShapeRepresentation(body_ctx, "Body", "AdvancedSweptSolid", [solid])


def add_swept_run(f: Any, body_ctx: Any, *,
                  profile_points: list[tuple[float, float]],
                  legs: list[tuple[Vec3, Vec3, Vec3, float]]) -> Any:
    """A *shaped* section carried along a 3D polyline: one extrusion per leg, one Body.

    :func:`add_swept_disk`'s counterpart for anything that is not a circle — a square rail's
    stock section. ``IfcExtrudedAreaSolid`` runs along one straight axis, so the mitre cannot
    survive the trip and each leg is square-ended; still one element with one representation
    rather than a solid per band. ``legs`` is ``resolve/sweep.py::sweep_leg_axes``'s output.
    """
    items = []
    for origin_m, axis, ref_direction, depth_m in legs:
        points = [f.createIfcCartesianPoint(point) for point in profile_points]
        polyline = f.createIfcPolyline(points + [points[0]])
        profile = f.createIfcArbitraryClosedProfileDef("AREA", None, polyline)
        placement = f.createIfcAxis2Placement3D(
            f.createIfcCartesianPoint(origin_m),
            f.createIfcDirection(axis), f.createIfcDirection(ref_direction),
        )
        items.append(f.createIfcExtrudedAreaSolid(
            profile, placement, f.createIfcDirection((0.0, 0.0, 1.0)), depth_m))
    if not items:
        return None
    return f.createIfcShapeRepresentation(body_ctx, "Body", "SweptSolid", items)
