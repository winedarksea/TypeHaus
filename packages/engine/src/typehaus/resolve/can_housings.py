"""A recessed ceiling can's housing as a body, shared by the check and the router.

``electrical.ceiling_can_framing`` grades the housing (the type's footprint, ``body_z0_m`` to
``body_z1_m`` above the ceiling plane) against framing, ducts and pipes; ``routing/obstacles``
makes it hard for both so a proposal does not land in one.
"""

from __future__ import annotations

from typing import Any


def can_tags(plan: Any) -> list[str]:
    """Tags of every recessed ceiling luminaire."""
    return [e.tag for e in plan.all_elements()
            if e.element_kind == "ElectricalDevice"
            and e.mount is not None and e.mount.kind.value == "ceiling"
            and e.mount.recessed_into_host_surface]


def can_housings(model: Any) -> list[tuple[str, tuple[tuple[float, float], ...], float, float]]:
    """``(tag, footprint ring, z0, z1)`` of each can whose body is resolved."""
    bodies = {item.tag: item for item in model.canvas_objects}
    out = []
    for tag in can_tags(model.plan):
        body = bodies.get(tag)
        if (body is None or body.body_z0_m is None or body.body_z1_m is None
                or len(body.footprint) < 3):
            continue
        out.append((tag, tuple(body.footprint), body.body_z0_m, body.body_z1_m))
    return out
