"""RM-M-BATH2's vanity, its radiant floor, and the joists under the drop-in bath.

Three changes landed together and each is silently breakable from somewhere else:

  * the sink is a 54" ONE-BASIN VANITY, not the double-bowl kitchen sink that stood in for
    it, and it fits the west wall only because the water closet's code clearance leaves
    exactly 59";
  * the radiant mat is the room's ONLY heat source and is sized to a real purchasable
    cable, so `watts` is a nameplate rather than `area x 12`;
  * the bath's floor is answered with blocking and a sister ply, and the four blocks have
    to TILE the bays rather than overlap.
"""

from __future__ import annotations

from itertools import pairwise
from pathlib import Path

from shapely.geometry import Polygon, box

from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"
M_PER_IN = 0.0254


def _plan():
    return load_plan(CATLIN_DIR).plan


def _model():
    return resolve(_plan())[0]


def _element(plan, storey, tag):
    return next(e for e in plan.storey_elements(storey) if getattr(e, "tag", "") == tag)


def _canvas(model, tag):
    return next(o for o in model.canvas_objects if o.tag == tag)


def _finish_face(model, wall_tag, axis, side):
    """The wall's painted face, in inches — NOT `Room.clear_face`.

    `clear_face` is inset from the wall AXIS by the room's lining, so on RM-M-BATH2's
    13 7/8" west wall it reads SIX INCHES off the plane a cabinet actually lands on. Every
    dimension in this file is struck off the layer polygons for that reason."""
    wall = next(w for w in model.walls if w.tag == wall_tag)
    i = 0 if axis == "x" else 1
    values = [p[i] / M_PER_IN for layer in wall.layers for p in layer.polygon]
    return max(values) if side == "max" else min(values)


# The basin: a 20" x 15 1/2" undermount over the 30" sink base at the vanity's north end.
def _basin(model):
    vanity = Polygon(_canvas(model, "FX-M-BATH2-SINK").footprint)
    vx0, vy0, vx1, vy1 = (v / M_PER_IN for v in vanity.bounds)
    cx, cy = (vx0 + vx1) / 2, vy1 - 15.0
    return box((cx - 7.75) * M_PER_IN, (cy - 10) * M_PER_IN,
               (cx + 7.75) * M_PER_IN, (cy + 10) * M_PER_IN)


# --- the vanity ------------------------------------------------------------------------

def test_the_vanity_is_one_basin_and_no_longer_a_kitchen_sink():
    """The whole point of the change. `FX-KITCHEN-SINK-33` is the library's DOUBLE-bowl
    kitchen sink; it drew two bowls on a bathroom plan and billed as a kitchen sink."""
    plan = _plan()
    sink = _element(plan, "main", "FX-M-BATH2-SINK")
    assert sink.type_ref == "FX-VANITY-54-SINGLE"

    vanity = {t.tag: t for t in plan.library.fixture_types}["FX-VANITY-54-SINGLE"]
    assert vanity.plan_symbol == "vanity"
    width, depth = (v.meters / M_PER_IN for v in vanity.footprint)
    assert (round(width, 4), round(depth, 4)) == (54.0, 21.0)
    # The kitchen sink type survives, because the KITCHEN still uses it.
    assert _element(plan, "main", "FX-M-KITCH-SINK").type_ref == "FX-KITCHEN-SINK-33"


def test_the_vanity_stands_on_the_floor_rather_than_hanging_on_the_wall():
    """The old instance carried `Mount(WALL, 27")` to drag a kitchen deck down to lavatory
    height. A vanity is a floor-standing cabinet; that mount would float a 54" carcass 27"
    up the wall with its toe kick in mid-air."""
    sink = _element(_plan(), "main", "FX-M-BATH2-SINK")
    assert sink.mount.kind.value == "floor"
    assert sink.mount.elevation is None


