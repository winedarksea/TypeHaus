"""Snow-related structural screens: sliding discharge, and rafter spans at the snow load.

Both are the same class of answer the sibling structural checks give — a prescriptive table
lookup or a geometric screen, labeled "[advisory, not engineering]" and never presented as a
design. What is new here is that they are the *snow* cases the roof framing sheet explicitly
disclaims (``emit/draw/roofframingplan.py``): that sheet prints Pg and Pf and says drift,
sliding and unbalanced cases are the engineer's. This module takes exactly one of those back
— whether a sliding-snow *exposure* exists and whether retention was authored for it — and
leaves the rest where the sheet put it.
"""

from __future__ import annotations

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import ConnectorKind

_M_PER_FT = 0.3048

# How far downslope of an eave sliding snow is assumed to land. A documented heuristic, not a
# computed trajectory: a real one needs the slope, the surface friction, the snow density and
# the release depth, none of which the model carries. The rule below is deliberately coarse
# and deliberately conservative — snow off a taller roof reaches at least a body-length out,
# roughly as far as it fell, and past about 15' the assumption stops being defensible at all.
_MIN_REACH_FT = 6.0
_MAX_REACH_FT = 15.0

# Allowable rafter spans (ft), SPF #2, at 50 psf ground snow, from the IRC R802.4.1 rafter
# span tables. Keyed by (profile, o.c. spacing) because a rafter table is published per
# spacing and interpolating between two published rows is not a lookup, it is a design.
# Engineered profiles (I-joist, LVL, PSL) are deliberately absent: they are sized by their
# manufacturer's software against the actual load case, so they resolve UNKNOWN below rather
# than borrowing a sawn-lumber row.
_RAFTER_SPAN_FT: dict[tuple[str, float], float] = {
    ("2x6", 16.0): 9.1,
    ("2x8", 16.0): 11.5,
    ("2x10", 16.0): 14.1,
    ("2x12", 16.0): 16.3,
    ("2x6", 24.0): 7.4,
    ("2x8", 24.0): 9.5,
    ("2x10", 24.0): 11.5,
    ("2x12", 24.0): 13.4,
}




# --- sliding snow ---------------------------------------------------------------------


def _bbox(points) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _downslope_eaves(roof) -> list[tuple[str, tuple[float, float, float, float]]]:
    """The eave edges snow can slide off, as (label, (x0, y0, x1, y1)) segments.

    ``ridge_direction`` names the axis the ridge runs along, so the slopes fall across the
    *other* axis: a ridge running in x sheds north and south. A shed roof still resolves with
    a ridge direction, and taking both edges of it is the conservative reading — the model
    does not record which way a shed falls, and screening the uphill edge too costs a false
    positive at worst, where missing the downhill one costs the whole check.
    """
    x0, y0, x1, y1 = _bbox(roof.footprint)
    if roof.ridge_direction == "x":
        return [("south", (x0, y0, x1, y0)), ("north", (x0, y1, x1, y1))]
    return [("west", (x0, y0, x0, y1)), ("east", (x1, y0, x1, y1))]


def _discharge_strip(edge: tuple[float, float, float, float], label: str, reach_m: float):
    """The plan-space band outboard of ``edge`` that sliding snow is assumed to reach.

    The roof footprint already includes its overhang, so the band starts at the footprint
    edge rather than adding one.
    """
    from shapely.geometry import box

    x0, y0, x1, y1 = edge
    if label == "south":
        return box(x0, y0 - reach_m, x1, y0)
    if label == "north":
        return box(x0, y1, x1, y1 + reach_m)
    if label == "west":
        return box(x0 - reach_m, y0, x0, y1)
    return box(x1, y0, x1 + reach_m, y1)


def _lower_surfaces(ctx: CheckContext, upper) -> list[tuple[str, object, float]]:
    """Everything sliding snow off ``upper`` could land *on*: (tag, polygon, top elevation).

    Roofs below this one, plus horizontal glazing panels — the breezeway canopy is the case
    that motivated this check, and a polycarbonate sheet is precisely the surface an impact
    load matters for.
    """
    from shapely.geometry import Polygon

    from typehaus.model.structure import GlazingPanel

    out: list[tuple[str, object, float]] = []
    for roof in ctx.model.roofs:
        if roof.tag == upper.tag or roof.ridge_z_m >= upper.eave_z_m:
            continue
        out.append((roof.tag, Polygon(roof.footprint), roof.ridge_z_m))
    for element in ctx.plan.all_elements():
        if not isinstance(element, GlazingPanel) or element.plane != "horizontal":
            continue
        top = element.top_elevation.meters
        if top >= upper.eave_z_m:
            continue
        out.append((element.tag, Polygon([p.xy_m for p in element.outline]), top))
    return out


def _snow_guard_tags(ctx: CheckContext) -> set[str]:
    """Roof tags a modeled snow guard is authored on.

    Presence, not adequacy: a row of guards is either authored on the shedding slope or it is
    not. How many, at what spacing, and whether they hold the drift is the manufacturer's
    calculation off the real snow load — which is why this reports PASS-with-a-note and not
    "the retention is sufficient".
    """
    from typehaus.model.structure import Connector

    tags: set[str] = set()
    for element in ctx.plan.all_elements():
        if isinstance(element, Connector) and element.kind is ConnectorKind.SNOW_GUARD:
            tags.update(element.connects)
    return tags


