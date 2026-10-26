"""SlatBrace: a framed band of 45° slats, each a knee brace — layout, members, bill, IFC.

The frame is catlin's former chevron (``notes/canopy_west_band.md`` §8) on a bare frame,
so the layout numbers are the note's: 24.375" x 25.125" bays, seven slats a bay at 2 1/4"
clear, j = 0 screwed infill, four braces across mid-band. Single-brace tests use the
2026-10-25 §3 geometry with paired connectors on flush 4x6 faces.
"""

from __future__ import annotations

import math

import pytest

from typehaus.model import ft, inch, pt

FT = 0.3048
IN = 0.0254
_SPAN_FT = 42.47917 - 37.5  # PT-BW-CW to PT-BW-CNW
_BASE_FT, _TOP_FT = 4.0, 6.34375


def _band(**overrides):
    from typehaus.model import SlatBrace

    fields = dict(uid="SLB0000A01", tag="SB-T", start=pt(ft(0), ft(0)),
                  end=pt(ft(_SPAN_FT), ft(0)), base_elevation=ft(_BASE_FT),
                  top_elevation=ft(_TOP_FT), plane_offset=inch(1.0), assembly="WOOD")
    fields.update(overrides)
    return SlatBrace(**fields)


def _frame(band):
    from typehaus.model import (
        Assembly,
        Building,
        Layer,
        LayerFunction,
        Library,
        Material,
        PlanModel,
        Project,
        Site,
        Storey,
        degF,
    )
    from typehaus.resolve import resolve

    materials = (Material(tag="spf", name="SPF framing", r_per_inch=1.25, perm_rating=2.9),)
    assemblies = (Assembly(tag="WOOD", layers=(
        Layer(name="w", material_ref="spf", thickness=inch(1.5),
              function=LayerFunction.STRUCTURE),)),)
    project = Project(name="SL", project_uuid="00000000-0000-4000-8000-0000000000c2",
                      site=Site(lat=44.9, lon=-93.2, elevation=ft(830),
                                design_temp_heating=degF(-15), design_temp_cooling=degF(90)),
                      building=Building(name="SL"))
    storey = Storey(uid="ST000000c2", tag="main", elevation=ft(0), default_ceiling_height=ft(9))
    plan = PlanModel(project=project,
                     library=Library(materials=materials, assemblies=assemblies),
                     storeys=(storey,), elements={"main": (band,)})
    return resolve(plan)


@pytest.fixture(scope="module")
def band_model():
    model, _ = _frame(_band())
    return model


def test_the_layout_is_section_3a() -> None:
    from typehaus.resolve.slat_braces import slat_layout

    lay = slat_layout(_band())
    assert lay.width / IN == pytest.approx(24.375, abs=1e-3)
    assert lay.height / IN == pytest.approx(25.125, abs=1e-3)
    assert lay.pitch / IN == pytest.approx(3.75 * math.sqrt(2), abs=1e-6)
    for bay in (0, 1):
        slats = lay.bay(bay)
        assert [s.j for s in slats] == list(range(-3, 4))  # j = ±4 is 5.00", under 8"
        assert [s.j for s in slats if not s.braced] == [0]  # §3a-ter: a corner to corner
        assert lay.crossing_mid(bay) == 4
        assert min(s.length for s in slats) / IN == pytest.approx(12.5, abs=0.01)
        assert max(s.length for s in slats) / IN == pytest.approx(34.47, abs=0.01)
    lands = [(s.low, s.high) for s in lay.bay(0)]
    assert lands.count(("chord", "top")) == 3 and lands.count(("sill", "centre")) == 3
    assert ("chord", "centre") in lands


def test_the_bays_mirror_about_the_centre_post(band_model) -> None:
    """Every slat rises toward the centre: a chevron, symmetric about midspan."""
    brace, = band_model.braces
    mid = _SPAN_FT * FT / 2
    rising = {}
    for m in brace.members:
        if m.category != "brace":
            continue
        assert m.z0_end_m > m.z0_m  # p0 is the low end
        rising[m.child_key] = (abs(m.p1[0] - mid) < abs(m.p0[0] - mid), m.p0[0], m.p1[0])
    assert all(toward for toward, _a, _b in rising.values())
    for j in range(-3, 4):
        _t, a0, a1 = rising[f"slat-0{j:+d}"]
        _t, b0, b1 = rising[f"slat-1{j:+d}"]
        assert a0 + b0 == pytest.approx(2 * mid) and a1 + b1 == pytest.approx(2 * mid)


