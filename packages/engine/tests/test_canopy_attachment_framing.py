"""The declared connections require real wood at both nail groups and at every plate."""

from dataclasses import replace

import pytest

from typehaus.engineering.item import Status
from typehaus.engineering.lateral_system import compute
from typehaus.emit.draw.roofframingplan import build_roof_framing_schedule, roof_framing_notes
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_ir import GSweep
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.roof_geometry import roof_height_at, roof_slope_factor
from typehaus.takeoff.diaphragm_attachments import diaphragm_attachment_rows


def _record_with_roof(catlin_ctx, roof):
    model = replace(
        catlin_ctx.model, roofs=[roof if r.tag == roof.tag else r for r in catlin_ctx.model.roofs]
    )
    context = replace(catlin_ctx.engineering.context, model=model)
    return next(r for r in compute(context) if r.item_id == "lateral_system/RF-BW-CANOPY")


def test_bevels_contact_the_deck_and_clear_the_existing_trusses(catlin_model_ro):
    for roof in catlin_model_ro.roofs:
        if roof.tag not in ("RF-BW-CANOPY", "RF-GARAGE"):
            continue
        blocks = [m for m in roof.members if m.category == "blocking"]
        assert blocks
        trusses = [m for m in roof.members if m.category == "roof_truss"]
        for block in blocks:
            solid = member_solid(block)
            assert isinstance(solid, GSweep)
            top = solid.profile[2:]
            assert all(p[2] == pytest.approx(roof_height_at(roof, p[:2])) for p in top)
            assert all(
                not (
                    block.p0[1] < t.p0[1] + 0.75 * M_PER_IN - 1e-8
                    and block.p1[1] > t.p0[1] - 0.75 * M_PER_IN + 1e-8
                )
                for t in trusses
            ), block.child_key


def test_standard_sheet_edges_have_backing_in_every_canopy_bay(catlin_model_ro):
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-BW-CANOPY")
    spec = catlin_model_ro.plan.by_tag(roof.tag).diaphragm
    assert spec.panel_width.inches * roof_slope_factor(roof) <= 48
    stations_in = (81, 126, 171, 216, 261, 306, 351)
    bays_in = ((448, 470.5), (472, 494.5), (496, 518.625))
    for station in stations_in:
        for lo, hi in bays_in:
            assert any(
                block.category == "blocking"
                and block.p0[0] == pytest.approx(station * M_PER_IN)
                and block.p0[1] == pytest.approx(lo * M_PER_IN)
                and block.p1[1] == pytest.approx(hi * M_PER_IN)
                for block in roof.members
            ), (station, lo, hi)


@pytest.mark.parametrize("problem", ["absent", "raised", "too_thin", "wrong_species"])
def test_a_bad_garage_nailer_keeps_the_permit_path_incomplete(catlin_ctx, problem):
    roof = next(r for r in catlin_ctx.model.roofs if r.tag == "RF-GARAGE")
    key = "joint-nailer-CN-BW-JOINT-6-north"
    changed = []
    for member in roof.members:
        if member.child_key != key:
            changed.append(member)
        elif problem != "absent":
            changes = {
                "raised": {"z0_m": member.z0_m + M_PER_IN, "z1_m": member.z1_m + M_PER_IN},
                "too_thin": {"section_ring": None, "z0_m": member.z1_m - M_PER_IN},
                "wrong_species": {"material": "spf"},
            }
            changed.append(replace(member, **changes[problem]))
    record = _record_with_roof(catlin_ctx, replace(roof, members=tuple(changed)))
    assert record.status is Status.INCOMPLETE
    assert any("CN-BW-JOINT-6: RF-GARAGE longitudinal" in m for m in record.missing)


def test_removing_one_collector_block_names_both_unbacked_plates(catlin_ctx):
    roof = next(r for r in catlin_ctx.model.roofs if r.tag == "RF-BW-CANOPY")
    changed = replace(
        roof,
        members=tuple(m for m in roof.members if m.child_key != "collector-block-BM-BW-RW-001"),
    )
    record = _record_with_roof(catlin_ctx, changed)
    assert record.status is Status.INCOMPLETE
    assert all(any(f"CN-BW-EAVE-{i}: eave blocking" in m for m in record.missing) for i in (3, 4))


def test_added_framing_and_fasteners_are_billed(catlin_model_ro):
    rows = {row["scope"]: row for row in diaphragm_attachment_rows(catlin_model_ro)}
    assert rows["diaphragm blocking end angles"]["count"] == 36
    assert rows["diaphragm blocking end angles"]["role"] == "diaphragm_blocking_end_tie"
    assert rows["diaphragm blocking end angles"]["part_number"] == "LS30"
    assert rows["diaphragm blocking angle nails"]["count"] == 36 * 6
    assert rows["diaphragm joint strap nails"]["count"] == 7 * 12
    assert rows["diaphragm joint nailer deck nails"]["count"] == 238
    assert "six outermost" in rows["diaphragm joint strap nails"]["basis"]


def test_roof_sheets_separate_stock_sizes_and_print_both_attachments(catlin_model_ro):
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-BW-CANOPY")
    rows = {row[1]: row for row in build_roof_framing_schedule(catlin_model_ro, roof).rows}
    for label, profile, quantity in (
        ("COLLECTOR BLOCK", "5.5x15.5", "6"),
        ("JOINT NAILER", "3.5x5.5", "5"),
        ("PANEL EDGE BLOCK", "2x4", "20"),
    ):
        assert rows[label][2] == profile
        assert rows[label][4] == quantity
    for roof in catlin_model_ro.roofs:
        if roof.tag in ("RF-BW-CANOPY", "RF-GARAGE"):
            notes = " ".join(roof_framing_notes(catlin_model_ro, roof))
            assert "six outermost 0.148x2.5in nails per leg" in notes
            assert "no sheathing break" in notes
            assert "12/18" in notes
