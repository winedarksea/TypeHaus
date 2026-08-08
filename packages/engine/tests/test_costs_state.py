"""Cost tracking state (takeoff/costs.py): the durable record of what was actually bought.

Round-trip persistence, loud rejection of malformed files, the three ops, staleness
against a real catlin BOM, and the (section, key) join contract with ESTIMATE_PLANS —
which is the whole design: a paid check-off must point at the same row the estimate
prices, or the two views drift apart silently.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.cli.prices import ESTIMATE_PLANS, PriceRange, _SECTIONS
from typehaus.takeoff.bom import bill_of_materials
from typehaus.takeoff.costs import (COSTS_FILENAME, CostEntry, CostsState, ExtraItem,
                                    apply_costs_op, costs_payload, load_costs, write_costs)


@pytest.fixture(scope="module")
def bom(catlin_model):
    return bill_of_materials(catlin_model)


# --- the join contract ---------------------------------------------------------------------

def test_every_estimate_plan_joins_a_real_bom_section(bom):
    """ESTIMATE_PLANS is authored once and read by estimate_costs AND costs_payload; a plan
    whose bom_key names nothing would make every entry under it permanently stale."""
    for name, bom_key, key_field, quantity_field, _unit in ESTIMATE_PLANS:
        assert name in _SECTIONS, name
        assert bom_key in bom, f"{name} joins missing BOM section {bom_key!r}"
        rows = bom[bom_key]
        assert isinstance(rows, list)
        for row in rows:
            assert key_field in row, f"{bom_key} rows lack join field {key_field!r}"
    # And every price section has exactly one plan — the reverse direction.
    assert {name for name, *_ in ESTIMATE_PLANS} == set(_SECTIONS)


# --- load / write round trip ---------------------------------------------------------------

def test_absent_file_is_an_empty_state(tmp_path: Path):
    state = load_costs(tmp_path)
    assert state.entries == {} and state.extra == ()


def test_write_then_load_round_trips(tmp_path: Path):
    state = CostsState(
        entries={
            "framing": {"2x6": CostEntry(paid=True, paid_date="2026-08-01",
                                         product="Menards SPF #2", actual_cost=3184.50)},
            "hardware": {"LUS210": CostEntry(note="waiting on quote")},
        },
        extra=(
            ExtraItem(id="dumpster", name="Dumpster rental",
                      cost=PriceRange(450.0, 450.0), paid=True, category="sitework"),
            ExtraItem(id="permit-fee", name="Building permit",
                      cost=PriceRange(1800.0, 2400.0)),
        ),
    )
    write_costs(tmp_path, state)
    loaded = load_costs(tmp_path)
    assert loaded == state
    # Deterministic: writing what was loaded reproduces the file byte for byte.
    text = (tmp_path / COSTS_FILENAME).read_text()
    write_costs(tmp_path, loaded)
    assert (tmp_path / COSTS_FILENAME).read_text() == text


def test_keys_with_toml_hostile_characters_survive(tmp_path: Path):
    """BOM keys carry quotes and spaces (`5.5" x 1"` edge-trim profiles, part numbers)."""
    state = CostsState(entries={"placeables": {'wolf "range" 36': CostEntry(paid=True)}})
    write_costs(tmp_path, state)
    assert load_costs(tmp_path) == state


@pytest.mark.parametrize("body, message", [
    ("[entries.lumber.x]\npaid = true\n", "unknown entries section"),
    ("[entries.framing.x]\npayed = true\n", "unknown field"),
    ("[entries.framing.x]\nactual_cost = -3\n", "actual_cost"),
    ("[[extra]]\nname = \"no id\"\n", "required"),
    ("[[extra]]\nid = \"a\"\nname = \"x\"\ncost = { low = 2, high = 1 }\n", "low <= high"),
    ("[whatever]\n", "unknown top-level"),
])
def test_a_malformed_costs_file_errors_loudly(tmp_path: Path, body: str, message: str):
    (tmp_path / COSTS_FILENAME).write_text(body)
    with pytest.raises(ValueError) as error:
        load_costs(tmp_path)
    assert message in str(error.value)


def test_duplicate_extra_ids_are_rejected(tmp_path: Path):
    (tmp_path / COSTS_FILENAME).write_text(
        "[[extra]]\nid = \"a\"\nname = \"one\"\n[[extra]]\nid = \"a\"\nname = \"two\"\n")
    with pytest.raises(ValueError) as error:
        load_costs(tmp_path)
    assert "duplicate" in str(error.value)


# --- ops -----------------------------------------------------------------------------------

def test_set_entry_sets_and_clearing_every_field_deletes():
    state = apply_costs_op(CostsState(), {
        "op": "set_entry", "section": "framing", "key": "2x6",
        "entry": {"paid": True, "product": "SPF"}})
    assert state.entries["framing"]["2x6"].paid
    cleared = apply_costs_op(state, {
        "op": "set_entry", "section": "framing", "key": "2x6", "entry": {}})
    assert cleared.entries == {}


def test_set_entry_rejects_an_unknown_section():
    with pytest.raises(ValueError) as error:
        apply_costs_op(CostsState(), {"op": "set_entry", "section": "lumber",
                                      "key": "2x6", "entry": {"paid": True}})
    assert "unknown section" in str(error.value)


def test_set_extra_mints_a_slug_and_updates_in_place():
    state = apply_costs_op(CostsState(), {
        "op": "set_extra", "item": {"name": "Dumpster rental!", "cost": 450}})
    assert [item.id for item in state.extra] == ["dumpster-rental"]
    # Same name again mints a fresh id rather than clobbering.
    state = apply_costs_op(state, {
        "op": "set_extra", "item": {"name": "Dumpster rental!", "cost": 450}})
    assert [item.id for item in state.extra] == ["dumpster-rental", "dumpster-rental-2"]
    # An explicit id updates that item in place, keeping order.
    state = apply_costs_op(state, {
        "op": "set_extra", "item": {"id": "dumpster-rental", "name": "Dumpster rental!",
                                    "cost": 500, "paid": True}})
    assert [item.id for item in state.extra] == ["dumpster-rental", "dumpster-rental-2"]
    assert state.extra[0].paid and state.extra[0].cost.low == 500


def test_delete_extra_removes_and_rejects_the_unknown():
    state = apply_costs_op(CostsState(), {"op": "set_extra", "item": {"name": "Crane day"}})
    state = apply_costs_op(state, {"op": "delete_extra", "id": "crane-day"})
    assert state.extra == ()
    with pytest.raises(ValueError):
        apply_costs_op(state, {"op": "delete_extra", "id": "crane-day"})


def test_an_unknown_op_is_rejected():
    with pytest.raises(ValueError) as error:
        apply_costs_op(CostsState(), {"op": "pay_everything"})
    assert "unknown costs op" in str(error.value)


# --- payload: staleness and totals ---------------------------------------------------------

def test_stale_entries_are_surfaced_never_dropped(bom):
    """An entry whose (section, key) matches no current BOM row is a fact the owner must
    see — the plan moved on under a paid check-off."""
    live_key = str(bom["framing_by_size"][0]["profile"])
    state = CostsState(entries={
        "framing": {live_key: CostEntry(paid=True),
                    "2x97": CostEntry(paid=True, actual_cost=10.0)},
    })
    payload = costs_payload(bom, None, state)
    assert payload["stale"] == [{"section": "framing", "key": "2x97"}]
    # The stale entry still appears in entries — surfaced, not dropped.
    assert "2x97" in payload["entries"]["framing"]


def test_payload_totals_include_extras_and_actuals(bom):
    state = CostsState(
        entries={"framing": {
            str(bom["framing_by_size"][0]["profile"]): CostEntry(paid=True,
                                                                 actual_cost=1000.0),
            str(bom["framing_by_size"][1]["profile"]): CostEntry(paid=False,
                                                                 actual_cost=999.0),
        }},
        extra=(ExtraItem(id="permit", name="Permit", cost=PriceRange(1800, 2400)),
               ExtraItem(id="dumpster", name="Dumpster", cost=PriceRange(450, 450),
                         paid=True)),
    )
    payload = costs_payload(bom, None, state)
    totals = payload["totals"]
    assert totals["extra"] == {"low": 2250.0, "high": 2850.0}
    assert totals["extra_paid"] == {"low": 450.0, "high": 450.0}
    # Only the PAID entry's actual cost counts as spent.
    assert totals["actual_paid"] == 1000.0
    assert totals["paid_entries"] == 1
    # Without prices there is no estimate and no combined total — absent, not $0.
    assert payload["prices_loaded"] is False and payload["estimate"] is None
    assert "combined" not in totals


def test_payload_join_mirrors_estimate_plans(bom):
    payload = costs_payload(bom, None, CostsState())
    assert set(payload["join"]) == {name for name, *_ in ESTIMATE_PLANS}
    framing = payload["join"]["framing"]
    assert framing == {"bom_key": "framing_by_size", "key_field": "profile",
                       "quantity_field": "order_length_ft", "unit": "LF",
                       "in_total": True}
    # Furnishings read the same BOM table as placeables and are reported beside the
    # construction total, so a client mapping bom_key -> section has to keep both.
    assert payload["join"]["furnishings"]["bom_key"] == "placeables"
    assert payload["join"]["furnishings"]["in_total"] is False
    assert payload["join"]["placeables"]["in_total"] is True
