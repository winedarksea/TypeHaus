"""[light_run_materials] — the cove/LED table joins the BOM, in two units, per type.

The table used to be UNREAD: keyed on ``item`` ("channel", "tape") and named by no
``ESTIMATE_PLANS`` entry, so every foot of channel and every end cap fell into ``unpriced``
and the two runs anybody cared about were reached by a driven ``[allowances]`` row instead.
Those rows are gone; this is what replaced them.
"""

from pathlib import Path

import pytest

from typehaus.cli.price_file import _SECTIONS, ALTERNATE_UNITS, load_prices
from typehaus.cli.prices import ESTIMATE_PLANS, QUALIFIED_KEY_FIELD, estimate_costs
from typehaus.takeoff.bom import bill_of_materials
from typehaus.takeoff.cost_codes import SECTION_CODES

HOUSE = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_estimate(catlin_model, catlin_areas):
    prices = load_prices(HOUSE)
    assert prices is not None
    # ``areas`` because catlin drives an allowance off ``space_summary.gross_sf``; nothing
    # in this section reads it.
    return estimate_costs(bill_of_materials(catlin_model), prices, catlin_areas)


def test_the_section_is_declared_everywhere_a_section_must_be():
    plan = next(p for p in ESTIMATE_PLANS if p[0] == "light_run_materials")
    # It reads its own BOM table, keys on the item, and multiplies ``quantity``.
    assert plan == ("light_run_materials", "light_run_materials", "item", "quantity", "LF")
    assert "light_run_materials" in _SECTIONS
    assert "light_run_materials" in SECTION_CODES
    # The per-type qualifier is what keeps a damp-location exterior extrusion and a
    # sauna-rated silicone tape off the 24V cove rate.
    assert QUALIFIED_KEY_FIELD["light_run_materials"] == "type"


def test_a_piece_row_prices_in_pieces_and_a_foot_row_in_feet():
    """The obstacle this section was blocked on: one table, two honest units.

    ``EA`` is a printed LABEL over the SAME ``quantity`` column — nothing converts — so a
    row that forgets ``unit = "EA"`` reads as feet, which is why the offer is explicit.
    """
    assert ALTERNATE_UNITS["light_run_materials"] == {"EA": "quantity"}


def test_every_light_run_material_row_is_priced(catlin_estimate):
    assert [row for row in catlin_estimate["unpriced"]
            if row["section"] == "light_run_materials"] == []
    section = catlin_estimate["sections"]["light_run_materials"]
    units = {row["key"]: row["unit"] for row in section["rows"]}
    assert units["channel"] == "LF" and units["tape"] == "LF"
    assert units["end_cap"] == "EA" and units["corner_connector"] == "EA"
    assert units["end_cap:ED-T-LT-LINEAR-EXT"] == "EA"
    assert section["subtotal"]["low"] > 0


def test_the_two_stopgap_allowances_are_gone_and_nothing_bills_twice(catlin_estimate):
    """Both were DRIVEN off ``light_run_materials.quantity[...]``. Now that the table is
    priced, keeping either would bill the same channel and tape a second time."""
    allowances = {row["key"] for row in catlin_estimate["sections"]["allowances"]["rows"]}
    assert "electrical-garage-exterior-linear" not in allowances
    assert "electrical-sauna-under-bench-strip" not in allowances
    assert not [finding for finding in catlin_estimate["driver_overlaps"]
                if "light_run_materials" in finding["sections"]]


def test_the_exterior_and_sauna_types_price_apart_from_the_24v_cove(catlin_estimate):
    rows = {(row["key"], row["quantity"]): row
            for row in catlin_estimate["sections"]["light_run_materials"]["rows"]}
    exterior = next(row for (key, _), row in rows.items()
                    if key == "channel:ED-T-LT-LINEAR-EXT")
    cove = next(row for (key, _), row in rows.items() if key == "channel")
    per_ft = lambda row: row["unit_price"]["low"]  # noqa: E731
    assert per_ft(exterior) > per_ft(cove), "ladder work at the eaves is not cove work"
