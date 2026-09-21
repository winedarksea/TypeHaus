"""Segmental (SRW) gravity retaining wall — the unit's own free body.

``tiered_retaining/<FoundationWall tag>``: a wall that retains fill, declares no lateral support
and stands on no footing — in practice a dry-stacked unit on a levelling pad. Until 2026-09-20
this kind was a deferral; nothing computed whether the wall stands up.

**The free body.** A rigid block `B` deep and `H = H_r + D` high: the retained height is the
authored ``unbalanced_fill`` (never ``drop_ft`` — the R404.1.1 trap in
``params/raised_garden.py``), the embedment `D` is the nearest grade station down to the base.
The active EFP triangle runs the full `H`; **no passive is credited on `D`** — it is trench
backfill. Graded: sliding on the levelling pad, overturning about the toe, bearing (or, when
the resultant is off the base, how far off), course interface shear, base-course embedment,
and tier independence against a taller parallel wall within 2H.

**What this is not.** Not ``retaining_wall``: its ``_retaining_walls`` is deliberately not
widened here — an isolated-cantilever record for a footingless unit is the wrong free body.
Not a published chart read either: ``SegmentalWallSpec.published`` corroborates at most, and is
refused unless its guards are answered (:func:`published_refusal`).

**NOT GRADED** (the deferral's deliverable): global stability of both tiers on a common
failure surface against a measured soil profile — the geotechnical engineer's; the unit, any
reinforcement and the pad — the SRW supplier's engineer's. The surcharge on a parallel lower
wall is graded on ITS record (``tier_surcharge``, via :func:`reading`).

Oracle: ``notes/raised_garden_srw.md``, reproduced by ``tests/test_segmental_wall.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Scope,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by
from typehaus.engineering.retaining_basis import REQUIRED_FS, _base_interface
from typehaus.engineering.soil import SOIL_UNIT_WEIGHT_BAND_PCF, presumptive

KIND = "tiered_retaining"
BASIS = ("IRC R404.4; IBC 1610.1 / 1806.2 presumptive values; rigid gravity free body of a "
         "segmental unit wall")
#: 1 -> 2: GM active EFP 45 -> 40 (IBC Table 1610.1, ``soil.py``).
BASIS_VERSION = "2"

#: Base-course embedment floor, and the H/10 rule beside it.
MIN_EMBEDMENT_IN = 6.0
#: Two walls are designed independently only if the clear offset is >= 2 x the lower height.
TIER_FACTOR = 2.0
#: Axes within 10 degrees are parallel tiers; a perpendicular abutment is a corner.
_PARALLEL_SIN = math.sin(math.radians(10.0))
_M_PER_FT = 0.3048
_KG_M3_PER_PCF = 16.018463

oracled_by(KIND, Oracle(note="raised_garden_srw.md", section="§3-§6",
                        test="tests/test_segmental_wall.py"))


@dataclass(frozen=True)
class Section:
    """The wall as the free body sees it, feet and pcf."""

    retained_ft: float
    embedment_ft: float
    unit_depth_ft: float
    unit_weight_pcf: float
    batter_deg: float = 0.0
    course_ft: float = 0.5

    @property
    def height_ft(self) -> float:
        return self.retained_ft + self.embedment_ft


@dataclass(frozen=True)
class FreeBody:
    thrust_plf: float
    weight_plf: float
    resisting_moment: float
    overturning_moment: float
    fs_sliding: float
    fs_overturning: float
    #: Resultant's distance from the toe; <= 0 means off the base.
    resultant_ft: float
    eccentricity_ft: float
    #: Peak toe pressure, psf; ``None`` where the resultant is off the base.
    bearing_psf: float | None
    course_shear_plf: float


def analyse(section: Section, efp_psf_per_ft: float, friction: float) -> FreeBody:
    """Plain numbers in, so the oracle test can drive it from the note's own table."""
    h, b = section.height_ft, section.unit_depth_ft
    thrust = 0.5 * efp_psf_per_ft * h * h
    overturning = thrust * h / 3.0
    weight = section.unit_weight_pcf * b * h
    # A battered prism's centroid sits back of the toe by B/2 plus half its lean.
    lean = h * math.tan(math.radians(section.batter_deg)) / 2.0
    resisting = weight * (b / 2.0 + lean)
    x = (resisting - overturning) / weight
    e = b / 2.0 - x
    if x <= 0.0:
        bearing = None
    elif e <= b / 6.0:
        bearing = weight / b * (1.0 + 6.0 * e / b)
    else:
        bearing = 2.0 * weight / (3.0 * x)
    above_base_course = max(h - section.course_ft, 0.0)
    return FreeBody(
        thrust_plf=thrust, weight_plf=weight, resisting_moment=resisting,
        overturning_moment=overturning,
        fs_sliding=friction * weight / thrust, fs_overturning=resisting / overturning,
        resultant_ft=x, eccentricity_ft=e, bearing_psf=bearing,
        course_shear_plf=0.5 * efp_psf_per_ft * above_base_course ** 2,
    )


