"""Reference design values for engineered members a check grades by arithmetic.

Copied from the evaluation report, never derived. A member grade the catalog does not hold
is an UNKNOWN in the check that wanted it, not an engine default.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemberGrade:
    """Joist/beam-orientation reference values, psi, at normal (100%) load duration, in the
    ``service`` condition they are stated for: a ``"wet"`` row has C_M already taken."""

    tag: str
    fb_psi: float
    #: Fb is published at this depth and scaled by (ref / d) ** exponent (C_V).
    fb_ref_depth_in: float
    fb_size_exponent: float
    fv_psi: float
    e_psi: float
    fc_perp_psi: float
    #: Equivalent specific gravity for a bolt in the face, load perpendicular to grain.
    bolt_g_perp: float
    #: The shear term of the published deflection formula, as the uniform-load form's
    #: coefficient: delta_shear = k * W * L**2 / (E * b * d), W plf, L ft.
    shear_deflection_k: float
    source: str
    service: str = "dry"

    def fb_adjusted_psi(self, depth_in: float) -> float:
        return self.fb_psi * (self.fb_ref_depth_in / depth_in) ** self.fb_size_exponent


MICROLLAM_LVL_2_0E = MemberGrade(
    tag="microllam-lvl-2.0e",
    fb_psi=2600.0, fb_ref_depth_in=12.0, fb_size_exponent=0.136,
    fv_psi=285.0, e_psi=2.0e6, fc_perp_psi=750.0, bolt_g_perp=0.50,
    shear_deflection_k=28.8,
    source="ICC-ES ESR-1387 (Weyerhaeuser; reissued Feb 2025, revised Jul 2026), read "
           "2026-10-05: Table 1, Microllam LVL 2.0E-2600Fb WS, joist/beam orientation — "
           "E 2.0e6, Fb 2,600, Fv 285, Fc-perp 750 psi; footnote 7 C_V = (12/d)^0.136; "
           "footnote 5 combined bending + shear deflection (28.8 W L^2 / E b d); Table 2 "
           "bolts installed in face, load perpendicular to grain, G = 0.50",
)

# The porch's 2x12 KDAT: No. 2 is the grade IRC Table R507.6 (the porch's own span row) is
# published for, and nothing in the house states a better one. Reference values with C_M
# applied; C_F is in the table's size-specific values, C_r is not taken (a 3-ply line under
# one point load is not a repetitive member), C_i is 1.0 (southern pine is not incised).
# Sawn-lumber E is apparent: shear deflection is already in it.
SOUTHERN_PINE_NO2_2X12_WET = MemberGrade(
    tag="southern-pine-no2-2x12-wet",
    fb_psi=750.0, fb_ref_depth_in=11.25, fb_size_exponent=0.0,
    fv_psi=175.0 * 0.97, e_psi=1.4e6 * 0.9, fc_perp_psi=565.0 * 0.67, bolt_g_perp=0.55,
    shear_deflection_k=0.0,
    service="wet",
    source="AWC NDS 2018 Supplement Table 4B, Southern Pine No. 2, 2\"-4\" thick, 12\" "
           "wide: Fb 750, Fv 175, Fc-perp 565, E 1,400,000 psi; Table 4B wet service "
           "factors: C_M 1.0 on Fb (Fb C_F <= 1,150 psi), 0.97 on Fv, 0.67 on Fc-perp, 0.9 "
           "on E. NDS Table 12.3.3A: southern pine G = 0.55",
)

MEMBER_GRADES = {grade.tag: grade for grade in (MICROLLAM_LVL_2_0E,
                                                SOUTHERN_PINE_NO2_2X12_WET)}
