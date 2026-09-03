"""A belled pier's bearing on the ground — ``spread_footing/<Post tag>``.

The item ``structural.deck_footing_size`` hands off when a deck post bears on a ``Footing``
rather than a ``Pad``. That is not the check failing to reach: it is the honest statement
that IRC Table R507.3.1 publishes flat-pad rows and these are augered shafts with belled
bases, which the table has no row for and never will.

What it does instead is the question R507.3.1 actually asks — is the pressure under the bell
inside the presumptive allowable — answered in numbers a reviewer can disagree with.

**Oracle.** ``houses/catlin/notes/sunken_garden_piers.md``, hand-worked in a separate pass;
``tests/test_pier_calcs.py`` reproduces it.

**Screening, not a design.** Presumptive code-table values only, no geotechnical report; no
settlement, no group effect, no uplift and no lateral case. See ``retaining_basis`` for the
same disclaimer at more length — it is the same site and the same missing boring.
"""

from __future__ import annotations

import math

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.pier_basis import (
    DECK_DEAD_LOAD_PSF,
    DECK_LIVE_LOAD_PSF,
    _Pier,
    cast_piers,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys
from typehaus.engineering.retaining_basis import PRESUMPTIVE_FC_PSI
from typehaus.engineering.soil import CONCRETE_UNIT_WEIGHT_PCF, presumptive

KIND = "spread_footing"

#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
#: "2" added the three SECTION states below to what had been a bearing-only record.
BASIS_VERSION = "2"
BASIS = ("IRC R507.3.1; IBC Table 1806.2 presumptive values; "
         "ACI 318-19 §14.5 plain concrete (flexure, one-way and two-way shear)")

#: ACI 318-19 Table 21.2.1 — plain concrete, every limit state.
PHI_PLAIN = 0.60

#: ACI 318-19 §14.5.1.7. **The one provision in this module a reader is most likely to miss.**
#: For a plain-concrete footing cast against soil, every strength computation takes the
#: overall thickness LESS 2 inches — the Code's allowance for an unformed bottom face poured
#: against dirt. On a 12" bell that is a sixth of the section given away before any number is
#: computed, and skipping it overstates flexural capacity by 44% (it goes as h squared).
PLAIN_SOIL_CAST_DEDUCTION_IN = 2.0


def _piers_on_their_own_footing(ctx: EngineeringContext) -> list[_Pier]:
    """The subset ``cast_piers`` yields that this module governs — one with a ``Footing``.

    ``cast_piers`` also yields a pier on a ``Pad``, and a ``Pad`` **is** an IRC Table
    R507.3.1 row: ``structural.deck_footing_size`` sizes it against the same tributary and
    the same presumptive soil, prescriptively. Minting an engineered bearing record beside
    that one would put two authorities on one number and gain nothing — the table publishes
    the flat-pad case, which is exactly what a pad is. What has no row is the augered BELL,
    and a bell arrives as a ``Footing``.

    ``shared_wall_footing`` is excluded for the identical reason at the other end of the
    scale. Since 2026-09-03 ``cast_piers`` also yields a column standing on a concrete
    foundation WALL, carried by that wall's continuous strip footing — catlin's four balcony
    corner columns on W-SG-W1/E1. That footing already has an authority:
    ``structural.foundation_unbalanced_fill`` grades it as ``retaining_wall/<tag>``, on the
    wall's own bearing, sliding and overturning. Computing a point pressure on the same
    concrete from this side would be a second answer to one question, and the weaker of the
    two — a strip footing under a wall does not bear like an isolated pad under a post.
    """
    return [pier for pier in cast_piers(ctx)
            if pier.footing_tag and not pier.shared_wall_footing]


@keys(KIND)
def enumerate_piers(ctx: EngineeringContext) -> list[str]:
    return [pier.tag for pier in _piers_on_their_own_footing(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, pier) for pier in _piers_on_their_own_footing(ctx)]


def _one(ctx: EngineeringContext, pier: _Pier) -> EngineeringRecord:
    tags = tuple(t for t in (pier.tag, pier.footing_tag) if t)
    soil = presumptive(getattr(ctx, "soil_class", None))
    if soil is None:
        return EngineeringRecord(
            item_id=item_id(KIND, pier.tag), kind=KIND, key=pier.tag,
            basis_version=BASIS_VERSION, basis=BASIS, status=Status.INCOMPLETE,
            summary=f"{pier.tag}: the bearing check could not run",
            missing=("a declared soil class (Site/profile soil_class)",),
            element_tags=tags)

    # **The bell bears on the SITE's own soil, not on a replacement section, and that is the
    # one judgement in this module.** The retaining footings sit on 42" of washed stone and
    # `retaining_basis._base_interface` reads IBC class 3 off it for exactly that reason.
    # These two do not: `params/sunken_garden.py` augered both bells to frost depth
    # precisely so they would bear on undisturbed soil, and what they carry is a
    # 7" LEVELLING course (`SPEC.pier_levelling_bedding_in`), not a soil replacement. A
    # 7" course spreads load into the native soil within inches of the bell, so crediting
    # the stone's 3,000 psf here would be reading a 42" section's allowable off a bedding
    # that is a sixth of it. The site's class governs, which is the conservative direction.
    bearing = (pier.service_lb + pier.footing_weight_lb) / pier.bearing_area_ft2
    section, section_notes = _section_states(ctx, pier)
    states = (
        LimitState("bearing", bearing, soil.allowable_bearing_psf, "psf",
                   f"IBC Table 1806.2 class {soil.ibc_class} ({soil.soil_class}), "
                   f"presumptive"),
    ) + section
    over = any(not state.ok for state in states)
    inputs = (
        Quantity("tributary_area", pier.tributary_ft2, "ft2", 0.01),
        Quantity("bell_width", pier.footing_width_in, "in", 0.5),
        Quantity("bell_depth", pier.footing_depth_in, "in", 0.5),
        Quantity("bearing_area", pier.bearing_area_ft2, "ft2", 0.001),
        Quantity("column_diameter", pier.diameter_in, "in", 0.5),
        Quantity("column_height", pier.height_in, "in", 0.01),
        Quantity("carried_dead", pier.carried_dead_lb, "lb", 1.0),
        Quantity("dead_load", pier.dead_lb, "lb", 1.0),
        Quantity("live_load", pier.live_lb, "lb", 1.0),
        Quantity("allowable_bearing", soil.allowable_bearing_psf, "psf", 1.0),
        Quantity("concrete_unit_weight", CONCRETE_UNIT_WEIGHT_PCF, "pcf", 1.0),
    )
    notes = (
        f"SCREENING on presumptive code values, not a design: {soil.citation}. No "
        f"geotechnical report is on file for this site.",
        f"Service load {pier.service_lb:,.0f} lb + {pier.footing_weight_lb:,.0f} lb of bell "
        f"over {pier.bearing_area_ft2:.2f} ft2. Tributary {pier.tributary_ft2:.1f} ft2 at "
        f"{DECK_DEAD_LOAD_PSF:.0f} psf dead + {DECK_LIVE_LOAD_PSF:.0f} psf live (IRC "
        f"Table R301.5), plus the column's own {pier.self_weight_lb:,.0f} lb.",
        "THE BELL IS READ AS A CIRCLE. `resolve/envelope.py` draws a post-hosted footing as "
        "a SQUARE of side `width`, and `params/sunken_garden.py` calls that number a bell "
        "DIAMETER — taking the square would credit 27% more bearing area than exists.",
        "Bearing is taken on the SITE's own class, not on the washed-stone value the "
        "retaining footings earn: these bells were augered to frost depth to bear on "
        "undisturbed soil, and their 7\" levelling course is not a soil replacement.",
        "Not checked: settlement, group effect, uplift, lateral load on the shaft.",
        "AND THERE IS NO DEPTH OR WIDTH BONUS TO CLAIM. IBC 1806.3.3's 'increase for depth' "
        "raises LATERAL bearing only, and 1806.3 is scoped to resistance to lateral loads; "
        "2018 IBC has no provision raising presumptive VERTICAL pressure for a deeper or "
        "wider footing. (The +20%/ft, 3x cap some references remember is 1997 UBC Table "
        "18-I-A and did not carry into the IBC.) The only sanctioned escalators are 1806.1's "
        "one-third with the alternative wind/seismic combinations, and 1806.2's 'data to "
        "substantiate the use of higher values' — which means a boring, not a table.",
    )
    notes = notes + section_notes
    if pier.carried_dead_lb or pier.tributary_ft2 <= 0.0:
        notes = notes + (
            f"This pier carries a post standing ON it as well as its own deck share — the "
            f"{pier.tributary_ft2:.1f} ft2 above includes what that post hands down, which "
            f"is the share `structural.deck_footing_size`'s N/A on it promised would be "
            f"picked up here.",
        )

    return EngineeringRecord(
        item_id=item_id(KIND, pier.tag), kind=KIND, key=pier.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over else Status.OK,
        summary=(f"{pier.tag} on a {pier.footing_width_in:.0f}\" belled pier: "
                 f"{bearing:,.0f} psf against the {soil.allowable_bearing_psf:,.0f} psf "
                 f"IBC Table 1806.2 presumes for {soil.soil_class}"),
        inputs=inputs, limit_states=states, notes=notes, element_tags=tags)


def _section_states(ctx: EngineeringContext,
                    pier: _Pier) -> tuple[tuple[LimitState, ...], tuple[str, ...]]:
    """Flexure, one-way shear and two-way (punching) shear on the bell itself.

    **The bell had bearing graded and its own strength ungraded**, which is half a footing
    check: soil pressure is a demand on the concrete as much as on the ground, and a bell
    thin enough to punch through fails at a pressure the ground would have carried.

    **Graded as PLAIN concrete, and that is legal here.** ACI 318-19 §14.1.4 permits plain
    concrete in a footing — unlike §14.1.5, which does not permit a plain concrete *column*
    at any stress. So a bell with no reinforcement authored is not INCOMPLETE the way a bare
    sonotube column is; it is a plain section, and the question is whether the plain section
    is enough. Where a house DOES author steel, the plain capacity below is still what is
    reported: steel only adds, so plain is the conservative bound, and the record says in as
    many words that the authored bars are not being credited rather than quietly crediting
    them with a formula nobody has oracled.

    Three Code decisions worth stating rather than burying:

    * **The circular column becomes an equivalent square** (§13.2.7.3), side
      ``sqrt(pi d^2 / 4)`` — 10.64" for a 12" round. Every critical section below is measured
      from that square's face, which is what the Code's critical-section geometry assumes.
    * **h is the overall thickness less 2"** (§14.5.1.7), because the bottom of an augered
      bell is poured against dirt. See :data:`PLAIN_SOIL_CAST_DEDUCTION_IN`.
    * **The pressure is the FACTORED column load over the bell area, and the bell's own
      weight is excluded.** A footing does not punch itself: its self-weight is carried
      straight down into the soil directly beneath it and generates no shear across the
      critical perimeter and no moment about the column face. Including it — the natural
      thing to do, having just included it in the bearing check one screen above — would
      overstate every demand here by about a tenth.
    """
    from typehaus.model.structure import Footing
    from typehaus.resolve.concrete import concrete_spec_for
    from typehaus.resolve.concrete import fc_psi as _spec_fc

    thickness_in = pier.footing_depth_in - PLAIN_SOIL_CAST_DEDUCTION_IN
    diameter_in = pier.footing_width_in
    if thickness_in <= 0.0 or diameter_in <= 0.0 or not pier.round_section:
        # A square pad under a square post is a different critical-section geometry, and
        # this module has never had one to grade. Reporting nothing is right; inventing a
        # circular derivation for a rectangle is not.
        return (), ()

    footing = next((f for f in ctx.plan.all_elements()
                    if isinstance(f, Footing) and f.tag == pier.footing_tag), None)
    spec_fc = _spec_fc(concrete_spec_for(ctx.plan, footing)) if footing is not None else None
    fc = spec_fc or PRESUMPTIVE_FC_PSI
    root_fc = math.sqrt(fc)

    radius_in = diameter_in / 2.0
    # §13.2.7.3 — a circular column is graded as a square of equal area.
    equivalent_side_in = math.sqrt(math.pi * pier.diameter_in ** 2 / 4.0)
    half_side_in = equivalent_side_in / 2.0
    bell_area_in2 = math.pi * radius_in ** 2
    pressure_psi = pier.factored_lb / bell_area_in2

    # --- two-way (punching): critical perimeter at h/2 from the column face, §14.5.5.2(b).
    punch_radius_in = half_side_in + thickness_in / 2.0
    perimeter_in = 8.0 * punch_radius_in           # the square's perimeter, 4 x 2r
    inside_in2 = (2.0 * punch_radius_in) ** 2
    punch_demand = pressure_psi * max(bell_area_in2 - inside_in2, 0.0)
    # §14.5.5.1(b): Vn = (4/3 + 8/(3 beta)) lambda sqrt(f'c) bo h, capped at 2.66. beta is
    # the column's long/short ratio, which for a square equivalent is 1.0, so the bracket is
    # 4.0 and the CAP always governs here. Carried as the min anyway: the cap is the Code's
    # sentence, not this section's arithmetic, and a future rectangular column needs it.
    punch_capacity = PHI_PLAIN * min(4.0 / 3.0 + 8.0 / 3.0, 2.66) \
        * root_fc * perimeter_in * thickness_in

    # --- one-way: critical section at h from the column face, §14.5.5.2(a).
    oneway_offset_in = half_side_in + thickness_in
    if oneway_offset_in >= radius_in:
        # The critical section falls outside the footing: there is no section to check,
        # which is a real answer and not a missing one. Reported as a zero demand so the
        # state still appears — a limit state silently absent reads as one nobody thought of.
        oneway_demand, oneway_capacity, width_in = 0.0, 1.0, 0.0
    else:
        half_chord_in = math.sqrt(radius_in ** 2 - oneway_offset_in ** 2)
        width_in = 2.0 * half_chord_in
        oneway_demand = pressure_psi * _segment_area_in2(radius_in, oneway_offset_in)
        oneway_capacity = PHI_PLAIN * (4.0 / 3.0) * root_fc * width_in * thickness_in

    # --- flexure: critical section at the column face, §13.2.7.1, capacity §14.5.2.1(a)
    #     Mn = 5 lambda sqrt(f'c) Sm on the GROSS section, Sm = b h^2 / 6.
    flex_area_in2 = _segment_area_in2(radius_in, half_side_in)
    flex_arm_in = _segment_centroid_in(radius_in, half_side_in) - half_side_in
    flex_demand = pressure_psi * flex_area_in2 * flex_arm_in
    flex_width_in = 2.0 * math.sqrt(max(radius_in ** 2 - half_side_in ** 2, 0.0))
    flex_capacity = PHI_PLAIN * 5.0 * root_fc * flex_width_in * thickness_in ** 2 / 6.0

    fc_note = (f"f'c {fc:,.0f} psi (the mix the assembly specifies)" if spec_fc
               else f"f'c {fc:,.0f} psi PRESUMPTIVE (this pour specifies no mix)")
    states = (
        LimitState("two-way (punching) shear", punch_demand, punch_capacity, "lb",
                   f"ACI 318-19 §14.5.5.1(b) plain concrete, phi {PHI_PLAIN:.2f} "
                   f"(Table 21.2.1) — bo {perimeter_in:.1f}\" at h/2 from an "
                   f"{equivalent_side_in:.2f}\" equivalent square (§13.2.7.3), "
                   f"h {thickness_in:.1f}\" after §14.5.1.7's 2\" deduction, {fc_note}"),
        LimitState("one-way shear", oneway_demand, oneway_capacity, "lb",
                   (f"ACI 318-19 §14.5.5.1(a), critical section at h from the column face "
                    f"— which at {oneway_offset_in:.2f}\" falls OUTSIDE a "
                    f"{diameter_in:.0f}\" bell, so there is no section to check"
                    if width_in <= 0.0 else
                    f"ACI 318-19 §14.5.5.1(a) plain concrete, phi {PHI_PLAIN:.2f} — a "
                    f"{width_in:.2f}\" chord at h from the column face, h "
                    f"{thickness_in:.1f}\", {fc_note}")),
        LimitState("flexure at the column face", flex_demand, flex_capacity, "lb-in",
                   f"ACI 318-19 §14.5.2.1(a) Mn = 5 lambda sqrt(f'c) Sm on the gross "
                   f"section, phi {PHI_PLAIN:.2f} — Sm on a {flex_width_in:.2f}\" chord "
                   f"x h {thickness_in:.1f}\", cantilevering "
                   f"{radius_in - half_side_in:.2f}\" past the equivalent square, {fc_note}"),
    )
    notes = (
        "SECTION STRENGTH IS GRADED AS PLAIN CONCRETE, and ACI 318-19 §14.1.4 permits that "
        "in a footing — §14.1.5's ban on a plain concrete COLUMN is a different sentence "
        "about a different member. This bell authors no reinforcement, so plain is what it "
        "is; where one did, the plain capacity would still be reported, because steel only "
        "adds and this module has no oracled reinforced derivation to credit it with.",
        f"h IS {thickness_in:.1f}\", NOT {pier.footing_depth_in:.1f}\". ACI 318-19 §14.5.1.7 "
        f"takes 2\" off a plain footing cast against soil, and flexural capacity goes as h "
        f"squared — skipping it would overstate this section by 44%.",
        f"The bell's own {pier.footing_weight_lb:,.0f} lb is EXCLUDED from all three states "
        f"above and included in the bearing state below it. A footing does not punch itself: "
        f"its weight goes straight down into the soil under it and crosses no critical "
        f"perimeter. Net factored pressure {pressure_psi * 144.0:,.0f} psf.",
    )
    return states, notes


def _segment_area_in2(radius_in: float, offset_in: float) -> float:
    """Area of the circular segment beyond ``offset_in`` from the centre of a circle."""
    if offset_in >= radius_in:
        return 0.0
    root = math.sqrt(radius_in ** 2 - offset_in ** 2)
    return radius_in ** 2 * math.acos(offset_in / radius_in) - offset_in * root


def _segment_centroid_in(radius_in: float, offset_in: float) -> float:
    """Distance from the circle's CENTRE to that segment's centroid.

    ``(2/3) (R^2 - x^2)^(3/2) / A``. Returned about the centre rather than about the cut so
    the caller subtracts its own offset and the two conventions cannot be confused — which
    is the mistake that puts a footing's moment arm out by the column's half-width.
    """
    area = _segment_area_in2(radius_in, offset_in)
    if area <= 0.0:
        return offset_in
    return (2.0 / 3.0) * (radius_in ** 2 - offset_in ** 2) ** 1.5 / area