# --- scope ----------------------------------------------------------------------------------

def _footingless_walls(ctx: EngineeringContext) -> list:
    from typehaus.model.structure import Footing, FoundationWall

    hosted = {f.under for f in ctx.plan.all_elements() if isinstance(f, Footing)}
    return [w for w in ctx.plan.all_elements()
            if isinstance(w, FoundationWall) and w.tag not in hosted]


def segmental_walls(ctx: EngineeringContext) -> list:
    """Retains fill, declares no restraint, has no footing — disjoint from
    ``retaining_wall``'s ``lateral_support`` scope by construction."""
    out = []
    for wall in _footingless_walls(ctx):
        if getattr(wall, "lateral_support", None) is not None:
            continue
        fill = getattr(wall, "unbalanced_fill", None)
        if fill is not None and fill.meters > 0.0:
            out.append(wall)
    return sorted(out, key=lambda w: w.tag)


@keys(KIND)
def _keys(ctx: EngineeringContext) -> list[str]:
    return [wall.tag for wall in segmental_walls(ctx)]


# --- geometry off the model ----------------------------------------------------------------

@dataclass(frozen=True)
class Tier:
    tag: str
    lower_height_ft: float
    clear_ft: float
    parallel: bool


def _footprint(resolved):  # type: ignore[no-untyped-def]
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    rings = [Polygon(layer.polygon) for layer in resolved.layers
             if not layer.is_cavity and len(layer.polygon) >= 3]
    return unary_union([r for r in rings if r.is_valid and r.area > 0]) if rings else None


def _direction(axis) -> tuple[float, float]:  # type: ignore[no-untyped-def]
    (ax, ay), (bx, by) = axis
    length = math.hypot(bx - ax, by - ay) or 1.0
    return (bx - ax) / length, (by - ay) / length


def _overlaps_along(axis, other) -> bool:  # type: ignore[no-untyped-def]
    """Whether ``other``'s axis projects onto a positive length of ``axis``."""
    (ax, ay), _ = axis
    ux, uy = _direction(axis)
    span = math.hypot(axis[1][0] - ax, axis[1][1] - ay)
    ts = sorted((px - ax) * ux + (py - ay) * uy for px, py in other)
    return min(ts[1], span) - max(ts[0], 0.0) > 1e-6


def lower_tiers(ctx: EngineeringContext, wall) -> list[Tier]:  # type: ignore[no-untyped-def]
    """Every taller RETAINING wall (authored ``unbalanced_fill`` above this wall's) whose clear
    offset is inside ``TIER_FACTOR`` x its height, parallel or not."""
    from typehaus.model.structure import FoundationWall

    resolved = {w.tag: w for w in ctx.model.walls}
    here = resolved.get(wall.tag)
    mine = _footprint(here) if here is not None else None
    if mine is None or wall.unbalanced_fill is None:
        return []
    ux, uy = _direction(here.axis)
    out = []
    for other in ctx.plan.all_elements():
        if not isinstance(other, FoundationWall) or other.tag == wall.tag:
            continue
        fill = other.unbalanced_fill
        if fill is None or fill.meters <= wall.unbalanced_fill.meters:
            continue
        # A basement wall braced by its floors does not rotate as a tier.
        if getattr(other, "lateral_support", None) == "top_and_bottom":
            continue
        theirs = resolved.get(other.tag)
        shape = _footprint(theirs) if theirs is not None else None
        if shape is None:
            continue
        lower = fill.meters / _M_PER_FT
        clear = mine.distance(shape) / _M_PER_FT
        if clear >= TIER_FACTOR * lower:
            continue
        vx, vy = _direction(theirs.axis)
        parallel = (abs(ux * vy - uy * vx) < _PARALLEL_SIN
                    and _overlaps_along(here.axis, theirs.axis))
        out.append(Tier(other.tag, lower, clear, parallel))
    return sorted(out, key=lambda t: (t.clear_ft, t.tag))


