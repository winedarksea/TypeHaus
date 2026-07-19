"""Honest EN-1 — prescriptive envelope, WWR, block load (→ Permit-ready plan set Phase 7)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.checks.code.mn_energy import MN_ZONE_6, evaluate_envelope
from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def test_prescriptive_rows_cover_every_envelope_role(catlin_model):
    rows = evaluate_envelope(catlin_model, catlin_model.plan)
    roles = {row.role for row in rows}
    assert {"roof", "above-grade wall", "foundation wall", "window"} <= roles


def test_deck_slab_reports_unknown_not_pass(catlin_model):
    rows = evaluate_envelope(catlin_model, catlin_model.plan)
    deck_rows = [row for row in rows if row.component == "SL-M-DECK"]
    assert deck_rows
    assert all(row.verdict == "unknown" for row in deck_rows)


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
    from typehaus.emit.draw import write_permit_set
    from typehaus.energy import estimate_block_load
    from typehaus.checks.registry import Preferences

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
