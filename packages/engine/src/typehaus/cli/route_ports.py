"""Leave an EXACT equipment port along its declared direction (docs/routing.md).

``ServicePort.direction`` says which way the water or air leaves the machine. A route that
starts there with a sideways leg is one no fitting makes, so the terminal moves to the end of
a short straight stub along that axis, the search runs from the stub's end, and the stub is
put back on the found path. Approximate ports and runs ending on a line (a tee) are left alone.

A duct port whose equipment type has a ``PortKit`` gets the kit's lead instead of the stub:
transition (where the duct is not the port's size) plus flex, laid straight
(``routing/duct_fittings.kit_lead``, duct basis §8).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_ports import placed_ports

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.cli.route_support import Endpoints

Point3 = tuple[float, float, float]

#: Stub = one pipe/duct outside diameter (insulation included) + this allowance. The diameter
#: seats the fitting's hub or collar and the allowance is the socket/clamp bite, so the first
#: turn is a real elbow instead of a bend at the port face. No published laying length exists
#: for these parts (docs/routing.md), so this is a stated allowance, not a datasheet value.
STUB_ALLOWANCE_IN = 2.0
#: A direction counts as axis-aligned within 15 degrees (cos 15 = 0.966); the lattice is
#: orthogonal, so an oblique port stays a plain terminal rather than being snapped wrongly.
AXIS_COS_MIN = 0.966
#: Terminal-to-port match, metres: the router already snapped the terminal onto the port.
PORT_MATCH_M = 1e-3


@dataclass(frozen=True)
class PortLead:
    """A port the route must leave along ``direction``; ``tip`` is the search terminal."""

    label: str
    port: Point3
    tip: Point3
    direction: str  # "+x" ... "-z"

    @property
    def inches(self) -> float:
        return sum((a - b) ** 2 for a, b in zip(self.tip, self.port, strict=True)) ** 0.5 / M_PER_IN


def stub_length_m(radius_m: float) -> float:
    """Outside diameter plus :data:`STUB_ALLOWANCE_IN`, on the proposal's 1/16" grid."""
    inches = 2.0 * radius_m / M_PER_IN + STUB_ALLOWANCE_IN
    return -(-inches * 16.0 // 1.0) / 16.0 * M_PER_IN


def _axis(direction: tuple[float, float, float]) -> tuple[int, int] | None:
    """``(axis index, sign)`` of the dominant component, or None when oblique."""
    norm = sum(c * c for c in direction) ** 0.5
    if norm == 0.0:
        return None
    axis = max(range(3), key=lambda i: abs(direction[i]))
    if abs(direction[axis]) / norm < AXIS_COS_MIN:
        return None
    return axis, 1 if direction[axis] > 0 else -1


def _matches(port: Any, ends: Any, point: Point3) -> bool:
    if (abs(port.x_m - point[0]) > PORT_MATCH_M or abs(port.y_m - point[1]) > PORT_MATCH_M
            or abs(port.z_m - point[2]) > PORT_MATCH_M):
        return False
    system = getattr(ends.system, "value", ends.system)
    if ends.kind == "duct":
        return port.duct_system in (None, system)
    return bool(system) and port.service == system


def with_port_leads(model: Any, ends: Endpoints | None) -> Endpoints | None:
    """``ends`` with each exact, directed port terminal moved to its stub's tip.

    Gravity runs are untouched (their invert is derived, and a fixture drain has no
    ``ServicePort``), as is a root that is a line to tee onto."""
    if ends is None or ends.falls:
        return ends
    ports = [p for p in placed_ports(model) if p.exact and p.direction is not None]
    if not ports:
        return ends
    stub = stub_length_m(ends.radius_m)
    kits = _kit_reader(model, ends)
    changes: dict[str, Any] = {}
    notes: list[str] = []
    for side in ("origin", "root"):
        point: Point3 = getattr(ends, side)
        if side == "root" and ends.root_paths:
            continue
        port = next((p for p in ports if _matches(p, ends, point)), None)
        if port is None:
            continue
        found = _axis(port.direction)
        label = f"{port.equipment_tag}.{port.port_tag}"
        if found is None:
            notes.append(f"{label}: direction is not along an axis, so the route may "
                         "leave it any way the search finds")
            continue
        axis, sign = found
        length = stub
        lead = kits(port) if kits is not None else None
        if lead is not None:
            length = max(stub, lead.length_m)  # an unread kit is no shorter than the stub
            notes.append(f'{label}: the port kit\'s {length / M_PER_IN:.3f}" lead is laid straight '
                         "before the first rigid fitting"
                         + "".join(f"; {gap}" for gap in lead.unread))
        tip = tuple(c + sign * length if i == axis else c for i, c in enumerate(point))
        changes[side] = tip
        changes[f"{side}_lead"] = PortLead(label, point, tip, f"{'+' if sign > 0 else '-'}"
                                                              f"{'xyz'[axis]}")
    if notes:
        changes["advice"] = (*ends.advice, *notes)
    return replace(ends, **changes) if changes else ends


def _kit_reader(model: Any, ends: Endpoints):
    """``port -> KitLead | None`` off the house's ``DuctStandard``; None for a non-duct."""
    if ends.kind != "duct" or not hasattr(model, "canvas_objects"):
        return None
    from typehaus.resolve.duct_standard import duct_standard
    from typehaus.routing.duct_fittings import kit_lead

    standard, _ = duct_standard(getattr(model, "plan", None))
    if standard is None:
        return None
    types = {o.tag: o.type_ref for o in model.canvas_objects}
    size = ends.diameter_m or max(ends.width_m, ends.depth_m)

    def read(port: Any):
        kit = standard.port_kit(types.get(port.equipment_tag), port.port_tag)
        differs = port.section_m is None or abs(port.section_m[0] - size) > 1e-6
        return kit_lead(kit, needs_transition=differs)

    return read


def terminal_refusal(space: Any, ends: Endpoints,
                     band: tuple[float, float] | None) -> str | None:
    """Why the terminals cannot be searched, or None: outside the ``--level`` band, or a
    port lead running into something other than its own machine."""
    if band is not None and not any(band[0] - 1e-9 <= p[2] <= band[1] + 1e-9
                                    for p in (ends.origin, ends.root)):
        return ("neither of its ends stands inside the --level band, so restricting the "
                "search to that storey asks for a route that cannot reach where it is told")
    return _lead_overshoot(ends) or _lead_blocked(space, ends)


def _lead_overshoot(ends: Endpoints) -> str | None:
    """The refusal when the run's other end stands on its lead, short of the tip: the run
    cannot hold the straight its port needs (duct basis §8)."""
    for lead, other in ((ends.origin_lead, ends.root), (ends.root_lead, ends.origin)):
        if lead is None:
            continue
        along = [t - p for t, p in zip(lead.tip, lead.port, strict=True)]
        span = sum(a * a for a in along) ** 0.5
        if span == 0.0:
            continue
        rel = [o - p for o, p in zip(other, lead.port, strict=True)]
        reach = sum(a * r for a, r in zip(along, rel, strict=True)) / span
        off = max(0.0, sum(r * r for r in rel) - reach * reach) ** 0.5  # plumb: may dip < 0
        if 0.0 <= reach < span - 1e-9 and off <= ends.radius_m:
            return (f'{lead.label} is an exact port facing {lead.direction}; the '
                    f'{lead.inches:.3f}" straight lead it needs before the first fitting is '
                    f'longer than the {reach / M_PER_IN:.3f}" to the run\'s other end, short '
                    f'by {(span - reach) / M_PER_IN:.3f}". Move the machine or the far end')
    return None


def _lead_blocked(space: Any, ends: Endpoints) -> str | None:
    """The refusal sentence when a stub hits something other than its own machine."""
    for lead in (ends.origin_lead, ends.root_lead):
        if lead is None:
            continue
        own = space.blocked_all(lead.port[:2], lead.port[2])
        hit = (set(space.blocked_all(lead.tip[:2], lead.tip[2])) - own
               or space.edge_blocked(lead.port[:2], lead.tip[:2], lead.port[2],
                                     lead.tip[2], ignore=own))
        if hit:
            what = hit if isinstance(hit, str) else ", ".join(sorted(hit))
            return (f"{lead.label} is an exact port facing {lead.direction}; the "
                    f'{lead.inches:.2f}" straight lead it needs before the first '
                    f"turn runs into {what}. Move the obstruction or the machine, or mark "
                    "the port approximate")
    return None


def attach_leads(points: list[Point3], ends: Endpoints) -> tuple[list[Point3], list[str], int]:
    """Found path (origin tip -> root tip) with the port points put back on its ends.

    Returns ``(points, notes, extra bends)``; a tip the route continues straight through is
    dropped, so the stub does not leave a collinear vertex."""
    notes: list[str] = []
    bends = 0
    for side, lead in (("origin", ends.origin_lead), ("root", ends.root_lead)):
        if lead is None or len(points) < 2:
            continue
        ordered = points if side == "origin" else points[::-1]
        straight = _collinear(lead.port, ordered[0], ordered[1])
        ordered = [lead.port, *(ordered[1:] if straight else ordered)]
        bends += 0 if straight else 1
        points = ordered if side == "origin" else ordered[::-1]
        notes.append(f'port lead: leaves {lead.label} {lead.direction} for '
                     f'{lead.inches:.2f}" before turning (exact port direction)')
    return points, notes, bends


def _collinear(a: Point3, b: Point3, c: Point3) -> bool:
    ab = [y - x for x, y in zip(a, b, strict=True)]
    bc = [y - x for x, y in zip(b, c, strict=True)]
    cross = [ab[1] * bc[2] - ab[2] * bc[1], ab[2] * bc[0] - ab[0] * bc[2],
             ab[0] * bc[1] - ab[1] * bc[0]]
    dot = sum(p * q for p, q in zip(ab, bc, strict=True))
    return all(abs(v) < 1e-9 for v in cross) and dot > 0
