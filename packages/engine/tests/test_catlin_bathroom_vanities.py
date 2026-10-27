"""The five other bathrooms' vanities.

Every bathroom in this house except RM-M-BATH2 had a bare bowl and no cabinet: five
``FX-LAV-24`` and one ``FX-LAV-COMPACT``, footprints with no carcass and nowhere to put
anything. They are stock-width vanities now, and each one is held in place by something
that is invisible from the plan source:

  * the wall's own FINISH FACE, which is not ``Room.clear_face`` -- two of these were
    authored off ``clear_face`` and stood *inside* the studs, at 0 FAIL;
  * a WATER CLOSET's Minnesota envelope, which is UPC 402.5's 24"/15" and not the IRC's 21";
  * a DOOR'S SWING ARC and its fully open position: the hall bath's 36" base and east
    hinge restore circulation that a collision-only check could not defend;
  * a RADIANT FLOOR that must not run under a closed-toe cabinet.

Each of those is a silent failure mode from a different file, which is why they are pinned
here together rather than beside whichever thing they constrain.
"""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon, box

IN = 0.0254

# tag -> (type_ref, storey, backing wall, which face of it the cabinet stands on)
VANITIES = {
    # The basement bath rotated north-south on 2026-09-05, so its 36" vanity turned with it:
    # it runs ACROSS the room's south end now, backing W-B-CW2's north face, where it used to
    # stand along the east wall against W-B-CN2's 12" pour.
    "FX-B-BATH-LAV": ("FX-ANGSJON-36-SS", "basement", "W-B-CW2", "+y"),
    "FX-M-BATH1-LAV": ("FX-DURAVIT-DCODE-070545", "main", "W-M-HS1", "+y"),
    "FX-S-BATH1-LAV": ("FX-ANGSJON-36", "second", "W-S-BA-E1B", "-x"),
    "FX-S-SUITEBATH-LAV": ("FX-CHULTON-30", "second", "W-S-SN3", "-y"),
    "FX-S-VANITY-LAV1": ("FX-VANITY-30-SEKTION", "second", "W-S-BD-N", "-y"),
    "FX-S-VANITY-LAV2": ("FX-VANITY-30-SEKTION", "second", "W-S-BD-N", "-y"),
}


def _obj(model, tag):
    return next(o for o in model.canvas_objects if o.tag == tag)


def _bbox(obj):
    """Plan bounds of a resolved object, in inches."""
    xs = [p[0] / IN for p in obj.footprint]
    ys = [p[1] / IN for p in obj.footprint]
    return min(xs), max(xs), min(ys), max(ys)


def _wall_face(model, wall_tag, side):
    """The wall's real finish face, off its own layer polygons -- NEVER clear_face.

    ``Room.clear_face`` is inset from the wall AXIS by the room's lining thickness, so on a
    thick wall it reads inches away from the plane a cabinet actually lands on. Reading the
    layer polygons is the only way to get the built face.
    """
    wall = next(w for w in model.walls if w.tag == wall_tag)
    pts = [p for layer in wall.layers for p in layer.polygon]
    assert pts, f"{wall_tag} resolved no layer polygons"
    xs = [p[0] / IN for p in pts]
    ys = [p[1] / IN for p in pts]
    return {"-x": min(xs), "+x": max(xs), "-y": min(ys), "+y": max(ys)}[side]


def test_bathroom_lavatories_use_the_selected_vanities_or_wall_basin(catlin_model_ro):
    """The bare bowls are gone; nothing in this house is an FX-LAV-24 any more."""
    model = catlin_model_ro
    for tag, (type_ref, storey, _, _) in VANITIES.items():
        obj = _obj(model, tag)
        assert obj.type_ref == type_ref, f"{tag} is {obj.type_ref}"
        assert obj.storey == storey

    remaining = [o.tag for o in model.canvas_objects
                 if getattr(o, "type_ref", "") == "FX-LAV-24"]
    assert remaining == [], f"a bare 24in bowl survived: {remaining}"