def test_the_counter_lands_at_thirty_six_inches():
    """`FixtureType.height` is OVERALL including the spout — the symbol builder subtracts a
    fixed 0.14 m faucet band — so 41.5" is what puts the deck at the chosen comfort height.
    Change the height and the counter moves; this is the arithmetic that says by how much."""
    from typehaus.model.placeable_symbols.plumbing import _deck_height

    vanity = {t.tag: t for t in _plan().library.fixture_types}["FX-VANITY-54-SINGLE"]
    deck_m, _faucet = _deck_height(vanity.height.meters)
    # 41.5" less the builder's fixed 0.14 m (5.512") faucet band is 35.99", i.e. 36" to
    # within a hundredth. There is no height that lands on 36.000" in round inches.
    assert round(deck_m / M_PER_IN, 1) == 36.0


def test_the_vanity_fits_the_west_wall_without_entering_the_toilets_clearance():
    """The 54" is set by this: the run from the south wall to the start of
    FX-M-BATH2-WC's 21" IRC P2705.1 front clearance is 59", and a cabinet may not stand in
    a code envelope. If the water closet ever moves west or south, this is what breaks."""
    model = _model()
    south_face = _finish_face(model, "W-M-BDN1", "y", "max")

    vanity = Polygon(_canvas(model, "FX-M-BATH2-SINK").footprint)
    vx0, vy0, vx1, vy1 = (v / M_PER_IN for v in vanity.bounds)
    assert round(vy1 - vy0, 2) == 54.0        # the 54" runs north/south, so rotation applied
    assert round(vx1 - vx0, 2) == 21.0
    assert abs(vy0 - south_face) < 0.05       # hard into the room's south-west corner

    # The bowl faces south (rotation 0), so P2705.1's 21" reaches south off its front edge.
    wc = Polygon(_canvas(model, "FX-M-BATH2-WC").footprint)
    envelope_starts = min(p[1] for p in wc.exterior.coords) / M_PER_IN - 21.0
    assert vy1 < envelope_starts, "the cabinet stands in the water closet's code envelope"
    # ...and the slack is real but small: the run is 57 1/4", so 54" leaves 3 1/4".
    assert 2.5 < envelope_starts - vy1 < 4.5


def test_the_vanity_backs_onto_the_wall_face_not_the_rooms_clear_face():
    """** THE REGRESSION THIS FILE EXISTS FOR MOST. ** A first cut of this cabinet was
    placed off `Room.clear_face`, which is inset from the wall AXIS rather than from the
    finished face — so a 54" vanity stood SIX INCHES inside W-M-W3's studs, and the whole
    house still checked 0 FAIL, because nothing grades a fixture against a wall face. The
    same mistake put the floor-heat polygon in the wall beside it."""
    model = _model()
    face = _finish_face(model, "W-M-W3", "x", "max")
    room = next(r for r in model.rooms if r.tag == "RM-M-BATH2")
    reported = min(p[0] for p in room.clear_face) / M_PER_IN
    assert face - reported > 5.0, "if these ever agree, this test has stopped testing"

    back = min(p[0] for p in _canvas(model, "FX-M-BATH2-SINK").footprint) / M_PER_IN
    assert abs(back - face) < 0.05, "the cabinet is not on the finished wall face"


def test_the_vanity_has_a_receptacle_within_reach_of_the_basin():
    """NEC 210.52(D) / IRC E3901.6: a receptacle within 36" of the outside edge of each
    basin. ** THE ENGINE ENCODES NO E3901 RULE AT ALL **, so this is the only thing
    asserting it for this room. ED-M-BATH2-TUB-RC does NOT count and the test says so
    explicitly: it measures ~32" from the basin, but it is sealed inside the tub deck box
    behind an access panel and serves the bath's heater."""
    from shapely.geometry import Point

    model = _model()
    basin = _basin(model)
    outlet = _canvas(model, "ED-M-BATH2-RC1")
    assert basin.distance(Point(outlet.position)) / M_PER_IN < 36.0
    # Above the 36" counter, not at the old baseboard height behind a cabinet.
    assert outlet.z_m / M_PER_IN > 36.0
    # And it is a bathroom receptacle, so E3902.1 makes GFCI mandatory either way.
    assert outlet.type_ref == "ED-T-RECEPTACLE-GFCI"


