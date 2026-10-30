"""The drywall accessories that follow one element rather than a room ring (→ drywall_trims).

* ``led_profile`` — each plaster-in run, its length;
* ``outside_corner`` on a soffit — its outline less what a wall or lower soffit backs;
* ``tile_reveal`` — a non-wood band replacing the wall finish: its top where it stops below
  the ceiling, and each end not continued round a corner by another band at its height;
* ``door_l_bead`` — a trimless door, ``2·h + w`` on each gypsum face;
* ``window_corner`` / ``window_frame`` — a window return's three-sided bead pair, on the
  standard's beads or, with none declared, the library generics.
"""

from __future__ import annotations

import math

from shapely.geometry import LineString, Point, Polygon

from typehaus.resolve.drywall_trims import TrimContext, room_floor, top_at
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_door_products import finish_faces
from typehaus.resolve.interior_trim_scope import face_is_gypsum
from typehaus.resolve.room_lookup import room_owning

_GENERIC_WINDOW_BEADS = ("drywall-corner-bead", "drywall-frame-termination-bead")
_ROOM_PROBE_M = 0.15
_JAMB_PROBE_M = 0.05
_CONTINUED_M = 0.03
_SAME_HEIGHT_M = 0.0254
_TOP_GAP_M = 0.025
_SOFFIT_BACKED_M = 0.0254
_SOFFIT_STEP_M = 0.003


def led_profiles(ctx: TrimContext) -> None:
    profile = ctx.standard.led_profile
    for run in ctx.model.light_runs:
        if run.profile == "plaster_in" and profile is not None:
            ctx.add("led_profile", run.room, run.storey, profile.material_ref, run.length_m,
                    (run.tag, run.room or ""))


def soffit_corners(ctx: TrimContext) -> None:
    """A soffit's bottom edge takes corner bead where no wall or lower soffit stands under it.

    Judged with a 1" gap, not ``wall_contacts``' fitting tolerance: an outline authored a
    fraction off the board still butts it, and a lower neighbour makes the edge inside.
    """
    from typehaus.resolve.soffits import wall_footprint

    model = ctx.model
    for soffit in model.soffits:
        ring = list(soffit.outline)
        if len(ring) < 3:
            continue
        backers = [wall_footprint(wall) for wall in model.walls
                   if wall.storey == soffit.storey and wall.layers
                   and wall.z0_m < soffit.z0_m < wall.z1_m]
        backers += [Polygon(other.outline) for other in model.soffits
                    if other.uid != soffit.uid and other.storey == soffit.storey
                    and len(other.outline) >= 3 and other.z0_m < soffit.z0_m - _SOFFIT_STEP_M]
        near = [shape.buffer(_SOFFIT_BACKED_M, join_style=2) for shape in backers
                if not shape.is_empty and shape.distance(Polygon(ring)) < _SOFFIT_BACKED_M]
        centroid = Polygon(ring).centroid
        room = room_owning(model, soffit.storey, (centroid.x, centroid.y))
        for index in range(len(ring)):
            edge = LineString((ring[index], ring[(index + 1) % len(ring)]))
            spans = sorted(
                (min(stations), max(stations))
                for shape in near
                for piece in _lines(edge.intersection(shape))
                for stations in ([edge.project(Point(c)) for c in piece.coords],))
            covered, reach = 0.0, 0.0
            for lo, hi in spans:
                lo = max(lo, reach)
                if hi > lo:
                    covered += hi - lo
                    reach = hi
            ctx.add("outside_corner", room.tag if room else None, soffit.storey,
                    ctx.standard.outside_corner_ref, edge.length - covered,
                    (soffit.tag, room.tag if room else ""))


def _lines(geometry):
    return [part for part in getattr(geometry, "geoms", (geometry,))
            if part.geom_type == "LineString" and part.length > 0.0]


def tile_reveals(ctx: TrimContext) -> None:
    model = ctx.model
    rooms = {room.tag: room for room in model.rooms}
    bands = [band for band in model.panelings
             if band.room in rooms and band.replaces_wall_finish and len(band.outline) >= 3
             and band.z0_m is not None and band.z1_m is not None
             and not getattr(ctx.materials.get(band.material_ref), "species", None)]
    walls = {wall.tag: wall for wall in model.walls}
    for band in bands:
        room, wall = rooms[band.room], walls.get(band.wall_tag)
        if wall is None:
            continue
        outline = Polygon(band.outline)
        centroid = (outline.centroid.x, outline.centroid.y)
        top = top_at(model, room, centroid, (wall,))
        tags = (band.room, band.tag)
        face = _GypsumBeside(ctx, wall, band, centroid)
        if band.z1_m < top - _TOP_GAP_M and face.at(centroid, band.z1_m + 0.02,
                                                     band.z1_m + 0.08):
            ctx.add("tile_reveal", band.room, band.storey, ctx.standard.tile_reveal_ref,
                    band.run_m, tags)
        mid_z = (band.z0_m + band.z1_m) / 2.0
        for end in _band_ends(band.outline):
            if not face.at(face.past(end), mid_z - 0.05, mid_z + 0.05):
                continue  # the band ends on cedar, glass or another finish, not board
            continued = any(
                other is not band and abs(other.z1_m - band.z1_m) < _SAME_HEIGHT_M
                and other.z0_m < band.z1_m and other.z1_m > band.z0_m
                and Polygon(other.outline).distance(Point(end)) < _CONTINUED_M
                for other in bands if other.room == band.room)
            if not continued:
                ctx.add("tile_reveal", band.room, band.storey, ctx.standard.tile_reveal_ref,
                        band.z1_m - band.z0_m, tags)