def test_the_attic_guest_bath_takes_the_one_vanity_its_wall_measures(catlin_model_ro):
    """RM-A-STUBATH got a cabinet on 2026-09-09, and 24" x 18" is not a preference.

    This test used to pin the opposite decision -- the room kept its bare 18" x 14" bowl,
    because the water closet's UPC 402.5 envelope crosses the north wall a vanity would want.
    The envelope did not move; what moved is the shower, which went neo-angle and gave the
    wall back its east end. Three numbers box the cabinet in, each from a different file, and
    every one of them is a silent failure: widen it and it eats ED-A-STUBATH-GFCI's only legal
    plate (E3901.6 wants a receptacle within 36" of the basin), deepen it and it stands in the
    water closet's envelope, slide it east and it runs through the shower pan.
    """
    model = catlin_model_ro
    obj = _obj(model, "FX-A-STUBATH-LAV")
    assert obj.type_ref == "FX-VANITY-24-SEKTION-SS"
    x0, x1, y0, y1 = _bbox(obj)
    # North face of W-A-HALL-S, and 18" of depth is all there is before the WC envelope's
    # y = 20'-7" (247").
    assert y1 == pytest.approx(265.625, abs=0.01)
    assert y0 >= 247.0, f"the carcass reaches y={y0:.3f}, inside the water closet's envelope"
    # ED-A-STUBATH-GFCI centres a 4" plate at x=150", so its east edge is x=152".
    assert x0 >= 152.0, f"the carcass starts at x={x0:.3f}, over the GFCI plate"
    # FX-A-STUBATH-SH's west panel. The counter scribes to it and must not pass it.
    assert x1 <= 176.63, f"the carcass ends at x={x1:.3f}, inside the shower pan"


def test_the_attic_showers_cut_corner_still_holds_p2708_1(catlin_model_ro):
    """The neo-angle is only legal while its corner cut stays shallow.

    IRC P2708.1 wants 900 sq in of interior area and a 30" minimum finished dimension. The
    pan is drawn to a 16"-per-leg cut, which on the FINISHED interior (34" legs inside a 36"
    base) inscribes 30 1/2" -- half an inch of margin. A deeper cut spends it, and nothing in
    the engine grades a shower compartment, so this arithmetic lives here or nowhere.
    """
    model = catlin_model_ro
    shower = _obj(model, "FX-A-STUBATH-SH")
    assert shower.type_ref == "FX-SHOWER-36-NEO-COMBO"
    outline = Polygon([(p[0] / IN, p[1] / IN) for p in shower.footprint])
    assert len(outline.exterior.coords) == 6, "the pan resolved as a rectangle, not a pentagon"
    # Shrink the pan's own outline to the finished interior, then measure the largest circle
    # that fits: `buffer(-r)` empties exactly when r passes the inscribed radius.
    interior = outline.buffer(-1.0)
    assert interior.area >= 900.0, f"interior is {interior.area:.0f} sq in, under P2708.1's 900"
    assert not interior.buffer(-15.0).is_empty, "a 30in circle no longer fits the compartment"


def test_each_vanity_backs_its_walls_finish_face_not_the_rooms_clear_face(catlin_model_ro):
    """The regression that matters most: two of these used to stand inside the studs.

    ``FX-M-BATH1-LAV`` sat at y=268.94" against a finish face at y=271.39" -- 2.45" into the
    wall -- and ``FX-S-BATH1-LAV`` 1.88" into W-S-BA-E1B. Both built and checked clean for
    months, because nothing in the engine grades a Fixture against a wall face.
    """
    model = catlin_model_ro
    for tag, (_, _, wall_tag, side) in VANITIES.items():
        x0, x1, y0, y1 = _bbox(_obj(model, tag))
        face = _wall_face(model, wall_tag, side)
        back = {"-x": x1, "+x": x0, "-y": y1, "+y": y0}[side]
        assert abs(back - face) < 0.05, (
            f"{tag} backs {back:.2f}in but {wall_tag}'s face is {face:.2f}in "
            f"({'inside the wall' if abs(back) > abs(face) else 'floating'})")


