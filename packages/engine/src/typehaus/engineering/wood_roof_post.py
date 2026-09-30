"""Pinned 6x6 KDAT roof posts: wet-service column, cap, base and pier anchor.

Oracle: houses/catlin/notes/canopy_garage_diaphragm.md §5a.
"""

from __future__ import annotations

import math

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by

KIND = "wood_roof_post"
BASIS_VERSION = "1"
BASIS = ("AWC NDS 2018 Supplement Table 4D, Southern Pine No. 2 timbers, wet-service row; "
         "NDS §3.7 column stability and §3.9 combined stress; ICC-ES ESR-2604 Table 2; "
         "Simpson L-F-SSNAILS / ICC-ES ESR-1622; ACI 318-19 Ch. 17")
oracled_by(KIND, Oracle(note="canopy_garage_diaphragm.md", section="§5a",
                        test="tests/test_wood_roof_post_calcs.py"))

# Table 4D explicitly publishes these Southern Pine timber values for WET service.
SIDE_IN = 5.5
FC_WET_PSI = 525.0
FB_WET_PSI = 850.0
EMIN_WET_PSI = 440_000.0
CD_SNOW = 1.15
CD_WIND = 1.60
SAWN_C = 0.8
SLENDERNESS_LIMIT = 50.0
R507_4_HEIGHT_FT = 14.0
# ESR-2604 Table 2's CCQ download and ESR-1622's ABU66 download are recorded
# in the catalog citation but its AllowableLoads leaves download unset.
CCQ_DOWNLOAD_LB = 24_065.0
ABU_DOWNLOAD_LB = 18_205.0


def column_stability(length_in: float, fc_star_psi: float) -> tuple[float, float]:
    """NDS §3.7.1.5: (FcE, Cp), K = 1 at pinned head and foot."""
    fce = 0.822 * EMIN_WET_PSI / (length_in / SIDE_IN) ** 2
    ratio = fce / fc_star_psi
    term = (1.0 + ratio) / (2.0 * SAWN_C)
    cp = term - math.sqrt(term ** 2 - ratio / SAWN_C)
    return fce, cp


def _posts(ctx: EngineeringContext):
    from typehaus.engineering.roof_lateral import roof_winds

    return sorted(((post, wind) for wind in roof_winds(ctx).values() for post in wind.pinned
                   if getattr(ctx.plan.by_tag(post.tag), "assembly", None)
                   in {"POST_KDAT", "POST_KDAT_WRAPPED_PVC"}),
                  key=lambda row: row[0].tag)


@keys(KIND)
def enumerate_posts(ctx: EngineeringContext) -> list[str]:
    return [post.tag for post, _ in _posts(ctx)]


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    return [_one(ctx, post, wind) for post, wind in _posts(ctx)]


