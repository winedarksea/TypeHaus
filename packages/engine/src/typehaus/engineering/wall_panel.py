"""A cladding panel spanning open girts — ``wall_panel/<lowest Wall tag in the group>``.

**Why this item exists at all.** A face-fastened PBR panel at these spacings is covered by
an evaluation report (ICC-ES ESR-4729), which is a prescriptive path: a reviewer reads the
report's own table and the question is closed. A CONCEALED-fastener profile over OPEN
FRAMING is in no report. Its bending capacity is published by the manufacturer and nothing
else about it is — the limit state that governs it, withdrawal of the hidden leg's screws,
is a number no panel maker prints. That is decision #65's case exactly: not an UNKNOWN with
a paragraph behind it, but an ENGINEERED item with a name, a computed demand and a capacity
a seal can confirm.

What is read and what is computed
---------------------------------
* **The demand is computed, in full.** ASCE 7-16 Chapter 30 Part 1 components-and-cladding
  wall pressures at the building's mean roof height, Zone 5 (corner) because a wall panel
  runs through both zones and is ordered as one product, brought to ASD at 0.6W (§2.4.1).
* **The bending capacity is READ, never derived.** A rolled panel's section modulus is a
  manufacturer's fact; this engine does not own one. It comes off
  ``Material.panel_allowable_psf`` / ``panel_allowable_span_in``, and a declared span that
  does not match the model's own girt spacing is reported rather than interpolated.
* **The withdrawal capacity is COMPUTED, per NDS 2018 §12.2** — see
  ``wall_panel_withdrawal.py``. It is a rational design from the code's own equation, which
  is what IAPMO UES ER-309 expressly authorises, and it is done here because waiting for a
  published row means waiting for a document nobody is writing.

**One item per (panel, spacing), not per wall.** Twenty walls clad in one product over one
girt course are one design and one seal; twenty identical sheets are twenty chances for a
reviewer to stamp nineteen and miss one. The key is the lowest member tag, so it is stable
under anything but a membership change, and ``panel_count`` is an input so a membership
change stales the seal (``element_tags`` is not hashed). ``haus engineering --item`` on any
member resolves to the group.

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
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import (
    EngineeringContext,
    calc,
    keys,
    oracled_by,
)
from typehaus.engineering.wall_panel_withdrawal import (
    fastener_demand_lb,
    tributary_area_ft2,
    withdrawal_allowable_lb,
)

KIND = "wall_panel"

#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
BASIS_VERSION = "2"
BASIS = ("ASCE 7-16 §30.3 (C&C, walls) with §2.4.1 0.6W; manufacturer span table; "
         "AWC NDS 2018 §12.2 (wood screw withdrawal)")

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


#: The panel flange the screw passes through before it reaches wood, deducted from the
#: length. 24 ga sheet — the thickest cladding steel on this house, so the deduction is the
#: conservative one, and at 0.024" it moves a capacity by about a pound. It is a constant
#: rather than a Material field because no authored number would be read more carefully
#: than this comment, and none would change an answer.
SHEET_FLANGE_IN = 0.0239


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
    # The product facts a withdrawal calculation needs, all authored on the Material and
    # none of them defaulted: a missing one is an INCOMPLETE naming it, never a guess.
    open_framing_source: str | None
    fastener: str | None
    fastener_diameter_in: float | None
    fastener_length_in: float | None
    coverage_in: float | None
    flange_in: float
    # The SUPPORT, read off the girt layer the panel is screwed into.
    support_material: str
    support_thickness_in: float
    support_specific_gravity: float | None


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
        support = catalog.get(backing.material_ref or "")
        out.append(_Panel(
            wall_tag=wall.tag, material_ref=skin.material_ref or "",
            support_spacing_in=spacing,
            allowable_psf=getattr(material, "panel_allowable_psf", None),
            allowable_span_in=getattr(material, "panel_allowable_span_in", None),
            mean_roof_height_ft=height or 0.0,
            open_framing_source=getattr(material, "open_framing_source", None),
            fastener=getattr(material, "panel_fastener", None),
            fastener_diameter_in=getattr(material, "panel_fastener_diameter_in", None),
            fastener_length_in=getattr(material, "panel_fastener_length_in", None),
            coverage_in=getattr(material, "fastener_coverage_in", None),
            flange_in=SHEET_FLANGE_IN,
            support_material=backing.material_ref or "",
            support_thickness_in=backing.thickness_m / 0.0254,
            support_specific_gravity=getattr(support, "specific_gravity", None)))
    return out


def _groups(ctx: EngineeringContext) -> dict[str, list[_Panel]]:
    """The panels collected into designs — one entry per ``(material, girt spacing)``.

    Keyed by the LOWEST member tag rather than by a synthetic name: an item id a person
    types has to be one the model already spells, and the lowest tag is deterministic under
    everything except a membership change, which is what ``panel_count`` is in the inputs
    for. Exposure is not part of the key — the demand is the corner zone on every wall, so
    two walls with the same panel and the same girts have the same design whichever way
    they face.
    """
    buckets: dict[tuple[str, float], list[_Panel]] = {}
    for panel in _panels(ctx):
        buckets.setdefault((panel.material_ref, panel.support_spacing_in), []).append(panel)
    return {min(p.wall_tag for p in members): sorted(members, key=lambda p: p.wall_tag)
            for members in buckets.values()}


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


#: The independent hand pass this module is checked against — see ``Oracle``.
oracled_by(
    KIND,
    Oracle(note="board_batten_girt_span.md", test="tests/test_wall_panel_calcs.py"),
)


@keys(KIND)
def enumerate_panels(ctx: EngineeringContext) -> list[str]:
    return sorted(_groups(ctx))


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, key, members) for key, members in sorted(_groups(ctx).items())]


def _one(ctx: EngineeringContext, key: str, members: list[_Panel]) -> EngineeringRecord:
    panel = members[0]
    tags = tuple(member.wall_tag for member in members)
    ident = item_id(KIND, key)
    basis = wind.wind_basis(ctx.plan.project.site)
    missing: list[str] = []
    if basis is None:
        missing.append("a complete design wind basis on Site "
                       "(design_wind_speed_mph, wind_exposure, risk_category)")
    if panel.mean_roof_height_ft <= 0.0:
        missing.append("a resolved roof to take the mean roof height from")
    if basis is None or panel.mean_roof_height_ft <= 0.0:
        return EngineeringRecord(
            item_id=ident, kind=KIND, key=key,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{key}: the cladding wind demand could not be computed",
            missing=tuple(missing), element_tags=tags)

    q_h = wind.velocity_pressure_psf(basis, panel.mean_roof_height_ft)
    area = effective_wind_area_ft2(panel.support_spacing_in)
    gcp = external_pressure_coefficient(area, "5")
    gcp_field = external_pressure_coefficient(area, "4")
    strength_psf = abs(q_h * (gcp - GC_PI))
    demand_psf = wind.ASD_WIND_FACTOR * strength_psf
    field_psf = wind.ASD_WIND_FACTOR * abs(q_h * (gcp_field - GC_PI))

    states: list[LimitState] = []
    _bending(panel, demand_psf, area, states, missing)
    withdrawal, trib, load = _withdrawal(panel, demand_psf, states, missing)

    inputs = [
        Quantity("design_wind_speed", basis.speed_mph, "mph", 1.0),
        Quantity("mean_roof_height", panel.mean_roof_height_ft, "ft", 0.01),
        Quantity("velocity_pressure", q_h, "psf", 0.01),
        Quantity("support_spacing", panel.support_spacing_in, "in", 0.25),
        Quantity("effective_wind_area", area, "ft2", 0.01),
        Quantity("GCp_zone5", gcp, "", 0.01),
        Quantity("GCpi", GC_PI, "", 0.01),
        Quantity("suction_asd", demand_psf, "psf", 0.01),
        Quantity("panel_count", float(len(members)), "", None),
    ]
    if panel.support_specific_gravity is not None:
        inputs.append(Quantity("specific_gravity", panel.support_specific_gravity, "", 0.01))
    if panel.fastener_diameter_in is not None:
        inputs.append(Quantity("fastener_diameter", panel.fastener_diameter_in, "in", 0.001))
    if panel.fastener_length_in is not None:
        inputs.append(Quantity("fastener_length", panel.fastener_length_in, "in", 0.01))
    if panel.coverage_in is not None:
        inputs.append(Quantity("fastener_coverage", panel.coverage_in, "in", 0.25))
    if withdrawal is not None:
        inputs.append(Quantity(
            "thread_penetration", withdrawal.thread_penetration_in, "in", 0.01))
        inputs.append(Quantity("tributary_area", trib, "ft2", 0.01))
        inputs.append(Quantity("fastener_demand", load, "lb", 0.1))

    notes = _notes(panel, demand_psf, field_psf, strength_psf, basis, withdrawal, len(members))

    # OVER wins over INCOMPLETE: a panel over an allowable is not "not yet designed", it is
    # a panel that failed a table somebody printed.
    over = any(not state.ok for state in states)
    status = Status.OVER if over else (Status.INCOMPLETE if missing else Status.OK)
    others = f", and {len(members) - 1} more wall(s) on the same design" if len(members) > 1 else ""
    return EngineeringRecord(
        item_id=ident, kind=KIND, key=key,
        basis_version=BASIS_VERSION, basis=BASIS, status=status,
        summary=(f"{key}{others} clad in {panel.material_ref} over "
                 f"{panel.support_spacing_in:g}\" open girts: {demand_psf:,.1f} psf ASD "
                 f"corner-zone suction"),
        inputs=tuple(inputs), limit_states=tuple(states), missing=tuple(missing),
        notes=tuple(notes), element_tags=tags)


def _bending(panel: _Panel, demand_psf: float, area: float,
             states: list[LimitState], missing: list[str]) -> None:
    """Panel bending, against the manufacturer's own published allowable — read, not derived."""
    if panel.open_framing_source is None:
        missing.append(
            f"Material.open_framing_source on {panel.material_ref} — the manufacturer's own "
            f"words permitting this panel over open framing. A panel nobody's literature "
            f"puts on girts is not a calculation problem, it is the wrong product")
    if panel.allowable_psf is None or panel.allowable_span_in is None:
        missing.append(
            f"Material.panel_allowable_psf and panel_allowable_span_in on "
            f"{panel.material_ref} — the manufacturer's published allowable uniform load "
            f"and the span it was read at")
        return
    if abs(panel.allowable_span_in - panel.support_spacing_in) > 0.01:
        missing.append(
            f"an allowable read at this wall's own {panel.support_spacing_in:g}\" support "
            f"spacing — {panel.material_ref} declares {panel.allowable_psf:g} psf at "
            f"{panel.allowable_span_in:g}\", and a span table is not interpolated here")
        return
    states.append(LimitState(
        "panel bending, negative (suction)", demand_psf, panel.allowable_psf, "psf",
        f"ASCE 7-16 Fig. 30.3-1 zone 5 at {area:.2f} ft2, §2.4.1 0.6W, against the "
        f"manufacturer's published allowable at {panel.allowable_span_in:g}\""))


