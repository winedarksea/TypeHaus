"""Interior doors are stock prehungs cut on site to a 1/2"-3/4" undercut (owner, 2026-11-06).

The RO keeps its derived 81.51" over the finished floor; the slab is cut to hang at its
undercut, and the System 1 return figures are oracled against
``houses/catlin/notes/system1_return_path.md`` (Q = 1.07 A sqrt(dP)).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.model import DoorType, DoorUndercut
from typehaus.quantities import ft, inch
from typehaus.resolve.door_sizing import door_sizing

_IN = 0.0254
_RULE = DoorUndercut(hung=inch(0.5), minimum=inch(0.5), maximum=inch(0.75))


def _standard():
    return SimpleNamespace(jamb_allowance=inch(1), jamb_stock_depths=(), door_undercut=_RULE)


@pytest.mark.parametrize(("undercut", "cut_in"), [(None, 0.106), (inch(0.75), 0.356)])
def test_stock_slab_is_cut_to_its_undercut_and_the_ro_holds(undercut, cut_in):
    door_type = DoorType(tag="DT", width=ft(2, 6), height=ft(6, 8), undercut=undercut)
    sizing = door_sizing(SimpleNamespace(tag="D"), door_type, _standard(),
                         floor_finish_m=0.75 * _IN)
    assert (sizing.rough_h_m - sizing.floor_finish_m) / _IN == pytest.approx(81.512, abs=1e-3)
    assert sizing.leaf_cut_m / _IN == pytest.approx(cut_in, abs=1e-3)
    assert (sizing.leaf_h_m + sizing.leaf_cut_m) / _IN == pytest.approx(80.0)
    assert sizing.undercut_m == (undercut or _RULE.hung).meters


def test_undercut_rule_refuses_a_hung_gap_outside_its_range():
    with pytest.raises(ValueError):
        DoorUndercut(hung=inch(1.75), minimum=inch(0.5), maximum=inch(0.75))


def test_every_catlin_leaf_hangs_within_the_range(catlin_ctx):
    from typehaus.checks.advisory.door_undercut import door_undercut
    from typehaus.findings import Result

    findings = door_undercut(catlin_ctx)
    assert not [f.message for f in findings if f.result == Result.ADVISORY]
    by_door = {f.element_tags[0]: f for f in findings if f.element_tags}
    assert "hangs 0.75\"" in by_door["D-S-BED1"].message      # a relief door, at the top
    assert "hangs 0.50\"" in by_door["D-S-NCLOSET"].message   # the factory 1/2"


def test_bedroom_return_at_the_largest_allowed_undercut_matches_the_hand_note(catlin_ctx):
    """75 cfm net (80 supply less the ERV's 5) through 30" x 3/4" = 22.5 in2."""
    from typehaus.checks.mep.door_transfer_air import door_transfer_air
    from typehaus.findings import Result

    bed1 = next(f for f in door_transfer_air(catlin_ctx) if f.element_tags[0] == "RM-S-BED1")
    expected = (75 / (1.07 * 22.5)) ** 2
    assert bed1.result == Result.ADVISORY
    assert f"{expected:.1f} Pa" in bed1.message
