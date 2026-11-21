"""Drain tees at the low points a run names (``DuctRun.drains``), billed in ``[duct_parts]``.

The product is the drain's own ``product_ref``, not a ``DuctStandard`` row: a drain tap is
chosen per low point, not per size. A drain whose ``at`` is on no vertex derives nothing;
``mep.duct_drainage`` reports it.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.model.ducts import DuctStandard, duct_size_text
from typehaus.quantities import M_PER_IN
from typehaus.resolve.duct_branches import section
from typehaus.resolve.mep_fittings import MIN_FITTING_TURN_DEG
from typehaus.resolve.model_ducts import Point3, ResolvedDuctPart

#: How far a drain's ``at`` may sit from the vertex it names, in plan.
AT_TOLERANCE_M = 1.0 * M_PER_IN
#: A capped tap's outlet: IMC 307.2.2's 3/4" condensate minimum, ready for the line.
CAPPED_OUTLET_M = 0.75 * M_PER_IN


def drain_vertex(duct: Any, at: tuple[float, float]) -> int | None:
    """The lowest path vertex within ``AT_TOLERANCE_M`` of ``at`` in plan (a riser foot is
    two vertices at one plan point), or None."""
    hits = [i for i, p in enumerate(duct.path) if math.dist(p, at) <= AT_TOLERANCE_M]
    if not hits or len(duct.z_m) != len(duct.path):
        return None
    return min(hits, key=lambda i: duct.z_m[i])


def _turn_deg(a: Point3, here: Point3, b: Point3) -> float:
    """The 3D turn at ``here`` between legs a->here and here->b."""
    u = [here[i] - a[i] for i in range(3)]
    v = [b[i] - here[i] for i in range(3)]
    nu, nv = math.hypot(*u), math.hypot(*v)
    if nu < 1e-9 or nv < 1e-9:
        return 0.0
    cos = sum(p * q for p, q in zip(u, v, strict=True)) / (nu * nv)
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def _tap_point(duct: Any, index: int, standard: DuctStandard) -> Point3:
    """Where the tee stands: at the vertex, or one elbow take-off along the level leg into
    it where the vertex is a turn (the elbow's mouth, its lowest inside point). A grade
    break takes no elbow, so its tee stays on the vertex."""
    pts = [(x, y, z) for (x, y), z in zip(duct.path, duct.z_m, strict=True)]
    here = pts[index]
    legs = [pts[j] for j in (index - 1, index + 1) if 0 <= j < len(pts)]
    level = [p for p in legs if math.dist(p[:2], here[:2]) > 1e-6]
    if len(legs) < 2 or not level or _turn_deg(legs[0], here, legs[1]) < MIN_FITTING_TURN_DEG:
        return here
    row = standard.elbow_for(duct.diameter_m) if duct.diameter_m else None
    reach = (row.radius_m() if row else None) or duct.diameter_m or 0.0
    other = level[0]
    length = math.dist(here, other)
    t = min(reach / length, 1.0) if length > 1e-9 else 0.0
    return tuple(here[i] + t * (other[i] - here[i]) for i in range(3))  # type: ignore[return-value]


def drain_parts(model: Any, standard: DuctStandard) -> list[ResolvedDuctPart]:
    by_tag = {d.tag: d for d in model.ducts}
    pipes = {r.tag: r for r in model.pipe_runs}
    parts: list[ResolvedDuctPart] = []
    for run in model.plan.all_elements():
        drains = getattr(run, "drains", ())
        duct = by_tag.get(run.tag) if drains else None
        if duct is None:
            continue
        for drain in drains:
            index = drain_vertex(duct, (drain.at.x.meters, drain.at.y.meters))
            if index is None:
                continue
            pipe = pipes.get(drain.pipe_ref) if drain.pipe_ref else None
            parts.append(ResolvedDuctPart(
                kind="drain_tee", run_tag=duct.tag, storey=duct.storey, size=section(duct),
                point=_tap_point(duct, index, standard), axis=(0.0, 0.0, -1.0),
                branch=duct_size_text(pipe.diameter_m if pipe is not None else CAPPED_OUTLET_M),
                other=drain.pipe_ref, product_ref=drain.product_ref))
    return parts
