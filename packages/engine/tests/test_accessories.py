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


def _balcony_deck_top(model) -> float:
    """Top of the aluminium boards over FS-SG-DECK — the balcony walking surface.

    There is no SL-SG-DECK slab standing in for it any more (2026-08-22): the plank is the
    floor system's own ``subfloor``, so the surface underfoot is the resolved deck sheet.
    """
    deck = next(f for f in model.floors if f.tag == "FS-SG-DECK")
    assert deck.deck_z1_m > deck.deck_z0_m, "FS-SG-DECK must resolve a deck sheet"
    return deck.deck_z1_m


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
    assert member.z1_end_m == pytest.approx(8.4583333 * FT)
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
    soffit = 8.4583333 * FT  # the pillar-top plane, 2" down since the 3-2x12 beams
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
    # 8.458', not the 8.625' this was until 2026-08-23: the beams went 3-2x10 -> 3-2x12 to
    # clear IRC Table R507.5(1), and the whole pillar-top band came down 2" with them.
    assert ns.z1_end_m == pytest.approx(8.4583333 * FT)  # N-S beam soffit
    assert ew.z1_end_m == pytest.approx(8.4583333 * FT)  # girt soffit — the same plane now
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
    own band: soffit at the resolved pillar-top plane, tops flush with the beams.

    The girts share the beams' depth by construction (SPEC.balcony_girt), so when the beams
    went 3-2x10 -> 3-2x12 on 2026-08-23 the girts went 2x10 -> 2x12 with them. Flushness is
    the invariant, and it is why the TOP plane below is unchanged from the 2x10 era while
    the soffit dropped 2": depth +2", soffit -2".
    """
    solids = {s.tag: s for s in catlin_model.solids}
    for tag in ("BM-SG-GIRT-RW", "BM-SG-GIRT-RE", "BM-SG-GIRT-FW", "BM-SG-GIRT-FE"):
        assert solids[tag].z1_m == pytest.approx(9.3958333 * FT)
        assert solids[tag].z0_m == pytest.approx(8.4583333 * FT)  # 2x12 on the pillar tops
    for tag in ("BM-SG-BLW", "BM-SG-BLC", "BM-SG-BLE"):
        assert solids[tag].z0_m == pytest.approx(8.4583333 * FT)
        assert solids[tag].z1_m == pytest.approx(9.3958333 * FT)
    # The girts name their pillars for the schedule but carry no joists, so the pillars
    # keep the heights the deck joists gave them (the rear row 2" high for drainage).
    assert solids["PT-SG-BF1"].z1_m == pytest.approx(8.4583333 * FT)
    assert solids["PT-SG-BR1"].z1_m == pytest.approx(8.625 * FT)


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
    jog_z = ft(19, 6).meters
    # ** THE CHASE STOPS AT THE JOG SINCE 2026-08-29, AND -CHASE2 CARRIES ON ABOVE IT. **
    # The riser rises from below grade at x=1'-0" as it always did, but the attic's 6:12
    # roof underside there is 20'-8 1/4" — it cannot reach the 23'-10" wall exit at that
    # station. `VentRun.chase_offset` steps it 12'-4" east inside FS-ATTIC's I-joist band
    # (through the webs) and it stands up again at x=13'-4". No roof penetration, and the
    # chase itself does not move through any storey below.
    chase2 = [s for s in vent if s.tag.endswith("CHASE2")]
    assert len(chase2) == 2
    for c in chases:
        assert c.z0_m < -2.0 and abs(c.z1_m - jog_z) < 0.05
    for c in chase2:
        assert abs(c.z0_m - jog_z) < 0.05 and abs(c.z1_m - exit_z) < 0.05
    jogs = [s for s in vent if "-JOG" in s.tag]
    assert len(jogs) == 2 * _PIPE_SWEEP_BANDS
    for j in jogs:
        assert abs((j.z0_m + j.z1_m) / 2 - jog_z) < inch(2).meters
    for o in outs:
        assert abs((o.z0_m + o.z1_m) / 2 - exit_z) < inch(2).meters
    # Termination is derived: 12" above the true roof surface at the exterior riser — now at
    # x=13'-4" with the jog — not the 33' that was once authored.
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    assembly = catlin_model.plan.library.resolve_assembly(roof.assembly)
    skin = sum(layer.thickness.meters for layer in above_structure_layers(assembly))
    expected = roof_height_at(roof, (ft(13, 4).meters, ft(37).meters)) + skin + inch(12).meters
    # eave_z_m is the deck plane, and the CATLIN_ROOF skin (zip + vapour barrier +
    # foam + nailbase deck + underlayment + vent mat + standing seam) adds another 7.975"
    # above that deck plane, so the derived termination rides that much higher than the
    # bare-plate datum. The skin is summed here rather than written down, so a roof rebuild
    # moves the vent with it — 2026-08-20 took it from 8.5" to 7.975" and nothing broke.
    # ~29'-7" since 2026-08-29: the jog stands the riser at x=13'-4", four feet closer to
    # the ridge, and a 6:12 plane climbs twice as fast as the 4:12 it replaced. It is still
    # BELOW the 30'-3" ridge, which is the claim that matters — a termination over the ridge
    # is a pipe with no roof under it.
    assert expected < 30 * FT
    assert expected < roof.ridge_z_m
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
    deck_top = _balcony_deck_top(catlin_model)
    posts = [s for s in _solids(catlin_model, "railing")
             if "RL-SG-BALCONY" in s.tag and "POST" in s.tag]
    assert posts, "railing posts expected"
    for post in posts:
        assert math.isclose(post.z0_m, deck_top, abs_tol=0.02), "guard must start on the boards"
        assert math.isclose(post.z1_m - deck_top, 3.5 * FT, abs_tol=0.02)


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
    """A ``serves_stair`` handrail slopes with its flight: its rail bands climb
    monotonically instead of extruding one horizontal bar over the stair, and the brackets
    that carry it rise with them.

    It used to be posts. ``Railing.mount`` was authored ``"wall"`` on every handrail in this
    house and read by nothing, so a 36" floor post stood at every station of a rail that is
    screwed to a wall — see ``test_railing_geometry.py`` for that half.
    """
    def along_y(solid):
        return min(y for _, y in solid.outline)

    brackets = sorted((s for s in catlin_model.solids
                       if s.tag.startswith("RL-S-HANDRAIL-E-BRACKET")), key=along_y)
    assert len(brackets) >= 2
    rail_h = 36 * 0.0254
    # ST-M2S lower flight: first tread top one riser above the main floor, landing at the
    # far end — the rail rides the walking line, not the authored base_elevation.
    assert brackets[0].z1_m == pytest.approx(0.1905 + rail_h, abs=2e-2)
    assert brackets[-1].z1_m == pytest.approx(1.524 + rail_h, abs=2e-2)
    for bracket in brackets:
        assert bracket.z1_m - bracket.z0_m < 6 * 0.0254, "a bracket, not a post"
    # The rail is ONE solid now, carrying the 3D polyline it used to be chopped into bands to
    # approximate (→ resolve/sweep.py), so the rake is read off that path rather than off a
    # stack of pieces sorted along y.
    rails = [s for s in catlin_model.solids
             if s.tag.startswith("RL-S-HANDRAIL-E-RAIL") and s.sweep is not None]
    assert len(rails) == 1, "a handrail is one bar, cut once and ordered once"
    path = sorted(rails[0].sweep.path, key=lambda point: point[1])
    zs = [z for _x, _y, z in path]
    assert zs == sorted(zs), "the rail must climb with the flight"
    assert zs[-1] - zs[0] > 1.0  # the full ~4'4" rise of the lower flight
    assert 1.524 + rail_h - 0.15 < zs[-1] < 1.524 + rail_h + 0.05


def _bay_pickets(model, tag):
    """The balcony guard's pickets grouped into their bays, ordered along each bay.

    The bay walk is recomputed from the element rather than read off the solids, so this is
    a genuine cross-check: the pickets have to land where the posts say the bays are.
    """
    from typehaus.resolve.geometry import length, normal, project_onto_axis, sub, unit
    from typehaus.resolve.railings import railing_post_stations

    guard = model.plan.by_tag(tag)
    pickets = [s for s in model.solids
               if s.category == "railing_infill" and s.tag.startswith(f"{tag}-")]
    path = [p.xy_m for p in guard.path]
    stations = railing_post_stations(path, max(guard.post_spacing.meters, 0.3))
    bays = []
    for a, b in zip(stations[:-1], stations[1:]):
        run = length(sub(b, a))
        axis, across = unit(sub(b, a)), normal(sub(b, a))
        here = []
        for picket in pickets:
            us = [project_onto_axis(point, a, axis) for point in picket.outline]
            offsets = [abs(project_onto_axis(point, a, across)) for point in picket.outline]
            if -1e-6 <= (min(us) + max(us)) / 2.0 <= run + 1e-6 and min(offsets) <= 0.05:
                here.append(((min(us) + max(us)) / 2.0, max(us) - min(us)))
        bays.append(sorted(here))
    return bays


def test_catlin_balcony_guard_draws_its_balusters(catlin_model) -> None:
    """The defect this infill closes: ``RL-SG-BALCONY`` authored ``infill="balusters",
    baluster_spacing=4"`` and drew two horizontal bars with 40" of daylight between them,
    while the R312.1.3 check passed on the authored field alone. The pickets exist now, they
    stand on the deck-walking-surface datum the guard is measured from, and they stop short
    of both rails so they tuck under the banded rail instead of poking through it."""
    deck_top = _balcony_deck_top(catlin_model)
    pickets = [s for s in catlin_model.solids
               if s.category == "railing_infill" and s.tag.startswith("RL-SG-BALCONY-")]
    assert len(pickets) > 80, "a 38' guard at a 4\" clear gap is ~90 pickets"
    rail_half = 0.75 * 0.0254
    for picket in pickets:
        assert math.isclose(picket.z0_m, deck_top + rail_half, abs_tol=1e-9), (
            "a picket's foot sits on the walking surface, trimmed under the bottom rail")
        assert math.isclose(picket.z1_m, deck_top + 3.5 * FT - rail_half, abs_tol=1e-9), (
            "...and its head stops under the top rail")


def test_catlin_balcony_pickets_reconcile_against_the_sphere_rule(catlin_model) -> None:
    """Per bay: every clear gap is at or under 4", AND one fewer picket would open one that
    is not. The second half is what a ``<=``-only assert cannot catch — an off-by-one that
    adds a picket passes the rule and bills the owner for metal nobody needs."""
    gap_limit = 4 * 0.0254
    for bay in _bay_pickets(catlin_model, "RL-SG-BALCONY"):
        assert bay, "every bay of a baluster guard carries pickets"
        width = bay[0][1]
        gaps = [b_centre - a_centre - width for (a_centre, _w), (b_centre, _w2)
                in zip(bay, bay[1:])]
        assert gaps, "a bay with one picket cannot demonstrate a gap"
        assert max(gaps) <= gap_limit + 1e-9, (
            f"drawn gap {max(gaps) / 0.0254:.3f}\" exceeds the 4\" sphere")
        # Minimality: the same clear span with one fewer picket must break the rule.
        count = len(bay)
        clear = count * width + sum(gaps) + 2 * gaps[0]
        fewer = count - 1
        assert (clear - fewer * width) / (fewer + 1) > gap_limit - 1e-9, (
            "the picket count is not the smallest that satisfies R312.1.3")


def test_catlin_handrails_get_no_infill(catlin_model) -> None:
    """``role == "handrail"`` is the gate, and it is the same predicate the R312.1.3 census
    uses — a handrail is not a guard and has nothing to fill."""
    for tag in ("RL-A-HANDRAIL", "RL-M-HANDRAIL-E", "RL-M-HANDRAIL-W",
                "RL-S-HANDRAIL-E", "RL-S-HANDRAIL-W"):
        assert not [s for s in catlin_model.solids
                    if s.tag.startswith(f"{tag}-")
                    and s.category in ("railing_infill", "railing_glass")], tag


def test_infill_never_lands_on_the_frame_category(catlin_model) -> None:
    """The frame's ``"railing"`` category is what the 2D plan filter, the trades gate and
    the BOM's frame row all key on. Infill landing there would put 147 near-coincident
    squares on every floor plan and silently move the frame row's count."""
    frame = [s for s in catlin_model.solids if s.category == "railing"]
    assert frame
    assert all("POST" in s.tag or "RAIL" in s.tag or "BRACKET" in s.tag for s in frame)
    # Not pinned to a count any more. A raking rail is banded finely enough to draw as one
    # continuous bar and a round one is faceted on top of that, so the frame's solid count
    # is a function of stair slope and rail diameter rather than a number worth freezing.
    # What the category has to keep meaning is unchanged: frame, never infill — and the
    # infill is still drawn, in its own categories, rather than having quietly gone missing.
    assert [s for s in catlin_model.solids
            if s.category in ("railing_infill", "railing_glass")]


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
    # The house wall is screened; the GARAGE wall deliberately is not, and that is the point
    # of deriving this rather than authoring it. GARAGE_WALL_2X6 dropped its rainscreen furring
    # on 2026-08-20 (nail strip face-fastens straight to the Zip-R), so there is no cavity left
    # to close — and the rule noticed without anyone editing a screen.
    assert "W-M-S1" in expected
    assert "W-G-S" not in expected


