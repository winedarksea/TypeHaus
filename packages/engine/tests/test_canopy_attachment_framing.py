"""The declared connections require real wood at both nail groups and at every plate."""

from dataclasses import replace

import pytest

from typehaus.engineering.item import Status
from typehaus.engineering.lateral_system import compute
from typehaus.emit.draw.roofframingplan import build_roof_framing_schedule, roof_framing_notes
from typehaus.engineering.nail_yield import nail_single_shear_lb
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


def test_standard_sheet_edges_have_backing_in_every_bay_the_sheets_reach(catlin_model_ro):
    roofs = {r.tag: r for r in catlin_model_ro.roofs}
    canopy = roofs["RF-BW-CANOPY"]
    spec = catlin_model_ro.plan.by_tag(canopy.tag).diaphragm
    assert spec.panel_edge_blocking.module.inches * roof_slope_factor(canopy) <= 48
    stations_in = (81, 126, 171, 216, 261, 306, 351)
    # Three canopy bays, and RF-GARAGE's first bay, where the continuous first course ends.
    bays_in = (("RF-BW-CANOPY", 448, 470.5), ("RF-BW-CANOPY", 472, 494.5),
               ("RF-BW-CANOPY", 496, 518.625), ("RF-GARAGE", 520.125, 541.875))
    for station in stations_in:
        for tag, lo, hi in bays_in:
            assert any(
                block.category == "blocking" and block.material == "spf"
                and block.profile == "2x4"
                and block.p0[0] == pytest.approx(station * M_PER_IN)
                and block.p0[1] == pytest.approx(lo * M_PER_IN)
                and block.p1[1] == pytest.approx(hi * M_PER_IN)
                for block in roofs[tag].members
            ), (station, tag, lo, hi)


def test_no_strap_at_the_ridge_and_the_end_straps_centre_on_the_lsl_blocks(catlin_model_ro):
    plan = catlin_model_ro.plan
    assert plan.by_tag("CN-BW-JOINT-4") is None
    canopy = next(r for r in catlin_model_ro.roofs if r.tag == "RF-BW-CANOPY")
    blocks = {m.child_key: m for m in canopy.members}
    for strap, block, header_face_in in (("CN-BW-JOINT-1", "collector-block-BM-BW-RW-002", 74.75),
                                         ("CN-BW-JOINT-7", "collector-block-BM-BW-RE-002", 357.25)):
        member = blocks[block]
        assert member.profile == "3.5x16 LSL" and member.material == "lsl"
        assert plan.by_tag(strap).position.xy_m[0] == pytest.approx(member.p0[0])
        # Flush with the header's inboard face, where its plate is.
        faces = (member.p0[0] - 1.75 * M_PER_IN, member.p0[0] + 1.75 * M_PER_IN)
        assert any(f == pytest.approx(header_face_in * M_PER_IN) for f in faces)


@pytest.mark.parametrize("problem", ["absent", "raised", "too_thin", "unrated_wood"])
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
                # LVL publishes no specific gravity in the library: no strap row reads it.
                "unrated_wood": {"material": "lvl"},
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


def test_removing_the_east_plate_leaves_the_east_chord_unconnected(catlin_ctx):
    plan = catlin_ctx.plan
    elements = {storey: tuple(e for e in items if e.tag != "CN-BW-EAVE-E")
                for storey, items in plan.elements.items()}
    context = replace(catlin_ctx.engineering.context,
                      plan=plan.model_copy(update={"elements": elements}))
    record = next(r for r in compute(context) if r.item_id == "lateral_system/RF-BW-CANOPY")
    assert record.status is Status.INCOMPLETE
    assert any(m.startswith("BM-BW-RE: a rated plate joining it") for m in record.missing)


def test_the_chord_plates_carry_the_chord_force_and_the_west_collector_share(catlin_ctx):
    record = next(r for r in compute(catlin_ctx.engineering.context)
                  if r.item_id == "lateral_system/RF-BW-CANOPY")
    states = {s.name: s for s in record.limit_states}
    # canopy_west_band.md §6: 87.3 / 2 + 174.2 west, 87.3 east, both against 450.
    west = states["BM-BW-RW chord into CN-BW-JOINT-1's block"]
    east = states["BM-BW-RE chord into CN-BW-JOINT-7's block"]
    assert west.demand == pytest.approx(217.8, abs=0.1)
    assert east.demand == pytest.approx(87.3, abs=0.1)
    assert east.capacity == pytest.approx(450)


