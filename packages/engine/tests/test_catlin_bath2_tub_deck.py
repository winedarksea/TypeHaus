"""RM-M-BATH2's drop-in bath and the framed deck it sits in.

The Kohler K-1130-W1 (K-5713-W1 until 2026-10-22) replaced an FX-TUB-60 alcove
allowance, and a drop-in is not a substitution — it is a different piece of construction. What is pinned here is the handful
of dimensions and material choices that the rest of the room was then drawn to, each of
which is silently breakable by an edit somewhere else:

  * the rim laps the west knee wall and meets W-M-BA2E at 1/8";
  * the deck's south face IS the shower's north face, which is the whole reason the two
    read as one built element and the reason the room's depth adds up;
  * the knee-wall cavity is MINERAL WOOL, which a house-wide reinsulation sweep would
    otherwise take;
  * the Bask heated surface has its dedicated GFCI circuit and an outlet inside the box,
    at the heater end, with a 20" x 15" service leaf beside it;
  * the deck's finished west face is the shower's front-glass plane.
"""

from __future__ import annotations

from functools import cache

from pathlib import Path

import pytest

from shapely.geometry import Polygon

from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"

M_PER_IN = 0.0254


@cache
def _plan():
    """The loaded catlin plan — built once for this module.

    Memoised: this was called 12 times and rebuilt the whole house each time. Everything
    here reads and nothing mutates, which is what makes one shared instance safe (the same
    rule ``catlin_model_ro`` states in conftest).
    """
    return load_plan(CATLIN_DIR).plan


def _canvas(model, tag):
    return next(o for o in model.canvas_objects if o.tag == tag)


def _bounds(outline):
    xs = [p[0] / M_PER_IN for p in outline]
    ys = [p[1] / M_PER_IN for p in outline]
    return min(xs), max(xs), min(ys), max(ys)


def test_the_bath_is_the_kohler_drop_in_and_needs_power():
    """A drop-in with a heated shell, not the alcove allowance it replaced. `POWER_120` in
    `needs` is the load-bearing assertion: it is what makes a *bathtub* carry an electrical
    requirement into the fixture schedule at all."""
    plan = _plan()
    types = {t.tag: t for t in plan.library.fixture_types}
    tub = next(e for e in plan.storey_elements("main") if getattr(e, "tag", "") == "FX-M-BATH2-TUB")
    assert tub.type_ref == "FX-KOHLER-UNDERSCORE-6032"

    kohler = types["FX-KOHLER-UNDERSCORE-6032"]
    assert kohler.product_ref == "PROD-KOHLER-1130-W1-0"
    assert kohler.plan_symbol == "kohler-underscore-6032"
    assert "power_120" in {s.value for s in kohler.needs}
    width, depth = (v.meters / M_PER_IN for v in kohler.footprint)
    assert round(width, 4) == 60.0
    assert round(depth, 4) == 32.0

    products = {p.tag for p in plan.library.products}
    assert {"PROD-KOHLER-1130-W1-0", "PROD-KOHLER-7272"} <= products
    assert "PROD-KOHLER-5713-W1-0" not in products


