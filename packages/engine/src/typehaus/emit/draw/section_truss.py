"""A roof truss in section: chords, heel and webs, drawn from its ``TrussShape``.

The engine resolves ONE member per truss, an envelope from bearing to bearing and plate top
to ridge (``roof_gable.truss_member``). Cut, that envelope is a solid box filling the attic
with wood that is not there. This is the section twin of ``ui/src/three/roofTruss.ts``: the
chord depth, heel, tails and gable flag are model; the fink web pattern is the one drawing
convention, as it is in the viewer. The top chord's TOP edge lies on the roof plane
(``truss_heel_lift_m`` put the deck at plate + heel + chord), so the deck sits on it.
"""

from __future__ import annotations

import math

from typehaus.emit.draw.lineweights import PROFILE
from typehaus.emit.draw.scene import Hatch, Polyline
from typehaus.emit.draw.section_clip import clip_polygon
from typehaus.quantities import M_PER_IN

# The viewer's constants (roofTruss.ts), so the two drawings agree on the pattern.
_DEFAULT_CHORD_M = 3.5 * M_PER_IN
_FINK_PANEL_FRACTION = 1 / 3
_TOP_CHORD_PANEL_FRACTION = 1 / 4
_GABLE_STUD_SPACING_M = 16 * M_PER_IN
_MIN_GABLE_STUD_M = 1.5 * M_PER_IN


def top_chord_frame(member, section) -> tuple[float, float, float, float]:
    """``(chord, heel, slope, plumb_depth)``: the top chord springs ``heel`` over the plate.

    A heel that would not fit under the apex springs off the bottom chord, as in the viewer.
    """
    chord = section.flange_thickness_m or _DEFAULT_CHORD_M
    rise = member.z1_m - member.z0_m
    heel = member.truss.heel_m if member.truss.heel_m + chord < rise else chord
    slope = (rise - heel - chord) / (math.dist(member.p0, member.p1) / 2.0)
    return chord, heel, slope, chord * math.sqrt(1.0 + slope * slope)


def truss_sticks(member, section) -> list[list[tuple[float, float]]]:
    """Each stick as a polygon in the truss plane: ``s`` from the p0 bearing, ``z`` absolute."""
    shape = member.truss
    span = math.dist(member.p0, member.p1)
    rise = member.z1_m - member.z0_m
    if shape is None or span < 1e-9 or rise < 1e-9:
        return []
    chord, heel, slope, plumb_depth = top_chord_frame(member, section)
    web = section.web_thickness_m or section.width_m
    half = span / 2.0
    z0 = member.z0_m

    def top(s: float) -> float:
        return z0 + heel + chord + slope * min(s, span - s)

    def under(s: float) -> float:
        return top(s) - plumb_depth

    sticks = [[(0.0, z0), (span, z0), (span, z0 + chord), (0.0, z0 + chord)]]
    for (a, b_) in ((-shape.tail_lo_m, half), (half, span + shape.tail_hi_m)):
        sticks.append([(a, under(a)), (b_, under(b_)), (b_, top(b_)), (a, top(a))])
    floor = z0 + chord
    # The raised heel: the vertical the plant plates at each bearing under the top chord.
    if under(0.0) - floor > web:
        for (a, b_) in ((0.0, web), (span - web, span)):
            sticks.append([(a, floor), (b_, floor), (b_, under(b_)), (a, under(a))])
    if under(half) - floor < web:
        return sticks
    if shape.gable:
        s = _GABLE_STUD_SPACING_M
        while s < span - 1e-9:
            if under(s) - floor >= _MIN_GABLE_STUD_M:
                sticks.append(_bar((s, floor), (s, under(s)), web))
            s += _GABLE_STUD_SPACING_M
        return sticks
    apex = (half, under(half))
    if under(span * _FINK_PANEL_FRACTION) - floor < web:
        sticks.append(_bar((half, floor), apex, web, web / 2.0))
        return sticks
    for side in (-1.0, 1.0):
        foot = (half + side * span * (0.5 - _FINK_PANEL_FRACTION), floor)
        s_top = half + side * span * (0.5 - _TOP_CHORD_PANEL_FRACTION)
        sticks.append(_bar(foot, apex, web, web / 2.0))
        sticks.append(_bar(foot, (s_top, under(s_top)), web, web / 2.0))
    return sticks


def _bar(a, b, thickness, overrun=0.0) -> list[tuple[float, float]]:
    """A stick of ``thickness`` between two plane points, grown ``overrun`` at each end."""
    ds, dz = b[0] - a[0], b[1] - a[1]
    length = math.hypot(ds, dz)
    ts, tz = ds / length, dz / length
    ns, nz = -tz * thickness / 2.0, ts * thickness / 2.0
    a = (a[0] - ts * overrun, a[1] - tz * overrun)
    b = (b[0] + ts * overrun, b[1] + tz * overrun)
    return [(a[0] - ns, a[1] - nz), (b[0] - ns, b[1] - nz),
            (b[0] + ns, b[1] + nz), (a[0] + ns, a[1] + nz)]


def emit_truss_cut(b, member, section, plane, crop, uid, tag, pattern, material,
                   is_cut: bool) -> bool:
    """Draw ``member`` as its sticks; ``False`` hands an oblique truss back to the envelope.

    Along its span (the cut runs down the truss), every stick is drawn in elevation, tails
    included — but only when the envelope itself is cut (``is_cut``). Across it, each stick
    the station crosses is a cut face one truss thick.
    """
    along = [member.p1[i] - member.p0[i] for i in (0, 1)]
    if abs(along[plane.perp_index]) < 1e-9:
        if not is_cut:
            return True
        start, sign = member.p0[plane.u_index], math.copysign(1.0, along[plane.u_index])
        for stick in truss_sticks(member, section):
            _emit_polygon(b, [(start + sign * s, z) for (s, z) in stick], crop, uid, tag,
                          pattern, material)
        return True
    if abs(along[plane.u_index]) > 1e-9:
        return False
    station = (plane.station_m - member.p0[plane.perp_index]) * math.copysign(
        1.0, along[plane.perp_index])
    centre, width = member.p0[plane.u_index], section.width_m
    for stick in truss_sticks(member, section):
        band = _z_at(stick, station)
        if band is None:
            continue
        u0, u1 = centre - width / 2.0, centre + width / 2.0
        _emit_polygon(b, [(u0, band[0]), (u1, band[0]), (u1, band[1]), (u0, band[1])],
                      crop, uid, tag, pattern, material)
    return True


def _z_at(polygon, s: float) -> tuple[float, float] | None:
    """The z range a convex polygon covers on the vertical line at ``s``."""
    zs = []
    for index, (s1, z1) in enumerate(polygon):
        s0, z0 = polygon[index - 1]
        if min(s0, s1) <= s <= max(s0, s1) and abs(s1 - s0) > 1e-12:
            zs.append(z0 + (z1 - z0) * (s - s0) / (s1 - s0))
    if len(zs) < 2 or max(zs) - min(zs) < 1e-9:
        return None
    return min(zs), max(zs)


def _emit_polygon(b, polygon, crop, uid, tag, pattern, material) -> None:
    clipped = clip_polygon(polygon, crop)
    if len(clipped) < 3:
        return
    points = tuple((u / M_PER_IN, z / M_PER_IN) for (u, z) in clipped)
    b.add(Polyline(points=points, layer="S-FRAM", closed=True, lineweight=PROFILE,
                   uid=uid, tag=tag))
    b.add(Hatch(boundary=points, pattern=pattern, layer="A-WALL-PATT",
                uid=uid, material=material or "spf"))
