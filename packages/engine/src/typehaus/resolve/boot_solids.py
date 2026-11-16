"""A register boot's solid, shaped by its entry and its catalog envelope (decision #136).

The entry is the record's ``entry`` (straight / end / side / trunk) when set, else read off
its ``joint``/``turn`` (``resolve/terminal_joints``):

* ``straight`` (a straight end, drop or inlet): a loft from the run's section to the face
  section, at least the boot's depth behind the face; the run's tip inside it is trimmed.
* ``end`` / ``side`` (a 90 at the run's end): a box behind the face, past the run's far
  side, with a collar of the run's section from the box wall out along the run: into the
  box's short end or its long side, whichever the run arrives at. A run lying partly in a
  plain neck's own depth (no damper: the neck is the boot) keeps its line: the collar
  enters the neck's side
  (``neck_side_joint``, cut by ``neck_solids.joint_necks``), the box only past its back.
* ``trunk`` (a side joint): a box behind the face, a collar down to the trunk's surface and a
  thin flange on it.

The envelope is the boot row's (``ResolvedDuctPart.length_m``/``width_m``/``height_m``) when
it states one: ``length`` x ``width`` the box along the face's longer x shorter axis and
``height`` its depth behind the face (a straight boot's reach; a row stating only ``length``
keeps the older reading, its reach). Unstated: the face section, the depth derived.

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
#: A run end this far in front of a neck's back is still behind it.
NECK_PLANE_M = M_PER_IN / 16.0


def _half_along(section: Section, run_axis: Vec3, d: Vec3) -> float:
    """The run section's half extent along ``d`` (perpendicular to the run)."""
    if section.is_round:
        return section.width / 2.0
    right, up = leg_frame(run_axis)
    return (abs(_dot(d, right)) * section.width + abs(_dot(d, up)) * section.depth) / 2.0


class _Box:
    """The boot body behind the face: ``w`` along ``wa``, ``h`` along ``ha``, ``depth``
    (None: derived) along the face normal."""

    def __init__(self, part: Any, face: Any) -> None:
        self.wa, self.ha = face.width_axis, face.height_axis
        self.w, self.h = face.width_m, face.height_m
        self.depth = getattr(part, "height_m", None)
        sides = [v for v in (getattr(part, "length_m", None), getattr(part, "width_m", None))
                 if v]
        if len(sides) == 2:  # the longer side along the face's longer axis
            big, small = max(sides), min(sides)
            self.w, self.h = (big, small) if face.width_m >= face.height_m else (small, big)

    def half(self, d: Vec3) -> float:
        return (abs(_dot(d, self.wa)) * self.w + abs(_dot(d, self.ha)) * self.h) / 2.0

    def mesh(self, c: Vec3, n: Vec3, deep: float) -> GMesh:
        mouth = Section(False, self.w, self.h)
        return prism(_ring(mouth, c, self.wa, self.ha, 4),
                     _ring(mouth, _add(c, n, deep), self.wa, self.ha, 4))


def _reach(part: Any) -> float | None:
    """A straight boot's stated depth: ``height``, else a lone ``length`` (the older row)."""
    if getattr(part, "height_m", None):
        return part.height_m
    if part.length_m and not getattr(part, "width_m", None):
        return part.length_m
    return None


def _straight(part: Any, size: Section, face: Any, point: Vec3, axis: Vec3
              ) -> tuple[GMesh, Vec3]:
    n, c = face.normal, face.centre
    along = _dot(tuple(point[i] - c[i] for i in range(3)), n)
    length = max(_reach(part) or size.larger, along)
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


def _into_neck(face: Any, along: float, half: float) -> bool:
    """The run lies partly in a neck box's own depth: its collar enters the neck's side."""
    return face.source == "neck" and along - half < -NECK_PLANE_M


def _end_90(part: Any, size: Section, face: Any, point: Vec3, axis: Vec3,
            plain_neck: bool = False) -> tuple[GMesh, Vec3]:
    n, c = face.normal, face.centre
    rel = tuple(point[i] - c[i] for i in range(3))
    along, half = _dot(rel, n), _half_along(size, axis, n)
    box = _Box(part, face)
    into = plain_neck and _into_neck(face, along, half)
    parts = []
    if not into or along + half > MIN_BOX_M:  # a box behind the neck only past its back
        parts.append(box.mesh(c, n, box.depth or max(along + half, MIN_BOX_M)))
    # Lateral coordinate of the run end along its own axis, against the box's half extent:
    # the collar enters the short end or the long side, whichever the run comes in at.
    q, e = _dot(rel, axis), box.half(axis)
    wall = _add(point, axis, e - q)
    collar_len = max(q - e, COLLAR_LENGTH_M)
    # A run proud of a face plane keeps its collar behind it (the run's own offset stays);
    # one in a neck's depth keeps its own line, through the neck's cut side.
    shift = 0.0 if into else max(half - along, 0.0)
    parts.append(loft(_add(wall, n, shift), axis, size, size, collar_len))
    return combine_meshes(*parts), _add(wall, axis, collar_len)


