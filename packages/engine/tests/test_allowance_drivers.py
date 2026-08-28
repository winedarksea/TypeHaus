"""Driven allowances: a lump sum that finally has a quantity behind it.

``[allowances]`` was the one table in ``prices.toml`` with no model quantity — a flat dollar
figure for scope the model does not resolve. A third of the reference house's money sat
there, and none of it moved when the house moved. A ``driver =`` fixes that for the rows
where the model *does* carry a quantity, without moving them out of the table: they keep an
allowance's range, an allowance's cost code and an allowance's work package, and they gain
rate x quantity.

The rules pinned here, in order of how much damage breaking them does:

1. **A driver that cannot be resolved raises.** Never zero, never silently priced as free.
   The same class of failure as a malformed price, for the same reason.
2. **A driver that resolves to ZERO reports as unpriced**, not as a $0 line. "This house has
   none of that" is a claim the reader has to be able to disagree with.
3. **Only ``[allowances]`` may carry one.** Every other section already joins the BOM, and a
   second per-row quantity source would silently shadow it.
4. The double-count guard reports, and does not decide. Measuring a vent mat off the roof
   cladding's area is right; billing the cladding twice is wrong; the two look identical.
"""

from __future__ import annotations

import pytest

from typehaus.cli.prices import estimate_costs, load_prices

_BOM = {
    "openings": [
        {"kind": "door", "type": "DT-INT-SWING30", "operation": "swing", "count": 12},
        {"kind": "door", "type": "DT-EXT-OVERHEAD192", "operation": "overhead", "count": 1},
        {"kind": "window", "type": "WT-3048", "operation": "casement", "count": 9},
    ],
    "envelope_layers": [
        {"scope": "roof", "function": "cladding", "material": "standing-seam",
         "net_area_sqft": 1_000.0},
        {"scope": "roof", "function": "sheathing", "material": "osb",
         "net_area_sqft": 1_000.0},
        {"scope": "wall", "function": "cladding", "material": "pbr-panel-26",
         "net_area_sqft": 400.0},
    ],
    # One row per circuit and no count column — what the `rows` pseudo-field exists for.
    "panel_schedule": [{"circuit": f"CKT-{n}", "poles": 1} for n in range(6)],
}

_AREAS = {"conditioned": 2_000.0, "gross": 2_500.0}


def _prices(tmp_path, body: str):
    (tmp_path / "prices.toml").write_text(body)
    return load_prices(tmp_path)


def _allowance(tmp_path, row: str, bom=None, areas=None):
    prices = _prices(tmp_path, f"[allowances]\n{row}\n")
    return estimate_costs(_BOM if bom is None else bom, prices, areas)


# --- the quantity ---------------------------------------------------------------------------

def test_an_undriven_allowance_is_unchanged(tmp_path) -> None:
    """The whole point of doing this inside [allowances]: a row that names no driver behaves
    exactly as every allowance did before drivers existed."""
    section = _allowance(tmp_path, "site-general-conditions = { low = 35000, high = 80000 }"
                         )["sections"]["allowances"]
    assert section["rows"][0]["quantity"] == 1.0
    assert section["rows"][0]["unit"] == "ls"
    assert "driver" not in section["rows"][0]
    assert section["subtotal"] == {"low": 35_000.0, "high": 80_000.0}


def test_a_driver_sums_a_numeric_field_over_the_table(tmp_path) -> None:
    row = _allowance(
        tmp_path,
        'x = { low = 1.0, high = 2.0, unit = "SF", '
        'driver = "envelope_layers.net_area_sqft" }',
    )["sections"]["allowances"]["rows"][0]
    assert row["quantity"] == 2_400.0
    assert row["unit"] == "SF"
    assert row["cost"] == {"low": 2_400.0, "high": 4_800.0}


