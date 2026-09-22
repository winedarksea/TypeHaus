"""What a credited end fixity ADDS to a veneer beam's record — note §6f.

Split from ``veneer_beam.py`` for size, on the ``veneer_beam_anchorage.py`` precedent.

The deflection credit is the reason ``FoundationWall.end_restraint`` exists; these are its
consequences, and grading them is what makes the credit honest rather than free. Three
things arrive at the monolithic joint once α > 0 and none of them is graded anywhere else:
the beam's own **negative flexure** at the support, the **moment the wall receives** (a
plain-concrete section over ``b + 2t``, because no authored bar crosses that joint in the
right direction), and the **shear** that moment's couple delivers across the same band.

**The claim is graded at α, the SUPPORT at α and again at ``elastic_fixity``.** A joint
stiffer than claimed is conservative for the beam and UNCONSERVATIVE for the wall, so the
wall's row prints the elastic bound beside the claimed demand; if the wall could not take
the elastic moment the derate would be buying deflection with someone else's capacity.

Oracle: ``houses/catlin/notes/sunken_garden_veneer_beam.md`` §6f.
"""

from __future__ import annotations

from typing import Any

from typehaus.engineering.item import LimitState
from typehaus.model.rebar import BARS

_M_PER_IN = 0.0254
#: ACI 318-19 Table 14.5.2.1 (US customary): ``Mn = 5 λ √f'c · Sm``, f'c in psi. The
#: 0.42 λ √f'c form quoted in SI summaries is the same expression with f'c in MPa.
PLAIN_FLEXURE_COEFFICIENT = 5.0
#: ACI 318-19 Table 21.2.1 — flexure, shear and bearing on structural PLAIN concrete.
PHI_PLAIN = 0.60
#: ACI 318-19 Table 22.5.5.1(a) — λ √f'c multiplier for Vc with no shear reinforcement.
SHEAR_COEFFICIENT = 2.0
PHI_SHEAR = 0.75


def plain_flexural_capacity_ftlb(*, fc_psi: float, width_in: float,
                                 thickness_in: float) -> float:
    """φMn of a structural plain concrete section, ACI 318-19 Table 14.5.2.1, ft-lb."""
    section_modulus = width_in * thickness_in ** 2 / 6.0
    return (PHI_PLAIN * PLAIN_FLEXURE_COEFFICIENT * fc_psi ** 0.5
            * section_modulus / 12.0)


def _effective_width_in(restraint: Any, thickness_in: float, width_in: float) -> float:
    """The authored spread, or ``b + 2t`` — ACI's usual reading of a load into a wall."""
    authored = getattr(restraint, "effective_width", None)
    return float(authored.inches) if authored is not None else width_in + 2.0 * thickness_in


def joint_states(ctx: Any, restraint: Any, supports: tuple[Any, ...], *,
                 factored_moment_ftlb: float, beam_phi_mn_ftlb: float, beam_width_in: float,
                 beam_d_in: float) -> tuple[list[LimitState], list[str]]:
    """``(states, notes)`` for the rows the fixity adds. ``supports`` are the two support
    bands; ``factored_moment_ftlb`` is the SIMPLE-SPAN Mu (``wu L²/8``) the record grades."""
    from typehaus.engineering.retaining_basis import bar_for_roles
    from typehaus.resolve.concrete import concrete_spec_for, cover_for, fc_psi

    alpha = float(restraint.fixity)
    elastic = restraint.elastic_fixity
    # M_end = α wL²/12 = α (2/3) (wL²/8): the record already has the simple-span Mu.
    m_end = alpha * factored_moment_ftlb * 2.0 / 3.0
    states = [LimitState(
        "negative flexure at the supports", m_end, beam_phi_mn_ftlb, "ft-lb",
        f"ACI 318-19 §22.2, φ 0.90 on the mirror top row; M_end = α wu L²/12 at the CLAIMED "
        f"α {alpha:g}"
        + (f" (elastic estimate {elastic:g}, derated)" if elastic is not None else ""))]

    for sup in supports:
        element = ctx.plan.by_tag(sup.tag)
        wall_fc = fc_psi(concrete_spec_for(ctx.plan, element))
        wall_cover, _where = cover_for(ctx.plan, element)
        if wall_fc is None or wall_cover is None:
            continue
        thickness = (sup.u1 - sup.u0) / _M_PER_IN
        b_eff = _effective_width_in(restraint, thickness, beam_width_in)
        phi_mn = plain_flexural_capacity_ftlb(fc_psi=wall_fc, width_in=b_eff,
                                              thickness_in=thickness)
        vertical = bar_for_roles(getattr(element, "reinforcement", None), ("vertical",))
        db = BARS[vertical[0]].diameter_in if vertical and vertical[0] in BARS else 0.0
        d_wall = thickness - wall_cover - db / 2.0
        bound = (f"; at the full elastic α {elastic:g} the wall would receive "
                 f"{m_end / alpha * elastic:,.0f} ft-lb, d/c "
                 f"{m_end / alpha * elastic / phi_mn:.3f}" if elastic and alpha else "")
        states.append(LimitState(
            f"end moment into {sup.tag}, plain concrete", m_end, phi_mn, "ft-lb",
            f"ACI 318-19 Table 14.5.2.1 Mn = 5λ√f'c·Sm, φ {PHI_PLAIN} (Table 21.2.1), over "
            f"b_eff {b_eff:.0f}\" = b + 2t at f'c {wall_fc:,.0f} — no authored bar crosses "
            f"this joint in flexure, so the section is graded PLAIN{bound}"))
        states.append(LimitState(
            f"end-moment shear into {sup.tag}", m_end * 12.0 / beam_d_in,
            PHI_SHEAR * SHEAR_COEFFICIENT * wall_fc ** 0.5 * b_eff * d_wall, "lb",
            f"ACI 318-19 Table 22.5.5.1(a) over b_eff {b_eff:.0f}\", d {d_wall:.3f}\" "
            f"({thickness:.0f}\" less {wall_cover:g}\" cover"
            + (f" and #{vertical[0]}/2" if db else "") + "); the end moment arrives as the "
            f"couple T = C = M_end/d over the beam's own {beam_d_in:.4f}\" lever arm"))

    notes = [
        f"END FIXITY, CREDITED FOR SERVICEABILITY ONLY (note §6f): α {alpha:g} is CLAIMED"
        + (f", a {elastic / alpha:.2g}:1 derate on the elastic estimate {elastic:g} "
           f"(k_θ = 3EI_w/h on the wall ABOVE the joint alone, far end pinned, gross section)"
           if elastic and alpha else "")
        + ". Midspan flexure stays graded at α = 0, so a joint softer than claimed costs "
        "deflection and can never buy strength; what the fixity adds is graded above, and "
        "the support is graded at the elastic bound as well as at the claim."
        + (f" SOURCE: {restraint.source}" if getattr(restraint, "source", None) else ""),
    ]
    return states, notes
