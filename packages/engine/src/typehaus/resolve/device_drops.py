"""Derived NM sleeves: one vertical 3/4" EMT drop per surface box, box to ceiling (#93).

On bare concrete the house feeds a surface box with NM-B run overhead and protected down
the wall in an EMT sleeve (NEC 334.15(B)/(C); a sleeve is outside the Chapter 9 fill tables,
Note 2, and needs no bonding of its own, 250.86 Ex. 2). No horizontal runs on the wall.

The drop's centreline is the wall face plus half its OD; it runs from the box's top
knockout to the lowest surface overhead — the finished ceiling where there is one, the deck
soffit where the room is open — or, where a trunk or duct hugs the wall across its line,
1/2" under that run. The NM above is then off the sleeve; ``electrical.nm_sleeve_reach``
says how far, so an offset around the run is decided rather than assumed away.
Skipped where an authored ``ConduitRun`` already reaches the box. It joins ``model.conduits``
as a ``derived`` run, so the envelopes, the concrete crossing walk and the solids see it, and
the trunk-only readers (conductors, data reach, bend totals) leave it out.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.resolve.model import ResolvedConduitRun, ResolvedModel
from typehaus.resolve.pipe_sections import raceway_outside_diameter_m


def add_derived_run(model: ResolvedModel, *, uid: str, tag: str, storey: str,
                    points: list[tuple[float, float, float]], trade_size_m: float,
                    material: str, service: str | None, derived: str,
                    to_ref: str | None, cast_in: bool = False,
                    stops_under: str | None = None,
                    unsleeved_m: float = 0.0) -> ResolvedConduitRun:
    """Append one derived raceway and its swept solid."""
    from typehaus.resolve.mep import _emit_run_solids, conduit_category
    from typehaus.resolve.round_solids import PIPE_FACETS
    from typehaus.resolve.sweep import round_profile

    path = [(x, y) for x, y, _ in points]
    z = tuple(p[2] for p in points)
    run = ResolvedConduitRun(
        uid=uid, tag=tag, storey=storey, path=path, trade_size_m=trade_size_m,
        z_start_m=z[0], z_end_m=z[-1],
        length_m=sum(math.dist(a, b) for a, b in zip(points, points[1:], strict=False)),
        from_ref=None, to_ref=to_ref, service=service, z_m=z, material=material,
        derived=derived, cast_in=cast_in, stops_under=stops_under, unsleeved_m=unsleeved_m)
    model.conduits.append(run)
    _emit_run_solids(model, uid, tag, storey, path, list(z),
                     round_profile(trade_size_m / 2.0, PIPE_FACETS), conduit_category(service))
    return run


def _service(model: ResolvedModel, box: Any) -> str:
    if box.device_kind == "data_outlet":
        return "data"
    circuit = next((c for c in model.plan.library.circuits if c.tag == box.circuit), None)
    return "power_240" if circuit is not None and circuit.poles == 2 else "power_120"


def _ceiling_plane(model: ResolvedModel, box: Any) -> float | None:
    from typehaus.resolve.room_floor import room_floor_elevation

    room = next((r for r in model.rooms if r.tag == box.room), None)
    storey = next((s for s in model.plan.storeys if s.tag == box.storey), None)
    if room is None or storey is None:
        return None
    plane = room_floor_elevation(model, room) + storey.default_ceiling_height.meters
    return plane if plane > box.z1_m else None


#: Air left between a sleeve's top and a run it stops under.
_CLEARANCE_M = 0.0127


def _under_runs(runs: list[tuple[str, Any, float, float]], x: float, y: float, z0: float,
                top: float, half_od: float) -> tuple[float, str | None]:
    """``top``, lowered to stop under any routed run that crosses the drop's line, and that
    run's tag (None where nothing crosses)."""
    under = None
    for tag, (path, z), radius, half_height in runs:
        for (ax, ay), (bx, by), za, zb in zip(path, path[1:], z, z[1:], strict=False):
            dx, dy = bx - ax, by - ay
            span = dx * dx + dy * dy
            if span < 1e-12:
                continue  # a riser runs beside the drop, not across it
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / span))
            if math.hypot(ax + dx * t - x, ay + dy * t - y) > radius + half_od:
                continue
            underside = za + (zb - za) * t - half_height - _CLEARANCE_M
            if z0 < underside < top:
                top, under = underside, tag
    return top, under


def derive_sleeve_drops(model: ResolvedModel) -> None:
    """One derived drop per surface box no authored raceway reaches."""
    from typehaus.resolve.device_boxes import _house
    from typehaus.resolve.overhead import OverheadIndex

    standard, reached = _house(model.plan)
    # Outside a room there is no ceiling to feed from (an outdoor box is fed otherwise).
    boxes = [box for box in model.device_boxes if box.mounting == "surface"
             and box.room is not None and box.device_tag not in reached]
    if standard is None or not boxes:
        return
    size = standard.surface_drop.meters
    half_od = raceway_outside_diameter_m(size, "emt") / 2.0
    overhead = OverheadIndex(model, finishes=True)
    from typehaus.resolve.mep_envelopes import (
        insulation_thickness_m,
        run_polylines,
        run_sections,
    )

    sections = run_sections(model)
    runs = []
    for _kind, tag, path, z in run_polylines(model):
        if len(z) == len(path) >= 2:
            half_w, half_d, insulation = sections.get(tag, (0.0, 0.0, None))
            wrap = insulation_thickness_m(insulation) or 0.0
            runs.append((tag, (path, z), half_w + wrap, half_d + wrap))
    for box in boxes:
        x = box.face_point[0] + box.normal[0] * half_od
        y = box.face_point[1] + box.normal[1] * half_od
        above = overhead.lowest_above(x, y, box.z1_m)
        if above is None:
            continue  # nothing overhead to feed from: no drop is derived
        # Under an open well the NM still comes off this storey's ceiling plane.
        ceiling = min(above.z_m, _ceiling_plane(model, box) or above.z_m)
        top, under = _under_runs(runs, x, y, box.z1_m, ceiling, half_od)
        add_derived_run(model, uid=f"{box.device_uid}-drop", tag=f"{box.device_tag}-DROP",
                        storey=box.storey, points=[(x, y, box.z1_m), (x, y, top)],
                        trade_size_m=size, material="emt", service=_service(model, box),
                        derived="nm_sleeve", to_ref=box.device_tag, stops_under=under,
                        unsleeved_m=ceiling - top)