def test_a_filter_narrows_the_sum(tmp_path) -> None:
    row = _allowance(tmp_path, 'x = { low = 1, high = 1, unit = "ea", '
                     'driver = "openings.count[kind=door]" }'
                     )["sections"]["allowances"]["rows"][0]
    assert row["quantity"] == 13.0


def test_filters_are_anded_because_one_is_not_enough(tmp_path) -> None:
    """The row this mechanism was built for. ``envelope_layers`` reports a LAYER, not a
    plane, so ``[scope=roof]`` alone sums the cladding and the sheathing into 2,000 SF of a
    1,000 SF roof — a driver that looks right and is 2x wrong."""
    one = _allowance(tmp_path, 'x = { low = 1, high = 1, unit = "SF", '
                     'driver = "envelope_layers.net_area_sqft[scope=roof]" }'
                     )["sections"]["allowances"]["rows"][0]
    two = _allowance(tmp_path, 'x = { low = 1, high = 1, unit = "SF", '
                     'driver = "envelope_layers.net_area_sqft[scope=roof,function=cladding]" }'
                     )["sections"]["allowances"]["rows"][0]
    assert one["quantity"] == 2_000.0
    assert two["quantity"] == 1_000.0


def test_the_rows_pseudo_field_counts_rows(tmp_path) -> None:
    """A panel schedule is one row per circuit and carries no count column, and "36
    circuits" is exactly what a breaker allowance wants to multiply."""
    row = _allowance(tmp_path, 'x = { low = 40, high = 80, unit = "ea", '
                     'driver = "panel_schedule.rows" }'
                     )["sections"]["allowances"]["rows"][0]
    assert row["quantity"] == 6.0
    assert row["cost"] == {"low": 240.0, "high": 480.0}


def test_the_two_scalars_read_the_space_summary(tmp_path) -> None:
    conditioned = _allowance(tmp_path, 'x = { low = 1, high = 1, unit = "SF", '
                             'driver = "space_summary.conditioned_sf" }', areas=_AREAS)
    gross = _allowance(tmp_path, 'x = { low = 1, high = 1, unit = "SF", '
                       'driver = "space_summary.gross_sf" }', areas=_AREAS)
    assert conditioned["sections"]["allowances"]["rows"][0]["quantity"] == 2_000.0
    assert gross["sections"]["allowances"]["rows"][0]["quantity"] == 2_500.0


def test_a_driven_row_is_still_an_allowance(tmp_path) -> None:
    """Nothing downstream needs to know which kind of row it got: same section, same basis,
    same cost code, same place in the construction total."""
    section = _allowance(tmp_path, 'permits-mep = { low = 10, high = 20, unit = "ea", '
                         'driver = "openings.count[kind=window]" }'
                         )["sections"]["allowances"]
    assert section["in_total"] is True
    row = section["rows"][0]
    assert row["quantity"] == 9.0 and row["driver"] == "openings.count[kind=window]"
    # The `permits-` prefix still declares the trade, exactly as for a lump sum.
    assert row["nahb_code"] == "1000"


# --- what a driver refuses to guess ---------------------------------------------------------

def test_an_unknown_table_raises_naming_the_key(tmp_path) -> None:
    with pytest.raises(ValueError) as excinfo:
        _allowance(tmp_path, 'x = { low = 1, high = 2, driver = "wibble.count" }')
    assert "'x'" in str(excinfo.value) and "wibble" in str(excinfo.value)


def test_a_dict_table_is_not_a_driver_target(tmp_path) -> None:
    """``solar`` is a dict of summaries, which is why the BOM grew a ``solar_modules`` list
    view beside it rather than teaching the join about dicts."""
    with pytest.raises(ValueError, match="summary dict"):
        _allowance(tmp_path, 'x = { low = 1, high = 2, driver = "solar.watts" }',
                   bom={"solar": {"total_watts": 5_280.0}})