def _withdrawal(panel: _Panel, demand_psf: float, states: list[LimitState],
                missing: list[str]):
    """Concealed-leg screw withdrawal, NDS 2018 §12.2 — computed, because nobody publishes it."""
    absent = [
        (panel.support_specific_gravity is None,
         f"Material.specific_gravity on the support {panel.support_material or '(unnamed)'} "
         f"— NDS Table 12.3.3A G, which withdrawal goes as the SQUARE of"),
        (panel.fastener_diameter_in is None,
         f"Material.panel_fastener_diameter_in on {panel.material_ref} — the shank diameter "
         f"D in W = 2850 G^2 D"),
        (panel.fastener_length_in is None,
         f"Material.panel_fastener_length_in on {panel.material_ref} — without it there is "
         f"no thread penetration and therefore no capacity"),
        (panel.coverage_in is None,
         f"Material.fastener_coverage_in on {panel.material_ref} — the panel's net coverage "
         f"is the tributary width one screw carries"),
    ]
    named = [text for is_absent, text in absent if is_absent]
    if named:
        missing.extend(named)
        return None, 0.0, 0.0
    assert panel.support_specific_gravity is not None
    assert panel.fastener_diameter_in is not None and panel.fastener_length_in is not None
    assert panel.coverage_in is not None
    withdrawal = withdrawal_allowable_lb(
        panel.support_specific_gravity, panel.fastener_diameter_in,
        panel.fastener_length_in, panel.support_thickness_in, panel.flange_in)
    trib = tributary_area_ft2(panel.support_spacing_in, panel.coverage_in)
    load = fastener_demand_lb(demand_psf, panel.support_spacing_in, panel.coverage_in)
    if withdrawal.reason is not None:
        missing.append(f"a longer panel screw: {withdrawal.reason}")
        return withdrawal, trib, load
    states.append(LimitState(
        "concealed-leg screw withdrawal", load, withdrawal.capacity_lb, "lb",
        f"AWC NDS 2018 §12.2, W = 2850 G^2 D at G {panel.support_specific_gravity:g}, "
        f"C_D 1.6 (Table 2.3.2 wind), C_M 0.7 (Table 11.3.3 wet service), "
        f"{withdrawal.thread_penetration_in:.2f}\" thread penetration"))
    return withdrawal, trib, load


