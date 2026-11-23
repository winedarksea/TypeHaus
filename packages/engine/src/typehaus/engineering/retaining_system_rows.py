"""The court's load path rows: the strut, and the footings in plan (free body §8, §15).

The sliding rows answer whether the body moves. These answer whether the thrusts reach the
bases that resist them:

* ``strut compression`` — the cross-member between the two side legs, ACI 318-19 §14.5.4,
  at the f'c its own assembly specifies. Its force is the continuous-beam reaction of the two
  footing spans it props: the retaining leg, and the braced leg spliced on beyond it.
* ``footing plan bending`` — each side footing spans in plan from FT-SG-S to the strut,
  carrying its wall's whole thrust (its base friction is spent north-south by the sliding
  row, so none is credited east-west). A deep beam (ACI 318-19 §9.9.1.1), graded by strut and
  tie (Ch. 23): the load enters along the stem, so the arch rises from the stem line to the
  tie at the toe edge, phi 0.75 on the bars in that tie.
* ``corner delivery`` — the unopposed footing in plan between the side footings, carrying
  its thrust less its own base friction (which points along that thrust, the direction the
  sliding row spends it in), the same strut and tie.

All three are strength rows at 1.6H (IBC §1605.2); the sliding rows are service FS.
"""

from __future__ import annotations

from typehaus.engineering.item import LimitState
from typehaus.engineering.retaining_basis import (
    EARTH_PRESSURE_LOAD_FACTOR,
    PRESUMPTIVE_FC_PSI,
    REINFORCEMENT_FY_PSI,
    _geometry,
    _structure_thickness_in,
)

_M = 0.3048
#: ACI 318-19 §14.5.4 plain wall axial strength coefficient (``0.45 f'c Ag``); §14.5.6 is
#: BEARING (0.85) and is the wrong section.
STRUT_STRESS_COEFFICIENT = 0.45
#: ACI 318-19 Table 21.2.1: plain concrete 0.60; strut-and-tie 0.75.
PHI_PLAIN = 0.60
PHI_STM = 0.75
#: A propped leg's share of its own thrust at the prop: fully fixed corner 3/8, pinned 1/2.
STRUT_PROP_SHARE = (0.375, 0.500)
_LONGITUDINAL = ("bottom-y", "edge-y")


def cross_axis(ctx, cross):  # type: ignore[no-untyped-def]
    """The cross-member's plan axis, metres: a wall's resolved axis or a cast beam's
    centreline off its resolved solid."""
    resolved = next((w for w in ctx.model.walls if w.tag == cross.tag), None)
    if resolved is not None:
        return resolved.axis
    solid = next((s for s in ctx.model.solids
                  if s.tag == cross.tag and s.category == "beam"), None)
    if solid is None or len(solid.outline) != 4:
        return None
    a, b, c, d = solid.outline
    return (((a[0] + d[0]) / 2, (a[1] + d[1]) / 2), ((b[0] + c[0]) / 2, (b[1] + c[1]) / 2))


def cross_section_in(ctx, cross) -> tuple[float, float]:  # type: ignore[no-untyped-def]
    """``(thickness, height)`` of the cross-member, inches; zero where unstated."""
    from typehaus.model.structure import Beam
    from typehaus.resolve.framing.profiles import cross_section

    if isinstance(cross, Beam):
        cs = cross_section(cross.size)
        return cs.width_m / _M * 12.0, cs.depth_m / _M * 12.0
    thickness_in = _structure_thickness_in(ctx, cross.assembly) or 0.0
    height_in = 0.0
    if cross.top_elevation is not None and cross.bottom_elevation is not None:
        height_in = cross.top_elevation.inches - cross.bottom_elevation.inches
    return thickness_in, height_in


def cross_span_ft(ctx, cross) -> float:  # type: ignore[no-untyped-def]
    axis = cross_axis(ctx, cross)
    if axis is None:
        return 0.0
    (x0, y0), (x1, y1) = axis
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / _M


def _unit(axis):  # type: ignore[no-untyped-def]
    (x0, y0), (x1, y1) = axis
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    return ((x1 - x0) / length, (y1 - y0) / length) if length else None


