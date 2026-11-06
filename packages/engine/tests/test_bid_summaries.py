"""A trade summary regroups quantities the model already derives: each one adds back to the
takeoff it restates, so a sub pricing the summary and one pricing the BOM price one job."""

from __future__ import annotations

import pytest

from typehaus.resolve.fixture_units import HOST_COUNTED_SYMBOLS, WSFU_BY_SYMBOL
from typehaus.resolve.plumbing_tables import DFU_BY_SYMBOL, FIXTURE_CLASS_BY_SYMBOL
from typehaus.takeoff.bid_summaries import SummaryInputs, build_summaries
from typehaus.takeoff.electrical import electrical_device_takeoff
from typehaus.takeoff.envelope import envelope_layer_takeoff
from typehaus.takeoff.finishes import floor_finish_rows


@pytest.fixture(scope="module")
def summaries(catlin_model):
    return build_summaries(SummaryInputs(catlin_model, {}))


def _table(summaries, trade: str, slug: str):
    return next(t for t in summaries[trade].tables if t.slug == slug)


def _total(table, column: str) -> float:
    index = table.columns.index(column)
    return sum(float(row[index]) for row in table.rows if row[0] != "Total")


def test_every_fixture_symbol_has_a_class() -> None:
    assert set(DFU_BY_SYMBOL) | set(WSFU_BY_SYMBOL) | HOST_COUNTED_SYMBOLS <= set(
        FIXTURE_CLASS_BY_SYMBOL)


def test_every_typed_opening_is_on_one_schedule(catlin_model, summaries) -> None:
    doors = {t.tag: t for t in catlin_model.plan.library.door_types}
    windows = {t.tag for t in catlin_model.plan.library.window_types}
    typed = {o.tag for o in catlin_model.openings
             if (doors.get(o.type_ref) if o.is_door else o.type_ref in windows)}
    listed = [row[1] for slug in ("windows-exterior-doors", "interior-doors")
              for row in _table(summaries, "openings", slug).rows]
    assert sorted(listed) == sorted(typed)


def test_roof_wall_and_board_splits_add_back_to_the_envelope(summaries, catlin_model) -> None:
    rows = envelope_layer_takeoff(catlin_model)
    roof = sum(r["net_area_sqft"] for r in rows
               if r["scope"] == "roof" and r["function"] == "cladding")
    assert _total(_table(summaries, "roofing", "roof-geometry"), "Sloped SF") == pytest.approx(
        roof, abs=0.5)
    cladding = sum(r["net_area_sqft"] for r in rows
                   if r["scope"].endswith("wall") and r["function"] == "cladding")
    assert _total(_table(summaries, "siding", "elevations"), "Net SF") == pytest.approx(
        cladding, abs=1.0)
    gypsum = {m.tag for m in catlin_model.plan.library.materials if m.gypsum_type}
    walls = sum(r["net_area_sqft"] for r in rows
                if r["scope"].endswith("wall") and r["material"] in gypsum)
    board = _table(summaries, "drywall", "board")
    assert sum(float(row[4]) for row in board.rows if row[1] == "walls") == pytest.approx(
        walls, abs=1.0)


def test_room_finishes_add_back_to_the_floor_finish_rows(summaries, catlin_model) -> None:
    net = sum(float(r["net_area_sqft"]) for r in floor_finish_rows(catlin_model)
              if not r.get("under") and r.get("known", True))
    assert _total(_table(summaries, "flooring", "room-finishes"), "Net SF") == pytest.approx(
        net, abs=1.0)


def test_fixture_and_device_counts_match_their_takeoffs(summaries, catlin_model) -> None:
    fixtures = _table(summaries, "plumbing", "fixtures")
    assert _total(_table(summaries, "plumbing", "fixture-count"), "Count") == len(fixtures.rows)
    devices = sum(int(r["count"]) for r in electrical_device_takeoff(catlin_model)
                  if r["kind"] != "light")
    assert _total(_table(summaries, "electrical", "device-count"), "Total") == devices

