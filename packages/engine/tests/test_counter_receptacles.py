"""NEC 210.52(C)(1): no point of a counter wall space more than 24" from a receptacle in it."""

import pytest

from typehaus.checks.mep.electrical_counters import obstructed_gaps, space_gaps

IN = 0.0254


def _in(gaps):
    return [(round(lo / IN, 3), round(hi / IN, 3)) for lo, hi in gaps]


def test_a_48_inch_space_with_a_centred_receptacle_passes():
    # 24" each way reaches both ends exactly: no gap.
    assert space_gaps([(0, 48 * IN)], [24 * IN]) == []


def test_a_60_inch_space_with_a_centred_receptacle_misses_6_inches_each_end():
    # Hand-worked: 30" +/- 24" covers 6"..54", leaving 0..6" and 54..60".
    assert _in(space_gaps([(0, 60 * IN)], [30 * IN])) == pytest.approx([(0, 6), (54, 60)])


def test_a_receptacle_serves_only_the_space_it_stands_in_and_under_12_inches_is_exempt():
    # Sink break at 40": the receptacle at 20" does not reach the 52..90" space (38" long,
    # needs one), and the 11" sliver at 40..51" owes nothing.
    gaps = space_gaps([(0, 40 * IN), (40 * IN, 51 * IN), (52 * IN, 90 * IN)], [20 * IN])
    assert _in(gaps) == pytest.approx([(52, 90)])


def test_glass_at_the_counter_needs_the_count_and_an_outlet_beside_each_edge():
    # 115" space, glass 28"..91" (63" RO). Hand-worked: ceil(115 / 48) = 3 outlets. Outlets at
    # 22" and 98" sit 6" and 7" from the glass edges and cover 0..46 and 74..122, so nothing
    # outside the glass is past 24".
    space, glass = (0, 115 * IN), [(28 * IN, 91 * IN)]
    gaps, lacks = obstructed_gaps(space, glass, [8 * IN, 22 * IN, 98 * IN])
    assert gaps == [] and lacks == []
    # Without the third outlet the reach is fine but the count is short: 2 < 3.
    gaps, lacks = obstructed_gaps(space, glass, [22 * IN, 98 * IN])
    assert gaps == [] and len(lacks) == 1 and "3 needed" in lacks[0]
    # Count met but nothing beside the north edge: 91..103 holds no outlet.
    _, lacks = obstructed_gaps(space, glass, [4 * IN, 8 * IN, 22 * IN, 114 * IN])
    assert lacks == ['no outlet on the wall within 12" after the glass']