def test_the_vanity_clears_the_window_over_it():
    """WIN-M-BATH2's 3'-0" sill is the SAME plane as this 36" counter, so the two would
    collide if the cabinet ran north. It stops ~11 7/8" short of the opening."""
    model = _model()
    window = next(o for o in model.openings if o.tag == "WIN-M-BATH2")
    wall = next(w for w in model.walls if w.tag == "W-M-W3")
    # `center_along_m` runs from axis[0] along the wall's own direction, and this wall is
    # authored NORTH TO SOUTH — reading it off min(y) would put the window 28" from the
    # wrong end of the room.
    (_, y_start), (_, y_end) = wall.axis
    sign = 1.0 if y_end >= y_start else -1.0
    centre = y_start + sign * window.center_along_m
    lo = centre - window.width_m / 2

    vanity_north = max(p[1] for p in _canvas(model, "FX-M-BATH2-SINK").footprint)
    assert lo > vanity_north
    assert 12.0 < (lo - vanity_north) / M_PER_IN < 16.0


def test_the_bathroom_door_swings_out_and_clears_the_vanity():
    """** THE CONSTRAINT THAT NEARLY COST THE VANITY ITS SIZE. ** D-M-BATH2's 30" opening
    runs x 2'-0"..4'-6" and the cabinet's east face lands at x=1'-11 5/8" — 3 5/8" inside
    it. Hinged east and swinging IN, the leaf clipped the cabinet by 25 in2. The door was
    turned around rather than the cabinet shrunk, so BOTH of these must stay true: the arc
    is on the BEDROOM side of W-M-BDN1, and the bedroom side is empty.

    Note this surfaced as `integrity.door_swing_conflict`, an UNKNOWN rather than a FAIL —
    `haus check --only fail` stayed clean through it. It was found by reading the takeoff's
    findings, not by the gate."""
    model = _model()
    door = next(o for o in model.openings if o.tag == "D-M-BATH2")
    swing = Polygon([(p[0], p[1]) for p in door.swing_clearance])
    wall_y = 156.0 * M_PER_IN                      # W-M-BDN1's axis; the bath is y > this
    assert swing.bounds[3] <= wall_y + 1e-6, "the door swings back into the bathroom"

    for tag in ("FX-M-BATH2-SINK", "FX-M-BATH2-WC", "FX-M-BATH2-SH", "FX-M-BATH2-TUB"):
        assert not swing.intersects(Polygon(_canvas(model, tag).footprint)), tag
    # And nothing stands in the bedroom where the leaf now lands.
    blockers = [o.tag for o in model.canvas_objects
                if o.storey == "main" and len(o.footprint) >= 3
                and o.tag != "D-M-BATH2" and Polygon(o.footprint).intersects(swing)]
    assert blockers == []


def test_the_sink_base_carries_a_billable_shelf():
    """The owner asked for drawer AND shelf space. Drawers have no vocabulary in the engine
    and live in the type's `source`; the shelf is a board and bills as owner-milled oak."""
    model = _model()
    bank = next(b for b in model.shelf_banks if b.tag == "SB-M-BATH2-VAN")
    assert bank.host == "FX-M-BATH2-SINK"
    # A Fixture hosting casework is legal — `resolve/millwork.py` builds its placeable map
    # from `canvas_objects`, which carries Fixtures — but the depth cannot be DERIVED from a
    # FixtureType, so it must be authored or the bank resolves with no depth at all.
    assert round(bank.depth_m / M_PER_IN, 2) == 18.5


# --- the radiant floor -----------------------------------------------------------------

