"""Segmental (SRW) gravity retaining wall — the unit's own free body.

``tiered_retaining/<FoundationWall tag>``: a wall that retains fill, declares no lateral support
and stands on no footing — in practice a dry-stacked unit on a levelling pad.

**The free body** (NCMA/Allan Block gravity method, ``srw_gravity``). A rigid unit `B` deep,
battered at its setback, `H = H_r + D` high: the retained height is the authored
``unbalanced_fill`` (never ``drop_ft`` — the R404.1.1 trap in ``params/raised_garden.py``), the
embedment `D` is the nearest grade station down to the base, and **no passive is credited on
`D`** — it is trench backfill. Coulomb thrust with ``δ = ⅔φ``; its vertical component is
credited to sliding and the restoring moment; the base slides at ``tan φ`` of the weaker of the
levelling pad (``FootingBedding.friction_angle_deg``) and the ground, else IBC 1806.2's
coefficient. φ of the ground is read back off IBC 1610.1's EFP at each end of the soil unit
weight band, and both ends are run. A drainage zone behind the unit (``srw_backfill``) makes
the thrust a two-zone trial wedge. Graded: sliding, overturning, bearing (or, off the base,
how far off), course interface shear, base-course embedment, and tier independence against a
taller parallel wall within 2H that faces the SAME way (``srw_tiers``); a back-to-back pair
is named, not graded on that row.

**What this is not.** Not ``retaining_wall``: its ``_retaining_walls`` is deliberately not
widened here. Not a published chart read either: ``SegmentalWallSpec.published`` corroborates
at most, and is refused unless its guards are answered (:func:`published_refusal`).

**NOT GRADED**: global stability of both tiers on a common failure surface — the geotechnical
engineer's; any reinforcement — the SRW supplier's engineer's. The surcharge on a parallel lower
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
from typehaus.engineering.soil import (
    SOIL_UNIT_WEIGHT_BAND_PCF,
    presumptive,
    soil_is_presumed,
    soil_provenance_note,
)
from typehaus.engineering.srw_backfill import confined_note, drainage_zone, zone_note
from typehaus.engineering.srw_gravity import (
    WALL_FRICTION_RATIO,
    FreeBody,
    Section,
    analyse,
    phi_from_efp,
)
from typehaus.engineering.srw_tiers import TIER_FACTOR, Tier, lower_tiers

__all__ = ["KIND", "TIER_FACTOR", "FreeBody", "Section", "Tier", "analyse", "lower_tiers",
           "published_refusal", "reading", "segmental_walls"]

KIND = "tiered_retaining"
BASIS = ("IRC R404.4; NCMA/Allan Block gravity method (Coulomb, δ = 2/3 φ, battered face); "
         "IBC 1610.1 / 1806.2 presumptive values")
#: 1 -> 2: GM active EFP 45 -> 40 (IBC Table 1610.1, ``soil.py``).
#: 2 -> 3: Rankine EFP on a vertical face -> the NCMA gravity method (``srw_gravity``).
#: 3 -> 4: the drainage zone as a two-zone trial wedge; the 2H row for same-facing tiers only.
BASIS_VERSION = "4"

#: Base-course embedment floor, and the H/10 rule beside it.
MIN_EMBEDMENT_IN = 6.0
_M_PER_FT = 0.3048
_KG_M3_PER_PCF = 16.018463

oracled_by(KIND, Oracle(note="raised_garden_srw.md", section="§2-§6",
                        test="tests/test_segmental_wall.py"))


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
    if not _drainage_layers(ctx, wall) and spec.drainage_zone is None:
        return (f"assembly {wall.assembly} declares no DRAINAGE layer and the spec no "
                "drainage_zone behind the unit")
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
    pad_phi_deg: float | None = None
    pad_tag: str | None = None

    @property
    def weight_plf(self) -> float:
        """The whole unit on its pad: its own height, not the free body's."""
        return self.section.unit_weight_pcf * self.section.unit_depth_ft * self.wall_ft


def _pad(ctx: EngineeringContext, wall) -> tuple[float | None, str | None]:  # type: ignore[no-untyped-def]
    """The levelling pad's authored φ, and the bedding that states it."""
    from typehaus.model.structure import FootingBedding

    for bed in ctx.plan.all_elements():
        if (isinstance(bed, FootingBedding) and bed.host_ref == wall.tag
                and bed.friction_angle_deg is not None):
            return bed.friction_angle_deg, bed.tag
    return None, None


