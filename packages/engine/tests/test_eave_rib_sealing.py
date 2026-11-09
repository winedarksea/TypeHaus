"""Rib-end records, their independent grade, and whole-cartridge procurement (no real house)."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from typehaus.checks.integrity import eave_rib_sealing as check_module
from typehaus.findings import Result
from typehaus.library.trim.image_ii_eave_sealing import IMAGE_II_EAVE_SEALING as SPEC
from typehaus.library.trim.image_ii_eave_sealing import SourcedValue, ValueBasis
from typehaus.quantities import M_PER_IN
from typehaus.resolve import roof_eave_rib_ends as resolver
from typehaus.resolve.metal_skin_profiles import IMAGE_II_16_PROFILE as PROFILE
from typehaus.resolve.model import ResolvedRoof
from typehaus.resolve.model_eave_sealing import (
    CLEAT_EAVE,
    FULL_CAVITY,
    RIPPED_CAVITY,
    SHARED_CAVITY,
    WRAPPED_EAVE,
    ResolvedEaveSealingRun,
)
from typehaus.takeoff.cladding_trim import _eave_sealing_rows, _Rows
from typehaus.takeoff.eave_rib_sealing import CUBIC_IN_PER_FL_OZ, cartridge_orders, eave_run_sealing

PITCH = PROFILE.pitch_m
#: Roofing along the ridge: seven full ribs, none near a rake, on the centre's own register.
LOW, HIGH = 0.5 * PITCH, 7.5 * PITCH


def _roof(direction="y", form="gable", tag="RF"):
    along = (LOW, HIGH)
    corners = (((0, along[0]), (4, along[0]), (4, along[1]), (0, along[1])) if direction == "y"
               else ((along[0], 0), (along[1], 0), (along[1], 4), (along[0], 4)))
    return ResolvedRoof("uid-" + tag, tag, "main", form, corners, 3.0, 4.0, direction, "roof", 24.0)


def _rect(roof):
    return (0.0, 4.0, LOW, HIGH) if roof.ridge_direction == "y" else (LOW, HIGH, 0.0, 4.0)


STACK = SimpleNamespace(seam_flats=lambda: [(0.0, 0.05, 0.01)], slope=0.5,
                        membrane_top_w=0.02, factor=1.118)


@pytest.fixture
def wire(monkeypatch):
    def apply(*, kit="IMAGE_II", wrapped=False, abutted=frozenset(), register=None, low_high=None,
              anchor=None):
        from typehaus.resolve.roof_edge_geometry import roof_edge_runs

        def layers(roof, _model):
            rect = _rect(roof)
            if low_high is not None:
                rect = ((0.0, 4.0, *low_high) if roof.ridge_direction == "y"
                        else (*low_high, 0.0, 4.0))
            yield None, 0.0, rect, PROFILE

        monkeypatch.setattr(resolver, "roof_edge_kit", lambda _m, _r: kit)
        monkeypatch.setattr(resolver, "profiled_roof_layers", layers)
        monkeypatch.setattr(resolver, "seam_anchor", lambda _m, _r: anchor)
        monkeypatch.setattr(resolver, "abutted_run_keys", lambda _m, _r: abutted)
        monkeypatch.setattr(resolver, "seam_register_roofs",
                            lambda _m, roof: register or (roof,))
        monkeypatch.setattr(resolver, "roof_continues_at", lambda *_a: True)
        monkeypatch.setattr(
            resolver, "wrapped_eave_runs",
            lambda _m, roof: (tuple(r for r in roof_edge_runs(roof) if r.is_eave), STACK)
            if wrapped else ((), None))
        monkeypatch.setattr(check_module, "roof_edge_kit", lambda _m, _r: kit)
        monkeypatch.setattr(check_module, "abutted_run_keys", lambda _m, _r: abutted)

    return apply


def _model(*roofs):
    return SimpleNamespace(roofs=list(roofs), eave_sealing_runs=[])


@pytest.mark.parametrize("direction", ["x", "y"])
@pytest.mark.parametrize("wrapped", [False, True])
def test_both_eaves_record_every_full_rib_once(wire, direction, wrapped) -> None:
    wire(wrapped=wrapped)
    runs = resolver._sealing_runs(_model(), _roof(direction))
    assert {run.run_key for run in runs} == {"eave-lo", "eave-hi"}
    for run in runs:
        assert run.eave_condition == (WRAPPED_EAVE if wrapped else CLEAT_EAVE)
        assert len(run.rib_ends) == 7
        assert {end.cavity for end in run.rib_ends} == {FULL_CAVITY}
        assert all(end.treatment == SPEC.treatment for end in run.rib_ends)
    keys = [end.key for run in runs for end in run.rib_ends]
    assert len(keys) == len(set(keys))


def test_a_sheds_high_edge_and_an_abutted_eave_have_no_exposed_ends(wire) -> None:
    wire()
    assert [run.run_key for run in resolver._sealing_runs(_model(), _roof(form="shed"))] == [
        "eave-lo"]
    wire(abutted=frozenset({"eave-hi"}))
    assert [run.run_key for run in resolver._sealing_runs(_model(), _roof())] == ["eave-lo"]


def test_a_roof_with_no_kit_records_nothing(wire) -> None:
    wire(kit=None)
    assert resolver._sealing_runs(_model(), _roof()) == ()


def test_an_unspecified_kit_stays_unresolved_rather_than_assumed(wire) -> None:
    wire(kit="OTHER_PANEL")
    ends = resolver._sealing_runs(_model(), _roof())[0].rib_ends
    assert ends and all(end.treatment is None for end in ends)


def test_a_rib_cut_by_a_rake_is_inspected_not_plugged(wire) -> None:
    wire(low_high=(PITCH / 2, 7.25 * PITCH), anchor=PITCH / 2)
    ends = resolver._sealing_runs(_model(), _roof())[0].rib_ends
    ripped = [end for end in ends if end.cavity == RIPPED_CAVITY]
    assert len(ripped) == 1 and ripped[0].treatment is None


def test_a_rib_on_a_shared_boundary_is_counted_by_one_roof(wire) -> None:
    roof_a, roof_b = _roof(tag="RF-A"), _roof(tag="RF-B")
    wire(low_high=(PITCH / 2, HIGH), anchor=PITCH / 2, abutted=frozenset({"rake-lo-0"}),
         register=(roof_a, roof_b))
    shared = [[end for end in resolver._sealing_runs(_model(), roof)[0].rib_ends
               if end.cavity == SHARED_CAVITY] for roof in (roof_a, roof_b)]
    assert [len(ends) for ends in shared] == [1, 0]


def _pan_members(stations, normal_sign=1.0, connection="roof:pan-hem", gap=0.75 * M_PER_IN):
    """One pan per interval between ``stations``, on the y-ridge roof's eave at ``normal_sign``."""
    across = 4.0 if normal_sign > 0 else 0.0
    return [SimpleNamespace(connection=connection, p0=(across, a + gap / 2),
                            p1=(across, b - gap / 2))
            for a, b in zip(stations, stations[1:], strict=False)]


