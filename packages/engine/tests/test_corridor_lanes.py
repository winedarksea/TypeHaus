"""Tiers and lanes — where in an occupied channel a router may actually go.

``corridors.floor_corridors`` offered one corridor per bay, on its CENTRELINE, with what
was already in it subtracted from the width. That is the right answer to "is there room"
and the wrong answer to "where": a 12 1/2" truss bay holding one 4" duct has 8 1/2" left
and none of it is on the centreline. Same shape of error in z — the midpoint of an 8 7/8"
web window is very often the plane the occupant is on.

Oracle: ``houses/catlin/notes/mep_duct_routing_basis.md`` §3.
"""

from __future__ import annotations

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.routing.corridor_lanes import _median_station, _widest_free
from typehaus.routing.corridors import Corridor
from typehaus.routing.graph import _corridor_levels


class _Space:
    def __init__(self, radius_m: float, clearance_m: float) -> None:
        self.radius_m = radius_m
        self.clearance_m = clearance_m


def _bay(clear_in: float, *, occupied_z: float | None = None, occupants=()):
    return Corridor(tag="FS-X:bay@1.0", kind="bay", axis="x", station=1.0,
                    z0_m=0.0, z1_m=8.875 * M_PER_IN,
                    clear_width_m=clear_in * M_PER_IN, lo_m=0.0, hi_m=10.0,
                    occupied_z=occupied_z, occupants=occupants)


# --- tiers ------------------------------------------------------------------------------


def test_an_EMPTY_channel_offers_one_plane() -> None:
    """There is no reason to prefer high or low in a bay with nothing in it, and one plane
    is thirty times cheaper than several."""
    corridor = _bay(12.5)
    window = corridor.z_window(2 * M_PER_IN)
    levels = _corridor_levels(corridor, window, _Space(2 * M_PER_IN, 0.5 * M_PER_IN))
    assert levels == [(window[0] + window[1]) / 2.0]


def test_an_OCCUPIED_channel_offers_its_two_tiers() -> None:
    """The note's §3 case: an 8 7/8" web window takes two 4" ducts stacked with 7/8" to
    spare, and the router could nominate neither of them — the only plane it offered was
    the midpoint, which is where the occupant is."""
    corridor = _bay(12.5, occupied_z=4.4 * M_PER_IN, occupants=("DU-OTHER",))
    radius, clearance = 2 * M_PER_IN, 0.5 * M_PER_IN
    window = corridor.z_window(radius)
    levels = _corridor_levels(corridor, window, _Space(radius, clearance))
    assert levels == [window[0], window[1]]
    # The note's numbers, with this corridor's floor at 0: an 8 7/8" window and a 4" duct
    # give tiers at 2" and 6 7/8", 4 7/8" apart — two 4" ducts with 7/8" to spare. On
    # FS-S-WEST's real 109 5/8" .. 118 1/2" that is 111 5/8" and 116 1/2".
    assert [round(z / M_PER_IN, 4) for z in levels] == [2.0, 6.875]
    assert round((levels[1] - levels[0]) / M_PER_IN, 4) == 4.875


def test_a_window_that_cannot_hold_TWO_falls_back_to_the_midpoint() -> None:
    """Offering two tiers that do not both fit would be proposing a stack nobody can
    build. A 6" duct in the same 8 7/8" window leaves its two extremes 2 7/8" apart and it
    is 6" wide, so there is one tier and the midpoint is it."""
    corridor = _bay(12.5, occupied_z=4.4 * M_PER_IN, occupants=("DU-OTHER",))
    radius, clearance = 3 * M_PER_IN, 0.5 * M_PER_IN
    window = corridor.z_window(radius)
    levels = _corridor_levels(corridor, window, _Space(radius, clearance))
    assert levels == [(window[0] + window[1]) / 2.0]


# --- lanes ------------------------------------------------------------------------------


