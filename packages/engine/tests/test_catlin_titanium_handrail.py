"""Catlin's owner-furnished titanium: ST-B2M's two rails and the range backsplash.

Oracle: ``houses/catlin/notes/titanium_handrail_backsplash.md`` — §1's cut plan, §4's
R301.5 hand-calc and §5's backsplash datum are reproduced here.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from typehaus.checks.code.mn_residential.handrail_clearance import rail_samples, top_rail_path
from typehaus.checks.code.mn_residential.handrail_hardware import support_stations
from typehaus.takeoff.railings import railing_takeoff

_IN = 0.0254
_RAILS = ("RL-M-HANDRAIL-E", "RL-M-HANDRAIL-W")
_NOTE = (Path(__file__).resolve().parents[3] / "houses" / "catlin" / "notes"
         / "titanium_handrail_backsplash.md")


def _parts(model, tag):
    return sorted(s.tag[len(tag) + 1:] for s in model.solids if s.tag.startswith(f"{tag}-"))


@pytest.mark.parametrize("tag", _RAILS)
def test_each_basement_rail_returns_at_both_ends_on_one_mid_bracket(catlin_model_ro, tag):
    rail = catlin_model_ro.plan.by_tag(tag)
    assert rail.type_ref == "RAILING-INT-TI-HANDRAIL-42"
    assert (rail.start_termination, rail.end_termination) == ("wall_return", "wall_return")
    parts = _parts(catlin_model_ro, tag)
    assert [p for p in parts if not p.startswith("RAIL")] == [
        "BRACKET2", "ENDPLATE1", "ENDPLATE2", "RETURN1", "RETURN2"]


@pytest.mark.parametrize("tag", _RAILS)
def test_each_basement_rail_clears_its_wall_and_spans_under_a_metre(catlin_ctx, tag):
    rail = catlin_ctx.plan.by_tag(tag)
    beside = [s.to_face_m for s in rail_samples(catlin_ctx, rail) if s.to_face_m]
    assert beside
    assert min(beside) - 0.021 >= 1.5 * _IN          # R311.7.8.2
    assert max(beside) + 0.021 <= 4.5 * _IN          # R311.7.1
    stations, stubs = support_stations(catlin_ctx, rail, top_rail_path(catlin_ctx, rail))
    assert stubs == 0 and len(stations) == 3
    spans = [b - a for a, b in zip(stations, stations[1:], strict=False)]
    assert max(spans) <= 1.0                         # bracket_spacing_max, note §4
    # Note §1: two pieces of 1200 mm stock per rail cover the developed length.
    assert 1.2 < stations[-1] <= 2.4


def test_the_takeoff_counts_the_fittings_and_the_stock(catlin_model_ro):
    (row,) = [r for r in railing_takeoff(catlin_model_ro)
              if r["type"] == "RAILING-INT-TI-HANDRAIL-42"]
    assert sorted(row["tags"]) == list(_RAILS)
    assert (row["bracket_count"], row["return_count"]) == (2, 4)
    assert (row["stock_count"], row["splice_count"]) == (4, 2)


def test_the_note_r301_5_hand_calc():
    """§4: a 200 lb point load at midspan of a 1000 mm simple span of 42 x 2.5 tube."""
    d_out, d_in = 42.0, 37.0
    inertia = math.pi * (d_out ** 4 - d_in ** 4) / 64.0
    modulus = inertia / (d_out / 2.0)
    load = 200 * 4.448
    stress = load * 1000.0 / 4.0 / modulus
    deflection = load * 1000.0 ** 3 / (48 * 105_000 * inertia)
    assert inertia == pytest.approx(60_746, rel=1e-4)
    assert modulus == pytest.approx(2_893, rel=1e-3)
    assert stress == pytest.approx(76.9, abs=0.05)
    assert stress / 275 == pytest.approx(0.28, abs=0.005)
    assert deflection == pytest.approx(2.9, abs=0.05)
    text = _NOTE.read_text()
    for printed in ("60,746", "2,893", "**76.9 MPa**", "**0.28**", "2.9 mm"):
        assert printed in text, printed


def test_the_backsplash_is_two_uncut_sheets_behind_the_range(catlin_model_ro):
    (band,) = [p for p in catlin_model_ro.panelings if p.tag == "WP-M-KIT-BACKSPLASH"]
    assert band.thickness_m == pytest.approx(0.0008, abs=1e-9)
    assert band.run_m == pytest.approx(1.0, abs=1e-6)            # two 1000 mm sheets wide
    assert band.band_z1_m - band.band_z0_m == pytest.approx(1.0, abs=1e-6)  # two 500 tall
    assert band.area_m2 * 10.7639 == pytest.approx(10.76, abs=0.01)
    ys = [y for _x, y in band.outline]
    assert (min(ys) + max(ys)) / 2.0 == pytest.approx(372.375 * _IN, abs=1e-4)  # range
    # The 36" counter over the +15/16" finished floor; W-M-E1's base is the storey datum.
    assert band.band_z0_m == pytest.approx(36.9375 * _IN, abs=1e-6)
