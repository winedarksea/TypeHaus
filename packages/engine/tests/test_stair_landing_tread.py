"""ST-M2S's landing: a 3/4" + 3/4" floor stack whose landing tread lips down to tread depth."""

import pytest

from typehaus.quantities import inch
from typehaus.server.model_json_fabric import framing_json


def _stair(model):
    return next(stair for stair in model.stairs if stair.tag == "ST-M2S")


def _member(stair, key):
    return next(member for member in stair.members if member.child_key == key)


def test_the_landing_deck_is_the_floor_stack_and_its_framing_meets_it(catlin_model_ro):
    stair = _stair(catlin_model_ro)
    for name in ("lower", "upper"):
        deck = _member(stair, f"landing-{name}")
        assert deck.z1_m - deck.z0_m == pytest.approx(inch(1.5).meters)
        framing = [m for m in stair.members
                   if m.child_key.startswith((f"landing-joist-{name}-",
                                              f"landing-rim-{name}-"))]
        assert framing and all(m.z1_m == pytest.approx(deck.z0_m) for m in framing)
    tread = _member(stair, "tread-lower-000")
    assert tread.z1_m - tread.z0_m == pytest.approx(inch(1.75).meters)


def test_only_an_arrival_edge_carries_a_lip_over_its_riser(catlin_model_ro):
    stair = _stair(catlin_model_ro)
    lips = {part.key: part for part in stair.finish_parts if part.role == "landing-nosing"}
    assert set(lips) == {"landing-lower:nosing", "stairhead:nosing"}
    lip = lips["landing-lower:nosing"]
    assert lip.material_ref == "oak-tread"
    deck = _member(stair, "landing-lower")
    # Tread depth down from the walking face: the riser below tops out at its underside.
    assert lip.z1_m == pytest.approx(deck.z1_m)
    assert lip.z1_m - lip.z0_m == pytest.approx(inch(1.75).meters)
    head = next(m for m in stair.members if m.category == "riser"
                and m.z1_m == pytest.approx(lip.z0_m))
    assert head.child_key.startswith("riser-lower-")
    # 3/4" riser + the flight's 1" nosing in front of the landing edge.
    xs = [x for x, _ in lip.outline]
    ys = [y for _, y in lip.outline]
    assert min(max(xs) - min(xs), max(ys) - min(ys)) == pytest.approx(inch(1.75).meters)


def test_the_lip_reaches_the_viewer(catlin_model_ro):
    stairs = framing_json(catlin_model_ro, None)["stairs"]
    stair = next(s for s in stairs if s["tag"] == "ST-M2S")
    assert [part["role"] for part in stair["finish_parts"]] == ["landing-nosing"] * 2