def test_members_stay_in_their_bay(band_model) -> None:
    """Plates at each end, the slats between them and clear of both, flush with one face."""
    brace, = band_model.braces
    by_key = {m.child_key: m for m in brace.members}
    assert by_key["plate-sill"].z0_m == pytest.approx(_BASE_FT * FT)
    assert by_key["plate-top"].z1_m == pytest.approx(_TOP_FT * FT)
    assert by_key["post-centre"].p0 == pytest.approx((_SPAN_FT * FT / 2, 0.0))
    sill_top, top_under = by_key["plate-sill"].z1_m, by_key["plate-top"].z0_m
    slats = [m for m in brace.members if m.category == "brace"]
    assert len(slats) == 14
    for m in slats:
        assert m.z0_m >= sill_top - 1e-9 and m.z1_end_m <= top_under + 1e-9
        assert m.p0[1] == pytest.approx(IN) and m.plan_width_m == pytest.approx(3.5 * IN)


def test_the_slats_bill_as_lumber_and_the_parts_as_hardware(band_model) -> None:
    from typehaus.takeoff.framing import framing_takeoff
    from typehaus.takeoff.hardware import hardware_takeoff

    lumber = {(r["profile"], r["category"]): r for r in framing_takeoff(band_model)}
    assert lumber[("2x4", "brace")]["pieces"] == 14
    rows = {r["scope"]: r for r in hardware_takeoff(band_model)
            if r["scope"].startswith("slat brace")}
    assert rows["slat brace connector"]["count"] == 24
    assert rows["slat brace connector"]["part_number"] == "KBS1Z"
    assert rows["slat brace infill screw"]["count"] == 8  # 2 slats x 2 ends x 2
    assert rows["slat brace plate screw"]["count"] == 16
    assert rows["slat brace centre post tie"]["count"] == 4


def test_a_corner_slat_is_screwed_infill(band_model) -> None:
    """§3a-ter: j = 0's KBS1Z legs would run into both plates, so it takes toe screws, no
    connector, and every connector on a post stays inside the bay's height."""
    from typehaus.resolve.slat_braces import slat_layout

    layout = slat_layout(_band())
    members = {m.child_key: m for m in band_model.braces[0].members}
    assert members["slat-0+0"].connection == "screwed:SDWS22300DB"
    assert members["slat-1-1"].connection == "kneebrace:KBS1Z"
    tags = {s.tag for s in band_model.solids if s.product == "KBS1Z"}
    assert not any("~0+0~" in t or "~1+0~" in t for t in tags)
    sill = _BASE_FT * FT + layout.plate
    on_post = {f"~{s.bay}{s.j:+d}~{end}" for s in layout.slats
               for end, landing in (("low", s.low), ("high", s.high))
               if landing in ("chord", "centre")}
    posted = [s for s in band_model.solids if s.product == "KBS1Z"
              and any(s.tag.endswith(k) for k in on_post)]
    assert len(posted) == 12  # j = -3 ... -1 at a chord, +1 ... +3 at the centre, two bays
    for solid in posted:
        assert sill - 1e-6 <= solid.z0_m and solid.z1_m <= sill + layout.height + 1e-6


def test_neighbouring_connectors_need_their_heel_spacing() -> None:
    """At the old 1 1/2" gap every pair of KBS1Z overlapped (note §3a): the resolver refuses."""
    from typehaus.resolve.kbs_geometry import kbs_heel_spacing
    from typehaus.resolve.slat_braces import slat_layout

    assert kbs_heel_spacing() / IN == pytest.approx(3.0 + 1.5 * math.sqrt(2))
    assert slat_layout(_band()).pitch >= kbs_heel_spacing()
    model, findings = _frame(_band(clear_gap=inch(1.5)))
    assert not model.braces
    assert [f.check_id for f in findings] == ["integrity.slat_brace"]
    assert "would overlap" in findings[0].message


