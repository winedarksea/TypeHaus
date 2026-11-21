"""``LayerMaterial.extent`` — abuse-resistant gypsum on the lower 4' only (catlin interiors).

The swap splits the target layer into two slot-mates (AR below, the assembly's own board
above); the board's consumers must see one board in two bands, not two boards.
"""

from __future__ import annotations

import pytest

from typehaus.quantities import inch


def test_a_split_face_resolves_to_two_banded_slot_mates(catlin_model_ro):
    wall = catlin_model_ro.wall("W-M-C2")  # gwb-b: AR to 48 3/4" over the 3/4" subfloor
    lower = next(ly for ly in wall.layers if ly.name == "gwb-b")
    upper = next(ly for ly in wall.layers if ly.name == "gwb-b-upper")
    assert (lower.material_ref, upper.material_ref) == ("gwb-ar", "gwb")
    assert lower.slot == upper.slot == "gwb-b-split"
    assert lower.thickness_m == pytest.approx(upper.thickness_m)
    assert lower.band(wall)[1] == pytest.approx(wall.z0_m + inch(48.75).meters)
    assert upper.z0_m == pytest.approx(lower.band(wall)[1])
    # One row of the stack: the pair is one depth, not two boards.
    assert sum(ly.slot == "gwb-b-split" for ly in wall.depth_layers()) == 1


def test_a_free_end_bills_both_boards_over_their_own_bands(catlin_model_ro):
    ends = [e for e in catlin_model_ro.wall_ends
            if e.wall == "W-M-WELL" and e.node == "N-M-WELL-S"]
    height = {e.material_ref: e.height_m for e in ends}
    assert set(height) == {"gwb-ar", "gwb"}
    assert height["gwb-ar"] == pytest.approx(inch(48).meters)  # on the stair, no subfloor
    assert height["gwb"] > 0
