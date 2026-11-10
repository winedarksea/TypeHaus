"""``code.NEC_215_18_spd``: an SPD circuit in each panel holding branch breakers."""

from __future__ import annotations

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.model import (Building, Circuit, DeviceKind, ElectricalDevice, ElectricalDeviceType,
                            Library, PlanModel, Project, Service, ServicePort, Site, Storey, m, pt)
from typehaus.resolve import resolve

_CID = "code.NEC_215_18_spd"


def _results(*circuits: Circuit) -> list[str]:
    port = ServicePort(tag="power", service=Service.POWER_240, position=(m(0), m(0), m(0)))
    panel_type = ElectricalDeviceType(tag="ED-T-PNL", name="Panel", footprint=(m(.5), m(.1)),
                                      height=m(1), spaces=42, ports=(port,))
    panel = ElectricalDevice(tag="ED-M-PANEL", kind=DeviceKind.PANEL,
                             position=pt(m(0), m(0)), type_ref="ED-T-PNL")
    plan = PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000003",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(circuits=circuits, electrical_device_types=(panel_type,)),
        elements={"main": (panel,)},
    )
    model, _ = resolve(plan)
    report = run_from_model(model, [], tier=Tier.CODE, only=_CID)
    return [f.result.value for f in report.findings if f.check_id == _CID]


def test_a_branch_panel_needs_its_own_spd_circuit():
    branch = Circuit(tag="CKT-1", panel_ref="ED-M-PANEL", breaker_amps=20, slot=1)
    spd = Circuit(tag="CKT-SPD", panel_ref="ED-M-PANEL", breaker_amps=20, poles=2, slot=3,
                  spd=True)
    assert _results(branch) == ["unknown"]
    assert _results(branch, spd) == ["pass"]
    assert _results(spd) == ["not_applicable"]
