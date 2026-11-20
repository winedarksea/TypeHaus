"""Cast-in sill parts: a MASA on its sill face; an STHD's leaf on its framing face with the
spoon turned into the core."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_ir import Vec2, Vec3

if TYPE_CHECKING:
    from typehaus.resolve.connector_geometry.placement import ConnectorPlacementIndex


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
               z_m: float, tangent: Vec2, derived: bool) -> tuple | None:
    """The concrete core a strap is cast into: a derived joint's return, else a ``connects``."""
    if derived:
        run = index.return_at(references[0], point, z_m, tangent) if references else None
        return _core_layer(index, run.element_tags[0]) if run and run.element_tags else None
    return next((core for tag in references if (core := _core_layer(index, tag))), None)


def embedded_strap_frame(core: Sequence[Vec2], point: Vec2, x_axis: Vec3, y_axis: Vec3,
                         projection_in: float, cover_in: float
                         ) -> tuple[Vec3, Vec3, float | None]:
    """``(x_axis, y_axis, spoon projection | None)``: the spoon away from the nearer core face.

    The leaf stays on ``point``. Across the wall the spoon runs toward the far core face and
    stops ``cover_in`` short of it; ``None`` keeps the catalog projection.
    """
    n = y_axis[:2]
    offsets = [(p[0] - point[0]) * n[0] + (p[1] - point[1]) * n[1] for p in core]
    lo, hi = min(offsets), max(offsets)
    reach = hi
    if hi < -lo:  # turned half a revolution, so the frame stays right-handed
        x_axis, y_axis, reach = (-x_axis[0], -x_axis[1], 0.0), (-y_axis[0], -y_axis[1], 0.0), -lo
    room_in = reach / M_PER_IN - cover_in
    return x_axis, y_axis, (room_in if 0.0 < room_in < projection_in else None)


def strap_frame(index: ConnectorPlacementIndex, part: str, references: Sequence[str],
                point: Vec2, z_m: float, x_axis: Vec3, y_axis: Vec3, derived: bool
                ) -> tuple[Vec3, Vec3, float | None]:
    """An STHD's frame; unchanged where no foundation core is found under it."""
    from typehaus.resolve.connector_geometry.ties import EMBEDDED_STRAPS, SILHOUETTE, strap_part

    core = core_under(index, references, point, z_m, x_axis[:2], derived)
    if core is None:
        return x_axis, y_axis, None
    projection_in = EMBEDDED_STRAPS[strap_part(part)].spoon_projection_in
    return embedded_strap_frame(core, point, x_axis, y_axis, projection_in,
                                SILHOUETTE.embedded_spoon_cover_in)
