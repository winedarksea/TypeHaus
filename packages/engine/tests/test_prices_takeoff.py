"""prices.toml — user-supplied $ / $-range estimates on the takeoff and variant compare.

Type:Haus ships no default prices; these tests cover the loader (load-if-exists, loud on a
malformed file), the range arithmetic, the honest-about-unpriced estimate, and the two CLI
surfaces (`haus takeoff`, `haus variants compare`) with and without the file present.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from typehaus.cli.prices import PriceRange, estimate_costs, load_prices
from _helpers import copy_house

_SAMPLE = """\
[framing]
"2x4" = 0.72
"2x6" = { low = 0.95, high = 1.35 }

[sheet_goods]
osb = 22.50

[hardware]
LUS210 = 1.85

[concrete]
slab = { low = 180, high = 240 }

[floor_heat]
electric = 12.0

[placeables]
dishwasher-24 = { low = 700, high = 1100 }
"""


def test_price_range_arithmetic_and_formatting() -> None:
    exact = PriceRange(0.72, 0.72)
    assert exact.is_exact
    assert exact.times(100).fmt() == "$72.00"
    spread = PriceRange(0.95, 1.35)
    assert spread.times(10).fmt() == "$9.50 – $13.50"
    # A negative quantity (a compare delta that removes material) keeps ends sorted.
    negative = spread.times(-10)
    assert (negative.low, negative.high) == (-13.5, -9.5)
    assert negative.fmt(signed=True) == "-$13.50 – -$9.50"
    assert exact.times(10).fmt(signed=True) == "+$7.20"


def test_load_prices_is_load_if_exists(tmp_path: Path) -> None:
    assert load_prices(tmp_path) is None  # no file: no prices, no error
    (tmp_path / "prices.toml").write_text(_SAMPLE)
    prices = load_prices(tmp_path)
    assert prices is not None
    assert prices.framing["2x4"].is_exact
    assert (prices.framing["2x6"].low, prices.framing["2x6"].high) == (0.95, 1.35)
    assert prices.placeables["dishwasher-24"].high == 1100


@pytest.mark.parametrize("body, message", [
    ("[lumber]\n\"2x4\" = 1.0\n", "unknown section"),
    ("[framing]\n\"2x4\" = { low = 2.0, high = 1.0 }\n", "low <= high"),
    ("[framing]\n\"2x4\" = -1.0\n", "negative"),
    ("[framing]\n\"2x4\" = \"cheap\"\n", "must be a number"),
])
def test_a_malformed_prices_file_errors_loudly(tmp_path: Path, body: str, message: str) -> None:
    """A mistyped price must never be silently priced at zero."""
    (tmp_path / "prices.toml").write_text(body)
    with pytest.raises(ValueError) as error:
        load_prices(tmp_path)
    assert message in str(error.value)


def test_estimate_costs_prices_what_it_can_and_confesses_the_rest(tmp_path: Path) -> None:
    (tmp_path / "prices.toml").write_text(_SAMPLE)
    prices = load_prices(tmp_path)
    bom = {
        "framing_by_size": [
            {"profile": "2x4", "order_length_ft": 100},
            {"profile": "2x6", "order_length_ft": 10},
            {"profile": "11.875 I-joist", "order_length_ft": 50},  # unpriced
        ],
        "sheet_goods": [{"material": "osb", "sheets_4x8": 4}],
        "hardware": [{"part_number": "LUS210", "count": 10}],
        "structural_solids": [{"category": "slab", "volume_cubic_yards": 2.0}],
        "floor_heat": [{"system": "electric", "wire_length_ft": 10.0}],
        "placeables": [{"type": "dishwasher-24", "count": 1}],
    }
    estimate = estimate_costs(bom, prices)
    framing = estimate["sections"]["framing"]
    assert framing["subtotal"] == {"low": pytest.approx(81.5), "high": pytest.approx(85.5)}
    assert estimate["sections"]["sheet_goods"]["subtotal"]["low"] == pytest.approx(90.0)
    assert estimate["sections"]["concrete"]["subtotal"] == {"low": 360.0, "high": 480.0}
    assert estimate["total"] == {
        "low": pytest.approx(81.5 + 90.0 + 18.5 + 360.0 + 120.0 + 700.0),
        "high": pytest.approx(85.5 + 90.0 + 18.5 + 480.0 + 120.0 + 1100.0),
    }
    assert estimate["unpriced"] == [{"section": "framing", "key": "11.875 I-joist",
                                     "quantity": 50, "unit": "LF"}]
    assert "$" in estimate["total_fmt"]


def _run(*args: str):
    from typehaus.cli.app import app

    return CliRunner().invoke(app, list(args))


@pytest.fixture()
def priced_starter(starter_dir: Path, tmp_path: Path) -> Path:
    """A disposable copy of the starter house carrying a sample prices.toml."""
    house = tmp_path / "house"
    copy_house(starter_dir, house)
    (house / "prices.toml").write_text(_SAMPLE)
    return house


def test_cli_takeoff_reports_dollar_estimates_with_prices_present(priced_starter: Path) -> None:
    result = _run("takeoff", str(priced_starter))
    assert result.exit_code == 0, result.output
    assert "Cost estimate" in result.output
    assert "$" in result.output


def test_cli_takeoff_still_works_without_prices(starter_dir: Path) -> None:
    result = _run("takeoff", str(starter_dir))
    assert result.exit_code == 0, result.output
    assert "Cost estimate" not in result.output


def test_cli_variants_compare_shows_dollar_ranges(priced_starter: Path) -> None:
    result = _run("variants", "compare", "as-authored", "2x4-ci",
                  "--house", str(priced_starter), "--no-checks")
    assert result.exit_code == 0, result.output
    assert "$" in result.output  # the Δ $ (est) column landed
    assert "framing" in result.output


def test_cli_variants_compare_still_works_without_prices(starter_dir: Path) -> None:
    result = _run("variants", "compare", "as-authored", "2x4-ci",
                  "--house", str(starter_dir), "--no-checks")
    assert result.exit_code == 0, result.output
    assert "$" not in result.output


# --- every BOM table is priced, declared a view, or listed unpriced -------------------------
# The estimate refuses to price a rate with nothing to multiply. The mirror of that rule is
# what `unpriced` reports — and until 2026-08-21 it could only report a miss inside a table
# some ESTIMATE_PLAN already read, so a table no plan named at all fell through both. That is
# how catlin's LED run materials came to be resolved, exported and invisible to every cost
# surface. These three pin the sweep that closed it.

def test_a_bom_table_no_plan_reads_surfaces_as_unpriced(tmp_path) -> None:
    """The hole itself: an undeclared table is listed, summed by (key, unit)."""
    (tmp_path / "prices.toml").write_text(_SAMPLE)
    estimate = estimate_costs({
        "framing_by_size": [{"profile": "2x4", "order_length_ft": 100}],
        "light_run_materials": [
            {"item": "tape", "unit": "LF", "quantity": 3.3},
            {"item": "tape", "unit": "LF", "quantity": 6.7},
            {"item": "end_cap", "unit": "EA", "quantity": 4},
        ],
    }, load_prices(tmp_path))
    assert [row for row in estimate["unpriced"] if row["section"] == "light_run_materials"] == [
        {"section": "light_run_materials", "key": "end_cap", "quantity": 4.0, "unit": "EA"},
        {"section": "light_run_materials", "key": "tape", "quantity": 10.0, "unit": "LF"},
    ]
    # Listed, never priced at zero: the total is the framing and nothing else.
    assert estimate["total"] == {"low": pytest.approx(72.0), "high": pytest.approx(72.0)}


def test_a_declared_view_is_not_reported_as_a_hole(tmp_path) -> None:
    """`electrical_devices` is the same objects [placeables] already prices per type."""
    from typehaus.cli.prices import UNPRICED_VIEWS

    (tmp_path / "prices.toml").write_text(_SAMPLE)
    estimate = estimate_costs({
        "placeables": [{"type": "dishwasher-24", "count": 1}],
        "electrical_devices": [{"kind": "receptacle", "type": "ED-T-RECEP", "count": 40}],
    }, load_prices(tmp_path))
    assert "electrical_devices" in UNPRICED_VIEWS
    assert not [row for row in estimate["unpriced"] if row["section"] == "electrical_devices"]


def test_every_catlin_bom_table_is_priced_declared_or_unpriced(catlin_model) -> None:
    """The completeness guarantee, against the real house.

    This is the test a *new* takeoff table trips: it will be neither read by a plan nor
    named in UNPRICED_VIEWS, so it has to show up in `unpriced` — loud by default, which is
    the whole point of the sweep. Fixing it is a one-line decision, not a silent omission.
    """
    from typehaus.cli.prices import ESTIMATE_PLANS, UNPRICED_VIEWS, estimate_costs
    from typehaus.takeoff import bill_of_materials

    bom = bill_of_materials(catlin_model)
    prices = load_prices(Path("houses/catlin"))
    estimate = estimate_costs(bom, prices)
    read = {bom_key for _, bom_key, *_ in ESTIMATE_PLANS}
    listed = {row["section"] for row in estimate["unpriced"]}
    orphans = {
        name for name, table in bom.items()
        if name not in read and name not in UNPRICED_VIEWS
        and isinstance(table, list) and table and name not in listed
    }
    assert not orphans, f"BOM tables reaching no cost surface at all: {sorted(orphans)}"
    # And the table that motivated the sweep is really there, not merely not-an-orphan.
    assert "light_run_materials" in listed
