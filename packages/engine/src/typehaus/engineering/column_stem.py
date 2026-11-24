"""The wall stem under a fixed cast column: flexure below the dowels, and the stem as the
E-W cantilever it is (review B-05, D-R3, verifier 2026-11-23).

``column_support`` grades the JOINT a column makes with a wall top. The stem below it carries
the column's moment AND shear down the wall, and IRC Table R404.1.2(8), which grades the wall,
publishes no surcharge column and assumes a PROPPED head. Two rows:

* **Below the dowels.** The developed dowels reinforce the head; past their tips the moment
  spreads into PLAIN concrete at 45 deg from the column's width (ACI 318-19 §14.5.2.1,
  ``M_n = 5 lambda sqrt(f'c) S``, phi 0.60), **clipped at the stem's free end**. Taken as a
  cantilever with NO prop: the moment at the tips is ``M_u + V_u x`` over the embedment ``x``
  (the head shear's lever), not ``M_u`` alone.
* **The stem as a cantilever under E-W wind.** All four columns push BOTH stems the same way,
  so the porch diaphragm cannot prop each stem against the other: the E-W lateral reaches the
  ground through the stems, each a cantilever from its footing carrying its columns' ``M + V H``
  over the 45 deg spread, plus the retained soil's moment (active, 1.6 H). The wall's own
  vertical bars on the earth face are the section.

**Oracle.** ``houses/catlin/notes/balcony_moment_columns.md`` §22, §27.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.engineering.item import LimitState, Quantity, Step, num

#: ACI 318-19 Table 21.2.1 — plain concrete in flexure.
PHI_PLAIN = 0.60
#: ACI 318-19 §14.5.2.1: ``M_n = 5 lambda sqrt(f'c) S``.
PLAIN_FLEXURE_COEFFICIENT = 5.0
#: A column's moment spreads into the wall at 45 deg each side of its own width.
SPREAD_SLOPE = 1.0
#: ASCE 7-16 §2.3.1 combination 4's lateral earth factor, ``1.6 H`` where soil adds.
SOIL_LOAD_FACTOR = 1.6
#: ACI 318-19 Table 21.2.1, tension-controlled flexure.
PHI_FLEXURE = 0.90


def plain_flexure_lb_in(fc_psi: float, width_in: float, thickness_in: float) -> float:
    """``phi M_n`` of a plain rectangular section, lb-in."""
    return (PHI_PLAIN * PLAIN_FLEXURE_COEFFICIENT * math.sqrt(fc_psi)
            * width_in * thickness_in ** 2 / 6.0)


def spread_width_in(column_radius_in: float, spread_in: float, north_in: float,
                    south_in: float) -> float:
    """The width a column's moment spreads over: the radius plus the 45 deg spread each way
    from its centre, each side stopped at the stem's end (``north_in`` / ``south_in`` are the
    distances from the column centre to the ends of the pour)."""
    reach = column_radius_in + SPREAD_SLOPE * spread_in
    return min(reach, north_in) + min(reach, south_in)


def reinforced_flexure_lb_in_per_ft(fc_psi: float, thickness_in: float, cover_in: float,
                                    bar_diameter_in: float, area_per_ft_in2: float,
                                    fy_psi: float = 60_000.0) -> float:
    """``phi M_n`` per foot of a stem with one curtain of bars at the tension face."""
    depth = thickness_in - cover_in - bar_diameter_in / 2.0
    block = area_per_ft_in2 * fy_psi / (0.85 * fc_psi * 12.0)
    return PHI_FLEXURE * area_per_ft_in2 * fy_psi * (depth - block / 2.0)


@dataclass(frozen=True)
class StemDemand:
    """What the worst §2.3.1 case puts on the wall head, factored, per column."""

    label: str
    mu_lb_in: float
    vu_lb: float


def stem_states(*, tag: str, fc_psi: float, thickness_in: float, column_width_in: float,
                embedment_in: float, north_in: float, south_in: float, demand: StemDemand
                ) -> tuple[list[LimitState], list[Quantity]]:
    """The below-the-dowels row for one column."""
    below = spread_width_in(column_width_in / 2.0, embedment_in, north_in, south_in)
    capacity = plain_flexure_lb_in(fc_psi, below, thickness_in)
    moment = demand.mu_lb_in + demand.vu_lb * embedment_in
    states = [LimitState(
        f"{tag}: stem flexure below the dowels", moment / 12.0, capacity / 12.0, "lb-ft",
        f"ACI 318-19 §14.5.2.1 plain concrete, phi {PHI_PLAIN}, {thickness_in:g}\" stem over "
        f"{below:.0f}\" ({column_width_in / 2.0:g}\" radius + 45 deg spread over the "
        f"{embedment_in:g}\" the dowels run, stopped at the pour's ends, {north_in:.0f}\" / "
        f"{south_in:.0f}\" from this column); the head moment AND its shear's lever, "
        f"M_u + V_u x = {demand.mu_lb_in / 12.0:,.0f} + {demand.vu_lb:,.0f} x "
        f"{embedment_in / 12.0:.1f}', taken the whole way down with no prop credited — "
        f"governed by ASCE 7-16 §2.3.1 {demand.label}",
        combination=f"ASCE 7-16 §2.3.1 {demand.label}",
        working=(
            Step("M_u", "magnified head moment of the governing combination",
                 demand.mu_lb_in / 12.0, "lb-ft", source=f"{demand.label}; the column_support "
                 "joint rows"),
            Step("V_u", "factored head shear", demand.vu_lb, "lb"),
            Step("x", "length the dowels run into the stem", embedment_in / 12.0, "ft",
                 source="the authored dowel embedment"),
            Step("M_tip", "moment at the dowel tips: head moment plus the shear's lever, no "
                 "prop credited", moment / 12.0, "lb-ft", "M_u + V_u x",
                 f"{num(demand.mu_lb_in / 12.0)} + {num(demand.vu_lb)} x "
                 f"{num(embedment_in / 12.0)}"),
            Step("b", "width the moment spreads over: the column radius plus 45 deg each side "
                 "over the dowel length, each side stopped at the end of the pour", below,
                 "in", "min(R + x, n) + min(R + x, s)",
                 f"min({num(column_width_in / 2.0)} + {num(embedment_in)}, {num(north_in)}) "
                 f"+ min({num(column_width_in / 2.0)} + {num(embedment_in)}, "
                 f"{num(south_in)})"),
            Step("phi M_n", f"design moment strength of the plain {thickness_in:g} in. stem "
                 "over that width", capacity / 12.0, "lb-ft",
                 "phi 5 lambda sqrt(f'c) b h^2 / 6 / 12",
                 f"{num(PHI_PLAIN)} x {num(PLAIN_FLEXURE_COEFFICIENT)} x sqrt({num(fc_psi)}) "
                 f"x {num(below)} x {num(thickness_in)}^2 / 6 / 12",
                 "ACI 318-19 §14.5.2.1, phi per Table 21.2.1")))]
    return states, [Quantity(f"{tag}.stem_thickness", thickness_in, "in", 0.125),
                    Quantity(f"{tag}.stem_fc", fc_psi, "psi", 1.0),
                    Quantity(f"{tag}.spread_below_dowels", below, "in", 0.5)]
