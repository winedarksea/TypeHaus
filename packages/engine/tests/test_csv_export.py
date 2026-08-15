"""The CSV exit — deterministic bytes, and the columns a contractor's software reads.

The engine had no CSV writer at all, which is why nothing it computes could reach an
estimating package: RSMeans Online, Craftsman Cloud, Buildertrend and a QuickBooks job-cost
import all read CSV/Excel, and every one of them was one file format away.

Determinism is the property under test as much as the content. ``csv.writer`` picks its own
line ending, quotes at its own discretion, and formats floats however ``str`` feels, so the
same model produces different bytes on different machines and a re-export diff stops meaning
anything.
"""

from __future__ import annotations

import csv

import pytest

from typehaus.cli.prices import estimate_costs, load_prices
from typehaus.emit.csv_writer import NEWLINE, escape, format_field, render_rows, write_csv
from typehaus.takeoff.costs import CostEntry, CostsState
from typehaus.takeoff.estimate_csv import ESTIMATE_COLUMNS, estimate_rows

_BOM = {
    "framing_by_size": [{"profile": "2x6", "order_length_ft": 100.0}],
    "structural_solids": [
        {"category": "column", "volume_cubic_yards": 1.0, "assembly": "ELM_TIMBER"},
        {"category": "column", "volume_cubic_yards": 2.0, "assembly": "POST_WHITE"},
    ],
}
_PRICES = '[basis]\nframing = "material"\nconcrete = "installed"\n' \
          '[framing]\n"2x6" = 1.0\n[concrete]\ncolumn = 300\n'


@pytest.fixture
def estimate(tmp_path):
    (tmp_path / "prices.toml").write_text(_PRICES)
    return estimate_costs(_BOM, load_prices(tmp_path))


# --- the writer ---------------------------------------------------------------------------

@pytest.mark.parametrize("value, expected", [
    (None, ""), (True, "true"), (False, "false"),
    (1.5, "1.50"), (2.0, "2"), (0.0, "0"), ("x", "x"), (7, "7"),
])
def test_field_formatting_is_fixed(value, expected) -> None:
    assert format_field(value) == expected


@pytest.mark.parametrize("value, expected", [
    ("plain", "plain"), ("a,b", '"a,b"'), ('say "hi"', '"say ""hi"""'),
    ("two\nlines", '"two\nlines"'),
])
def test_rfc4180_quoting(value, expected) -> None:
    assert escape(value) == expected


def test_line_ending_is_lf_on_every_platform() -> None:
    assert NEWLINE == "\n"
    assert "\r" not in render_rows(["a"], [{"a": 1}])


def test_the_column_list_is_the_contract() -> None:
    """A row key the header does not name is dropped; a column no row carries is blank.
    Without that, one stray key silently widens a file somebody's import mapping is pinned to."""
    out = render_rows(["a", "b"], [{"a": 1, "surprise": 2}])
    assert out == "a,b\n1,\n"


def test_write_csv_creates_parents_and_returns_the_path(tmp_path) -> None:
    path = write_csv(tmp_path / "deep" / "out.csv", ["a"], [{"a": 1}])
    assert path.read_text() == "a\n1\n"


def test_the_same_rows_produce_the_same_bytes(tmp_path) -> None:
    rows = [{"a": 1.005, "b": None}, {"a": 2, "b": "x,y"}]
    first = write_csv(tmp_path / "a.csv", ["a", "b"], rows).read_bytes()
    second = write_csv(tmp_path / "b.csv", ["a", "b"], rows).read_bytes()
    assert first == second


# --- the estimate rows --------------------------------------------------------------------

def test_the_column_order_is_the_documented_intake_shape() -> None:
    assert ESTIMATE_COLUMNS[:6] == ("nahb_code", "csi_code", "trade", "section", "key",
                                    "description")
    assert ESTIMATE_COLUMNS[-2:] == ("actual_cost", "paid")


def test_one_row_per_section_key_even_when_the_estimate_has_several(estimate) -> None:
    """``structural_solids`` bills two assemblies as ``concrete/column``. ``(section, key)``
    is what ``costs.toml`` files an actual cost under, so the CSV has to aggregate or the
    file cannot be written back unambiguously."""
    rows = estimate_rows(estimate)
    keys = [(row["section"], row["key"]) for row in rows]
    assert len(keys) == len(set(keys))
    column = next(row for row in rows if row["key"] == "column")
    assert column["quantity"] == pytest.approx(3.0)
    assert column["total_low"] == pytest.approx(900.0)
    assert "ELM_TIMBER" in column["description"] and "POST_WHITE" in column["description"]


def test_rows_are_sorted_by_the_join_key(estimate) -> None:
    rows = estimate_rows(estimate)
    assert rows == sorted(rows, key=lambda row: (row["section"], row["key"]))


def test_a_merged_row_leaves_the_split_columns_blank_not_zero(estimate) -> None:
    """Zero would read as "this row has no labour". Blank reads as "not known", which is
    the true statement about an installed price with no declared split."""
    column = next(row for row in estimate_rows(estimate) if row["key"] == "column")
    assert column["basis"] == "installed"
    assert column["material_low"] is None and column["labour_low"] is None
    framing = next(row for row in estimate_rows(estimate) if row["section"] == "framing")
    assert framing["material_low"] == pytest.approx(100.0)


def test_actual_cost_and_paid_come_from_costs_toml(estimate) -> None:
    state = CostsState(entries={"framing": {"2x6": CostEntry(paid=True, actual_cost=91.5)}})
    row = next(r for r in estimate_rows(estimate, state) if r["section"] == "framing")
    assert row["actual_cost"] == 91.5 and row["paid"] is True


def test_the_file_round_trips_through_a_csv_reader(tmp_path, estimate) -> None:
    path = write_csv(tmp_path / "e.csv", ESTIMATE_COLUMNS, estimate_rows(estimate))
    parsed = list(csv.DictReader(path.open()))
    assert [row["key"] for row in parsed] == [row["key"] for row in estimate_rows(estimate)]
    assert sum(float(row["total_low"]) for row in parsed) == pytest.approx(1000.0)
