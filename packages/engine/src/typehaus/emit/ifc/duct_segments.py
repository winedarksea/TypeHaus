"""``IfcDuctSegment`` per path leg, trimmed to the stretches the run is drawn as (#136).

``resolve/duct_fabrication.py`` replaces a run's ``{uid}-run`` solid with straight stretches
and elbows, every piece hosted on the run (``host_ref == duct.tag``, tag ``{tag}-RUN``). A leg
exports as the stretch(es) of it that survive: its body stops where an elbow, take-off collar,
damper or end boot takes over, so segments no longer overlap the fittings. Keys stay
``seg-{leg:02d}`` (stable GlobalIds); a leg a damper or collar splits in two adds
``seg-{leg:02d}-2``, ... after the first. A leg no stretch survives on keeps its element and
GlobalId bodiless. With no pieces at all (a run the stage skipped) each leg exports whole.

A round section is an ``IfcSweptDiskSolid``; a rectangular one an extrusion on the stretch's
own frame (``SolidSweep.vertical_up``), so a riser keeps the section the level legs carry.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from typehaus._meta import PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.model.ids import derive_child_guid
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel, SolidSweep
from typehaus.resolve.sweep import (
    carried_up,
    clean_path,
    rect_profile,
    sweep_leg_axes,
)

Vec3 = tuple[float, float, float]
#: A stretch leg this near an original leg lies on it.
_ON_LEG_M = 1e-3


def is_elbow_piece(solid: Any) -> bool:
    return "-elbow-" in solid.uid


def run_pieces(model: ResolvedModel) -> dict[str, list[Any]]:
    """Each duct run's drawn pieces (stretches and elbows), in model order, by run tag."""
    out: dict[str, list[Any]] = {}
    for solid in model.solids:
        if solid.host_ref and solid.sweep is not None and solid.tag.endswith("-RUN"):
            out.setdefault(solid.host_ref, []).append(solid)
    return out


def _distance_to_leg(point: Vec3, a: Vec3, b: Vec3) -> float:
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    n2 = ab[0] ** 2 + ab[1] ** 2 + ab[2] ** 2
    t = 0.0 if n2 < 1e-18 else max(0.0, min(1.0, sum(
        (point[k] - a[k]) * ab[k] for k in range(3)) / n2))
    return math.dist(point, tuple(a[k] + ab[k] * t for k in range(3)))


def _legs(duct: Any) -> list[tuple[int, Vec3, Vec3]]:
    """``(index, p0, p1)`` per drawn leg of ``duct.path``; a repeated vertex is no leg."""
    z_m = getattr(duct, "z_m", None) or ()
    out = []
    for index in range(len(duct.path) - 1):
        p0, p1 = duct.path[index], duct.path[index + 1]
        z0, z1 = (z_m[index], z_m[index + 1]) if len(z_m) == len(duct.path) else (0.0, 0.0)
        if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) < 1e-6 and abs(z1 - z0) < 1e-9:
            continue
        out.append((index, (p0[0], p0[1], z0), (p1[0], p1[1], z1)))
    return out


def _intervals(duct: Any, legs: Sequence[tuple[int, Vec3, Vec3]],
               pieces: Sequence[Any]) -> dict[int, list[tuple[Vec3, Vec3, Any]]]:
    """Per leg index, the ``(start, end, SolidSweep)`` bodies it exports as, along the leg."""
    out: dict[int, list[tuple[Vec3, Vec3, Any]]] = {index: [] for index, _, _ in legs}
    stretches = [p for p in pieces if not is_elbow_piece(p)]
    if not stretches or not getattr(duct, "z_m", None):
        profile = tuple(rect_profile(duct.width_m, duct.depth_m))
        sweep_up = carried_up([a for _, a, _ in legs] + [legs[-1][2]]) if legs else None
        for index, a, b in legs:
            out[index].append((a, b, SolidSweep(path=(a, b), profile=profile,
                                                vertical_up=sweep_up)))
        return out
    for piece in stretches:
        path = clean_path(piece.sweep.path)
        for a, b in zip(path, path[1:], strict=False):
            mid = tuple((a[k] + b[k]) / 2.0 for k in range(3))
            index, gap = min(((i, _distance_to_leg(mid, p0, p1)) for i, p0, p1 in legs),
                             key=lambda item: item[1], default=(None, math.inf))
            if index is None or gap > _ON_LEG_M:
                continue
            out[index].append((a, b, SolidSweep(
                path=(a, b), profile=piece.sweep.profile,
                vertical_up=piece.sweep.vertical_up)))
    return out


def _representation(f: Any, body: Any, duct: Any, a: Vec3, b: Vec3, sweep: Any) -> Any:
    if duct.diameter_m is not None:
        return ll.add_swept_disk(f, body, points_m=[a, b], radius_m=duct.diameter_m / 2.0)
    return ll.add_swept_run(f, body, profile_points=[tuple(p) for p in sweep.profile],
                            legs=sweep_leg_axes(sweep))


def emit_duct_run(f: Any, body: Any, duct: Any, storeys: dict[str, Any], project_uuid: Any,
                  pieces: Sequence[Any] = ()) -> list[Any]:
    """One ``IfcDuctSegment`` per stretch of each path leg (module docstring)."""
    legs = _legs(duct)
    intervals = _intervals(duct, legs, pieces) if legs else {}
    segments = []
    for index, bodies in intervals.items():
        for n, (a, b, sweep) in enumerate(bodies or [(None, None, None)], start=1):
            child_key = f"seg-{index:02d}" if n == 1 else f"seg-{index:02d}-{n}"
            element = ll.create_entity(f, "IfcDuctSegment", name=f"{duct.tag}/{child_key}")
            element.GlobalId = derive_child_guid(project_uuid, duct.uid, child_key)
            if sweep is not None:
                ll.assign_representation(f, element, _representation(
                    f, body, duct, a, b, sweep))
            ll.ensure_pset(f, element, PSET_SOURCE, {"uid": duct.uid, "tag": duct.tag})
            ll.ensure_pset(f, element, "TypeHaus_Duct", {
                "system": duct.system, "width_in": duct.width_m / M_PER_IN,
                "depth_in": duct.depth_m / M_PER_IN, "routing": duct.routing,
                # Blank rather than absent where unset: a pset key that comes and goes makes
                # a schedule column that comes and goes.
                "diameter_in": (duct.diameter_m / M_PER_IN
                                if duct.diameter_m is not None else 0.0),
                "material": duct.material or "", "insulation": duct.insulation or "",
            })
            ll.assign_container(f, element, storeys[duct.storey])
            segments.append(element)
    return segments


def emit_duct_runs(f: Any, body: Any, model: ResolvedModel, storeys: dict[str, Any],
                   project_uuid: Any) -> list[Any]:
    """Every duct run's segments, in uid order."""
    by_run = run_pieces(model)
    out: list[Any] = []
    for duct in sorted(model.ducts, key=lambda item: item.uid):
        out.extend(emit_duct_run(f, body, duct, storeys, project_uuid,
                                 by_run.get(duct.tag, ())))
    return out

