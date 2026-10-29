"""Wall drain columns and the over-dig (resolve/wall_column.py, resolve/excavation*.py).

The catlin numbers are oracled against houses/catlin/notes/foundation_aggregate_and_backfill.md.
"""

from __future__ import annotations

import itertools

import pytest
from _helpers import CATLIN
from shapely.geometry import Point, Polygon, box

from typehaus.resolve.excavation_slices import Hole, levels, slice_hole
from typehaus.takeoff.excavation import excavation_takeoff

#: The hand note's totals (§6), and how close a modelled number must land.
HAND = {"drain-column-stone": (51.9, 0.02), "drain-column-geotextile": (1455.0, 0.03),
        "cut": (1230.4, 0.05), "backfill": (528.0, 0.10), "cap": (100.7, 0.15),
        "haul-off": (717.2, 0.10)}


def _columns(model):
    return [s for s in model.solids if s.category == "drain_column"]


def test_columns_close_corners_never_double_and_stay_out_of_the_beds(catlin_model_ro):
    columns = _columns(catlin_model_ro)
    assert columns
    for a, b in itertools.combinations(columns, 2):
        if min(a.z1_m, b.z1_m) - max(a.z0_m, b.z0_m) > 1e-6:
            assert Polygon(a.outline).intersection(Polygon(b.outline)).area < 1e-4, (a.tag, b.tag)
    for column, bed in itertools.product(columns, catlin_model_ro.footing_beddings):
        if min(column.z1_m, bed.z1_m) - max(column.z0_m, bed.stone_z0_m) > 1e-6:
            overlap = Polygon(column.outline).intersection(Polygon(bed.outline)).area
            assert overlap < 1e-4, (column.tag, bed.tag)  # m2: rounding slivers only
    # The house's outside corners are stone: a point just off each one, diagonally.
    house = [c for c in columns if c.tag.startswith("FB-B-")]
    x0 = min(x for c in house for x, _ in c.outline)
    x1 = max(x for c in house for x, _ in c.outline)
    y1 = max(y for c in house for _, y in c.outline)
    for corner in ((x0 + 0.05, y1 - 0.05), (x1 - 0.05, y1 - 0.05)):
        assert any(Polygon(c.outline).contains(Point(corner)) for c in house), corner


@pytest.mark.parametrize("h_per_v, expected_cut, expected_cap",
                         [(0.0, 300.0 + 3 * 26.0, 0.5 * 26.0), (1.0, 300.0 + 204.0, 55.667)])
def test_a_hand_rectangle_digs_what_the_formula_says(h_per_v, expected_cut, expected_cap):
    """A 10 m square house with a 1 m x 10 m bed off its east face, 3 m deep, 1 m working
    space. The dig outside the house at reach r is (1+2r)(10+2r) - 10r = 10 + 12r + 4r^2,
    which is 26 m2 at r = 1 and integrates to 204 m3 over r = 1..4 (55.667 over the top
    0.5 m, r = 3.5..4, the cap)."""
    outline = box(0, 0, 10, 10)
    hole = Hole(outline, [(box(10, 0, 11, 10), 0.0, 3.0, True)], [(outline, 0.0)], [],
                grade=3.0, z_struct=0.0, working_space=1.0, h_per_v=h_per_v, cap=0.5)
    cut, fill, cap, prisms = slice_hole(hole, levels(0.0, 3.0, 0.05, []))
    assert cut == pytest.approx(expected_cut, rel=1e-3)
    assert fill == pytest.approx(expected_cut - 300.0, rel=1e-3)
    assert cap == pytest.approx(expected_cap, rel=1e-3)
    assert {category for category, *_ in prisms} == {"backfill_native", "backfill_cap"}


def test_takeoff_matches_the_hand_note_and_the_allowances_are_gone(catlin_model_ro):
    rows = {row["item"]: float(row["quantity"]) for row in excavation_takeoff(catlin_model_ro)}
    for item, (hand, tolerance) in HAND.items():
        assert rows[item] == pytest.approx(hand, rel=tolerance), item
    prices = (CATLIN / "prices.toml").read_text()
    for retired in ("foundation-free-draining-backfill =",
                    "site-excavation-sunken-garden-drained-backfill ="):
        assert retired not in prices
