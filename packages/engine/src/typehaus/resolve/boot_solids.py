"""A register boot's solid, shaped by how its run meets the terminal (decision #136).

The record's ``joint``/``face``/``turn`` (``resolve/terminal_joints``) pick the shape:

* straight (end, drop, inlet): a loft from the run's section to the face section, at least
  the boot's length behind the face; the run's tip inside that length is trimmed.
* 90 end: a box of the face section carried back along the normal past the run's far side,
  and a collar of the run section from the box wall out along the run.
* side: a box behind the face, a collar down to the trunk's surface and a thin flange on it.

No face found: the old plain loft toward the terminal. ``boot_inlet_point`` is where the
run's section meets the boot, for trimming the run's sweep.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import combine_meshes
from typehaus.resolve.duct_mesh import (
    _FACETS,
    Section,
    _add,
    _box,
    _dot,
    _ring,
    _unit,
    loft,
    parse_section,
    prism,
)
from typehaus.resolve.geometry_ir import GMesh, Vec3
from typehaus.resolve.sweep import leg_frame

COLLAR_LENGTH_M = 2.0 * M_PER_IN
#: The flange's oversize past the side collar, each way, and its sheet thickness.
FLANGE_LAP_M, FLANGE_T_M = 0.5 * M_PER_IN, M_PER_IN / 32.0
#: The least box depth behind a side boot's face.
MIN_BOX_M = 0.5 * M_PER_IN


def _half_along(section: Section, run_axis: Vec3, d: Vec3) -> float:
    """The run section's half extent along ``d`` (perpendicular to the run)."""
    if section.is_round:
        return section.width / 2.0
    right, up = leg_frame(run_axis)
    return (abs(_dot(d, right)) * section.width + abs(_dot(d, up)) * section.depth) / 2.0


def _face_half(face: Any, d: Vec3) -> float:
    return (abs(_dot(d, face.width_axis)) * face.width_m
            + abs(_dot(d, face.height_axis)) * face.height_m) / 2.0


def _straight(part: Any, size: Section, face: Any, point: Vec3, axis: Vec3
              ) -> tuple[GMesh, Vec3]:
    n, c = face.normal, face.centre
    along = _dot(tuple(point[i] - c[i] for i in range(3)), n)
    length = max(part.length_m or size.larger, along)
    k = _dot(axis, n)
    run = axis if k > 0.5 else n  # a straight end leaves within 45 degrees of the normal
    start = _add(point, run, (length - along) / max(k, 0.5) if run is axis else length - along)
    w, h = face.width_axis, face.height_axis
    duct = size
    if not size.is_round:  # the run's width lies along whichever face axis its right does
        right, _ = leg_frame(run)
        if abs(_dot(right, w)) < abs(_dot(right, h)):
            duct = Section(False, size.depth, size.width)
    mouth = Section(False, face.width_m, face.height_m)
    count = 4 if not size.is_round else _FACETS
    return prism(_ring(duct, start, w, h, count), _ring(mouth, c, w, h, count)), start


def _end_90(size: Section, face: Any, point: Vec3, axis: Vec3) -> tuple[GMesh, Vec3]:
    n, c = face.normal, face.centre
    rel = tuple(point[i] - c[i] for i in range(3))
    along, half = _dot(rel, n), _half_along(size, axis, n)
    deep = max(along + half, MIN_BOX_M)
    mouth = Section(False, face.width_m, face.height_m)
    w, h = face.width_axis, face.height_axis
    body = prism(_ring(mouth, c, w, h, 4), _ring(mouth, _add(c, n, deep), w, h, 4))
    # Lateral coordinate of the run end along its own axis, against the box's half extent.
    q, e = _dot(rel, axis), _face_half(face, axis)
    wall = _add(point, axis, e - q)
    collar_len = max(q - e, COLLAR_LENGTH_M)
    # A run proud of the face plane keeps its collar behind it (the run's own offset stays).
    collar = loft(_add(wall, n, max(half - along, 0.0)), axis, size, size, collar_len)
    return combine_meshes(body, collar), _add(wall, axis, collar_len)