def reading(ctx: EngineeringContext, wall) -> tuple[Reading | None, list[str]]:  # type: ignore[no-untyped-def]
    tag = wall.tag
    spec = getattr(wall, "srw", None)
    missing: list[str] = []
    soil = presumptive(getattr(ctx, "soil_class", None),
                       basis=getattr(ctx, "soil_basis", None))
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
    pad_phi, pad_tag = _pad(ctx, wall)
    return Reading(section, soil, _base_interface(ctx, wall) or soil, embedment, grade_from,
                   wall_ft, weight_authored, pad_phi, pad_tag), []


@dataclass(frozen=True)
class _End:
    """One end of the soil unit-weight band, graded."""

    soil_pcf: float
    body: FreeBody
    base_phi_deg: float | None      # None: IBC 1806.2's coefficient stood in
    states: tuple[LimitState, ...]

    @property
    def over(self) -> bool:
        return any(not state.ok for state in self.states)

    @property
    def worst(self) -> float:
        return max(state.ratio for state in self.states if not state.is_detailing)


def _end(read: Reading, soil_pcf: float, spec) -> _End:  # type: ignore[no-untyped-def]
    base, section = read.base, read.section
    phi = phi_from_efp(read.soil.active_efp_psf_per_ft, soil_pcf)
    if read.pad_phi_deg is not None:
        base_phi = min(read.pad_phi_deg, phi)
        mu = math.tan(math.radians(base_phi))
        slide_cite = (f"IRC R404.4; μ = tan {base_phi:.1f}°, the weaker of {read.pad_tag}'s "
                      f"{read.pad_phi_deg:g}° and the ground's {phi:.1f}° (NCMA)")
    else:
        base_phi, mu = None, base.friction_coefficient
        slide_cite = (f"IRC R404.4; friction {mu:.2f}, IBC Table 1806.2 class {base.ibc_class} "
                      "— no pad φ is authored, so the table stands in for tan φ")
    body = analyse(section, soil_pcf, phi, mu, drainage_zone(spec))
    states = [
        LimitState("sliding", REQUIRED_FS, body.fs_sliding, "", slide_cite,
                   is_safety_factor=True),
        LimitState("overturning", REQUIRED_FS, body.fs_overturning, "",
                   "IRC R404.4, about the toe", is_safety_factor=True),
        LimitState("bearing", body.bearing_psf, base.allowable_bearing_psf, "psf",
                   f"IBC Table 1806.2 class {base.ibc_class} (an allowable)")
        if body.bearing_psf is not None else
        LimitState("bearing — resultant on the base", body.eccentricity_ft,
                   section.unit_depth_ft / 2.0, "ft",
                   "no bearing pressure exists unless the resultant falls on the base"),
    ]
    shear = spec.interface_shear_lb_per_ft if spec is not None else None
    if shear is not None and body.course_shear_plf > 0.0:
        states.append(LimitState("course interface shear", REQUIRED_FS,
                                 shear / body.course_shear_plf, "",
                                 f"IRC R404.4 on {spec.source}", is_safety_factor=True))
    return _End(soil_pcf, body, base_phi, tuple(states))