def test_nail_yield_reproduces_the_hand_calculation():
    # canopy_garage_diaphragm.md §3b: 8d common through 3/4in Structural I.
    assert nail_single_shear_lb(0.131, 0.75, 1.75, 0.50, 0.42, 100_000) == (
        pytest.approx(84.38, abs=0.01), "IIIs")
    assert nail_single_shear_lb(0.131, 0.75, 1.75, 0.50, 0.50, 100_000) == (
        pytest.approx(90.12, abs=0.01), "IIIs")


def test_nailers_read_their_own_nails_at_their_own_species(catlin_ctx):
    record = next(r for r in compute(catlin_ctx.engineering.context)
                  if r.item_id == "lateral_system/RF-BW-CANOPY")
    states = {s.name: s for s in record.limit_states}
    # §3b: 9 x 135.00 SPF, 9 x 144.19 LSL, 8 x 135.00 SPF; 262.06 lb each.
    for name, capacity in (("CN-BW-JOINT-2 RF-BW-CANOPY", 1215.0),
                           ("CN-BW-JOINT-1 RF-BW-CANOPY", 1297.7),
                           ("CN-BW-JOINT-2 RF-GARAGE", 1080.0)):
        state = states[f"{name} nailer into deck"]
        assert state.capacity == pytest.approx(capacity, abs=0.1)
        assert state.demand == pytest.approx(262.06, abs=0.05)


def test_added_framing_and_fasteners_are_billed(catlin_model_ro):
    rows = {row["scope"]: row for row in diaphragm_attachment_rows(catlin_model_ro)}
    # 6 LSL blocks + 4 canopy and 6 garage nailers, an angle at each end.
    assert rows["diaphragm blocking end angles"]["count"] == 32
    assert rows["diaphragm blocking end angles"]["role"] == "diaphragm_blocking_end_tie"
    assert rows["diaphragm blocking end angles"]["part_number"] == "LS30Z"
    assert rows["diaphragm blocking angle nails"]["count"] == 32 * 6
    assert rows["diaphragm joint strap nails"]["count"] == 6 * 12
    # 4 x 18 canopy + 6 x 16 garage + 2 x 18 on the end LSL blocks.
    # 4 x 18 + 6 x 16 + 2 x 18 deck, 10 x 5 lamination, 28 x 6 toenails: one bid line.
    nails = rows["diaphragm 8d nails"]
    assert nails["count"] == 204 + 10 * 5 + 28 * 6
    assert "204 deck-to-nailer" in nails["basis"] and "168 panel-edge" in nails["basis"]
    assert "six outermost" in rows["diaphragm joint strap nails"]["basis"]


def test_roof_sheets_separate_stock_sizes_and_print_both_attachments(catlin_model_ro):
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-BW-CANOPY")
    rows = {row[1]: row for row in build_roof_framing_schedule(catlin_model_ro, roof).rows}
    for label, profile, quantity in (
        ("COLLECTOR BLOCK", "3.5x16 LSL", "6"),
        ("JOINT NAILER", "2-2x6", "4"),
        ("PANEL EDGE BLOCK", "2x4", "21"),
    ):
        assert rows[label][2] == profile
        assert rows[label][4] == quantity
    for roof in catlin_model_ro.roofs:
        if roof.tag in ("RF-BW-CANOPY", "RF-GARAGE"):
            notes = " ".join(roof_framing_notes(catlin_model_ro, roof))
            assert "six outermost 0.148x2.5in HDG nails per leg" in notes
            assert "no sheathing break" in notes
            assert "12/18" in notes
            assert "PANEL EDGE BLOCKS" in notes
            assert ("IN THE FIRST BAY, FROM RF-BW-CANOPY" in notes) == (roof.tag == "RF-GARAGE")
