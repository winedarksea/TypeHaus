"""A steel HSS post pinned at both ends under a roof header — ``steel_post/<post tag>``.

The canopy's east posts (``EAST_POST_SYSTEM = "steel"``) are hollow structural sections,
welded to a saddle at the head and a base plate at the foot, galvanized after fabrication
and powder-coated. Pinned at both ends, they carry gravity and their own drag and nothing
else — the roof's lateral load is the neighbour's (``diaphragm_delivery``).

Graded, each against its own standard:

* **AISC 360-16 §E7** — the wall's width-to-thickness against Table B4.1a (case 6 for a
  rectangular tube, case 9 for a round), so §E3 applies unreduced;
* **§E2** — KL/r against the user-note limit of 200, K = 1.0 pinned-pinned;
* **§E3** — flexural buckling, ``P_n / Ω_c`` at Ω_c 1.67, against D + S on the roof share;
* **§H1.1** — the post's own drag as a simple-span moment beside that axial, a bound;
* **the saddle** — two through-bolts in the header, AWC NDS 2018 §12.3.1's yield-limit
  equations in double shear with steel side plates, against the net 0.6D + 0.6W uplift;
* **the base** — its cast-in anchors in the pier, ACI 318-19 Ch. 17 through
  ``holdown_anchor`` (the §8f single centred bolt, which bounds the pair from below).

**The published section is read, not derived.** A500's tabulated properties include the
corner radii, which a sharp-corner tube overstates by ~7% in I (``analytical/pynite_map``
computes the stiffness; this grades the strength). A section not in :data:`PUBLISHED`
is INCOMPLETE naming itself — never a computed guess.

**The grade is ASTM A500 Gr C and it is an assumption the record prints**: F_y 50 ksi for a
rectangular tube, 46 ksi round. Nothing in the model names a steel grade.

**Oracle.** ``houses/catlin/notes/canopy_garage_diaphragm.md`` §5;
``tests/test_steel_post_calcs.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by

KIND = "steel_post"
BASIS = ("AISC 360-16 §B4.1, §E2, §E3, §E7, §H1.1 (ASD, Ω_c 1.67, Ω_b 1.67); AWC NDS 2018 "
         "§12.3.1 (bolts, steel side plates); ACI 318-19 Ch. 17 (the cast-in base anchors)")
#: 1: the kind as introduced, 2026-09-29.
BASIS_VERSION = "1"

oracled_by(KIND, Oracle(note="canopy_garage_diaphragm.md", section="§5",
                        test="tests/test_steel_post_calcs.py"))

E_KSI = 29_000.0
OMEGA_C = 1.67
OMEGA_B = 1.67
SLENDERNESS_LIMIT = 200.0
#: ASTM A500 Gr C: 50 ksi for a shaped (rectangular) tube, 46 for a round one.
FY_KSI = {"hss": 50.0, "hss_round": 46.0}


@dataclass(frozen=True)
class Section:
    """AISC Manual Table 1-12 / 1-13 properties: A in2, I in4, r in, Z in3, b/t (or D/t)."""

    area_in2: float
    inertia_in4: float
    radius_in: float
    plastic_in3: float
    slender_ratio: float
    weight_plf: float


#: The sections this engine may grade, read from the AISC Manual (15th ed.) Tables 1-12
#: and 1-13. Keyed on the profile spelling ``cross_section`` reads.
PUBLISHED = {
    "HSS4x4x0.25": Section(3.37, 7.80, 1.52, 4.69, 14.2, 12.21),
}

#: The saddle's through-bolts and side plates, the note's §5 parts.
SADDLE_BOLTS = 2
SADDLE_BOLT_IN = 0.625
SADDLE_PLATE_IN = 0.25
#: NDS Table 12.3.3 notes: F_es of an A36 side plate, 1.5 F_u; F_yb of a SAE J429 Gr 2 bolt.
FES_STEEL_PSI = 87_000.0
FYB_PSI = 45_000.0
#: The header's specific gravity (southern pine) and its C_D / C_M at an exposed eave.
HEADER_G = 0.55
C_D_WIND = 1.6
C_M_WET = 0.7


def _pinned_posts(ctx: EngineeringContext) -> list:  # type: ignore[type-arg]
    from typehaus.engineering.roof_lateral import roof_winds
    from typehaus.resolve.framing.profiles import cross_section

    out = []
    for wind in roof_winds(ctx).values():
        for post in wind.pinned:
            element = ctx.plan.by_tag(post.tag)
            if cross_section(getattr(element, "size", "") or "").shape in FY_KSI:
                out.append((post, wind))
    return sorted(out, key=lambda row: row[0].tag)


@keys(KIND)
def enumerate_steel_posts(ctx: EngineeringContext) -> list[str]:
    return [post.tag for post, _ in _pinned_posts(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, post, wind) for post, wind in _pinned_posts(ctx)]


def flexural_buckling_ksi(fy_ksi: float, klr: float) -> tuple[float, float]:
    """``(F_e, F_cr)`` ksi, AISC 360-16 Eq. E3-4 and E3-2/E3-3."""
    fe = math.pi ** 2 * E_KSI / klr ** 2
    fcr = (0.658 ** (fy_ksi / fe)) * fy_ksi if fy_ksi / fe <= 2.25 else 0.877 * fe
    return fe, fcr


def slender_limit(shape: str, fy_ksi: float) -> float:
    """Table B4.1a: case 6 (rectangular HSS walls) 1.40 sqrt(E/F_y); case 9 (round) 0.11 E/F_y."""
    return 0.11 * E_KSI / fy_ksi if shape == "hss_round" else 1.40 * math.sqrt(E_KSI / fy_ksi)


def bolt_double_shear_lb(diameter_in: float, main_in: float, side_in: float, g: float,
                         perpendicular: bool) -> tuple[float, dict[str, float]]:
    """NDS 2018 §12.3.1, double shear, steel side plates: the least yield mode, lb."""
    fem = (6100.0 * g ** 1.45 / math.sqrt(diameter_in) if perpendicular
           else 11200.0 * g)
    k_theta = 1.25 if perpendicular else 1.0
    re = fem / FES_STEEL_PSI
    k3 = -1.0 + math.sqrt(2.0 * (1.0 + re) / re
                          + 2.0 * FYB_PSI * (2.0 + re) * diameter_in ** 2
                          / (3.0 * fem * side_in ** 2))
    modes = {
        "I_m": diameter_in * main_in * fem / (4.0 * k_theta),
        "I_s": 2.0 * diameter_in * side_in * FES_STEEL_PSI / (4.0 * k_theta),
        "III_s": 2.0 * k3 * diameter_in * side_in * fem / ((2.0 + re) * 3.2 * k_theta),
        "IV": (2.0 * diameter_in ** 2 / (3.2 * k_theta)
               * math.sqrt(2.0 * fem * FYB_PSI / (3.0 * (1.0 + re)))),
    }
    return min(modes.values()), modes


def _one(ctx: EngineeringContext, post, wind) -> EngineeringRecord:  # type: ignore[no-untyped-def]
    from typehaus.engineering.holdown_anchor import round_pier_anchor
    from typehaus.engineering.holdown_anchor import states as anchor_states
    from typehaus.engineering.pier_basis import (
        DECK_DEAD_LOAD_PSF,
        _round_size,
        design_roof_snow_psf,
        roof_tributaries,
    )
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi
    from typehaus.resolve.framing.profiles import cross_section

    ident = item_id(KIND, post.tag)
    element = ctx.plan.by_tag(post.tag)
    size = element.size
    shape = cross_section(size).shape
    section = PUBLISHED.get(size)
    header = next(iter(_headers(ctx, post.tag)), None)
    tags = tuple(t for t in (post.tag, header, post.below) if t)
    roof_trib, _ = roof_tributaries(ctx)
    trib = roof_trib.get(post.tag, 0.0)
    missing = [text for ok, text in (
        (section is not None, f"AISC Manual properties for `{size}` in steel_post.PUBLISHED"),
        (trib > 0.0, "a roof tributary on this post (`pier_basis.roof_tributaries`)"),
    ) if not ok]
    if missing:
        return EngineeringRecord(item_id=ident, kind=KIND, key=post.tag,
                                 basis_version=BASIS_VERSION, basis=BASIS,
                                 status=Status.INCOMPLETE,
                                 summary=f"{post.tag}: the steel post could not be graded",
                                 missing=tuple(missing), element_tags=tags)
    assert section is not None
    fy = FY_KSI[shape]
    length_in = post.length_ft * 12.0
    klr = length_in / section.radius_in
    fe, fcr = flexural_buckling_ksi(fy, klr)
    allowable_kip = fcr * section.area_in2 / OMEGA_C
    snow, snow_basis = design_roof_snow_psf(ctx)
    axial_lb = trib * (DECK_DEAD_LOAD_PSF + snow) + section.weight_plf * post.length_ft
    drag_plf = wind.pressure_psf * post.width_ft
    moment_lb_ft = drag_plf * post.length_ft ** 2 / 8.0
    mc_kip_ft = fy * section.plastic_in3 / OMEGA_B / 12.0
    p_ratio = axial_lb / 1000.0 / allowable_kip
    m_ratio = moment_lb_ft / 1000.0 / mc_kip_ft
    interaction = p_ratio / 2.0 + m_ratio if p_ratio < 0.2 else p_ratio + 8.0 / 9.0 * m_ratio
    uplift = trib * (wind.pressure_psf - 0.6 * DECK_DEAD_LOAD_PSF)
    z, modes = bolt_double_shear_lb(SADDLE_BOLT_IN, _header_width_in(ctx, header),
                                    SADDLE_PLATE_IN, HEADER_G, perpendicular=True)
    z_adj = z * C_D_WIND * C_M_WET
    limit = slender_limit(shape, fy)

    states = [
        LimitState("wall slenderness, §E7", section.slender_ratio, limit, "",
                   f"AISC 360-16 Table B4.1a case {'9 D/t' if shape == 'hss_round' else '6 b/t'}"
                   f", {section.slender_ratio:.1f} against λ_r {limit:.2f} at F_y {fy:.0f} ksi"
                   " — nonslender, so §E3 applies with Q = 1.0",
                   is_detailing=True),
        LimitState("slenderness KL/r, §E2", klr, SLENDERNESS_LIMIT, "",
                   f"K 1.0 (pinned-pinned) x {length_in:.2f}\" / r {section.radius_in:.2f}\""),
        LimitState("axial, flexural buckling §E3", axial_lb, allowable_kip * 1000.0, "lb",
                   f"F_e {fe:.2f} ksi, F_cr {fcr:.3f} ksi, P_n {fcr * section.area_in2:.2f} "
                   f"kip / Ω_c {OMEGA_C}; D + S: {trib:.1f} ft2 x ({DECK_DEAD_LOAD_PSF:g} + "
                   f"{snow:.1f}) psf plus the post's {section.weight_plf:.2f} plf"),
        LimitState("combined axial and drag, §H1.1", interaction, 1.0, "",
                   f"H1-1{'b' if p_ratio < 0.2 else 'a'}: {p_ratio:.4f} axial with the post's "
                   f"own drag {drag_plf:.2f} plf as a simple span, M {moment_lb_ft:.2f} lb-ft "
                   f"against M_c {mc_kip_ft:.3f} kip-ft — D + S taken with the full 0.6W, a "
                   f"bound"),
        LimitState("saddle bolts, uplift", uplift, SADDLE_BOLTS * z_adj, "lb",
                   f"NDS 2018 §12.3.1 double shear, {SADDLE_BOLT_IN}\" bolts, "
                   f"{SADDLE_PLATE_IN}\" steel side plates, load perpendicular to "
                   f"{header or 'the header'}'s grain (G {HEADER_G}): modes "
                   + ", ".join(f"{k} {v:,.0f}" for k, v in modes.items())
                   + f" lb; Z {z:,.0f} x C_D {C_D_WIND} x C_M {C_M_WET} = {z_adj:,.0f} lb "
                   f"per bolt. Demand 0.6D + 0.6W on {trib:.1f} ft2"),
    ]
    notes = [
        f"THE GRADE IS AN ASSUMPTION: ASTM A500 Gr C, F_y {fy:.0f} ksi. The published section "
        f"({size}: A {section.area_in2}, I {section.inertia_in4}, r {section.radius_in}, "
        f"Z {section.plastic_in3}) is AISC Manual Table 1-12's.",
        f"SNOW: {snow_basis}.",
        "STAINLESS AND GALVANIZED ARE NEVER MIXED at the head: HDG bolts through an HDG "
        "saddle, with a butyl isolation layer against the treated header.",
    ]
    inputs = [Quantity("axial_lb", axial_lb, "lb", 1.0),
              Quantity("uplift_lb", uplift, "lb", 1.0),
              Quantity("length_in", length_in, "in", 0.01),
              Quantity("roof_tributary_ft2", trib, "ft2", 0.01)]

    pier = ctx.plan.by_tag(post.below or "")
    pier_size = _round_size(getattr(pier, "size", "") or "") if pier is not None else None
    if pier_size is not None:
        anchor = round_pier_anchor(f"{post.tag} base", pier_size[0],
                                   fc_psi(concrete_spec_for(ctx.plan, pier)) or 3000.0)
        states += anchor_states(
            anchor, max(uplift, 0.0), post.base_lb,
            f"the post's net roof uplift {uplift:,.1f} lb (0.6D + 0.6W)",
            f"the post's base drag reaction {post.base_lb:,.2f} lb")
        notes.append(
            f"THE BASE PLATE'S ANCHORS ARE GRADED AS ONE CENTRED BOLT IN {post.below}: the "
            f"pair's breakout cone is the same pier-bounded area, and one bolt's pullout and "
            f"steel are half the pair's, so this is the lower bound. The plate sits on "
            f"levelling nuts over an OPEN, DRAINED gap — never grouted — and the anchors see "
            f"bending under the {post.base_lb:,.1f} lb of shear, which is named, not graded.")
    else:
        notes.append(f"NO PIER under {post.tag} resolves as a round cast pier, so its base "
                     f"anchors are not graded here.")

    over = any(not s.ok for s in states)
    worst = max(states, key=lambda s: s.demand / s.capacity if s.capacity else 0.0)
    return EngineeringRecord(
        item_id=ident, kind=KIND, key=post.tag, basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if over else Status.OK,
        summary=(f"{post.tag}: {size} pinned-pinned, {length_in:.2f}\" — {worst.name} governs "
                 f"at {worst.demand / worst.capacity:.2f}"),
        inputs=tuple(inputs), limit_states=tuple(states), notes=tuple(notes),
        element_tags=tags)


def _headers(ctx: EngineeringContext, post_tag: str) -> list[str]:
    from typehaus.model.structure import Beam

    return sorted(e.tag for e in ctx.plan.all_elements()
                  if isinstance(e, Beam) and post_tag in (e.bearing_refs or ()))


def _header_width_in(ctx: EngineeringContext, header: str | None) -> float:
    from typehaus.resolve.framing.profiles import cross_section

    element = ctx.plan.by_tag(header or "")
    size = getattr(element, "size", None)
    return (cross_section(size).width_m / 0.0254) if size else 3.5