def neck_side_joint(part: Any) -> tuple[Vec3, Vec3, Section, bool] | None:
    """For a 90 boot onto a plain neck (``neck_solids.boot_drawn``) whose run lies in the
    neck's depth: (collar centre on the neck wall, the run's axis, its section, whether a box
    is drawn behind the neck), else None."""
    size = parse_section(part.size)
    if size is None or boot_entry(part) not in ("end", "side"):
        return None
    face, point = part.face, part.point
    axis = _unit(part.axis) or (0.0, 0.0, 1.0)
    rel = tuple(point[i] - face.centre[i] for i in range(3))
    along, half = _dot(rel, face.normal), _half_along(size, axis, face.normal)
    if not _into_neck(face, along, half):
        return None
    e = _Box(part, face).half(axis)
    return (_add(point, axis, e - _dot(rel, axis)), axis, size, along + half > MIN_BOX_M)


def _side(part: Any, size: Section, face: Any, point: Vec3, axis: Vec3
          ) -> tuple[GMesh, Vec3]:
    n, c = face.normal, face.centre
    reach = _half_along(size, axis, n)
    surface = _add(point, n, -reach)  # the trunk's face toward the terminal
    gap = max(_dot(tuple(surface[i] - c[i] for i in range(3)), n), 0.0)
    box = _Box(part, face)
    depth = (min(box.depth, max(gap, MIN_BOX_M)) if box.depth
             else max(gap - COLLAR_LENGTH_M, gap / 2.0, MIN_BOX_M))
    parts = [box.mesh(c, n, depth)]
    # The collar: the box's extent along the trunk, inside the trunk's width across it.
    across = _unit((n[1] * axis[2] - n[2] * axis[1], n[2] * axis[0] - n[0] * axis[2],
                    n[0] * axis[1] - n[1] * axis[0])) or face.width_axis
    span = 2.0 * box.half(axis)
    cross = min(2.0 * box.half(across), 2.0 * _half_along(size, axis, across))
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


def boot_entry(part: Any) -> str | None:
    """The boot's entry: the record's, else read off its joint (None: no joint face)."""
    if part.face is None or part.joint is None:
        return None
    if part.joint == "side":  # only a trunk has the surface a side boot's flange sits on
        return "trunk"
    entry = getattr(part, "entry", None)
    if entry in ("straight", "end", "side"):
        return entry
    return "end" if part.joint == "end" and part.turn == "90" else "straight"


def _shaped(part: Any, size: Section, plain_neck: bool = False
            ) -> tuple[GMesh, Vec3] | None:
    """(mesh, inlet point), or None for a record with no joint face. ``plain_neck``: the
    face is a neck that is itself the boot (no damper), so a collar may enter its side."""
    entry = boot_entry(part)
    if entry is None:
        return None
    face, point = part.face, part.point
    axis = _unit(part.axis) or (0.0, 0.0, 1.0)
    if entry == "trunk":
        return _side(part, size, face, point, axis)
    if entry in ("end", "side"):
        return _end_90(part, size, face, point, axis, plain_neck)
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


def _plain_neck(model: Any, tag: str | None) -> bool:
    from typehaus.resolve.neck_solids import _plain_neck as plain

    types = getattr(getattr(getattr(model, "plan", None), "library", None), "register_types", ())
    obj = next((o for o in getattr(model, "canvas_objects", ()) if o.tag == tag), None)
    catalog = next((t for t in types if obj is not None and t.tag == obj.type_ref), None)
    return plain(getattr(catalog, "neck", None))


def boot_mesh(model: Any, part: Any, size: Section, neck: Section | None) -> GMesh | None:
    """The boot's solid (see the module docstring)."""
    shaped = _shaped(part, size, _plain_neck(model, getattr(part, "other", None)))
    return shaped[0] if shaped is not None else _plain_boot(model, part, size, neck)
