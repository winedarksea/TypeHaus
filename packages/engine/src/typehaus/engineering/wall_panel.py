"""A cladding panel spanning open girts — ``wall_panel/<Wall tag>``.

**Why this item exists at all.** A face-fastened PBR panel at these spacings is covered by
an evaluation report (ICC-ES ESR-4729), which is a prescriptive path: a reviewer reads the
report's own table and the question is closed. A CONCEALED-fastener profile over OPEN
FRAMING is not in that report, or in any other. Its only published capacity is the
manufacturer's own span table, its manufacturers disagree about whether open girts are
permitted at all, and the limit state that actually governs it — withdrawal of the hidden
leg's screws — is published by nobody at any spacing. Western States says so in as many
words: "consult a design engineer for load and design calculations."

That is decision #65's case exactly. The requirement does not become an UNKNOWN with a
paragraph of prose behind it; it becomes an ENGINEERED item with a name, a computed demand,
and a written statement of the one input a seal has to supply.

What this module computes and what it deliberately does not
-----------------------------------------------------------
* **The demand is computed, in full.** ASCE 7-16 Chapter 30 Part 1 components-and-cladding
  wall pressures at the building's mean roof height, Zone 5 (corner) because a wall panel
  runs through both zones and is ordered as one product, brought to ASD at 0.6W (§2.4.1) so
  it can be set beside an allowable.
* **The bending capacity is READ, never derived.** A rolled panel's section modulus is a
  manufacturer's fact; this engine does not own one. It comes off
  ``Material.panel_allowable_psf`` / ``panel_allowable_span_in``, and a declared span that
  does not match the model's own girt spacing is reported rather than interpolated.
* **The governing limit state is NOT computed, and the record says so.** Concealed-leg
  screw withdrawal is what fails these panels, and no manufacturer publishes it. The record
  is therefore INCOMPLETE **even when the bending ratio passes** — which is the whole point:
  a panel that clears the only table anybody published has not thereby been designed.

**Oracle.** ``houses/catlin/notes/board_batten_girt_span.md``, hand-worked in a separate
pass; ``tests/test_wall_panel_calcs.py`` reproduces it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus import wind
from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys

KIND = "wall_panel"

#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
BASIS_VERSION = "1"
BASIS = "ASCE 7-16 §30.3 (C&C, walls) with §2.4.1 0.6W; manufacturer span table"

#: ASCE 7-16 Table 26.13-1, enclosed building. Applied with the sign that makes suction
#: worse, which is the case a cladding panel is ordered against.
GC_PI = 0.18

#: ASCE 7-16 Fig. 30.3-1, walls of an enclosed low-rise building: negative GC_p at the two
#: ends of the figure's log axis, for the CORNER zone (Zone 5) and the FIELD zone (Zone 4).
#: A panel is one product running through both, so Zone 5 governs what gets ordered.
_GCP_NEGATIVE = {
    "5": ((10.0, -1.4), (500.0, -0.8)),
    "4": ((10.0, -1.1), (500.0, -0.8)),
}


def external_pressure_coefficient(area_ft2: float, zone: str = "5") -> float:
    """GC_p for a wall, log-interpolated across Fig. 30.3-1's own axis.

    Held flat outside 10-500 ft2 because the figure is: below 10 ft2 the curve is drawn
    horizontal, and a cladding panel's effective wind area is always down there.
    """
    (small_area, small), (large_area, large) = _GCP_NEGATIVE[zone]
    if area_ft2 <= small_area:
        return small
    if area_ft2 >= large_area:
        return large
    fraction = (math.log10(area_ft2) - math.log10(small_area)) / (
        math.log10(large_area) - math.log10(small_area))
    return small + fraction * (large - small)


def effective_wind_area_ft2(span_in: float) -> float:
    """ASCE 7-16 §26.2: span x effective width, where the width is not less than span/3.

    A wall panel's real coverage (20", 32", 36") is wider than ``span/3`` at any of this
    house's girt spacings, so taking ``span/3`` is the SMALLER area and therefore the more
    negative GC_p — the conservative side, and the side that needs no product dimension the
    model may not carry. At every spacing a girt wall uses it lands well under 10 ft2, where
    the figure is flat, so the choice changes no coefficient here.
    """
    span_ft = span_in / 12.0
    return span_ft * (span_ft / 3.0)


@dataclass(frozen=True)
class _Panel:
    """One wall's cladding panel, with the girt band that carries it."""

    wall_tag: str
    material_ref: str
    support_spacing_in: float
    allowable_psf: float | None
    allowable_span_in: float | None
    mean_roof_height_ft: float