def _side(size: Section, face: Any, point: Vec3, axis: Vec3) -> tuple[GMesh, Vec3]:
    n, c, w, h = face.normal, face.centre, face.width_axis, face.height_axis
    reach = _half_along(size, axis, n)
    surface = _add(point, n, -reach)  # the trunk's face toward the terminal
    gap = max(_dot(tuple(surface[i] - c[i] for i in range(3)), n), 0.0)
    depth = max(gap - COLLAR_LENGTH_M, gap / 2.0, MIN_BOX_M)
    mouth = Section(False, face.width_m, face.height_m)
    parts = [prism(_ring(mouth, c, w, h, 4), _ring(mouth, _add(c, n, depth), w, h, 4))]
    # The collar: the face's extent along the trunk, inside the trunk's width across it.
    across = _unit((n[1] * axis[2] - n[2] * axis[1], n[2] * axis[0] - n[0] * axis[2],
                    n[0] * axis[1] - n[1] * axis[0])) or w
    span = 2.0 * _face_half(face, axis)
    cross = min(2.0 * _face_half(face, across), 2.0 * _half_along(size, axis, across))
    centre = _add(c, n, depth)
    centre = _add(centre, across, _dot(tuple(surface[i] - centre[i] for i in range(3)), across))
    collar_len = _dot(tuple(surface[i] - centre[i] for i in range(3)), n)
    if collar_len > 1e-3:
        parts.append(_box(_add(centre, n, collar_len / 2.0), (axis, across, n),
                          (span, cross, collar_len)))
    # On the trunk round the collar, never proud of the face (a trunk touching it).
    lift = max(collar_len - FLANGE_T_M / 2.0, FLANGE_T_M / 2.0 - depth)
    flange = _add(centre, n, lift)
    parts.append(_box(flange, (axis, across, n),
                      (span + 2 * FLANGE_LAP_M, cross + 2 * FLANGE_LAP_M, FLANGE_T_M)))
    return combine_meshes(*parts), point


def _shaped(part: Any, size: Section) -> tuple[GMesh, Vec3] | None:
    """(mesh, inlet point), or None for a record with no joint face."""
    kind, face, turn, point = part.joint, part.face, part.turn, part.point
    axis = _unit(part.axis) or (0.0, 0.0, 1.0)
    if face is None or kind is None:
        return None
    if kind == "side":
        return _side(size, face, point, axis)
    if kind == "end" and turn == "90":
        return _end_90(size, face, point, axis)
    return _straight(part, size, face, point, axis)


def boot_inlet_point(part: Any) -> Vec3:
    """Where the run's section meets the boot: the run sweep ends here. A side boot leaves
    its trunk whole (its joint point); a record with no face, its own point."""
    size = parse_section(part.size)
    shaped = _shaped(part, size) if size is not None else None
    return shaped[1] if shaped is not None else part.point


def _plain_boot(model: Any, part: Any, size: Section, neck: Section | None) -> GMesh:
    """A boot onto a terminal with no face found: lofted toward the terminal."""
    target = next((o for o in model.canvas_objects if o.tag == part.other), None)
    if part.width_m and part.height_m:
        neck = Section(False, part.width_m, part.height_m)
    neck = neck or size
    direction, reach = (0.0, 0.0, 1.0), None
    if target is not None:
        z = target.body_z0_m if target.body_z0_m is not None else part.point[2]
        to = (target.position[0] - part.point[0], target.position[1] - part.point[1],
              z - part.point[2])
        direction = _unit(to) or direction
        reach = math.sqrt(sum(c * c for c in to))
    length = part.length_m or max(size.larger, neck.larger)
    if part.length_m is None and reach:
        length = min(length, reach)
    return loft(part.point, direction, size, neck, length)


def boot_mesh(model: Any, part: Any, size: Section, neck: Section | None) -> GMesh | None:
    """The boot's solid (see the module docstring)."""
    shaped = _shaped(part, size)
    return shaped[0] if shaped is not None else _plain_boot(model, part, size, neck)
