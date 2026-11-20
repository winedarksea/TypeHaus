"""Cast-in sill parts: a MASA on its sill face; an STHD's leaf on its framing face with the
spoon turned into the core.

An STHD is tested cast at a concrete face with its spoon reaching across the stem (ESR-2920
Figure 1). Where the framing face stands inside the core and the spoon cannot reach its
catalog projection from there, the strap enters at the core face behind it and is bent one
full cycle (§4.2) over the pour top to the framing: ``jog_in``.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_ir import Vec2, Vec3

if TYPE_CHECKING:
    from typehaus.resolve.connector_geometry.placement import ConnectorPlacementIndex


@dataclass(frozen=True)
class EmbeddedStrap:
    """One placed STHD, as drawn: what ``structural.strap_hold_down_embedment`` grades."""

    uid: str
    tag: str
    part: str
    derived: bool
    core_tag: str
    framed_tag: str | None
    leaf_xy: Vec2          # the leaf's face on the framing
    entry_xy: Vec2         # where the strap enters the concrete (leaf less the jog)
    spoon_xy: Vec2         # unit, across the core toward the toe
    along_xy: Vec2         # unit, along the wall
    line_z_m: float        # the strap's embedment line, as placed
    embedment_in: float    # the catalog depth drawn below that line
    projection_in: float   # the spoon's reach as drawn
    jog_in: float


_NAILED_VERTICALS = frozenset({"stud", "king", "corner", "jack"})


def first_stud_z_m(wall, near_xy: Vec2 | None = None,
                   radius_m: float = 12.0 * M_PER_IN) -> float | None:
    """The lowest vertical a strap can nail to (plates, sills, rims excluded, §4.2), among
    those within ``radius_m`` of ``near_xy`` when given."""
    zs = [m.z0_m for m in wall.members if m.category in _NAILED_VERTICALS
          and (near_xy is None or math.dist(m.p0[:2], near_xy) <= radius_m)]
    return min(zs) if zs else None


def _core_layer(index: ConnectorPlacementIndex, tag: str) -> tuple | None:
    wall = index.model.wall(tag)
    if wall is None or not wall.is_foundation:
        return None
    layer = next((lyr for lyr in wall.layers if lyr.function == "structure" and lyr.polygon),
                 None)
    return tuple(layer.polygon) if layer is not None else None


def on_sill_face(outline: Sequence[Vec2], point: Vec2, y_axis: Vec3) -> Vec2:
    """A MASA's leaf: ``point`` moved onto the sill's -y face, read off the sill itself."""
    face = min(x * y_axis[0] + y * y_axis[1] for x, y in outline) \
        - point[0] * y_axis[0] - point[1] * y_axis[1]
    return (point[0] + y_axis[0] * face, point[1] + y_axis[1] * face)


def core_under(index: ConnectorPlacementIndex, references: Sequence[str], point: Vec2,
               z_m: float, tangent: Vec2, derived: bool
               ) -> tuple[str, tuple, str | None] | None:
    """``(core tag, core polygon, framed tag)``: a derived joint's return, else a ``connects``."""
    if derived:
        run = index.return_at(references[0], point, z_m, tangent) if references else None
        if not run or not run.element_tags:
            return None
        core = _core_layer(index, run.element_tags[0])
        framed = run.element_tags[1] if len(run.element_tags) > 1 else None
        return (run.element_tags[0], core, framed) if core else None
    found = next(((tag, core) for tag in references if (core := _core_layer(index, tag))),
                 None)
    if found is None:
        return None
    framed = next((tag for tag in references if tag != found[0]
                   and index.model.wall(tag) is not None), None)
    return found[0], found[1], framed


def embedded_strap_frame(core: Sequence[Vec2], point: Vec2, x_axis: Vec3, y_axis: Vec3,
                         projection_in: float, cover_in: float
                         ) -> tuple[Vec3, Vec3, float | None, float]:
    """``(x_axis, y_axis, spoon projection | None, jog)``: the spoon toward the far core face.

    The leaf stays on ``point``. Where the catalog spoon does not fit ``cover_in`` short of
    the far face, the strap enters at the near face (``jog`` inches back); where even the
    whole core is too thin, the spoon is clamped and the check refuses it.
    """
    n = y_axis[:2]
    offsets = [(p[0] - point[0]) * n[0] + (p[1] - point[1]) * n[1] for p in core]
    lo, hi = min(offsets), max(offsets)
    reach, behind = hi, -lo
    if hi < -lo:  # turned half a revolution, so the frame stays right-handed
        x_axis, y_axis = (-x_axis[0], -x_axis[1], 0.0), (-y_axis[0], -y_axis[1], 0.0)
        reach, behind = -lo, hi
    room_in = reach / M_PER_IN - cover_in
    if room_in >= projection_in:
        return x_axis, y_axis, None, 0.0
    jog_in = max(behind / M_PER_IN, 0.0)
    if room_in + jog_in >= projection_in:
        return x_axis, y_axis, None, jog_in
    return x_axis, y_axis, (room_in if room_in > 0.0 else None), 0.0


def strap_frame(index: ConnectorPlacementIndex, solid, part: str, references: Sequence[str],
                point: Vec2, z_m: float, x_axis: Vec3, y_axis: Vec3, derived: bool
                ) -> tuple[Vec3, Vec3, float | None, float]:
    """An STHD's frame, recorded on ``model.embedded_straps``; unchanged with no core."""
    from typehaus.resolve.connector_geometry.ties import EMBEDDED_STRAPS, SILHOUETTE, strap_part

    found = core_under(index, references, point, z_m, x_axis[:2], derived)
    if found is None:
        return x_axis, y_axis, None, 0.0
    core_tag, core, framed = found
    dims = EMBEDDED_STRAPS[strap_part(part)]
    x_axis, y_axis, spoon_in, jog_in = embedded_strap_frame(
        core, point, x_axis, y_axis, dims.spoon_projection_in,
        SILHOUETTE.embedded_spoon_cover_in)
    jog_m = jog_in * M_PER_IN
    index.model.embedded_straps.append(EmbeddedStrap(
        uid=solid.uid, tag=solid.tag, part=part, derived=derived, core_tag=core_tag,
        framed_tag=framed,
        leaf_xy=point, entry_xy=(point[0] - y_axis[0] * jog_m, point[1] - y_axis[1] * jog_m),
        spoon_xy=(y_axis[0], y_axis[1]), along_xy=(x_axis[0], x_axis[1]), line_z_m=z_m,
        embedment_in=dims.embedment_depth_in,
        projection_in=spoon_in if spoon_in is not None else dims.spoon_projection_in,
        jog_in=jog_in))
    return x_axis, y_axis, spoon_in, jog_in
