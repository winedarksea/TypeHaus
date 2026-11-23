"""Straight development of a deformed bar in tension on ACI 318-19's general equation.

``resolve/rebar/detailing.development_length_raw_in`` is Table 25.4.2.3's simplified row, which
assumes the bar's confinement is merely adequate. §25.4.2.4 is the general equation and credits
the real cover and spacing (review B-08: the balcony's #5 dowels read 21.2" on the simplified
row and 12.7" on the equation). Both are permitted; the equation is used where the bar's
cover and spacing are known and the simplified row is printed beside it as the bound.

``l_d = (3/40)(f_y / (lambda sqrt(f'c))) (psi_t psi_e psi_s psi_g / ((c_b + K_tr)/d_b)) d_b``,
``(c_b + K_tr)/d_b`` taken no more than 2.5, ``psi_s`` 0.8 for #6 and smaller, ``psi_g`` 1.0 at
Grade 60, never less than the 12" of §25.4.2.1. Oracle: ``notes/balcony_moment_columns.md`` §21.
"""

from __future__ import annotations

import math

CONFINEMENT_CAP = 2.5
MINIMUM_LENGTH_IN = 12.0
SMALL_BAR_DIAMETER_IN = 0.75        # #6, ACI Table 25.4.2.5's psi_s break


def confinement_term(cover_to_centre_in: float, half_spacing_in: float, bar_diameter_in: float,
                     ktr: float = 0.0) -> float:
    """``(c_b + K_tr) / d_b`` capped at 2.5: ``c_b`` the lesser of the cover to the bar's
    centre and half the bars' centre-to-centre spacing."""
    return min((min(cover_to_centre_in, half_spacing_in) + ktr) / bar_diameter_in,
               CONFINEMENT_CAP)


def general_development_in(bar_diameter_in: float, fc_psi: float, fy_psi: float,
                           confinement: float, psi_t: float = 1.0, psi_e: float = 1.0) -> float:
    psi_s = 0.8 if bar_diameter_in <= SMALL_BAR_DIAMETER_IN else 1.0
    ld = (3.0 / 40.0 * fy_psi / math.sqrt(fc_psi) * psi_t * psi_e * psi_s / confinement
          * bar_diameter_in)
    return max(ld, MINIMUM_LENGTH_IN)
