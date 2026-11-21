"""Metal-wall penetrations and mounts (decision #142) on catlin, and the boot-on-flat rule."""

from __future__ import annotations

from dataclasses import replace

import pytest

_IN = 0.0254


def _pens(model, wall):
    return [p for p in model.wall_penetrations if p.wall_tag == wall]


def test_north_gable_has_the_vent_and_radon_exits_and_four_strap_blocks(catlin_model_ro):
    exits = {p.run_tag: p for p in _pens(catlin_model_ro, "W-A-N2")}
    assert set(exits) == {"VR-M-STACK-4in-vent", "VR-M-STACK-radon"}
    assert all(p.kind == "round" and p.closure == "boot" for p in exits.values())
    assert exits["VR-M-STACK-4in-vent"].boot_size == "#4"
    assert exits["VR-M-STACK-4in-vent"].sleeve_d_m == pytest.approx(6.625 * _IN)
    straps = [m for m in catlin_model_ro.mount_blocks
              if m.wall_tag == "W-A-N2" and m.kind == "strap_block"]
    assert len(straps) == 4
    assert sum(m.top_z is not None for m in straps) == 2  # the two under the rake


def test_hp2_linesets_cross_one_per_batten_bay(catlin_model_ro):
    sets = sorted(p.station_m for p in _pens(catlin_model_ro, "W-M-S2") if p.kind == "lineset")
    assert len(sets) == 3
    assert [b - a for a, b in zip(sets, sets[1:], strict=False)] == pytest.approx([12 * _IN] * 2)


def test_a_boot_moved_onto_a_batten_fails(catlin_model_ro):
    from typehaus.checks.integrity.wall_penetration_closure import _FlatCache, _pen_findings

    radon = next(p for p in _pens(catlin_model_ro, "W-A-N2")
                 if p.run_tag == "VR-M-STACK-radon")
    flats = _FlatCache(catlin_model_ro, 0.3125 * _IN)
    assert not _pen_findings(catlin_model_ro, radon, flats)
    on_batten = replace(radon, station_m=12 * _IN)  # a batten's centre on BBD75
    found = _pen_findings(catlin_model_ro, on_batten, flats)
    assert found and "leaves its flat" in found[0].message


def test_the_derived_block_stands_the_device_off(catlin_model_ro):
    block = next(m for m in catlin_model_ro.mount_blocks if "ED-A-PV-JB" in m.holds)
    obj = next(o for o in catlin_model_ro.canvas_objects if o.tag == "ED-A-PV-JB")
    back = min((x - block.origin[0]) * block.normal[0] + (y - block.origin[1]) * block.normal[1]
               for x, y in obj.footprint)
    assert back == pytest.approx(block.depth_m, abs=1e-4)
