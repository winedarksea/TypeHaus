"""Drive the courtyard study from the **authored model** instead of from literals.

Until this module existed the study package was a second, parallel body of sunken-garden
engineering: ``inputs.default_design_input()`` hard-coded a court, and nothing checked that
the court it described was the court the house authors. It was not. The literal ordinary
retained height was 5.0 ft where the model gives **5.7865 ft**, so every case in the study —
including the one that answers "does removing the terrace buy a smaller section?" — was run
on a wall three-quarters of a foot shorter than the one being built.

The split matters in one direction only. ``engineering/retaining_{basis,wall,system}.py``
reads the plan and mints sealable records; this package reads nothing and writes a report.
So the report is what moves: it is driven from the same resolved model the register is, and
where a value genuinely cannot be derived it keeps the literal **and says so**, rather than
silently agreeing with itself.

**Leaf rule.** ``engineering/`` imports ``model``/``resolve``/``quantities``/``wind`` and
never ``checks``. Everything here is inside that: ``retaining_basis`` for the section,
``resolve.orientation`` for which side of a wall the soil is on.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.engineering.registry import EngineeringContext
from typehaus.engineering.retaining_basis import _geometry
from typehaus.engineering.retaining_court.inputs import (
    BasedValue,
    CourtDesignInput,
    CourtGeometry,
    CourtWallTags,
    default_design_input,
)

_M_PER_FT = 0.3048

#: How far from a retaining wall's **outboard** face a grade spot may sit and still be read
#: as the ordinary yard that wall retains, feet. 20 ft is comfortably wider than any
#: terrace-to-wall dimension and narrow enough that a spot on the far side of the house does
#: not reach in — the failure mode a bare "nearest spot" rule has. Paired with a
#: longitudinal window of the wall's own run plus the same reach, so a spot off the end of a
#: leg is not read across the corner.
GRADE_SPOT_REACH_FT = 20.0

#: Two wall axes are "the same section" when every dimension agrees to this, feet. Tight
#: enough that a real retype is caught; loose enough to absorb the inch arithmetic a house
#: writes its elevations in.
_SECTION_TOLERANCE_FT = 1e-6


def _court_walls(ctx: EngineeringContext) -> list:
    """The free retaining walls, by the register's own predicate.

    Imported rather than re-spelled: a study scoped differently from the register would be
    the very split this module exists to close.
    """
    from typehaus.engineering.retaining_wall import _retaining_walls

    return sorted(_retaining_walls(ctx), key=lambda w: w.tag)


def _axis_ft(ctx: EngineeringContext, tag: str) -> tuple[tuple[float, float],
                                                         tuple[float, float]] | None:
    wall = next((w for w in ctx.model.walls if w.tag == tag), None)
    if wall is None:
        return None
    (ax, ay), (bx, by) = wall.axis
    return (ax / _M_PER_FT, ay / _M_PER_FT), (bx / _M_PER_FT, by / _M_PER_FT)


def _outward_sign(ctx: EngineeringContext, wall) -> float | None:
    """+1 or -1 in the ``normal(start->end)`` frame, toward the retained soil.

    ``None`` where the storey's winding is unrecoverable — refused rather than defaulted,
    for the reason ``retaining_basis._heelward_offset`` gives: the fallback sign is a real
    value a real structure can also have, so taking it would read the *court* as the
    retained side on exactly the input where being wrong inverts the answer.
    """
    from typehaus.resolve.orientation import resolve_storey_windings, wall_outward_sign

    resolved = next((w for w in ctx.model.walls if w.tag == wall.tag), None)
    if resolved is None:
        return None
    windings = resolve_storey_windings(ctx.plan, resolved.storey)
    key = windings.component_key_for_wall(wall)
    if not windings.outer_loop_area_by_component_key.get(key):
        return None
    return wall_outward_sign(ctx.plan, wall, resolved.storey, windings.sign_for_wall(wall))


def ordinary_retained_height_ft(ctx: EngineeringContext) -> tuple[float | None, str]:
    """Yard grade beside the walls, measured **up from the footing top**, and its basis.

    This is the height the study calls "ordinary": the fill that stands against the stem at
    ordinary yard level, with the raised terrace carried separately as a finite-strip
    surcharge above it. It is the one input the literal got wrong, and the direction of the
    error is the unsafe one — a *lower* ordinary line moves height out of direct at-rest
    pressure and into the strip solution, which is gentler.

    The yard is read from the site's own ``grade`` spot elevations on each wall's **outboard**
    side, and the **highest** of them governs: more ordinary soil against the stem is the
    conservative reading, and the single global ``Site.grade`` plane is not usable here for
    the reason ``retaining_basis._geometry`` gives about ``unbalanced_fill``.
    """
    walls = _court_walls(ctx)
    if not walls:
        return None, "no free retaining wall in the model"
    spots = [s for s in ctx.plan.project.site.spot_elevations if s.kind == "grade"]
    if not spots:
        return None, "the site authors no grade spot elevations"

    best: float | None = None
    for wall in walls:
        if wall.bottom_elevation is None:
            continue
        axis = _axis_ft(ctx, wall.tag)
        sign = _outward_sign(ctx, wall)
        if axis is None or sign is None:
            continue
        (ax, ay), (bx, by) = axis
        run = math.hypot(bx - ax, by - ay)
        if run < _SECTION_TOLERANCE_FT:
            continue
        ux, uy = (bx - ax) / run, (by - ay) / run
        # ``normal(unit(axis))`` is the LEFT normal, and ``resolve_wall_geometry`` puts the
        # interior face at ``-sign * n`` — so the retained (exterior) face is at ``+sign * n``.
        nx, ny = -uy * sign, ux * sign
        footing_top_ft = wall.bottom_elevation.meters / _M_PER_FT
        for spot in spots:
            px, py = spot.position.xy_m
            px, py = px / _M_PER_FT, py / _M_PER_FT
            offset = (px - ax) * nx + (py - ay) * ny
            along = (px - ax) * ux + (py - ay) * uy
            if offset <= 0.0 or offset > GRADE_SPOT_REACH_FT:
                continue
            if not -GRADE_SPOT_REACH_FT <= along <= run + GRADE_SPOT_REACH_FT:
                continue
            height = spot.elevation.meters / _M_PER_FT - footing_top_ft
            best = height if best is None else max(best, height)
    if best is None:
        return None, ("no grade spot elevation sits outboard of a retaining wall within "
                      f"{GRADE_SPOT_REACH_FT:.0f} ft")
    return best, (f"authored grade spot elevations outboard of "
                  f"{', '.join(w.tag for w in walls)}, highest governing")


def court_geometry(ctx: EngineeringContext) -> tuple[CourtGeometry | None, list[str]]:
    """The court's section and plan dimensions, or the names of what the model lacks."""
    walls = _court_walls(ctx)
    if len(walls) < 3:
        return None, [f"three free retaining walls forming a court (found {len(walls)})"]

    sections: dict[str, object] = {}
    missing: list[str] = []
    for wall in walls:
        geometry, gaps = _geometry(ctx, wall)
        if geometry is None:
            missing.extend(gaps)
        else:
            sections[wall.tag] = geometry
    if missing:
        return None, missing

    axes = {wall.tag: _axis_ft(ctx, wall.tag) for wall in walls}
    if any(axis is None for axis in axes.values()):
        return None, [f"a resolved axis for {tag}" for tag, axis in axes.items()
                      if axis is None]

    pair = _parallel_pair(axes)
    if pair is None:
        return None, ["two parallel retaining legs whose separation is the court's width"]
    (left, right) = pair

    # The legs share one section exactly. The end wall may differ only by a longer TOE
    # (its footing wider by the same amount); a different heel, stem or depth is a second
    # section this single-section study cannot describe.
    first = sections[left]
    fields = ("stem_thickness_ft", "stem_height_ft", "footing_width_ft",
              "footing_depth_ft", "toe_ft")
    end_extensions = []
    for tag, geometry in sections.items():
        extension = geometry.toe_ft - first.toe_ft if tag not in pair else 0.0
        for field in fields:
            expected = getattr(first, field)
            if field in ("footing_width_ft", "toe_ft"):
                expected += extension
            if abs(getattr(geometry, field) - expected) > _SECTION_TOLERANCE_FT:
                return None, [f"one common court section — {tag} differs from "
                              f"{first.tag} in {field}"]
        if extension < -_SECTION_TOLERANCE_FT:
            return None, [f"an end wall toe no shorter than the legs' — {tag} is "
                          f"{-extension:.2f}' shorter"]
        if tag not in pair:
            end_extensions.append(extension)
    (ax, ay), (bx, by) = axes[left]
    run = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / run, (by - ay) / run
    (cx, cy), _ = axes[right]
    separation = abs((cx - ax) * -uy + (cy - ay) * ux)

    end_tags = [tag for tag in sections if tag not in pair]
    return CourtGeometry(
        # Axis-to-axis less one full stem: each centreline carries half a stem into the
        # court, so the clear dimension loses one thickness, not two halves of two.
        clear_width_ft=separation - first.stem_thickness_ft,
        retained_side_length_ft=run,
        concrete_stem_height_ft=first.stem_height_ft,
        concrete_top_elevation_ft=0.0,
        footing_depth_ft=first.footing_depth_ft,
        stem_thickness_in=first.stem_thickness_ft * 12.0,
        footing_width_ft=first.footing_width_ft,
        toe_ft=first.toe_ft,
        end_toe_extension_ft=max(end_extensions, default=0.0),
        walls=court_wall_tags(ctx, walls, pair, end_tags, axes),
    ), []


