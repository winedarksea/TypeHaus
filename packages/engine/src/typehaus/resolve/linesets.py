"""One ``ResolvedLineset`` per refrigerant ``PipeRun`` (decision #139).

The run is the bundled pair; this stage reads it against its head (``serves``), the head's
``outdoor_ref`` unit and port, the outdoor type's ``RefrigerantLimits`` and the house's
``LinesetStandard``: developed length, rise, exterior (cover) length, the ordered length and
the pre-flared kit it buys, the field charge, and how far each end lands from its port pair.
Graded by ``checks/mep/linesets.py``, billed in ``[linesets]``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.resolve.pipe_sections import lineset_bundle_diameter_m

#: Sample spacing for the exterior-leg walk.
_SAMPLE_M = 0.05


@dataclass(frozen=True)
class ResolvedLineset:
    tag: str
    head_tag: str | None
    outdoor_tag: str | None
    port: str | None
    liquid_m: float
    vapor_m: float
    developed_m: float
    #: Outdoor-unit end minus head end (absolute z): positive with the unit above.
    rise_m: float | None
    exterior_m: float
    ordered_m: float
    #: Smallest stock kit at or above ``ordered_m``; None when none is long enough.
    kit_m: float | None
    #: Field charge beyond the precharge, this set's share of its unit's; None = unread rate.
    field_charge_oz: float | None
    #: Distance from each end to its port pair's midpoint; None when the pair is undeclared.
    head_offset_m: float | None
    outdoor_offset_m: float | None
    ports_exact: bool

    @property
    def leftover_m(self) -> float | None:
        return None if self.kit_m is None else self.kit_m - self.developed_m


def lineset_standard(plan: Any) -> Any | None:
    from typehaus.model.linesets import LinesetStandard

    return next((el for el in plan.all_elements() if isinstance(el, LinesetStandard)), None)


def lineset_section(plan: Any, run: Any) -> tuple[str | None, float]:
    """``(insulation spec, bundle OD m)``: the run's spec, else the standard's."""
    from typehaus.resolve.mep_envelopes import insulation_thickness_m
    from typehaus.resolve.pipe_sections import pipe_outside_diameter_m

    standard = lineset_standard(plan)
    insulation = run.insulation or (standard.insulation if standard else None)
    cable = standard.control_cable_diameter.meters if standard else 0.0
    lagging = insulation_thickness_m(insulation) or 0.0
    vapor = pipe_outside_diameter_m(run.diameter.meters, run.material)
    liquid = pipe_outside_diameter_m(run.liquid_diameter.meters, run.material)
    return insulation, lineset_bundle_diameter_m(vapor, liquid, lagging, cable)


def _pair_point(ports: list, equipment: str, suffix: str) -> tuple[Any, bool] | None:
    pair = [p for p in ports if p.equipment_tag == equipment
            and p.port_tag in (f"liquid{suffix}", f"vapor{suffix}")]
    if len(pair) != 2:
        return None
    mid = tuple(sum(c) / 2.0 for c in zip(pair[0].point, pair[1].point, strict=True))
    return mid, all(p.exact for p in pair)


def _interior_sets(model: Any) -> list[tuple[float, float, Any]]:
    """``(z0, z1, plan polygon)`` per storey: its rooms and wall bodies, over the z its walls
    span (a wall's band reaches down through the floor framing), what is inside."""
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all
    from typehaus.resolve.soffits import wall_footprint

    out = []
    for storey in model.plan.storeys:
        walls = [w for w in model.walls if w.storey == storey.tag]
        if not walls:
            continue
        shapes = [Polygon(r.clear_face) for r in model.rooms
                  if r.storey == storey.tag and len(r.clear_face) >= 3]
        shapes += [wall_footprint(w) for w in walls]
        shapes = [s for s in shapes if not s.is_empty and s.is_valid]
        out.append((min(w.z0_m for w in walls), max(w.z1_m for w in walls), union_all(shapes)))
    return out


def exterior_length_m(run: Any, interior: list) -> float:
    """Developed length of the run whose centreline is outside every storey's envelope."""
    from shapely.geometry import Point

    if not run.z_m:
        return 0.0
    pts = [(*p, z) for p, z in zip(run.path, run.z_m, strict=True)]
    total = 0.0
    for a, b in zip(pts, pts[1:], strict=False):
        seg = math.dist(a, b)
        steps = max(1, math.ceil(seg / _SAMPLE_M))
        for i in range(steps):
            t = (i + 0.5) / steps
            x, y, z = (a[k] + (b[k] - a[k]) * t for k in range(3))
            inside = any(z0 <= z <= z1 and shape.covers(Point(x, y))
                         for z0, z1, shape in interior)
            if not inside:
                total += seg / steps
    return total


def derive_linesets(model: Any) -> None:
    from typehaus.resolve.mep_ports import placed_ports

    runs = [r for r in model.pipe_runs if r.system == "refrigerant"]
    if not runs:
        return
    plan = model.plan
    standard = lineset_standard(plan)
    equipment = {el.tag: el for el in plan.all_elements() if el.element_kind == "Equipment"}
    types = {t.tag: t for t in plan.library.equipment_types}
    ports = placed_ports(model)
    interior = _interior_sets(model)
    loop = standard.service_loop.meters if standard else 0.0
    kits = sorted(k.meters for k in standard.stock_kit_lengths) if standard else []

    # Per outdoor unit: total length, for the charge share.
    def unit_of(run: Any) -> str | None:
        head = equipment.get(run.serves[0]) if run.serves else None
        return getattr(head, "outdoor_ref", None) if head is not None else None

    totals: dict[str, float] = {}
    for run in runs:
        if unit_of(run):
            totals[unit_of(run)] = totals.get(unit_of(run), 0.0) + run.length_m

    for run in runs:
        head_tag = run.serves[0] if run.serves else None
        od_tag = unit_of(run)
        suffix = f"-{run.outdoor_port}" if run.outdoor_port else ""
        head_pair = _pair_point(ports, head_tag, "") if head_tag else None
        od_pair = _pair_point(ports, od_tag, suffix) if od_tag else None
        ends = [(*run.path[0], run.z_m[0]), (*run.path[-1], run.z_m[-1])] if run.z_m else []
        od_end = head_end = None
        if ends and od_pair is not None:
            od_end = min(ends, key=lambda e: math.dist(e, od_pair[0]))
            head_end = ends[1] if od_end is ends[0] else ends[0]
        elif ends and head_pair is not None:
            head_end = min(ends, key=lambda e: math.dist(e, head_pair[0]))
            od_end = ends[1] if head_end is ends[0] else ends[0]
        rise = od_end[2] - head_end[2] if od_end and head_end else None
        ordered = run.length_m + loop
        kit = next((k for k in kits if k >= ordered - 1e-6), None)
        limits = getattr(types.get(getattr(equipment.get(od_tag), "type_ref", None)),
                         "refrigerant_limits", None) if od_tag else None
        charge = _field_charge(limits, run.length_m, totals.get(od_tag or "", 0.0))
        model.linesets.append(ResolvedLineset(
            tag=run.tag, head_tag=head_tag, outdoor_tag=od_tag, port=run.outdoor_port,
            liquid_m=run.liquid_diameter_m or 0.0, vapor_m=run.diameter_m,
            developed_m=run.length_m, rise_m=rise,
            exterior_m=exterior_length_m(run, interior), ordered_m=ordered, kit_m=kit,
            field_charge_oz=charge,
            head_offset_m=math.dist(head_end, head_pair[0]) if head_pair and head_end else None,
            outdoor_offset_m=math.dist(od_end, od_pair[0]) if od_pair and od_end else None,
            ports_exact=bool(head_pair and od_pair and head_pair[1] and od_pair[1])))


def _field_charge(limits: Any, length_m: float, unit_total_m: float) -> float | None:
    """This set's share of its unit's charge beyond the precharge, oz."""
    if limits is None or limits.precharged_length is None or unit_total_m <= 0:
        return None
    excess_ft = max(0.0, unit_total_m - limits.precharged_length.meters) / 0.3048
    if excess_ft == 0.0:
        return 0.0
    if limits.charge_oz_per_ft is None:
        return None
    return excess_ft * limits.charge_oz_per_ft * length_m / unit_total_m
