"""Stair structural guard passes: the subfloor clip and the wall-bearing pass."""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.model.enums import StructuralRole
from typehaus.model.spatial import Stair
from typehaus.resolve.model import FramedMember, ResolvedModel
from typehaus.resolve.stairs.common import _MIN_SHARED_RUN_M, _TREAD_THICKNESS_M


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
    - **Framed wall** — annotated ``framed-wall-ledger:{tag}`` and nothing else. A wall
      ``axis`` is its *centreline*, so a band drawn on it would be geometry invented
      inside the stud cavity; the ledger the framer actually installs waits on insetting
      stair members to the host's finished face (see plans/TODO.md D3).

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
                out.append(replace(member, connection=f"framed-wall-ledger:{host.tag}"))
                if member.category == "landing":
                    # Only the endpoints the wall actually runs past are carried; a host
                    # that overlaps half a rim leaves the far corner needing a post.
                    supported_corners.update(
                        corner_key(point) for point in covered_ends(member, interval))
                continue
            if host is not None:
                tag = f"concrete-wall-hanger:{host.tag}"
                out.append(replace(member, connection=tag))
                if member.category == "stringer":
                    top_p0 = member.z1_m
                    top_p1 = member.z1_m if member.z1_end_m is None else member.z1_end_m
                    out.append(FramedMember(
                        stair.uid, f"hanger-{host.tag}-{member.child_key}", "hanger",
                        "hanger", member.p0, member.p1,
                        max(subfloor, top_p0 - hanger_depth), top_p0, member.length_m,
                        z0_end_m=max(subfloor, top_p1 - hanger_depth), z1_end_m=top_p1,
                        connection=tag))
                else:
                    out.append(FramedMember(
                        stair.uid, f"hanger-{host.tag}-{member.child_key}", "hanger",
                        "hanger", member.p0, member.p1,
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