#: How far off a leg's line an element may sit and still be read as on it, feet.
_ON_LINE_FT = 1.0


def _frame(axis) -> tuple[float, float, float, float, float]:
    (ax, ay), (bx, by) = axis
    run = math.hypot(bx - ax, by - ay)
    return ax, ay, (bx - ax) / run, (by - ay) / run, run


def court_wall_tags(ctx: EngineeringContext, walls: list, pair: tuple[str, str],
                    end_tags: list[str], axes: dict) -> CourtWallTags:
    """Each coupled-model role's authored tag, read off the model's relations.

    Left is the leg with the smaller plan (x, y) midpoint. A leg's upper extension is a
    resolved wall collinear with it that meets its open end; the cross-member is the court
    walls' shared ``base_restraint_ref``; the tie is a veneer beam spanning the two uppers.
    A role nothing plays keeps its label.
    """
    from typehaus.engineering.veneer_beam import veneer_beams

    def mid(tag):
        (ax, ay), (bx, by) = axes[tag]
        return ((ax + bx) / 2.0, (ay + by) / 2.0)

    left, right = sorted(pair, key=mid)
    end_pts = [p for tag in end_tags for p in axes[tag]]

    def upper(tag: str) -> str | None:
        ax, ay, ux, uy, _run = _frame(axes[tag])
        # the open end: the leg endpoint farther from the end wall
        a, b = axes[tag]
        if not end_pts:
            return None
        open_pt = max((a, b), key=lambda q: min(math.dist(q, p) for p in end_pts))
        for wall in sorted(ctx.model.walls, key=lambda w: w.tag):
            if wall.tag in axes:
                continue
            pts = [(x / _M_PER_FT, y / _M_PER_FT) for x, y in wall.axis]
            off = [abs((x - ax) * -uy + (y - ay) * ux) for x, y in pts]
            if max(off) <= 1e-3 and min(math.dist(q, open_pt) for q in pts) <= 1e-3:
                return wall.tag
        return None

    refs = {getattr(w, "base_restraint_ref", None) for w in walls} - {None}
    lu, ru = upper(left), upper(right)
    tie = None
    if lu and ru:
        la, lb = _axis_ft(ctx, lu), _axis_ft(ctx, ru)
        for beam, _carried in veneer_beams(ctx):
            axis = _axis_ft(ctx, beam.tag)
            if axis is None:
                continue
            a, b = axis
            if any(_line_offset(p, la) <= _ON_LINE_FT and _line_offset(q, lb) <= _ON_LINE_FT
                   for p, q in ((a, b), (b, a))):
                tie = beam.tag
                break
    base = CourtWallTags()
    return CourtWallTags(
        left_upper=lu or base.left_upper, left=left,
        right_upper=ru or base.right_upper, right=right,
        end=end_tags[0] if len(end_tags) == 1 else base.end,
        cross=next(iter(refs)) if len(refs) == 1 else base.cross,
        tie=tie or base.tie)