def test_an_unread_centre_post_is_a_missing_row_not_a_number() -> None:
    from typehaus.engineering.lateral_band_slats import SlatBand, _centre_post
    from typehaus.resolve.slat_braces import slat_layout

    el = _band(centre_post="4x4")
    lay = slat_layout(el)
    states, missing = [], []
    _centre_post(el, lay, SlatBand(el, lay, 1045.06, lay.crossing_mid(0)), states, missing)
    assert not states and "4x4" in missing[0]


def test_the_band_emits_slats_as_ifc_braces(band_model, tmp_path) -> None:
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc.emitter import emit_ifc

    path = emit_ifc(band_model, tmp_path / "band.ifc")
    emitted = ifcopenshell.open(str(path))
    members = {m.Name: m for m in emitted.by_type("IfcMember")}
    assert members["SB-T/slat-0+0"].PredefinedType == "BRACE"
    assert members["SB-T/plate-top"].PredefinedType == "MEMBER"
    assert len(emitted.by_type("IfcMechanicalFastener")) == 24
    assert all(c.Representation for c in emitted.by_type("IfcMechanicalFastener"))
    assert all(c.Representation.Representations[0].RepresentationType == "Tessellation"
               for c in emitted.by_type("IfcMechanicalFastener"))
    assert members["SB-T/slat-0-2"].Representation.Representations[0].RepresentationType == (
        "SweptSolid")


def test_top_landings_are_not_the_crossing_slats() -> None:
    """Top-only connectors would leave two of the four graded slats untied in each bay."""
    from typehaus.resolve.slat_braces import slat_layout

    layout = slat_layout(_band())
    for bay in (0, 1):
        top = [s for s in layout.bay(bay) if s.high == "top"]
        mid = layout.height / 2.0
        assert len(top) == 3
        assert sum(s.u0 <= s.c + mid <= s.u1 for s in top) == 2
        assert layout.crossing_mid(bay) == 4


def test_actual_slat_faces_meet_the_frame_without_interpenetration(band_model) -> None:
    from typehaus.resolve.geometry_ir import GSweep
    from typehaus.resolve.geometry_members import member_solid
    from typehaus.resolve.slat_braces import slat_layout

    layout = slat_layout(_band())
    sill = _BASE_FT * FT + layout.plate
    ceiling = sill + layout.height
    members = {m.child_key: m for m in band_model.braces[0].members}
    for slat in layout.slats:
        member = members[f"slat-{slat.bay}{slat.j:+d}"]
        solid = member_solid(member)
        assert isinstance(solid, GSweep)
        for x, _y, z in solid.profile:
            assert sill - 1e-9 <= z <= ceiling + 1e-9
            station = (x - layout.chord_face if slat.bay == 0
                       else layout.length - layout.chord_face - x)
            assert -1e-9 <= station <= layout.width + 1e-9
        if slat.low == "sill":
            assert sum(abs(z - sill) < 1e-9 for _, _, z in solid.profile) == 2
        if slat.high == "top":
            assert sum(abs(z - ceiling) < 1e-9 for _, _, z in solid.profile) == 2
        assert member.cut_length_m > member.length_m
    # The middle board also meets both plates at its clipped long points.
    assert len(members["slat-0+0"].elevation_profile) == 6


def test_lumber_nests_the_miter_blanks(band_model) -> None:
    from typehaus.takeoff.framing import framing_takeoff

    members = [m for m in band_model.braces[0].members if m.category == "brace"]
    row = next(r for r in framing_takeoff(band_model) if r["category"] == "brace")
    assert row["cut_length_ft"] == round(sum(m.cut_length_m for m in members) / FT, 1)
    assert row["cut_length_ft"] > round(sum(m.length_m for m in members) / FT, 1)


