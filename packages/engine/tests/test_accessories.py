"""U7 accessories: dowels, connectors, railings, sump/vent, and edge trim.

These resolve into ``ResolvedSolid`` geometry (rendered by the existing glTF/IFC solid
paths). The tests assert the schema primitives exist, the Catlin house authors them, and
the resolver derives the intended geometry (especially the shared radon/plumbing vent
routing: up the chase, out, then up the siding to 12" above the roof)."""

from __future__ import annotations

import math

import pytest

from typehaus.model import (
    Connector,
    ConnectorKind,
    Dowel,
    Fascia,
    Flashing,
    Gutter,
    Railing,
    RailingKind,
    Sump,
    TrimKind,
    VentRun,
    element_kinds,
    ft,
    inch,
    pt,
)
from typehaus.model.enums import DeviceKind, PipeSystem

FT = 0.3048


def test_new_kinds_registered_as_constructors() -> None:
    from typehaus.model.registry import constructor_names

    ctors = constructor_names()
    kinds = element_kinds()
    for name in ("Dowel", "Connector", "Railing", "Sump", "VentRun",
                 "Fascia", "Gutter", "Flashing"):
        assert name in kinds, f"{name} not a registered element kind"
        assert name in ctors, f"{name} not a dialect constructor"


def test_enums_extended() -> None:
    assert DeviceKind.JUNCTION_BOX.value == "junction_box"
    assert PipeSystem.RADON.value == "radon"
    assert ConnectorKind.STANDING_SEAM_CLAMP.value == "standing_seam_clamp"
    assert RailingKind.METAL_FASCIA_MOUNT.value == "metal_fascia_mount"
    assert TrimKind.WRB_COUNTERFLASHING.value == "wrb_counterflashing"


def test_elements_are_frozen_and_typed() -> None:
    dowel = Dowel(uid="AAAAAAAAAA", tag="DW-1", position=pt(ft(0), ft(0)),
                  length=inch(24), diameter=inch(0.625), elevation=ft(-9),
                  foam_thickness=inch(2))
    with pytest.raises(Exception):
        dowel.tag = "DW-2"  # type: ignore[misc]
    rail = Railing(uid="AAAAAAAAAB", tag="RL-1",
                   path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))),
                   height=ft(3.5), base_elevation=ft(10), post_spacing=inch(60))
    assert rail.kind is RailingKind.METAL_FASCIA_MOUNT
    assert Fascia(uid="", tag="F", path=(pt(ft(0), ft(0)), pt(ft(1), ft(0))),
                  top_elevation=ft(10), depth=inch(9), thickness=inch(1)).kind is TrimKind.FASCIA


# --- resolver / Catlin integration ------------------------------------------
def _solids(model, category):
    return [s for s in model.solids if s.category == category]


def test_catlin_resolves_all_accessory_categories(catlin_model) -> None:
    for category in ("railing", "dowel", "thermal_break", "connector",
                     "fascia", "gutter", "flashing", "sump", "vent"):
        assert _solids(catlin_model, category), f"no {category} solids resolved"


def test_catlin_dowels_and_foam_bridge_the_footing_joint(catlin_model) -> None:
    dowels = _solids(catlin_model, "dowel")
    foam = _solids(catlin_model, "thermal_break")
    assert len(dowels) == 9  # 3 locations x 3 bars
    assert len(foam) == 3
    # Bars sit at mid-footing (~ -9.25') and span ~24" across the joint.
    for bar in dowels:
        assert bar.z0_m < -2.5 < bar.z1_m or abs((bar.z1_m + bar.z0_m) / 2 + 9.25 * FT) < 0.2


def test_catlin_vent_routes_up_out_up_to_above_roof(catlin_model) -> None:
    vent = _solids(catlin_model, "vent")
    assert len(vent) == 6  # radon + plumbing vent, each: chase + out + term
    chases = [s for s in vent if s.tag.endswith("CHASE")]
    terms = [s for s in vent if s.tag.endswith("TERM")]
    outs = [s for s in vent if s.tag.endswith("OUT")]
    assert len(chases) == len(terms) == len(outs) == 2
    # Chase rises from below grade to near the attic ceiling (~29').
    for c in chases:
        assert c.z0_m < -2.0 and abs(c.z1_m - 29 * FT) < 0.05
    # Out segment is horizontal near the attic ceiling.
    for o in outs:
        assert abs((o.z0_m + o.z1_m) / 2 - 29 * FT) < 0.1
    # Termination tops 12" above the roof (33').
    for t in terms:
        assert abs(t.z1_m - 33 * FT) < 0.05


def test_catlin_balcony_guard_is_a_42in_railing(catlin_model) -> None:
    posts = [s for s in _solids(catlin_model, "railing") if "POST" in s.tag]
    assert posts, "railing posts expected"
    for post in posts:
        assert math.isclose(post.z0_m, 10 * FT, abs_tol=0.02)
        assert math.isclose(post.z1_m - post.z0_m, 3.5 * FT, abs_tol=0.02)


def test_catlin_sump_sits_below_the_basement_slab(catlin_model) -> None:
    sumps = _solids(catlin_model, "sump")
    assert len(sumps) == 1
    assert sumps[0].z0_m < sumps[0].z1_m <= 0.0


def test_catlin_house_roof_eave_trim_closes_the_eave(catlin_model) -> None:
    """Tier 2 roof-eave closure: fascia + 6" box gutter + drip edge along both house
    eave edges (west/east — the ridge runs N-S), at elevations tied to the deck plane
    per the golden eave detail. Garage trim stays deferred with the truss roof."""
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    eave, plate = roof.eave_z_m, roof.bearing_z_m
    for side in ("W", "E"):
        fascia = next(s for s in catlin_model.solids if s.tag == f"TR-RF-FASCIA-{side}-1")
        gutter = next(s for s in catlin_model.solids if s.tag == f"TR-RF-GUTTER-{side}-1")
        drip = next(s for s in catlin_model.solids if s.tag == f"TR-RF-DRIP-{side}-1")
        assert (fascia.category, gutter.category, drip.category) == (
            "fascia", "gutter", "flashing")
        # Fascia closes the band: top of deck+membrane down past the plate.
        assert fascia.z1_m == pytest.approx(eave + inch(1.0).meters)
        assert fascia.z0_m == pytest.approx(plate - inch(2.0).meters)
        # Box gutter hangs with its top 1.2" below the roof-furring underside (7.25"
        # perpendicular above the deck), 5" channel height.
        assert gutter.z1_m == pytest.approx(eave + inch(7.25 - 1.2).meters)
        assert gutter.z1_m - gutter.z0_m == pytest.approx(inch(5.0).meters)
        # Drip edge turns down over the fascia into the gutter from the metal eave.
        assert drip.z1_m == pytest.approx(eave + inch(9.0).meters)
        assert drip.z0_m < gutter.z1_m + inch(1.0).meters
    assert not [s for s in catlin_model.solids if s.tag.startswith("TR-RF-")
                and "GARAGE" in s.tag]


def test_gltf_emits_with_accessories(catlin_model) -> None:
    from typehaus.emit.gltf.emitter import emit_gltf_dict

    gltf, blob = emit_gltf_dict(catlin_model)
    assert gltf["materials"] and blob, "glTF should build with accessory solids"
