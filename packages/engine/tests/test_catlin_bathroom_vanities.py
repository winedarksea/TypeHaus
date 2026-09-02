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

from shapely.geometry import Polygon, box

from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"
IN = 0.0254

# tag -> (type_ref, storey, backing wall, which face of it the cabinet stands on)
VANITIES = {
    "FX-B-BATH-LAV": ("FX-VANITY-36-SHALLOW", "basement", "W-B-CN2", "-x"),
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


def test_the_attic_guest_bath_was_deliberately_left_alone():
    """RM-A-STUBATH keeps its compact bowl, and that is a decision, not an omission.

    Its water closet sits on the west wall, and that puts the toilet's 24" front envelope
    across the north wall a vanity would have used. There is no 30"+ run left in the room
    that a cabinet's own front clearance does not then push into the shower. If the attic
    bath is re-laid out, this is the test to delete.
    """
    model = _model()
    assert _obj(model, "FX-A-STUBATH-LAV").type_ref == "FX-LAV-COMPACT"


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

    swing = next(Polygon(o.swing_clearance) for o in model.openings
                 if o.tag == "D-S-BATH1" and o.swing_clearance)
    cab = box(x0 * IN, y0 * IN, x1 * IN, y1 * IN)
    assert not cab.intersects(swing), "the 48in vanity is inside D-S-BATH1's swing"

    sx0, _, sy0, _ = _bbox(_obj(model, "FURN-S-BATH1-SHELF"))
    assert sy0 - y1 >= 0, "the vanity runs past the shower return shelf"
    assert sy0 - y1 < 1.0, (
        f"{sy0 - y1:.2f}in to the shelf -- if this grew, a wider cabinet now fits")


def test_the_basement_vanity_is_shallow_because_of_its_door():
    """18" is not a preference here: at 21" the cabinet meets D-B-BATH's arc everywhere.

    This is the test that explains why RM-B-BATH gets the shallow type while RM-S-SUITEBATH,
    with less wall, keeps the standard 21" one.
    """
    model = _model()
    x0, x1, y0, y1 = _bbox(_obj(model, "FX-B-BATH-LAV"))
    assert round(x1 - x0, 2) == 18.0, "the basement vanity stopped being shallow"

    swing = next(Polygon(o.swing_clearance) for o in model.openings
                 if o.tag == "D-B-BATH" and o.swing_clearance)
    assert not box(x0 * IN, y0 * IN, x1 * IN, y1 * IN).intersects(swing)

    # ... and the counterfactual, which is the whole point: a 21" carcass on this wall is
    # caught by the arc at every position it could take along the run.
    deep = [y for y in range(219, 222 + 1)
            if not box((x1 - 21) * IN, y * IN, x1 * IN, (y + 36) * IN).intersects(swing)]
    assert deep == [], "a 21in cabinet now clears the door -- re-check the shallow choice"


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