def _one(ctx: EngineeringContext, wall) -> EngineeringRecord:  # type: ignore[no-untyped-def]
    tag = wall.tag
    spec = getattr(wall, "srw", None)
    read, missing = reading(ctx, wall)
    if read is None:
        return _incomplete(tag, missing)
    section, soil, base, embedment = read.section, read.soil, read.base, read.yard_ft
    retained, depth_ft, batter = section.retained_ft, section.unit_depth_ft, section.batter_deg
    tiers = lower_tiers(ctx, wall)

    common: list[LimitState] = []
    required_in = max(MIN_EMBEDMENT_IN, section.height_ft * 12.0 / 10.0)
    common.append(LimitState("base-course embedment", required_in, embedment * 12.0, "in",
                             f"max(6\", H/10), to {read.grade_from}", is_detailing=True))
    # The 2H row is a terrace rule: back-to-back pairs are named in the notes instead.
    parallel = [t for t in tiers if t.parallel and t.clear_ft > 0.0 and not t.back_to_back]
    if parallel:
        worst = max(parallel, key=lambda t: t.lower_height_ft / t.clear_ft)
        common.append(LimitState(
            f"tier independence vs {worst.tag}", TIER_FACTOR * worst.lower_height_ft,
            worst.clear_ft, "ft",
            f"clear offset >= 2 x the lower wall's {worst.lower_height_ft:.2f}' retained",
            is_detailing=True))
    ends = [_end(read, pcf, spec) for pcf in SOIL_UNIT_WEIGHT_BAND_PCF]
    ends = [_End(e.soil_pcf, e.body, e.base_phi_deg, e.states + tuple(common)) for e in ends]
    shown = max(ends, key=lambda e: e.worst)
    body = shown.body

    shear = spec.interface_shear_lb_per_ft if spec is not None else None
    open_inputs = [] if shear is not None else [
        f"the maker's course interface shear (srw.interface_shear_lb_per_ft) — the demand "
        f"is {body.course_shear_plf:,.0f} plf above the base course"]
    if not read.weight_authored:
        open_inputs.append("the product's in-place unit weight (srw.unit_weight_pcf)")

    refusal = published_refusal(ctx, wall, tiers)
    notes = _notes(ctx, wall, read, ends, tiers, refusal)
    inputs = (
        Quantity("retained_height", section.retained_ft, "ft", 0.01),
        Quantity("embedment", section.embedment_ft, "ft", 0.01),
        Quantity("yard_to_base", embedment, "ft", 0.01),
        Quantity("unit_depth", section.unit_depth_ft, "ft", 0.01),
        Quantity("unit_weight", section.unit_weight_pcf, "pcf", 0.1),
        Quantity("batter", section.batter_deg, "deg", 0.1),
        Quantity("course_height", section.course_ft, "ft", 0.01),
        Quantity("active_efp", soil.active_efp_psf_per_ft, "psf/ft", 1.0),
        Quantity("soil_presumed", 1.0 if soil_is_presumed(soil) else 0.0, "-", 0.5),
        Quantity("wall_friction_ratio", WALL_FRICTION_RATIO, "", 0.01),
        Quantity("pad_friction_angle", read.pad_phi_deg if read.pad_phi_deg is not None
                 else -1.0, "deg", 0.1),
        Quantity("friction_coefficient", base.friction_coefficient, "", 0.01),
        Quantity("allowable_bearing", base.allowable_bearing_psf, "psf", 1.0),
        Quantity("interface_shear", shear if shear is not None else -1.0, "plf", 1.0),
        Quantity("drainage_zone_width", spec.drainage_zone.width.feet
                 if spec is not None and spec.drainage_zone is not None else 0.0, "ft", 0.01),
        Quantity("drainage_zone_phi", spec.drainage_zone.friction_angle_deg
                 if spec is not None and spec.drainage_zone is not None else -1.0, "deg", 0.1),
        *(q for t in tiers for q in (
            Quantity(f"tier_{t.tag}_height", t.lower_height_ft, "ft", 0.01),
            Quantity(f"tier_{t.tag}_clear", t.clear_ft, "ft", 0.01),
            Quantity(f"tier_{t.tag}_facing", {True: -1.0, False: 1.0, None: 0.0}[
                t.back_to_back], "", 1.0))),
    )
    summary = (f"{tag}: {depth_ft * 12:.1f}\" SRW unit, {section.height_ft:.2f}' free body "
               f"({retained:.2f}' retained + {section.embedment_ft * 12:.0f}\" embedded, "
               f"batter {batter:g}°) — at {shown.soil_pcf:.0f} pcf sliding FS "
               f"{body.fs_sliding:.2f}, overturning FS {body.fs_overturning:.2f} (IRC R404.4 "
               f"wants {REQUIRED_FS:g})")
    over = [e.over for e in ends]
    missing_out: tuple[str, ...] = ()
    # Retained fill above the wall top: the capped free body is a section neither authored
    # input describes, so it cannot PASS (an OVER at both ends still stands).
    overtopped = retained + embedment - read.wall_ft
    if overtopped > 0.01:
        notes += (f"MISMATCH: {read.grade_from} puts the ground {embedment * 12:.0f}\" above "
                  f"the base, and the authored {retained:.2f}' retained on top of that is "
                  f"{overtopped * 12:.0f}\" above the wall top. The free body is capped at the "
                  f"wall's own {read.wall_ft:.2f}'; the two authored inputs disagree here.",)
    if overtopped > 0.01 and not all(over):
        status = Status.INCOMPLETE
        missing_out = (f"agreement between {tag}'s unbalanced_fill ({retained:.2f}') and "
                       f"{read.grade_from}: together they put fill {overtopped * 12:.0f}\" "
                       f"above the wall top, and the free body is capped at a section "
                       f"neither describes", *open_inputs)
    elif all(over):
        # A FAIL at both ends stands whatever the open inputs say.
        status = Status.OVER
        notes += tuple(f"Open input: {text}." for text in open_inputs)
    elif any(over):
        status = Status.INCOMPLETE
        low, high = SOIL_UNIT_WEIGHT_BAND_PCF
        missing_out = (f"a measured soil friction angle and unit weight: the free body checks "
                       f"at one end of {low:.0f}-{high:.0f} pcf and not the other",
                       *open_inputs)
    else:
        status = Status.INCOMPLETE if open_inputs else Status.OK
        missing_out = tuple(open_inputs)
    return EngineeringRecord(
        item_id=item_id(KIND, tag), kind=KIND, key=tag, basis_version=BASIS_VERSION,
        basis=BASIS, status=status, summary=summary, inputs=inputs,
        limit_states=shown.states, missing=missing_out,
        notes=notes, element_tags=(tag,), scope=Scope.SCREENING)


