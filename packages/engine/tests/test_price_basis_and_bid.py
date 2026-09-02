"""The cost model: what a price *includes*, and the ladder from net to bid.

Every number in ``prices.toml`` declares whether it is material-only or installed, so an
estimate can split a homeowner's shopping list from a contractor's number, and sales tax —
material-only in MN — has something to apply itself to.

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


# --- 2C: the ready-mix guard, and the qualified key that opens it -------------------------
# `structural_solids` keys on solid CATEGORY, and a category is not a material: "slab" covers
# an EPS-formed concrete deck *and* an aluminium balcony plank. MATERIAL_ONLY stops the
# wood/metal ones billing at the ready-mix $/cy. But those solids are billed by no other
# table, so a house that names one explicitly — by its qualified `category:assembly` key —
# has to be able to price it, or the estimate can only ever report it as a hole.

_MIXED_SOLIDS = {"structural_solids": [
    {"category": "slab", "assembly": "CATLIN_DECK_EPS_INT",
     "structure_material": "concrete", "volume_cubic_yards": 10.0},
    {"category": "slab", "assembly": "BALCONY_DECK_ALUMINUM",
     "structure_material": "aluminum-deck", "volume_cubic_yards": 2.0},
]}


def test_a_non_concrete_solid_stays_unpriced_when_the_house_says_nothing(tmp_path) -> None:
    prices = _prices(tmp_path, '[basis]\nconcrete = "installed"\n[concrete]\nslab = 200\n')
    estimate = estimate_costs(_MIXED_SOLIDS, prices)
    unpriced = {row["key"] for row in estimate["unpriced"]}
    assert "slab:BALCONY_DECK_ALUMINUM" in unpriced
    # ...and it is a hole, not a zero: only the concrete yardage reaches the subtotal.
    assert estimate["sections"]["concrete"]["subtotal"]["low"] == 2000.0


def test_a_bare_category_rate_never_reaches_the_aluminium_deck(tmp_path) -> None:
    """The double-count the guard exists to stop. `slab = 200` must not pick up 2 cy of
    aluminium plank just because the plank's category happens to be "slab"."""
    prices = _prices(tmp_path, '[basis]\nconcrete = "installed"\n[concrete]\nslab = 200\n')
    keys = {row["key"] for row in estimate_costs(_MIXED_SOLIDS, prices)["sections"]
            ["concrete"]["rows"]}
    assert keys == {"slab"}


def test_an_explicit_qualified_key_prices_a_non_concrete_solid(tmp_path) -> None:
    prices = _prices(tmp_path, '[basis]\nconcrete = "installed"\n[concrete]\nslab = 200\n'
                               '"slab:BALCONY_DECK_ALUMINUM" = 3900\n')
    estimate = estimate_costs(_MIXED_SOLIDS, prices)
    rows = {row["key"]: row for row in estimate["sections"]["concrete"]["rows"]}
    assert rows["slab:BALCONY_DECK_ALUMINUM"]["cost"]["low"] == 7800.0
    assert not [r for r in estimate["unpriced"] if r["key"].startswith("slab:BALCONY")]
    # The concrete deck still bills on the bare-category rate; opening the hatch for one
    # assembly must not change what the others do.
    assert rows["slab"]["cost"]["low"] == 2000.0


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


# --- 2D: a row that names its own unit ------------------------------------------------------
#
# ``[concrete]`` prices ``structural_solids`` by the cubic yard because most of what that table
# holds is a pour. A sump is not: it is one object, and pricing it by the yard makes the LINE
# right and the RATE unauditable. ``ALTERNATE_UNITS`` lets one row read a different field of the
# same BOM row, and these pin that it reads the field it says and errors when it cannot.

_UNIT_SOLIDS = {
    "structural_solids": [
        {"category": "footing", "structure_material": "concrete",
         "volume_cubic_yards": 10.0, "count": 4, "plan_area_sqft": 300.0},
        {"category": "sump", "structure_material": None,
         "volume_cubic_yards": 0.19, "count": 1, "plan_area_sqft": 2.2},
    ],
}


def test_a_row_without_a_unit_still_prices_on_the_section_quantity(tmp_path) -> None:
    """The whole point of the default: no existing prices.toml changes meaning."""
    prices = _prices(tmp_path, '[concrete]\nfooting = 100\n')
    row = estimate_costs(_UNIT_SOLIDS, prices)["sections"]["concrete"]["rows"][0]
    assert (row["quantity"], row["unit"]) == (10.0, "cy")
    assert row["cost"] == {"low": 1000.0, "high": 1000.0}


