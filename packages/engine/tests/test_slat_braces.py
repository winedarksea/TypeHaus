"""SlatBrace: a framed band of 45° slats, each a knee brace — layout, members, bill, IFC.

The frame is catlin's west band (``notes/canopy_west_band.md`` §3a) on a bare two-post frame,
so the layout numbers are the note's: 24.375" x 25.125" bays, seven slats a bay at 2 1/4"
clear, j = 0 screwed infill, four braces across mid-band.
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
        for x, y, z in solid.profile:
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
