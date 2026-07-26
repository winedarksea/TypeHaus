"""Stair structural guard passes: the subfloor clip and the wall-bearing pass."""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.model.enums import StructuralRole
from typehaus.model.spatial import Stair
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedModel
from typehaus.resolve.stairs.common import _MIN_SHARED_RUN_M, _TREAD_THICKNESS_M

# The 2x board a framer lags to a framed host wall's face for a stringer/rim to bear on.
_LEDGER_PROFILE = "2x10"


def _clip_stair_to_subfloor(members: tuple[FramedMember, ...],
                            subfloor: float) -> tuple[FramedMember, ...]:
    """Clamp generated stair framing to the subfloor the flight springs from.

    The U-stair well partition (and any carriage member) bears on the first framed deck
    and must never drop into the foundation below it. This is the clip guard the audit
    called for; for a flight already sized off that deck it is a no-op backstop.
    """
    out: list[FramedMember] = []
    for member in members:
        z0 = max(member.z0_m, subfloor)
        z1 = max(member.z1_m, subfloor)
        z0e = None if member.z0_end_m is None else max(member.z0_end_m, subfloor)
        z1e = None if member.z1_end_m is None else max(member.z1_end_m, subfloor)
        if (z0, z1, z0e, z1e) == (member.z0_m, member.z1_m, member.z0_end_m, member.z1_end_m):
            out.append(member)
        else:
            out.append(replace(member, z0_m=z0, z1_m=z1, z0_end_m=z0e, z1_end_m=z1e))
    return tuple(out)


def _wall_run_overlap(wall, p0: tuple[float, float], p1: tuple[float, float]
                      ) -> tuple[float, float, tuple[float, float]] | None:
    """Geometry of an axis-aligned member p0→p1 lying along ``wall``'s axis.

    Returns ``(offset, shared_run, (lo, hi))`` — the perpendicular distance from the
    member to the wall axis, the length they share, and the shared interval in the run
    coordinate — or ``None`` when the two are not colinear-parallel at all.
    """
    (wx0, wy0), (wx1, wy1) = wall.axis
    if abs(wx1 - wx0) < 1e-6 and abs(p1[0] - p0[0]) < 1e-6:  # both run in y
        offset = abs(p0[0] - wx0)
        lo, hi = sorted((p0[1], p1[1]))
        wlo, whi = sorted((wy0, wy1))
    elif abs(wy1 - wy0) < 1e-6 and abs(p1[1] - p0[1]) < 1e-6:  # both run in x
        offset = abs(p0[1] - wy0)
        lo, hi = sorted((p0[0], p1[0]))
        wlo, whi = sorted((wx0, wx1))
    else:
        return None
    shared_lo, shared_hi = max(lo, wlo), min(hi, whi)
    return offset, shared_hi - shared_lo, (shared_lo, shared_hi)


def _best_host_wall(model: ResolvedModel, stair: Stair, p0: tuple[float, float],
                    p1: tuple[float, float]):
    """The wall a stair member p0→p1 bears on, or ``(None, None)``.

    Three independent gates, all required:

    1. **Bearing intent** — the wall is foundation concrete, is authored
       ``StructuralRole.BEARING``, or is named in the stair's ``bearing_refs``. A
       non-bearing partition beside a flight carries nothing.
    2. **Geometry** — the member sits within half the wall's own depth (plus a tread
       board) of its axis. An axis is a *centreline*, so this is the wall's real reach;
       the flat 0.20 m it replaces let a 4.75" partition 4" away read as a host.
    3. **Shared run** — they overlap by more than ``_MIN_SHARED_RUN_M``.

    Survivors rank by foundation first (concrete beats framing under the same member),
    then by the longest shared run, then by the closest axis — the old first-match-wins
    ``next()`` picked whichever wall happened to be declared first, which on catlin meant
    a 4" clip of ``W-M-C4B`` beat 5'-8" of ``W-M-C5``.

    Returns ``(wall, shared_interval)`` so the caller can tell which member endpoints the
    host actually reaches.
    """
    ranked = []
    for wall in model.walls:
        if wall.storey != stair.from_storey:
            continue
        if not (wall.is_foundation or wall.tag in stair.bearing_refs
                or _authored_is_bearing(model, wall.tag)):
            continue
        overlap = _wall_run_overlap(wall, p0, p1)
        if overlap is None:
            continue
        offset, shared_run, interval = overlap
        if offset > wall.thickness_m / 2 + _TREAD_THICKNESS_M:
            continue
        if shared_run <= _MIN_SHARED_RUN_M:
            continue
        ranked.append((not wall.is_foundation, -shared_run, offset, wall.tag, wall, interval))
    if not ranked:
        return None, None
    best = min(ranked, key=lambda entry: entry[:4])
    return best[4], best[5]