def _embedment_ft(ctx: EngineeringContext, wall) -> tuple[float, str]:  # type: ignore[no-untyped-def]
    """Yard above the base, from the nearest grade station (else ``Site.grade``)."""
    from shapely.geometry import Point

    from typehaus.resolve.site_earth import nearest_grade_station, site_grade_elevation_m

    resolved = next((w for w in ctx.model.walls if w.tag == wall.tag), None)
    grade, label = site_grade_elevation_m(ctx.model), "Site.grade"
    if resolved is not None:
        (ax, ay), (bx, by) = resolved.axis
        station = nearest_grade_station(ctx.model, Point((ax + bx) / 2.0, (ay + by) / 2.0))
        if station is not None:
            label, grade = station
    return (grade - wall.bottom_elevation.meters) / _M_PER_FT, label


def _structure_layer(ctx: EngineeringContext, wall):  # type: ignore[no-untyped-def]
    from typehaus.model.enums import LayerFunction

    assembly = ctx.plan.library.resolve_assembly(wall.assembly)
    for layer in (assembly.layers if assembly is not None else ()):
        if layer.function is LayerFunction.STRUCTURE:
            return layer
    return None


def _drainage_layers(ctx: EngineeringContext, wall) -> list[str]:  # type: ignore[no-untyped-def]
    from typehaus.model.enums import LayerFunction

    assembly = ctx.plan.library.resolve_assembly(wall.assembly)
    return [layer.name for layer in (assembly.layers if assembly is not None else ())
            if layer.function is LayerFunction.DRAINAGE]


def published_refusal(ctx: EngineeringContext, wall, tiers: list[Tier]) -> str | None:  # type: ignore[no-untyped-def]
    """Why the authored chart row cannot describe this wall, or ``None``.

    Every guard a gravity chart assumes and the model can answer; an unanswered guard is a
    mismatch, not agreement (``published._drift``).
    """
    spec = getattr(wall, "srw", None)
    row = getattr(spec, "published", None)
    if row is None:
        return None
    if not _drainage_layers(ctx, wall):
        return f"assembly {wall.assembly} declares no DRAINAGE layer behind the unit"
    if spec.batter_deg is None:
        return "no batter is stated on the SegmentalWallSpec"
    if not spec.cap:
        return "no cap unit is modelled"
    height = (wall.top_elevation.meters - wall.bottom_elevation.meters) / _M_PER_FT
    near = [t for t in tiers if t.clear_ft < TIER_FACTOR * height]
    if near:
        return (f"{near[0].tag} ({near[0].lower_height_ft:.2f}' retained) stands "
                f"{near[0].clear_ft:.2f}' away, inside 2H = {TIER_FACTOR * height:.2f}'")
    if row.span.feet + 1e-6 < height:
        return f"the row publishes {row.span.feet:.2f}' and the wall is {height:.2f}'"
    return None


# --- the record -------------------------------------------------------------------------------

def _incomplete(tag: str, missing: list[str]) -> EngineeringRecord:
    return EngineeringRecord(
        item_id=item_id(KIND, tag), kind=KIND, key=tag, basis_version=BASIS_VERSION,
        basis=BASIS, status=Status.INCOMPLETE, summary=f"{tag}: the SRW free body could not run",
        missing=tuple(missing), element_tags=(tag,), scope=Scope.SCREENING)


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, wall) for wall in segmental_walls(ctx)]


