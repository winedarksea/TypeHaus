"""Broad exterior tiers have a close-spaced carriage and a separate wear-board order."""

from types import SimpleNamespace

import pytest

from typehaus.model.spatial import Stair
from typehaus.quantities import ft, inch, pt
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.stairs.dispatch import _resolve_stair
from typehaus.takeoff.framing import framing_takeoff, sheet_goods_takeoff
from typehaus.takeoff.stairs import stair_finish_takeoff


def _tiers(**overrides):
    spec = dict(
        uid="TESTTIER01", tag="ST-TIERS", from_storey="main", to_storey="main",
        start=pt(ft(20), ft(40)), width=ft(6), run_direction="x", run_reversed=True,
        base_elevation=inch(-34), top_elevation=ft(0), tread_depth=inch(24),
        nosing_depth=inch(0), stringer_spacing=inch(12), tread_thickness=inch(1),
        material="kdat", tread_material="composite-deck",
    )
    spec.update(overrides)
    return Stair(**spec)


def _resolve(stair):
    storey = SimpleNamespace(tag="main", elevation=ft(0))
    plan = SimpleNamespace(storey=lambda tag: storey, storeys=[storey],
                           storey_elements=lambda tag: [stair],
                           by_tag=lambda tag: stair if tag == stair.tag else None)
    model = ResolvedModel(plan)
    resolved, findings = _resolve_stair(model, stair, "main")
    if resolved is not None:
        model.stairs.append(resolved)
    return model, findings


@pytest.mark.parametrize("direction", ["x", "y"])
@pytest.mark.parametrize("reversed_run", [True, False])
def test_maximum_stringer_spacing_and_finished_rises(direction, reversed_run):
    model, findings = _resolve(_tiers(run_direction=direction, run_reversed=reversed_run,
                                      width=inch(73)))
    assert not findings
    stair = model.stairs[0]
    strings = [m for m in stair.members if m.category == "stringer"]
    axis = 1 if direction == "x" else 0
    stations = sorted(m.p0[axis] for m in strings)
    assert len(strings) == 8  # ceil(73 / 12) bays + both end members
    assert stations[-1] - stations[0] == pytest.approx(inch(73).meters)
    assert max(b - a for a, b in zip(stations, stations[1:])) <= inch(12).meters
    assert {m.material for m in strings} == {"kdat"}
    treads = sorted((m for m in stair.members if m.category == "tread"),
                     key=lambda m: m.z1_m)
    assert len(treads) == 4
    assert {m.material for m in treads} == {"composite-deck"}
    surfaces = [stair.base_elevation_m, *(m.z1_m for m in treads),
                stair.arrival_elevation_m]
    assert [b - a for a, b in zip(surfaces, surfaces[1:])] == pytest.approx(
        [inch(34).meters / 5] * 5)
    for tread in treads:
        section = cross_section(tread.profile)
        assert section.depth_m == pytest.approx(inch(1).meters)
        assert section.width_m == pytest.approx(inch(24).meters)
    assert all(m.z1_end_m == pytest.approx(-inch(1).meters) for m in strings)


def test_composite_tiers_bill_area_once_and_keep_framing_separate():
    model, findings = _resolve(_tiers())
    assert not findings
    finish = stair_finish_takeoff(model)[0]
    assert finish["tread_material"] == "composite-deck"
    assert finish["tread_run_in"] == 24
    assert finish["tread_area_sqft"] == 48  # four tiers, each 6 x 2 feet
    sheets = sheet_goods_takeoff(model)
    assert len(sheets) == 1
    assert sheets[0]["net_area_sqft"] == 48
    assert sheets[0]["material"] == "composite-deck"
    assert sheets[0]["thickness_in"] == 1
    lumber = framing_takeoff(model)
    assert sum(row["pieces"] for row in lumber) == 7
    assert {row["material"] for row in lumber} == {"kdat"}
    assert all(row["profile"] == "2x12" for row in lumber)


def test_unset_options_preserve_two_stringers_and_lumber_treads():
    model, findings = _resolve(_tiers(stringer_spacing=None, tread_material=None,
                                      tread_thickness=None))
    assert not findings
    stair = model.stairs[0]
    assert len([m for m in stair.members if m.category == "stringer"]) == 2
    treads = [m for m in stair.members if m.category == "tread"]
    assert {m.profile for m in treads} == {"deck 24x1.5"}
    assert {m.material for m in treads} == {"kdat"}
    assert not sheet_goods_takeoff(model)
    assert sum(row["pieces"] for row in framing_takeoff(model)) == 6


@pytest.mark.parametrize("name", ["stringer_spacing", "tread_thickness"])
@pytest.mark.parametrize("value", [inch(0), inch(-1)])
def test_nonpositive_support_or_board_dimensions_report_integrity(name, value):
    model, findings = _resolve(_tiers(**{name: value}))
    assert not model.stairs
    assert findings[0].check_id == "integrity.stair_geometry"


def test_stringer_spacing_does_not_silently_apply_to_a_winder():
    """``stringer_spacing`` is read by the box carriage in ``straight.py`` and nowhere else.

    A winder's boxes and a U-split's landing are laid out by their own rules, so accepting
    the field on one would be accepting a number nothing reads.
    """
    model, findings = _resolve(_tiers(layout="right_angle_winder", winder_count=3,
                                      turn_direction="right"))
    assert not model.stairs
    assert "only for straight" in findings[0].message