def test_the_rim_laps_the_west_knee_wall_and_meets_the_east_wall_at_an_eighth():
    """The rim laps W-M-TUBDK-W's top by no more than its lap past the published cutout,
    the wall still clears the modelled shell, and the east rim stands 1/8"-1/4" off
    W-M-BA2E's face."""
    from typehaus.model.placeable_symbols._kohler_underscore_rect import shell_section

    plan = _plan()
    model, _ = resolve(plan)
    tub = _bounds(_canvas(model, "FX-M-BATH2-TUB").footprint)
    cutout = _bounds([p.xy_m for p in next(
        e for e in plan.storey_elements("main") if getattr(e, "tag", "") == "FO-M-TUBDK").outline])

    def face(tag, layer, axis):
        wall = next(w for w in model.walls if w.tag == tag)
        return max(p[axis] for p in next(x for x in wall.layers if x.name == layer).polygon) / M_PER_IN

    bay_west, bay_south = face("W-M-TUBDK-W", "ply-bay", 0), face("W-M-TUBDK-S", "ply-bay", 1)
    lap = bay_west - tub[0]
    assert 0 < lap <= cutout[0] - tub[0] + 1e-6, "rim does not lap the west knee wall"

    kohler = next(t for t in plan.library.fixture_types if t.tag == "FX-KOHLER-UNDERSCORE-6032")
    width, depth = (v.meters for v in kohler.footprint)
    # Rotated 90 degrees, so the shell's plan x half-extent is its local y half-extent.
    shell_x = max(shell_section(f / 10, width, depth)[3] for f in range(11)) / M_PER_IN
    assert (tub[0] + tub[1]) / 2 - shell_x > bay_west, "knee wall cuts the shell"

    ba2e = next(w for w in model.walls if w.tag == "W-M-BA2E")
    ba2e_face = min(min(p[0] for p in layer.polygon) for layer in ba2e.layers) / M_PER_IN
    assert 0.125 - 1e-6 <= ba2e_face - tub[1] <= 0.25

    # The foot bay holds the end drain, K-7272 and the filler's 4794 rough.
    assert 4.5 <= tub[2] - bay_south <= 5.5
    # Kohler's published 59 1/2" x 31 1/2" cutout, centred on the rim.
    assert cutout[1] - cutout[0] == pytest.approx(31.5)
    assert cutout[3] - cutout[2] == pytest.approx(59.5)
    assert (cutout[0] + cutout[1]) / 2 == pytest.approx((tub[0] + tub[1]) / 2)


def test_the_deck_and_the_shower_share_one_knee_wall():
    """W-M-TUBDK-S's south face and FX-M-BATH2-SH's north face are the same line. That is
    the integration; if these ever diverge the room has a slot of dead floor in it again."""
    model, _ = resolve(_plan())
    shower = _bounds(_canvas(model, "FX-M-BATH2-SH").footprint)
    south = next(w for w in model.walls if w.tag == "W-M-TUBDK-S")
    outer = min(p[1] for p in next(x for x in south.layers if x.name == "ply-room").polygon)
    assert abs(outer / M_PER_IN - shower[3]) < 1e-6
    # The Corian apron's finished face is the shower's west (front-glass) plane.
    apron = next(p for p in model.panelings
                 if p.tag == "WP-M-BATH2-TUBDK-APRON" and p.wall_tag == "W-M-TUBDK-W")
    west = min(x for x, _ in apron.outline) / M_PER_IN
    assert west == pytest.approx(shower[0], abs=0.02)


def test_the_water_closet_backs_a_wall_with_its_code_clearance_clear():
    """Its 15"-a-side envelope (UPC 402.5, the section MN enforces) is bounded by W-M-W3 on one hand and the tub deck
    on the other, with about 11" to spare — so this is the assertion that catches the deck
    growing westward."""
    model, _ = resolve(_plan())
    wc = _bounds(_canvas(model, "FX-M-BATH2-WC").footprint)
    room = next(r for r in model.rooms if r.tag == "RM-M-BATH2")

    plan = _plan()
    fixture = next(e for e in plan.storey_elements("main")
                   if getattr(e, "tag", "") == "FX-M-BATH2-WC")
    assert fixture.wall_ref == "W-M-HS1"

    # Tank ON the wall. Measured against W-M-HS1's own room-side finish, NOT against
    # `room.clear_face` — that polygon is inset from the wall AXIS by the lining alone
    # (5/8"), so on a 6 3/4" staggered wall it sits 2 3/4" inside the face you can touch.
    hs1 = next(w for w in model.walls if w.tag == "W-M-HS1")
    face = min(p[1] for p in next(x for x in hs1.layers if x.name == "paint-b").polygon)
    assert abs(face / M_PER_IN - wc[3]) < 0.05

    west = next(w for w in model.walls if w.tag == "W-M-TUBDK-W")
    deck_face = min(p[0] for p in next(x for x in west.layers if x.name == "ply-room").polygon)
    centre = (wc[0] + wc[1]) / 2
    assert centre + 15.0 <= deck_face / M_PER_IN
    assert centre - 15.0 >= min(p[0] for p in room.clear_face) / M_PER_IN