@dataclass(frozen=True)
class Reading:
    """The wall as read off the model; ``tier_surcharge`` shares it rather than re-reading."""

    section: Section
    soil: object
    base: object
    yard_ft: float            # yard above the base, uncapped (>= 0)
    grade_from: str
    wall_ft: float
    weight_authored: bool

    @property
    def weight_plf(self) -> float:
        """The whole unit on its pad: its own height, not the free body's."""
        return self.section.unit_weight_pcf * self.section.unit_depth_ft * self.wall_ft


def reading(ctx: EngineeringContext, wall) -> tuple[Reading | None, list[str]]:  # type: ignore[no-untyped-def]
    tag = wall.tag
    spec = getattr(wall, "srw", None)
    missing: list[str] = []
    soil = presumptive(getattr(ctx, "soil_class", None))
    if soil is None:
        missing.append("a declared soil class (Site/profile soil_class)")
    if wall.top_elevation is None or wall.bottom_elevation is None:
        missing.append(f"top_elevation/bottom_elevation on {tag}")
    layer = _structure_layer(ctx, wall)
    if layer is None and (spec is None or spec.unit_depth is None):
        missing.append(f"a STRUCTURE layer on {wall.assembly}, or srw.unit_depth")
    material = ctx.plan.library.material(layer.material_ref) if layer is not None else None
    density = getattr(material, "density", None)
    if (spec is None or spec.unit_weight_pcf is None) and not density:
        missing.append(f"srw.unit_weight_pcf on {tag} (its material carries no density)")
    if missing:
        return None, missing

    # Unit weight: the product's, else the material's density — a solid-unit UPPER bound on
    # resistance, so a FAIL on it is robust and a PASS on it is not (see the status below).
    weight_authored = spec is not None and spec.unit_weight_pcf is not None
    unit_pcf = spec.unit_weight_pcf if weight_authored else density / _KG_M3_PER_PCF
    depth_ft = (spec.unit_depth.feet if spec is not None and spec.unit_depth is not None
                else round(layer.thickness.inches * 2.0) / 24.0)
    batter = spec.batter_deg if spec is not None and spec.batter_deg is not None else 0.0
    coursing = getattr(getattr(layer, "masonry", None), "coursing", None)
    embedment, grade_from = _embedment_ft(ctx, wall)
    embedment = max(embedment, 0.0)
    retained = wall.unbalanced_fill.meters / _M_PER_FT
    wall_ft = (wall.top_elevation.meters - wall.bottom_elevation.meters) / _M_PER_FT
    section = Section(retained_ft=retained, unit_depth_ft=depth_ft, unit_weight_pcf=unit_pcf,
                      embedment_ft=min(embedment, max(wall_ft - retained, 0.0)),
                      batter_deg=batter, course_ft=coursing.feet if coursing is not None else 0.5)
    return Reading(section, soil, _base_interface(ctx, wall) or soil, embedment, grade_from,
                   wall_ft, weight_authored), []


