"""Every stair landing rim end has a support, and a hung one its hanger's capacity.

A rim end is carried by one of: a hanger on an authored column face (graded against the
part's published floor-column download, SPF row), the wall it is fastened along, a post
under it with IRC R502.6's 1 1/2" of bearing, or the wall-carried member it frames into at a
corner. A rim running into a column, or an end on none of these, FAILs. Winder boxes bear
through their own decks and are out of scope. Hand check:
houses/catlin/notes/stair_landing_post_hangers.md.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.stair_stringers import _DEAD_PSF, _LIVE_PSF
from typehaus.findings import Finding, Result, not_applicable
from typehaus.quantities import M_PER_FT, M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedStair

CHECK_ID = "structural.landing_rim_support"
_R502_6_MIN_BEARING_IN = 1.5  # IRC R502.6: 1 1/2" on wood or metal
_R502_6 = "IRC R502.6"
_WALL_CARRIED = ("framed-wall-ledger:", "concrete-wall-hanger:", "framed-wall-spacer:")
_PSF_TO_PA = 47.880259
_N_PER_LB = 4.448222
_TOL = 1e-4
_NEAR_M = 2 * M_PER_IN  # a stringer end this close to a member's depth bears on it


def _rims(stair: ResolvedStair) -> list[FramedMember]:
    return [m for m in stair.members if m.child_key.startswith("landing-rim-")
            and not m.child_key.startswith("landing-rim-winder") and m.p0 != m.p1]


def _run_axis(member: FramedMember) -> int:
    return 0 if abs(member.p1[0] - member.p0[0]) >= abs(member.p1[1] - member.p0[1]) else 1


def _half(member: FramedMember) -> float:
    return (member.plan_width_m or cross_section(member.profile).width_m) / 2.0


def _box(outline) -> tuple[float, float, float, float]:
    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    return min(xs), min(ys), max(xs), max(ys)


def _into_column(rim: FramedMember, columns) -> str | None:
    """The column a rim's own footprint runs into, if any (more than a hair of overlap)."""
    axis = _run_axis(rim)
    lo, hi = sorted((rim.p0[axis], rim.p1[axis]))
    c, half = rim.p0[1 - axis], _half(rim)
    for solid in columns:
        box = _box(solid.outline)
        if rim.z0_m >= solid.z1_m - _TOL or rim.z1_m <= solid.z0_m + _TOL:
            continue
        run = min(hi, box[axis + 2]) - max(lo, box[axis])
        side = min(c + half, box[3 - axis]) - max(c - half, box[1 - axis])
        if run > M_PER_IN / 16 and side > M_PER_IN / 16:
            return solid.tag
    return None


def _post_bearing_in(rim: FramedMember, end, boxes) -> tuple[str, float] | None:
    """The best ``(label, bearing in)`` of a post topping out under this rim end."""
    axis = _run_axis(rim)
    lo, hi = sorted((rim.p0[axis], rim.p1[axis]))
    best = None
    for label, box, top in boxes:
        if abs(top - rim.z0_m) > M_PER_IN / 8:
            continue
        if not box[1 - axis] - _TOL <= end[1 - axis] <= box[3 - axis] + _TOL:
            continue
        if not box[axis] - _TOL <= end[axis] <= box[axis + 2] + _TOL:
            continue
        bearing = (min(hi, box[axis + 2]) - max(lo, box[axis])) / M_PER_IN
        if best is None or bearing > best[1]:
            best = (label, bearing)
    return best


def _framed_into(stair: ResolvedStair, rim: FramedMember, end) -> str | None:
    """A wall-carried member of the stair the rim end butts at a corner, level with it."""
    axis = _run_axis(rim)
    for other in stair.members:
        if (other is rim or other.p0 == other.p1 or _run_axis(other) == axis
                or not (other.connection or "").startswith(_WALL_CARRIED)
                or abs(other.z1_m - rim.z1_m) > M_PER_IN / 8):
            continue
        lo, hi = sorted((other.p0[1 - axis], other.p1[1 - axis]))
        if (abs(end[axis] - other.p0[axis]) <= _half(other) + _TOL
                and lo - _TOL <= end[1 - axis] <= hi + _TOL):
            return other.child_key
    return None


def _wall_reaches(ctx: CheckContext, stair: ResolvedStair, rim: FramedMember, end) -> bool:
    """The rim's own host wall (or its ledger board) runs past this end."""
    connection = rim.connection or ""
    if not connection.startswith(_WALL_CARRIED):
        return False
    axis = _run_axis(rim)
    host = connection.split(":", 1)[1]
    board = next((m for m in stair.members if m.child_key.endswith(f"-{host}-{rim.child_key}")
                  and m.category == "hanger"), None)
    if board is not None:
        lo, hi = sorted((board.p0[axis], board.p1[axis]))
    else:  # the rim is its own ledger: read the wall's run the way resolve did
        from typehaus.resolve.stairs.bearing import _best_host_wall

        plan_stair = ctx.model.plan.by_tag(stair.tag)
        wall, interval = _best_host_wall(ctx.model, plan_stair, rim.p0, rim.p1)
        if wall is None:
            return False
        lo, hi = interval
    return lo - 1e-3 <= end[axis] <= hi + 1e-3


