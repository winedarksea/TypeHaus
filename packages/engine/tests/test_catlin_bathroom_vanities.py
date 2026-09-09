"""The five other bathrooms' vanities.

Every bathroom in this house except RM-M-BATH2 had a bare bowl and no cabinet: five
``FX-LAV-24`` and one ``FX-LAV-COMPACT``, footprints with no carcass and nowhere to put
anything. They are stock-width vanities now, and each one is held in place by something
that is invisible from the plan source:

  * the wall's own FINISH FACE, which is not ``Room.clear_face`` -- two of these were
    authored off ``clear_face`` and stood *inside* the studs, at 0 FAIL;
  * a WATER CLOSET's Minnesota envelope, which is UPC 402.5's 24"/15" and not the IRC's 21";
  * a DOOR'S SWING ARC, which is a quarter-disc and not the bounding box -- the hall bath
    gets 48" instead of a special-order 42" only because the difference is real;
  * a RADIANT FLOOR that must not run under a closed-toe cabinet.

Each of those is a silent failure mode from a different file, which is why they are pinned
here together rather than beside whichever thing they constrain.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from shapely.geometry import Polygon, box

from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"
IN = 0.0254

# tag -> (type_ref, storey, backing wall, which face of it the cabinet stands on)
VANITIES = {
    # The basement bath rotated north-south on 2026-09-05, so its 36" vanity turned with it:
    # it runs ACROSS the room's south end now, backing W-B-CW2's north face, where it used to
    # stand along the east wall against W-B-CN2's 12" pour.
    "FX-B-BATH-LAV": ("FX-VANITY-36-SHALLOW", "basement", "W-B-CW2", "+y"),
    "FX-M-BATH1-LAV": ("FX-VANITY-24-SHALLOW", "main", "W-M-HS1", "+y"),
    "FX-S-BATH1-LAV": ("FX-VANITY-48-SINGLE", "second", "W-S-BA-E1B", "-x"),
    "FX-S-SUITEBATH-LAV": ("FX-VANITY-30-SINGLE", "second", "W-S-SN3", "-y"),
    "FX-S-VANITY-LAV1": ("FX-VANITY-30-SHALLOW", "second", "W-S-BD-N", "-y"),
    "FX-S-VANITY-LAV2": ("FX-VANITY-30-SHALLOW", "second", "W-S-BD-N", "-y"),
}


def _model():
    return resolve(load_plan(CATLIN_DIR).plan)[0]


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


def test_every_bathroom_lavatory_is_a_vanity_with_a_cabinet():
    """The bare bowls are gone; nothing in this house is an FX-LAV-24 any more."""
    model = _model()
    for tag, (type_ref, storey, _, _) in VANITIES.items():
        obj = _obj(model, tag)
        assert obj.type_ref == type_ref, f"{tag} is {obj.type_ref}"
        assert obj.storey == storey

    remaining = [o.tag for o in model.canvas_objects
                 if getattr(o, "type_ref", "") == "FX-LAV-24"]
    assert remaining == [], f"a bare 24in bowl survived: {remaining}"


def test_the_attic_guest_bath_takes_the_one_vanity_its_wall_measures():
    """RM-A-STUBATH got a cabinet on 2026-09-09, and 24" x 18" is not a preference.

    This test used to pin the opposite decision -- the room kept its bare 18" x 14" bowl,
    because the water closet's UPC 402.5 envelope crosses the north wall a vanity would want.
    The envelope did not move; what moved is the shower, which went neo-angle and gave the
    wall back its east end. Three numbers box the cabinet in, each from a different file, and
    every one of them is a silent failure: widen it and it eats ED-A-STUBATH-GFCI's only legal
    plate (E3901.6 wants a receptacle within 36" of the basin), deepen it and it stands in the
    water closet's envelope, slide it east and it runs through the shower pan.
    """
    model = _model()
    obj = _obj(model, "FX-A-STUBATH-LAV")
    assert obj.type_ref == "FX-VANITY-24-SHALLOW"
    x0, x1, y0, y1 = _bbox(obj)
    # North face of W-A-HALL-S, and 18" of depth is all there is before the WC envelope's
    # y = 20'-7" (247").
    assert y1 == pytest.approx(265.625, abs=0.01)
    assert y0 >= 247.0, f"the carcass reaches y={y0:.3f}, inside the water closet's envelope"
    # ED-A-STUBATH-GFCI centres a 4" plate at x=150", so its east edge is x=152".
    assert x0 >= 152.0, f"the carcass starts at x={x0:.3f}, over the GFCI plate"
    # FX-A-STUBATH-SH's west panel. The counter scribes to it and must not pass it.
    assert x1 <= 176.63, f"the carcass ends at x={x1:.3f}, inside the shower pan"


def test_the_attic_showers_cut_corner_still_holds_p2708_1():
    """The neo-angle is only legal while its corner cut stays shallow.

    IRC P2708.1 wants 900 sq in of interior area and a 30" minimum finished dimension. The
    pan is drawn to a 16"-per-leg cut, which on the FINISHED interior (34" legs inside a 36"
    base) inscribes 30 1/2" -- half an inch of margin. A deeper cut spends it, and nothing in
    the engine grades a shower compartment, so this arithmetic lives here or nowhere.
    """
    model = _model()
    shower = _obj(model, "FX-A-STUBATH-SH")
    assert shower.type_ref == "FX-SHOWER-36-NEO-COMBO"
    outline = Polygon([(p[0] / IN, p[1] / IN) for p in shower.footprint])
    assert len(outline.exterior.coords) == 6, "the pan resolved as a rectangle, not a pentagon"
    # Shrink the pan's own outline to the finished interior, then measure the largest circle
    # that fits: `buffer(-r)` empties exactly when r passes the inscribed radius.
    interior = outline.buffer(-1.0)
    assert interior.area >= 900.0, f"interior is {interior.area:.0f} sq in, under P2708.1's 900"
    assert not interior.buffer(-15.0).is_empty, "a 30in circle no longer fits the compartment"


def test_each_vanity_backs_its_walls_finish_face_not_the_rooms_clear_face():
    """The regression that matters most: two of these used to stand inside the studs.

    ``FX-M-BATH1-LAV`` sat at y=268.94" against a finish face at y=271.39" -- 2.45" into the
    wall -- and ``FX-S-BATH1-LAV`` 1.88" into W-S-BA-E1B. Both built and checked clean for
    months, because nothing in the engine grades a Fixture against a wall face.
    """
    model = _model()
    for tag, (_, _, wall_tag, side) in VANITIES.items():
        x0, x1, y0, y1 = _bbox(_obj(model, tag))
        face = _wall_face(model, wall_tag, side)
        back = {"-x": x1, "+x": x0, "-y": y1, "+y": y0}[side]
        assert abs(back - face) < 0.05, (
            f"{tag} backs {back:.2f}in but {wall_tag}'s face is {face:.2f}in "
            f"({'inside the wall' if abs(back) > abs(face) else 'floating'})")


def test_no_vanity_stands_in_a_water_closets_minnesota_envelope():
    """UPC 402.5, which is what Minnesota actually enforces: 24" in front, 15" each side.

    NOT the IRC's 21". Minn. R. 1309.0010 subp. 3.D deletes IRC chapters 25-33 outright and
    1309.0307 sends fixtures to Minn. R. ch. 4714 / the 2018 UPC. This walks the envelope by
    hand rather than trusting the resolved zone, so it still holds if the code profile is
    ever unset.
    """
    model = _model()
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


def test_the_hall_baths_forty_eight_fits_between_the_door_arc_and_the_shelf():
    """48" is a stock width and 42" is special-order, so this inch matters commercially.

    The swing's BOUNDING BOX reaches y=348", which would leave 46.5" and force the 42". The
    arc is a quarter-disc and the cabinet clears it at y=345.88", which leaves 48.62" -- so
    the house buys a volume-tier cabinet instead of a one-SKU one. The margin to
    FURN-S-BATH1-SHELF is 0.62" and there is nothing else to give.
    """
    model = _model()
    x0, x1, y0, y1 = _bbox(_obj(model, "FX-S-BATH1-LAV"))
    assert round(x1 - x0, 2) == 21.0 and round(y1 - y0, 2) == 48.0

    door = next(o for o in model.openings
                if o.tag == "D-S-BATH1" and o.swing_clearance)
    swing = Polygon(door.swing_clearance)
    cab = box(x0 * IN, y0 * IN, x1 * IN, y1 * IN)
    assert not cab.intersects(swing), "the 48in vanity is inside D-S-BATH1's swing"
    # ** AND IT CLEARS ONLY FROM THE WEST JAMB. ** W-S-BD-N1B runs +x, so the unflipped
    # jamb is the EAST one at x=114" and a leaf hung there sweeps 15.6 in2 of this carcass —
    # which is what the plan sheets drew until `_door_swing_clearance` was corrected on
    # 2026-09-09. `flip_hinge` on the door is the fix, and this is what defends it.
    # The first vertex of the sector IS the hinge.
    hinge_x = door.swing_clearance[0][0] / IN
    assert round(hinge_x, 2) == 84.0, (
        f"D-S-BATH1 hinged at x={hinge_x:.2f}in; off the WEST jamb the 48in cabinet is gone")

    sx0, _, sy0, _ = _bbox(_obj(model, "FURN-S-BATH1-SHELF"))
    assert sy0 - y1 >= 0, "the vanity runs past the shower return shelf"
    assert sy0 - y1 < 1.0, (
        f"{sy0 - y1:.2f}in to the shelf -- if this grew, a wider cabinet now fits")


def test_the_basement_vanity_is_shallow_and_the_reason_changed_with_the_room():
    """** THE DOOR-SWING ARGUMENT IS RETIRED, AND SAYING SO IS THE POINT. **

    Until 2026-09-05 this cabinet stood along RM-B-BATH's east wall with `D-B-BATH` in the
    north partition swinging past it, and 18" was forced: a 21" carcass was caught by the
    arc at every station along the run, which is why this room took the shallow type where
    RM-S-SUITEBATH — with less wall — keeps the standard 21" one.

    The basement's west-side replan rotated the room north-south. The vanity runs across the
    SOUTH end now and `D-B-BATH` is on the east wall swinging OUT into the new hall, so its
    arc never enters this room at all. 18" survives on the commercial argument alone (the
    big-box combos that arrive with their top and bowl on them are 18.6"-18.75" deep, so 18"
    is the pallet depth — see `fixture_types.py`), and on the room's own 3'-5 1/4" width:
    at 21" the front zone would leave 20 1/4" of floor.

    Both halves are asserted, so nobody re-derives the retired reason and nobody quietly
    upgrades the cabinet either.
    """
    model = _model()
    x0, x1, y0, y1 = _bbox(_obj(model, "FX-B-BATH-LAV"))
    assert round(y1 - y0, 2) == 18.0, "the basement vanity stopped being shallow"
    assert round(x1 - x0, 2) == 36.0

    # The swing is out of the room, so the arc it once governed is not in play any more.
    swing = next(Polygon(o.swing_clearance) for o in model.openings
                 if o.tag == "D-B-BATH" and o.swing_clearance)
    cab = box(x0 * IN, y0 * IN, x1 * IN, y1 * IN)
    assert not cab.intersects(swing)
    # Measured off the WALL's own finish face, never off `Room.clear_face`, which
    # polygonizes wall AXES and reaches 2.4"-3.4" past every face in the room: the swing
    # touches that ring by construction and would prove nothing.
    bath_face = max(p[0] for ly in model.wall("W-B-BA-E").layers if ly.name == "gwb-a"
                    for p in ly.polygon)
    assert min(p[0] for p in swing.exterior.coords) >= bath_face - 1e-6, (
        "D-B-BATH swings back into the room -- the 18in depth is load bearing again")


def test_the_alcove_is_two_bowls_at_exactly_the_code_minimum_spacing():
    """60" is the smallest legal true double, and this alcove is 61.49" wide.

    IRC P2705.1 / IPC 405.3.1 want 30" between adjacent fixtures and 15" from a lavatory
    centreline to a side wall. 15 + 30 + 15 = 60, so there is no slack at all: if either
    cabinet ever moves, one of the two numbers below breaks.
    """
    model = _model()
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


def test_every_vanity_carries_a_billable_shelf():
    """The storage is the point, and doors-plus-a-shelf is why these are not drawer banks.

    A drawer base runs about 1.5x a door base of the same width. Each of these cabinets is a
    plain two-door box with one full-depth adjustable shelf cut from the owner's own oak,
    which is what recovers the volume without paying the drawer premium.
    """
    model = _model()
    banks = {b.host: b for b in model.shelf_banks}
    for tag in VANITIES:
        assert tag in banks, f"{tag} has no shelf bank -- its cabinet bills as an empty box"
        bank = banks[tag]
        assert bank.material_ref == "oak-shelf-4q"
        # depth is AUTHORED on every one: the derivation is keyed on FurnitureTypes and
        # every host here is a FixtureType, so an underived depth is a hard finding.
        for shelf in bank.shelves:
            assert shelf.depth_m > 0, f"{bank.tag} derived a zero depth"
            assert shelf.count == 2, "one shelf plus the case top"


def test_the_hall_bath_mat_gave_way_to_the_cabinet_and_is_a_real_cable():
    """Heating cable under a closed-toe vanity has nowhere to dump its heat.

    Schluter forbids it outright, and `advisory.floor_heat_fixture_keepout` FAILed the moment
    the 48" cabinet landed on the old zone. The mat keeps the manufacturer's 2" standoff, and
    the wattage that came out of the resize is a PART NUMBER -- DHEHK12027, 26.7 sq ft /
    338 W -- not the `area x 12` the old 510 W was. Cable is sold in uncuttable lengths.
    """
    model = _model()
    zone = next(z for z in model.floor_heat if z.tag == "FH-S-BATH1")
    poly = Polygon(zone.zone)
    x0, x1, y0, y1 = _bbox(_obj(model, "FX-S-BATH1-LAV"))
    cab = box(x0 * IN, y0 * IN, x1 * IN, y1 * IN)

    assert not poly.intersects(cab), "the mat runs under the vanity"
    assert poly.distance(cab) / IN >= 1.99, (
        f"only {poly.distance(cab) / IN:.2f}in of standoff; Schluter wants 2in")

    # `watts` is authored data and does not survive onto the resolved zone (which keeps
    # only geometry, spacing and a derived wire length), so read it off the plan element.
    plan = load_plan(CATLIN_DIR).plan
    authored = next(e for e in plan.storey_elements("second")
                    if getattr(e, "tag", "") == "FH-S-BATH1")
    area = poly.area / IN / IN / 144
    assert authored.watts == 338, "wattage is a purchased nameplate, not area x 12"
    assert 26.7 <= area <= 28.0, f"{area:.2f} sq ft no longer suits a 26.7 sq ft cable"
