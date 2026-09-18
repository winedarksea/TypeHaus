"""Where a machine's declared connections actually are, in project coordinates.

A :class:`~typehaus.model.placeables.ServicePort` is a **product** fact: a station, a
direction and a section in the product's own frame, stated once on an ``EquipmentType`` and
shared by every placement of it. Turning that into "the supply spigot of EQ-B-ERV is at
(31.4', 12.9', 7.1') pointing up, 6" round" needs the placement's rotation and its resolved
base, and three callers wanted it:

* ``mep.equipment_port_service``, to grade a dimensioned port where it is rather than
  dropping to "something of the right service reached the case";
* ``cli/route_support``, so a duct re-route **terminates on the port** instead of on the
  authored end that happens to sit somewhere inside the case — a foot of slop at a spigot is
  the difference between a proposal an installer can build and one they have to re-aim;
* the evaluation report, which has to say which connections are exact and which are not.

So the transform lives here, once. ``rotate_into_plan`` is the same one the plan symbols and
the drain-drop resolver use, which is the point: a port drawn in one place and routed to in
another would be two readings of one product.

**Certainty is carried, never inferred.** A port with no ``direction`` and a default
``PortCertainty.APPROXIMATE`` is reported as approximate even where its coordinates look
specific, because four ports at ``(0, 0, 21.6")`` have specific-looking coordinates too and
that is exactly the authoring this field exists to tell apart.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.model.placeables import ServicePort
    from typehaus.resolve.model import ResolvedModel


@dataclass(frozen=True)
class PlacedPort:
    """One declared connection, placed. ``direction`` is in the PROJECT frame."""

    equipment_tag: str
    port_tag: str
    #: ``Service`` value, e.g. ``"supply_air"``.
    service: str
    #: The ``DuctSystem`` value a run must carry to connect, or None for a non-air service.
    duct_system: str | None
    x_m: float
    y_m: float
    z_m: float
    exact: bool
    direction: tuple[float, float, float] | None = None
    #: ``(width, depth)`` in metres; equal for a round spigot. None when unstated.
    section_m: tuple[float, float] | None = None

    @property
    def point(self) -> tuple[float, float, float]:
        return self.x_m, self.y_m, self.z_m

    def radius_m(self) -> float | None:
        """Half the larger section dimension — what a lattice has to leave clear."""
        return max(self.section_m) / 2.0 if self.section_m else None

    def describe(self) -> str:
        from typehaus.quantities import M_PER_IN
        where = (f"({self.x_m / M_PER_IN / 12:.2f}', {self.y_m / M_PER_IN / 12:.2f}', "
                 f"{self.z_m / M_PER_IN / 12:.2f}')")
        section = (f', {self.section_m[0] / M_PER_IN:.3g}x'
                   f'{self.section_m[1] / M_PER_IN:.3g}"' if self.section_m else "")
        return (f"{self.equipment_tag}.{self.port_tag} [{self.service}] at {where}"
                f"{section} ({'exact' if self.exact else 'approximate'})")


def placed_ports(model: ResolvedModel) -> list[PlacedPort]:
    """Every ``ServicePort`` of every placed ``Equipment``, in project coordinates.

    Equipment whose type is unknown, or which never resolved to a canvas object, is skipped
    rather than reported: this is a reading, and "that machine did not resolve" is a verdict
    somebody else already gives.
    """
    from typehaus.model.enums import AIR_SERVICE_DUCT_SYSTEM
    from typehaus.resolve.mep_sleeves import rotate_into_plan

    plan = getattr(model, "plan", None)
    if plan is None:
        return []
    types = {entry.tag: entry for entry in plan.library.equipment_types}
    objects = {obj.tag: obj for obj in model.canvas_objects}

    out: list[PlacedPort] = []
    for element in plan.all_elements():
        if element.element_kind != "Equipment":
            continue
        machine = types.get(getattr(element, "type_ref", None) or "")
        obj = objects.get(element.tag)
        if machine is None or obj is None:
            continue
        for port in machine.ports:
            x, y = rotate_into_plan(element, (port.position[0].meters,
                                              port.position[1].meters))
            system = AIR_SERVICE_DUCT_SYSTEM.get(port.service)
            out.append(PlacedPort(
                equipment_tag=element.tag, port_tag=port.tag,
                service=port.service.value, duct_system=system.value if system else None,
                x_m=x, y_m=y, z_m=obj.z_m + port.position[2].meters,
                exact=_is_exact(port),
                direction=_direction_in_plan(element, port),
                section_m=_section_m(port)))
    return out


def port_at(model: ResolvedModel, point: tuple[float, float],
            z_m: float | None, *, duct_system: str | None,
            tolerance_m: float) -> PlacedPort | None:
    """The EXACT port a run end is landing on, or None.

    Only exact ports are offered: snapping a terminal to an approximate one would move the
    run to a coordinate the datasheet never gave, which is worse than leaving it where its
    author put it. Nearest wins, and the system must match where the port states one.
    """
    best: tuple[float, PlacedPort] | None = None
    for port in placed_ports(model):
        if not port.exact:
            continue
        if duct_system is not None and port.duct_system not in (None, duct_system):
            continue
        plan_off = max(abs(port.x_m - point[0]), abs(port.y_m - point[1]))
        z_off = 0.0 if z_m is None else abs(port.z_m - z_m)
        if plan_off > tolerance_m or z_off > tolerance_m:
            continue
        score = plan_off + z_off
        if best is None or score < best[0]:
            best = (score, port)
    return None if best is None else best[1]


def _is_exact(port: ServicePort) -> bool:
    checker = getattr(port, "is_exact", None)
    return bool(checker()) if callable(checker) else False


def _section_m(port: ServicePort) -> tuple[float, float] | None:
    reader = getattr(port, "section_m", None)
    return reader() if callable(reader) else None


def _direction_in_plan(element: Any, port: ServicePort
                       ) -> tuple[float, float, float] | None:
    """The port's outlet vector, rotated into the project frame.

    Rotated as a direction, not as a point: ``rotate_into_plan`` places a *station* and so
    carries the placement's translation with it, and adding a translation to a unit vector
    is how a router ends up aiming a spigot at the origin. The vector is recovered as the
    difference of two placed points, which is the translation-free part of exactly that
    transform, and z is untouched because a placement's rotation is about the vertical.
    """
    from typehaus.resolve.mep_sleeves import rotate_into_plan

    if port.direction is None:
        return None
    dx, dy, dz = (float(v) for v in port.direction)
    ox, oy = rotate_into_plan(element, (0.0, 0.0))
    px, py = rotate_into_plan(element, (dx, dy))
    return px - ox, py - oy, dz
