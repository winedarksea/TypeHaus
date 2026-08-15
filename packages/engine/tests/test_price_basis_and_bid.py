"""The cost model: what a price *includes*, and the ladder from net to bid.

Every number in ``prices.toml`` used to be material-only-by-convention, stated in four
paragraphs of prose at the top of the file that no consumer could read. Two sections
actually carried labour and said so only in a comment. So an estimate could not tell a
homeowner's shopping list from a contractor's number, and sales tax — material-only in MN —
had nothing to apply itself to.

The rules being pinned here, in order of how much damage breaking them does:

1. A **merged** number is never divided. An ``installed`` price with no declared split
   reports as merged, and tax is told how much it could not reach.
2. **Waste is never double-counted.** Four sections are billed on an order quantity that
   already carries it; a ``[waste]`` entry on one of those is a hard error.
3. The parts always sum to the whole — basis subtotals to the section subtotal, section
   subtotals to the total, ladder stages to the bid.
"""

from __future__ import annotations

import pytest

from typehaus.cli.prices import (INSTALLED, LABOUR, MATERIAL, _SECTIONS, estimate_costs,
                                 load_prices)
from typehaus.takeoff.cost_model import per_sf

_BOM = {
    "framing_by_size": [{"profile": "2x6", "order_length_ft": 100.0}],
    "envelope_layers": [{"material": "rockwool", "net_area_sqft": 200.0}],
    "structural_solids": [{"category": "slab", "volume_cubic_yards": 10.0}],
}


def _prices(tmp_path, body: str):
    (tmp_path / "prices.toml").write_text(body)
    return load_prices(tmp_path)


# --- 2A: the four value shapes ------------------------------------------------------------

def test_a_bare_number_takes_its_sections_declared_basis(tmp_path) -> None:
    prices = _prices(tmp_path, '[basis]\nconcrete = "installed"\n[concrete]\nslab = 200\n')
    assert prices.concrete["slab"].basis == INSTALLED
    assert prices.basis_for("concrete", "slab") == INSTALLED


def test_a_row_may_override_its_sections_basis(tmp_path) -> None:
    """The shape a real merged quote arrives in — one row, priced installed, in a file
    that is otherwise material."""
    prices = _prices(tmp_path, '[basis]\nframing = "material"\n'
                               '[framing]\n"2x6" = 1.0\n'
                               '"2x10" = { low = 2.8, high = 3.4, basis = "installed" }\n')
    assert prices.framing["2x6"].basis == MATERIAL
    assert prices.framing["2x10"].basis == INSTALLED
    assert (prices.framing["2x10"].low, prices.framing["2x10"].high) == (2.8, 3.4)


def test_an_explicit_split_sums_to_the_installed_price(tmp_path) -> None:
    prices = _prices(tmp_path, '[framing]\nLVL = { material = { low = 7, high = 9 }, '
                               'labour = { low = 3, high = 5 } }\n')
    price = prices.framing["LVL"]
    assert price.is_split and price.basis == INSTALLED
    assert (price.low, price.high) == (10.0, 14.0)


@pytest.mark.parametrize("body, message", [
    ('[framing]\n"2x6" = { material = { low = 1, high = 2 } }\n', "needs exactly"),
    ('[framing]\n"2x6" = { low = 1, high = 2, basis = "guess" }\n', "expected one of"),
    ('[framing]\n"2x6" = { low = 1, high = 2, colour = "red" }\n', "unexpected key"),
    ('[basis]\nnope = "material"\n', "unknown section"),
    ('[basis]\nframing = "installed"\n[concrete]\nslab = 1\n', "does not cover"),
])
def test_a_malformed_basis_errors_loudly(tmp_path, body: str, message: str) -> None:
    with pytest.raises(ValueError) as error:
        _prices(tmp_path, body)
    assert message in str(error.value)


def test_a_file_with_no_basis_table_says_so_rather_than_guessing_quietly(tmp_path) -> None:
    prices = _prices(tmp_path, '[framing]\n"2x6" = 1.0\n')
    assert prices.basis_declared is False
    assert prices.basis["framing"] == MATERIAL  # the documented file default, but declared


# --- 2A: three subtotals ------------------------------------------------------------------