def _notes(panel: _Panel, demand_psf: float, field_psf: float, strength_psf: float,
           basis, withdrawal, count: int) -> list[str]:
    notes = [
        f"Zone 5 (corner) governs the ORDER: one product runs through both zones. Zone 4 "
        f"(field) is {field_psf:.1f} psf ASD against zone 5's {demand_psf:.1f}.",
        f"Strength-level suction is {strength_psf:.1f} psf; {demand_psf:.1f} psf is that at "
        f"0.6W (ASCE 7-16 §2.4.1), the basis every allowable cited here is published on.",
        f"Wind basis: {basis.describe()}, K_zt {wind.K_ZT_FLAT:g}, K_d "
        f"{wind.K_D_BUILDINGS:g}, K_e taken as 1.0 (ASCE 7-16 §26.9).",
        f"One seal covers {count} wall(s): the same panel, the same girt spacing and the "
        f"same corner-zone demand are one design. Membership is in the fingerprint as "
        f"`panel_count`, so adding or removing a wall stales the stamp.",
    ]
    if panel.open_framing_source:
        notes.append(f"Open framing is on-label: {panel.open_framing_source}")
    if withdrawal is not None and withdrawal.reason is None:
        notes.append(
            "Withdrawal is COMPUTED, not read. The manufacturer's own load table states it "
            "\"does not address web crippling, fasteners, support material or load "
            "testing\" — bending only — and no maker publishes a pull-out value for a "
            "concealed leg into wood. IAPMO UES ER-309 expressly permits a design "
            "professional to extend published data by engineering mechanics, and NDS "
            "§12.2 is that mechanics. Cross-check: ER-309's own DFL row, 208 lb at 1\" "
            "penetration, is 2850 x 0.50^2 x 0.19 x 1.6 to within a pound.")
        notes.append(_alternates(panel, withdrawal))
        notes.append(
            "Graded as an NDS WOOD screw, so the screw ordered must be a wood-point "
            "(Type 17) fastener and not a self-drilling point — a drill point in a "
            "1-1/2\" girt reams its own thread away. A published pull-out value for this "
            "screw into wood would supersede this calculation.")
    notes.append(
        "NOT CHECKED, and no seal should read this as covering them: the girt itself in "
        "bending and its block-to-stud connection, panel deflection, thermal movement of a "
        "continuous run, and the manufacturer table's 3-equal-span basis at the short walls.")
    return notes


def _alternates(panel: _Panel, withdrawal) -> str:
    """The shorter screws the same panel ships with, priced in d/c — why 2" is specified."""
    assert panel.fastener_diameter_in is not None and panel.coverage_in is not None
    assert panel.support_specific_gravity is not None
    parts = []
    for length in (1.0, 1.5, panel.fastener_length_in or 0.0):
        if length <= 0.0:
            continue
        alt = withdrawal_allowable_lb(
            panel.support_specific_gravity, panel.fastener_diameter_in, length,
            panel.support_thickness_in, panel.flange_in)
        parts.append(f"{length:g}\" -> {alt.thread_penetration_in:.3f}\" pen, "
                     f"{alt.capacity_lb:.0f} lb")
    return ("Screw length is the whole capacity here, so the alternates are printed: "
            + "; ".join(parts) + ". The guide's own 1\" pancake screw is what a panel order "
            "ships with and it does not meet the manufacturer's \"1/2\" or more past the "
            "inside face of the support\" rule; the 2\" does, with the tip outside the girt.")
