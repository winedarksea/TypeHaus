"""Where on the Image II eave pieces a leader lands, read off the cut the section draws.

Each anchor is a point of a real piece's cut outline — the eave's face, its hook, the pan's
hem around the hook, the strip-in, the gutter's roof flange and back — never a bbox centre,
which on a folded sheet is usually air. ``u`` grows outboard by ``out_sign``; inches.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.emit.draw.section_sheet_metal import PAN_END_CONNECTION
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.geometry_slice import CutPlane, slice_part, slice_solid
from typehaus.resolve.roof_image_ii import CONNECTION_EAVE, CONNECTION_STRIP

Anchor = tuple[float, float]
#: Across the cut from the cladding face, and up/down from the roof plane, that a piece may
#: lie and still be this eave's (inches).
_REACH_U_IN = 18.0
_REACH_Z_IN = 18.0
#: The band outboard of the cladding face where the eave face and the gutter back stand.
_FACE_BAND_IN = (-0.25, 0.75)
#: How far below the kick's tip the gutter-back leader lands, on the back's exposed run: at
#: the lap itself it shared a point with the face's leader.
_BELOW_KICK_IN = 0.5
#: The vertical face proper, without the kick that leans into the trough.
_FACE_PLANE_IN = 0.25
#: Inside the cladding face, over the wall panel head (inches).
_HEAD_IN = -0.6


@dataclass(frozen=True)
class EaveCut:
    """The eave pieces' cut points at one station, in the section frame (inches)."""

    clad_out: float
    out_sign: float
    eave: tuple[Anchor, ...]
    pan_end: tuple[Anchor, ...]
    strip: tuple[Anchor, ...]
    gutter: tuple[Anchor, ...]
    gutter_product: str | None

    def out(self, point: Anchor) -> float:
        return self.out_sign * (point[0] - self.clad_out)

    def eave_face(self) -> Anchor | None:
        """Mid-height of the eave face's vertical run, just outside the wall panel."""
        plane = [p for p in self._face() if self.out(p) <= _FACE_PLANE_IN]
        if not plane:
            return _median_z(self._face())
        zs = [z for _u, z in plane]
        return (max(plane, key=self.out)[0], (min(zs) + max(zs)) / 2.0)

    def eave_hook(self) -> Anchor | None:
        """The doubled lip's outer fold."""
        return max(self.eave, key=self.out, default=None)

    def pan_hem(self) -> Anchor | None:
        """The pan's fold around the hook."""
        return max(self.pan_end, key=self.out, default=None)

    def strip_in(self) -> Anchor | None:
        """The strip-in's upslope edge, where it laps onto the field membrane."""
        return min(self.strip, key=self.out, default=None)

    def gutter_flange(self) -> Anchor | None:
        """The roof flange's upslope end, under the eave leg."""
        return max(self.gutter, key=lambda p: p[1], default=None)

    def gutter_back(self) -> Anchor | None:
        """The gutter back just under the eave face's kick, below the lap it sits behind."""
        face = self._face()
        back = [p for p in self.gutter
                if _FACE_BAND_IN[0] <= self.out(p) <= _FACE_BAND_IN[1] + 0.5]
        if not face or not back:
            return None
        u = sorted(p[0] for p in back)[len(back) // 2]
        return (u, min(z for _u, z in face) - _BELOW_KICK_IN)

    def wall_head(self) -> Anchor | None:
        """The eave leg's underside over the wall panel head, ``_HEAD_IN`` inside the face.

        The leg is straight from its hem to the face corner, and its cut has vertices only at
        those ends, so the point is interpolated between them.
        """
        face = self._face()
        if not face or not self.eave:
            return None
        corner = max(face, key=lambda p: p[1])
        inboard = min(self.out(p) for p in self.eave)
        hem = min((p for p in self.eave if self.out(p) <= inboard + 0.1), key=lambda p: p[1])
        span = self.out(corner) - self.out(hem)
        if span <= 0.0:
            return None
        t = (_HEAD_IN - self.out(hem)) / span
        return (hem[0] + (corner[0] - hem[0]) * t, hem[1] + (corner[1] - hem[1]) * t)

    def _face(self) -> list[Anchor]:
        return [p for p in self.eave if _FACE_BAND_IN[0] <= self.out(p) <= _FACE_BAND_IN[1]]


def eave_cut(model, roof, direction: str, station: float, clad_out: float,
             junction_z: float, out_sign: float) -> EaveCut | None:
    """The eave pieces this cut passes through, or ``None`` on a roof without them."""
    if roof is None:
        return None
    plane = CutPlane(axis=direction, station_m=station)
    found: dict[str, list[Anchor]] = {CONNECTION_EAVE: [], PAN_END_CONNECTION: [],
                                      CONNECTION_STRIP: []}
    for member in roof.members:
        if member.connection not in found:
            continue
        solid = member_solid(member)
        points = [] if solid is None else _near(
            [p for profile in slice_solid(solid, plane) for p in profile.outline],
            clad_out, junction_z)
        found[member.connection] += points
    if not found[CONNECTION_EAVE]:
        return None
    gutter, product = _gutter_points(model, plane, clad_out, junction_z)
    return EaveCut(clad_out, out_sign, tuple(found[CONNECTION_EAVE]),
                   tuple(found[PAN_END_CONNECTION]), tuple(found[CONNECTION_STRIP]),
                   tuple(gutter), product)


def _gutter_points(model, plane, clad_out: float, junction_z: float):
    points: list[Anchor] = []
    product = None
    for solid in model.solids:
        if solid.category != "gutter":
            continue
        element = model.geometry.by_uid(solid.uid)
        if element is None:
            continue
        cut = _near([p for part in element.parts for profile in slice_part(part, plane)
                     for p in profile.outline], clad_out, junction_z)
        if cut:
            points += cut
            product = product or solid.product
    return points, product


def _near(outline, clad_out: float, junction_z: float) -> list[Anchor]:
    points = [(u / M_PER_IN, z / M_PER_IN) for u, z in outline]
    return [(u, z) for u, z in points
            if abs(u - clad_out) <= _REACH_U_IN and abs(z - junction_z) <= _REACH_Z_IN]


def _median_z(points: list[Anchor]) -> Anchor | None:
    if not points:
        return None
    ordered = sorted(points, key=lambda p: p[1])
    return ordered[len(ordered) // 2]