def test_the_bathroom_has_no_heat_source_but_the_mat():
    """This is why the zone was GROWN rather than trimmed to match its old wattage. The
    only air terminal in the room is an ERV EXHAUST, which takes heat out."""
    plan = _plan()
    terminals = [e for e in plan.storey_elements("main")
                 if e.element_kind in {"Register", "Equipment"}
                 and getattr(e, "room", None) == "RM-M-BATH2"]
    assert [t.tag for t in terminals] == ["REG-M-EXH2"]
    assert terminals[0].kind.value == "exhaust"


def test_the_mat_is_a_real_cable_and_covers_the_zone_without_exceeding_it():
    """Heating cable is sold in fixed lengths and CANNOT be cut, so the rule is to buy the
    largest unit that does not exceed the heated area and park the surplus in a buffer
    zone. `watts` is that unit's nameplate, never `area x 12` — no supplier sells the
    number the formula produces."""
    zone = _element(_plan(), "main", "FH-M-BATH2")
    area_ft2 = Polygon([p.xy_m for p in zone.zone]).area / 0.3048 ** 2
    assert 16.0 <= area_ft2 <= 21.3, "below 16 ft2 drop to DHEHK12011; above 21.3 go up"
    assert zone.watts == 203           # Schluter DHEHK12016, 16.0 ft2, 120 V, 1.7 A

    circuit = next(c for c in _plan().library.circuits if c.tag == "CKT-FH-BATH2")
    assert circuit.load_va == 203      # NEC 220.51 counts fixed heating at 100% of load
    assert circuit.gfci                # NEC 424.44(G), mandatory for a bathroom floor cable


def test_the_mat_is_sized_to_the_room_with_no_headroom_left():
    """16.0 ft2 of cable delivers ~298 BTU/h at Schluter's 18.6 BTU/h/ft2 of floor surface
    (82 F floor, 72 F operative), against ~303 BTU/h of design load through one R-40.7 wall
    and one U-0.25 window at -15 F. ** That is 98%, and the honest reading is "sized to the
    room", not "has margin". ** The room has no more legal floor to heat — the keepouts are
    manufacturer minimums — so if this ratio ever drops materially the answer is a SECOND
    heat source, not a bigger mat. The band below is what would catch that."""
    from typehaus.analysis import assembly_r_value

    model = _model()
    plan = _plan()
    lib = plan.library
    wall_r = assembly_r_value(next(a for a in lib.assemblies
                                   if a.tag == "CATLIN_EXT_2X6"), lib).value.r_us
    window_u = next(t for t in lib.window_types if t.tag == "WT-2736-T").u_factor.u_us
    delta_f = 70 - (-15)

    depth_in = (_finish_face(model, "W-M-HS1", "y", "min")
                - _finish_face(model, "W-M-BDN1", "y", "max"))
    glass_ft2 = 27 * 36 / 144
    opaque_ft2 = (depth_in / 12) * 9.4 - glass_ft2
    load = opaque_ft2 / wall_r * delta_f + glass_ft2 * window_u * delta_f
    assert 250 < load < 360
    assert 0.90 < (16.0 * 18.6) / load < 1.15


def test_the_zone_holds_every_manufacturer_keepout():
    """Schluter's handbook, not invented numbers: 2" off walls and fixed cabinets, 7" off
    the water closet's drain centreline, and NEVER under a bathtub platform or a closed-toe
    vanity — trapped air overheats the cable."""
    from shapely.geometry import Point

    model = _model()
    zone = Polygon([p.xy_m for p in _element(_plan(), "main", "FH-M-BATH2").zone])
    for tag in ("FX-M-BATH2-SINK", "FX-M-BATH2-WC", "FX-M-BATH2-SH", "FX-M-BATH2-TUB"):
        footprint = Polygon(_canvas(model, tag).footprint)
        assert not zone.intersects(footprint), tag
        assert zone.distance(footprint) / M_PER_IN >= 1.99, tag
    # The deck box, which is walls and a slab rather than a fixture and so is invisible to
    # `advisory.floor_heat_fixture_keepout` — the cable may not run under it either.
    deck = box(52.0 * M_PER_IN, 194.375 * M_PER_IN, 95.37 * M_PER_IN, 267.37 * M_PER_IN)
    assert zone.distance(deck) / M_PER_IN >= 1.99
    wc_drain = Point(30 * M_PER_IN, 250.615 * M_PER_IN).buffer(7 * M_PER_IN)
    assert not zone.intersects(wc_drain)