def test_a_screen_sits_in_the_cavity_it_closes_at_the_cladding_start(catlin_model) -> None:
    """Depth is the rainscreen cavity's own thickness and elevation is the wall base — both
    read off the wall, so re-sizing the stand-off moves the strip with it.

    Three ways a wall can spell that cavity, and this house has used two of them:

    * a band PACKED WITH INSULATION vents only the unfilled remainder in front of the fill —
      the Swinburne outrigger wall (2026-08-23), 1" of a 3-1/2" band, where drawing the whole
      band would have ordered a 3-1/2" insect closure for a 1" job;
    * a SOLID band with its gap authored BEHIND it as its own AIRGAP layer — the catlin truss
      (2026-08-26). Its outer girt is 1-1/2" of solid KDAT with a 1/2" vent behind it, and
      between the 24" courses that gap opens into the 1-1/2" the girts stand off. So the
      cavity is **2.0"**, and reading the band alone would report 1-1/2" of wood as air and
      miss the air entirely.

    Both are one function (``rainscreen_band``), and the strip the model draws spans exactly
    what it reports — the two polygons unioned — or the order and the drawing disagree.
    """
    from typehaus.resolve.accessories import (
        BUG_SCREEN_HEIGHT_IN,
        rainscreen_cavity_m,
    )
    from typehaus.resolve.geometry import polygon_area

    wall = next(w for w in catlin_model.walls if w.tag == "W-M-S1")
    screen = next(s for s in catlin_model.solids
                  if s.tag == "W-M-S1-BUGSCREEN")
    assert screen.z0_m == pytest.approx(wall.z0_m)
    assert screen.z1_m - screen.z0_m == pytest.approx(inch(BUG_SCREEN_HEIGHT_IN).meters)
    furring = [ly for ly in wall.depth_layers() if ly.function == "furring"][-1]
    airgap = next(ly for ly in wall.depth_layers() if ly.function == "airgap")
    vent_m = furring.thickness_m + airgap.thickness_m
    assert vent_m == pytest.approx(inch(2.0).meters)
    assert rainscreen_cavity_m(wall.layers) == pytest.approx(vent_m)
    # The strip spans both bands, in their own footprint: same run, the cavity's depth.
    # Compared by area rather than by vertex list, because the bands are mitred at their
    # corners and the union inherits that shape.
    band_area = abs(polygon_area(list(furring.polygon)))
    assert abs(polygon_area(list(screen.outline))) == pytest.approx(
        band_area * vent_m / furring.thickness_m, rel=0.02)


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