@pytest.mark.parametrize("offset", [1.0, -1.0])
def test_connectors_follow_the_flush_face_on_a_rotated_band(offset) -> None:
    """The catlin south-to-north run makes positive offset the west face."""
    element = _band(start=pt(ft(8), ft(10)), end=pt(ft(8), ft(10 + _SPAN_FT)),
                    plane_offset=inch(offset))
    model, _ = _frame(element)
    connectors = [s for s in model.solids if s.product == "KBS1Z"]
    assert len(connectors) == 24 and len({s.uid for s in connectors}) == 24
    assert all(s.derived and s.body_mesh for s in connectors)
    face_x = 8 * FT - math.copysign(2.75 * IN, offset)
    for connector in connectors:
        xs = [x for x, _, _ in connector.body_mesh.positions]
        # Exterior face leaves are at the actual west/east face, not at the slat axis.
        assert any(abs(x - face_x) < 1e-9 for x in xs)
        assert max(xs) - min(xs) < 1.6 * IN


def test_connector_geometry_is_serialized_and_does_not_double_bill(band_model) -> None:
    from typehaus.emit.gltf.emitter import emit_gltf_dict
    from typehaus.server.model_json import model_to_dict
    from typehaus.takeoff.framing import structural_solids_takeoff

    payload = model_to_dict(band_model)
    connectors = [s for s in payload["solids"] if s["product"] == "KBS1Z"]
    assert len(connectors) == 24
    assert all(s["body_mesh"]["triangles"] for s in connectors)
    assert not any(r["category"] == "connector" for r in structural_solids_takeoff(band_model))
    gltf, _ = emit_gltf_dict(band_model, lod="framed")
    connector_uids = {s["uid"] for s in connectors}
    assert connector_uids <= {n.get("extras", {}).get("uid") for n in gltf["nodes"]}


def test_punched_kbs_cells_are_closed_steel_not_flat_markers() -> None:
    from collections import Counter

    from typehaus.resolve.kbs_geometry import KBS_GEOMETRY, kbs_mesh

    r = math.sqrt(2)
    mesh = kbs_mesh((0, 0, 0), (0, 0, -1), (-1, 0, 0),
                    (1 / r, 0, 1 / r), (-1 / r, 0, 1 / r), (0, -1, 0))
    edges = Counter(tuple(sorted(edge)) for a, b, c in mesh.triangles
                    for edge in ((a, b), (b, c), (c, a)))
    assert set(edges.values()) == {2}
    assert max(y for _, y, _ in mesh.positions) == pytest.approx(KBS_GEOMETRY.steel_thickness_m)
    assert min(y for _, y, _ in mesh.positions) == pytest.approx(-KBS_GEOMETRY.flange_width_m)


def _single_band(**overrides):
    fields = dict(slat="4x6", plane_offset=inch(0), brace_offset=inch(-6.5),
                  connectors_per_end=2, clear_gap=inch(0))
    fields.update(overrides)
    return _band(**fields)


def test_single_brace_geometry_and_both_flush_faces() -> None:
    from typehaus.resolve.slat_braces import slat_layout
    from typehaus.takeoff.framing import framing_takeoff
    from typehaus.takeoff.hardware import hardware_takeoff

    element = _single_band(start=pt(ft(8), ft(10)),
                           end=pt(ft(8), ft(10 + _SPAN_FT)))
    layout = slat_layout(element)
    assert len(layout.slats) == 2
    from typehaus.resolve.framing.profiles import cross_section

    assert cross_section(element.slat).width_m / IN == pytest.approx(3.5)
    for bay in (0, 1):
        slat, = layout.bay(bay)
        assert slat.c / IN == pytest.approx(-6.5)
        assert slat.length / IN == pytest.approx(18.625 * math.sqrt(2))
        assert (slat.low, slat.high, slat.braced) == ("chord", "top", True)
        assert layout.crossing_mid(bay) == 1
    model, findings = _frame(element)
    assert not findings
    connectors = [s for s in model.solids if s.product == "KBS1Z"]
    assert len(connectors) == len({s.uid for s in connectors}) == 8
    assert len({s.tag for s in connectors}) == 8
    for side in (-1, 1):
        face_x = 8 * FT + side * 2.75 * IN
        on_face = [s for s in connectors if any(abs(x - face_x) < 1e-9
                   for x, _, _ in s.body_mesh.positions)]
        assert len(on_face) == 4
    hardware = next(r for r in hardware_takeoff(model) if r["scope"] == "slat brace connector")
    assert hardware["count"] == 8
    assert hardware["role"] == "knee_brace_equal_width"
    lumber = next(r for r in framing_takeoff(model) if r["category"] == "brace")
    assert lumber["profile"] == "4x6" and lumber["pieces"] == 2


