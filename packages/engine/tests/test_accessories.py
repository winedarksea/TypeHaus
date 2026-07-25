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
    for name in ("Dowel", "Connector", "KneeBrace", "Railing", "Sump", "VentRun",
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


def test_knee_brace_resolves_to_a_raked_wood_member(catlin_model) -> None:
    """The brace is a stick of lumber, not a marker: a raked member on a 45-degree run.

    ``ResolvedSolid`` only extrudes a plan outline vertically, so modelling the diagonal as
    a solid would mean a stack of bands — and the solids take-off would bill each band as
    its own piece of structure. A ``FramedMember`` rakes natively and lands in the cut list.
    """
    brace = next(b for b in catlin_model.braces if b.tag == "KB-SG-F1-NS")
    member, = brace.members
    assert member.category == "brace"
    assert member.profile == "2x6"
    assert member.z0_end_m is not None and member.z1_end_m is not None
    # A 45-degree brace rises exactly as far as it runs.
    leg = math.hypot(member.p1[0] - member.p0[0], member.p1[1] - member.p0[1])
    assert leg == pytest.approx(3 * FT)
    assert member.z1_end_m - member.z1_m == pytest.approx(leg)
    assert member.length_m == pytest.approx(leg * math.sqrt(2))
    # It lands on the beam soffit, and leaves from the post face rather than its centre —
    # an end buried in the column reads as a member clash.
    assert member.z1_end_m == pytest.approx(8.625 * FT)
    post_centre_y = -9.5 * FT
    assert abs(member.p0[1] - post_centre_y) == pytest.approx(2.75 * 0.0254)


def test_balcony_braces_reach_two_different_soffits(catlin_model) -> None:
    """The E-W girt hangs under the N-S beam, so the two braces at a corner are not level.

    This is why the brace carries its own soffit instead of deriving one from its storey.
    """
    ns = next(b for b in catlin_model.braces if b.tag == "KB-SG-R1-NS").members[0]
    ew = next(b for b in catlin_model.braces if b.tag == "KB-SG-R1-EW").members[0]
    assert ns.z1_end_m == pytest.approx(8.625 * FT)  # N-S beam soffit
    assert ew.z1_end_m == pytest.approx(8.0208333 * FT)  # a 2x8 girt depth lower
    # Both feet stay well above the pillar base at the railing top (3.583').
    assert min(ns.z0_m, ew.z0_m) > 4.0 * FT
    # Every brace is in the framing cut list, so a framer orders the lumber.
    braced = [m for m in catlin_model.all_members() if m.category == "brace"]
    assert len(braced) == 8


def test_balcony_girts_hang_at_the_true_beam_soffit(catlin_model) -> None:
    """``Beam.top_elevation`` places the girts, and perturbs nothing that derives its own.

    The N-S beams get their drop from the deck joists that bear on them; the girts carry no
    joists, so without an authored top they would hang from the storey datum and collide
    with the deck.
    """
    solids = {s.tag: s for s in catlin_model.solids}
    for tag in ("BM-SG-GIRT-R", "BM-SG-GIRT-F"):
        assert solids[tag].z1_m == pytest.approx(8.625 * FT)
        assert solids[tag].z0_m == pytest.approx(8.0208333 * FT)  # 2-2x8
    for tag in ("BM-SG-BLW", "BM-SG-BLC", "BM-SG-BLE"):
        assert solids[tag].z0_m == pytest.approx(8.625 * FT)
        assert solids[tag].z1_m == pytest.approx(9.3958333 * FT)
    # The girts name their pillars for the schedule but carry no joists, so the pillars
    # keep the heights the deck joists gave them (the rear row 2" high for drainage).
    assert solids["PT-SG-BF1"].z1_m == pytest.approx(8.625 * FT)
    assert solids["PT-SG-BR1"].z1_m == pytest.approx(8.7916667 * FT)


def test_catlin_dowels_and_foam_bridge_the_footing_joint(catlin_model) -> None:
    dowels = _solids(catlin_model, "dowel")
    foam = _solids(catlin_model, "thermal_break")
    assert len(dowels) == 9  # 3 locations x 3 bars
    assert len(foam) == 3
    # Bars sit at mid-footing (~ -9.25') and span ~24" across the joint.
    for bar in dowels:
        assert bar.z0_m < -2.5 < bar.z1_m or abs((bar.z1_m + bar.z0_m) / 2 + 9.25 * FT) < 0.2


def test_foam_thermal_break_lies_in_the_joint_it_breaks(catlin_model) -> None:
    """The block's thin dimension is the dowel axis; its long one runs along the joint.

    Catlin's dowels run N-S (``axis="y"``) between the house and the sunken-garden footings,
    so each 2" block must be 2" deep in Y and span the bar row in X. Rotated 90° it stops
    separating the two structures at all.
    """
    for block in _solids(catlin_model, "thermal_break"):
        xs = [x for x, _ in block.outline]
        ys = [y for _, y in block.outline]
        depth_across_joint = max(ys) - min(ys)
        run_along_joint = max(xs) - min(xs)
        assert abs(depth_across_joint - inch(2).meters) < 1e-9
        assert run_along_joint > depth_across_joint


def test_foam_thermal_break_follows_an_east_west_dowel(catlin_model) -> None:
    """The same rule with the axis flipped — guards against hard-coding Catlin's Y run."""
    from typehaus.resolve.accessories import _resolve_dowel

    model = catlin_model
    before = len(model.solids)
    east_west = Dowel(uid="AAAAAAAAAC", tag="DW-EW", position=pt(ft(0), ft(0)), axis="x",
                      length=inch(24), diameter=inch(0.625), elevation=ft(0), count=3,
                      spacing=inch(8), foam_thickness=inch(2))
    try:
        _resolve_dowel(model, east_west, "basement")
        block = next(s for s in model.solids if s.tag == "DW-EW-FOAM")
        xs = [x for x, _ in block.outline]
        ys = [y for _, y in block.outline]
        assert abs(max(xs) - min(xs) - inch(2).meters) < 1e-9  # thin along the bar axis
        assert max(ys) - min(ys) > max(xs) - min(xs)  # long along the joint
    finally:
        del model.solids[before:]


def test_catlin_vent_routes_up_out_up_to_above_roof(catlin_model) -> None:
    from typehaus.resolve.roof_geometry import roof_height_at

    vent = _solids(catlin_model, "vent")
    chases = [s for s in vent if s.tag.endswith("CHASE")]
    terms = [s for s in vent if s.tag.endswith("TERM")]
    outs = [s for s in vent if "-OUT" in s.tag]
    from typehaus.resolve.accessories import _PIPE_SWEEP_BANDS

    assert len(chases) == len(terms) == 2  # radon + plumbing vent
    assert len(outs) == 2 * _PIPE_SWEEP_BANDS  # each horizontal jog is one swept stack
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
    # ~28.05': eave_z_m is the deck plane, ~10.7" above the knee-wall plate (golden eave
    # detail), so the derived termination rides that much higher than the bare-plate datum.
    assert expected < 29 * FT
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


def test_vent_horizontal_jog_sweeps_the_same_polygon_as_the_risers(catlin_model) -> None:
    """The jog used to be four stacked square bands next to two true 12-gon risers.

    A horizontal run cannot be a vertical prism, so it is swept as bands in Z. Matching the
    risers means the band boundaries land on the riser polygon's own vertex elevations —
    ``_PIPE_FACETS // 2`` bands, i.e. ``_PIPE_FACETS // 2 + 1`` distinct heights, with each
    band as wide as the circle is at that height.
    """
    from typehaus.resolve.accessories import _PIPE_FACETS, _PIPE_SWEEP_BANDS

    radius = inch(3).meters / 2.0
    jogs = [s for s in _solids(catlin_model, "vent") if "-OUT" in s.tag]
    per_riser = {}
    for band in jogs:
        per_riser.setdefault(band.tag.rsplit("-OUT", 1)[0], []).append(band)

    for riser_tag, bands in per_riser.items():
        assert len(bands) == _PIPE_SWEEP_BANDS, riser_tag
        heights = sorted({round(z, 9) for band in bands for z in (band.z0_m, band.z1_m)})
        assert len(heights) == _PIPE_FACETS // 2 + 1  # the 12-gon section, on its side
        # Section spans the true diameter, and no band is wider than the pipe.
        assert abs((heights[-1] - heights[0]) - 2 * radius) < 1e-9
        section_area = 0.0
        for band in bands:
            width = max(x for x, _ in band.outline) - min(x for x, _ in band.outline)
            assert width <= 2 * radius + 1e-9
            section_area += width * (band.z1_m - band.z0_m)
        # Roundness: the swept section's area tracks the circle's. Four bands were 2.6% shy
        # of it (visibly square); the riser's 12-gon resolution closes that to ~1.1%.
        assert abs(section_area - math.pi * radius**2) / (math.pi * radius**2) < 0.015


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
    """42" is measured from the surface underfoot, not from the storey datum.

    The aluminum boards sit *on* the joists whose tops define the datum, so a guard based
    on the datum stands only 40.5" above the deck someone actually walks on.
    """
    deck = next(s for s in catlin_model.solids if s.tag == "SL-SG-DECK")
    posts = [s for s in _solids(catlin_model, "railing") if "POST" in s.tag]
    assert posts, "railing posts expected"
    for post in posts:
        assert math.isclose(post.z0_m, deck.z1_m, abs_tol=0.02), "guard must start on the boards"
        assert math.isclose(post.z1_m - deck.z1_m, 3.5 * FT, abs_tol=0.02)


def test_catlin_sump_sits_below_the_basement_slab(catlin_model) -> None:
    sumps = _solids(catlin_model, "sump")
    assert len(sumps) == 1
    assert sumps[0].z0_m < sumps[0].z1_m <= 0.0


def test_catlin_house_roof_eave_trim_closes_the_eave(catlin_model) -> None:
    """Tier 2 roof-eave closure on RF-HOUSE: fascia is *derived* from Roof.eave_trim
    (resolve/roof_edge.py, so it rides the deck-plane datum on every edge); the 6" box
    gutter + drip edge are authored runs along both eave edges (west/east — the ridge
    runs N-S), at elevations tied to the deck plane per the golden eave detail. Garage
    gutter/drip stay deferred with the truss roof."""
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    eave, plate = roof.eave_z_m, roof.bearing_z_m
    # Derived fascia members: two boards per edge run (spf sub-fascia + aluminum face),
    # topping out on the roof plane at the eaves and closing down past the plate.
    fascia = [m for m in roof.members if m.category == "fascia"]
    runs = {m.child_key.rsplit("-fascia-", 1)[0] for m in fascia}
    assert {"eave-lo", "eave-hi", "rake-lo-0", "rake-lo-1", "rake-hi-0", "rake-hi-1"} <= runs
    # The outboard face board rides up over the deck + membrane edge (1" perpendicular,
    # slope-corrected) to the foam underside; the sub-fascia nailer under the deck still
    # tops out on the plane. Both close down past the plate.
    rise = inch(1.0).meters * math.hypot(1.0, 4.0 / 12.0)
    for member in fascia:
        if member.child_key.startswith("eave"):
            top = eave if member.child_key.endswith("-0") else eave + rise
            assert member.z1_m == pytest.approx(top)
            assert member.z0_m <= plate - inch(1.5).meters
    # No hand-authored fascia solids — that would double the derived band.
    assert not [s for s in catlin_model.solids if s.tag.startswith("TR-RF-FASCIA")]
    for side in ("W", "E"):
        gutter = next(s for s in catlin_model.solids if s.tag == f"TR-RF-GUTTER-{side}-1")
        drip = next(s for s in catlin_model.solids if s.tag == f"TR-RF-DRIP-{side}-1")
        assert (gutter.category, drip.category) == ("gutter", "flashing")
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
