"""Screw withdrawal from a wood support — NDS 2018 §12.2, for a concealed panel leg.

Pure arithmetic, no model types. It exists as its own module because it is the one part of
``wall_panel.py`` a reviewer checks line by line against the standard, and because the
answer is a *rational design*: no manufacturer publishes a pull-out value for a concealed
board-and-batten leg screwed into wood, and IAPMO UES ER-309 expressly permits a design
professional to extend published data by engineering mechanics rather than wait for a row
that will not be printed.

    W  = 2850 G^2 D            NDS 2018 §12.2.1, lb per inch of thread penetration
    W' = W C_D C_M C_t C_eg    §12.2.3 / Table 11.3.1, the adjusted design value
    Z  = W' p                  p = thread penetration into the SIDE member

Two deductions the equation does not spell and a spreadsheet forgets. The panel's own
flange is not the support, so its thickness comes off the length; and the tapered tip
carries no thread, which NDS App. L puts at ``2D`` for a wood screw. What is left is capped
at the support's own thickness — a screw that runs out the back of a 1-1/2" girt is not
holding 2" of wood, whatever its length says on the box.
"""

from __future__ import annotations

from dataclasses import dataclass

#: NDS 2018 §12.2.1. The coefficient is the standard's own, for a wood screw in side grain.
WITHDRAWAL_COEFFICIENT = 2850.0

#: NDS 2018 App. L: a wood screw's tapered tip is ``2D`` long and carries no thread.
TIP_LENGTHS_D = 2.0

#: NDS 2018 Table 2.3.2, wind. The same 1.6 every wind-governed capacity in this house is
#: adjusted by; a fastener is not exempt from it.
C_D_WIND = 1.6

#: NDS 2018 Table 11.3.3, wet service, withdrawal of a screw. 0.7 — the same call
#: ``library/hardware.py`` makes for exterior connectors on this house, and the right one
#: for a rainscreen cavity that wets and dries with the weather.
C_M_WET = 0.7


@dataclass(frozen=True)
class Withdrawal:
    """One screw into one support, from the standard's own terms."""

    w_per_in: float
    """W, lb per inch of penetration, before adjustment."""
    w_adjusted_per_in: float
    """W', after C_D C_M C_t C_eg."""
    thread_penetration_in: float
    """p — what is actually in the wood, tip and flange deducted, capped at the support."""
    capacity_lb: float
    """Z = W' p."""
    reason: str | None = None
    """Why the capacity is zero, when it is. ``None`` when the screw reaches wood."""


def withdrawal_allowable_lb(
    specific_gravity: float,
    diameter_in: float,
    length_in: float,
    support_thickness_in: float,
    flange_thickness_in: float = 0.0,
    *,
    c_d: float = C_D_WIND,
    c_m: float = C_M_WET,
    c_t: float = 1.0,
    c_eg: float = 1.0,
) -> Withdrawal:
    """The allowable withdrawal of one wood screw, NDS 2018 §12.2.

    ``c_eg`` is 1.0 for a screw into side grain and is a parameter only so that an end-grain
    case has to say so; NDS §12.2.4 would put it at 0.75, and this house has none.
    """
    w = WITHDRAWAL_COEFFICIENT * specific_gravity ** 2 * diameter_in
    w_adjusted = w * c_d * c_m * c_t * c_eg
    embedded = length_in - flange_thickness_in - TIP_LENGTHS_D * diameter_in
    penetration = min(max(embedded, 0.0), support_thickness_in)
    reason = None
    if penetration <= 0.0:
        reason = (f"a {length_in:g}\" screw through a {flange_thickness_in:g}\" flange has "
                  f"no thread left in the support once the {TIP_LENGTHS_D:g}D tapered tip "
                  f"is deducted")
    return Withdrawal(w_per_in=w, w_adjusted_per_in=w_adjusted,
                      thread_penetration_in=penetration,
                      capacity_lb=w_adjusted * penetration, reason=reason)


def fastener_demand_lb(pressure_psf: float, spacing_in: float, coverage_in: float) -> float:
    """The load on one fastener: pressure x the area it is the only thing holding.

    One screw per panel per girt is the concealed-leg pattern — the batten hides a single
    line of fasteners at each support — so the tributary area is the girt spacing by the
    panel's net coverage. Coverage is a product fact and the answer moves with it directly:
    an 11" panel is 45% of the demand a 24" one would put on the same screw.
    """
    return pressure_psf * (spacing_in / 12.0) * (coverage_in / 12.0)


def tributary_area_ft2(spacing_in: float, coverage_in: float) -> float:
    return (spacing_in / 12.0) * (coverage_in / 12.0)
