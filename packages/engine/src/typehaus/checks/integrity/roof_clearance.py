"""Nothing the occupant's space contains may stand above the roof structure over it.

Every other relationship between an element and the roof is owned somewhere: a bearing
wall's top by ``resolve/roof_geometry.apply_to_roof_wall_tops``, the cladding lap by
``resolve/envelope``, member-against-member by ``checks/structural/interference``. The gap
this closes is the one nobody owned — an element authored with an explicit elevation, under
a roof that later moved.

That is not hypothetical. ``houses/catlin/plan/mep_venting.py`` says it in its own words:

    ELEVATIONS ARE STOREY-RELATIVE AND THE ATTIC DATUM IS ft(20). Authored as project
    elevations until 2026-08-29, this run resolved 20'-0" too high and hung over the roof.
    Nothing caught it: ``_resolve_pipe_run`` adds the datum silently and no check grades a
    pipe against the roof plane it sits under.

When catlin's attic went from a 4:12 roof over 5'-0" knee walls to a 6:12 cathedral rake on
flat plates, the clear height at the eave went from 5'-0" to 1 1/2". Five families of
element kept the stations they had been given under the old roof — a stair guard, a
bookcase wall's blocking course, both ERV outdoor legs, a bath extract's grille and the
radon riser — and ``haus check`` reported 0 FAIL through all of it. Only the 3D view showed
it, which is not a gate.

**Subject.** An allowlist, keyed to the rule's own sentence rather than to a denylist of
whatever exists today (the lesson ``code.R305_ceiling_height`` drew): the things that hang
in occupied air and are authored at an elevation of their own — MEP distribution and
terminals, and guards. Deliberately *not* in scope, each because something else owns it:

* structure and envelope — a ``ToRoof`` wall is *supposed* to rise into the roof plane, and
  ``interference`` grades framing against framing;
* roof trim and roof-mounted parts (fascia, gutter, snow guard, seam clamp) — they live on
  the roof by definition;
* anything below the storey the roof covers, and anything outside the roof's plan footprint.

**Measure.** The roof's *structural* underside at the element's own plan position
(``roof_underside_at``) — what a wall below must reach, not the exterior plane. The finish
ceiling hangs below that, so this is the generous end: an element that fails here fails by
more than it says, never by less.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.quantities import M_PER_IN
from typehaus.resolve.roof_geometry import roof_underside_at

_CHECK_ID = "integrity.element_above_roof"

#: Solid categories in the rule's subject. Prefixes cover the duct/pipe/conduit families,
#: whose category carries the system (``pipe_water_hot``, ``duct_return``) and would
#: otherwise have to be enumerated system by system and re-enumerated on every new one.
_SUBJECT_PREFIXES = ("duct_", "conduit_")
_SUBJECT_CATEGORIES = frozenset({
    "railing", "railing_infill",          # R312.1 guards and their infill
    "pipe_drain", "pipe_vent",            # DWV
    "pipe_water_cold", "pipe_water_hot",  # supply
    "vent",                               # vent risers and terminations
    "backflow_preventer", "shutoff", "main_shutoff", "vacuum_breaker",
    "water_hammer_arrestor",              # in-line plumbing devices
})

#: Buried and in-slab families share the plumbing prefixes but are never in occupied air.
_NEVER_IN_AIR = frozenset({"drain_tile", "drywell", "sump", "pipe_sleeve"})

#: The roof's structural underside is where a *wall* stops. A duct strapped tight to the
#: underside, or a guard scribed to it, reads a hair over on rounding alone. One inch is
#: below anything a trade could act on and well under the smallest real error seen (4 3/4").
_TOLERANCE_M = 1.0 * M_PER_IN


def _top_probes(solid) -> list[tuple[float, float, float]]:
    """``(x, y, top_z)`` probes for one solid — each plan point paired with ITS OWN top.

    The solid's ``z1_m`` alone will not do. A swept run's z lives on the sweep path, and a
    raked one climbs: catlin's ``RL-A-HANDRAIL`` rises 9'-2" as it follows the flight west,
    so its high end stands under the ridge while its low end stands under the eave. Grading
    the whole solid's maximum against the underside at every plan point condemns it for
    being tall where the roof is tall — which is the shape of a false positive, and a check
    that cries wolf about a correct handrail is worse than no check.

    So a swept solid is probed vertex by vertex, each against the roof over that vertex,
    with the sweep profile's own half-height added back on. Only an extruded solid — one
    top plane over one outline — is probed at its ``z1_m``.
    """
    sweep = getattr(solid, "sweep", None)
    path = getattr(sweep, "path", None) if sweep is not None else None
    if path is None and isinstance(sweep, dict):
        path = sweep.get("path")
    if path:
        profile = getattr(sweep, "profile", None)
        if profile is None and isinstance(sweep, dict):
            profile = sweep.get("profile")
        half = max((abs(pt[1]) for pt in (profile or ())), default=0.0)
        return [(pt[0], pt[1], pt[2] + half) for pt in path]
    top = solid.z1_m
    if top is None:
        return []
    return [(pt[0], pt[1], top) for pt in (solid.outline or ())]


def _lowest_roof_over(ctx: CheckContext, point: tuple[float, float]):
    """The lowest roof structure over a plan point, as ``(roof, underside_z)``.

    Bearing footprint rather than ``ResolvedRoof.footprint``: the latter is expanded by the
    overhang and the cladding lap, so it reaches past the wall to ground a duct has every
    right to stand over. Where more than one roof covers a point — a wing tucked under a
    main run — the *lowest* one is the binding constraint, because that is the one an
    element standing there would come up against first.
    """
    from typehaus.resolve.roof_geometry import roof_bearing_footprint

    best = None
    for roof in ctx.model.roofs:
        footprint = roof_bearing_footprint(ctx.model, roof)
        if footprint is None:
            continue
        xs = [corner[0] for corner in footprint]
        ys = [corner[1] for corner in footprint]
        if not (min(xs) <= point[0] <= max(xs) and min(ys) <= point[1] <= max(ys)):
            continue
        underside = roof_underside_at(ctx.model, roof, point)
        if best is None or underside < best[1]:
            best = (roof, underside)
    return best


@check(Tier.INTEGRITY, _CHECK_ID)
def element_above_roof(ctx: CheckContext) -> list[Finding]:
    roofs = list(ctx.model.roofs)
    if not roofs:
        return [Finding(
            severity=Severity.WARN, result=Result.UNKNOWN, check_id=_CHECK_ID,
            message="UNKNOWN — no roof resolves, so there is no plane to grade against",
            element_tags=(),
        )]

    graded = 0
    worst: dict[str, tuple[float, float, float, str]] = {}
    for solid in ctx.model.solids:
        category = solid.category or ""
        if category in _NEVER_IN_AIR:
            continue
        if not (category in _SUBJECT_CATEGORIES
                or any(category.startswith(p) for p in _SUBJECT_PREFIXES)):
            continue
        tag = solid.tag or solid.uid or category
        probes = _top_probes(solid)
        if not probes:
            continue
        graded += 1
        for x, y, top in probes:
            point = (x, y)
            over_roof = _lowest_roof_over(ctx, point)
            if over_roof is None:
                continue
            roof, underside = over_roof
            over = top - underside
            if over > _TOLERANCE_M and over > worst.get(tag, (0.0,))[0]:
                worst[tag] = (over, top, underside, roof.tag)

    if not graded:
        return [Finding(
            severity=Severity.WARN, result=Result.UNKNOWN, check_id=_CHECK_ID,
            message=("UNKNOWN — no railing, duct, pipe or vent solid resolves, so there is "
                     "nothing in this rule's subject to grade"),
            element_tags=(),
        )]

    if not worst:
        return [Finding(
            severity=Severity.WARN, result=Result.PASS, check_id=_CHECK_ID,
            message=(f"every one of {graded} railing/duct/pipe/vent solids stands under the "
                     f"roof structure above it"),
            element_tags=(),
        )]

    findings: list[Finding] = []
    for tag, (over, top, underside, roof_tag) in sorted(
            worst.items(), key=lambda kv: -kv[1][0]):
        findings.append(Finding(
            severity=Severity.ERROR, result=Result.FAIL, check_id=_CHECK_ID,
            message=(f"{tag} tops out at {top / .3048:.2f}', "
                     f"{over / M_PER_IN:.1f}\" above {roof_tag}'s underside "
                     f"({underside / .3048:.2f}') over it"),
            element_tags=(tag,),
            fix_hint=("lower the element, or move it in plan to where the roof is high "
                      "enough — the underside is the roof structure's, so the finished "
                      "ceiling is lower still"),
        ))
    return findings
