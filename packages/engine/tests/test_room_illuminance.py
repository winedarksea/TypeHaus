"""``advisory.room_illuminance``: the lumen method over points and tape, ADVISORY when short."""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.checks.mep.lighting_illuminance import room_illuminance
from typehaus.model import (
    DeviceKind,
    ElectricalDevice,
    Library,
    LuminaireForm,
    LuminaireType,
    ft,
    inch,
    pt,
)


def _type(tag, form, lumens, lamp="LED"):
    return LuminaireType(tag=tag, name=tag, footprint=(inch(4), inch(4)), height=inch(4),
                         form=form, lumens=lumens, lamp=lamp)


def _ctx(overrides=None):
    library = Library(electrical_device_types=(
        _type("PANEL", LuminaireForm.PANEL, 5000.0),
        _type("FAN", LuminaireForm.CEILING_FAN_LIGHT, None, lamp=None),
        _type("TAPE", LuminaireForm.STRIP, 200.0)))
    devices = [ElectricalDevice(uid=f"D{i}", tag=f"ED-{i}", kind=DeviceKind.LIGHT,
                                position=pt(ft(i), ft(1)), type_ref=ref, room="RM-SHOP")
               for i, ref in enumerate(("PANEL", "PANEL", "FAN"))]
    plan = SimpleNamespace(library=library, all_elements=lambda: devices)
    rooms = [SimpleNamespace(tag="RM-SHOP", occupancy="utility", area_m2=20.0),
             SimpleNamespace(tag="RM-LIVE", occupancy="living", area_m2=20.0)]
    runs = [SimpleNamespace(tag="LR-1", type_ref="TAPE", room="RM-SHOP",
                            length_m=ft(10).meters)]
    return SimpleNamespace(plan=plan, model=SimpleNamespace(rooms=rooms, light_runs=runs),
                           preferences=SimpleNamespace(mep=SimpleNamespace(
                               illuminance_lux=overrides or {})))


def test_short_room_is_advisory_with_tape_counted_and_the_lampless_fan_ignored():
    (finding,) = room_illuminance(_ctx())  # the living room has no default target
    assert finding.result.value == "advisory"
    # (2 x 5000 + 10 ft x 200) lm x 0.60 x 0.80 / 20 m2 = 288 lx
    assert "12,000 lm" in finding.message and "288 lx" in finding.message
    passed = room_illuminance(_ctx({"RM-SHOP": 250, "living": 0}))
    assert [f.result.value for f in passed] == ["pass"]
