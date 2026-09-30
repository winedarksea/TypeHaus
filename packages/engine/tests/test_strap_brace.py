"""StrapBrace: a flat steel X-brace that resolves like a brace and bills as hardware."""

from __future__ import annotations

import math

import pytest

from typehaus.model import ft, inch, pt

FT = 0.3048
IN = 0.0254
_FACE_IN = 2.75            # half a 6x6: the strap is pushed onto the posts' +y face
_THK_IN = 0.0598           # 16 ga
_WIDTH_IN = 1.25
_LOW_FT, _HIGH_FT = 1.0, 7.0
_SPAN_FT = 8.0
_NAILS = 7


def _frame():
    """Two 6x6 posts, a beam, and two CS16 straps crossing between them (an X)."""
    from typehaus.model import (
        Assembly,
        Beam,
        Building,
        Layer,
        LayerFunction,
        Library,
        Material,
        Node,
        PlanModel,
        Post,
        Project,
        Site,
        Storey,
        StrapBrace,
        degF,
    )
    from typehaus.resolve import resolve

    materials = (Material(tag="spf", name="SPF framing", r_per_inch=1.25, perm_rating=2.9),)
    assemblies = (Assembly(tag="WOOD", layers=(
        Layer(name="w", material_ref="spf", thickness=inch(1.5),
              function=LayerFunction.STRUCTURE),)),)
    project = Project(name="SB", project_uuid="00000000-0000-4000-8000-0000000000c1",
                      site=Site(lat=44.9, lon=-93.2, elevation=ft(830),
                                design_temp_heating=degF(-15), design_temp_cooling=degF(90)),
                      building=Building(name="SB"))
    storey = Storey(uid="ST000000c1", tag="main", elevation=ft(0), default_ceiling_height=ft(9))
    strap = {"product": "CS16", "width": inch(_WIDTH_IN), "gauge": 16,
             "face_plane": inch(_FACE_IN), "fasteners_each_end": _NAILS,
             "fastener": '10d x 1-1/2" HDG', "connects": ("PT-SB-W", "PT-SB-E")}
    elements = [
        Node(uid="SBN0000W01", tag="N-SB-W", position=pt(ft(0), ft(0))),
        Node(uid="SBN0000E01", tag="N-SB-E", position=pt(ft(_SPAN_FT), ft(0))),
        Post(uid="SBP0000W01", tag="PT-SB-W", position=pt(ft(0), ft(0)), size="6x6",
             height=ft(8), assembly="WOOD"),
        Post(uid="SBP0000E01", tag="PT-SB-E", position=pt(ft(_SPAN_FT), ft(0)), size="6x6",
             height=ft(8), assembly="WOOD"),
        Beam(uid="SBB0000B01", tag="BM-SB", start_node="N-SB-W", end_node="N-SB-E",
             size="2-2x10", assembly="WOOD", top_elevation=ft(8 + 9.25 / 12),
             bearing_refs=("PT-SB-W", "PT-SB-E")),
        StrapBrace(uid="SBS0000A01", tag="SB-A", start=pt(ft(0), ft(0)),
                   start_elevation=ft(_LOW_FT), end=pt(ft(_SPAN_FT), ft(0)),
                   end_elevation=ft(_HIGH_FT), **strap),
        StrapBrace(uid="SBS0000B01", tag="SB-B", start=pt(ft(0), ft(0)),
                   start_elevation=ft(_HIGH_FT), end=pt(ft(_SPAN_FT), ft(0)),
                   end_elevation=ft(_LOW_FT), **strap),
    ]
    plan = PlanModel(project=project,
                     library=Library(materials=materials, assemblies=assemblies),
                     storeys=(storey,), elements={"main": tuple(elements)})
    model, findings = resolve(plan)
    return model, findings


@pytest.fixture(scope="module")
def strap_model():
    model, _ = _frame()
    return model