def test_an_unknown_field_raises_and_lists_the_real_ones(tmp_path) -> None:
    with pytest.raises(ValueError) as excinfo:
        _allowance(tmp_path, 'x = { low = 1, high = 2, driver = "openings.acreage" }')
    message = str(excinfo.value)
    assert "acreage" in message and "'count'" in message and "'rows'" in message


def test_an_unknown_filter_field_raises(tmp_path) -> None:
    with pytest.raises(ValueError, match="colour"):
        _allowance(tmp_path, 'x = { low = 1, high = 2, '
                   'driver = "openings.count[colour=blue]" }')


def test_a_scalar_driver_without_areas_raises_rather_than_reading_zero(tmp_path) -> None:
    """Every production caller passes areas since ``server/space_summary.estimate_areas``.
    A caller that does not gets told so, because the alternative is an air-sealing line
    silently priced against a 0 sf house."""
    with pytest.raises(ValueError, match="without areas"):
        _allowance(tmp_path, 'x = { low = 1, high = 2, driver = "space_summary.gross_sf" }')


def test_a_zero_driver_is_unpriced_rather_than_free(tmp_path) -> None:
    """The house has no overhead door, so it has no opener. That is a CLAIM — reported on
    the unpriced list where a reader can disagree with it — and not a $0 line item, which
    reads as "included"."""
    estimate = _allowance(tmp_path, 'finish-garage-door-opener = { low = 500, high = 1400, '
                          'unit = "ea", driver = "openings.count[operation=bifold]" }')
    assert "allowances" not in estimate["sections"]
    miss = next(row for row in estimate["unpriced"] if row["section"] == "allowances")
    assert miss["key"] == "finish-garage-door-opener" and miss["quantity"] == 0.0
    assert miss["driver"] == "openings.count[operation=bifold]"


# --- where a driver may appear --------------------------------------------------------------

def test_a_driver_on_any_other_section_is_a_load_time_error(tmp_path) -> None:
    """[envelope_layers] already joins the BOM through ESTIMATE_PLANS. Two ways to reach the
    same quantity is one too many, and the one that wins would be invisible."""
    with pytest.raises(ValueError, match="only \\[allowances\\] may"):
        _prices(tmp_path, '[envelope_layers]\ngwb = { low = 1, high = 2, '
                'driver = "envelope_layers.net_area_sqft" }\n')


def test_a_malformed_driver_is_a_load_time_error(tmp_path) -> None:
    with pytest.raises(ValueError, match="not \"<bom_table>.<field>\""):
        _prices(tmp_path, '[allowances]\nx = { low = 1, high = 2, driver = "openings" }\n')


def test_a_driven_rows_unit_is_a_free_label(tmp_path) -> None:
    """Everywhere else a ``unit =`` SELECTS which BOM field the rate multiplies, and an
    unoffered one is a hard error. A driven allowance has already chosen its field."""
    row = _allowance(tmp_path, 'x = { low = 1, high = 1, unit = "drop", '
                     'driver = "openings.count[kind=window]" }'
                     )["sections"]["allowances"]["rows"][0]
    assert row["unit"] == "drop"
    with pytest.raises(ValueError, match="printed LABEL"):
        _prices(tmp_path, '[allowances]\nx = { low = 1, high = 2, '
                'unit = "square feet of roof", driver = "openings.count" }\n')


def test_an_undriven_allowance_still_may_not_name_a_unit(tmp_path) -> None:
    """The free-label escape hatch is the driver's, not the table's: a lump sum's unit is
    "ls" because there is nothing to count."""
    with pytest.raises(ValueError, match="offers no alternatives"):
        _prices(tmp_path, '[allowances]\nx = { low = 1, high = 2, unit = "SF" }\n')


# --- the double-count guard -----------------------------------------------------------------