def test_material_labour_and_merged_sum_to_the_section_subtotal(tmp_path) -> None:
    prices = _prices(tmp_path, '[basis]\nframing = "material"\nconcrete = "installed"\n'
                               'envelope_layers = "labour"\n'
                               '[framing]\n"2x6" = 1.0\n'
                               '[concrete]\nslab = 200\n'
                               '[envelope_layers]\nrockwool = 2.0\n')
    estimate = estimate_costs(_BOM, prices)
    for name, section in estimate["sections"].items():
        buckets = section["basis_subtotals"]
        for end in ("low", "high"):
            parts = sum(buckets[b][end] for b in (MATERIAL, LABOUR, "merged"))
            assert parts == pytest.approx(section["subtotal"][end], abs=0.01), name


def test_an_installed_row_without_a_split_lands_in_merged_and_is_never_divided(tmp_path) -> None:
    prices = _prices(tmp_path, '[basis]\nconcrete = "installed"\n[concrete]\nslab = 200\n')
    estimate = estimate_costs(_BOM, prices)
    buckets = estimate["sections"]["concrete"]["basis_subtotals"]
    assert buckets["merged"]["low"] == 2000.0
    assert buckets[MATERIAL]["low"] == 0.0 and buckets[LABOUR]["low"] == 0.0


def test_a_declared_split_scales_with_the_quantity(tmp_path) -> None:
    prices = _prices(tmp_path, '[framing]\n"2x6" = { material = { low = 0.7, high = 0.7 }, '
                               'labour = { low = 0.3, high = 0.3 } }\n')
    estimate = estimate_costs(_BOM, prices)
    buckets = estimate["sections"]["framing"]["basis_subtotals"]
    assert buckets[MATERIAL]["low"] == pytest.approx(70.0)
    assert buckets[LABOUR]["low"] == pytest.approx(30.0)


# --- 2B: waste, contingency, markup, tax --------------------------------------------------

@pytest.mark.parametrize("section, module_hint", [
    ("framing", "takeoff/framing.py"),
    ("sheet_goods", "sheets_4x8"),
    ("floor_finishes", "takeoff/finishes.py"),
    ("wood_surfaces", "takeoff/wood_surfaces.py"),
])
def test_waste_on_an_order_quantity_section_is_a_hard_error(tmp_path, section, module_hint) -> None:
    """The exact double-count the whole design guards against — and the message has to name
    the takeoff module that already owns the factor, or "you already have waste" is useless."""
    with pytest.raises(ValueError) as error:
        _prices(tmp_path, f'[waste]\n{section} = 0.10\n')
    assert "double-count" in str(error.value)
    assert module_hint in str(error.value)


def test_waste_applies_to_a_net_section_and_shows_as_its_own_line(tmp_path) -> None:
    prices = _prices(tmp_path, '[envelope_layers]\nrockwool = 2.0\n[waste]\nenvelope_layers = 0.10\n')
    estimate = estimate_costs(_BOM, prices)
    stages = {row["label"]: row for row in estimate["bid"]["stages"]}
    assert stages["subtotal_net"]["low"] == 400.0
    assert stages["waste"]["low"] == pytest.approx(40.0)
    assert stages["subtotal_ordered"]["low"] == pytest.approx(440.0)


def test_a_per_key_waste_override_beats_the_section_rate(tmp_path) -> None:
    prices = _prices(tmp_path, '[envelope_layers]\nrockwool = 2.0\n'
                               '[waste]\nenvelope_layers = 0.20\n'
                               '"envelope_layers:rockwool" = 0.05\n')
    assert prices.adjustments.waste_rate("envelope_layers", "rockwool") == 0.05
    assert prices.adjustments.waste_rate("envelope_layers", "other") == 0.20