def _one(ctx: EngineeringContext, wall) -> EngineeringRecord:  # type: ignore[no-untyped-def]
    tag = wall.tag
    spec = getattr(wall, "srw", None)
    read, missing = reading(ctx, wall)
    if read is None:
        return _incomplete(tag, missing)
    section, soil, base, embedment = read.section, read.soil, read.base, read.yard_ft
    grade_from, wall_ft, weight_authored = read.grade_from, read.wall_ft, read.weight_authored
    retained, depth_ft, batter = section.retained_ft, section.unit_depth_ft, section.batter_deg
    # The fill cannot stand above the wall: where the yard and the authored retained height
    # overshoot the top, the free body is the wall's own height (and the note says so).
    overtopped = retained + embedment - wall_ft
    body = analyse(section, soil.active_efp_psf_per_ft, base.friction_coefficient)
    tiers = lower_tiers(ctx, wall)

    states = [
        LimitState("sliding", REQUIRED_FS, body.fs_sliding, "",
                   f"IRC R404.4; friction {base.friction_coefficient:.2f} on the levelling "
                   f"pad, IBC Table 1806.2 class {base.ibc_class}", is_safety_factor=True),
        LimitState("overturning", REQUIRED_FS, body.fs_overturning, "",
                   "IRC R404.4, about the toe", is_safety_factor=True),
        LimitState("bearing", body.bearing_psf, base.allowable_bearing_psf, "psf",
                   f"IBC Table 1806.2 class {base.ibc_class} (an allowable)")
        if body.bearing_psf is not None else
        LimitState("bearing — resultant on the base", body.eccentricity_ft,
                   depth_ft / 2.0, "ft",
                   "no bearing pressure exists unless the resultant falls on the base"),
    ]
    shear = spec.interface_shear_lb_per_ft if spec is not None else None
    if shear is not None and body.course_shear_plf > 0.0:
        states.append(LimitState("course interface shear", REQUIRED_FS,
                                 shear / body.course_shear_plf, "",
                                 f"IRC R404.4 on {spec.source}", is_safety_factor=True))
    required_in = max(MIN_EMBEDMENT_IN, section.height_ft * 12.0 / 10.0)
    states.append(LimitState("base-course embedment", required_in, embedment * 12.0, "in",
                             f"max(6\", H/10), to {grade_from}", is_detailing=True))
    parallel = [t for t in tiers if t.parallel and t.clear_ft > 0.0]
    if parallel:
        worst = max(parallel, key=lambda t: t.lower_height_ft / t.clear_ft)
        states.append(LimitState(
            f"tier independence vs {worst.tag}", TIER_FACTOR * worst.lower_height_ft,
            worst.clear_ft, "ft",
            f"clear offset >= 2 x the lower wall's {worst.lower_height_ft:.2f}' retained",
            is_detailing=True))

    over = any(not state.ok for state in states)
    open_inputs = [] if shear is not None else [
        f"the maker's course interface shear (srw.interface_shear_lb_per_ft) — the demand "
        f"is {body.course_shear_plf:,.0f} plf above the base course"]
    if not weight_authored:
        open_inputs.append("the product's in-place unit weight (srw.unit_weight_pcf)")

    refusal = published_refusal(ctx, wall, tiers)
    notes = _notes(ctx, wall, section, soil, base, body, tiers, refusal, weight_authored,
                   grade_from)
    inputs = (
        Quantity("retained_height", section.retained_ft, "ft", 0.01),
        Quantity("embedment", section.embedment_ft, "ft", 0.01),
        Quantity("yard_to_base", embedment, "ft", 0.01),
        Quantity("unit_depth", section.unit_depth_ft, "ft", 0.01),
        Quantity("unit_weight", section.unit_weight_pcf, "pcf", 0.1),
        Quantity("batter", section.batter_deg, "deg", 0.1),
        Quantity("course_height", section.course_ft, "ft", 0.01),
        Quantity("active_efp", soil.active_efp_psf_per_ft, "psf/ft", 1.0),
        Quantity("friction_coefficient", base.friction_coefficient, "", 0.01),
        Quantity("allowable_bearing", base.allowable_bearing_psf, "psf", 1.0),
        Quantity("interface_shear", shear if shear is not None else -1.0, "plf", 1.0),
        *(q for t in tiers for q in (
            Quantity(f"tier_{t.tag}_height", t.lower_height_ft, "ft", 0.01),
            Quantity(f"tier_{t.tag}_clear", t.clear_ft, "ft", 0.01))),
    )
    summary = (f"{tag}: {depth_ft * 12:.0f}\" SRW unit, {section.height_ft:.2f}' free body "
               f"({section.retained_ft:.2f}' retained + {section.embedment_ft * 12:.0f}\" "
               f"embedded, batter {batter:g}°) — sliding FS {body.fs_sliding:.2f}, "
               f"overturning FS {body.fs_overturning:.2f} (IRC R404.4 wants "
               f"{REQUIRED_FS:g})")
    # A FAIL stands whatever the open inputs say (each could only worsen it or leave it);
    # a pass on a fallback unit weight or an ungraded interface does not.
    status = Status.OVER if over else (Status.INCOMPLETE if open_inputs else Status.OK)
    if overtopped > 0.01:
        notes += (f"MISMATCH: {grade_from} puts the ground {embedment * 12:.0f}\" above the "
                  f"base, and the authored {retained:.2f}' retained on top of that is "
                  f"{overtopped * 12:.0f}\" above the wall top. The free body is capped at "
                  f"the wall's own {wall_ft:.2f}'; the two authored inputs disagree here.",)
    if status is Status.OVER:
        notes += tuple(f"Open input: {text}." for text in open_inputs)
    return EngineeringRecord(
        item_id=item_id(KIND, tag), kind=KIND, key=tag, basis_version=BASIS_VERSION,
        basis=BASIS, status=status, summary=summary, inputs=inputs,
        limit_states=tuple(states),
        missing=tuple(open_inputs) if status is Status.INCOMPLETE else (),
        notes=notes, element_tags=(tag,), scope=Scope.SCREENING)