def test_no_vanity_stands_in_a_water_closets_minnesota_envelope(catlin_model_ro):
    """UPC 402.5, which is what Minnesota actually enforces: 24" in front, 15" each side.

    NOT the IRC's 21". Minn. R. 1309.0010 subp. 3.D deletes IRC chapters 25-33 outright and
    1309.0307 sends fixtures to Minn. R. ch. 4714 / the 2018 UPC. This walks the envelope by
    hand rather than trusting the resolved zone, so it still holds if the code profile is
    ever unset.
    """
    model = catlin_model_ro
    closets = {o.tag: o for o in model.canvas_objects
               if o.kind == "Fixture" and "-WC" in o.tag}
    for tag, (_, _, _, _) in VANITIES.items():
        van = _obj(model, tag)
        vx0, vx1, vy0, vy1 = _bbox(van)
        cab = box(vx0, vy0, vx1, vy1)
        for wc in closets.values():
            if wc.room != van.room:
                continue
            wx0, wx1, wy0, wy1 = _bbox(wc)
            # The bowl's own depth axis is its longer side; the envelope is 30" wide
            # (15" each side of the centreline) and reaches 24" off the front face.
            if (wx1 - wx0) >= (wy1 - wy0):          # bowl runs along x, faces +/-x
                cy = (wy0 + wy1) / 2
                env = [box(wx1, cy - 15, wx1 + 24, cy + 15),
                       box(wx0 - 24, cy - 15, wx0, cy + 15)]
            else:                                    # bowl runs along y
                cx = (wx0 + wx1) / 2
                env = [box(cx - 15, wy1, cx + 15, wy1 + 24),
                       box(cx - 15, wy0 - 24, cx + 15, wy0)]
            # The bowl faces away from its wall, so only one of the two envelopes is real;
            # requiring the cabinet to clear BOTH is the conservative reading and is what
            # every one of these placements was designed to.
            for zone in env:
                overlap = cab.intersection(zone).area
                assert overlap < 0.01, (
                    f"{tag} takes {overlap:.1f} sq in out of {wc.tag}'s 24in/15in envelope")


def test_the_hall_bath_vanity_clears_the_east_hinged_door_and_tub_return(catlin_model_ro):
    """The shorter base gives the entry back its turn and keeps the door beside the wall."""
    model = catlin_model_ro
    x0, x1, y0, y1 = _bbox(_obj(model, "FX-S-BATH1-LAV"))
    assert (x1 - x0, y1 - y0) == pytest.approx((21.75, 37))
    door = next(o for o in model.openings if o.tag == "D-S-BATH1")
    assert not door.flip_hinge and not door.flip_swing
    top = Polygon(_obj(model, "FX-S-BATH1-LAV").footprint)
    swing = Polygon(door.swing_clearance)
    assert not top.intersects(swing)
    assert top.distance(swing) / IN >= 6.4
    assert not any(c.tag == "CT-S-BATH1-VANITY" for c in model.countertops)
    assert not any(b.host == "FX-S-BATH1-LAV" for b in model.shelf_banks)


def test_the_basement_vanity_is_shallow_and_clears_the_pocket_door(catlin_model_ro):
    """The 18" cabinet fits the narrow room and the bathroom door has no sweep."""
    model = catlin_model_ro
    x0, x1, y0, y1 = _bbox(_obj(model, "FX-B-BATH-LAV"))
    assert round(y1 - y0, 2) == 21.75
    assert round(x1 - x0, 2) == 37.0

    door = next(o for o in model.openings if o.tag == "D-B-BATH")
    assert door.type_ref == "DT-POCKET-INT-36"
    assert not door.swing_clearance
    assert door.pocket_sign == 1