@pytest.mark.parametrize("overrides", [dict(slat="4x4"), dict(chord_size="4x4"),
                                          dict(plate="2x4"),
                                          dict(centre_post="4x4"), dict(plane_offset=inch(1))])
def test_type_one_requires_both_faces_flush(overrides) -> None:
    model, findings = _frame(_single_band(**overrides))
    assert not model.braces
    assert findings[0].check_id == "integrity.slat_brace"
    assert "equal-width" in findings[0].message


@pytest.mark.parametrize("offset", [-6.0, 0, 100])
def test_explicit_brace_with_unbuildable_connector_is_refused(offset) -> None:
    model, findings = _frame(_single_band(brace_offset=inch(offset)))
    assert not model.braces
    assert findings[0].check_id == "integrity.slat_brace"
    assert "brace_offset" in findings[0].message


def test_type_one_capacity_is_a_joint_rating_and_preserves_type_two() -> None:
    from typehaus.hardware.catalog import (
        ROLE_KNEE_BRACE,
        ROLE_KNEE_BRACE_EQUAL_WIDTH,
        allowable_for_model,
        hardware_for_role,
    )

    assert allowable_for_model("KBS1Z", role=ROLE_KNEE_BRACE).lateral_f1_lb == 540
    assert allowable_for_model("KBS1Z", role=ROLE_KNEE_BRACE_EQUAL_WIDTH).lateral_f1_lb == 1010
    assert hardware_for_role(ROLE_KNEE_BRACE_EQUAL_WIDTH).model == "KBS1Z"


def test_chord_push_uses_its_landing_and_empty_centre_has_zero_demand() -> None:
    from typehaus.engineering.lateral_band_slats import SlatBand, _centre_post
    from typehaus.resolve.slat_braces import slat_layout

    element = _single_band()
    layout = slat_layout(element)
    band = SlatBand(element, layout, 1038.35, 1)
    assert band.chord_landing_ft == pytest.approx(4 + (1.5 + 6.5) / 12)
    assert band.chord_push_lb() == pytest.approx(519.175)
    assert band.couple_lb_ft() == pytest.approx(519.175 * 2 * 8.5 / 12, abs=0.01)
    states, missing = [], []
    _centre_post(element, layout, band, states, missing)
    assert not missing and all(state.demand == 0 for state in states)


def test_true_corner_braces_resolve_both_corners_and_eight_flush_connectors() -> None:
    from typehaus.resolve.slat_braces import slat_layout
    from typehaus.resolve.slat_cuts import clipped_slat_profile
    from typehaus.takeoff.hardware import hardware_takeoff

    element = _single_band(corner_to_corner=True, brace_offset=None)
    layout = slat_layout(element)
    model, findings = _frame(element)
    assert not findings
    assert len(model.solids) == 8
    for slat in layout.slats:
        assert slat.slope == pytest.approx(layout.height / layout.width)
        assert slat.length == pytest.approx(math.hypot(layout.width, layout.height))
        profile = clipped_slat_profile(slat, layout, 3.5 * IN)
        assert any(u == pytest.approx(0) and z == pytest.approx(0) for u, z in profile)
        assert any(u == pytest.approx(layout.width) and z == pytest.approx(layout.height)
                   for u, z in profile)
        member = next(m for m in model.braces[0].members
                      if m.child_key == f"slat-{slat.bay}+0")
        assert member.cut_length_m == pytest.approx(slat.length)
    hardware = next(r for r in hardware_takeoff(model) if r["scope"] == "slat brace connector")
    assert hardware["count"] == 8
    assert layout.crossing_mid(0) == layout.crossing_mid(1) == 1


