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
                     "fascia", "gutter", "downspout", "flashing", "sump", "vent"):
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


def test_knee_brace_hardware_resolves_as_a_band_at_each_end(catlin_model) -> None:
    """The APVKB kit is a pair of wrap-around straps, so the hardware reads at both
    joints — a band hugging the member's z-band at the beam/girt end and another at the
    post end — instead of the single floating marker box the old spelling drew."""
    member = next(b for b in catlin_model.braces if b.tag == "KB-SG-R1-NS").members[0]
    solids = {s.tag: s for s in catlin_model.solids}
    top = solids["KB-SG-R1-NS-APVKB45-6-TOP"]
    bottom = solids["KB-SG-R1-NS-APVKB45-6-BOT"]
    assert top.category == bottom.category == "connector"
    soffit = 8.625 * FT
    assert top.z1_m == pytest.approx(soffit)
    assert bottom.z1_m == pytest.approx(soffit - 3 * FT)  # down the 3' leg, at the post
    # Each band spans exactly the end-grain z-band of the wood it wraps.
    assert top.z1_m - top.z0_m == pytest.approx(member.z1_m - member.z0_m)
    assert bottom.z1_m - bottom.z0_m == pytest.approx(member.z1_m - member.z0_m)
    # And no marker boxes remain anywhere.
    assert not any(tag.endswith("-CONN") for tag in solids)


def test_balcony_braces_reach_the_shared_pillar_top_soffit(catlin_model) -> None:
    """The girt segments ride the pillar tops beside the N-S beams now, so the two braces
    at a corner are level at the resolved pillar-top plane. The brace still carries its own
    soffit rather than deriving one from its storey — the members a post is braced to need
    not share an elevation in general; since the girt third pass these two happen to."""
    ns = next(b for b in catlin_model.braces if b.tag == "KB-SG-R1-NS").members[0]
    ew = next(b for b in catlin_model.braces if b.tag == "KB-SG-R1-EW").members[0]
    assert ns.z1_end_m == pytest.approx(8.625 * FT)  # N-S beam soffit
    assert ew.z1_end_m == pytest.approx(8.625 * FT)  # girt soffit — the same plane now
    # Both feet stay well above the pillar base at the railing top (3.583').
    assert min(ns.z0_m, ew.z0_m) > 4.0 * FT
    # Every brace is in the framing cut list, so a framer orders the lumber.
    braced = [m for m in catlin_model.all_members() if m.category == "brace"]
    assert len(braced) == 8


def test_balcony_girts_sit_flush_with_the_beams(catlin_model) -> None:
    """``Beam.top_elevation`` places the girts, and perturbs nothing that derives its own.

    The N-S beams get their drop from the deck joists that bear on them; the girt segments
    carry no joists, so without an authored top they would hang from the storey datum and
    collide with the deck. Since the third pass they sit ON the pillar tops in the beams'
    own band: 2x10, soffit at the resolved pillar-top plane, tops flush with the beams.
    """
    solids = {s.tag: s for s in catlin_model.solids}
    for tag in ("BM-SG-GIRT-RW", "BM-SG-GIRT-RE", "BM-SG-GIRT-FW", "BM-SG-GIRT-FE"):
        assert solids[tag].z1_m == pytest.approx(9.3958333 * FT)
        assert solids[tag].z0_m == pytest.approx(8.625 * FT)  # 2x10 on the pillar tops
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
    from typehaus.resolve.roof_layer_setbacks import above_structure_layers

    vent = _solids(catlin_model, "vent")
    chases = [s for s in vent if s.tag.endswith("CHASE")]
    terms = [s for s in vent if s.tag.endswith("TERM")]
    outs = [s for s in vent if "-OUT" in s.tag]
    from typehaus.resolve.accessories import _PIPE_SWEEP_BANDS

    assert len(chases) == len(terms) == 2  # radon + plumbing vent
    assert len(outs) == 2 * _PIPE_SWEEP_BANDS  # each horizontal jog is one swept stack
    exit_z = ft(23, 10).meters
    # Chase rises from below grade to the turn-out, which stays *under* the rake.
    for c in chases:
        assert c.z0_m < -2.0 and abs(c.z1_m - exit_z) < 0.05
    for o in outs:
        assert abs((o.z0_m + o.z1_m) / 2 - exit_z) < inch(2).meters
    # Termination is derived: 12" above the true roof surface at the exterior riser (moved
    # to the NW corner, x=1', 2026-07-28), not the 33' that was once authored — that sat 2'
    # above the ridge of this 4:12 gable.
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    assembly = catlin_model.plan.library.resolve_assembly(roof.assembly)
    skin = sum(layer.thickness.meters for layer in above_structure_layers(assembly))
    expected = roof_height_at(roof, (ft(1).meters, ft(37).meters)) + skin + inch(12).meters
    # ~27.9': eave_z_m is the deck plane, and the CATLIN_ROOF skin (foam+furring+
    # standing-seam) adds another 8.5" above that deck plane, so the derived termination
    # rides that much higher than the bare-plate datum.
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
    posts = [s for s in _solids(catlin_model, "railing")
             if "RL-SG-BALCONY" in s.tag and "POST" in s.tag]
    assert posts, "railing posts expected"
    for post in posts:
        assert math.isclose(post.z0_m, deck.z1_m, abs_tol=0.02), "guard must start on the boards"
        assert math.isclose(post.z1_m - deck.z1_m, 3.5 * FT, abs_tol=0.02)