def _line_offset(point, axis) -> float:
    ax, ay, ux, uy, _run = _frame(axis)
    return abs((point[0] - ax) * -uy + (point[1] - ay) * ux)


def _parallel_pair(axes: dict) -> tuple[str, str] | None:
    """The two legs of the U — parallel, equal run. The third is the end wall."""
    tags = sorted(axes)
    for index, left in enumerate(tags):
        (ax, ay), (bx, by) = axes[left]
        left_run = math.hypot(bx - ax, by - ay)
        for right in tags[index + 1:]:
            (cx, cy), (dx, dy) = axes[right]
            right_run = math.hypot(dx - cx, dy - cy)
            if abs(left_run - right_run) > 1e-3 or left_run < _SECTION_TOLERANCE_FT:
                continue
            cross = ((bx - ax) * (dy - cy) - (by - ay) * (dx - cx)) / (left_run * right_run)
            if abs(cross) < 1e-6:
                return left, right
    return None


def design_input_from_model(
        ctx: EngineeringContext) -> tuple[CourtDesignInput, tuple[str, ...]]:
    """The study's basis, derived. Second element names every value that stayed a literal.

    Nothing here invents a site fact. Soil strength, stiffness, groundwater and the balcony
    reactions are not in the model and stay exactly as ``default_design_input`` states them,
    unresolved and visible. What *is* in the model — the section, the plan dimensions, the
    yard the walls stand in — is read from it.
    """
    design = default_design_input()
    fell_back: list[str] = []

    geometry, gaps = court_geometry(ctx)
    if geometry is None:
        fell_back.extend(f"court geometry: {gap}" for gap in gaps)
    else:
        design = replace(design, geometry=geometry)

    height, basis = ordinary_retained_height_ft(ctx)
    if height is None:
        fell_back.append(f"ordinary retained height: {basis}")
    else:
        design = replace(design, soil=replace(
            design.soil,
            ordinary_retained_height_ft=BasedValue(height, basis, measured=True)))
    return design, tuple(fell_back)
