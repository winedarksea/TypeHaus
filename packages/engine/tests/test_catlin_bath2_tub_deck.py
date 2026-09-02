"""RM-M-BATH2's drop-in bath and the framed deck it sits in.

The Kohler K-5713-W1 replaced an FX-TUB-60 alcove allowance, and a drop-in is not a
substitution — it is a different piece of construction. What is pinned here is the handful
of dimensions and material choices that the rest of the room was then drawn to, each of
which is silently breakable by an edit somewhere else:

  * the bath fits its bay with Kohler's clearance and no more;
  * the deck's south face IS the shower's north face, which is the whole reason the two
    read as one built element and the reason the room's depth adds up;
  * the knee-wall cavity is MINERAL WOOL, which a house-wide reinsulation sweep would
    otherwise take;
  * the Bask heated surface has its dedicated GFCI circuit and an outlet inside the box.
"""

from __future__ import annotations

from pathlib import Path

from shapely.geometry import Polygon

from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"

M_PER_IN = 0.0254


def _plan():
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
    assert tub.type_ref == "FX-KOHLER-UNDERSCORE-6036"

    kohler = types["FX-KOHLER-UNDERSCORE-6036"]
    assert kohler.product_ref == "PROD-KOHLER-5713-W1-0"
    assert "power_120" in {s.value for s in kohler.needs}
    # The spec drawing's dimensions, not the marketing name's 59 3/4".
    width, depth = (v.meters / M_PER_IN for v in kohler.footprint)
    assert round(width, 4) == 59.6875
    assert round(depth, 4) == 35.75

    products = {p.tag for p in plan.library.products}
    assert {"PROD-KOHLER-5713-W1-0", "PROD-KOHLER-7272"} <= products


def test_the_bath_fits_its_bay_within_kohlers_eighth_inch():
    """Kohler allows a maximum 1/8" gap between the rim and the framing, and the bay was
    drawn to that. Both numbers matter in both directions: a bay that grows leaves a gap
    the rim cannot span, and one that shrinks will not take the bath at all."""
    model, _ = resolve(_plan())
    tub = _bounds(_canvas(model, "FX-M-BATH2-TUB").footprint)

    west = next(w for w in model.walls if w.tag == "W-M-TUBDK-W")
    south = next(w for w in model.walls if w.tag == "W-M-TUBDK-S")
    bay_west = max(p[0] for p in next(x for x in west.layers if x.name == "ply-bay").polygon)
    bay_south = max(p[1] for p in next(x for x in south.layers if x.name == "ply-bay").polygon)
    bay_west /= M_PER_IN
    bay_south /= M_PER_IN

    # East and north are the room's own walls; the bay is closed by the two knee walls.
    west_gap = tub[0] - bay_west
    south_gap = tub[2] - bay_south
    assert west_gap > 0, "bath overruns the west knee wall"
    assert west_gap <= 0.25, "bath is not tight to the west knee wall"
    assert south_gap > 0, "bath overruns the south knee wall"
    # The foot deck: the surplus is deliberately at the foot, where the outlet lives.
    assert 3.5 <= south_gap <= 4.5


def test_the_deck_and_the_shower_share_one_knee_wall():
    """W-M-TUBDK-S's south face and FX-M-BATH2-SH's north face are the same line. That is
    the integration; if these ever diverge the room has a slot of dead floor in it again."""
    model, _ = resolve(_plan())
    shower = _bounds(_canvas(model, "FX-M-BATH2-SH").footprint)
    south = next(w for w in model.walls if w.tag == "W-M-TUBDK-S")
    outer = min(p[1] for p in next(x for x in south.layers if x.name == "ply-room").polygon)
    assert abs(outer / M_PER_IN - shower[3]) < 1e-6


def test_the_water_closet_backs_a_wall_with_its_code_clearance_clear():
    """Its 15"-a-side envelope (P2705.1) is bounded by W-M-W3 on one hand and the tub deck
    on the other, with about 7" to spare — so this is the assertion that catches the deck
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
    box = plan.library.resolve_assembly("CATLIN_TUBDECK_INT_2X4")
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
    for tag in ("CATLIN_TUBDECK_INT_2X4", "CATLIN_TUBDECK_INT_PLY_CAP"):
        assert "INT" in tag.split("_"), f"{tag} would be graded against MN Zone 6"


def test_the_deck_cap_is_plywood_over_blocking_and_the_bath_hole_is_cut_out_of_it():
    """The cap bills the plywood by the square foot only because the sheet is a SHEATHING
    layer over a STRUCTURE one; and the hole has to come out of that area or the estimate
    orders a deck with no bath in it."""
    plan = _plan()
    cap = plan.library.resolve_assembly("CATLIN_TUBDECK_INT_PLY_CAP")
    functions = {layer.name: layer.function.value for layer in cap.layers}
    assert functions == {"deck-block": "structure", "deck-ply": "sheathing"}

    slab = next(e for e in plan.storey_elements("main") if getattr(e, "tag", "") == "SL-M-TUBDK")
    assert slab.openings == ("FO-M-TUBDK",)
    assert round(slab.top_elevation.meters / M_PER_IN, 4) == 22.25

    outer = Polygon([p.xy_m for p in slab.outline]).area / (M_PER_IN ** 2)
    hole = next(e for e in plan.storey_elements("main") if getattr(e, "tag", "") == "FO-M-TUBDK")
    cut = Polygon([p.xy_m for p in hole.outline]).area / (M_PER_IN ** 2)
    # ~19.8 sf of deck with ~13.5 sf of it cut away for the bath.
    assert 19.0 < outer / 144 < 20.5
    assert 13.0 < cut / 144 < 14.0


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
        assert all(m.profile == "2x4" for m in wall.members)


def test_the_deck_does_not_carve_up_the_room():
    """The knee walls stop at the room's finished faces and so never reach the wall AXES the
    room resolver polygonizes. Reach them and RM-M-BATH2 loses ~20 sf of floor area to a
    face nothing claims."""
    model, _ = resolve(_plan())
    room = next(r for r in model.rooms if r.tag == "RM-M-BATH2")
    assert 72.0 < room.area_m2 * 10.7639 < 73.5


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
    x, y = (v / M_PER_IN for v in outlet.position.xy_m)
    # "Behind the bath": inside the box, in the foot bay SOUTH of the shell — the only part
    # of the enclosure with room for a plug, since the bath sits 3/16" off the west face.
    assert tub[0] - 1.0 <= x <= tub[1]
    assert y < tub[2], "the outlet is not behind the bath"
    assert tub[2] - y < 4.0, "the outlet has fallen out of the foot bay"


def test_the_drain_matches_the_bath_kohler_actually_specifies():
    """1 1/2", the K-7272 Clearflo's tee — not the 2" the FX-TUB-60 allowance was drawn at."""
    plan = _plan()
    run = next(e for e in plan.storey_elements("basement")
               if getattr(e, "tag", "") == "PR-B-TUB2-DRAIN")
    assert round(run.diameter.meters / M_PER_IN, 4) == 1.5
    assert run.serves == ("FX-M-BATH2-TUB",)
