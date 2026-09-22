"""Corrected gravity-beam screening for W-SG-BRKBM.

Actual 5,000 psi concrete, strength-design load factors, ACI's effective-span rule and both
minimum-steel equations. Oracled against ``houses/catlin/notes/sunken_garden_veneer_beam.md``
§3 and §4, whose arithmetic is worked by hand at the same inputs.

**The load factor is 1.4, not 1.2** — see :data:`DEAD_LOAD_FACTOR`. This module carried 1.2
from the day it was written until 2026-09-14, which understated every demand by 17% on a
member whose load is dead weight and nothing else.

**Torsion is computed, not dismissed.** :func:`check_veneer_beam` returns the threshold and
cracking torsions beside the demand, because the note's original "compatibility torsion may
be neglected" is only half true here: the demand is comfortably below cracking and
comfortably ABOVE the threshold, and those two facts have different consequences.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

#: ACI 318-19 Table 5.3.1, Eq. (5.3.1a): ``U = 1.4D``. For a member whose load is dead
#: weight and nothing else — a brick wythe and the beam's own concrete — (5.3.1a) governs
#: and (5.3.1b) ``1.2D + 1.6L`` does not, because L is zero.
#:
#: ** THIS WAS 1.2 UNTIL 2026-09-14. ** The outside review said so and the correction had
#: gone the wrong way: 1.2D is (5.3.1b) with its live-load term dropped, which is not a
#: combination ACI publishes. Every demand this module returns rose 17%, and the 3-#5
#: selection still clears — the two-#5 conclusion the note carried does not, and did not at
#: 1.2D either (see :func:`check_veneer_beam` on ACI §9.6.1.2).
DEAD_LOAD_FACTOR = 1.4

#: ACI 318-19 Table 21.2.1 — shear and torsion.
PHI_SHEAR_TORSION = 0.75

#: ACI 318-19 §22.7.4.1 (threshold) and §22.7.5.1 (cracking), as multiples of
#: ``lambda sqrt(f'c) * Acp^2 / pcp`` for a non-prestressed section.
#:
#: The two answer different questions and the note conflated them. **Below the threshold**,
#: torsion may be neglected outright. **Above it**, the member needs at least §9.6.4's
#: minimum torsional reinforcement — closed hoops with 135-degree hooks plus longitudinal
#: steel — even where the torsion is a compatibility effect. **Below cracking**, §22.7.3.2
#: lets an indeterminate member redistribute, so the design torsion need not exceed the
#: cracking value; it does not excuse the detailing the threshold triggers.
TORSION_THRESHOLD_COEFFICIENT = 0.25
TORSION_CRACKING_COEFFICIENT = 4.0


@dataclass(frozen=True)
class VeneerBeamResult:
    effective_span_ft: float
    service_load_plf: float
    factored_load_plf: float
    factored_moment_ftlb: float
    factored_shear_lb: float
    effective_depth_in: float
    required_steel_in2: float
    minimum_steel_in2: float
    provided_steel_in2: float
    flexure_ratio: float
    shear_ratio: float
    immediate_deflection_in: float
    long_term_deflection_in: float
    deflection_limit_in: float
    torsion_ftlb_per_ft: float
    #: The FACTORED torsion at the support, ft-lb. ``t * L / 2`` at the dead-load factor.
    factored_torsion_ftlb: float
    #: ``phi * T_th`` — below this, ACI 318-19 §22.7.4.1 permits torsion to be ignored.
    phi_threshold_torsion_ftlb: float
    #: ``phi * T_cr`` — below this an indeterminate member may redistribute (§22.7.3.2).
    phi_cracking_torsion_ftlb: float
    unresolved: tuple[str, ...]

    @property
    def torsion_may_be_neglected(self) -> bool:
        """True only below the §22.7.4.1 threshold — which on this beam it is NOT."""
        return self.factored_torsion_ftlb <= self.phi_threshold_torsion_ftlb

    @property
    def torsion_redistributes(self) -> bool:
        """True below cracking: the twist sheds into the slab rather than being resisted."""
        return self.factored_torsion_ftlb <= self.phi_cracking_torsion_ftlb


def check_veneer_beam(*, clear_span_ft: float = 19.0, bearing_in: float = 6.0,
                       width_in: float = 12.0, depth_in: float = 17.75,
                       fc_psi: float = 5000.0, fy_psi: float = 60000.0,
                       clear_cover_in: float = 2.0, stirrup_diameter_in: float = 0.375,
                       longitudinal_bar_diameter_in: float = 0.625,
                       provided_bar_count: int = 3, provided_bar_area_in2: float = 0.31,
                       veneer_load_plf: float = 308.0,
                       beam_load_plf: float = 222.0,
                       eccentricity_in: float = 4.14) -> VeneerBeamResult:
    """Screening flexure, shear, deflection and torsion for the court's veneer beam.

    ``eccentricity_in`` is the wythe's centre off the beam's, 4.14" as built — the wythe is
    deliberately off-centre so the cavity survives, which §4 of the note works out.

    **On the steel selection and ACI §9.6.1.2.** The minimum is the GREATER of
    ``3 sqrt(f'c) b d / fy`` and ``200 b d / fy``. At the real mix — 5,000 psi, not the
    4,000 the note computed at — those are 0.639 and 0.603 in^2, so 0.639 governs and
    **2 #5 (0.620 in^2) does not clear it**. Nor does the §9.6.1.3 one-third-over exception
    rescue it: 4/3 of the demand steel is 0.771 in^2, larger still. Three #5 is the study
    section and it clears both.
    """
    d = depth_in - clear_cover_in - stirrup_diameter_in - longitudinal_bar_diameter_in / 2.0
    center_span_ft = clear_span_ft + bearing_in / 12.0
    effective_span_ft = min(clear_span_ft + d / 12.0, center_span_ft)
    service_load = veneer_load_plf + beam_load_plf
    factored_load = DEAD_LOAD_FACTOR * service_load
    moment = factored_load * effective_span_ft ** 2 / 8.0
    shear = factored_load * effective_span_ft / 2.0
    required = moment * 12.0 / (0.9 * fy_psi * 0.9 * d)
    minimum = max(
        3.0 * math.sqrt(fc_psi) * width_in * d / fy_psi,
        200.0 * width_in * d / fy_psi,
    )
    provided = provided_bar_count * provided_bar_area_in2
    a = provided * fy_psi / (0.85 * fc_psi * width_in)
    phi_mn_ftlb = 0.9 * provided * fy_psi * (d - a / 2.0) / 12.0
    phi_vc_lb = 0.75 * 2.0 * math.sqrt(fc_psi) * width_in * d

    # --- Torsion, computed rather than dismissed (ACI 318-19 §22.7) -------------------
    # The wythe sits on the beam's north edge, so its weight arrives at an eccentricity and
    # twists the section. The note asserted this away as "compatibility torsion, neglected";
    # the arithmetic says the demand is below CRACKING (so it does redistribute) and above
    # the THRESHOLD (so §9.6.4's closed hoops and longitudinal steel are still owed). Two
    # different provisions, two different answers, and only one of them was quoted.
    torsion_per_ft = veneer_load_plf * eccentricity_in / 12.0
    factored_torsion = DEAD_LOAD_FACTOR * torsion_per_ft * effective_span_ft / 2.0
    area_cp_in2 = width_in * depth_in
    perimeter_cp_in = 2.0 * (width_in + depth_in)
    section_modulus_in3 = area_cp_in2 ** 2 / perimeter_cp_in
    # In-lb from the ACI expression; /12 to the ft-lb everything else here is in.
    threshold_torsion = (TORSION_THRESHOLD_COEFFICIENT * math.sqrt(fc_psi)
                         * section_modulus_in3 / 12.0)
    cracking_torsion = (TORSION_CRACKING_COEFFICIENT * math.sqrt(fc_psi)
                        * section_modulus_in3 / 12.0)

    span_in = effective_span_ft * 12.0
    inertia_in4 = width_in * depth_in ** 3 / 12.0
    modulus_psi = 57000.0 * math.sqrt(fc_psi)
    immediate = 5.0 * (service_load / 12.0) * span_in ** 4 / (
        384.0 * modulus_psi * inertia_in4
    )
    long_term = immediate * 3.0  # screening: sustained dead load, xi=2.0 plus immediate
    return VeneerBeamResult(
        effective_span_ft=effective_span_ft, service_load_plf=service_load,
        factored_load_plf=factored_load, factored_moment_ftlb=moment,
        factored_shear_lb=shear, effective_depth_in=d,
        required_steel_in2=required, minimum_steel_in2=minimum,
        provided_steel_in2=provided,
        flexure_ratio=moment / phi_mn_ftlb, shear_ratio=shear / phi_vc_lb,
        immediate_deflection_in=immediate, long_term_deflection_in=long_term,
        deflection_limit_in=span_in / 240.0,
        torsion_ftlb_per_ft=torsion_per_ft,
        factored_torsion_ftlb=factored_torsion,
        phi_threshold_torsion_ftlb=PHI_SHEAR_TORSION * threshold_torsion,
        phi_cracking_torsion_ftlb=PHI_SHEAR_TORSION * cracking_torsion,
        unresolved=(
            "verify beam-to-wall pocket restraint and bar development",
            # ** NOT "before neglecting torsion" ANY MORE. ** The threshold test is computed
            # and the demand is above it, so the detailing is owed whatever the
            # compatibility argument concludes; what is still open is the redistribution,
            # which needs the slab bearing to be real.
            "provide ACI 318-19 §9.6.4 minimum torsional reinforcement — closed hoops with "
            "135-degree hooks plus longitudinal steel — the factored torsion exceeds the "
            "§22.7.4.1 threshold even though it redistributes below cracking",
            "verify the garden slab bears on the beam's full south face before relying on "
            "§22.7.3.2 redistribution",
            "confirm sustained-load fraction, cracking and shrinkage restraint",
            "design masonry anchors for the full insulated standoff",
        ),
    )


# --- The registered record's arithmetic (2026-09-20, note §6) -----------------------------
# Pure functions, inches/pounds in and out; ``engineering/veneer_beam.py`` reads the plan and
# feeds them. ``check_veneer_beam`` above stays the report's screening at its literals.

#: ACI 318-19 Table 24.2.4.1.3: ξ for sustained load of five years or more.
SUSTAINED_XI = 2.0
#: Es, psi (ACI 318-19 §20.2.2.2).
STEEL_MODULUS_PSI = 29_000_000.0


@dataclass(frozen=True)
class TorsionDesign:
    """ACI 318-19 §22.7.6/§22.7.7 at the full factored twist — no §22.7.3.2 redistribution."""

    ph_in: float
    aoh_in2: float
    at_s_required: float        # in²/in, one leg
    at_s_provided: float        # in²/in, one leg
    combined_stress_psi: float  # §22.7.7.1(a) left side
    stress_limit_psi: float     # §22.7.7.1(a) right side
    hoop_spacing_max_in: float  # §9.7.6.3.3
    transverse_min: float       # §9.6.4.2, (Av + 2At)/s
    transverse_provided: float
    al_required_in2: float      # max(§22.7.6.1b, §9.6.4.3)


def torsion_design(*, tu_ftlb: float, vu_lb: float, width_in: float, depth_in: float,
                   d_in: float, cover_in: float, hoop_diameter_in: float,
                   hoop_leg_area_in2: float, hoop_spacing_in: float, fc_psi: float,
                   fy_psi: float = 60000.0) -> TorsionDesign:
    """Closed-hoop torsion design at θ 45° and the §9.6.4/§9.7.6 detailing rows (note §6c)."""
    root = math.sqrt(fc_psi)
    x1 = width_in - 2.0 * cover_in - hoop_diameter_in
    y1 = depth_in - 2.0 * cover_in - hoop_diameter_in
    ph, aoh = 2.0 * (x1 + y1), x1 * y1
    tu_inlb = tu_ftlb * 12.0
    at_s = tu_inlb / (2.0 * PHI_SHEAR_TORSION * 0.85 * aoh * fy_psi)
    shear = vu_lb / (width_in * d_in)
    twist = tu_inlb * ph / (1.7 * aoh ** 2)
    base = 5.0 * root * width_in * depth_in / fy_psi
    al_min = min(base - at_s * ph, base - 25.0 * width_in / fy_psi * ph)
    return TorsionDesign(
        ph_in=ph, aoh_in2=aoh, at_s_required=at_s,
        at_s_provided=hoop_leg_area_in2 / hoop_spacing_in,
        combined_stress_psi=math.hypot(shear, twist),
        stress_limit_psi=PHI_SHEAR_TORSION * (2.0 * root + 8.0 * root),
        hoop_spacing_max_in=min(ph / 8.0, 12.0),
        transverse_min=max(0.75 * root * width_in / fy_psi, 50.0 * width_in / fy_psi),
        transverse_provided=2.0 * hoop_leg_area_in2 / hoop_spacing_in,
        al_required_in2=max(at_s * ph, al_min),
    )


@dataclass(frozen=True)
class Deflection:
    """ACI 318-19 §24.2: Ie by Table 24.2.3.5, λΔ by §24.2.4.1, on a span with equal partial
    end fixity α (``end_fixity``). α = 0 is the simple span and is the default."""

    cracking_moment_ftlb: float
    cracked_inertia_in4: float
    #: Ie at MIDSPAN when α = 0; the §24.2.3.6 average ``0.70 Ie,mid + 0.30 Ie,end`` when not.
    effective_inertia_in4: float
    immediate_total_in: float
    immediate_self_in: float
    long_term_factor: float
    after_attachment_in: float
    span_in: float
    #: α — the end moment as a fraction of ``wL²/12``. Serviceability only; see note §6f.
    end_fixity: float = 0.0
    #: Ie at the SUPPORTS under the service load. Equal to Ig while the end stays uncracked.
    effective_inertia_end_in4: float = 0.0
    #: The SERVICE end moment ``α wL²/12``, ft-lb. The factored one is the record's to form.
    negative_moment_ftlb: float = 0.0

    @property
    def limit_480_in(self) -> float:
        """ACI 318-19 Table 24.2.2 — the looser of the pair."""
        return self.span_in / 480.0

    @property
    def limit_600_in(self) -> float:
        """TMS 402-22 §13.1.2.3 — the governing limit for a member supporting veneer."""
        return self.span_in / 600.0


def deflection_after_attachment(*, span_ft: float, service_plf: float, self_plf: float,
                                width_in: float, depth_in: float, d_in: float,
                                tension_in2: float, compression_in2: float,
                                fc_psi: float, end_fixity: float = 0.0) -> Deflection:
    """Long-term deflection under all sustained load plus the attached load's immediate share.

    Table 24.2.2's "after attachment" quantity for a member supporting an element likely to
    be damaged. Everything here is dead load, so all of it is sustained (note §6d).

    ``end_fixity`` is α in ``M_end = α wL²/12``, the equal-rotational-spring model of note
    §6f: ``M_mid = wL²/8 − M_end`` and ``Δ = wL⁴(5 − 4α)/(384 E Ie)``. **α = 0 reproduces the
    simple span bit for bit** — including reading Ie at midspan ALONE, because §24.2.3.6's
    ``0.70 Ie,mid + 0.30 Ie,end`` average is written for a member continuous at both ends and
    a simple span is neither. Serviceability only: nothing about strength reads this.
    """
    ec = 57000.0 * math.sqrt(fc_psi)
    n = STEEL_MODULUS_PSI / ec
    ig = width_in * depth_in ** 3 / 12.0
    mcr = 7.5 * math.sqrt(fc_psi) * ig / (depth_in / 2.0)          # in-lb, §19.2.3.1
    half_b, na = width_in / 2.0, n * tension_in2
    kd = (-na + math.sqrt(na * na + 4.0 * half_b * na * d_in)) / (2.0 * half_b)
    icr = width_in * kd ** 3 / 3.0 + na * (d_in - kd) ** 2
    span_in = span_ft * 12.0
    #: ``5 − 4α``: exactly 5.0 at α = 0, so the default expression is unchanged.
    shape = 5.0 - 4.0 * end_fixity

    def _ie(ma_ftlb: float) -> float:
        ma = ma_ftlb * 12.0
        return ig if ma <= 2.0 / 3.0 * mcr else (
            icr / (1.0 - (2.0 / 3.0 * mcr / ma) ** 2 * (1.0 - icr / ig)))

    def effective(plf: float) -> tuple[float, float, float, float]:
        m_end = end_fixity * plf * span_ft ** 2 / 12.0
        ie_mid, ie_end = _ie(plf * span_ft ** 2 / 8.0 - m_end), _ie(m_end)
        ie = ie_mid if end_fixity == 0.0 else 0.70 * ie_mid + 0.30 * ie_end
        return ie, ie_end, m_end, shape * (plf / 12.0) * span_in ** 4 / (384.0 * ec * ie)

    ie_total, ie_end, m_end, total = effective(service_plf)
    _ie_self, _ie_self_end, _m, own = effective(self_plf)
    factor = SUSTAINED_XI / (1.0 + 50.0 * compression_in2 / (width_in * d_in))
    return Deflection(
        cracking_moment_ftlb=mcr / 12.0, cracked_inertia_in4=icr,
        effective_inertia_in4=ie_total, immediate_total_in=total, immediate_self_in=own,
        long_term_factor=factor, after_attachment_in=factor * total + (total - own),
        span_in=span_in, end_fixity=end_fixity, effective_inertia_end_in4=ie_end,
        negative_moment_ftlb=m_end,
    )
