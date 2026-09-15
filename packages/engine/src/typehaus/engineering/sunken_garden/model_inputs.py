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
from typehaus.engineering.sunken_garden.inputs import (
    BasedValue,
    CourtGeometry,
    SunkenGardenDesignInput,
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

    first = next(iter(sections.values()))
    for tag, geometry in sections.items():
        for field in ("stem_thickness_ft", "stem_height_ft", "footing_width_ft",
                      "footing_depth_ft", "toe_ft"):
            if abs(getattr(geometry, field) - getattr(first, field)) > _SECTION_TOLERANCE_FT:
                return None, [f"one common court section — {tag} differs from "
                              f"{first.tag} in {field}"]

    axes = {wall.tag: _axis_ft(ctx, wall.tag) for wall in walls}
    if any(axis is None for axis in axes.values()):
        return None, [f"a resolved axis for {tag}" for tag, axis in axes.items()
                      if axis is None]

    pair = _parallel_pair(axes)
    if pair is None:
        return None, ["two parallel retaining legs whose separation is the court's width"]
    (left, right) = pair
    (ax, ay), (bx, by) = axes[left]
    run = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / run, (by - ay) / run
    (cx, cy), _ = axes[right]
    separation = abs((cx - ax) * -uy + (cy - ay) * ux)

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
    ), []


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
        ctx: EngineeringContext) -> tuple[SunkenGardenDesignInput, tuple[str, ...]]:
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