def _notes(ctx, wall, read, ends, tiers, refusal) -> tuple[str, ...]:  # type: ignore[no-untyped-def]
    section, soil, base = read.section, read.soil, read.base
    drained = _drainage_layers(ctx, wall)
    spec = getattr(wall, "srw", None)
    band = "; ".join(
        f"{e.soil_pcf:.0f} pcf: φ {e.body.soil_phi_deg:.1f}°, K_a {e.body.ka:.3f}, sliding "
        f"{e.body.fs_sliding:.2f}, overturning {e.body.fs_overturning:.2f}" for e in ends)
    out = [
        f"SCREENING on presumptive code values, not a design: {soil.citation}.",
        soil_provenance_note(soil),
        f"Free body {section.height_ft:.2f}' = {section.retained_ft:.2f}' retained "
        f"(authored unbalanced_fill) + {section.embedment_ft * 12:.1f}\" embedded (to "
        f"{read.grade_from}). NO passive is credited on the embedment: it is trench backfill.",
        f"{'Two-zone trial-wedge' if drainage_zone(spec) else 'Coulomb'} thrust (K_a below is "
        f"P/½γH²), δ = ⅔φ, on the back face battered {section.batter_deg:g}°, resolved "
        "at δ − ω: its vertical part presses the unit down and is credited to sliding and "
        "the restoring moment. The ground's φ is read back off IBC 1610.1's "
        f"{soil.active_efp_psf_per_ft:g} psf/ft at each end of the unit-weight band — "
        f"{band}.",
        (f"Base: μ = tan φ of the weaker of the levelling pad ({read.pad_tag}, "
         f"{read.pad_phi_deg:g}° authored) and the ground." if read.pad_phi_deg is not None
         else f"Base: no pad φ is authored, so IBC Table 1806.2's {base.soil_class} "
              f"coefficient {base.friction_coefficient:.2f} stands in for tan φ."),
        ("Unit weight from the product data (unit plus core infill)." if read.weight_authored
         else f"Unit weight {section.unit_weight_pcf:.1f} pcf is the material's SOLID density "
              "— an upper bound for a hollow or infilled unit, so a lighter real unit only "
              "fails harder."),
    ]
    body = max(ends, key=lambda e: e.worst).body
    if spec is not None and spec.drainage_zone is not None:
        out.append(zone_note(spec, body))
    elif drained:
        out.append("Drained face: " + ", ".join(drained) + ".")
    else:
        out.append(f"No hydrostatic case, and assembly {wall.assembly} declares no DRAINAGE "
                   "layer, so the drained-backfill presumption rests on nothing this model "
                   "carries.")
    if body.bearing_psf is None:
        out.append(f"The resultant falls {-body.resultant_ft:.2f}' in front of the toe: there "
                   "is no bearing pressure to grade, and the row reports how far off the base "
                   "it is instead.")
    zone = drainage_zone(spec)
    for tier in tiers:
        if tier.parallel:
            out.extend(confined_note(section, e.soil_pcf, e.body, zone, tier) for e in ends)
        if tier.back_to_back:
            out.append(
                f"BACK TO BACK: {tier.tag} retains {tier.lower_height_ft:.2f}' and stands "
                f"{tier.clear_ft:.2f}' clear, facing away from this unit ({tier.facing_basis}). "
                "The two retain one terrace from opposite sides, so the 2H independence row — "
                "a TERRACE rule, an upper wall set back from a lower one facing the same way "
                "(AB Commercial Installation Manual p.60; CMHA SRW-TEC-003) — is not applied. "
                "This is NOT a pass: that rule's two consequences are carried where they are "
                "real — this unit's bearing on its pad as a strip surcharge on "
                f"retaining_wall/{tier.tag} (tier_surcharge), and deep-seated slip under both, "
                "the geotechnical engineer's.")
            continue
        how = ("a parallel tier: this unit's bearing on its pad is carried onto it as a "
               f"lateral strip surcharge, graded on retaining_wall/{tier.tag}; facing "
               f"{'the same way' if tier.back_to_back is False else 'not established'}: "
               f"{tier.facing_basis}"
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
               "failure surface against a measured soil profile (geotechnical engineer); any "
               "geogrid (the SRW supplier's engineer). No seismic or frost-heave case. The "
               "surcharge on a parallel lower wall IS graded, on that wall's own record "
               "(engineering/tier_surcharge.py).")
    return tuple(out)
