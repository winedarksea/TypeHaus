"""A supply end on a shower assembly's inlet leaves it along the inlet's axis.

``mep.shower_assembly_alignment`` wants the run's last leg to meet the valve's hub outboard on the
hub's outward axis. The assembly's inlets carry a direction but are not "exact" equipment ports,
so ``route_ports.with_port_leads`` skips them; this gives the end the same straight stub.
"""

from __future__ import annotations

from dataclasses import replace
from math import cos, radians, sin
from typing import TYPE_CHECKING

from typehaus.cli.route_ports import PortLead, stub_length_m

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.cli.route_support import Endpoints
    from typehaus.resolve.model import ResolvedModel

_MATCH_M = 1e-3


def with_inlet_lead(model: ResolvedModel, ends: Endpoints | None) -> Endpoints | None:
    """``ends`` with its fixture end moved to the stub tip of a shower inlet it stands on."""
    if ends is None or ends.falls or ends.origin_lead is not None or not ends.serves:
        return ends
    from typehaus.resolve.mep_sleeves import placed_port_point

    types = {t.tag: t for t in model.plan.library.fixture_types}
    datum = {s.tag: s.elevation.meters for s in model.plan.storeys}
    placed = {o.tag: o for o in model.canvas_objects if o.kind == "Fixture"}
    system = getattr(ends.system, "value", ends.system)
    for tag in ends.serves:
        fixture = placed.get(tag)
        authored = next((e for e in model.plan.elements_of_kind("Fixture") if e.tag == tag), None)
        spec = getattr(types.get(getattr(authored, "type_ref", None)), "shower_assembly", None)
        if fixture is None or spec is None:
            continue
        angle = radians(fixture.rotation_degrees)
        for port in spec.inlet_ports():
            local = placed_port_point(model, tag, port)
            if port.service.value != system or local is None:
                continue
            hub = (local[0], local[1], local[2] + datum[fixture.storey])
            if max(abs(a - b) for a, b in zip(hub, ends.origin, strict=True)) > _MATCH_M:
                continue
            dx, dy, _dz = port.direction
            out = (dx * cos(angle) - dy * sin(angle), dx * sin(angle) + dy * cos(angle))
            axis = 0 if abs(out[0]) >= abs(out[1]) else 1
            sign = 1 if out[axis] > 0 else -1
            length = stub_length_m(ends.radius_m)
            at = ends.origin
            tip = tuple(c + sign * length if i == axis else c for i, c in enumerate(at))
            lead = PortLead(f"{tag}.{port.tag}", at, tip, f"{'+' if sign > 0 else '-'}{'xy'[axis]}")
            return replace(ends, origin=tip, origin_lead=lead)
    return ends