def test_the_deck_cavity_is_mineral_wool_and_must_stay_that_way():
    """** THIS IS THE ONE THAT GUARDS THE MOISTURE DECISION. ** The cavity sits under the rim
    of a 72-gallon bath inside a sealed box reachable only through a 14x14 panel. A
    house-wide `mineral-wool` -> `fiberglass` sweep must not take it, and nothing else in
    the repo would notice if it did."""
    plan = _plan()
    box = plan.library.resolve_assembly("TUBDECK_INT_2X3")
    stud = next(layer for layer in box.layers if layer.name == "stud")
    assert stud.cavity is not None
    assert stud.cavity.material_ref == "mineral-wool", (
        "RM-M-BATH2's tub deck must keep mineral wool — see the note on the assembly"
    )
    # Exterior-grade ply both faces, and symmetric: the box closes no loop, so its
    # outward_sign is the +1 fallback and an asymmetric stack would build inside-out.
    skins = [layer for layer in box.layers if layer.name.startswith("ply")]
    assert len(skins) == 2
    assert {layer.material_ref for layer in skins} == {"struct-1-plywood"}
    assert skins[0].thickness.meters == skins[1].thickness.meters
    # The `INT` token is what keeps mn_energy off both of these. It has to be a whole
    # `_`-delimited token — `_is_interior_assembly` splits, it does not substring-match —
    # so this reproduces that split rather than asserting on the literal.
    for tag in ("TUBDECK_INT_2X3", "TUBDECK_INT_PLY_CAP"):
        assert "INT" in tag.split("_"), f"{tag} would be graded against MN Zone 6"


def test_the_deck_cap_is_plywood_over_blocking_and_the_bath_hole_is_cut_out_of_it():
    """The cap bills the plywood by the square foot only because the sheet is a SHEATHING
    layer over a STRUCTURE one; and the hole has to come out of that area or the estimate
    orders a deck with no bath in it. The Corian top (2026-10-22) is a FINISH layer over
    the ply, so the finished deck is the rim's 22 3/4" and the ply stays at 22 1/4"."""
    plan = _plan()
    cap = plan.library.resolve_assembly("TUBDECK_INT_PLY_CAP")
    functions = {layer.name: layer.function.value for layer in cap.layers}
    assert functions == {"deck-block": "structure", "deck-ply": "sheathing",
                         "deck-top": "finish"}
    top = next(layer for layer in cap.layers if layer.name == "deck-top")
    assert top.material_ref == "solid-surface-fabricated"

    slab = next(e for e in plan.storey_elements("main") if getattr(e, "tag", "") == "SL-M-TUBDK")
    assert slab.openings == ("FO-M-TUBDK",)
    assert round(slab.top_elevation.meters / M_PER_IN, 4) == 22.75
    ply_top = slab.top_elevation.meters - top.thickness.meters
    assert round(ply_top / M_PER_IN, 4) == 22.25

    outer = Polygon([p.xy_m for p in slab.outline]).area / (M_PER_IN ** 2)
    hole = next(e for e in plan.storey_elements("main") if getattr(e, "tag", "") == "FO-M-TUBDK")
    cut = Polygon([p.xy_m for p in hole.outline]).area / (M_PER_IN ** 2)
    # ~17.3 sf of deck with Kohler's 59 1/2" x 31 1/2" (13.0 sf) cut away for the bath.
    assert 17.0 < outer / 144 < 17.7
    assert cut / 144 == pytest.approx(59.5 * 31.5 / 144)


def test_the_knee_walls_frame_and_stand_on_the_subfloor():
    """Real studs and plates, not a decorative mass — and their base is the subfloor at 3/4",
    not the storey datum, which is also where the bath's mortar bed lands."""
    model, _ = resolve(_plan())
    for tag in ("W-M-TUBDK-W", "W-M-TUBDK-S"):
        wall = next(w for w in model.walls if w.tag == tag)
        assert round(wall.z0_m / M_PER_IN, 4) == 0.75
        assert round(wall.z1_m / M_PER_IN, 4) == 20.0
        categories = {m.category for m in wall.members}
        assert {"stud", "plate"} <= categories, f"{tag} framed nothing"
        # Studs and plates are 2x3 (2026-10-21). The one member that is not is BK-M-TUBDK-AP
        # (plan/backing.py), the 2x8 flat framing the tub access panel in the west skirt.
        assert all(m.profile == "2x3" for m in wall.members if m.category != "blocking")
        blocks = [m for m in wall.members if m.category == "blocking"]
        assert {m.profile for m in blocks} <= {"2x8"}, f"{tag} grew unexpected blocking"