def test_the_alcove_is_two_bowls_at_exactly_the_code_minimum_spacing(catlin_model_ro):
    """60" is the smallest legal true double, and this alcove is 61.49" wide.

    UPC 402.5 -- the section MN enforces, not IRC P2705.1, which Minn. R. 1309.0010
    subp. 3.D deletes -- wants 30" between adjacent fixtures and 15" from a lavatory
    centreline to a side wall. 15 + 30 + 15 = 60, so there is no slack at all: if either
    cabinet ever moves, one of the two numbers below breaks.
    """
    model = catlin_model_ro
    ax0, ax1, _, _ = _bbox(_obj(model, "FX-S-VANITY-LAV1"))
    bx0, bx1, _, _ = _bbox(_obj(model, "FX-S-VANITY-LAV2"))
    assert round(ax1 - ax0, 2) == 30.0 and round(bx1 - bx0, 2) == 30.0
    assert abs(ax1 - bx0) < 0.05, "the two 30in bases no longer make one 60in run"

    centre_a, centre_b = (ax0 + ax1) / 2, (bx0 + bx1) / 2
    assert round(centre_b - centre_a, 2) == 30.0, "bowls are inside 30in centre-to-centre"

    west = _wall_face(model, "W-S-W2", "+x")
    east = _wall_face(model, "W-S-VE", "-x")
    assert centre_a - west >= 15.0, f"west bowl is {centre_a - west:.2f}in off its wall"
    assert east - centre_b >= 15.0, f"east bowl is {east - centre_b:.2f}in off its wall"


def test_every_vanity_carries_its_own_shelf(catlin_model_ro):
    """The storage is the point, and doors-plus-a-shelf is why these are not drawer banks.

    A drawer base runs about 1.5x a door base of the same width. Each of these cabinets is a
    plain two-door box with the one full-depth adjustable shelf it ships with, priced in the
    vanity row rather than milled from the owner's oak.
    """
    model = catlin_model_ro
    plan = model.plan
    # Every FX-VANITY-* instance in the house, not only the VANITIES table: RM-M-BATH2's and
    # RM-A-STUBATH's are vanities too, and the second one had no shelf until 2026-09-28.
    vanities = [el for el in plan.all_elements() if type(el).__name__ == "Fixture"
                and (el.type_ref or "").startswith("FX-VANITY-")]
    assert {"FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2", "FX-A-STUBATH-LAV",
            "FX-M-BATH2-SINK"} == {v.tag for v in vanities}
    for fixture in vanities:
        banks = [b for b in model.shelf_banks if b.host == fixture.tag]
        assert len(banks) == 1, f"{fixture.tag} has {len(banks)} shelf banks, wants one"
        bank = banks[0]
        assert bank.material_ref == "cabinet-plywood"
        assert bank.procurement == "included_in_host"
        # depth is AUTHORED on every one: the derivation is keyed on FurnitureTypes and
        # every host here is a FixtureType, so it is checked here against the carcass —
        # the carcass less a 3/4" back and a 1 3/4" scribe/trap set-off.
        # Except RM-M-BATH2's floating SEKTION (2026-10-22): IKEA's shelf in a 14 3/4" frame.
        depth = 14 * IN
        for shelf in bank.shelves:
            assert shelf.depth_m == pytest.approx(depth), bank.tag
            assert shelf.count == 2, "one shelf plus the case top"


