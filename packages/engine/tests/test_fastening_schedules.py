"""Decision #147: every authored fastening schedule is counted, and S-001 lists the special ones."""

from __future__ import annotations

from typehaus.hardware.catalog import (
    ROLE_SITE_BOLT,
    ROLE_SITE_LAG,
    ROLE_TRIM_FASTENER,
    ROLE_WINDOW_INSTALL_FASTENER,
    hardware_by_model,
    structural_hardware_catalog,
)
from typehaus.hardware.connector_fastening import STAINLESS_FINISHES
from typehaus.quantities import M_PER_IN
from typehaus.takeoff.hardware import hardware_takeoff
from typehaus.takeoff.trim_fasteners import fasteners_per_run
from typehaus.takeoff.window_fasteners import fin_fasteners

_TREATED_OK = STAINLESS_FINISHES | {"hdg", "mech_galv"}


def test_trim_and_fin_arithmetic():
    # 10'-1": a fastener each end and every 16" between, two rows -> (8 + 1) x 2.
    assert fasteners_per_run(121 * M_PER_IN, 16.0, rows=2) == 18
    assert fasteners_per_run(16 * M_PER_IN, 16.0) == 2
    # A 27.5 x 48 unit, fin at 8" from 2" off each corner: 23.5" -> 3 + 1, 44" -> 6 + 1.
    assert fin_fasteners(27.5, 48.0, 8.0, 2.0) == 2 * 4 + 2 * 7


def test_catlin_counts_the_wall_and_subfloor_schedules(catlin_model_ro):
    rows = {row["part_number"]: row for row in hardware_takeoff(catlin_model_ro)
            if row["scope"] == "sheathing nails"}
    # The subfloor reads its joists' 16": 7 support lines, 2 x 9 edge + 5 x 5 field.
    assert "43 per 4x8 sheet over 16 in o.c." in rows["WSV212S"]["basis"]
    assert set(rows["WSV212S"]["by_storey"]) == {"main", "second", "attic"}
    # Dry SPF walls bill the bright nail; the HDG 8d stays on the garage diaphragms.
    assert "cdx-plywood: 78 per 4x10 sheet" in rows["8d common 0.131x2.5 bright"]["basis"]
    assert "cdx-plywood" not in rows["8d common 0.131x2.5"]["basis"]


def test_hl_site_bolt_lengths_match_the_hand_note(catlin_model_ro):
    """houses/catlin/notes/hl_site_bolts.md §3."""
    rows = {row["part_number"]: row["count"] for row in hardware_takeoff(catlin_model_ro)
            if row["scope"] == "connector site bolts"}
    assert rows == {"BOLT-34X8-HDG": 2, "BOLT-12X5-HDG": 2,
                    "LAG-34X5-HDG": 2, "LAG-12X5-HDG": 2}


def test_every_catlin_trim_schedule_bills(catlin_model_ro):
    """An authored ``trim_fastening`` that counts nothing would print on S-001 unbilled."""
    rows = {row["part_number"]: row for row in hardware_takeoff(catlin_model_ro)
            if row["scope"] == "trim fasteners"}
    authored = {m.trim_fastening.part for m in catlin_model_ro.plan.library.materials
                if m.trim_fastening is not None}
    assert authored == set(rows)
    # D-B-SUNKEN's Trex box: two 82" sides (6 x 2) and a 63" head (5 x 2).
    assert rows["T08175FS75"]["count"] == 34


def test_trim_window_and_bolt_fasteners_survive_treated_wood(catlin_model_ro):
    """R317.3.1: anything that may land in treated wood is HDG or stainless; a bright
    sheathing nail never lands on a treated stud."""
    roles = {ROLE_TRIM_FASTENER, ROLE_WINDOW_INSTALL_FASTENER, ROLE_SITE_BOLT, ROLE_SITE_LAG}
    for item in structural_hardware_catalog():
        if item.role in roles:
            assert item.finish in _TREATED_OK, item.model
    materials = {m.tag: m for m in catlin_model_ro.plan.library.materials}
    for wall in catlin_model_ro.walls:
        assembly = catlin_model_ro.plan.library.resolve_assembly(wall.assembly)
        index = assembly.structure_index() if assembly else None
        if index is None:
            continue
        layers = assembly.layers
        # The studs the sheathing nails into, after any per-wall material swap.
        studs = next((r.material_ref for r in wall.layers if r.name == layers[index].name),
                     layers[index].material_ref)
        treated = getattr(materials.get(studs), "preservative_treated", False)
        for layer in layers:
            if treated and layer.nailing is not None:
                nail = hardware_by_model(layer.nailing.part)
                assert nail is not None and nail.finish != "bright", wall.tag


def test_special_fastening_folds_code_rows_and_lists_the_rest(catlin_model_ro):
    from typehaus.emit.draw.schedules.special_fastening import special_fastening_block

    lines = special_fastening_block(catlin_model_ro)
    assert lines[0] == ("SHEATHING AND SUBFLOOR NAILING PER IRC 2018 TABLE R602.3(1) ITEM 31 / "
                        "IRC 2018 TABLE R602.3(3) UNLESS LISTED")
    # The code-row schedules (walls, garage diaphragms) fold into that one line.
    assert not any("8d common" in line for line in lines)
    assert any("RSRS-01" in line for line in lines)
    assert any("WSV212S" in line for line in lines)