def _hung_reaction_lb(stair: ResolvedStair, member: FramedMember, end) -> float:
    """(D + L) at a hung end, lever-ruled: a joist's uniform strip plus the stringer feet on
    it; a rim's joists framing into it (never less than its half-joist strip, smeared)."""
    psf = _LIVE_PSF + _DEAD_PSF
    length = math.dist(member.p0, member.p1)
    name = member.child_key.split("-")[2]
    joists = [m for m in stair.members if m.child_key.startswith(f"landing-joist-{name}-")
              and m.p0 != m.p1]
    if member.child_key.startswith("landing-rim-"):
        width = max((math.dist(j.p0, j.p1) for j in joists), default=0.0) / 2.0
        smeared = psf * _PSF_TO_PA * width * length / 2.0 / _N_PER_LB
        point = sum(_hung_reaction_lb(stair, joist, foot)
                    * _lever(member, foot, end, length)
                    for joist in joists for foot in (joist.p0, joist.p1)
                    if _lands_on(member, foot))
        return max(smeared, point)
    axis = _run_axis(member)
    here = member.p0[1 - axis]
    stations = [m.p0[1 - axis] for m in joists if abs(m.p0[1 - axis] - here) > _TOL]
    below = [here - s for s in stations if s < here]
    above = [s - here for s in stations if s > here]
    width = ((min(below) / 2.0 if below else _half(member))
             + (min(above) / 2.0 if above else _half(member)))
    uniform = psf * _PSF_TO_PA * width * length / 2.0
    point = 0.0
    for flight in _flights(stair).values():
        for stringer, tributary_m in flight:
            ends = ((stringer.p0, stringer.z0_m, stringer.z1_m),
                    (stringer.p1, _or(stringer.z0_end_m, stringer.z0_m),
                     _or(stringer.z1_end_m, stringer.z1_m)))
            for foot, z0, z1 in ends:
                if abs(foot[1 - axis] - here) > _half(member) + 1.5 * M_PER_IN:
                    continue
                if z1 < member.z0_m - _NEAR_M or z0 > member.z1_m + _NEAR_M:
                    continue  # a flight on another landing over the same plan point
                lo, hi = sorted((member.p0[axis], member.p1[axis]))
                if not lo - _TOL <= foot[axis] <= hi + _TOL:
                    continue
                run = math.dist(stringer.p0, stringer.p1)
                load = psf * _PSF_TO_PA * tributary_m * run / 2.0
                point += load * _lever(member, foot, end, length)
    return (uniform + point) / _N_PER_LB


def _or(value: float | None, default: float) -> float:
    return default if value is None else value


def _lever(member: FramedMember, at, end, length: float) -> float:
    """The share of a load at ``at`` that reaches ``end`` of a simple span."""
    axis = _run_axis(member)
    return max(0.0, 1.0 - abs(at[axis] - end[axis]) / max(length, 1e-9))


def _lands_on(rim: FramedMember, foot) -> bool:
    """A joist end inside the rim's run, on its line (the joists run to its centreline)."""
    axis = _run_axis(rim)
    lo, hi = sorted((rim.p0[axis], rim.p1[axis]))
    return (abs(foot[1 - axis] - rim.p0[1 - axis]) <= _half(rim) + _TOL
            and lo + _TOL < foot[axis] < hi - _TOL)


def _flights(stair: ResolvedStair) -> dict[str, list[tuple[FramedMember, float]]]:
    """Stringers by flight, each with its tributary width (midpoints; outer faces at ends)."""
    groups: dict[str, list[FramedMember]] = {}
    for member in stair.members:
        if member.category == "stringer":
            groups.setdefault(member.child_key.rsplit("-", 1)[0], []).append(member)
    out = {}
    for key, stringers in groups.items():
        axis = 1 - _run_axis(stringers[0])
        ordered = sorted(stringers, key=lambda m: m.p0[axis])
        cross = [m.p0[axis] for m in ordered]
        rows = []
        for index, member in enumerate(ordered):
            left = ((cross[index] + cross[index - 1]) / 2.0 if index
                    else cross[index] - _half(member))
            right = ((cross[index] + cross[index + 1]) / 2.0 if index + 1 < len(cross)
                     else cross[index] + _half(member))
            rows.append((member, right - left))
        out[key] = rows
    return out


