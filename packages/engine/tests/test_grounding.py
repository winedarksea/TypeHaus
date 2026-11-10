"""Grounding and bonding checks (decision #123) on minimal plans."""

from __future__ import annotations

import uuid

from _helpers import check_context

from typehaus.checks.mep.electrical_grounding import (
    concrete_encased_electrode,
    rod_electrodes,
    separate_buildings,
)
from typehaus.checks.mep.electrical_grounding_bonds import lightning_bond
from typehaus.checks.structural.footing_size import footing_size
from typehaus.model import (
    Assembly,
    Building,
    Circuit,
    DeviceKind,
    ElectricalDevice,
    ElectricalDeviceType,
    Footing,
    FoundationWall,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    PlanModel,
    Project,
    Site,
    Storey,
    ft,
    inch,
    pt,
)
from typehaus.model.grounding import BondingConductor, GroundingElectrode
from typehaus.model.rebar import BarSpec, ReinforcementSpec

_METER_T = ElectricalDeviceType(tag="ED-T-MTR", name="Meter-main", footprint=(inch(14), inch(6)),
                                height=inch(30), service_amps=320)
_METER = ElectricalDevice(tag="ED-M-METER", kind=DeviceKind.METER, position=pt(ft(0), ft(-1)),
                          type_ref="ED-T-MTR")


def _project(*buildings: Building) -> Project:
    return Project(name="g", project_uuid=uuid.UUID("00000000-0000-4000-8000-000000000123"),
                   site=Site(lat=44.9, lon=-93.2, elevation=ft(830)), building=Building(name="g"),
                   buildings=buildings)


def _plan(*elements, circuits=(), types=(_METER_T,), storeys=None, project=None) -> PlanModel:
    storeys = storeys or (Storey(tag="b", elevation=ft(0), default_ceiling_height=ft(8)),)
    plan = PlanModel(project=project or _project(), storeys=storeys,
                     library=Library(electrical_device_types=types, circuits=circuits,
                                     materials=(Material(tag="concrete", name="Concrete"),),
                                     assemblies=(Assembly(tag="CONC", layers=(Layer(
                                         name="c", material_ref="concrete", thickness=inch(8),
                                         function=LayerFunction.STRUCTURE),)),)))
    return plan.with_elements(storeys[0].tag, list(elements))


def _rod(tag: str, x_ft: float, use: str = "ges") -> GroundingElectrode:
    return GroundingElectrode(tag=tag, kind="rod", use=use, position=pt(ft(x_ft), ft(-3)),
                              top_elevation=ft(0), length=ft(8))


def _gec(tag: str, to: str) -> BondingConductor:
    return BondingConductor(tag=tag, from_ref="ED-M-METER", to_ref=to, role="gec", size="6")


def _results(fn, plan) -> list:
    return [f for f in fn(check_context(plan)) if f.result.value != "not_applicable"]


def _footing_plan(coating: str) -> PlanModel:
    nodes = [Node(tag=f"N-{i}", position=p) for i, p in enumerate(
        (pt(ft(0), ft(0)), pt(ft(30), ft(0)), pt(ft(30), ft(14)), pt(ft(0), ft(14))), 1)]
    walls = [FoundationWall(tag=f"F-{i}", start_node=f"N-{a}", end_node=f"N-{b}",
                            assembly="CONC", top_elevation=ft(0), bottom_elevation=ft(-8))
             for i, (a, b) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1)]
    bar = BarSpec(role="electrode", bar=4, count=1, coating=coating)
    footing = Footing(tag="FT-1", under="F-1", width=ft(2), depth=ft(1), assembly="CONC",
                      reinforcement=ReinforcementSpec(bars=(bar,), cover=inch(3)))
    ufer = GroundingElectrode(tag="GE-UFER", kind="concrete_encased", position=pt(ft(5), ft(0)),
                              top_elevation=ft(-8), host_ref="FT-1")
    storey = Storey(tag="b", elevation=ft(-8), default_ceiling_height=ft(8))
    return _plan(*nodes, *walls, footing, ufer, storeys=(storey,))


def test_ufer_counts_conductive_bar_only_and_its_footing_stays_plain():
    good = _results(concrete_encased_electrode, _footing_plan("hdg-a767"))
    assert [f.result.value for f in good] == ["pass"], [f.message for f in good]
    assert "29.5 ft" in good[0].message
    bad = _results(concrete_encased_electrode, _footing_plan("epoxy"))
    assert [f.result.value for f in bad] == ["fail"]
    assert "epoxy" in bad[0].message
    # An electrode-only spec leaves the strip plain, so R403.1(1) still grades it.
    sized = footing_size(check_context(_footing_plan("hdg-a767")))
    assert any("FT-1" in f.element_tags for f in sized), [f.message for f in sized]


def test_a_lone_rod_and_a_close_pair_fail():
    lone = _results(rod_electrodes, _plan(_METER, _rod("GE-1", 0), _gec("BC-1", "GE-1")))
    assert [f.result.value for f in lone] == ["fail"]
    assert "lone rod" in lone[0].message
    pair = _results(rod_electrodes, _plan(_METER, _rod("GE-1", 0), _rod("GE-2", 4),
                                          _gec("BC-1", "GE-1"), _gec("BC-2", "GE-2")))
    assert "fail" in [f.result.value for f in pair]
    assert any("4.0 ft from GE-2" in f.message for f in pair)
    apart = _results(rod_electrodes, _plan(_METER, _rod("GE-1", 0), _rod("GE-2", 7),
                                           _gec("BC-1", "GE-1"), _gec("BC-2", "GE-2")))
    assert [f.result.value for f in apart] == ["pass", "pass"]


def test_an_isolated_lightning_terminal_fails_250_106():
    plan = _plan(_METER, _rod("GE-1", 0), _rod("GE-2", 7), _rod("GE-LPS", 30, "lps_terminal"),
                 _gec("BC-1", "GE-1"), _gec("BC-2", "GE-2"))
    found = {f.element_tags[0]: f.result.value for f in _results(lightning_bond, plan)}
    assert found == {"GE-LPS": "fail"}


def test_a_garage_fed_by_two_circuits_needs_its_own_electrodes():
    project = _project(Building(tag="HOUSE", name="House"), Building(tag="GARAGE", name="Garage"))
    storeys = (Storey(tag="h", elevation=ft(0), default_ceiling_height=ft(8), building="HOUSE"),
               Storey(tag="g", elevation=ft(0), default_ceiling_height=ft(8), building="GARAGE"))
    panel = ElectricalDevice(tag="ED-H-PANEL", kind=DeviceKind.PANEL, position=pt(ft(1), ft(1)))
    loads = [ElectricalDevice(tag=f"ED-G-R{i}", kind=DeviceKind.RECEPTACLE,
                              position=pt(ft(40 + 4 * i), ft(1)), circuit=f"CKT-{i}")
             for i in (1, 2)]
    circuits = tuple(Circuit(tag=f"CKT-{i}", panel_ref="ED-H-PANEL", breaker_amps=20)
                     for i in (1, 2))
    plan = _plan(_METER, panel, circuits=circuits, storeys=storeys, project=project)
    plan = plan.with_elements("g", loads)
    found = _results(separate_buildings, plan)
    assert [f.result.value for f in found] == ["fail"]
    assert "GARAGE" in found[0].message
