"""The wall stem under a fixed cast column: flexure below the dowels, the head prop, the strut.

``column_support`` grades the JOINT a column makes with a wall top. The stem below it carries
the same column moment down the wall (review B-05, D-R3), and IRC Table R404.1.2(8) — what
grades the wall — publishes no surcharge column. Three questions, each a row:

* **Below the dowels.** The developed dowels reinforce the head; past their tips the moment
  spreads into PLAIN concrete at 45° from the column's width (ACI 318-19 §14.5.2.1,
  ``M_n = 5 lambda sqrt(f'c) S``, phi 0.60). Taken as a cantilever with NO prop, so the moment
  is the head's all the way down: the row does not lean on the porch diaphragm.
* **The head prop.** With the wall propped at its head by the porch diaphragm, an end moment
  ``M`` puts ``3M / 2H`` on the prop and a shear ``V`` at the head goes straight to it. The
  force is the porch ledger's and the diaphragm's to deliver; it is stated per column and per
  wall, and what receives it is the strut row.
* **The strut.** The diaphragm delivers the prop in compression to the opposite stem's head,
  which takes it as a cantilever from its footing over the same 45° spread, in plain concrete.

**Oracle.** ``houses/catlin/notes/balcony_moment_columns.md`` §22.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.engineering.item import LimitState, Quantity

#: ACI 318-19 Table 21.2.1 — plain concrete in flexure.
PHI_PLAIN = 0.60
#: ACI 318-19 §14.5.2.1: ``M_n = 5 lambda sqrt(f'c) S``.
PLAIN_FLEXURE_COEFFICIENT = 5.0
#: A column's moment spreads into the wall at 45° each side of its own width.
SPREAD_SLOPE = 1.0


def plain_flexure_lb_in(fc_psi: float, width_in: float, thickness_in: float) -> float:
    """``phi M_n`` of a plain rectangular section, lb-in."""
    return (PHI_PLAIN * PLAIN_FLEXURE_COEFFICIENT * math.sqrt(fc_psi)
            * width_in * thickness_in ** 2 / 6.0)


@dataclass(frozen=True)
class StemDemand:
    """What the worst §2.3.1 case puts on the wall head, factored, per column."""

    label: str
    mu_lb_in: float
    vu_lb: float


def prop_lb(demand: StemDemand, height_in: float) -> float:
    """``V + 3M / 2H``: a shear at the propped head goes to the prop; an end moment on a
    propped cantilever puts ``3M / 2H`` on it."""
    return demand.vu_lb + 1.5 * demand.mu_lb_in / height_in


def stem_states(*, tag: str, wall_tag: str, fc_psi: float, thickness_in: float,
                height_in: float, column_width_in: float, embedment_in: float,
                demand: StemDemand) -> tuple[list[LimitState], list[Quantity], str]:
    """``(states, inputs, prop sentence)`` for one column on a stem."""
    below = column_width_in + 2.0 * SPREAD_SLOPE * embedment_in
    cap_below = plain_flexure_lb_in(fc_psi, below, thickness_in)
    prop = prop_lb(demand, height_in)
    # The strut: the prop on the OPPOSITE stem's head, a cantilever from its footing.
    base_moment = prop * height_in
    strut_width = column_width_in + 2.0 * SPREAD_SLOPE * height_in
    cap_strut = plain_flexure_lb_in(fc_psi, strut_width, thickness_in)
    where = f"governed by ASCE 7-16 §2.3.1 {demand.label}"
    states = [
        LimitState(
            f"{tag}: stem flexure below the dowels", demand.mu_lb_in / 12.0, cap_below / 12.0,
            "lb-ft",
            f"ACI 318-19 §14.5.2.1 plain concrete, phi {PHI_PLAIN}, {thickness_in:g}\" stem over "
            f"{below:.0f}\" ({column_width_in:g}\" column + 45 deg spread over the "
            f"{embedment_in:g}\" the dowels run); the head moment taken the whole way down, no "
            f"prop credited — {where}",
            combination=f"ASCE 7-16 §2.3.1 {demand.label}"),
        LimitState(
            f"{tag}: opposite stem under the head prop (strut)", base_moment / 12.0,
            cap_strut / 12.0, "lb-ft",
            f"ACI 318-19 §14.5.2.1 plain concrete, phi {PHI_PLAIN}: the {prop:,.0f} lb prop "
            f"delivered by the porch diaphragm at the opposite stem's head, {height_in:.1f}\" "
            f"above its footing, over {strut_width:.0f}\" of 45 deg spread; the wall's own bars "
            f"and the retained soil moment (Table R404.1.2(8)) are not in this row — {where}",
            combination=f"ASCE 7-16 §2.3.1 {demand.label}"),
    ]
    inputs = [Quantity(f"{tag}.prop_factored", prop, "lb", 1.0),
              Quantity(f"{tag}.stem_thickness", thickness_in, "in", 0.125),
              Quantity(f"{tag}.stem_fc", fc_psi, "psi", 1.0)]
    sentence = (f"{tag}: {prop:,.0f} lb factored (V {demand.vu_lb:,.0f} + 3M/2H, M "
                f"{demand.mu_lb_in / 12.0:,.0f} lb-ft over {height_in / 12.0:.2f}') into the "
                f"porch diaphragm, {wall_tag}'s head")
    return states, inputs, sentence