@pytest.mark.parametrize("low", ["chord", "sill"])
@pytest.mark.parametrize("high", ["top", "centre"])
def test_tighter_corner_bends_bear_on_real_wood_for_either_support_face(low, high) -> None:
    from dataclasses import replace

    from shapely.geometry import LineString, Polygon, box

    from typehaus.resolve.kbs_geometry import KBS_GEOMETRY
    from typehaus.resolve.slat_braces import slat_layout
    from typehaus.resolve.slat_connector_landings import slat_connector_ends
    from typehaus.resolve.slat_cuts import clipped_slat_profile

    layout = slat_layout(_single_band(corner_to_corner=True, brace_offset=None))
    slat = replace(layout.bay(0)[0], low=low, high=high)
    brace = Polygon(clipped_slat_profile(slat, layout, 3.5 * IN)).buffer(1e-10)
    w, h, p = layout.width, layout.height, layout.plate
    supports = {"chord": box(-2 * layout.chord_face, 0, 0, h),
                "centre": box(w, 0, w + 2 * layout.centre_half, h),
                "sill": box(0, -p, w, 0), "top": box(0, h, w, h + p)}
    leg, flange = KBS_GEOMETRY.leg_length_m, KBS_GEOMETRY.flange_width_m
    for placement in slat_connector_ends(slat, 3.5 * IN):
        assert 0 < placement.included_angle_degrees < 90
        for wood, along, across in (
                (brace, placement.brace_axis, placement.brace_face),
                (supports[placement.landing].buffer(1e-10),
                 placement.support, placement.support_face)):
            leaf = Polygon([(placement.u + s * along[0] + t * across[0],
                             placement.z + s * along[1] + t * across[1])
                            for s, t in ((0, 0), (leg, 0), (leg, flange), (0, flange))])
            assert wood.covers(leaf)
            assert wood.covers(LineString([
                (placement.u, placement.z),
                (placement.u + leg * along[0], placement.z + leg * along[1])]))


def test_corner_geometry_does_not_inherit_the_open_knee_connection_rating() -> None:
    from types import SimpleNamespace

    from typehaus.engineering.lateral_band_slats import SlatBand, slat_rows
    from typehaus.resolve.slat_braces import slat_layout

    element = _single_band(corner_to_corner=True, brace_offset=None)
    layout = slat_layout(element)
    band = SlatBand(element, layout, 1038.35, 1)
    assert band.slat_lb == pytest.approx(519.175 * math.hypot(1, layout.height / layout.width))
    assert band.vertical_per_end_lb > band.per_end_lb
    states, notes, missing, inputs = [], [], [], []
    slat_rows(None, SimpleNamespace(tag="W"), SimpleNamespace(tag="HEADER"),
              band, states, notes, missing, inputs)
    assert not states
    assert "tightly bent KBS1Z" in missing[0]
    assert "included" in missing[0]
    assert "tab/fastener placement" in missing[0]
    assert "centre-post contact under compression" in notes[0]


def test_corner_layout_refuses_conflicting_offset_and_insufficient_connector_room() -> None:
    _, findings = _frame(_single_band(corner_to_corner=True))
    assert "alternative layouts" in findings[0].message
    model, findings = _frame(_single_band(corner_to_corner=True, brace_offset=None,
                                        end=pt(inch(14), inch(0))))
    assert not model.braces
    assert "leg runs off" in findings[0].message


def test_corner_draft_exports_cut_profiles_and_eight_connectors(tmp_path) -> None:
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.gltf.emitter import emit_gltf_dict
    from typehaus.emit.ifc.emitter import emit_ifc

    model, _ = _frame(_single_band(corner_to_corner=True, brace_offset=None))
    exported = ifcopenshell.open(str(emit_ifc(model, tmp_path / "corners.ifc")))
    assert len(exported.by_type("IfcMechanicalFastener")) == 8
    braces = [m for m in exported.by_type("IfcMember") if m.PredefinedType == "BRACE"]
    assert len(braces) == 2
    assert all(m.Representation.Representations[0].RepresentationType == "SweptSolid"
               for m in braces)
    gltf, _ = emit_gltf_dict(model, lod="framed")
    assert {s.uid for s in model.solids} <= {n.get("extras", {}).get("uid") for n in gltf["nodes"]}