def test_the_deck_does_not_carve_up_the_room():
    """The knee walls stop at the room's finished faces and so never reach the wall AXES the
    room resolver polygonizes. Reach them and RM-M-BATH2 loses ~20 sf of floor area to a
    face nothing claims."""
    model, _ = resolve(_plan())
    room = next(r for r in model.rooms if r.tag == "RM-M-BATH2")
    # 87.97" x 106.24" between finish faces = 64.9 sf. The knee walls close no loop, so
    # they stand IN the room and are not subtracted; subtracting them split off the 17 sf
    # tub box. The band catches that collapse, not the wall.
    assert 64.4 < room.area_m2 * 10.7639 < 65.4


def test_the_bask_heated_surface_has_its_dedicated_gfci_circuit_and_outlet():
    """Kohler's REQUIRED service: a dedicated 120 V 15 A Class A GFCI circuit with the
    outlet behind the bath. GFCI at the breaker rather than the device is not a stylistic
    choice here — the outlet is sealed inside the deck box."""
    plan = _plan()
    circuit = next(c for c in plan.library.circuits if c.tag == "CKT-BATH2-TUB")
    assert circuit.breaker_amps == 15 and circuit.poles == 1
    assert circuit.gfci is True
    assert circuit.load_va == 65, "load is the 65 W the heater draws, not the breaker rating"

    outlet = next(e for e in plan.storey_elements("main")
                  if getattr(e, "tag", "") == "ED-M-BATH2-TUB-RC")
    assert outlet.circuit == "CKT-BATH2-TUB"
    assert outlet.kind.value == "receptacle", "a GFCI device inside a sealed box cannot be reset"

    model, _ = resolve(plan)
    tub = _bounds(_canvas(model, "FX-M-BATH2-TUB").footprint)
    x, y = (v / M_PER_IN for v in _canvas(model, outlet.tag).position)
    # "Behind the bath", at the HEAD: the K-1130-W1's heater pad and power supply are on the
    # lumbar (north) end, and Kohler wants the outlet within 24" of the supply.
    assert tub[0] <= x <= tub[1]
    assert y > tub[3], "the outlet is not behind the bath's head"
    assert y - tub[3] < 4.0, "the outlet has left the head of the box"
    # The heater-end service leaf: Kohler's 20"L x 15"H minimum, overlapping the head.
    panel = _canvas(model, "FURN-M-BATH2-TUBDK-AP-N")
    px0, px1, py0, py1 = _bounds(panel.footprint)
    assert py1 - py0 >= 20 - 1e-6
    assert (panel.body_z1_m - panel.body_z0_m) / M_PER_IN >= 15 - 1e-6
    assert py1 > (tub[2] + tub[3]) / 2 + 20 and y - py1 < 24


def test_the_drain_matches_the_bath_kohler_actually_specifies():
    """1 1/2", the K-7272 Clearflo's tee — not the 2" the FX-TUB-60 allowance was drawn at."""
    plan = _plan()
    run = next(e for e in plan.storey_elements("basement")
               if getattr(e, "tag", "") == "PR-B-TUB2-DRAIN")
    assert round(run.diameter.meters / M_PER_IN, 4) == 1.5
    assert run.serves == ("FX-M-BATH2-TUB",)


def test_the_filler_sits_on_the_foot_ledge_at_deck_height():
    """FX-M-BATH2-FILLER stands on the finished foot deck (22 3/4"), its hole line over the
    foot bay and its spout over the rim, inside the room."""
    model, _ = resolve(_plan())
    filler = _canvas(model, "FX-M-BATH2-FILLER")
    tub = _bounds(_canvas(model, "FX-M-BATH2-TUB").footprint)
    x0, x1, y0, y1 = _bounds(filler.footprint)
    assert round(filler.z_m / M_PER_IN, 3) == 22.75
    assert tub[0] < x0 and x1 < tub[1]
    assert y0 < tub[2] < y1, "the filler is not on the foot ledge reaching over the rim"
    south = next(w for w in model.walls if w.tag == "W-M-TUBDK-S")
    assert y0 > max(p[1] for p in next(x for x in south.layers if x.name == "ply-bay").polygon) / M_PER_IN
    room = next(r for r in model.rooms if r.tag == "RM-M-BATH2")
    assert Polygon(room.clear_face).contains(Polygon(filler.footprint))


