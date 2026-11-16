"""Where a duct meets an air terminal: the terminal's duct-side face, in world space.

``neck_back`` is a neck box's back face (moved here from ``duct_part_solids``).
``terminal_face`` generalises it to every terminal ``terminal_joints`` classifies: a neck
box's back, else a components neck's duct-receiving box top, else the face body's back.
``room_offset_m`` reaches from that face back along ``-normal`` to the face the room sees,
so "past the grille into the room" is a plane test.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class TerminalFace:
    """A terminal's duct-side face: ``centre``, unit ``normal`` toward the duct, the
    ``width_axis``/``height_axis`` it spans (``width_m`` x ``height_m``), and the depth
    ``room_offset_m`` from it to the room face. ``source``: ``neck`` / ``component`` /
    ``face`` (no neck: the face body's back) / ``inlet`` (a dimensioned inlet)."""

    centre: Vec3
    normal: Vec3
    width_axis: Vec3
    height_axis: Vec3
    width_m: float
    height_m: float
    room_offset_m: float
    source: str


def _kind(obj: Any) -> str | None:
    return getattr(obj.mount.kind, "value", obj.mount.kind) if obj.mount else None


def wall_back(model: Any, obj: Any, toward: Vec3 | None = None) -> tuple[float, float] | None:
    """The plan direction into a wall terminal's host (``terminal_necks._back``); when no host
    is found, the side ``toward`` (the named run) lies on, else None."""
    from typehaus.resolve.terminal_necks import _back, _rotate

    axis = _rotate((0.0, 1.0), obj.rotation_degrees)
    back = _back(model, obj, axis)
    if back is not None or toward is None:
        return back
    side = (toward[0] - obj.position[0]) * axis[0] + (toward[1] - obj.position[1]) * axis[1]
    if abs(side) < 1e-9:
        return None
    return (axis[0], axis[1]) if side > 0 else (-axis[0], -axis[1])


def neck_back(model: Any, obj: Any, neck: Any, toward: Vec3 | None = None
              ) -> tuple[Vec3, Vec3, Vec3, Vec3] | None:
    """A neck box's back face: (centre, normal toward the duct, width axis, height axis)."""
    from typehaus.resolve.terminal_necks import _face_offset, _rotate

    kind = _kind(obj)
    if obj.body_z0_m is None or kind is None:
        return None
    across = (*_rotate((1.0, 0.0), obj.rotation_degrees), 0.0)
    depth = neck.depth.meters
    top = obj.body_z1_m if obj.body_z1_m is not None else obj.body_z0_m
    if kind in ("ceiling", "floor"):
        other = (*_rotate((0.0, 1.0), obj.rotation_degrees), 0.0)
        if kind == "ceiling":
            return (*obj.position, obj.body_z0_m + depth), (0.0, 0.0, 1.0), across, other
        return (*obj.position, top - depth), (0.0, 0.0, -1.0), across, other
    back = wall_back(model, obj, toward)
    if back is None:
        return None
    reach = _face_offset(obj, back) + depth
    centre = (obj.position[0] + back[0] * reach, obj.position[1] + back[1] * reach,
              (obj.body_z0_m + top) / 2.0)
    return centre, (back[0], back[1], 0.0), across, (0.0, 0.0, 1.0)


def terminal_face(model: Any, obj: Any, register_type: Any, toward: Vec3 | None = None
                  ) -> TerminalFace | None:
    """The duct-side face of a placed terminal, or None when it cannot be placed.

    ``toward`` (a point on the named run) orients a wall terminal no host is found behind.
    """
    kind = _kind(obj)
    if obj.body_z0_m is None or kind not in ("wall", "ceiling", "floor"):
        return None
    neck = getattr(register_type, "neck", None)
    if neck is not None and neck.components and kind == "ceiling":
        return _component_face(obj, neck)
    if neck is not None:
        placed = neck_back(model, obj, neck, toward)
        if placed is None:
            return None
        centre, normal, across, up = placed
        # A wall neck starts behind the body; a ceiling or floor neck starts at the face.
        body = 0.0
        if kind == "wall":
            from typehaus.resolve.terminal_necks import _face_offset

            body = 2.0 * _face_offset(obj, normal[:2])
        return TerminalFace(centre, normal, across, up, neck.width.meters, neck.height.meters,
                            neck.depth.meters + body, "neck")
    if register_type is None or obj.body_z1_m is None:
        return None
    from typehaus.resolve.terminal_necks import _face_offset, _rotate

    width = register_type.footprint[0].meters
    across = (*_rotate((1.0, 0.0), obj.rotation_degrees), 0.0)
    if kind == "wall":
        back = wall_back(model, obj, toward)
        if back is None:
            return None
        reach = _face_offset(obj, back)
        centre = (obj.position[0] + back[0] * reach, obj.position[1] + back[1] * reach,
                  (obj.body_z0_m + obj.body_z1_m) / 2.0)
        return TerminalFace(centre, (back[0], back[1], 0.0), across, (0.0, 0.0, 1.0), width,
                            register_type.height.meters, 2.0 * reach, "face")
    other = (*_rotate((0.0, 1.0), obj.rotation_degrees), 0.0)
    depth = obj.body_z1_m - obj.body_z0_m
    if kind == "ceiling":
        return TerminalFace((*obj.position, obj.body_z1_m), (0.0, 0.0, 1.0), across, other,
                            width, register_type.footprint[1].meters, depth, "face")
    return TerminalFace((*obj.position, obj.body_z0_m), (0.0, 0.0, -1.0), across, other,
                        width, register_type.footprint[1].meters, depth, "face")


def _component_face(obj: Any, neck: Any) -> TerminalFace | None:
    """A ceiling assembly: the top of the component that receives the duct."""
    from typehaus.resolve.terminal_necks import _rotate

    parts = [c for c in neck.components if not c.clearance_only]
    part = next((c for c in parts if c.receives_duct), parts[0] if parts else None)
    if part is None:
        return None
    dx, dy = _rotate(tuple(v.meters for v in part.offset[:2]), obj.rotation_degrees)
    top = part.offset[2].meters + part.depth.meters
    across = (*_rotate((1.0, 0.0), obj.rotation_degrees), 0.0)
    other = (*_rotate((0.0, 1.0), obj.rotation_degrees), 0.0)
    return TerminalFace((obj.position[0] + dx, obj.position[1] + dy, obj.body_z0_m + top),
                        (0.0, 0.0, 1.0), across, other, part.width.meters,
                        part.height.meters, top, "component")


def inlet_face(model: Any, tag: str) -> TerminalFace | None:
    """A dimensioned inlet (``end_terminal_ref``) as a face; ``room_offset_m`` is 0."""
    from typehaus.resolve.terminal_necks import terminal_inlet

    placed = terminal_inlet(model, tag)
    if placed is None:
        return None
    centre, normal, width, height = placed
    n = (normal[0], normal[1], normal[2] if len(normal) > 2 else 0.0)
    across = (-n[1], n[0], 0.0) if abs(n[2]) < 0.99 else (1.0, 0.0, 0.0)
    up = (n[1] * across[2] - n[2] * across[1], n[2] * across[0] - n[0] * across[2],
          n[0] * across[1] - n[1] * across[0])
    return TerminalFace(tuple(centre), n, across, up, width, height, 0.0, "inlet")
