"""NEC 110.26(E)(1) dedicated space over each panel — shared by the check and the router.

The panel's own footprint, floor to 6 ft above its top or the structural ceiling (taken as
the room's clear height), whichever is lower, is reserved for the electrical installation.
``electrical.panel_dedicated_space`` grades a pipe or duct in it; ``routing/obstacles``
makes it hard for both. Conduit is the installation and may enter it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_IN = 0.0254
ABOVE_M = 72 * _IN


@dataclass(frozen=True)
class DedicatedSpace:
    panel: str
    footprint: tuple[tuple[float, float], ...]
    floor_m: float
    z1_m: float


def panels(plan: Any) -> list:
    return sorted((e for e in plan.all_elements()
                   if e.element_kind == "ElectricalDevice" and e.kind.value == "panel"),
                  key=lambda e: e.tag)


def floor_and_top(panel: Any, body: Any) -> tuple[float, float] | None:
    """``(floor under the panel, panel top)``, or None without a mount elevation."""
    elevation = getattr(panel.mount, "elevation", None)
    if elevation is None or body.body_z0_m is None or body.body_z1_m is None:
        return None
    return body.body_z0_m - elevation.meters, body.body_z1_m


def dedicated_spaces(model: Any) -> dict[str, DedicatedSpace | None]:
    """Panel tag -> its dedicated space; None where no body or mount places one."""
    bodies = {item.tag: item for item in model.canvas_objects}
    rooms = {room.tag: room for room in model.rooms}
    out: dict[str, DedicatedSpace | None] = {}
    for panel in panels(model.plan):
        body = bodies.get(panel.tag)
        band = None if body is None else floor_and_top(panel, body)
        if body is None or band is None or len(body.footprint) < 3:
            out[panel.tag] = None
            continue
        floor, top = band
        room = rooms.get(body.room or "")
        z1 = top + ABOVE_M
        if room is not None and room.clear_height_m is not None:
            z1 = min(z1, floor + room.clear_height_m)
        out[panel.tag] = DedicatedSpace(panel.tag, tuple(body.footprint), floor, z1)
    return out