def test_the_hall_bath_mat_gave_way_to_the_cabinet_and_is_a_real_cable(
        catlin_plan, catlin_model_ro):
    """Heating cable under a closed-toe vanity has nowhere to dump its heat.

    Schluter forbids it outright, and `advisory.floor_heat_fixture_keepout` FAILed the moment
    the 48" cabinet landed on the old zone. The mat keeps the manufacturer's 2" standoff, and
    the wattage that came out of the resize is a PART NUMBER -- DHEHK12027, 26.7 sq ft /
    338 W -- not the `area x 12` the old 510 W was. Cable is sold in uncuttable lengths.
    """
    model = catlin_model_ro
    zone = next(z for z in model.floor_heat if z.tag == "FH-S-BATH1")
    poly = Polygon(zone.zone)
    x0, x1, y0, y1 = _bbox(_obj(model, "FX-S-BATH1-LAV"))
    cab = box(x0 * IN, y0 * IN, x1 * IN, y1 * IN)

    assert not poly.intersects(cab), "the mat runs under the vanity"
    assert poly.distance(cab) / IN >= 1.99, (
        f"only {poly.distance(cab) / IN:.2f}in of standoff; Schluter wants 2in")

    # `watts` is authored data and does not survive onto the resolved zone (which keeps
    # only geometry, spacing and a derived wire length), so read it off the plan element.
    plan = catlin_plan
    authored = next(e for e in plan.storey_elements("second")
                    if getattr(e, "tag", "") == "FH-S-BATH1")
    area = poly.area / IN / IN / 144
    assert authored.watts == 338, "wattage is a purchased nameplate, not area x 12"
    assert 26.7 <= area <= 28.0, f"{area:.2f} sq ft no longer suits a 26.7 sq ft cable"


def test_powder_room_has_real_toilet_front_clearance_and_an_open_entry(catlin_model_ro):
    model = catlin_model_ro
    room = Polygon(next(r.clear_face for r in model.rooms if r.tag == "RM-M-BATH1"))
    toilet = _obj(model, "FX-M-BATH1-WC")
    basin = _obj(model, "FX-M-BATH1-LAV")
    tx0, tx1, ty0, ty1 = _bbox(toilet)
    bx0, bx1, by0, by1 = _bbox(basin)
    # TOTO SS-02352 p.2: overall projection, not the shorter underside dimension.
    assert (tx1 - tx0, ty1 - ty0) == pytest.approx((14.9375, 21.25))
    assert toilet.type_ref == "FX-TOTO-AP-WH"
    assert room.bounds[3] / IN - ty1 >= 24.25
    assert room.covers(Polygon(toilet.required_clearances[0]))
    assert room.bounds[3] / IN - by1 >= 32.25
    assert room.bounds[2] / IN - (bx0 + bx1) / 2 >= 15
    assert (bx0 + bx1 - tx0 - tx1) / 2 >= 30
    door = next(o for o in model.openings if o.tag == "D-M-BATH1")
    assert door.type_ref == "DT-INT-SWING32"
    assert door.width_m / IN == pytest.approx(32)
    door_south = min(y for _, y in door.swing_clearance) / IN
    door_north = max(y for _, y in door.swing_clearance) / IN
    assert door_north - max(door_south, by1) >= 30.7
    assert not Polygon(door.swing_clearance).intersects(Polygon(basin.footprint))
    assert (bx1 - bx0, by1 - by0) == pytest.approx((17.75, 13.375))
    assert basin.attachment_wall == "W-M-HS1"
    stops = [a for a in model.pipe_accessories
             if a.tag in {"PA-M-BATH1-STOP-CW", "PA-M-BATH1-STOP-HW"}]
    assert len(stops) == 2
    # A valve inferred from the shared riser's first vertex lands below this floor.
    assert all(0 < stop.z_m < basin.body_z0_m for stop in stops)
    finished_floor_m = basin.z_m - 0.7186
    assert all((stop.z_m - finished_floor_m) / IN == pytest.approx(24) for stop in stops)
    drain = next(run for run in model.pipe_runs if run.tag == "PR-B-LAV1-DRAIN")
    vent = next(run for run in model.pipe_runs if run.tag == "PR-M-BATH1-LAV-VENT")
    assert (drain.z_start_m - finished_floor_m) / IN == pytest.approx(20)
    assert vent.z_start_m == pytest.approx(drain.z_start_m)
    waste = next(r for r in model.pipe_runs if r.tag == "PR-B-LAV1-DRAIN")
    vent = next(r for r in model.pipe_runs if r.tag == "PR-M-BATH1-LAV-VENT")
    assert waste.path[0] == pytest.approx(vent.path[0])
    assert waste.z_m[0] == pytest.approx(vent.z_m[0], abs=IN / 16)
    assert not any(bank.host == basin.tag for bank in model.shelf_banks)
    assert Polygon(basin.footprint).disjoint(Polygon(toilet.required_clearances[0]))


