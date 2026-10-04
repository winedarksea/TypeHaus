"""SlatBrace: a framed band of 45° slats, each a knee brace — layout, members, bill, IFC.

The frame is catlin's west band (``notes/canopy_west_band.md`` §3a) on a bare two-post frame,
so the layout numbers are the note's: 24.375" x 25.125" bays, nine slats a bay, five across
mid-band.
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
    assert lay.pitch / IN == pytest.approx(3.0 * math.sqrt(2), abs=1e-6)
    for bay in (0, 1):
        slats = lay.bay(bay)
        assert [s.j for s in slats] == list(range(-4, 5))  # j = ±5 is 5.00", under 8"
        assert lay.crossing_mid(bay) == 5
        assert min(s.length for s in slats) / IN == pytest.approx(11.0, abs=0.01)
        assert max(s.length for s in slats) / IN == pytest.approx(34.47, abs=0.01)
    lands = [(s.low, s.high) for s in lay.bay(0)]
    assert lands.count(("chord", "top")) == 4 and lands.count(("sill", "centre")) == 4
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
    for j in range(-4, 5):
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
    assert len(slats) == 18
    for m in slats:
        assert m.z0_m >= sill_top - 1e-9 and m.z1_end_m <= top_under + 1e-9
        assert m.p0[1] == pytest.approx(IN) and m.plan_width_m == pytest.approx(3.5 * IN)


def test_the_slats_bill_as_lumber_and_the_parts_as_hardware(band_model) -> None:
    from typehaus.takeoff.framing import framing_takeoff
    from typehaus.takeoff.hardware import hardware_takeoff

    lumber = {(r["profile"], r["category"]): r for r in framing_takeoff(band_model)}
    assert lumber[("2x4", "brace")]["pieces"] == 18
    rows = {r["scope"]: r for r in hardware_takeoff(band_model)
            if r["scope"].startswith("slat brace")}
    assert rows["slat brace connector"]["count"] == 36
    assert rows["slat brace connector"]["part_number"] == "KBS1Z"
    assert rows["slat brace plate screw"]["count"] == 16
    assert rows["slat brace centre post tie"]["count"] == 4


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
    members = {m.Name: m for m in ifcopenshell.open(str(path)).by_type("IfcMember")}
    assert members["SB-T/slat-0+0"].PredefinedType == "BRACE"
    assert members["SB-T/plate-top"].PredefinedType == "MEMBER"