def _notes(ctx, wall, section, soil, base, body, tiers, refusal,  # type: ignore[no-untyped-def]
           weight_authored, grade_from) -> tuple[str, ...]:
    low, high = SOIL_UNIT_WEIGHT_BAND_PCF
    drained = _drainage_layers(ctx, wall)
    out = [
        f"SCREENING on presumptive code values, not a design: {soil.citation}. No "
        "geotechnical report is on file for this site.",
        f"Free body {section.height_ft:.2f}' = {section.retained_ft:.2f}' retained "
        f"(authored unbalanced_fill) + {section.embedment_ft * 12:.1f}\" embedded (to "
        f"{grade_from}). The active triangle runs the full height and NO passive is credited "
        "on the embedment: it is trench backfill.",
        f"Base: {base.soil_class}, friction {base.friction_coefficient:.2f}. A levelling pad "
        "earns the clean-stone row only if its FootingBedding declares "
        "non_frost_susceptible.",
        ("Unit weight from the product data." if weight_authored else
         f"Unit weight {section.unit_weight_pcf:.1f} pcf is the material's SOLID density — an "
         "upper bound for a hollow or infilled unit, so a lighter real unit only fails harder."),
        (f"Batter {section.batter_deg:g}° from the SegmentalWallSpec; EFP publishes no batter "
         "reduction, so batter moves only the restoring arm." if section.batter_deg else
         "No batter is authored; graded vertical, as drawn."),
        f"Soil unit weight ({low:.0f}-{high:.0f} pcf) does not enter: the EFP carries it and "
        "a vertical unit with no heel carries no soil. Both ends of the band are identical.",
        ("Drained face: " + ", ".join(drained) + "." if drained else
         f"No hydrostatic case, and assembly {wall.assembly} declares no DRAINAGE layer, so "
         "the drained-backfill presumption rests on nothing this model carries."),
    ]
    if body.bearing_psf is None:
        out.append(f"The resultant falls {-body.resultant_ft:.2f}' in front of the toe: there "
                   "is no bearing pressure to grade, and the row reports how far off the base "
                   "it is instead.")
    for tier in tiers:
        how = ("a parallel tier: this unit's bearing on its pad is carried onto it as a "
               f"lateral strip surcharge, graded on retaining_wall/{tier.tag}"
               if tier.parallel else
               "not a parallel tier: it meets this unit end-on, so no surcharge is carried "
               "onto it")
        out.append(
            f"TIER: {tier.tag} retains {tier.lower_height_ft:.2f}' and stands "
            f"{tier.clear_ft:.2f}' clear ({how}), inside 2H = "
            f"{TIER_FACTOR * tier.lower_height_ft:.2f}'. The two cannot be designed "
            "independently. Where the lower wall is a closed cast loop "
            "(retaining_system) the classic tiered rotation is suppressed; deep-seated slip "
            "under both is NOT graded here and stays the geotechnical engineer's.")
    if refusal is not None:
        out.append(f"Published chart row REFUSED: {refusal}. It could not close this item "
                   "anyway; the free body governs.")
    elif getattr(getattr(wall, "srw", None), "published", None) is not None:
        out.append("Published chart row: every guard answered. Corroboration only; the free "
                   "body governs.")
    out.append("NOT GRADED: global stability of this wall and any lower one on a common "
               "failure surface against a measured soil profile (geotechnical engineer); the "
               "unit, any geogrid and the pad (the SRW supplier's engineer). No seismic or "
               "frost-heave case. The surcharge on a parallel lower wall IS graded, on that "
               "wall's own record (engineering/tier_surcharge.py).")
    return tuple(out)