def _one(ctx: EngineeringContext, post, wind) -> EngineeringRecord:
    from typehaus.engineering.holdown_anchor import round_pier_anchor
    from typehaus.engineering.holdown_anchor import states as anchor_states
    from typehaus.engineering.pier_basis import (
        DECK_DEAD_LOAD_PSF,
        _round_size,
        design_roof_snow_psf,
        roof_tributaries,
    )
    from typehaus.library.hardware.simpson_post_bases import (
        ABU66SS_POST_BASE,
        CCQ46SDS_POST_CAP,
    )
    from typehaus.model.structure import Beam
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi

    element = ctx.plan.by_tag(post.tag)
    header = next((e.tag for e in ctx.plan.all_elements()
                   if isinstance(e, Beam) and post.tag in (e.bearing_refs or ())), None)
    connectors = [e for e in ctx.plan.all_elements()
                  if getattr(e, "connects", ()) and post.tag in e.connects]
    cap = next((e for e in connectors if e.size == "CCQ46SDS2.5"), None)
    base = next((e for e in connectors if e.size == "ABU66SS"), None)
    pier = ctx.plan.by_tag(post.below or "")
    pier_size = _round_size(getattr(pier, "size", "") or "") if pier else None
    trib = roof_tributaries(ctx)[0].get(post.tag, 0.0)
    missing = [text for ok, text in (
        (element.size == "6x6", f"NDS wet-service values for {element.size!r}"),
        (trib > 0, "a roof tributary on the post"),
        (header is not None, "a roof header bearing on the post"),
        (cap is not None, "a CCQ46SDS2.5 head cap"),
        (base is not None, "an ABU66SS stainless standoff base"),
        (pier_size is not None, "a round concrete pier under the base"),
    ) if not ok]
    tags = tuple(t for t in (post.tag, header, post.below,
                              getattr(cap, "tag", None), getattr(base, "tag", None)) if t)
    if missing:
        return EngineeringRecord(item_id=item_id(KIND, post.tag), kind=KIND, key=post.tag,
                                 basis_version=BASIS_VERSION, basis=BASIS,
                                 status=Status.INCOMPLETE,
                                 summary=f"{post.tag}: wood roof post cannot be graded",
                                 missing=tuple(missing), element_tags=tags)

    snow, snow_basis = design_roof_snow_psf(ctx)
    length_in = post.length_ft * 12.0
    area = SIDE_IN ** 2
    section_modulus = SIDE_IN ** 3 / 6.0
    # The KDAT material is 600 kg/m³ in the catalog; the actual 5.5-inch square is 7.87 plf.
    weight_plf = 600.0 * (SIDE_IN * 0.0254) ** 2 * 0.3048 * 2.20462262185
    axial = trib * (DECK_DEAD_LOAD_PSF + snow) + weight_plf * post.length_ft
    fc_star = FC_WET_PSI * CD_SNOW
    fce, cp = column_stability(length_in, fc_star)
    fc_prime = fc_star * cp
    fc_actual = axial / area
    drag_plf = wind.pressure_psf * post.width_ft
    moment_lb_in = drag_plf * post.length_ft ** 2 / 8.0 * 12.0
    fb_actual = moment_lb_in / section_modulus
    # This exceeds the NDS §3.9 compression-squared term for fc/Fc' < 1 and retains
    # the §3.9 second-order amplification, so it is a conservative uniaxial screen.
    interaction = fc_actual / fc_prime + fb_actual / (FB_WET_PSI * CD_WIND)
    interaction /= 1.0 - fc_actual / fce
    uplift = max(trib * (wind.pressure_psf - 0.6 * DECK_DEAD_LOAD_PSF), 0.0)
    cap_allow = CCQ46SDS_POST_CAP.allowable
    base_allow = ABU66SS_POST_BASE.allowable
    assert cap_allow and base_allow and pier_size
    states = [
        LimitState("NDS column slenderness", length_in / SIDE_IN, SLENDERNESS_LIMIT, "",
                   "NDS 2018 §3.7.1.4, pinned K = 1", is_detailing=True),
        LimitState("NDS wet-service axial", axial, fc_prime * area, "lb",
                   f"Table 4D Fc {FC_WET_PSI:g} psi (wet row) x C_D {CD_SNOW:g} x "
                   f"C_P {cp:.3f}; FcE {fce:.0f} psi, D + S ({snow_basis})"),
        LimitState("NDS combined axial and own drag", interaction, 1.0, "",
                   f"§3.9 conservative uniaxial screen; axial stress {fc_actual:.1f} psi, "
                   f"drag moment {moment_lb_in / 12:.1f} lb-ft, bending stress "
                   f"{fb_actual:.1f} psi, wet Fb {FB_WET_PSI:g} x C_D {CD_WIND:g}"),
        LimitState("IRC R507.4 height cross-check", post.length_ft, R507_4_HEIGHT_FT, "ft",
                   "2018 IRC Table R507.4, 6x6; the NDS snow check governs this roof",
                   is_detailing=True),
        LimitState("CCQ46SDS2.5 head uplift", uplift, cap_allow.uplift_lb, "lb",
                   "ICC-ES ESR-2604 Table 2; SYP G 0.55 meets §3.2.2 minimum 0.50"),
        LimitState("CCQ46SDS2.5 head download", axial, CCQ_DOWNLOAD_LB, "lb",
                   "ICC-ES ESR-2604 Table 2, C_D 1.0 lower-bound download"),
        LimitState("ABU66SS base uplift", uplift, base_allow.uplift_lb, "lb",
                   "Simpson L-F-SSNAILS parity to ESR-1622 bolted ABU66 row"),
        LimitState("ABU66SS base download", axial, ABU_DOWNLOAD_LB, "lb",
                   "Simpson L-F-SSNAILS parity to ESR-1622 ABU66 row"),
    ]
    pier_fc = fc_psi(concrete_spec_for(ctx.plan, pier)) or 3000.0
    anchor = round_pier_anchor(f"{post.tag} base", pier_size[0], pier_fc)
    states += anchor_states(anchor, uplift, post.base_lb,
                            f"net 0.6D + 0.6W uplift {uplift:.1f} lb",
                            f"own post drag {post.base_lb:.1f} lb")
    governing = max((s for s in states if not s.is_detailing),
                    key=lambda s: s.demand / s.capacity if s.capacity else float("inf"))
    return EngineeringRecord(
        item_id=item_id(KIND, post.tag), kind=KIND, key=post.tag,
        basis_version=BASIS_VERSION, basis=BASIS,
        status=Status.OVER if any(not s.ok for s in states) else Status.OK,
        summary=f"{post.tag}: wet-service 6x6 KDAT, {governing.name} governs at "
                f"{governing.demand / governing.capacity:.2f}",
        inputs=(Quantity("roof_tributary_ft2", trib, "ft2", 0.01),
                Quantity("post_length_in", length_in, "in", 0.01),
                Quantity("pier_fc_psi", pier_fc, "psi", 1.0),
                Quantity("axial_lb", axial, "lb", 1.0),
                Quantity("uplift_lb", uplift, "lb", 1.0)),
        limit_states=tuple(states), element_tags=tags,
        notes=("The PVC wrap is a nonstructural finish. It needs an open, drained base and "
               "an inspectable/removable panel; it contributes no column capacity.",
               "The CCQ46SDS2.5 and ABU66SS catalog records publish no lateral capacity. "
               "This calculation grades the post's own bending and the concrete anchor's "
               "shear, but a positive detail transferring the 24 lb reaction at each end "
               "through the cap and base remains to be engineered."))