def test_a_unit_override_reads_a_different_field_of_the_same_row(tmp_path) -> None:
    prices = _prices(tmp_path, '[concrete]\nsump = { low = 900, high = 2200, unit = "ea" }\n')
    row = estimate_costs(_UNIT_SOLIDS, prices)["sections"]["concrete"]["rows"][0]
    assert (row["quantity"], row["unit"]) == (1.0, "ea")
    assert row["cost"] == {"low": 900.0, "high": 2200.0}


def test_the_unit_is_resolved_per_row_not_per_section(tmp_path) -> None:
    """`sump` priced each and `footing` priced by the yard, in the same table, same estimate."""
    prices = _prices(tmp_path, '[concrete]\nfooting = 100\n'
                               'sump = { low = 900, high = 2200, unit = "ea" }\n')
    priced = estimate_costs(_UNIT_SOLIDS, prices)["sections"]["concrete"]["rows"]
    rows = {r["key"]: r for r in priced}
    assert (rows["footing"]["quantity"], rows["footing"]["unit"]) == (10.0, "cy")
    assert (rows["sump"]["quantity"], rows["sump"]["unit"]) == (1.0, "ea")


def test_a_unit_override_composes_with_a_material_labour_split(tmp_path) -> None:
    prices = _prices(tmp_path, '[concrete]\nsump = { unit = "ea", '
                               'material = { low = 400, high = 900 }, '
                               'labour = { low = 500, high = 1300 } }\n')
    row = estimate_costs(_UNIT_SOLIDS, prices)["sections"]["concrete"]["rows"][0]
    assert row["unit"] == "ea" and row["basis"] == INSTALLED
    assert row["material"] == {"low": 400.0, "high": 900.0}
    assert row["labour"] == {"low": 500.0, "high": 1300.0}


def test_a_unit_the_section_does_not_offer_is_a_load_error(tmp_path) -> None:
    with pytest.raises(ValueError, match="offers"):
        _prices(tmp_path, '[concrete]\nsump = { low = 1, high = 2, unit = "LF" }\n')


def test_a_section_with_no_alternates_refuses_a_unit_at_all(tmp_path) -> None:
    with pytest.raises(ValueError, match="no alternatives"):
        _prices(tmp_path, '[framing]\n"2x6" = { low = 1, high = 2, unit = "ea" }\n')


# --- 2E: the drainage product qualifier -----------------------------------------------------

_DRAINAGE = {
    "drainage": [
        {"category": "gutter", "product": "aluminum", "length_ft": 47.8},
        {"category": "gutter", "product": "metal-dark-exterior", "length_ft": 73.7},
    ],
}


def test_a_bare_drainage_category_still_prices_every_product(tmp_path) -> None:
    prices = _prices(tmp_path, '[drainage]\ngutter = 10\n')
    section = estimate_costs(_DRAINAGE, prices)["sections"]["drainage"]
    assert section["subtotal"] == {"low": 1215.0, "high": 1215.0}


def test_a_qualified_product_key_beats_the_bare_category(tmp_path) -> None:
    """47.8 LF of K-style at $10 and 73.7 LF of fabricated box at $30 — the 3x the blended
    rate was hiding."""
    prices = _prices(tmp_path, '[drainage]\ngutter = 10\n'
                               '"gutter:metal-dark-exterior" = 30\n')
    rows = {r["key"]: r for r in estimate_costs(_DRAINAGE, prices)["sections"]["drainage"]["rows"]}
    assert rows["gutter"]["cost"] == {"low": 478.0, "high": 478.0}
    assert rows["gutter:metal-dark-exterior"]["cost"] == {"low": 2211.0, "high": 2211.0}


# --- 2F: allowances -------------------------------------------------------------------------
#
# The one section with no model-side quantity. It exists because a total that omits the
# excavator is not a total, and it is a *section* rather than a fudge factor so that every
# lump sum is on its own line, with its own basis, inside the same ladder as a stick of 2x6.

def test_an_allowance_is_a_row_at_quantity_one(tmp_path) -> None:
    prices = _prices(tmp_path, '[allowances]\nsite-excavation = { low = 20000, high = 45000 }\n')
    section = estimate_costs({}, prices)["sections"]["allowances"]
    assert section["rows"][0]["quantity"] == 1.0
    assert section["rows"][0]["unit"] == "ls"
    assert section["subtotal"] == {"low": 20000.0, "high": 45000.0}


def test_allowances_are_inside_the_construction_total(tmp_path) -> None:
    """Unlike furnishings. A sofa is not a construction cost; an excavator is."""
    prices = _prices(tmp_path, '[basis]\nframing = "material"\nallowances = "installed"\n'
                               '[framing]\n"2x6" = 1.0\n'
                               '[allowances]\nsite-excavation = 20000\n')
    estimate = estimate_costs(_BOM, prices)
    assert estimate["sections"]["allowances"]["in_total"] is True
    assert estimate["total"]["low"] == 20100.0