def _mean_roof_height_ft(ctx: EngineeringContext) -> float | None:
    """h for q_h — the mean of eave and ridge over the tallest roof in the model.

    Per-building would be better and this model has no building grouping to ask; the tallest
    roof is the conservative reading, and on a site whose outbuilding is 10 ft shorter it is
    the house's own.
    """
    heights = [(roof.eave_z_m + roof.ridge_z_m) / 2.0 for roof in ctx.model.roofs
               if roof.eave_z_m is not None and roof.ridge_z_m is not None]
    if not heights:
        return None
    return max(heights) / 0.3048


def _panels(ctx: EngineeringContext) -> list[_Panel]:
    """Every wall whose outermost skin is a CONCEALED metal panel on open framing.

    The three conditions are the definition of the gap this item fills, and each one is read
    off the model rather than off a tag: the layer declares ``skin_family`` (it is one of the
    building's metal skins), it does NOT declare ``exposed_fastener`` (so no evaluation
    report's face-fastened table reaches it), and the layer immediately inboard of it carries
    a ``FramingSpec`` with a spacing (it spans open girts, rather than bearing on a
    continuous deck).
    """
    catalog = {material.tag: material for material in ctx.plan.library.materials}
    height = _mean_roof_height_ft(ctx)
    out: list[_Panel] = []
    for wall in ctx.model.walls:
        body = wall.body_layers()
        if len(body) < 2:
            continue
        skin, backing = body[-1], body[-2]
        material = catalog.get(skin.material_ref or "")
        if material is None or getattr(material, "skin_family", None) is None:
            continue
        if getattr(material, "exposed_fastener", False):
            continue
        spacing = _framing_spacing_in(ctx, wall, backing.name)
        if spacing is None:
            continue
        out.append(_Panel(
            wall_tag=wall.tag, material_ref=skin.material_ref or "",
            support_spacing_in=spacing,
            allowable_psf=getattr(material, "panel_allowable_psf", None),
            allowable_span_in=getattr(material, "panel_allowable_span_in", None),
            mean_roof_height_ft=height or 0.0))
    return out


def _framing_spacing_in(ctx: EngineeringContext, wall: object,
                        layer_name: str) -> float | None:
    """The spacing of the named layer's framing band, in inches, or ``None``.

    Read off the ASSEMBLY rather than the resolved layer: a ``layer_materials`` override
    swaps a material and never a ``FramingSpec``, so the assembly is where the girt band
    still is.
    """
    tag = getattr(wall, "assembly", None)
    assembly = next((a for a in ctx.plan.library.assemblies if a.tag == tag), None)
    if assembly is None:
        return None
    layer = next((lay for lay in assembly.layers if lay.name == layer_name), None)
    framing = getattr(layer, "framing", None) if layer is not None else None
    spacing = getattr(framing, "spacing", None) if framing is not None else None
    return None if spacing is None else float(spacing.inches)


@keys(KIND)
def enumerate_panels(ctx: EngineeringContext) -> list[str]:
    return [panel.wall_tag for panel in _panels(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, panel) for panel in _panels(ctx)]