def _authored_is_bearing(model: ResolvedModel, tag: str) -> bool:
    """``ResolvedWall`` drops the authored structural role, so read it off the plan."""
    authored = model.plan.by_tag(tag)
    return getattr(authored, "structural_role", None) is StructuralRole.BEARING


def _face_line(host, member: FramedMember, board_width: float, lo: float,
               hi: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """``(a, b)`` for a board flush against ``host``'s near face, spanning ``lo``→``hi``.

    Where the wall's depth actually sits is read off the resolved layer polygons rather
    than from ``axis``: an ``alignment=face(...)`` wall's authored line is one of its
    *faces*, not its centre, so ``axis ± thickness/2`` lands mid-wall and the board bites
    into the studs on one side (and floats outside the building on the other).

    Both host kinds go through here. A framed wall gets a lagged ledger board; concrete
    gets the hanger band let into the pour — but neither is fastened along the *stringer's*
    own centreline, which for a flight clipped to its subfloor made the band a byte-for-byte
    duplicate of the member it carries.
    """
    # 0 → the member runs in x (cross coordinate is y); 1 → it runs in y (cross is x).
    run_axis = 1 if abs(member.p1[0] - member.p0[0]) < 1e-6 else 0
    cross_axis = 1 - run_axis
    cross = [point[cross_axis] for layer in host.depth_layers() for point in layer.polygon]
    if cross:
        near, far = min(cross), max(cross)
        face = (far + board_width / 2.0
                if member.p0[cross_axis] >= (near + far) / 2.0
                else near - board_width / 2.0)
    else:  # no resolved depth (a bare axis): fall back to the authored line
        wall_cross = host.axis[0][cross_axis]
        side = 1.0 if member.p0[cross_axis] >= wall_cross else -1.0
        face = wall_cross + side * (host.thickness_m / 2.0 + board_width / 2.0)
    if run_axis == 1:
        return (face, lo), (face, hi)
    return (lo, face), (hi, face)


def _framed_ledger(stair: Stair, host, member: FramedMember,
                   interval: tuple[float, float], subfloor: float,
                   connection: str) -> FramedMember:
    """The ledger board a framed host wall carries ``member`` on.

    Two deliberate differences from the concrete hanger band (both share ``_face_line``'s
    plan position, flush against the host's face on the member's side):

    - **Span** — exactly the run interval the host shares with the member
      (``_best_host_wall``'s third gate measured it); a board spanning the member's full
      run would float past the end of the wall that carries it.
    - **Top** — tracks the member top *interpolated at the interval ends*, so a ledger
      under a partially-carried raked stringer bears where that stretch of stringer
      actually is, clamped at the subfloor like every stair member.
    """
    section = cross_section(_LEDGER_PROFILE)
    lo, hi = interval
    run_axis = 1 if abs(member.p1[0] - member.p0[0]) < 1e-6 else 0
    a, b = _face_line(host, member, section.width_m, lo, hi)
    # The member's top along its run: z1_m at p0, z1_end_m (raked) or z1_m at p1.
    s0, s1 = member.p0[run_axis], member.p1[run_axis]
    top0 = member.z1_m
    top1 = member.z1_m if member.z1_end_m is None else member.z1_end_m

    def top_at(s: float) -> float:
        if abs(s1 - s0) < 1e-9:
            return max(top0, top1)
        return top0 + (top1 - top0) * (s - s0) / (s1 - s0)

    top_lo, top_hi = top_at(lo), top_at(hi)
    return FramedMember(
        stair.uid, f"ledger-{host.tag}-{member.child_key}", "hanger", _LEDGER_PROFILE,
        a, b, max(subfloor, top_lo - section.depth_m), top_lo, hi - lo,
        z0_end_m=max(subfloor, top_hi - section.depth_m), z1_end_m=top_hi,
        connection=connection)


def _bear_stair_on_walls(model: ResolvedModel, stair: Stair,
                         members: tuple[FramedMember, ...],
                         subfloor: float) -> tuple[FramedMember, ...]:
    """Give the flight a resolvable load path against the walls it runs beside.

    A stair does not float: its outer stringers and its landing rims run against the
    walls flanking the well, and whatever they miss has to be posted down to the deck
    the flight springs from. Two host kinds, deliberately different:

    - **Foundation concrete** — the stringer/rim is carried on a wall-mounted
      (joist-hanger-style) ledger let into the pour. Annotated
      ``concrete-wall-hanger:{tag}`` *and* given a hanger band as connector geometry, so
      the bearing reads structurally. The band tracks the raked stringer top
      (``z1_m``/``z1_end_m``), so a lower-flight hanger bears at the landing and an
      upper-flight hanger at the arrival deck — never at ``max(z0, z1)`` of a full prism.
    - **Framed wall** — annotated ``framed-wall-ledger:{tag}`` *and* given a real ledger
      board (``_LEDGER_PROFILE``) as connector geometry. A wall ``axis`` is its
      *centreline*, so the board is NOT drawn there (that would be geometry invented
      inside the stud cavity — plans/TODO.md D3); it sits flush against the host's face
      on the member's side, spans exactly the run the host shares with the member, and
      its top tracks the (possibly raked) member top the way the concrete hanger band
      does. Category ``hanger`` on purpose: the interference rules and the hardware
      takeoff already treat that category as a stair-carriage connector, and the
      ``ledger-`` child-key prefix keeps the two kinds tellable apart.

    Any landing corner no host wall reaches gets a vertical 4x4 post to the subfloor.
    """
    hanger_depth = 0.2032  # 8" ledger band

    def corner_key(point: tuple[float, float]) -> tuple[float, float]:
        return (round(point[0], 4), round(point[1], 4))

    def covered_ends(member: FramedMember,
                     interval: tuple[float, float]) -> list[tuple[float, float]]:
        """The member's endpoints the host wall's shared run actually reaches.

        ``interval`` is in the member's run axis — y for a member running in y, x for one
        running in x — matching what ``_wall_run_overlap`` measured.
        """
        axis = 1 if abs(member.p1[0] - member.p0[0]) < 1e-6 else 0
        return [point for point in (member.p0, member.p1)
                if interval[0] - 1e-6 <= point[axis] <= interval[1] + 1e-6]

    out: list[FramedMember] = []
    rims_by_platform: dict[str, list[FramedMember]] = {}
    supported_corners: set[tuple[float, float]] = set()
    for member in members:
        if member.category == "landing" and member.child_key.startswith("landing-rim-"):
            rims_by_platform.setdefault(member.child_key.rsplit("-", 1)[0],
                                        []).append(member)
        bearable = (member.category == "stringer"
                    or (member.category == "landing"
                        and (member.child_key.startswith("landing-rim-")
                             or member.child_key.startswith("landing-joist-"))))
        if bearable and member.p0 != member.p1:
            host, interval = _best_host_wall(model, stair, member.p0, member.p1)
            if host is not None and not host.is_foundation:
                tag = f"framed-wall-ledger:{host.tag}"
                out.append(replace(member, connection=tag))
                out.append(_framed_ledger(stair, host, member, interval, subfloor, tag))
                if member.category == "landing":
                    # Only the endpoints the wall actually runs past are carried; a host
                    # that overlaps half a rim leaves the far corner needing a post.
                    supported_corners.update(
                        corner_key(point) for point in covered_ends(member, interval))
                continue
            if host is not None:
                tag = f"concrete-wall-hanger:{host.tag}"
                out.append(replace(member, connection=tag))
                run_axis = 1 if abs(member.p1[0] - member.p0[0]) < 1e-6 else 0
                band_a, band_b = _face_line(
                    host, member, cross_section("hanger").width_m,
                    member.p0[run_axis], member.p1[run_axis])
                if member.category == "stringer":
                    top_p0 = member.z1_m
                    top_p1 = member.z1_m if member.z1_end_m is None else member.z1_end_m
                    out.append(FramedMember(
                        stair.uid, f"hanger-{host.tag}-{member.child_key}", "hanger",
                        "hanger", band_a, band_b,
                        max(subfloor, top_p0 - hanger_depth), top_p0, member.length_m,
                        z0_end_m=max(subfloor, top_p1 - hanger_depth), z1_end_m=top_p1,
                        connection=tag))
                else:
                    out.append(FramedMember(
                        stair.uid, f"hanger-{host.tag}-{member.child_key}", "hanger",
                        "hanger", band_a, band_b,
                        max(subfloor, member.z1_m - hanger_depth), member.z1_m,
                        member.length_m, connection=tag))
                    supported_corners.update(
                        corner_key(point) for point in covered_ends(member, interval))
                continue
        out.append(member)
    # Any platform corner not on a ledgered edge bears on a 4x4 post to the subfloor.
    # The two rims' endpoints are exactly the platform's four corners; the corner shared
    # by both half-width platforms gets one post, sized to the higher platform.
    posts: dict[tuple[float, float], float] = {}
    for rims in rims_by_platform.values():
        z_top = min(rim.z0_m for rim in rims)  # underside of the platform framing
        for rim in rims:
            for point in (rim.p0, rim.p1):
                key = corner_key(point)
                if key in supported_corners:
                    continue
                posts[key] = max(posts.get(key, z_top), z_top)
    orient = (1.0, 0.0) if stair.run_direction == "x" else (0.0, 1.0)
    for index, (key, z_top) in enumerate(sorted(posts.items())):
        if z_top <= subfloor + 1e-9:
            continue
        out.append(FramedMember(stair.uid, f"landing-post-{index:03d}", "landing", "4x4",
                                key, key, subfloor, z_top, z_top - subfloor,
                                orient=orient))
    return tuple(out)