def test_the_widest_free_lane_is_the_one_offered() -> None:
    """A 12 1/2" bay whose 4" occupant sits from 0 to +4: that leaves 6.25" below it and
    2.25" above, and the lane offered is the 6.25"."""
    assert _widest_free(-6.25, 6.25, [(0.0, 4.0)], 4.0) == (-6.25, 0.0)


def test_a_lane_narrower_than_the_target_is_not_offered() -> None:
    """The free interval is not the bay's width, and pricing it as the bay's would propose
    two ducts in one lane. A 4" occupant dead centre leaves 4.25" either side: room for a
    4" duct and not for a 6" one."""
    assert _widest_free(-6.25, 6.25, [(-2.0, 2.0)], 6.0) is None
    # A tie, and it goes to the lower station — deterministic beats arbitrary.
    assert _widest_free(-6.25, 6.25, [(-2.0, 2.0)], 4.0) == (-6.25, -2.0)


def test_an_occupants_station_is_its_MEDIAN_in_the_bay() -> None:
    """A run that jogs into the bay and back has two stations, and the mean is the one
    place it is not."""
    path = [(0.0, 10.0), (1.0, 10.0), (2.0, 14.0), (3.0, 10.0)]
    # Bay centred on y = 10 with a 6-wide clear: the point at y=14 is outside it.
    assert _median_station(path, cross=1, bay_station=10.0, clear_m=6.0) == 10.0
    # Nothing of this run is in a bay eight units away.
    assert _median_station(path, cross=1, bay_station=30.0, clear_m=6.0) is None


def test_catlin_offers_a_second_lane_in_its_occupied_truss_bays(catlin_model_ro) -> None:
    """The capability, on the real house: FS-S-WEST's bays hold the level-2 radial bank,
    and a lane derived by subtraction is a station something else has not claimed."""
    from typehaus.routing.corridor_lanes import lane_corridors
    from typehaus.routing.corridors import floor_corridors

    bays = floor_corridors(catlin_model_ro)
    lanes = lane_corridors(catlin_model_ro, bays, radius_m=2 * M_PER_IN)
    assert lanes, "some occupied bay in catlin has a free lane off its centreline"
    for lane in lanes:
        assert lane.kind == "bay" and lane.tag.count(":bay@") == 1
        assert lane.clear_width_m > 0
        assert any(abs(lane.station - bay.station) > 1e-6 for bay in bays
                   if bay.tag.split(":bay@")[0] == lane.tag.split(":bay@")[0])
        assert any("derived by SUBTRACTION" in gap for gap in lane.gaps)


def test_a_proposal_names_the_lane_and_the_tier_it_rode() -> None:
    """A proposal a reader has to reverse-engineer a station from is one nobody pastes."""
    from typehaus.routing.trades.duct import bay_occupancy_note

    empty = bay_occupancy_note(_bay(12.5), 2 * M_PER_IN)
    assert empty is None

    shared = bay_occupancy_note(
        _bay(8.5, occupied_z=4.4 * M_PER_IN, occupants=("DU-OTHER",)), 2 * M_PER_IN)
    assert "station 39.37\"" in shared
    assert "already held at the tightest tier (4.40\") by DU-OTHER" in shared

    tight = bay_occupancy_note(
        _bay(4.0, occupied_z=4.4 * M_PER_IN, occupants=("DU-OTHER",)), 2 * M_PER_IN)
    assert "cannot place two lanes side by side" in tight


def test_the_lattice_cap_was_raised_rather_than_the_tiers_dropped() -> None:
    """The plan's rule, pinned: the cap exists to stop a lattice nobody can search, and
    dropping the tiers to fit under it would have bought a router that refuses a bay a
    fitter would use. Catlin's worst duct: 123,248 -> 203,518, and the constant's own
    comment carries the three rows and the bug the middle one hid."""
    from typehaus.routing.space import MAX_LATTICE_NODES

    assert MAX_LATTICE_NODES == 250_000
