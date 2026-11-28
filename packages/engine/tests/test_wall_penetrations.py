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
    pens = [p for p in _pens(catlin_model_ro, "W-M-S2") if p.kind == "lineset"]
    sets = sorted(p.station_m for p in pens)
    assert len(sets) == 3
    # The sleeve passes the LAGGED bundle, not the bare tubes.
    bundles = {r.tag: r.bundle_diameter_m for r in catlin_model_ro.pipe_runs}
    assert all(p.outside_d_m == pytest.approx(bundles[p.run_tag]) for p in pens)
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


def test_a_narrow_device_on_a_flat_with_its_screws_in_a_girt_takes_no_block(catlin_model_ro):
    kinds = {t: m.kind for m in catlin_model_ro.mount_blocks if m.kind != "strap_block"
             for t in m.holds}
    flat = {"ED-M-FRONT-RC1", "ED-M-REAR-RC1", "ED-A-RADON-RC", "ED-M-ENTRY-LT",
            "ED-M-STAIR-LT", "ED-S-BALCONY-LT", "ED-S-BALCONY-RC1", "ED-M-DOORBELL"}
    assert {t for t, k in kinds.items() if k == "flat"} == flat
    # Too wide, on a PBR pan's narrow flats, or on corrugated: the block stays.
    assert {"ED-M-HP1-DISC", "ED-A-PV-JB", "ED-M-IBT", "ED-G-EXT-LT-E"} <= {
        t for t, k in kinds.items() if k == "block"}
    mount = next(m for m in catlin_model_ro.mount_blocks if "ED-M-FRONT-RC1" in m.holds)
    obj = next(o for o in catlin_model_ro.canvas_objects if o.tag == "ED-M-FRONT-RC1")
    back = min((x - mount.origin[0]) * mount.normal[0] + (y - mount.origin[1]) * mount.normal[1]
               for x, y in obj.footprint)
    assert back == pytest.approx(-(0.75 - 0.0239) * _IN, abs=2e-4)  # on the pan, behind the crowns


def test_a_flat_mount_off_its_flat_or_girt_fails(catlin_model_ro):
    from typehaus.checks.integrity.wall_penetration_closure import _FlatCache, _mount_findings
    from typehaus.resolve.mount_blocks import penetration_standard

    standard = penetration_standard(catlin_model_ro.plan)
    flats = _FlatCache(catlin_model_ro, standard.bridgeable_rib_height.meters)
    mount = next(m for m in catlin_model_ro.mount_blocks if "ED-M-FRONT-RC1" in m.holds)
    assert not _mount_findings(catlin_model_ro, standard, mount, flats)
    on_batten = replace(mount, station_lo_m=mount.station_lo_m + 5 * _IN,
                        station_hi_m=mount.station_hi_m + 5 * _IN)
    assert "rigid flat" in _mount_findings(catlin_model_ro, standard, on_batten, flats)[0].message
    low = replace(mount, z0_m=mount.z0_m - 10 * _IN, z1_m=mount.z1_m - 10 * _IN)
    assert "girt" in _mount_findings(catlin_model_ro, standard, low, flats)[0].message
