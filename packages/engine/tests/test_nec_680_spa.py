"""NEC 680 Part IV (``code.NEC_680_spa``): Catlin's verdicts, and the modeled-tub distances."""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.checks import run_from_model
from typehaus.checks.mep.electrical_spa import spa_and_hot_tub
from typehaus.checks.registry import Tier
from typehaus.findings import Result
from typehaus.model.enums import DeviceKind, EquipmentKind

_CID = "code.NEC_680_spa"
_FT = 0.3048


def test_catlins_spa_circuit_is_graded_and_its_tub_is_not(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.CODE, only=_CID)
    found = [f for f in report.findings if f.check_id == _CID]
    verdicts = {f.result.value for f in found}
    assert verdicts == {"pass", "not_applicable", "unknown"}  # no FAIL
    passed = [f for f in found if f.result.value == "pass"]
    assert len(passed) == 1 and "Class A" in passed[0].message  # 680.44(A) / 680.5(B)
    unknown = " ".join(f.message for f in found if f.result.value == "unknown")
    assert "ED-B-SPA-DISC" in unknown and "680.13" in unknown  # waits on the tub footprint


def _ctx(extra_elements, walls=(), indoors=True):
    def box(x0, y0, x1, y1):
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    def obj(tag, x, y, footprint=None):
        return SimpleNamespace(tag=tag, storey="s", position=(x, y), footprint=footprint or [])

    spa = SimpleNamespace(element_kind="Equipment", kind=EquipmentKind.SPA, tag="EQ-SPA",
                          circuit="CKT-SPA", type_ref=None)
    elements = [spa, *(e for e, *_ in extra_elements)]
    objects = [obj("EQ-SPA", 1, 1, box(0, 0, 2, 2)), *(obj(e.tag, x, y)
                                                          for e, x, y in extra_elements)]
    room = SimpleNamespace(storey="s", axis_face=box(-20, -20, 20, 20), clear_face=[])
    rooms = [room] if indoors else []
    circuit = SimpleNamespace(tag="CKT-SPA", spa=True, gfci=True, gfci_class="A", poles=2,
                              breaker_amps=50)
    plan = SimpleNamespace(
        all_elements=lambda: elements,
        library=SimpleNamespace(circuits=[circuit], equipment_types=[]),
        project=SimpleNamespace(buildings=[SimpleNamespace(kind="dwelling")]))
    model = SimpleNamespace(canvas_objects=objects, rooms=rooms, walls=list(walls))
    return SimpleNamespace(plan=plan, model=model)


def _device(tag, kind, circuit=None):
    return SimpleNamespace(element_kind="ElectricalDevice", tag=tag, kind=kind, circuit=circuit)


def _verdicts(ctx):
    return [(f.result, f.message) for f in spa_and_hot_tub(ctx)]


def test_indoor_spa_switch_receptacle_and_equipment_distances():
    switch = _device("ED-SW", DeviceKind.SWITCH)
    near_rc = _device("ED-RC-NEAR", DeviceKind.RECEPTACLE)
    gfci_rc = _device("ED-RC-OK", DeviceKind.RECEPTACLE_GFCI)
    disc = _device("ED-DISC", DeviceKind.DISCONNECT)
    ctx = _ctx([(switch, 2 + 3 * _FT, 1), (near_rc, 2 + 4 * _FT, 1),
                (gfci_rc, 2 + 8 * _FT, 1), (disc, 2 + 4 * _FT, 1.2)])
    got = {tag: result for result, msg in _verdicts(ctx)
           for tag in ("ED-SW", "ED-RC-NEAR", "ED-RC-OK", "ED-DISC") if tag in msg}
    assert got["ED-SW"] is Result.FAIL            # 680.43(C): under 5 ft
    assert got["ED-RC-NEAR"] is Result.FAIL       # 680.43(A)(1): under 6 ft
    assert got["ED-RC-OK"] is Result.PASS         # 6-10 ft, GFCI
    assert got["ED-DISC"] is Result.UNKNOWN       # 680.41(B): self-contained not stated


def test_a_wall_between_clears_the_equipment_distance():
    disc = _device("ED-DISC", DeviceKind.DISCONNECT)
    wall = SimpleNamespace(storey="s", axis=[(2 + 2 * _FT, -5), (2 + 2 * _FT, 5)],
                           thickness_m=0.2)
    ctx = _ctx([(disc, 2 + 4 * _FT, 1)], walls=[wall])
    [(result, _)] = [v for v in _verdicts(ctx) if "ED-DISC" in v[1]]
    assert result is Result.PASS


def test_outdoor_spa_takes_the_20_ft_receptacle_and_the_680_13_disconnect():
    gfci_rc = _device("ED-RC", DeviceKind.RECEPTACLE_GFCI)
    gfci_rc.mount = SimpleNamespace(elevation=SimpleNamespace(meters=4 * _FT))
    disc = _device("ED-DISC", DeviceKind.DISCONNECT, circuit="CKT-SPA")
    near_disc = _device("ED-DISC2", DeviceKind.DISCONNECT, circuit="CKT-SPA")
    objects = [(gfci_rc, 2 + 15 * _FT, 1), (disc, 2 + 6 * _FT, 1), (near_disc, 2 + 2 * _FT, 1)]
    outdoor = {tag: result for result, msg in _verdicts(_ctx(objects, indoors=False))
               for tag in ("ED-RC", "ED-DISC2", "ED-DISC ") if tag in msg}
    assert outdoor["ED-RC"] is Result.PASS and outdoor["ED-DISC "] is Result.PASS
    assert outdoor["ED-DISC2"] is Result.FAIL  # 680.13: under 5 ft, no barrier
    # the same receptacle indoors is past 10 ft, so 680.43(A) finds none in 6-10 ft
    indoor = [(r, m) for r, m in _verdicts(_ctx(objects)) if "general-purpose" in m]
    assert indoor and indoor[0][0] is Result.FAIL
