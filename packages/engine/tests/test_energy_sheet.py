"""Honest EN-1 — prescriptive envelope, WWR, block load (→ Permit-ready plan set Phase 7)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.checks.code.mn_energy import MN_ZONE_6, evaluate_envelope

# ``slow`` (→ pyproject.toml, AGENTS.md §3): the permit-set PDF: 21 s to render the
# energy sheet. `scripts/verify.sh --fast` deselects it; the full gate still runs it.
pytestmark = pytest.mark.slow


def test_prescriptive_rows_cover_every_envelope_role(catlin_model):
    rows = evaluate_envelope(catlin_model, catlin_model.plan)
    roles = {row.role for row in rows}
    assert {"roof", "above-grade wall", "foundation wall", "window"} <= roles


def test_interior_deck_and_detached_garage_slabs_are_scoped_out(catlin_model):
    """Not every slab is an envelope slab. SL-M-DECK has conditioned space on both faces
    (basement below, main floor above) and SL-G-FLOOR floors the detached, unheated garage,
    so neither earns a prescriptive row — reporting them would assert a requirement the
    code does not make. The slabs that *are* in the envelope must still show up."""
    rows = evaluate_envelope(catlin_model, catlin_model.plan)
    components = {row.component for row in rows}
    assert "SL-M-DECK" not in components
    assert "SL-G-FLOOR" not in components
    assert "SL-B-FLOOR" in components


def test_no_envelope_component_is_left_unknown(catlin_model):
    """The tri-state contract still forbids a silent pass — this asserts the *other* half:
    every component the table does claim to evaluate has a real number behind it."""
    rows = evaluate_envelope(catlin_model, catlin_model.plan)
    unknown = [row for row in rows if row.verdict == "unknown"]
    assert not unknown, [(row.component, row.provided) for row in unknown]


def test_catlin_window_types_pass_u_factor(catlin_model):
    rows = evaluate_envelope(catlin_model, catlin_model.plan)
    window_rows = [row for row in rows if row.role == "window"]
    assert window_rows
    assert all(row.verdict == "pass" for row in window_rows)


def test_unconditioned_garage_excluded(catlin_model):
    rows = evaluate_envelope(catlin_model, catlin_model.plan)
    tags = {row.component for row in rows}
    assert "GARAGE_ROOF" not in tags
    assert "GARAGE_WALL_2X6" not in tags


def test_block_load_and_wwr_appear_on_sheet(catlin_model, tmp_path: Path):
    from typehaus.checks.building_science.wwr import wwr_summary
    from typehaus.checks.registry import Preferences
    from typehaus.emit.draw import write_permit_set
    from typehaus.energy import estimate_block_load

    load = estimate_block_load(catlin_model, Preferences())
    assert load.heating_load_btu_per_hour != 0.0 or load.unknown_inputs
    wwr = wwr_summary(catlin_model)
    assert 0.0 <= wwr["overall"] <= 1.0
    assert len(wwr["per_facade"]) == 4

    path, _ = write_permit_set(catlin_model, tmp_path / "permit_set.pdf")
    assert path.stat().st_size > 0


def test_basement_slab_below_slab_xps_passes_prescriptive_r(catlin_model):
    """SL-B-FLOOR carries a real assembly (3" below-slab XPS, R-15 @ 40 psi) — the
    tri-state contract's honest-PASS side, not just the always-UNKNOWN deck."""
    rows = evaluate_envelope(catlin_model, catlin_model.plan)
    slab_rows = [row for row in rows if row.component == "SL-B-FLOOR"]
    assert slab_rows
    assert all(row.verdict == "pass" for row in slab_rows)


def test_under_code_slab_assembly_fails_not_silent_pass():
    """A bare, uninsulated slab is genuinely under MN zone-6's R-10 slab requirement —
    exercised with ``assembly_r_value``, the same primitive ``evaluate_envelope`` calls,
    covering the tri-state contract's FAIL side (not just UNKNOWN/PASS)."""
    from typehaus.analysis import assembly_r_value
    from typehaus.model.assembly import Assembly, Layer
    from typehaus.model.enums import LayerFunction
    from typehaus.model.materials import Material
    from typehaus.model.plan import Library
    from typehaus.quantities import inch

    bare_slab = Assembly(tag="BARE_SLAB", layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(3.5),
             function=LayerFunction.STRUCTURE),
    ))
    library = Library(materials=(Material(tag="concrete", name="concrete", r_per_inch=0.08),))
    result = assembly_r_value(bare_slab, library)
    assert result.value is not None
    assert result.value.r_us < MN_ZONE_6.slab_r


def test_block_load_counts_only_the_envelope(catlin_model):
    """A block load sums the thermal boundary. Interior partitions and the closet doors
    hosted in them separate two rooms at the same setpoint: counting them against the
    outdoor design temperature inflates the load and fills ``unknown_inputs`` with doors
    that never see outdoor air."""
    from typehaus.checks.building_science.wwr import _wall_length
    from typehaus.checks.registry import Preferences
    from typehaus.energy import _is_envelope_wall, estimate_block_load

    load = estimate_block_load(catlin_model, Preferences())
    walls = next(component for component in load.components if component.kind == "walls")
    clad_wall_area_ft2 = sum(
        _wall_length(wall) * (wall.z1_m - wall.z0_m) * 10.7639104167
        for wall in catlin_model.walls
        if not wall.is_foundation
        and any(layer.function == "cladding" for layer in wall.layers)
    )
    # Gross clad area less its openings; never the whole (partition-inclusive) wall stock.
    assert 0 < walls.area_ft2 <= clad_wall_area_ft2

    envelope_wall_tags = {wall.tag for wall in catlin_model.walls
                          if _is_envelope_wall(wall, catlin_model)}
    interior_door_tags = {opening.tag for opening in catlin_model.openings
                          if opening.is_door and opening.host_wall not in envelope_wall_tags}
    assert interior_door_tags  # catlin has interior doors, so this is a real exclusion
    assert not any(tag in item for tag in interior_door_tags for item in load.unknown_inputs)


def test_wall_comparison_pairs_the_authored_wall_variants(catlin_model):
    """The M5 acceptance is a *wall* 2x4 -> 2x6 swap. The library also holds 2x4-framed
    roofs, and a variant assembly stores no layers of its own, so both the scoping and the
    variant resolution have to be right for this pair to appear."""
    from typehaus.checks.registry import Preferences
    from typehaus.energy import estimate_block_load

    comparison = estimate_block_load(catlin_model, Preferences()).wall_comparison
    assert comparison is not None
    # The exterior stack is 2x6 on every storey, so the only remaining authored 2x4-framed
    # wall stock is the interior partition family.
    assert comparison["baseline_assembly"] == "INT_2X4_PARTITION"
    assert comparison["upgrade_assembly"] == "CATLIN_EXT_2X6"
    assert comparison["heating_savings_btu_per_hour"] > 0