def test_powder_basin_fixings_land_in_solid_north_face_blocking(catlin_model_ro):
    """Both fixing plates must bear on timber that clears the opposing staggered stud."""
    model = catlin_model_ro
    basin = _obj(model, "FX-M-BATH1-LAV")
    x0, x1, _, _ = _bbox(basin)
    fixing_centers = [(x0 + x1) / 2 - 120 / 25.4, (x0 + x1) / 2 + 120 / 25.4]
    fixing_height = basin.body_z0_m + 0.145 - 0.055
    wall = next(w for w in model.walls if w.tag == "W-M-HS1")
    block = next(member for member in wall.members
                 if member.child_key.startswith("backing-") and member.profile == "2x10")
    for fixing_x in fixing_centers:
        # Two-inch-square rear plates need a full inch of wood on all four sides.
        assert min(block.p0[0], block.p1[0]) + IN < fixing_x * IN
        assert max(block.p0[0], block.p1[0]) - IN > fixing_x * IN
        assert block.z0_m + IN < fixing_height < block.z1_m - IN
    north_studs = [m for m in wall.members if m.category == "stud"
                   and m.p0[1] > 268 * IN]
    for end in (block.p0[0], block.p1[0]):
        assert any(abs(abs(end - stud.p0[0]) - 0.75 * IN) < 0.01 * IN
                   for stud in north_studs)
    assert block.p0[1] / IN - 0.75 == pytest.approx(269.25)
    opposing_stud = next(m for m in wall.members if m.category == "stud"
                         and m.p0[0] / IN == pytest.approx(56))
    assert opposing_stud.p0[1] / IN + 1.75 < block.p0[1] / IN - 0.75
    assert wall.assembly == "INT_2X6_STAGGERED_PLUMBING_HALF"
    # The service panel and bowl must stay centered on the same carrier.
    panel = _obj(model, "FURN-M-BATH1-AP")
    toilet = _obj(model, "FX-M-BATH1-WC")
    px0, px1, _, _ = _bbox(panel)
    tx0, tx1, _, _ = _bbox(toilet)
    assert (px0 + px1) / 2 == pytest.approx((tx0 + tx1) / 2)


def test_every_selected_lavatory_has_parts_ports_and_a_connected_exact_setout(catlin_plan, catlin_check_report):
    from typehaus.model import Service

    tags = {*VANITIES, "FX-M-BATH2-SINK", "FX-A-STUBATH-LAV", "FX-A-STUDIO-BAR-SINK"}
    types = {entry.tag: entry for entry in catlin_plan.library.fixture_types}
    for tag in tags:
        fixture_type = types[catlin_plan.by_tag(tag).type_ref]
        assert {port.service for port in fixture_type.ports} == {
            Service.DRAIN, Service.WATER_HOT, Service.WATER_COLD}
        assert {part.role for part in fixture_type.parts} >= {"faucet", "trap"}
        assert fixture_type.product_ref
    findings = [f for f in catlin_check_report().findings
                if f.check_id == "mep.fixture_port_connection" and f.element_tags[0] in tags]
    assert len(findings) == 27
    assert all(f.result.value == ("unknown" if f.element_tags[0] in {
        "FX-S-SUITEBATH-LAV", "FX-A-STUDIO-BAR-SINK"} else "pass") for f in findings)


def test_fabricated_double_top_keeps_both_bowl_cutouts(catlin_model_ro):
    top = next(top for top in catlin_model_ro.countertops if top.tag == "CT-S-VANITY")
    assert top.length_m / IN == pytest.approx(61)
    assert len(top.cutouts) == 2