def test_catlin_stair_guard_still_resolves_flat(catlin_model) -> None:
    """A guard with no ``serves_stair`` extrudes at one elevation, exactly as before the
    raking branch existed: posts ride the authored base, rails sit at fixed levels.
    Regression pin for the ``serves_stair`` fork in ``_resolve_railing``."""
    posts = [s for s in catlin_model.solids if s.tag.startswith("RL-S-STAIR-POST")]
    rails = [s for s in catlin_model.solids if s.tag.startswith("RL-S-STAIR-RAIL")]
    assert posts and rails
    base, top = 10 * FT, 13.5 * FT
    assert all(math.isclose(p.z0_m, base, abs_tol=1e-9) for p in posts)
    assert all(math.isclose(p.z1_m, top, abs_tol=1e-9) for p in posts)
    rail_half = 0.75 * 0.0254
    centres = {round(r.z0_m + rail_half, 4) for r in rails}
    assert centres == {round(base, 4), round(top, 4)}  # rail_count=2: bottom + top rail


def test_catlin_stair_handrail_rakes_along_the_flight(catlin_model) -> None:
    """A ``serves_stair`` handrail slopes with its flight: each post stands on the nosing
    line under it and rises ``top_height``, and the rail bands climb monotonically instead
    of extruding one horizontal bar over the stair (the gap this branch closes)."""
    def along_y(solid):
        return min(y for _, y in solid.outline)

    posts = sorted((s for s in catlin_model.solids
                    if s.tag.startswith("RL-S-HANDRAIL-E-POST")), key=along_y)
    assert len(posts) >= 2
    # ST-M2S lower flight: first tread top one riser above the main floor, landing at the
    # far end — the posts stand on the walking line, not on the authored base_elevation.
    assert posts[0].z0_m == pytest.approx(0.1905, abs=1e-3)
    assert posts[-1].z0_m == pytest.approx(1.524, abs=1e-3)
    rail_h = 36 * 0.0254
    for post in posts:
        assert post.z1_m - post.z0_m == pytest.approx(rail_h)
    bands = sorted((s for s in catlin_model.solids
                    if s.tag.startswith("RL-S-HANDRAIL-E-RAIL")), key=along_y)
    zs = [band.z0_m for band in bands]
    assert len(zs) >= 4
    assert zs == sorted(zs), "rail bands must climb with the flight"
    assert zs[-1] - zs[0] > 1.0  # the full ~4'4" rise of the lower flight
    # The top band's rail rides ~top_height above the walking line under it (its own
    # band-mid station on the slope, a shade under the landing edge's 1.524 m).
    assert 1.524 + rail_h - 0.15 < bands[-1].z1_m < 1.524 + rail_h + 0.05