def cross_fc(ctx, cross) -> tuple[float, str]:  # type: ignore[no-untyped-def]
    """The f'c the cross-member's own assembly specifies, else the code floor (named)."""
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi

    fc = fc_psi(concrete_spec_for(ctx.plan, cross))
    if fc:
        return fc, f"f'c {fc:,.0f} as specified"
    return PRESUMPTIVE_FC_PSI, f"f'c {PRESUMPTIVE_FC_PSI:,.0f} presumptive (none specified)"


def _braced_leg(ctx, braced, efp: float):  # type: ignore[no-untyped-def]
    """``(w plf, span ft, tag)`` for a spliced braced wall propped by the cross-member: its
    whole at-rest thrust to the underside of its footing (none taken by its top brace), over
    its footing's span along the wall. Its retained height is authored or read off grade."""
    from typehaus.engineering.retaining_system_body import _footing_of, _poly, _solid

    footing = _footing_of(ctx, braced.tag)
    solid = _solid(ctx, footing.tag, "footing") if footing else None
    resolved = next((w for w in ctx.model.walls if w.tag == braced.tag), None)
    if solid is None or resolved is None:
        return None
    if braced.unbalanced_fill is not None:
        fill = braced.unbalanced_fill.meters
    else:
        grade = ctx.plan.project.site.grade
        if grade is None:
            return None
        fill = max(0.0, min(grade.meters, braced.top_elevation.meters)
                   - braced.bottom_elevation.meters)
    height = fill / _M + footing.depth.meters / _M
    u = _unit(tuple((a / _M, b / _M) for a, b in resolved.axis))
    poly = _poly(solid.outline)
    proj = [x * u[0] + y * u[1] for x, y in poly.exterior.coords]
    return 0.5 * efp * height * height, max(proj) - min(proj), braced.tag


def strut(ctx, cross, body, braced: list, members) -> LimitState | None:  # type: ignore[no-untyped-def]
    """``strut compression``: the larger side's continuous two-span reaction at the prop."""
    from typehaus.engineering.retaining_system_body import DRY

    thickness, height = cross_section_in(ctx, cross)
    axis = cross_axis(ctx, cross)
    u = _unit(axis) if axis else None
    if u is None or not thickness or not height:
        return None
    fc, fc_how = cross_fc(ctx, cross)
    best = None
    for push, member in zip(body.pushes, members, strict=True):
        along = abs(push.direction[0] * u[0] + push.direction[1] * u[1])
        if along < 0.5:
            continue
        w1, l1 = body.thrust_per_ft(push, DRY) * along, member.length_ft
        legs = [leg for b in braced if (leg := _braced_leg(ctx, b, push.efp))
                and _shares_line(ctx, b, member.tag)]
        w2, l2, tag2 = legs[0] if legs else (0.0, 0.0, "")
        simple = 0.5 * w1 * l1 + 0.5 * w2 * l2
        moment = (w1 * l1 ** 3 + w2 * l2 ** 3) / (8.0 * (l1 + l2)) if l2 else 0.0
        reaction = simple + (moment / l1 + moment / l2 if l2 else 0.0)
        if best is None or reaction > best[0]:
            best = (reaction, simple, member.tag, tag2, w1, l1, w2, l2)
    if best is None:
        return None
    reaction, simple, tag1, tag2, w1, l1, w2, l2 = best
    span = cross_span_ft(ctx, cross)
    slender = max(0.0, 1.0 - (span * 12.0 / (32.0 * thickness)) ** 2)
    capacity = PHI_PLAIN * STRUT_STRESS_COEFFICIENT * fc * thickness * height * slender
    leg = (f" and {tag2}'s footing ({w2:,.0f} plf over {l2:.2f}', its whole at-rest thrust)"
           if tag2 else "")
    return LimitState(
        "strut compression", EARTH_PRESSURE_LOAD_FACTOR * reaction, capacity, "lb",
        f"ACI 318-19 §14.5.4, phi {PHI_PLAIN} at 1.6H — two-span continuous reaction "
        f"{reaction:,.0f} lb (simple spans {simple:,.0f}) from {tag1} ({w1:,.0f} plf over "
        f"{l1:.2f}', pinned at the corner){leg}; on {thickness:.0f}\" x {height:.1f}\", "
        f"{fc_how}, {span:.1f}' clear, slenderness factor {slender:.2f}")


