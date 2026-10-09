"""``DoorType.pocket_frame`` — a kit family moves the BOM and, where it publishes its own
rough opening, the framing. Eclisse is the case: RO 74 1/2" for a 36" leaf, not 73"."""

from __future__ import annotations

import pytest

from typehaus.hardware.catalog import pocket_frame_kit
from typehaus.quantities import ft, inch
from typehaus.resolve.framing.tables import pocket_run


@pytest.mark.parametrize(("family", "deep", "part"), [
    (None, False, "153068PF"),
    (None, True, "15603068"),
    ("eclisse", False, "EKC3680"),
    ("eclisse", True, None),  # the EKQ 80" kit has no retail listing to cite
])
def test_family_and_wall_depth_pick_the_kit(family, deep, part):
    kit = pocket_frame_kit(family, 36, deep)
    assert kit.part_number_by_length_in.get(36) == part
    assert ("ECLISSE" in kit.model) == (family == "eclisse")


def test_an_unknown_family_raises_rather_than_billing_nothing():
    with pytest.raises(LookupError):
        pocket_frame_kit("hafele", 36, False)


def test_commodity_ladder_keeps_its_2x4_kit_off_the_36_inch_leaf_in_a_deep_wall():
    assert pocket_frame_kit(None, 30, True).model == "POCKET-FRAME-1500PF"


def test_eclisse_rough_opening_is_its_published_table():
    """Tech sheet 11/2022: R.O. = F.S. + 1/2", F.S. = 74" at 36"."""
    for deep in (False, True):
        ro = pocket_frame_kit("eclisse", 36, deep).rough_opening_in_by_length_in[36]
        assert (ft(3) + pocket_run(ft(3), inch(ro))).inches == pytest.approx(74.5)


def test_catlin_pockets_frame_at_the_eclisse_rough_opening(catlin_model_ro):
    pockets = {op.tag: op for op in catlin_model_ro.openings if op.pocket_run_m}
    assert set(pockets) == {"D-M-LAUN", "D-B-BATH"}
    for op in pockets.values():
        assert (op.width_m + op.pocket_run_m) / inch(1).meters == pytest.approx(74.5)


def test_split_studs_are_drawn_but_not_billed_as_lumber(catlin_model_ro):
    from typehaus.takeoff.framing import framing_takeoff

    splits = [m for wall in catlin_model_ro.walls for m in wall.members
              if m.child_key.startswith("pocketsplit-")]
    assert splits and all(m.supplied_by == "pocket_door_frame_kit" for m in splits)
    profiles = {row["profile"] for row in framing_takeoff(catlin_model_ro)}
    assert not profiles & {"2-1x4", "2-1x6"}
