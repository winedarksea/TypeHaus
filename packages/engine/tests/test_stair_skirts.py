"""ST-M2S's skirt boards against houses/catlin/notes/stair_skirt_basis.md §3–§6."""

from __future__ import annotations

import pytest

IN = 0.0254


@pytest.fixture(scope="module")
def stair(catlin_model_ro):
    return next(s for s in catlin_model_ro.stairs if s.tag == "ST-M2S")


def test_treads_and_risers_butt_the_skirts(stair) -> None:
    """§4: each board's back is scribed to its wall's finish face, not the lane edge."""
    boards = [m for m in stair.members if m.category in ("tread", "riser")]
    assert len(boards) == 30
    lengths = {(m.child_key.split("-")[1], round(m.length_m / IN, 4)) for m in boards}
    assert lengths == {("lower", 41.0625), ("upper", 41.0625)}
    skirts = {m.child_key: m.p0[0] / IN for m in stair.members if m.category == "stair_skirt"}
    # Board centres 3/8" off W-M-STRW, W-M-WELL (both faces) and W-M-C5's paint.
    assert skirts == pytest.approx({"skirt-upper-right": 123.5, "skirt-upper-left": 165.3125,
                                    "skirt-lower-left": 170.5625, "skirt-lower-right": 212.375})


def test_four_skirts_with_the_note_s_reveal_toe_and_blanks(stair) -> None:
    skirts = {m.child_key: m for m in stair.members if m.category == "stair_skirt"}
    assert set(skirts) == {"skirt-lower-left", "skirt-lower-right",
                           "skirt-upper-left", "skirt-upper-right"}
    assert {k: round(m.cut_length_m / IN, 3) for k, m in skirts.items()} == {
        "skirt-lower-left": 95.821, "skirt-lower-right": 98.657,
        "skirt-upper-left": 92.140, "skirt-upper-right": 103.470}
    floor = stair.base_elevation_m
    # §3: 13.586" over the floor at the first riser face; level foot to +0.664".
    profile = skirts["skirt-lower-left"].elevation_profile
    assert max(z for s, z in profile if abs(s) < 1e-9) - floor == pytest.approx(13.586 * IN,
                                                                                 abs=1e-4)
    assert max(s for s, z in profile if abs(z - floor) < 1e-6) == pytest.approx(0.664 * IN,
                                                                                abs=1e-4)
    # §3: the toe drops to the 3 1/2" base 13.386" before the upper flight's first riser.
    upper = skirts["skirt-upper-right"]
    assert (upper.p0[1] / IN) - 383.125 == pytest.approx(13.386, abs=1e-3)
    toe = [z for s, z in upper.elevation_profile if abs(s) < 1e-9]
    assert max(toe) - min(toe) == pytest.approx(3.5 * IN, abs=1e-6)


def test_the_landing_takes_base_at_its_own_floor(catlin_model_ro) -> None:
    runs = {r.wall_tag: r for r in catlin_model_ro.base_runs
            if r.tag.startswith("BASE-ST-M2S-LANDING-")}
    assert {k: round(r.length_m / IN, 3) for k, r in runs.items()} == {
        "W-M-C5": 13.875, "W-M-C5B": 28.5, "W-M-N2": 88.875, "W-M-STRW": 28.239}
    assert all(r.piece.z0_m / IN == pytest.approx(61.2234, abs=1e-4) for r in runs.values())
    assert sum(r.end_corner == "inside" for r in runs.values()) == 2
