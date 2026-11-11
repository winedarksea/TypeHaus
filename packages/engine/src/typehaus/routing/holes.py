"""Holes already through a floor's members: authored runs, and runs laid in this campaign.

A new crossing is graded against them the way the checks grade it, off the same
``resolve/mep_crossings.leg_crossings`` stations:

* an I-joist hole stays "2 x the larger hole" clear of every other hole in the same joist
  (ESR-1153 Table A fn 1, as ``plan/framing_charts.py`` transcribes it;
  ``mep.run_member_crossing``);
* an open-web crossing lands in an opening it fits, and a D pocket takes ONE run
  (``mep.run_member_crossing``, ``mep.open_web_panel``).

A run the search may occupy (``touch``) is no neighbour. A run laid earlier in the same
campaign is not in the model yet, so its caller hands it in (``laid_lines``): two branches
laid 2.7" apart through one TJI, or a branch through the trunk's pocket, is otherwise
invisible until the network is graded. ``framing_bore_limits.md`` §10.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from typehaus.quantities import M_PER_IN

#: ``(tag, plan path, per-vertex centreline z, outside radius)``.
Line = tuple[str, tuple[tuple[float, float], ...], tuple[float, ...], float]


def laid_lines(proposals: Iterable[Any]) -> list[Line]:
    """Proposals laid earlier in a campaign as lines, at the outside a pasted run reads."""
    from typehaus.resolve.pipe_sections import (
        pipe_outside_diameter_m,
        raceway_outside_diameter_m,
    )

    out: list[Line] = []
    for p in proposals:
        material = p.echo.get("material")
        material = getattr(material, "value", material)
        if p.kind == "pipe":
            half = pipe_outside_diameter_m(p.diameter_m, material) / 2.0
        elif p.kind == "conduit":
            half = raceway_outside_diameter_m(p.diameter_m, material or "emt") / 2.0
        else:
            half = max(p.diameter_m, p.width_m, p.depth_m) / 2.0
        if len(p.points) >= 2:
            out.append((p.tag, tuple((x, y) for x, y, _z in p.points),
                        tuple(z for _x, _y, z in p.points), half))
    return out


def run_lines(model: Any, touch: frozenset[str], laid: Iterable[Line] = ()) -> list[Line]:
    """Every authored run but those in ``touch``, then ``laid``."""
    from typehaus.resolve.mep_envelopes import run_polylines, run_radii

    radii = run_radii(model)
    out: list[Line] = [(tag, path, z, radii.get(tag, 0.0))
                       for _kind, tag, path, z in run_polylines(model)
                       if tag not in touch and len(path) >= 2 and len(z) == len(path)]
    return [*out, *laid]


def crossings(lines: list[Line], floor: Any) -> list[tuple[str, float, Any]]:
    """``(tag, outside radius, MemberCrossing)`` for every line crossing ``floor``'s members."""
    from typehaus.resolve.mep_crossings import leg_crossings

    members = [m for m in floor.members if m.z0_m is not None]
    if not members:
        return []
    zlo = min(m.z0_m for m in members)
    zhi = max(getattr(m, "z1_m", None) or floor.deck_z0_m for m in members)
    xs = [v for m in members for v in (m.p0[0], m.p1[0])]
    ys = [v for m in members for v in (m.p0[1], m.p1[1])]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    out = []
    for tag, path, z, radius in lines:
        for k in range(len(path) - 1):
            (ax, ay), (bx, by) = path[k], path[k + 1]
            if (max(z[k], z[k + 1]) < zlo or min(z[k], z[k + 1]) > zhi
                    or max(ax, bx) < x0 or min(ax, bx) > x1
                    or max(ay, by) < y0 or min(ay, by) > y1):
                continue
            for crossing in leg_crossings(floor, path[k], path[k + 1], z[k], z[k + 1]):
                out.append((tag, radius, crossing))
    return out


def hole_index(lines: list[Line]) -> Callable[[Any, list[str]], list[list[tuple[float, float]]]]:
    """``(floor, member keys) -> per member [(station, outside radius)]`` of ``lines``' holes."""

    def holes(floor: Any, keys: list[str]) -> list[list[tuple[float, float]]]:
        index = {key: i for i, key in enumerate(keys)}
        out: list[list[tuple[float, float]]] = [[] for _ in keys]
        for _tag, radius, crossing in crossings(lines, floor):
            i = index.get(crossing.member_key)
            if i is not None:
                out[i].append((crossing.station_m, radius))
        return out

    return holes


def taken_pockets(lines: list[Line], floor: Any, members: list[Any]) -> list[dict[str, str]]:
    """Per member, its D pockets some line already passes through: key -> that line's tag."""
    from typehaus.resolve.open_web import run_of

    along_x = floor.direction == "x"
    index = {m.child_key: i for i, m in enumerate(members)}
    out: list[dict[str, str]] = [{} for _ in members]
    for tag, _radius, crossing in crossings(lines, floor):
        i = index.get(crossing.member_key)
        if i is None or members[i].web is None:
            continue
        opening = members[i].web.opening_at(run_of(members[i], crossing.station_m, along_x),
                                            crossing.z_m - members[i].z0_m)
        if opening is not None and opening.kind == "D":
            out[i].setdefault(opening.key, tag)
    return out


def web_refused(floor: Any, crossed: list[int], along: float, z: float,
                radius_m: float) -> bool:
    """Whether a crossing at ``along``, ``z`` misses every opening it fits (a web, a chord,
    a TrimEnd: ``open_web.grade_crossing``, the check's own verdict) or lands in a D pocket
    another run passes. The web prisms are the router's coarse reading; this is exact."""
    from typehaus.resolve.open_web import RunSize, grade_crossing, run_of

    along_x = floor.across == "y"
    size = RunSize(2 * radius_m, 2 * radius_m, True)
    for i in crossed:
        member = floor.parts[i]
        if member.web is None:
            continue
        grade = grade_crossing(member.web, run_of(member, along, along_x), z - member.z0_m,
                               size)
        if not grade.ok:
            return True
        if grade.opening.kind == "D" and grade.opening.key in floor.pockets[i]:
            return True
    return False


def ijoist_bores_ok(floor: Any, crossed: list[int], along: float, diameter_m: float) -> bool:
    """Every hole at ``along`` inside the I-joist chart's zone and clear of the other holes
    in the same joist: the check's own verdict, read the check's way."""
    from typehaus.resolve.mep_bores import joist_bore
    from typehaus.resolve.mep_hole_chart import DRILLED_HOLE_CLEARANCE_IN

    chart = getattr(floor, "chart", None)
    half = DRILLED_HOLE_CLEARANCE_IN * M_PER_IN / 2.0
    for i in crossed:
        lo, hi = floor.faces[i]
        if lo is None or hi is None:
            return False
        centre_in = min(along - lo, hi - along) / M_PER_IN
        nearest = nearest_d = None
        for station, other_r in floor.holes[i]:
            clear = (abs(station - along) - diameter_m / 2.0 - other_r - 2 * half) / M_PER_IN
            if nearest is None or clear < nearest:
                nearest, nearest_d = clear, 2 * (other_r + half) / M_PER_IN
        verdict = joist_bore(getattr(floor, "profile", ""), diameter_m / M_PER_IN,
                             chart=chart, edge_to_support_in=centre_in,
                             nearest_cut_in=nearest, nearest_diameter_in=nearest_d)
        if verdict.ok is not True:
            return False
    return True