@check(Tier.STRUCTURAL, CHECK_ID)
def landing_rim_support(ctx: CheckContext) -> list[Finding]:
    """Grade every U-stair landing rim end's support (IRC R502.6, the hanger's table)."""
    from typehaus.hardware.catalog import allowable_for_model
    from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG
    from typehaus.joints.authored import hanger_part, hanger_specs
    from typehaus.joints.column_hung import column_hung_connections

    stairs = [(stair, _rims(stair)) for stair in ctx.model.stairs]
    if not any(rims for _, rims in stairs):
        return [not_applicable(CHECK_ID, "no stair has a framed landing platform")]
    rules = DEFAULT_HARDWARE_TAKEOFF_CONFIG.hanger_detection
    hung = {}
    for connection in column_hung_connections(ctx.model, rules):
        hung.setdefault(connection.member_key, []).append(connection)
    specs = hanger_specs(ctx.model)
    columns = [s for s in ctx.model.solids if s.category == "column" and s.outline]
    out: list[Finding] = []
    for stair, rims in stairs:
        posts = [(m.child_key, (m.p0[0] - _half(m), m.p0[1] - _half(m),
                                m.p0[0] + _half(m), m.p0[1] + _half(m)), m.z1_m)
                 for m in stair.members if m.p0 == m.p1 and m.category == "landing_framing"]
        posts += [(s.tag, _box(s.outline), s.z1_m) for s in columns]
        hung_members = {m.child_key: m for m in stair.members
                        if f"{m.parent_uid}:{m.child_key}" in hung}
        for rim in rims:
            label = f"{stair.tag}:{rim.child_key}"
            column = _into_column(rim, columns)
            if column is not None:
                out.append(_advisory(CHECK_ID, f"{label} runs into column {column}",
                                     (stair.tag, column), Result.FAIL,
                                     "stop the rim at the column faces and hang each end",
                                     code=_R502_6))
                continue
            for end in (rim.p0, rim.p1):
                out.append(_end_finding(ctx, stair, rim, end, label, posts))
        for key, member in sorted(hung_members.items()):
            for connection in hung[f"{member.parent_uid}:{key}"]:
                _role, item, part = hanger_part(connection, specs)
                allowable = allowable_for_model(part) or item.allowable
                demand = _hung_reaction_lb(stair, member, _hung_end(member, connection))
                capacity = allowable.download_lb if allowable else None
                tags = (stair.tag, connection.carrier_tag)
                where = f"{stair.tag}:{key} on {connection.carrier_tag} ({part})"
                if capacity is None:
                    out.append(_advisory(CHECK_ID, f"{where}: no published download",
                                         tags, Result.UNKNOWN))
                    continue
                result = Result.PASS if demand <= capacity else Result.FAIL
                out.append(_advisory(
                    CHECK_ID, f"{where}: {demand:.0f} lb (D+L {_DEAD_PSF + _LIVE_PSF:g} psf) "
                    f"vs {capacity:.0f} lb floor (100), d/c {demand / capacity:.2f}",
                    tags, result, code="Simpson C-C-2026 SPF/HF face-mount table"))
    return out


def _hung_end(member: FramedMember, connection):
    """The member end the hung connection names (the one it leaves the face from)."""
    into = connection.outward_xy or (0.0, 0.0)
    return member.p0 if (member.p1[0] - member.p0[0]) * into[0] + (
        member.p1[1] - member.p0[1]) * into[1] > 0 else member.p1


def _end_finding(ctx, stair, rim, end, label, posts) -> Finding:
    from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG
    from typehaus.joints.column_hung import _column_face_under

    feet = f"({end[0] / M_PER_FT:.2f}', {end[1] / M_PER_FT:.2f}')"
    columns = [s for s in ctx.model.solids
               if s.category in DEFAULT_HARDWARE_TAKEOFF_CONFIG.hanger_detection
               .carrier_column_categories and s.outline]
    other = rim.p1 if end is rim.p0 else rim.p0
    run = math.dist(end, other)
    into = ((other[0] - end[0]) / run, (other[1] - end[1]) / run)
    column = _column_face_under(columns, end, into, 2 * _half(rim), rim)
    if column is not None:
        return _advisory(CHECK_ID, f"{label} end {feet} hangs on {column.tag}'s face",
                         (stair.tag, column.tag), Result.PASS, code=_R502_6)
    if _wall_reaches(ctx, stair, rim, end):
        return _advisory(CHECK_ID, f"{label} end {feet} is fastened along "
                         f"{rim.connection.split(':', 1)[1]} (that fastening is not graded "
                         "here)", (stair.tag,), Result.PASS, code=_R502_6)
    post = _post_bearing_in(rim, end, posts)
    if post is not None:
        result = Result.PASS if post[1] >= _R502_6_MIN_BEARING_IN - 1e-6 else Result.FAIL
        return _advisory(CHECK_ID, f"{label} end {feet} bears {post[1]:.2f}\" on {post[0]} "
                         f"(IRC R502.6 min {_R502_6_MIN_BEARING_IN}\")", (stair.tag,), result,
                         "set the post under the rim end for 1 1/2\" of bearing",
                         code=_R502_6)
    corner = _framed_into(stair, rim, end)
    if corner is not None:
        return _advisory(CHECK_ID, f"{label} end {feet} frames into wall-carried {corner}",
                         (stair.tag,), Result.PASS, code=_R502_6)
    return _advisory(CHECK_ID, f"{label} end {feet} bears on nothing", (stair.tag,),
                     Result.FAIL, "post the corner, hang it on a column face or ledger it",
                     code=_R502_6)