def _shares_line(ctx, braced, member_tag: str) -> bool:  # type: ignore[no-untyped-def]
    member = ctx.plan.by_tag(member_tag)
    return bool({braced.start_node, braced.end_node} & {member.start_node, member.end_node})


def _bars(spec):  # type: ignore[no-untyped-def]
    from typehaus.model.rebar import BARS

    out = []
    for bar in getattr(spec, "bars", ()) or ():
        if bar.role in _LONGITUDINAL:
            out.append((bar, BARS[bar.bar]))
    return out


def _toe_tie(ctx, wall) -> tuple[float, float, str] | None:  # type: ignore[no-untyped-def]
    """``(As in², tie depth from the toe edge in, how)``: every ``edge-y`` bar, plus the one
    distributed ``bottom-y`` bar in the outermost line — the bars a tie at the edge holds."""
    from typehaus.engineering.retaining_system_body import _footing_of

    footing = _footing_of(ctx, wall.tag)
    spec = getattr(footing, "reinforcement", None)
    cover = spec.cover.inches if spec is not None and spec.cover is not None else 3.0
    area, moment, parts = 0.0, 0.0, []
    for bar, size in _bars(spec):
        count = (bar.count or 0) if bar.role == "edge-y" else 1
        if not count:
            continue
        depth = cover + size.diameter_in / 2.0
        area += count * size.area_in2
        moment += count * size.area_in2 * depth
        parts.append(f"{count} #{bar.bar} ({bar.role})")
    if not area:
        return None
    return area, moment / area, " + ".join(parts)


def plan_bending(ctx, body, members, built) -> list[LimitState]:  # type: ignore[no-untyped-def]
    """``footing plan bending`` for each side footing and ``corner delivery`` for the S one."""
    from typehaus.engineering.retaining_system_body import DRY, _footing_of, _poly, _solid

    rows: list[LimitState] = []
    cross_dir = None
    for push in body.pushes:
        if any(abs(push.direction[0] * o.direction[0] + push.direction[1] * o.direction[1])
               > 0.99 and o is not push for o in body.pushes):
            cross_dir = push.direction
    for push, member, wall in zip(body.pushes, members, built, strict=True):
        geometry, _ = _geometry(ctx, ctx.plan.by_tag(member.tag))
        footing = _footing_of(ctx, member.tag)
        solid = _solid(ctx, footing.tag, "footing") if footing else None
        tie = _toe_tie(ctx, ctx.plan.by_tag(member.tag))
        if geometry is None or solid is None or tie is None:
            continue
        area, c_t, bars = tie
        u = _unit(member.axis_ft)
        poly = _poly(solid.outline)
        proj = [x * u[0] + y * u[1] for x, y in poly.exterior.coords]
        span = max(proj) - min(proj)
        w = body.thrust_per_ft(push, DRY)
        side = cross_dir is not None and abs(
            push.direction[0] * cross_dir[0] + push.direction[1] * cross_dir[1]) > 0.99
        if side:
            name, load = f"footing plan bending, {footing.tag}", w
            basis = (f"{member.tag}'s whole {w:,.0f} plf (its base friction is spent "
                     f"north-south by the sliding rows)")
        else:
            span = wall.length_ft
            own = body.friction * body.weight_on(poly)
            load = max(0.0, (w * push.width_ft - own) / push.width_ft)
            name = f"corner delivery, {footing.tag} in plan"
            basis = (f"{member.tag}'s {w:,.0f} plf over {push.width_ft:.2f}' less its own base "
                     f"friction {own:,.0f} lb (it points along that thrust) = {load:,.0f} plf")
        moment = EARTH_PRESSURE_LOAD_FACTOR * load * span * span / 8.0
        lever = (geometry.toe_ft + geometry.stem_thickness_ft / 2.0) * 12.0 - c_t
        demand = moment * 12.0 / lever
        capacity = PHI_STM * area * REINFORCEMENT_FY_PSI
        rows.append(LimitState(
            name, demand, capacity, "lb",
            f"ACI 318-19 Ch. 23 strut and tie, phi {PHI_STM} at 1.6H — {basis}, simple span "
            f"{span:.2f}' (Mu {moment:,.0f} ft-lb; fixed ends 2/3 of it); the arch rises from "
            f"the stem line to the toe-edge tie, z {lever:.1f}\"; tie {bars}, As {area:.2f} in²"))
    return rows
