"""NDS 2018 §12.3.1 single-shear yield limit for a nail, D < 1/4in (Table 12.3.1A).

Oracle: ``houses/catlin/notes/canopy_garage_diaphragm.md`` §3b, worked by hand.
"""

from math import sqrt

#: NDS Table 12.3.1B: Rd = K_D = 2.2 for D <= 0.17in, every mode.
REDUCTION_TERM_SMALL_NAIL = 2.2


def dowel_bearing_psi(gravity: float) -> float:
    """NDS Table 12.3.3 footnote: Fe = 16,600 G^1.84 for D < 1/4in."""
    return 16_600.0 * gravity ** 1.84


def nail_single_shear_lb(diameter_in: float, side_in: float, main_in: float,
                         side_gravity: float, main_gravity: float,
                         fyb_psi: float) -> tuple[float, str]:
    """The governing reference Z and its mode, before adjustment factors."""
    if diameter_in > 0.17:
        raise ValueError("this reads K_D for D <= 0.17in only")
    d, ls, lm = diameter_in, side_in, main_in
    fes, fem = dowel_bearing_psi(side_gravity), dowel_bearing_psi(main_gravity)
    re, rt = fem / fes, lm / ls
    rd = REDUCTION_TERM_SMALL_NAIL
    k1 = (sqrt(re + 2 * re ** 2 * (1 + rt + rt ** 2) + rt ** 2 * re ** 3)
          - re * (1 + rt)) / (1 + re)
    k2 = -1 + sqrt(2 * (1 + re) + 2 * fyb_psi * (1 + 2 * re) * d ** 2 / (3 * fem * lm ** 2))
    k3 = -1 + sqrt(2 * (1 + re) / re + 2 * fyb_psi * (2 + re) * d ** 2 / (3 * fem * ls ** 2))
    modes = {
        "Im": d * lm * fem / rd,
        "Is": d * ls * fes / rd,
        "II": k1 * d * ls * fes / rd,
        "IIIm": k2 * d * lm * fem / ((1 + 2 * re) * rd),
        "IIIs": k3 * d * ls * fem / ((2 + re) * rd),
        "IV": d ** 2 / rd * sqrt(2 * fem * fyb_psi / (3 * (1 + re))),
    }
    mode = min(modes, key=modes.get)
    return modes[mode], mode
