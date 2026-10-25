"""What a guard weighs, and whether the thing under it can carry that.

A guard does not have to be a stick railing. A masonry parapet standing at a porch edge is
the same fixture in code terms — R312.1's guard — and it is authored here as a ``Wall`` with
``guard=True`` rather than as a ``Railing``, because reducing it to posts and rails would
strip its four-layer stucco/CMU/air/brick stack, orphan the post bases grouted into its
cores, and drop its masonry volume out of the cubic-yard take-off.

What that costs is a load path nobody was asking about. A 42" grouted-CMU-and-brick parapet
runs about 420 plf; a wood deck rim designed to R507's 40 psf live + 10 psf dead cannot
carry that, and the model had no rule that would ever say so.

The load is derived from the guard's *own* assembly — every layer's thickness times its
material's density, times the guard's height — rather than from a magic number, so a lighter
guard prices itself out of the finding automatically and a heavier one prices itself in.
Air gaps carry nothing and are skipped; a solid layer whose material states no ``density``
makes the whole answer UNKNOWN, because a load computed from a partial stack is not a load.

The weighing and the "what is under it" sweep live in ``masonry_load.py`` now, shared with
``structural.through_deck_clearance``: what "bears on wood" means must have one answer.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import not_applicable as _not_applicable
from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.masonry_load import dead_load_plf, support_at
from typehaus.findings import Finding, Result
from typehaus.model.elements import Wall

_CHECK_ID = "structural.masonry_guard_bearing"

#: Stations along the guard's run, so a guard that starts on a wall and ends over a deck is
#: read as what it is rather than as whichever support happened to be found first.
_STATION_STEP_M = 0.25


@check(Tier.STRUCTURAL, _CHECK_ID)
def masonry_guard_bearing(ctx: CheckContext) -> list[Finding]:
    """A guard wall's dead load lands on something that can carry it.

    One finding per ``guard=True`` wall. PASS where every station of its run stands on
    concrete, masonry, steel or a footing, or where the derived load is under the house's
    ``max_guard_dead_load_on_wood_plf`` allowance whatever it stands on. FAIL where a heavy
    guard stands on wood framing. UNKNOWN — never PASS — where a layer states no density or
    no support can be identified under some part of the run.
    """
    guards = [element for element in ctx.plan.all_elements()
              if isinstance(element, Wall) and element.guard]
    if not guards:
        # N/A, not UNKNOWN: the plan was read and states positively that no wall is a
        # guard. There is no missing input here and nothing for anyone to author.
        return [_not_applicable(_CHECK_ID, "no wall in the plan is marked as a guard "
                                "(Wall.guard); a stick guard is graded by "
                                "structural.deck_guard and code.R312_1_guard_height "
                                "instead")]
    allowance = ctx.preferences.structural.max_guard_dead_load_on_wood_plf
    out: list[Finding] = []
    for element in guards:
        wall = next((w for w in ctx.model.walls if w.tag == element.tag), None)
        if wall is None:
            out.append(_unknown(_CHECK_ID, f"guard wall {element.tag} resolved no geometry, "
                                "so neither its weight nor its support can be read",
                                (element.tag,)))
            continue
        out.append(_grade(ctx, element.tag, wall, allowance))
    return out


def _grade(ctx: CheckContext, tag: str, wall, allowance_plf: float) -> Finding:
    height_m = wall.z1_m - wall.z0_m
    load_plf = dead_load_plf(ctx, wall, height_m)
    if load_plf is None:
        return _unknown(_CHECK_ID, f"guard wall {tag} has a solid layer whose material "
                        "states no density, so its dead load cannot be derived", (tag,))
    supports = _supports_along(ctx, wall)
    named = sorted({name for _kind, name in supports if name})
    # The allowance is asked FIRST, and the ordering is the docstring's own "whatever it
    # stands on". A guard light enough that ordinary wood framing carries it does not raise a
    # question about its bearing line, so failing to identify that line is not missing data —
    # it is an answer nobody needed. Asked the other way round, a 67 plf framed screen panel
    # standing partly over open deck reported UNKNOWN, which is this check demanding an input
    # its own threshold had already made irrelevant.
    if load_plf <= allowance_plf + 1e-9:
        return _advisory(_CHECK_ID, f"guard wall {tag} weighs {load_plf:.0f} plf, at or "
                         f"under the {allowance_plf:.0f} plf ordinary wood framing carries; "
                         "its support does not have to be hard", (tag,), Result.PASS)
    # A station over a beam the pier calcs weigh this wall onto is not a deck rim drawn for
    # 10 psf: the load is in an engineered record, so the allowance does not apply there.
    carried, whole_run = _engineered_supports(ctx, tag, wall)
    on_beam = [whole_run or any(p.covers(point) for p in carried.values())
               for point in _stations(wall)]
    rest = [s for s, covered in zip(supports, on_beam, strict=True) if not covered]
    if any(kind is None for kind, _name in rest):
        return _unknown(_CHECK_ID, f"guard wall {tag} carries {load_plf:.0f} plf but part "
                        "of its run has nothing modeled under it at its base elevation, so "
                        "what it bears on cannot be identified", (tag,))
    soft = sorted({name for kind, name in rest if kind == "wood"})
    if soft:
        return _advisory(
            _CHECK_ID,
            f"guard wall {tag} puts {load_plf:.0f} plf of dead load on wood framing "
            f"({', '.join(soft)}), over the {allowance_plf:.0f} plf allowance",
            (tag, *soft), Result.FAIL,
            fix_hint=("carry the guard on a concrete or masonry bearing line, or author a "
                      "lighter guard (a stick Railing rather than a masonry parapet)"))
    if any(on_beam):
        beams = ", ".join(sorted(carried))
        return _advisory(
            _CHECK_ID,
            f"guard wall {tag} weighs {load_plf:.0f} plf, over the {allowance_plf:.0f} plf "
            f"wood allowance, but its run is weighed onto {beams} in the pier calcs "
            "(pier_basis.wall_line_loads), not left on a deck rim",
            (tag, *sorted(carried)), Result.PASS)
    return _advisory(
        _CHECK_ID,
        f"guard wall {tag} weighs {load_plf:.0f} plf and bears on "
        f"{', '.join(named) or 'hard support'} the length of its run",
        (tag, *named), Result.PASS)


def _engineered_supports(ctx: CheckContext, tag: str, wall) -> tuple[dict, bool]:
    """(beam tag -> footprint, whole run weighed) for the beams ``pier_basis`` loads with
    this guard's line. A shear panel on its beam's own chords is weighed end to end."""
    from shapely.geometry import Polygon

    from typehaus.checks.structural._engineering import engineering_context
    from typehaus.engineering.pier_basis import beams_weighing_wall

    weighed = beams_weighing_wall(engineering_context(ctx), tag)
    (x0, y0), (x1, y1) = wall.axis
    whole_run = sum(weighed.values()) >= math.hypot(x1 - x0, y1 - y0) - 1e-6
    return ({solid.tag: Polygon(solid.outline).buffer(1e-6) for solid in ctx.model.solids
             if solid.tag in weighed}, whole_run)


def _stations(wall) -> list:
    """Points along the guard's run, base to tip, ``_STATION_STEP_M`` apart."""
    from shapely.geometry import Point

    (x0, y0), (x1, y1) = wall.axis
    steps = max(int(math.ceil(math.hypot(x1 - x0, y1 - y0) / _STATION_STEP_M)), 1)
    return [Point(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps)
            for i in range(steps + 1)]


def _supports_along(ctx: CheckContext, wall) -> list[tuple[str | None, str | None]]:
    """``(kind, name)`` under each station of the guard's run, walked base to tip."""
    return [support_at(ctx, wall, (point.x, point.y)) for point in _stations(wall)]
