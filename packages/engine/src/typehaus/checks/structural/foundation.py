"""Foundation-wall screens the framing solver does not do: unbalanced backfill height.

A basement wall's governing load case is usually not what it carries from above — it is the
soil pushing sideways on it. IRC Table R404.1.2(1) publishes how much unbalanced backfill a
*plain* (unreinforced) concrete wall may retain, by thickness and by how heavy the soil is.
Past that row the wall is an engineered element, and the code says so.

Same contract as the sibling structural checks: this is a table lookup, labeled advisory,
and it never claims to be a design. It also never guesses an input — no soil class means
UNKNOWN, because the three lateral-pressure columns are two wall thicknesses apart and
picking one silently would be choosing the answer.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import LayerFunction

_M_PER_FT = 0.3048

# IRC Table R405.1 soil groups → the equivalent-fluid lateral pressure (psf per foot of
# depth) Table R404.1.2(1) is indexed on.
_SOIL_LATERAL_PSF_PER_FT: dict[str, int] = {
    "GW": 30, "GP": 30, "SW": 30, "SP": 30,
    "GM": 45, "GC": 45, "SM": 45, "SM-SC": 45, "ML": 45,
    "SC": 60, "MH": 60, "ML-CL": 60, "CL": 60,
}

# Maximum unbalanced backfill height (ft) for a PLAIN concrete foundation wall, by nominal
# wall thickness (in) and lateral pressure column, per IRC Table R404.1.2(1). Reinforced
# walls are a different table entirely — a wall past these limits is not "nearly fine", it
# is outside the prescriptive path and wants a rebar schedule from an engineer.
_PLAIN_CONCRETE_MAX_FILL_FT: dict[tuple[float, int], float] = {
    (6.0, 30): 4.0, (6.0, 45): 4.0, (6.0, 60): 4.0,
    (8.0, 30): 5.0, (8.0, 45): 5.0, (8.0, 60): 4.0,
    (10.0, 30): 7.0, (10.0, 45): 6.0, (10.0, 60): 5.0,
    (12.0, 30): 8.0, (12.0, 45): 7.0, (12.0, 60): 6.0,
}


def _advisory(cid: str, msg: str, tags: tuple[str, ...], result: Result,
              fix_hint: str | None = None) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid,
                   message=f"[advisory, not engineering] {msg}", element_tags=tags,
                   result=result, fix_hint=fix_hint)


def _unknown(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=f"UNKNOWN — {msg}",
                   element_tags=tags, result=Result.UNKNOWN)


def _structural_thickness_in(ctx: CheckContext, assembly_tag: str) -> float | None:
    """The nominal thickness of the assembly's concrete STRUCTURE layer, in inches.

    The wall's *total* thickness is the wrong number: CATLIN_BASEMENT_12 is 12" of concrete
    plus damp-proofing plus 4" of XPS, and the foam retains nothing.
    """
    assembly = next((a for a in ctx.plan.library.assemblies if a.tag == assembly_tag), None)
    if assembly is None:
        return None
    for layer in assembly.layers:
        if layer.function is LayerFunction.STRUCTURE:
            # Rounded to the nominal 1/2": `.inches` comes back off a metres round-trip, so a
            # 12" layer arrives as 12.000000000000002 and misses the table key exactly.
            return round(layer.thickness.inches * 2.0) / 2.0
    return None


def _unbalanced_fill_ft(wall, grade_m: float) -> float | None:
    """How much backfill this wall retains, authored or derived.

    Derived, when not authored: from grade down to the bottom of the wall, clamped at zero.
    That is a *conservative proxy*, and deliberately so — the real unbalanced height depends
    on the finished grade at each face and on whether a slab braces the inside, neither of
    which the model carries. It over-reports a walkout wall whose exterior grade falls away,
    which is the safe direction to be wrong in; author ``unbalanced_fill`` where it matters.
    """
    if wall.unbalanced_fill is not None:
        return wall.unbalanced_fill.meters / _M_PER_FT
    if wall.top_elevation is None or wall.bottom_elevation is None:
        return None
    top = min(grade_m, wall.top_elevation.meters)
    return max(0.0, top - wall.bottom_elevation.meters) / _M_PER_FT


@check(Tier.STRUCTURAL, "structural.foundation_unbalanced_fill")
def foundation_unbalanced_fill(ctx: CheckContext) -> list[Finding]:
    """Plain concrete foundation walls against the IRC R404.1.2(1) unbalanced-fill limits.

    Findings are aggregated by (assembly, fill height) rather than emitted per wall: sixteen
    identical 12" walls retaining 9' of the same soil are one condition and one decision, and
    sixteen copies of it would bury the two that differ.
    """
    from typehaus.model.structure import FoundationWall

    cid = "structural.foundation_unbalanced_fill"
    profile = ctx.profile
    soil_class = getattr(profile, "soil_class", None) if profile is not None else None
    if soil_class is None:
        return [_unknown(cid, "the jurisdiction profile declares no soil_class, so no "
                              "equivalent-fluid pressure column of IRC Table R404.1.2(1) "
                              "applies")]
    lateral = _SOIL_LATERAL_PSF_PER_FT.get(soil_class.upper())
    if lateral is None:
        return [_unknown(cid, f"soil class {soil_class!r} is not one of the IRC Table R405.1 "
                              "groups this table is indexed on")]

    grade = ctx.plan.project.site.grade
    if grade is None:
        return [_unknown(cid, "the site declares no grade datum to measure backfill against")]
    grade_m = grade.meters

    walls = [w for w in ctx.plan.all_elements() if isinstance(w, FoundationWall)]
    if not walls:
        return []

    # (assembly, thickness, rounded fill ft, engineering_spec) → the wall tags in it.
    groups: dict[tuple, list[str]] = {}
    unknowns: dict[str, list[str]] = {}
    for wall in walls:
        thickness = _structural_thickness_in(ctx, wall.assembly)
        fill_ft = _unbalanced_fill_ft(wall, grade_m)
        if thickness is None or fill_ft is None:
            reason = ("the assembly declares no concrete STRUCTURE layer to read a thickness "
                      "from" if thickness is None else
                      "neither unbalanced_fill nor top/bottom elevations are authored")
            unknowns.setdefault(reason, []).append(wall.tag)
            continue
        if round(fill_ft, 1) <= 0.0:
            continue  # retains nothing — an interior cross wall, or a wall entirely above grade
        key = (wall.assembly, thickness, round(fill_ft, 1), wall.engineering_spec)
        groups.setdefault(key, []).append(wall.tag)

    out: list[Finding] = []
    for reason, tags in sorted(unknowns.items()):
        out.append(_unknown(cid, f"{len(tags)} foundation wall(s) — {reason}",
                            tuple(sorted(tags))))

    for (assembly, thickness, fill_ft, spec), tags in sorted(
            groups.items(), key=lambda item: (item[0][0], -item[0][2])):
        tags = sorted(tags)
        where = (f"{len(tags)} {assembly} wall(s) at {thickness:.0f}\" concrete retaining "
                 f"{fill_ft:.1f}' of unbalanced fill ({soil_class}, {lateral} psf/ft)")
        if spec:
            out.append(_advisory(cid, f"{where} — engineered design authored: {spec}",
                                 tuple(tags), Result.PASS))
            continue
        allowable = _PLAIN_CONCRETE_MAX_FILL_FT.get((thickness, lateral))
        if allowable is None:
            thickest = max(t for t, p in _PLAIN_CONCRETE_MAX_FILL_FT if p == lateral)
            beyond = ("thicker than the table's " f"{thickest:.0f}\" maximum"
                      if thickness > thickest else "not a tabulated plain-concrete section")
            out.append(_unknown(
                cid, f"{where}: {beyond}, so IRC Table R404.1.2(1) does not answer it — "
                     "engineered", tuple(tags)))
        elif fill_ft <= allowable + 1e-6:
            out.append(_advisory(
                cid, f"{where} is within the {allowable:.0f}' plain-concrete limit",
                tuple(tags), Result.PASS))
        else:
            out.append(_advisory(
                cid, f"{where} exceeds the {allowable:.0f}' plain-concrete limit — an "
                     "engineered design (typically a vertical reinforcement schedule) is "
                     "required", tuple(tags), Result.FAIL,
                fix_hint="author FoundationWall.engineering_spec with the engineer's "
                         "reinforcement schedule once it lands"))
    return out