def test_an_allowance_flows_through_the_bid_ladder(tmp_path) -> None:
    prices = _prices(tmp_path, '[contingency]\nrate = 0.10\n'
                               '[allowances]\nsite-excavation = 20000\n')
    bid = estimate_costs({}, prices)["bid"]
    assert bid["subtotal_net"] == {"low": 20000.0, "high": 20000.0}
    assert bid["total"] == {"low": 22000.0, "high": 22000.0}


def test_an_allowance_may_declare_a_material_labour_split(tmp_path) -> None:
    """Excavation is mostly labour and machine time; a lump sum that says so lets MN's
    material-only sales tax find the right base instead of taxing the whole thing."""
    prices = _prices(tmp_path, '[allowances]\nsite-excavation = { '
                               'material = { low = 4000, high = 9000 }, '
                               'labour = { low = 16000, high = 36000 } }\n')
    section = estimate_costs({}, prices)["sections"]["allowances"]
    assert section["basis_subtotals"]["material"] == {"low": 4000.0, "high": 9000.0}
    assert section["basis_subtotals"]["labour"] == {"low": 16000.0, "high": 36000.0}
    assert section["basis_subtotals"]["merged"] == {"low": 0.0, "high": 0.0}


def test_allowances_are_sorted_so_two_exports_diff(tmp_path) -> None:
    prices = _prices(tmp_path, '[allowances]\nzoning = 1\npermits = 2\nexcavation = 3\n')
    keys = [r["key"] for r in estimate_costs({}, prices)["sections"]["allowances"]["rows"]]
    assert keys == ["excavation", "permits", "zoning"]


def test_a_house_with_no_allowances_reports_no_allowances_section(tmp_path) -> None:
    prices = _prices(tmp_path, '[framing]\n"2x6" = 1.0\n')
    assert "allowances" not in estimate_costs(_BOM, prices)["sections"]


# --- 2G: an allowance is scheduled by its key prefix -----------------------------------------

def test_an_allowance_key_prefix_picks_its_trade() -> None:
    """`haus tasks` builds work packages at (trade x storey), so a mis-filed allowance puts
    the excavator's number in the plumber's package. The first draft of these patterns matched
    on substrings and filed "waterproofing" under ROOF (because "proof" contains "roof") and
    "egress-window-wells" under PLUMBING (via "*well*"). Prefixes, and this test."""
    from typehaus.takeoff.cost_codes import cost_code

    assert cost_code("allowances", "site-excavation-backfill-grading").trade == "earth"
    assert cost_code("allowances", "hvac-refrigerant-line-sets").trade == "mechanical"
    assert cost_code("allowances", "electrical-pv-array-modules").trade == "electrical"
    assert cost_code("allowances", "finish-door-hardware").trade == "openings"
    # The two the substring version got wrong.
    assert cost_code("allowances", "foundation-damp-or-waterproofing").trade == "concrete"
    assert cost_code("allowances", "radon-roughin-and-egress-window-wells").trade == "concrete"
    # General conditions is direct job cost (NAHB 9000), not the 1000 site-work default.
    assert cost_code("allowances", "site-general-conditions").nahb == "9000"


def test_every_catlin_allowance_declares_its_trade(catlin_dir) -> None:
    """A key that falls through to the section default is an unclassified one — readable, but
    it will be scheduled as earthwork. The reference house should have none."""
    from typehaus.takeoff.cost_codes import SECTION_CODES, cost_code

    prices = load_prices(catlin_dir)
    assert prices is not None and prices.allowances
    fell_through = [key for key in prices.allowances
                    if cost_code("allowances", key) == SECTION_CODES["allowances"]]
    assert not fell_through, f"unclassified allowance key(s): {fell_through}"


def test_catlin_does_not_pay_the_gc_twice(catlin_dir) -> None:
    """[markup] is deliberately zero AND general contractor overhead/profit is deliberately
    absent from [allowances]. Turning one on without noticing the other is the six-figure
    mistake this file's comments exist to prevent."""
    prices = load_prices(catlin_dir)
    assert prices is not None
    assert prices.adjustments.overhead == 0.0 and prices.adjustments.profit == 0.0
    assert not [key for key in prices.allowances if "overhead" in key or "profit" in key]


# --- 2H: waste is a material fact ------------------------------------------------------------