def _one(ctx: EngineeringContext, panel: _Panel) -> EngineeringRecord:
    ident = item_id(KIND, panel.wall_tag)
    basis = wind.wind_basis(ctx.plan.project.site)
    missing: list[str] = []
    if basis is None:
        missing.append("a complete design wind basis on Site "
                       "(design_wind_speed_mph, wind_exposure, risk_category)")
    if panel.mean_roof_height_ft <= 0.0:
        missing.append("a resolved roof to take the mean roof height from")
    if basis is None or panel.mean_roof_height_ft <= 0.0:
        return EngineeringRecord(
            item_id=ident, kind=KIND, key=panel.wall_tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{panel.wall_tag}: the cladding wind demand could not be computed",
            missing=tuple(missing), element_tags=(panel.wall_tag,))

    q_h = wind.velocity_pressure_psf(basis, panel.mean_roof_height_ft)
    area = effective_wind_area_ft2(panel.support_spacing_in)
    gcp = external_pressure_coefficient(area, "5")
    gcp_field = external_pressure_coefficient(area, "4")
    strength_psf = abs(q_h * (gcp - GC_PI))
    demand_psf = wind.ASD_WIND_FACTOR * strength_psf
    field_psf = wind.ASD_WIND_FACTOR * abs(q_h * (gcp_field - GC_PI))

    states: list[LimitState] = []
    # ** THE MISSING INPUT IS NAMED WHETHER OR NOT BENDING PASSES, and that is the point. **
    missing.append(
        f"the concealed-leg screw WITHDRAWAL allowable for {panel.material_ref} at "
        f"{panel.support_spacing_in:g}\" supports — the limit state that governs this panel, "
        f"published by no manufacturer at any spacing")
    if panel.allowable_psf is None or panel.allowable_span_in is None:
        missing.append(
            f"Material.panel_allowable_psf and panel_allowable_span_in on "
            f"{panel.material_ref} — the manufacturer's published allowable uniform load "
            f"and the span it was read at")
    elif abs(panel.allowable_span_in - panel.support_spacing_in) > 0.01:
        missing.append(
            f"an allowable read at this wall's own {panel.support_spacing_in:g}\" support "
            f"spacing — {panel.material_ref} declares {panel.allowable_psf:g} psf at "
            f"{panel.allowable_span_in:g}\", and a span table is not interpolated here")
    else:
        states.append(LimitState(
            "panel bending, negative (suction)", demand_psf, panel.allowable_psf, "psf",
            f"ASCE 7-16 Fig. 30.3-1 zone 5 at {area:.2f} ft2, §2.4.1 0.6W, against the "
            f"manufacturer's published allowable at {panel.allowable_span_in:g}\""))

    inputs = (
        Quantity("design_wind_speed", basis.speed_mph, "mph", 1.0),
        Quantity("mean_roof_height", panel.mean_roof_height_ft, "ft", 0.01),
        Quantity("velocity_pressure", q_h, "psf", 0.01),
        Quantity("support_spacing", panel.support_spacing_in, "in", 0.25),
        Quantity("effective_wind_area", area, "ft2", 0.01),
        Quantity("GCp_zone5", gcp, "", 0.01),
        Quantity("GCpi", GC_PI, "", 0.01),
        Quantity("suction_asd", demand_psf, "psf", 0.01),
    )
    notes = [
        f"Zone 5 (corner) governs the ORDER: a wall panel is one product and runs through "
        f"both zones. Zone 4 (field) on the same wall is {field_psf:.1f} psf ASD against "
        f"zone 5's {demand_psf:.1f}.",
        f"Strength-level suction is {strength_psf:.1f} psf; {demand_psf:.1f} psf is that at "
        f"0.6W (ASCE 7-16 §2.4.1), which is the basis every allowable this house cites is "
        f"published on. Comparing a published allowable against the strength-level number "
        f"is the mistake this line exists to prevent.",
        f"Wind basis: {basis.describe()}, K_zt {wind.K_ZT_FLAT:g}, K_d "
        f"{wind.K_D_BUILDINGS:g}, K_e taken as 1.0 (ASCE 7-16 §26.9).",
        "NOT CHECKED, and no seal should read this as covering them: withdrawal of the "
        "concealed leg's fasteners (the governing limit state), the girt itself in bending "
        "and its block-to-stud connection, panel deflection, thermal movement of a "
        "continuous run, and whether the manufacturer permits open framing at all — of "
        "eight surveyed, only two do, and substituting one of the other six forces a second "
        "girt course or a continuous deck.",
        "An evaluation report would close this item outright. There is none for a "
        "concealed-fastener profile over open girts, which is why it is here.",
    ]

    # OVER wins over INCOMPLETE: a panel whose bending is over its published allowable is
    # not "not yet designed", it is a panel that failed the one table anybody printed.
    over = any(not state.ok for state in states)
    status = Status.OVER if over else Status.INCOMPLETE
    return EngineeringRecord(
        item_id=ident, kind=KIND, key=panel.wall_tag,
        basis_version=BASIS_VERSION, basis=BASIS, status=status,
        summary=(f"{panel.wall_tag} clad in {panel.material_ref} over "
                 f"{panel.support_spacing_in:g}\" open girts: {demand_psf:,.1f} psf ASD "
                 f"corner-zone suction"),
        inputs=inputs, limit_states=tuple(states), missing=tuple(missing),
        notes=tuple(notes), element_tags=(panel.wall_tag,))
