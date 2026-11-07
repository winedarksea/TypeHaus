"""908.2 group order and the wet-vent walk, against `mep_group_wet_vent_basis.md`.

§4/§5 give the roles and sizes; §2's synthetic ladder is the walk the check reads (F1, and the
strict vertical-child reading that leaves option X to the AHJ)."""

from __future__ import annotations

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_trap_arm import developed_arm
from typehaus.routing.group_order import Member, group_order

IN = M_PER_IN


def _member(tag, symbol, dfu, floor, x, y, tie):
    return Member(tag, symbol, dfu, floor, (abs(x - tie[0]) + abs(y - tie[1])) * IN)


def test_bath2_lays_the_shower_dry_the_tub_wet_and_the_wc_last() -> None:
    """§4 option S: drain points and the main tie (72, 271) as authored."""
    tie = (72.0, 271.0)
    order = group_order([
        _member("WC", "toilet", 3, False, 30.0, 252.74, tie),
        _member("TUB", "kohler-underscore-6032", 2, True, 78.49, 215.18, tie),
        _member("SH", "shower", 2, True, 76.62, 179.0, tie),
        _member("LAV", "vanity", 1, False, 12.0, 182.38, tie)])
    assert order.laying == ("SH", "TUB", "WC") and order.own_vent == ("LAV",)
    assert order.upstream == () and order.dfu == 7 and order.wet_vent_in == 3.0
    # WC to the head 60.26" (§4.3).
    assert abs(30.0 - 72.0) + abs(252.74 - 271.0) == pytest.approx(60.26)


def test_suite_lays_option_y_the_tub_dry_the_lav_on_its_own_vent() -> None:
    """§5: tub, lav, WC in a row flowing west to the stack at (150, 216). Option X (the lav
    dry-venting the tub) is an owner/AHJ question, so the default is Y: 5 DFU, 3"."""
    tie = (150.0, 216.0)
    order = group_order([_member("WC", "toilet", 3, False, 134.81, 252.41, tie),
                         _member("LAV", "drawer-vanity", 1, False, 165.5, 264.75, tie),
                         _member("TUBSH", "tub-shower", 2, True, 197.62, 261.12, tie)])
    assert (order.dry, order.wet, order.last, order.own_vent) == (
        "TUBSH", (), ("WC",), ("LAV",))
    assert (order.dfu, order.wet_vent_in) == (5, 3.0)


def _ladder(lav_rise_in: float):
    """§2: collector C (3") flowing +x; the tub arm T joins at x=0, the lav L (dry vent at
    its top) at x=36", the WC arm W at x=72"."""
    drains = {"C": [(0.0, 0.0, 0.0), (100 * IN, 0.0, 0.0)],
              "T": [(0.0, 40.3 * IN, 0.0), (0.0, 0.0, 0.0)],
              "L": [(36 * IN, 3 * IN, lav_rise_in * IN), (36 * IN, 0.0, 0.0)],
              "W": [(72 * IN, 20 * IN, 0.0), (72 * IN, 0.0, 0.0)]}
    radii = {"C": 1.5 * IN, "T": 0.75 * IN, "L": 1.5 * IN, "W": 1.5 * IN}
    fx = {"T": ("T", 2.0, "tub", "s"), "L": ("L", 1.0, "lavatory", "s"),
          "W": ("W", 3.0, "toilet", "s")}
    vent = [drains["L"][0]]
    return lambda tag: developed_arm(tag, drains, radii, vent, (fx, tag))


def test_the_wc_downstream_of_the_dry_vent_ends_at_its_own_entry() -> None:
    walk = _ladder(0.0)
    arm, what, _gap, _notes = walk("T")
    assert arm / IN == pytest.approx(76.3) and "908.2 horizontal, 6 DFU" in what
    arm, what, _gap, _notes = walk("W")  # F1: None before
    assert arm / IN == pytest.approx(20.0) and "downstream of its dry vent" in what


def test_a_dry_vented_lav_dropping_to_the_branch_is_graded_908_1_vertical() -> None:
    """Option X's lav drop rises 25.58" over 3" of plan: the strict reading grades it as a
    908.1 vertical wet vent the tub does not discharge into, so the tub is not vented."""
    arm, _what, _gap, notes = _ladder(25.58)("T")
    assert arm is None and any("908.1 vertical" in n for n in notes)