class _GypsumBeside:
    """The board on ``wall``'s face next to a band: probed just past its edges."""

    def __init__(self, ctx: TrimContext, wall, band, centroid) -> None:
        origin, tangent, normal, _length = wall_frame(wall)
        side = 1.0 if ((centroid[0] - origin[0]) * normal[0]
                       + (centroid[1] - origin[1]) * normal[1]) > 0 else -1.0
        self.ctx, self.wall, self.tangent = ctx, wall, tangent
        self.into = (-normal[0] * side, -normal[1] * side)
        self.half = band.thickness_m / 2.0
        self.centroid = centroid

    def past(self, end):
        """A face point 2 cm beyond the band's ``end``, along the wall."""
        t = self.tangent
        away = 1.0 if ((end[0] - self.centroid[0]) * t[0]
                       + (end[1] - self.centroid[1]) * t[1]) > 0 else -1.0
        return (end[0] + t[0] * away * 0.02, end[1] + t[1] * away * 0.02)

    def at(self, xy, z0: float, z1: float) -> bool:
        # The band replaces the finish, so its room face is the wall's finish face.
        face = (xy[0] - self.into[0] * self.half, xy[1] - self.into[1] * self.half)
        return face_is_gypsum(self.wall, face, self.into, z0, z1, self.ctx.materials)


def _band_ends(outline) -> list[tuple[float, float]]:
    """Midpoints of a band rectangle's two short sides."""
    ring = list(outline)
    sides = [(math.dist(ring[i], ring[(i + 1) % len(ring)]), i) for i in range(len(ring))]
    short = sorted(sides)[:2]
    return [((ring[i][0] + ring[(i + 1) % len(ring)][0]) / 2.0,
             (ring[i][1] + ring[(i + 1) % len(ring)][1]) / 2.0) for _d, i in short]


def door_beads(ctx: TrimContext) -> None:
    model = ctx.model
    door_types = {dt.tag: dt for dt in model.plan.library.door_types}
    walls = {wall.tag: wall for wall in model.walls}
    for opening in sorted(model.openings, key=lambda o: o.uid):
        door_type = door_types.get(opening.type_ref or "")
        wall = walls.get(opening.host_wall)
        if (not opening.is_door or opening.kind != "door" or wall is None
                or not getattr(door_type, "trimless", False)):
            continue
        origin, tangent, normal, axis_length = wall_frame(wall)
        faces = finish_faces(wall)
        if axis_length <= 1e-9 or faces is None:
            continue
        cx = origin[0] + tangent[0] * opening.center_along_m
        cy = origin[1] + tangent[1] * opening.center_along_m
        jamb = opening.width_m / 2.0 + _JAMB_PROBE_M
        for side, face in ((1, faces[1]), (-1, faces[0])):
            room = room_owning(model, wall.storey, (cx + normal[0] * (face + side * _ROOM_PROBE_M),
                                                    cy + normal[1] * (face + side * _ROOM_PROBE_M)))
            if room is None:
                continue
            floor_z = room_floor(model, room)
            point = (cx + tangent[0] * jamb + normal[0] * face,
                     cy + tangent[1] * jamb + normal[1] * face)
            into = (-normal[0] * side, -normal[1] * side)
            if face_is_gypsum(wall, point, into, floor_z + 0.3, floor_z + 1.0, ctx.materials):
                ctx.add("door_l_bead", room.tag, room.storey, ctx.standard.door_bead_ref,
                        2.0 * opening.height_m + opening.width_m, (opening.tag, room.tag))


def window_returns(ctx: TrimContext) -> None:
    model = ctx.model
    corner, frame = ((ctx.standard.window_corner_ref, ctx.standard.window_frame_ref)
                     if ctx.standard is not None else _GENERIC_WINDOW_BEADS)
    openings = {opening.tag: opening for opening in model.openings}
    walls = {wall.tag: wall for wall in model.walls}
    for reveal in sorted(model.window_returns, key=lambda r: r.uid):
        room = _window_room(model, openings.get(reveal.window_ref), walls.get(reveal.wall_tag))
        tag = room.tag if room is not None else None
        for kind, material in (("window_corner", corner), ("window_frame", frame)):
            ctx.add(kind, tag, reveal.storey, material, reveal.bead_length_m,
                    (reveal.window_ref, tag or ""))


def _window_room(model, opening, wall):
    if opening is None or wall is None:
        return None
    origin, tangent, normal, axis_length = wall_frame(wall)
    faces = finish_faces(wall)
    if axis_length <= 1e-9 or faces is None:
        return None
    cx = origin[0] + tangent[0] * opening.center_along_m
    cy = origin[1] + tangent[1] * opening.center_along_m
    for side, face in ((1, faces[1]), (-1, faces[0])):
        offset = face + side * _ROOM_PROBE_M
        room = room_owning(model, wall.storey, (cx + normal[0] * offset, cy + normal[1] * offset))
        if room is not None:
            return room
    return None