def _graded(wire, *, drop=None, duplicate=False):
    wire()
    roof = _roof()
    run = resolver._sealing_runs(_model(), roof)[1]    # eave-hi
    stations = [LOW, *(k * PITCH for k in range(1, 8)), HIGH]
    pans = _pan_members(stations)
    roof = replace(roof, members=tuple(pans))
    ends = list(run.rib_ends)
    if drop is not None:
        del ends[drop]
    if duplicate:
        ends.append(ends[0])
    model = _model(roof)
    model.eave_sealing_runs = [replace(run, rib_ends=tuple(ends))]
    return [f for f in check_module.eave_rib_sealing(SimpleNamespace(model=model))
            if "eave-lo" not in f.message]


def test_independent_enumeration_passes_only_on_exact_coverage(wire) -> None:
    assert {f.result for f in _graded(wire)} == {Result.PASS}
    missing = _graded(wire, drop=3)
    assert [f.result for f in missing] == [Result.FAIL]
    assert "no treatment record" in missing[0].message
    assert Result.FAIL in {f.result for f in _graded(wire, duplicate=True)}


def _run(tag: str, ribs: int, hem_m: float = 0.0) -> ResolvedEaveSealingRun:
    end = SimpleNamespace(treatment=SPEC.treatment)
    return ResolvedEaveSealingRun("RF", tag, "east", "IMAGE_II", CLEAT_EAVE, (end,) * ribs,
                                  hem_m, 1.0, 0.5 * M_PER_IN ** 2)


def test_plug_volume_is_area_times_depth_and_only_treated_ends_count() -> None:
    model = SimpleNamespace(eave_sealing_runs=[_run("a", 4)])
    row = eave_run_sealing(model)[0]
    assert row.terminations == 4
    assert row.plug_volume_in3 == pytest.approx(4 * 0.5 * SPEC.plug_fill_depth_in.value)


def test_rounding_happens_once_on_the_pooled_volume() -> None:
    capacity = SPEC.sealant.cartridge_fl_oz.value * CUBIC_IN_PER_FL_OZ
    # Each run alone needs about half a cartridge after waste; two pool into one purchase.
    ribs = round(0.4 * capacity / (0.5 * SPEC.plug_fill_depth_in.value))
    model = SimpleNamespace(eave_sealing_runs=[_run("a", ribs), _run("b", ribs)])
    order = cartridge_orders(model)[0]
    assert order.gross_volume_in3 == pytest.approx(order.net_volume_in3 * 1.2)
    assert order.gross_volume_in3 <= capacity and order.cartridges == 1


def test_the_estimate_adds_no_vent_closure_or_rivets() -> None:
    rows = _Rows()
    _eave_sealing_rows(SimpleNamespace(eave_sealing_runs=[_run("a", 3, hem_m=2.0)]), rows)
    by_part = {row["part"]: row for row in rows.finish()}
    assert set(by_part) == {"64032XX", "eave-rib-plug", "eave-hem-bead", "6403899"}
    assert by_part["eave-rib-plug"]["quantity"] == 3
    assert by_part["eave-hem-bead"]["unit"] == "LF"
    assert by_part["64032XX"]["count"] == 1


def test_only_a_published_value_stops_being_an_open_item() -> None:
    assert any("chemistry" in item for item in SPEC.open_items())
    assert any("fill depth" in item for item in SPEC.open_items())
    published = SourcedValue(1.0, ValueBasis.MANUFACTURER, "a published row")
    closed = replace(SPEC, plug_fill_depth_in=published)
    assert not any("fill depth" in item for item in closed.open_items())