def test_a_driver_pointing_at_priced_rows_reports_an_overlap(tmp_path) -> None:
    """[allowances]'s one rule is that an allowance must be scope no other section prices,
    and nothing in the loader could ever check it. This is the check: it names the rows, and
    leaves the judgement to a reader, because a legitimate measurement and a double bill are
    the same driver."""
    prices = _prices(tmp_path, '[envelope_layers]\n"standing-seam" = 12.0\n'
                     '[allowances]\nroof-vent-mat = { low = 1.0, high = 1.85, unit = "SF", '
                     'driver = "envelope_layers.net_area_sqft[material=standing-seam]" }\n')
    overlaps = estimate_costs(_BOM, prices)["driver_overlaps"]
    assert len(overlaps) == 1
    assert overlaps[0] == {"item": "roof-vent-mat",
                           "sections": {"envelope_layers": ["standing-seam"]}}


def test_no_overlap_is_reported_when_the_rows_are_not_priced(tmp_path) -> None:
    """The guard reads what was actually PRICED, not what a plan could have priced: an
    allowance measured off a table nobody has a rate for is not a double bill."""
    prices = _prices(tmp_path, '[allowances]\nx = { low = 1.0, high = 2.0, unit = "SF", '
                     'driver = "envelope_layers.net_area_sqft[material=standing-seam]" }\n')
    assert estimate_costs(_BOM, prices)["driver_overlaps"] == []


def test_an_undriven_allowance_can_never_report_an_overlap(tmp_path) -> None:
    prices = _prices(tmp_path, '[envelope_layers]\n"standing-seam" = 12.0\n'
                     '[allowances]\nsite-general-conditions = 35000\n')
    assert estimate_costs(_BOM, prices)["driver_overlaps"] == []


# --- against the reference house -------------------------------------------------------------

def test_catlin_drives_most_of_its_allowance_block(catlin_model, catlin_areas) -> None:
    """The house-side half of the change, and the one that would go stale silently. Every
    driven row has to resolve to a real quantity — an unresolvable one raises, so reaching
    this assertion at all is most of the test."""
    from typehaus.takeoff.bom import bill_of_materials

    prices = load_prices(catlin_model.plan.source_root)
    assert prices is not None
    driven = {key for key, price in prices.allowances.items() if price.driver}
    assert len(driven) >= 15, "the conversion pass drove 17 of the 47 allowance rows"

    estimate = estimate_costs(bill_of_materials(catlin_model), prices, catlin_areas)
    rows = {row["key"]: row for row in estimate["sections"]["allowances"]["rows"]}
    for key in driven:
        assert rows[key]["quantity"] > 0, f"{key} drove to nothing"
        assert rows[key]["unit"] != "ls", f"{key} is driven and must not print as a lump"
    # And the rows deliberately LEFT as lump sums are still lump sums — the residual is the
    # honest half of this change, not an oversight.
    assert rows["site-general-conditions"]["quantity"] == 1.0
    assert rows["permits-design-testing-and-insurance"]["unit"] == "ls"


def test_catlins_driven_rows_follow_the_model(catlin_model, catlin_areas) -> None:
    """The point of the whole exercise, asserted rather than asserted-about: delete every
    window from the BOM and the window-driven allowances fall while the lump sums do not."""
    from typehaus.takeoff.bom import bill_of_materials

    prices = load_prices(catlin_model.plan.source_root)
    bom = bill_of_materials(catlin_model)
    before = {row["key"]: row["cost"]["low"] for row in
              estimate_costs(bom, prices, catlin_areas)["sections"]["allowances"]["rows"]}
    fewer = {**bom, "openings": [row for row in bom["openings"] if row["kind"] != "window"]}
    after = {row["key"]: row["cost"]["low"] for row in
             estimate_costs(fewer, prices, catlin_areas)["sections"]["allowances"]["rows"]}
    assert "finish-window-stools-and-aprons" not in after, "no windows, no stools"
    assert after["finish-door-hardware"] == before["finish-door-hardware"]
    assert after["site-general-conditions"] == before["site-general-conditions"]
