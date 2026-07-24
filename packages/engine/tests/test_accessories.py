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
    from typehaus.resolve.roof_geometry import roof_height_at

    vent = _solids(catlin_model, "vent")
    chases = [s for s in vent if s.tag.endswith("CHASE")]
    terms = [s for s in vent if s.tag.endswith("TERM")]
    outs = [s for s in vent if "-OUT" in s.tag]
    assert len(chases) == len(terms) == 2  # radon + plumbing vent
    assert len(outs) == 8  # each horizontal jog is stacked out of 4 round bands
    exit_z = ft(24, 6).meters
    # Chase rises from below grade to the turn-out, which stays *under* the rake.
    for c in chases:
        assert c.z0_m < -2.0 and abs(c.z1_m - exit_z) < 0.05
    for o in outs:
        assert abs((o.z0_m + o.z1_m) / 2 - exit_z) < inch(2).meters
    # Termination is derived: 12" above the roof plane at the exterior riser, not the
    # 33' that was authored — that sat 2' above the ridge of this 4:12 gable.
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    expected = roof_height_at(roof, (ft(3).meters, ft(37).meters)) + inch(12).meters
    assert expected < 28 * FT
    for t in terms:
        assert abs(t.z0_m - exit_z) < 0.05
        assert abs(t.z1_m - expected) < 1e-6


def test_catlin_vent_pipes_are_round_sections(catlin_model) -> None:
    """A 3" vent used to render as a square post; risers now carry a faceted circle."""
    from typehaus.resolve.accessories import _PIPE_FACETS

    radius = inch(3).meters / 2.0
    for solid in _solids(catlin_model, "vent"):
        if not (solid.tag.endswith("CHASE") or solid.tag.endswith("TERM")):
            continue
        assert len(solid.outline) == _PIPE_FACETS
        cx = sum(x for x, _ in solid.outline) / _PIPE_FACETS
        cy = sum(y for _, y in solid.outline) / _PIPE_FACETS
        for x, y in solid.outline:
            assert abs(math.hypot(x - cx, y - cy) - radius) < 1e-9


def test_vent_termination_derives_from_the_wall_the_riser_rides(catlin_model) -> None:
    """The zero-overhang rake leaves the riser outside every roof footprint, so the
    derivation has to come off the gable wall's ``ToRoof`` top, not plan containment."""
    from shapely.geometry import Point, Polygon

    from typehaus.resolve.vent_termination import exterior_riser_point, roof_cleared_by

    vent = catlin_model.plan.by_tag("VR-M-RADON-VENT")
    riser = Point(exterior_riser_point(vent))
    assert not any(Polygon(roof.footprint).covers(riser) for roof in catlin_model.roofs)
    assert roof_cleared_by(catlin_model, vent).tag == "RF-HOUSE"


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


def test_gltf_emits_with_accessories(catlin_model) -> None:
    from typehaus.emit.gltf.emitter import emit_gltf_dict

    gltf, blob = emit_gltf_dict(catlin_model)
    assert gltf["materials"] and blob, "glTF should build with accessory solids"