def test_knee_brace_member_carries_its_paint_material(catlin_model) -> None:
    """``KneeBrace.assembly`` reduces to its structure layer's material on the resolved
    member (the IR slot both emitters read), and the glTF palette resolves that ref to
    the authored white rather than the bare "brace" category lumber."""
    from typehaus.emit.gltf.palette import _hex_rgba, _material_finish_color

    for brace in catlin_model.braces:
        assert brace.members[0].material == "post-paint-white", brace.tag
    assert (_material_finish_color("post-paint-white", "brace")
            == _hex_rgba("#f4f2ee"))


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
    # The house eave has no fascia: siding and roofing are one continuous standing-seam
    # skin over the flush edge, so the resolver emits corner trim at the joint instead of
    # fascia boards and an edge-cladding band.
    assert not [m for m in roof.members if m.category == "fascia"]
    corner_trim = [m for m in roof.members if m.category == "corner_trim"]
    # Six runs (two eaves + four rake halves), each a formed section of cleat / face / hem.
    assert len(corner_trim) == 18
    assert {m.child_key.rsplit("-", 1)[1] for m in corner_trim} == {"cleat", "face", "hem"}
    for member in corner_trim:
        assert member.z1_m > eave
    # No hand-authored fascia solids — that would double the derived band.
    assert not [s for s in catlin_model.solids if s.tag.startswith("TR-RF-FASCIA")]
    for side in ("W", "E"):
        # Both runs are *formed* metal, so each resolves into its section's bands rather than
        # one solid bar: the gutter into an open-top U, the drip edge into a lap leg and a
        # turn-down. Where those bands sit relative to each other — the lap chain the eave
        # depends on — is pinned in test_catlin_eave_water.py; this is the envelope.
        bands = [s for s in catlin_model.solids
                 if s.tag.startswith(f"TR-RF-GUTTER-{side}-1-")]
        assert {s.tag.rsplit("-", 1)[1] for s in bands} == {"BACK", "BOTTOM", "FRONT"}
        drip = [s for s in catlin_model.solids if s.tag.startswith(f"TR-RF-DRIP-{side}-1-")]
        assert {s.tag.rsplit("-", 1)[1] for s in drip} == {"LAP", "DRIP"}
        assert {s.category for s in bands} == {"gutter"}
        assert {s.category for s in drip} == {"flashing"}
        gutter_top, gutter_bottom = max(s.z1_m for s in bands), min(s.z0_m for s in bands)
        # 5" of channel, its rim high enough to lap behind the corner trim's 2" leg and low
        # enough to leave the eave end of the roof's vent channel open.
        assert gutter_top - gutter_bottom == pytest.approx(inch(5.0).meters)
        vent_slot = eave + inch(7.25 * math.hypot(1.0, 4.0 / 12.0)).meters
        assert gutter_top < vent_slot, "the rim would dam the eave vent slot"
        # The drip's turn-down ends inside the trough, below the rim it empties over.
        assert min(s.z0_m for s in drip) < gutter_top
    # Each eave drains to a leader, so the gutters' slope notes point somewhere real.
    leaders = [s for s in catlin_model.solids if s.tag.startswith("TR-RF-LEADER-")]
    assert {s.tag for s in leaders} == {"TR-RF-LEADER-W", "TR-RF-LEADER-E"}
    assert not [s for s in catlin_model.solids if s.tag.startswith("TR-RF-")
                and "GARAGE" in s.tag]


def test_authored_gutters_resolve_as_open_top_channels(catlin_model) -> None:
    """An authored gutter is a trough, not a billet: rain has to be able to fall into it.

    Every authored ``Gutter`` run resolves into three bands per path segment — back, floor,
    front — and the floor sits a shell's thickness above the bottom of the channel. What
    makes it *open* is the negative: at the channel's own top elevation nothing spans the
    full width, so a section cut at the rim is two thin sheets with air between them.
    """
    from typehaus.resolve.trim_bands import GUTTER_SHELL_M

    runs = [el for el in catlin_model.plan.all_elements() if isinstance(el, Gutter)]
    assert runs, "the catlin house authors gutter runs"
    for run in runs:
        segments = len(run.path) - 1
        bands = [s for s in catlin_model.solids if s.tag.startswith(f"{run.tag}-")]
        assert len(bands) == 3 * segments, f"{run.tag}: 3 bands per segment"
        depth, thickness = run.depth.meters, run.thickness.meters
        shell = min(GUTTER_SHELL_M, thickness / 3.0, depth / 3.0)
        top = run.top_elevation.meters
        for index in range(1, segments + 1):
            keys = {s.tag.rsplit("-", 1)[1]: s for s in bands
                    if s.tag.startswith(f"{run.tag}-{index}-")}
            assert set(keys) == {"BACK", "BOTTOM", "FRONT"}
            # The floor of the trough: its top is one shell above the channel's bottom.
            assert keys["BOTTOM"].z0_m == pytest.approx(top - depth)
            assert keys["BOTTOM"].z1_m == pytest.approx(top - depth + shell)
            # Open at the rim: only the two thin sheets reach the top elevation, and
            # neither is anywhere near the full channel width.
            at_rim = [s for s in keys.values() if s.z1_m > top - 1e-9]
            assert {s.tag.rsplit("-", 1)[1] for s in at_rim} == {"BACK", "FRONT"}
            for sheet in at_rim:
                width = min(_span(sheet.outline, axis) for axis in (0, 1))
                assert width < thickness - shell