def test_the_ladder_runs_net_waste_contingency_markup_tax_total(tmp_path) -> None:
    prices = _prices(tmp_path, '[envelope_layers]\nrockwool = 2.0\n'
                               '[waste]\nenvelope_layers = 0.10\n'
                               '[contingency]\nrate = 0.10\n'
                               '[markup]\noverhead = 0.10\nprofit = 0.08\n'
                               '[tax]\nmaterial_rate = 0.06875\n')
    stages = {row["label"]: row["low"] for row in estimate_costs(_BOM, prices)["bid"]["stages"]}
    ordered = 400.0 * 1.10
    contingency = ordered * 0.10
    base = ordered + contingency
    overhead = base * 0.10
    profit = (base + overhead) * 0.08
    tax = base * 0.06875  # 100% material
    assert stages["contingency"] == pytest.approx(contingency, abs=0.02)
    assert stages["overhead"] == pytest.approx(overhead, abs=0.02)
    assert stages["profit"] == pytest.approx(profit, abs=0.02)
    assert stages["tax"] == pytest.approx(tax, abs=0.02)
    assert stages["total"] == pytest.approx(base + overhead + profit + tax, abs=0.05)


def test_tax_cannot_reach_a_merged_subtotal_and_reports_how_much(tmp_path) -> None:
    """Half material, half merged: tax sees the material half only, and the payload names
    the rest rather than quietly taxing or quietly exempting it."""
    prices = _prices(tmp_path, '[basis]\nconcrete = "installed"\nenvelope_layers = "material"\n'
                               '[concrete]\nslab = 40\n[envelope_layers]\nrockwool = 2.0\n'
                               '[tax]\nmaterial_rate = 0.10\n')
    bid = estimate_costs(_BOM, prices)["bid"]
    assert bid["subtotal_net"]["low"] == 800.0
    assert bid["untaxed_merged"]["low"] == 400.0
    stages = {row["label"]: row["low"] for row in bid["stages"]}
    assert stages["tax"] == pytest.approx(40.0, abs=0.05)  # 10% of the 400 material half


@pytest.mark.parametrize("body", ['[contingency]\nrate = 10\n', '[markup]\noverhead = 1.5\n',
                                  '[tax]\nmaterial_rate = 6.875\n'])
def test_a_percent_written_as_a_whole_number_is_rejected(tmp_path, body: str) -> None:
    """0.10 means 10%. Accepting 10 would silently multiply an estimate by eleven."""
    with pytest.raises(ValueError, match="fraction"):
        _prices(tmp_path, body)


def test_no_adjustments_means_the_total_is_untouched(tmp_path) -> None:
    """The default must be inert: a house that declares nothing gets the net number it
    always got, so adding this machinery cannot have moved anybody's estimate."""
    prices = _prices(tmp_path, '[framing]\n"2x6" = 1.0\n[envelope_layers]\nrockwool = 2.0\n')
    estimate = estimate_costs(_BOM, prices)
    assert estimate["bid"]["total"] == estimate["total"] == estimate["bid"]["subtotal_net"]


# --- 2C: $/sf -----------------------------------------------------------------------------

def test_per_sf_divides_by_the_areas_it_is_given(tmp_path) -> None:
    prices = _prices(tmp_path, '[framing]\n"2x6" = 1.0\n')
    estimate = estimate_costs(_BOM, prices, {"conditioned": 100.0, "gross": 200.0})
    assert estimate["per_sf"]["total"]["conditioned"] == {"low": 1.0, "high": 1.0}
    assert estimate["per_sf"]["total"]["gross"] == {"low": 0.5, "high": 0.5}


def test_per_sf_skips_a_zero_denominator_rather_than_dividing_by_it() -> None:
    assert per_sf({"low": 10.0, "high": 20.0}, {"conditioned": 0.0, "gross": 10.0}) == {
        "gross": {"low": 1.0, "high": 2.0}}


def test_estimate_costs_without_areas_reports_no_per_sf(tmp_path) -> None:
    prices = _prices(tmp_path, '[framing]\n"2x6" = 1.0\n')
    assert "per_sf" not in estimate_costs(_BOM, prices)


# --- the reference house ------------------------------------------------------------------

def test_catlins_basis_table_covers_every_section(catlin_dir) -> None:
    """The same contract ``ESTIMATE_PLANS`` has against ``_SECTIONS``: a basis table that
    covers most sections is one whose gaps read as deliberate exceptions."""
    prices = load_prices(catlin_dir)
    assert prices is not None and prices.basis_declared
    assert set(prices.basis) == set(_SECTIONS)


@pytest.fixture
def catlin_dir():
    from _helpers import CATLIN

    return CATLIN