@check(Tier.STRUCTURAL, "structural.sliding_snow")
def sliding_snow(ctx: CheckContext) -> list[Finding]:
    """Does a pitched roof discharge sliding snow onto a lower surface, and is it retained?

    Scope, stated plainly: this screens **exposure and retention presence only**. It computes
    no impact load, no drift, no unbalanced case, and no sliding trajectory — the discharge
    band is the documented heuristic at the top of this module. A FAIL means "an engineer or a
    snow-retention manufacturer has to look at this", never "this will collapse"; a PASS means
    "retention is authored here", never "the retention is adequate".
    """

    cid = "structural.sliding_snow"
    ground = ctx.plan.project.site.ground_snow_load_psf
    if ground is None:
        return [_unknown(cid, "the site declares no ground_snow_load_psf, so there is no "
                              "snow case to screen for")]

    guarded = _snow_guard_tags(ctx)
    out: list[Finding] = []
    for upper in ctx.model.roofs:
        if upper.ridge_z_m <= upper.eave_z_m:
            continue  # flat: nothing slides
        targets = _lower_surfaces(ctx, upper)
        if not targets:
            continue
        for label, edge in _downslope_eaves(upper):
            for tag, polygon, top in targets:
                drop_ft = (upper.eave_z_m - top) / _M_PER_FT
                reach_ft = min(max(drop_ft, _MIN_REACH_FT), _MAX_REACH_FT)
                strip = _discharge_strip(edge, label, reach_ft * _M_PER_FT)
                if not strip.intersects(polygon) or strip.intersection(polygon).area <= 0:
                    continue
                where = (f"{upper.tag}'s {label} eave discharges onto {tag}, "
                         f"{drop_ft:.1f}' below (assumed reach {reach_ft:.0f}')")
                if upper.tag in guarded:
                    out.append(_advisory(
                        cid, f"{where} — snow retention authored on {upper.tag}; sizing and "
                             "spacing remain the retention manufacturer's calculation at "
                             f"Pg = {ground:.0f} psf", (upper.tag, tag), Result.PASS))
                else:
                    out.append(_advisory(
                        cid, f"sliding snow from {where} — snow retention or an engineered "
                             "impact load is required", (upper.tag, tag), Result.FAIL,
                        fix_hint=f"author a row of Connector(kind=SNOW_GUARD, "
                                 f"connects=(\"{upper.tag}\",)) on the shedding slope"))
    if not out:
        out.append(_advisory(cid, "no pitched roof discharges onto a lower roof or glazed "
                                  "surface within the assumed reach", (), Result.PASS))
    return out


# --- rafter spans ---------------------------------------------------------------------


@check(Tier.STRUCTURAL, "structural.rafter_span")
def rafter_span(ctx: CheckContext) -> list[Finding]:
    """Resolved rafter spans against the IRC R802.4.1 table at this site's snow load.

    Same shape as ``structural.ijoist_span`` next door, and the same honesty about its edges:
    an engineered profile (I-joist, LVL), a spacing the table is not published at, or a roof
    with no rafters at all (trusses, a ridge-beam roof whose members resolve as beams) reports
    UNKNOWN — engineered — rather than borrowing a row that does not describe it.
    """
    cid = "structural.rafter_span"
    ground = ctx.plan.project.site.ground_snow_load_psf
    if ground is None:
        return [_unknown(cid, "the site declares no ground_snow_load_psf, so no rafter span "
                              "table applies")]
    if abs(ground - 50.0) > 1e-6:
        return [_unknown(cid, f"the rafter span table here is published at 50 psf ground "
                              f"snow and this site carries {ground:.0f} psf")]

    out: list[Finding] = []
    for roof in ctx.model.roofs:
        rafters = [member for member in roof.members if member.category == "rafter"]
        if not rafters:
            out.append(_unknown(cid, f"roof {roof.tag} resolves no rafters (trussed, or "
                                     "framed on a ridge beam) — engineered", (roof.tag,)))
            continue
        profile = rafters[0].profile
        spacings = {round(_spacing_in(roof, rafters), 1)}
        spacing_in = spacings.pop()
        allowable = _RAFTER_SPAN_FT.get((profile, spacing_in))
        if allowable is None:
            out.append(_unknown(
                cid, f"roof {roof.tag} is framed with {profile} at {spacing_in:.0f}\" o.c., "
                     "which the sawn-lumber rafter table does not publish — engineered",
                (roof.tag,)))
            continue
        span_ft = max(member.length_m for member in rafters) / _M_PER_FT
        within = span_ft <= allowable + 1e-6
        out.append(_advisory(
            cid, f"roof {roof.tag} {profile} rafter span {span_ft:.1f}' "
                 f"{'is within' if within else 'exceeds'} the {allowable:.1f}' table limit "
                 f"at {spacing_in:.0f}\" o.c., SPF #2, Pg = {ground:.0f} psf",
            (roof.tag,), Result.PASS if within else Result.FAIL))
    if not out:
        out.append(_unknown(cid, "the model resolves no roofs"))
    return out


def _spacing_in(roof, rafters) -> float:
    """The rafters' actual o.c. spacing, read off the resolved members.

    Measured rather than read from a FramingSpec: the spec is optional and the solver has its
    own default, and the number that matters for a span table is the one the roof was framed
    at, not the one someone may or may not have authored.
    """
    from typehaus.model.enums import StructuralRole  # noqa: F401 — parity with siblings

    axis = 0 if roof.ridge_direction == "x" else 1
    seats = sorted({round(member.p0[axis], 4) for member in rafters})
    if len(seats) < 2:
        return 16.0
    gaps = [b - a for a, b in zip(seats[:-1], seats[1:], strict=True) if b - a > 1e-6]
    if not gaps:
        return 16.0
    return sorted(gaps)[len(gaps) // 2] / 0.0254