def test_waste_never_rides_on_declared_labour(tmp_path) -> None:
    """You buy 110 SF of board to install 100 SF; you do not pay the installer 10% more for
    it. Before this rule, 41% of catlin's waste was being added to labour, which made waste
    and contingency read as the same stage twice."""
    prices = _prices(tmp_path, '[envelope_layers]\nrockwool = { material = { low = 3, high = 3 }, '
                               'labour = { low = 7, high = 7 } }\n'
                               '[waste]\nenvelope_layers = 0.10\n')
    estimate = estimate_costs(_BOM, prices)          # 200 SF -> $600 material, $1,400 labour
    section = estimate["sections"]["envelope_layers"]
    assert section["basis_subtotals"]["material"] == {"low": 600.0, "high": 600.0}
    # 10% of the $600 material, NOT of the $2,000 row.
    assert section["waste"] == {"low": 60.0, "high": 60.0}


def test_waste_on_a_merged_row_rides_on_the_whole_number(tmp_path) -> None:
    """The admitted exception: an installed price with no declared split cannot have its
    material half identified, so the factor applies to all of it. Waste over-applies on a
    merged row exactly where tax under-applies — declaring a split fixes both."""
    prices = _prices(tmp_path, '[basis]\nconcrete = "installed"\n'
                               '[concrete]\nslab = 100\n[waste]\nconcrete = 0.05\n')
    section = estimate_costs(_BOM, prices)["sections"]["concrete"]   # 10 cy -> $1,000 merged
    assert section["basis_subtotals"]["merged"] == {"low": 1000.0, "high": 1000.0}
    assert section["waste"] == {"low": 50.0, "high": 50.0}


# --- 2I: material whose price already carries tax --------------------------------------------
#
# A shelf price is pre-tax. A material rate back-derived from a published *installed* cost is
# not: that figure is a contractor's price to a homeowner and, in a materials-taxing state, has
# the tax inside it. Taxing it again is a straight double-count, and it is invisible without a
# way to say which rows are which.

def test_tax_skips_material_whose_price_already_includes_it(tmp_path) -> None:
    prices = _prices(tmp_path, '[framing]\n"2x6" = 1.0\n'
                               '[tax]\nmaterial_rate = 0.10\n'
                               '[tax_included]\nframing = true\n')
    bid = estimate_costs(_BOM, prices)["bid"]          # 100 LF x $1 = $100 material
    assert bid["material_tax_already_paid"] == {"low": 100.0, "high": 100.0}
    assert bid["taxable_material"] == {"low": 0.0, "high": 0.0}
    stages = {row["label"]: row for row in bid["stages"]}
    assert stages["tax"]["low"] == 0.0
    # The money is still in the estimate — only the tax base changed.
    assert bid["subtotal_net"] == {"low": 100.0, "high": 100.0}


def test_tax_inclusiveness_is_per_key_as_well_as_per_section(tmp_path) -> None:
    """It varies row by row inside a section: one rate off a shelf, the next backed out of a
    cost guide. Same key shape as [waste] for exactly that reason."""
    prices = _prices(tmp_path, '[framing]\n"2x6" = 1.0\n'
                               '[envelope_layers]\nrockwool = 2.0\n'
                               '[tax]\nmaterial_rate = 0.10\n'
                               '[tax_included]\n"framing:2x6" = true\n')
    bid = estimate_costs(_BOM, prices)["bid"]   # framing $100 (exempt) + rockwool $400
    assert bid["material_tax_already_paid"] == {"low": 100.0, "high": 100.0}
    assert bid["taxable_material"] == {"low": 400.0, "high": 400.0}


def test_a_row_reports_whether_its_price_carries_tax(tmp_path) -> None:
    prices = _prices(tmp_path, '[framing]\n"2x6" = 1.0\n[tax_included]\nframing = true\n')
    row = estimate_costs(_BOM, prices)["sections"]["framing"]["rows"][0]
    assert row["tax_included"] is True


def test_tax_included_must_be_a_boolean_not_a_rate(tmp_path) -> None:
    """"Does this number already have tax in it" is answerable; "what effective rate is buried
    in this national average" is not, and a float field would invite a guess dressed as one."""
    with pytest.raises(ValueError, match="true or false"):
        _prices(tmp_path, '[framing]\n"2x6" = 1.0\n[tax_included]\nframing = 0.06\n')


def test_tax_included_rejects_an_unknown_section(tmp_path) -> None:
    with pytest.raises(ValueError, match="unknown section"):
        _prices(tmp_path, '[tax_included]\nnot_a_section = true\n')


def test_nothing_changes_when_no_house_declares_tax_inclusiveness(tmp_path) -> None:
    """The default: every material rate is assumed pre-tax, which is what a shelf price is."""
    prices = _prices(tmp_path, '[framing]\n"2x6" = 1.0\n[tax]\nmaterial_rate = 0.10\n')
    bid = estimate_costs(_BOM, prices)["bid"]
    assert bid["material_tax_already_paid"] == {"low": 0.0, "high": 0.0}
    assert bid["taxable_material"] == {"low": 100.0, "high": 100.0}