def _span(outline, axis: int) -> float:
    """Extent of a plan outline along x (0) or y (1) — the band's own thin dimension."""
    values = [point[axis] for point in outline]
    return max(values) - min(values)


def test_gltf_emits_with_accessories(catlin_model) -> None:
    from typehaus.emit.gltf.emitter import emit_gltf_dict

    gltf, blob = emit_gltf_dict(catlin_model)
    assert gltf["materials"] and blob, "glTF should build with accessory solids"


# --- rainscreen bug screens (derived, not authored) ----------------------------------------

def test_every_rainscreen_wall_base_is_screened(catlin_model) -> None:
    """The vent closure is derived from the wall stack, so coverage is automatic.

    An open rainscreen cavity at the base of the standing seam is an insect route straight
    up behind the cladding. Nothing about it is authored per wall — the rule reads the
    assembly — so a new exterior wall cannot ship without one, which is the whole point of
    deriving it rather than hand-placing runs.
    """
    from typehaus.resolve.accessories import screens_rainscreen_base

    screens = {s.tag.replace("-BUGSCREEN", ""): s
               for s in catlin_model.solids if s.category == TrimKind.BUG_SCREEN.value}
    assert screens, "a standing-seam rainscreen house resolves bug screens"
    expected = {wall.tag for wall in catlin_model.walls
                if screens_rainscreen_base(catlin_model, wall)}
    assert set(screens) == expected
    # Both rainscreen families are covered: the house wall and the garage wall.
    assert {"W-M-S1", "W-G-S"} <= expected


def test_a_screen_sits_in_the_cavity_it_closes_at_the_cladding_start(catlin_model) -> None:
    """Depth is the rainscreen cavity's own thickness and elevation is the wall base — both
    read off the wall, so re-sizing the battens moves the strip with them."""
    from typehaus.resolve.accessories import (
        BUG_SCREEN_HEIGHT_IN,
        rainscreen_cavity_m,
    )

    wall = next(w for w in catlin_model.walls if w.tag == "W-M-S1")
    screen = next(s for s in catlin_model.solids
                  if s.tag == "W-M-S1-BUGSCREEN")
    assert screen.z0_m == pytest.approx(wall.z0_m)
    assert screen.z1_m - screen.z0_m == pytest.approx(inch(BUG_SCREEN_HEIGHT_IN).meters)
    furring = next(ly for ly in wall.depth_layers() if ly.function == "furring")
    assert list(screen.outline) == list(furring.polygon)
    assert rainscreen_cavity_m(wall.depth_layers()) == pytest.approx(furring.thickness_m)


def test_a_stacked_storey_does_not_get_a_second_screen(catlin_model) -> None:
    """The cladding and its cavity run past the floor line, so there is no cladding start
    at the second storey to screen. Screening every wall would triple the order."""
    stacked = [w for w in catlin_model.walls if w.storey in ("second", "attic")]
    assert stacked, "the fixture must actually have stacked storeys for this to mean anything"
    screened = {s.tag for s in catlin_model.solids
                if s.category == TrimKind.BUG_SCREEN.value}
    assert not [w for w in stacked if f"{w.tag}-BUGSCREEN" in screened]


def test_an_interior_partition_is_never_screened(catlin_model) -> None:
    """The predicate is a FURRING layer with CLADDING outboard of it — a service chase or a
    bare partition has no cavity to close, and must not order strip."""
    from typehaus.resolve.accessories import rainscreen_cavity_m

    interior = [w for w in catlin_model.walls
                if not any(ly.function == "cladding" for ly in w.depth_layers())]
    assert interior
    assert all(rainscreen_cavity_m(w.depth_layers()) is None for w in interior)
