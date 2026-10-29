"""A jamb pack at an L corner shares the corner pack instead of running into it.

Topology hands an L to a wall by tag, so a door on the *butting* wall whose jack and king
reach past the owner's near face stood inside the owner's corner studs (D-S-BATH1 at
N-S-BA1). The pack's wall takes the corner instead: its plates run through the square, its
jack and king stand inside its own corner pack, and the neighbour's end stud butts their
face — at N-S-BA1 a jack, a king, the corner stud, the end stud and the neighbour's end
stud, five together. Within the owning wall, a supplemental corner stud the pack would
overlap is not framed: the king stands in its place.

``structural.jamb_corner_pack`` grades the shared pack: a jack under each header end, a
full-height king or corner stud beside it, and the neighbour's end stud backed.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from typehaus.quantities import m as _m
from typehaus.resolve.framing.corners import neighbour_band_insets
from typehaus.resolve.framing.openings import (
    WallOpening,
    frame_end_supported,
    needs_jamb_pack,
    pocket_extent,
)
from typehaus.resolve.framing.tables import jamb_pack_counts, opening_framing_pattern

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel

#: Two corner ends at one height within this lap their top courses (``solver._laps``).
_LEVEL_TOL_M = 1e-4


def jamb_pack_extent(opening: WallOpening, thickness_m: float,
                     spacing_m: float, phase_m: float = 0.0) -> tuple[float, float] | None:
    """(low, high) stations of the opening's outermost jamb-pack faces, or None.

    The pack the same terms ``openings.frame_opening`` lays it from: the RO edge (a
    pocket's closed end on its pocket side), then jacks and kings a thickness apart. A
    supported frame end has no pack on that side, so its edge is the frame's own.
    """
    if not needs_jamb_pack(opening, spacing_m, thickness_m, phase_m):
        return None
    kings, jacks = jamb_pack_counts(_m(opening.width_m),
                                    opening_framing_pattern(opening.operation),
                                    getattr(opening, "jamb_framing", None))
    _mouth, closed = pocket_extent(opening)
    pocket_sign = 0 if not closed else (1 if opening.pocket_sign > 0 else -1)
    faces = []
    for sign in (-1, +1):
        edge = closed if sign == pocket_sign else opening.center_m + sign * opening.width_m / 2
        reach = 0.0 if frame_end_supported(opening, sign) else (kings + jacks) * thickness_m
        faces.append(edge + sign * reach)
    return faces[0], faces[1]


def drop_corner_studs_in_packs(studs: tuple, packs: list[tuple[float, float]]) -> tuple:
    """The corner studs no jamb pack overlaps; a king beside the corner is its stud."""
    return tuple(stud for stud in studs
                 if not any(low < stud.station_m + stud.along_axis_m / 2 - 1e-6
                            and stud.station_m - stud.along_axis_m / 2 + 1e-6 < high
                            for low, high in packs))


def jamb_packs_take_corners(plan: Any, model: ResolvedModel,
                            by_host: dict[str, list[WallOpening]]) -> None:
    """Give an L to the butting wall whose door's jamb pack reaches into the corner square.

    Only where the owner's own packs stay clear of the square (two packs cannot both have
    it) and both ends top out at one height (a lowered partition's corner is the
    full-height wall's, ``partition_top._full_height_owns_corners``). Sheathing keeps its
    own choice.
    """
    from typehaus.resolve.framing.solver import (
        _framing_axis,
        _structure_polygon,
        _wall_top_elevations,
        frames_as_members,
        structure_layer,
    )
    from typehaus.resolve.framing.tables import DEFAULT_SPACING, member_actual
    from typehaus.resolve.geometry import length, sub, unit

    def reaches_square(wall_tag: str, endpoint: str, neighbour_tag: str) -> bool:
        wall, neighbour = model.wall(wall_tag), model.wall(neighbour_tag)
        layer = structure_layer(plan, wall.assembly) if wall is not None else None
        if neighbour is None or not frames_as_members(layer):
            return False
        p0, p1 = _framing_axis(wall)
        axis_len, direction = length(sub(p1, p0)), unit(sub(p1, p0))
        at_start = endpoint == "start"
        insets = neighbour_band_insets(_structure_polygon(neighbour), p0, direction,
                                       axis_len, at_start=at_start)
        if insets is None:
            return False
        thickness = member_actual(layer.framing.member)[0] * 0.0254
        spacing = (layer.framing.spacing or DEFAULT_SPACING).meters
        # Doors only: a window's pack depends on the wall's layout phase, which is not
        # resolved yet, and no window stands in a corner square.
        for opening in (o for o in by_host.get(wall_tag, []) if o.is_door):
            extent = jamb_pack_extent(opening, thickness, spacing)
            if extent is None:
                continue
            if (extent[0] < insets[1]) if at_start else (extent[1] > axis_len - insets[1]):
                return True
        return False

    for index, junction in enumerate(model.junctions):
        if junction.kind != "l" or not junction.framing_owner:
            continue
        owner = next((item for item in junction.incidents
                      if item.wall_tag == junction.framing_owner), None)
        other = next((item for item in junction.incidents if item is not owner), None)
        if owner is None or other is None:
            continue
        owner_wall, other_wall = model.wall(owner.wall_tag), model.wall(other.wall_tag)
        if owner_wall is None or other_wall is None:
            continue
        tops = (_wall_top_elevations(owner_wall)[owner.endpoint == "end"],
                _wall_top_elevations(other_wall)[other.endpoint == "end"])
        if abs(tops[0] - tops[1]) > _LEVEL_TOL_M:
            continue
        if (reaches_square(other.wall_tag, other.endpoint, owner.wall_tag)
                and not reaches_square(owner.wall_tag, owner.endpoint, other.wall_tag)):
            model.junctions[index] = replace(junction, framing_owner=other.wall_tag)