pytestmark = pytest.mark.slow


def test_align_filler_is_centred_and_its_mounts_and_outlet_clear_the_rim(catlin_plan, catlin_model_ro):
    from shapely.geometry import Point

    from typehaus.model.placeable_symbols import model_parts, place_local
    from typehaus.model.placeable_symbols._roman_tub_filler import (
        HANDLE_CENTRES_IN,
        LEVER_REACH_IN,
        NECK_RADIUS_IN,
        SPOUT_BASE_DIAMETER_IN,
    )

    model = catlin_model_ro
    filler = _canvas(model, "FX-M-BATH2-FILLER")
    tub = _canvas(model, "FX-M-BATH2-TUB")
    trim = next(t for t in catlin_plan.library.fixture_types if t.tag == filler.type_ref)
    width, depth = (v.meters for v in trim.footprint)
    parts = model_parts(trim.plan_symbol, width, depth, trim.height.meters)
    hole_y = depth / 2 - SPOUT_BASE_DIAMETER_IN / 2 * M_PER_IN
    hole_line = place_local([(0, hole_y)], filler.position, filler.rotation_degrees)[0]
    outlet = place_local([parts[3]["center"][:2]], filler.position, filler.rotation_degrees)[0]
    assert filler.uid == "XSAHT3AEKA" and filler.host_fixture_ref == tub.tag
    assert filler.position[0] == pytest.approx(tub.position[0])
    assert hole_line[1] / M_PER_IN == pytest.approx(200.41)
    assert filler.z_m / M_PER_IN == pytest.approx(22.75)
    assert outlet[1] / M_PER_IN == pytest.approx(207.66)
    # Published top basin length (K-1130-W1, 55 1/8"), not merely the outside rim.
    basin_south = tub.position[1] - 55.125 / 2 * M_PER_IN
    assert 2.0 < (outlet[1] - basin_south) / M_PER_IN < 3.0
    cap = Polygon([p.xy_m for p in catlin_plan.by_tag("SL-M-TUBDK").outline])
    # Both escutcheons and 1 1/4-inch rough holes remain on the foot deck, ahead of shell.
    receptacle = _canvas(model, "ED-M-BATH2-TUB-RC")
    south_wall = next(w for w in model.walls if w.tag == "W-M-TUBDK-S")
    bay_south = max(y for layer in south_wall.layers if layer.name == "ply-bay"
                    for _, y in layer.polygon)
    for x in (-HANDLE_CENTRES_IN / 2, 0, HANDLE_CENTRES_IN / 2):
        xy = place_local([(x * M_PER_IN, hole_y)], filler.position, filler.rotation_degrees)[0]
        assert cap.covers(Point(xy).buffer(SPOUT_BASE_DIAMETER_IN / 2 * M_PER_IN))
        rough_hole = Point(xy).buffer(0.625 * M_PER_IN)
        assert rough_hole.bounds[1] > bay_south
        assert rough_hole.bounds[3] < Polygon(tub.footprint).bounds[1]
        assert rough_hole.distance(Polygon(receptacle.footprint)) > 6 * M_PER_IN
        if x:
            # A full disk is conservative for the actual quarter-turn lever sweep.
            sweep = Point(xy).buffer(LEVER_REACH_IN * M_PER_IN)
            neck = Point(hole_line).buffer(NECK_RADIUS_IN * M_PER_IN)
            assert sweep.disjoint(neck)
    products = {p.tag: p for p in catlin_plan.library.products}
    assert trim.product_ref == "PROD-MOEN-T393"
    assert products["PROD-MOEN-4794"].model == "4794"
    assert products["PROD-KOHLER-7272"].model == "K-7272-CP"
    assert "PROD-DELTA-15840LF" in next(
        t.source for t in catlin_plan.library.fixture_types if t.tag == "FX-VANITY-48-SEKTION")


def test_align_filler_exports_its_detailed_geometry(catlin_ifc_path):
    import ifcopenshell

    model = ifcopenshell.open(str(catlin_ifc_path))
    filler = next(o for o in model.by_type("IfcSanitaryTerminal") if o.Name == "FX-M-BATH2-FILLER")
    representation = filler.Representation.Representations[0]
    assert representation.RepresentationType == "Tessellation"
    assert len(representation.Items) == 10