def test_the_keepout_check_reads_the_rotated_footprint():
    """The engine fix this zone depends on.
    `advisory.floor_heat_fixture_keepout` used to rebuild each fixture's box from its TYPE's
    (width, depth) about its centre and never applied rotation, so a bath authored at
    rotation 90 was graded as a 59"-wide EAST/WEST box. A zone drawn to the phantom PASSED
    while running under the actual tub, which is the dangerous half of that defect."""
    model = _model()
    tub = _canvas(model, "FX-M-BATH2-TUB")
    assert tub.rotation_degrees == 90.0
    x0, y0, x1, y1 = Polygon(tub.footprint).bounds
    assert round((x1 - x0) / M_PER_IN, 2) == 35.75      # 35 3/4" ACROSS, not 59 11/16"
    assert round((y1 - y0) / M_PER_IN, 2) == 59.69


# --- the joists under the bath ---------------------------------------------------------

def test_the_filled_bath_is_answered_with_blocking_and_one_sister():
    """plans/TODO.md's 60 psf item. Four full-depth blocks and one sister ply."""
    model = _model()
    floor = next(f for f in model.floors if f.tag == "FS-M-WEST")
    blocks = [m for m in floor.members if m.category == "blocking"]
    sisters = [m for m in floor.members if m.category == "sister_joist"]
    assert len(blocks) == 4
    assert len(sisters) == 1
    assert round(sisters[0].length_m / 0.3048, 2) == 18.0, "a sister must run the whole span"


def test_the_blocks_tile_the_bays_and_do_not_overlap_the_sister():
    """`_reinforcement_members` blocks to the joist line on BOTH sides of each entry, so two
    entries 16" apart would double-block the bay between them and a free-standing sister
    would land in a bay something else already blocks. `structural.member_interference`
    FAILs on either. Two entries 32" apart, sister riding one of them, is what avoids it."""
    model = _model()
    floor = next(f for f in model.floors if f.tag == "FS-M-WEST")
    spans = sorted((min(m.p0[1], m.p1[1]) / M_PER_IN, max(m.p0[1], m.p1[1]) / M_PER_IN)
                   for m in floor.members if m.category == "blocking")
    for (_, prev_hi), (next_lo, _) in pairwise(spans):
        assert next_lo >= prev_hi, "blocking must tile the bays, never overlap"
    # And they span the bath, which is 59 11/16" of tub across four joist lines.
    assert spans[0][0] < 194.0 and spans[-1][1] > 254.0

    sister_y = next(m for m in floor.members if m.category == "sister_joist").p0[1] / M_PER_IN
    for lo, hi in spans:
        assert not (lo < sister_y < hi), "the sister ply sits in a blocked bay"


def test_the_sister_stays_clear_of_the_tub_drain():
    """It is on the 240" line rather than the 224" one for exactly this reason:
    PR-B-TUB2-DRAIN drops in the 224"..240" bay."""
    model = _model()
    floor = next(f for f in model.floors if f.tag == "FS-M-WEST")
    sister_y = next(m for m in floor.members if m.category == "sister_joist").p0[1] / M_PER_IN
    drain_y = _element(_plan(), "main", "FX-M-BATH2-TUB").drain_position.xy_m[1] / M_PER_IN
    assert abs(sister_y - drain_y) > 6.0
