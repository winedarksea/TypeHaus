"""An outie wall's opening perimeter: membrane the foam laps over, never under.

On a girt wall the KDAT jamb posts and head/sill courses stand 1/2" off the foam face, so a
lap onto the foam face lies in that slot, behind wood set before the foam exists. Instead
the pre-foam membrane ("raccoon", BSI-048) goes on after the bucks and before any block:
the buck's wall-side face, its front edge, and a band onto the sheathing that the foam then
laps over. The posts keep their back slot and dry to the cavity; only their outer face takes
a band, where the window flange and J-receiver bear. A window's pan coats the sill course
face and underside as a drip.
"""

from __future__ import annotations

from typehaus.resolve.flashing_config import FlashingConfig
from typehaus.resolve.framing.truss_common import LADDER_CATEGORY
from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.model import ResolvedOpening, ResolvedWall
from typehaus.resolve.sheet_geometry import extruded_quad

_TOL_M = 1e-5


def raccoon_meshes(frame, opening: ResolvedOpening, contour, cfg: FlashingConfig, *,
                   base: float, wall_base: float, jamb_top: float,
                   sill_side: bool) -> list[GMesh]:
    """The pre-foam membrane round the RO edge; ``contour`` is the head's (station, z).

    ``base`` is the RO bottom clamped to ``wall_base``, below which there is no sheathing.
    """
    lo = opening.center_along_m - opening.width_m / 2
    hi = lo + opening.width_m
    sill = base
    sheath, mount, buck = frame.sheath_face, frame.mount, frame.buck
    t, band = cfg.perimeter_membrane_m, cfg.raccoon_band_m
    bottom = max(wall_base, sill - band) if sill_side else base
    outward = (*[v * t for v in frame.outward], 0.0)
    out = []
    for station, sign in ((lo, 1.0), (hi, -1.0)):
        if buck > 0:
            # The jamb buck's wall-side face, thickened away from the RO: the post's seat.
            out.append(frame.section(station, ((sheath, sill), (mount, sill), (mount, jamb_top),
                                               (sheath, jamb_top)), t, -sign))
            out.append(frame.leg(station if sign > 0 else station - buck, buck,
                                 (mount, sill), (mount, jamb_top), t))
        out.append(frame.leg(station - band if sign > 0 else station, band,
                             (sheath, bottom), (sheath, jamb_top + band), t))
    for (s0, z0), (s1, z1) in zip(contour[:-1], contour[1:], strict=True):
        if buck > 0:
            out.append(extruded_quad(tuple(frame.point(s, d, z) for s, d, z in (
                (s0, sheath, z0), (s1, sheath, z1), (s1, mount, z1), (s0, mount, z0))),
                (0.0, 0.0, t)))
            out.append(extruded_quad(tuple(frame.point(s, mount, z) for s, z in (
                (s0, z0 - buck), (s1, z1 - buck), (s1, z1), (s0, z0))), outward))
        out.append(extruded_quad(tuple(frame.point(s, sheath, z) for s, z in (
            (s0, z0), (s1, z1), (s1, z1 + band), (s0, z0 + band))), outward))
    if sill_side:
        # The sill buck's underside; the pan's drip coat covers its front edge.
        if buck > 0:
            out.append(extruded_quad(tuple(frame.point(s, d, sill) for s, d in (
                (lo, sheath), (hi, sheath), (hi, mount), (lo, mount))), (0.0, 0.0, -t)))
        if sill - bottom > _TOL_M:
            out.append(extruded_quad(tuple(frame.point(s, sheath, z) for s, z in (
                (lo, bottom), (hi, bottom), (hi, sill), (lo, sill))), outward))
    return out


def sill_course(wall: ResolvedWall, opening: ResolvedOpening):
    """The flat course under the RO, its top on the sill; ``None`` on a wall without one."""
    lo = opening.center_along_m - opening.width_m / 2
    sill = wall.base_ref_z_m + opening.sill_m
    (x0, y0), (x1, y1) = wall.axis
    span = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    along = ((x1 - x0) / span, (y1 - y0) / span)
    for member in wall.members:
        if member.category != LADDER_CATEGORY or abs(member.z1_m - sill) > _TOL_M:
            continue
        stations = sorted((p[0] - x0) * along[0] + (p[1] - y0) * along[1]
                          for p in (member.p0, member.p1))
        if stations[0] - _TOL_M <= lo + opening.width_m / 2 <= stations[1] + _TOL_M:
            return member
    return None


def sill_drip(frame, wall: ResolvedWall, opening: ResolvedOpening,
              cfg: FlashingConfig) -> tuple[float, list[GMesh]] | None:
    """Where a window pan's drip coat stops, and its underside leg.

    The coat runs the sill course's face (the pan's down leg reaches the course bottom) and
    its underside back to the slot, across both posts' end grain: the posts are the same
    board as the course, so as wide as the course is tall.
    """
    course = sill_course(wall, opening)
    if course is None:
        return None
    depth = ((course.p0[0] - frame.origin[0]) * frame.outward[0]
             + (course.p0[1] - frame.origin[1]) * frame.outward[1])
    back = 2 * depth - frame.mount
    post = course.z1_m - course.z0_m
    lo = opening.center_along_m - opening.width_m / 2 - post
    hi = opening.center_along_m + opening.width_m / 2 + post
    z = course.z0_m
    underside = extruded_quad(tuple(frame.point(s, d, z) for s, d in (
        (lo, back), (hi, back), (hi, frame.mount), (lo, frame.mount))),
        (0.0, 0.0, -cfg.sill_membrane_m))
    return z, [underside]


def post_band_meshes(frame, opening: ResolvedOpening, cfg: FlashingConfig, *,
                     z0: float, z1: float) -> list[GMesh]:
    """Each jamb post's outer face where the flange and J-receiver bear; never its sides."""
    lo = opening.center_along_m - opening.width_m / 2
    hi = lo + opening.width_m
    width = cfg.post_band_m
    return [frame.leg(station, width, (frame.mount, z0), (frame.mount, z1),
                      cfg.perimeter_membrane_m) for station in (lo - width, hi)]