def _strap(model, tag="SB-A"):
    brace = next(b for b in model.braces if b.tag == tag)
    member, = brace.members
    return brace, member


def test_strap_resolves_to_one_thin_raked_member(strap_model) -> None:
    brace, m = _strap(strap_model)
    assert brace.kind == "strap" and m.category == "strap"
    # Plan: on the +y (left) face of the posts, the contact face at 2.75", body beyond it.
    y = (_FACE_IN + _THK_IN / 2) * IN
    assert m.p0 == pytest.approx((0.0, y)) and m.p1 == pytest.approx((_SPAN_FT * FT, y))
    assert m.plan_width_m == pytest.approx(_THK_IN * IN)
    # Elevation: centred on each end, vertical extent width / cos(theta).
    rise = (_HIGH_FT - _LOW_FT) * FT
    theta = math.atan2(rise, _SPAN_FT * FT)
    half = _WIDTH_IN * IN / 2 / math.cos(theta)
    assert (m.z0_m + m.z1_m) / 2 == pytest.approx(_LOW_FT * FT)
    assert (m.z0_end_m + m.z1_end_m) / 2 == pytest.approx(_HIGH_FT * FT)
    assert m.z1_m - m.z0_m == pytest.approx(2 * half)
    assert m.length_m == pytest.approx(math.hypot(_SPAN_FT * FT, rise))


def test_strap_is_no_clash_and_no_bad_profile() -> None:
    from typehaus.checks.structural._interference_geom import framing_candidates
    from typehaus.resolve.framing.profiles import parses

    model, findings = _frame()
    assert not [f for f in findings if "strap" in f.check_id]
    assert not [c for c in framing_candidates(model) if c.kind == "strap"]
    assert parses(_strap(model)[1].profile)


def test_strap_is_in_model_json_and_gltf(strap_model) -> None:
    from typehaus.emit.gltf import emit_gltf_dict
    from typehaus.server.model_json_fabric import framing_json

    braces = framing_json(strap_model, None)["braces"]
    assert {b["tag"]: b["kind"] for b in braces} == {"SB-A": "strap", "SB-B": "strap"}
    gltf, _ = emit_gltf_dict(strap_model)
    names = [node.get("name", "") for node in gltf["nodes"]]
    assert any(name.endswith("|brace|SBS0000A01") for name in names), names


def test_strap_is_not_lumber(strap_model) -> None:
    from typehaus.takeoff.framing import framing_takeoff

    assert not [r for r in framing_takeoff(strap_model) if r["category"] == "strap"]


def test_strap_bills_as_hardware(strap_model) -> None:
    from typehaus.takeoff.hardware import hardware_takeoff

    rows = hardware_takeoff(strap_model)
    strap, = [r for r in rows if r["scope"] == "strap brace"]
    assert strap["part_number"] == "CS16"
    # CS16 is sold by the coil: two ~10 ft straps are one 150 ft coil.
    assert strap["count"] == strap["coils"] == 1
    assert strap["tags"] == ["SB-A", "SB-B"]
    each_ft = math.hypot(_SPAN_FT, _HIGH_FT - _LOW_FT)
    assert strap["length_ft"] == pytest.approx(2 * each_ft, abs=0.1)
    assert "2 modeled strap brace(s)" in strap["basis"]
    nails, = [r for r in rows if r["scope"] == "strap brace fastener (CS16)"]
    assert nails["count"] == 2 * 2 * _NAILS
    assert nails["part_number"] == '10d x 1-1/2" HDG'


def test_strap_emits_as_ifc_brace(strap_model, tmp_path) -> None:
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc.emitter import emit_ifc

    path = emit_ifc(strap_model, tmp_path / "strap.ifc")
    members = {m.Name: m for m in ifcopenshell.open(str(path)).by_type("IfcMember")}
    assert members["SB-A/strap"].PredefinedType == "BRACE"
    assert members["SB-A/strap"].Representation is not None
