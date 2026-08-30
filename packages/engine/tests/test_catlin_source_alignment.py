"""The Catlin 2nd/3rd storeys against the Sensopia survey they reproduce.

`catlin_floorplan/Colin House - 2nd Floor.svg` and `... 3rd Floor.svg` are vector drawings
at 74.7029 px/m whose `path` #0 is the wall-fill polygon, so every partition face in them is
readable to ~1/16". The numbers below were measured off those polygons, converted to the
model frame (origin = SW sheathing corner, +x east, +y north) and rounded to the nearest
inch — the agreed fidelity policy being *interior partitions move to the source; the
exterior envelope, the x=18' bearing line and the 16" framing module do not*.

This file is the ratchet: without it the next edit can quietly drift a partition back off
the survey and nothing in `haus check` would notice, because none of these lines is
load-bearing and none of them is dimensioned on a sheet.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.quantities import ft
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR

TOL_M = 0.0254 / 2.0  # half an inch


@pytest.fixture(scope="module")
def catlin_plan():
    result = load_plan(CATLIN_DIR)
    assert result.plan is not None, result.findings
    return result.plan


def _node(plan, tag):
    node = plan.by_tag(tag)
    assert node is not None, f"missing node {tag}"
    return node.position.xy_m


# (node tag, axis, feet, inches, the measured source centreline in feet)
SECOND_LINES = (
    # South band north wall — three equal 9'-0" bedroom bays start here.
    ("N-S-C1", "y", 9, 0, 9.035),
    ("N-S-W3", "y", 9, 0, 9.035),
    ("N-S-D1", "y", 9, 0, 9.035),
    ("N-S-B1", "y", 9, 0, 9.035),
    ("N-S-E1", "y", 9, 0, 9.035),
    # East bedroom / hall partition and the two cross walls. The two cross-wall lines came
    # 4" south of the survey on 2026-08-15, for the same class of reason as N-A-V1 below
    # and against the same policy line: the 16" module outranks an interior partition.
    # N-S-E2 and N-S-E3 are where W-S-E3 and W-S-E4 start, so they set the phase of the
    # east wall's stud grid on the second storey; at the survey's 18'-0"/27'-0" the four
    # east windows had no set of stud lines that mirrored about y=18'-0" at all, and at
    # 17'-8"/26'-8" they have exactly one — 4'-0"/13'-0"/23'-0"/32'-0". The bedroom bays
    # go 9'-0" x 3 to 8'-8"/9'-0"/9'-4", which is the whole cost, and it falls the right
    # way round: RM-S-BED1's R303.1 margin is 0.05 sf and it is the bay that shrank.
    ("N-S-B2", "x", 21, 11, 21.894),
    ("N-S-B2", "y", 17, 8, 17.991, 4.0),
    ("N-S-B3", "y", 26, 8, 26.947, 4.0),
    ("N-S-E2", "y", 17, 8, 17.991, 4.0),
    ("N-S-E3", "y", 26, 8, 26.947, 4.0),
    # West block: walk-in / suite / suite bath.
    ("N-S-D2", "x", 9, 7.5, 9.616),
    ("N-S-D2", "y", 12, 5, 12.391),
    ("N-S-D3", "y", 15, 11, 15.909),
    ("N-S-D4", "y", 22, 4, 22.306),
    ("N-S-W2", "y", 22, 4, 22.306),
    # Vanity alcove. N-S-V2's line went 26'-4" -> 26'-6" on 2026-08-29, with N-S-W1,
    # N-S-BA1 and their three main-storey twins: the whole y=26'-4" line moved 2" north so
    # RM-M-BATH1 one storey down could make UPC 402.5's 24" in front of its water closet
    # (houses/catlin/plan/fixtures.py). This is the same class of trade as N-S-B2/B3/E2/E3
    # above — a code dimension outranking an interior partition line — and it is cheaper
    # than those were: 26'-6" is 1.5" off the survey's 26.374', still inside the default 2"
    # band, so it needs no override.
    ("N-S-V1", "x", 5, 10.5, 5.873),
    ("N-S-V2", "y", 26, 6, 26.374),
    # North-centre closet. (The hall-bath chase is checked separately: the source gives it
    # as a void, not as centrelines.)
    ("N-S-C3D", "y", 30, 10, 30.853),
    ("N-S-B4", "y", 30, 10, 30.853),
)

ATTIC_LINES = (
    ("N-A-C1", "y", 5, 7, 5.611),      # the source's Den north wall line
    # N-A-D1 (the Den's NW corner, same 5.611 line) stood here until 2026-08-27, when
    # RM-A-DEN was deleted and the node with it. N-A-C1 still pins this survey line.
    # The band wall's SOUTH FACE is set on FO-A-STAIR's north edge — the relationship the
    # source itself draws — so its centreline is wherever that face plus half the assembly
    # lands, and the survey line is a check on the face, not on the axis. At 4 1/2" thick
    # the axis fell 2 3/4" south of the source and needed a 3.0" override here. Since
    # 2026-08-27 the wall is the 12 3/4" bookcase assembly, the same face puts the axis at
    # 9'-4", and the error is 1 1/4" — inside the default band, so the override is gone.
    ("N-A-C2", "y", 9, 4, 9.228),
    ("N-A-E1", "y", 9, 4, 9.228),
    # ** THE STAIR VESTIBULE'S THREE NODES ARE GONE (2026-08-29). ** N-A-V1 (22'-8"),
    # N-A-V2 (22'-8") and N-A-V3 (21'-2") carried W-A-VE, W-A-VN and D-A-VEST, the source's
    # Den east and north walls, wrapping ST-S2A's head. The 6:12 roof retired them: at
    # x 21'-2"..22'-8" a full-height screen under a `1 1/2" + (36' - x)/2` rake is a soffit,
    # and D-A-VEST's 6'-8" head has no room at all. They were always a dangling pair closing
    # no polygonized face, so nothing else in the survey depends on them — which is what made
    # the 2026-08-01 4 1/4" trade payable and what makes the deletion payable now. N-A-V1
    # additionally set the phase of the east gable's bay centres by starting W-A-S4; W-A-S3
    # runs the whole east half since the merge, and `layout_origin="line"` lays that grid out
    # from the facade's global line rather than from a start node.
)


# Default fidelity band: the source is read to ~1/16" and rounded to the inch here, so an
# authored line more than 2" off it is drift, not rounding. Rows carrying a fifth number
# override it and say why.
_DEFAULT_TOL_IN = 2.0


@pytest.mark.parametrize("row", SECOND_LINES + ATTIC_LINES,
                         ids=lambda row: f"{row[0]}-{row[1]}")
def test_partition_centreline_matches_the_survey(catlin_plan, row):
    """Each authored line is where we said, and within tolerance of what the drawing shows."""
    tag, axis, feet, inches, source_ft = row[:5]
    tol_in = row[5] if len(row) > 5 else _DEFAULT_TOL_IN
    x, y = _node(catlin_plan, tag)
    got = x if axis == "x" else y
    assert got == pytest.approx(ft(feet, inches).meters, abs=TOL_M)
    assert abs(got - ft(source_ft).meters) <= tol_in * 0.0254


def test_the_lines_the_survey_does_not_get_to_move(catlin_plan):
    """The envelope and the bearing line are house facts, not survey readings."""
    for tag in ("N-S-SW", "N-S-NW", "N-S-W1", "N-S-W2", "N-S-W3"):
        assert _node(catlin_plan, tag)[0] == pytest.approx(0.0, abs=1e-9)
    for tag in ("N-S-SE", "N-S-E1", "N-S-E2", "N-S-E3", "N-S-NE"):
        assert _node(catlin_plan, tag)[0] == pytest.approx(ft(36).meters, abs=1e-9)
    centre = ft(18).meters
    # N-S-C3 retired with the wall segments BM-S-HALL replaced, and N-S-C3B with
    # W-S-BD-N2 and O-S-STAIRTOP (both 2026-07-28).
    for tag in ("N-S-S1", "N-S-C1", "N-S-C2", "N-S-C2B", "N-S-C2C",
                "N-S-C3D", "N-S-N1"):
        assert _node(catlin_plan, tag)[0] == pytest.approx(centre, abs=1e-9)
    for tag in ("N-A-S2", "N-A-C1", "N-A-C2", "N-A-N1"):
        assert _node(catlin_plan, tag)[0] == pytest.approx(centre, abs=1e-9)


def test_hall_bath_chase_is_the_source_two_foot_shaft(catlin_plan):
    """The mechanical chase is still (about) the source's 2'x2' shaft, just relocated.

    The source draws a 2'x2' hatched shaft in the hall bath's NE corner. As of 2026-07-28
    it moved to the NW corner instead — it now carries the radon+plumbing riser up from
    RM-M-MECH below, and the NE corner was never load-bearing for that requirement, just
    where the original architect happened to draw it. What survives from the source is the
    *size* of the clear shaft, not this particular corner.
    """
    west = ft(0).meters + 6.625 * 0.0254                         # exterior wall inside face
    east = _node(catlin_plan, "N-S-CH1")[0] - 2.25 * 0.0254       # 2x4 partition half + gwb
    south = _node(catlin_plan, "N-S-CH1")[1] + 2.25 * 0.0254      # 2x4 partition half + gwb
    north = ft(36).meters - 6.625 * 0.0254                        # exterior wall inside face
    assert east - west == pytest.approx(ft(2).meters, abs=3 * 0.0254)
    assert north - south == pytest.approx(ft(2).meters, abs=3 * 0.0254)


def test_attic_stair_well_sits_on_the_source_and_inside_the_finished_faces(catlin_plan):
    """FO-A-STAIR is the source's well, snapped to the faces the carriages bear on.

    East is the east wall's inside gwb face (36' - 6 5/8"), north is W-S-SS2's south gwb
    face (9'-0" - 2 3/8"), and the depth is then exactly ST-S2A's 3'-0" width. The port had
    this opening at x 22'-8"..36', y 8'-8"..12' — over RM-S-BED1, not RM-S-STUDY2, and with
    its east edge on the sheathing plane where the carriage's wall ledger resolved outside
    the building.
    """
    well = catlin_plan.by_tag("FO-A-STAIR")
    xs = [p.xy_m[0] for p in well.outline]
    ys = [p.xy_m[1] for p in well.outline]
    assert min(xs) == pytest.approx(ft(21, 2).meters, abs=TOL_M)
    assert max(xs) == pytest.approx(ft(35, 5.375).meters, abs=TOL_M)
    assert min(ys) == pytest.approx(ft(5, 9.625).meters, abs=TOL_M)
    assert max(ys) == pytest.approx(ft(8, 9.625).meters, abs=TOL_M)
    assert max(ys) - min(ys) == pytest.approx(ft(3).meters, abs=1e-9)

    stair = catlin_plan.by_tag("ST-S2A")
    # run_reversed on x makes `start` the well's SE corner (resolve/stairs/dispatch.py).
    assert stair.start.xy_m == pytest.approx((max(xs), min(ys)), abs=1e-9)
    assert stair.width.meters == pytest.approx(ft(3).meters, abs=1e-9)
    assert stair.layout == "right_angle_winder" and stair.run_reversed is True


def test_openings_land_on_the_source_gaps(catlin_plan):
    """Doors and windows sit on the gaps measured in the source wall polygon.

    `from_node` offsets are to the opening's near *edge*, so what is asserted here is the
    resolved centre. Windows are additionally snapped to the 16" stud module — the module
    outranks the survey — which is why each pair below is a target and a tolerance rather
    than an equality.
    """
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    centres = {}
    for opening in model.openings:
        wall = model.wall(opening.host_wall)
        (sx, sy), (ex, ey) = wall.axis
        length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
        t = opening.center_along_m / length
        centres[opening.tag] = (sx + (ex - sx) * t, sy + (ey - sy) * t)

    # Bedroom doors are on the hall partition, not on the cross walls: the port hosted
    # D-S-BED1 on W-S-BW1, whose centre resolved into the attic-stair band.
    # D-S-BED2/BED3 came 4" south with N-S-B2/N-S-B3 on 2026-08-15 (their offsets are
    # authored off those nodes and were left alone, so the doors kept their position in
    # their own rooms); D-S-BED1 hangs off N-S-B1, which did not move.
    #
    # D-S-BED2 then left the source gap outright on 2026-08-24, when the swing-direction pass
    # gave it `flip_swing`: swinging the other way put its sweep across FURN-S-BED2-WARD, the
    # room's only wardrobe, and the case cannot move (the bed's own side zone bounds it east
    # and the swing bounds it west, whichever hand the leaf takes). The door went 8 15/16"
    # north instead, to 23'-0 1/16". That is a real deviation from the survey and is asserted
    # as one — put the door back on 24'-1" and `integrity.door_swing_conflict` returns.
    #
    # D-S-BED1 left it on 2026-08-30, and it is the second such departure with a reason
    # rather than a loosened tolerance. Its centre was 15'-2", 6" off W-S-BW1's stud module,
    # so it cut two stud lines where one would do and `structural.door_framing_module` named
    # 15'-8" as the nearest legal station. The move was not free: at 15'-8" the west wall
    # space between RM-S-BED1's SW corner and the door's south jamb runs past NEC
    # 210.52(A)(1)'s 6 ft, so ED-S-BED1-RC5 goes in with it — exactly the trade ED-S-BED2-RC5
    # records one bedroom north. Put the door back on 15'-2" and the stud comes back with it.
    for tag, y_ft in (("D-S-BED1", 15 + 8 / 12), ("D-S-BED2", 23 + 1 / 16 / 12),
                      ("D-S-BED3", 28 + 7 / 12)):
        x, y = centres[tag]
        assert x == pytest.approx(ft(21, 11).meters, abs=TOL_M), tag
        assert y == pytest.approx(ft(y_ft).meters, abs=TOL_M), tag

    # East wall: the source's four 2'-8" openings at y 3'-10", 13'-9", 22'-9", 31'-8".
    # The whole row left the survey on 2026-08-15 for the facade's own mirror (below), so
    # what is still asserted against the source here is the *band* — each window is within
    # 16" of the opening the survey draws for its room, which is what makes it the same
    # window rather than a new one somewhere else in the wall.
    for tag, source_y in (("WIN-S-BED1", 13.75), ("WIN-S-BED2", 22.75)):
        x, y = centres[tag]
        assert x == pytest.approx(ft(36).meters, abs=ft(1).meters), tag
        assert abs(y - ft(source_y).meters) <= ft(1, 4).meters, tag

    # **WIN-S-BED3 left the band on 2026-08-27 and is asserted as a departure, not held in
    # it.** It retyped 27x36 -> 14x24 and moved to y=34'-0" to make a three-storey 14"
    # column with WIN-M-KIT-E below and WIN-A-E-N above — 2'-4" north of the survey's
    # 31'-8" opening, which is 12" past the 16" band the other three sit inside. Pinned to
    # the exact new station rather than loosened to a wider tolerance: the reason it moved
    # is a column, and a column is an equality. RM-S-BED3 pays 4.4 sf of glazing for it and
    # joins BED1/BED2 on R303.1 Exception 1; its R310 egress was never this window's job
    # (WIN-S-HALL-N carries it).
    x, y = centres["WIN-S-BED3"]
    assert x == pytest.approx(ft(36).meters, abs=ft(1).meters)
    assert y == pytest.approx(ft(34).meters, abs=TOL_M)
    assert abs(y - ft(31 + 8 / 12).meters) > ft(1, 4).meters, \
        "BED3 back inside the survey band — the 14\" column it left the band for is gone"

    # The east row is a mirror, not a survey reading and no longer a rhythm either. It ran
    # the source's stations until 2026-07-30, then an exact 9'-0" beat off y=5'-4", and
    # since 2026-08-15 it runs 4'-0"/13'-0"/23'-0"/32'-0" — an even beat is invisible but
    # a row 10" off the centre of the face it sits on is not. The facade's own regularity
    # outranks a survey position the way the 16" module already does; what changed is which
    # regularity. Asserted as the mirror, since that is now the load-bearing claim.
    #
    # The mirror is the INNER pair only since 2026-08-27: BED3's move to the 14" column
    # took the outer pair's north member with it, so WIN-S-STUDY3 keeps its station and
    # loses its partner (see the departure asserted above).
    for near, far in (("WIN-S-BED1", "WIN-S-BED2"),):
        assert centres[near][0] == pytest.approx(ft(36).meters, abs=ft(1).meters), near
        assert centres[far][0] == pytest.approx(ft(36).meters, abs=ft(1).meters), far
        assert centres[near][1] + centres[far][1] == pytest.approx(ft(36).meters,
                                                                  abs=TOL_M), far
    assert centres["WIN-S-STUDY3"][1] == pytest.approx(ft(4).meters, abs=TOL_M)
    # 13'-4", not 13'-0", since 2026-08-25: the inner pair moved 4" outward onto the layout
    # line's stud grid, which made the row evenly beaten (9'-4" x3) as well as mirrored. The
    # mirror asserted just above is the claim that outranks the survey; this station is the
    # row's own rhythm and moves with it.
    assert centres["WIN-S-BED1"][1] == pytest.approx(ft(13, 4).meters, abs=TOL_M)

    # The source draws one balcony door, east of the centre line, inside its 18'-8"..23'-11"
    # run. D-S-DECK-W is ours, not the survey's (2026-07-31) — the second door off the plant
    # room — and it is held to the mirror of D-S-DECK-E about the x=18' centre line rather
    # than to a source station it has none of.
    x, _y = centres["D-S-DECK-E"]
    assert ft(18, 8).meters < x < ft(23, 11).meters
    west, _y = centres["D-S-DECK-W"]
    assert ft(36).meters - x == pytest.approx(west, abs=TOL_M)


def test_balcony_french_door_uses_the_standard_60_inch_type(catlin_plan):
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    opening = next(opening for opening in model.openings if opening.tag == "D-S-DECK-E")
    door_type = next(door_type for door_type in model.plan.library.door_types
                     if door_type.tag == opening.type_ref)
    assert door_type.tag == "DT-EXT-FRENCH60"
    assert opening.width_m == pytest.approx(ft(5).meters)
    assert door_type.operation.value == "double_swing"
    assert door_type.glazed


def test_the_survey_rooms_all_exist(catlin_plan):
    """The rooms the source draws that the port was missing, and the one it does not have."""
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    tags = {room.tag for room in model.rooms if room.storey == "second"}
    # RM-S-LANDING is no longer its own claim: the source's single 181.02 sf "Hallway"
    # reads as one room again now that the centre line is open under BM-S-HALL.
    assert {"RM-S-SUITEBATH", "RM-S-VANITY", "RM-S-NCLOSET", "RM-S-HALL"} <= tags
    assert "RM-S-DRESS" not in tags  # the source has no dressing corridor

    # Source labels, for reference: our clear faces are inset by the gwb only while the
    # survey measures to its own 4 1/4"/6 3/4" wall faces, so ours read uniformly ~8% high.
    # A row may carry its own ceiling where we have deliberately left the survey behind.
    area_sf = {room.tag: room.area_m2 / 0.09290304 for room in model.rooms}
    for tag, source, *ceiling in (("RM-S-BED1", 114.2), ("RM-S-BED2", 114.2),
                                  ("RM-S-BED3", 114.2),
                                  ("RM-S-SUITEBATH", 46.01), ("RM-S-CLOSET", 22.05),
                                  # 1.30, not the default 1.25: W-S-BD-N moved 2" north on
                                  # 2026-08-29 with the whole y=26'-6" line, and this alcove
                                  # is the room that GAINED the 2" (RM-S-BATH1 on the other
                                  # face lost it and is still well inside its band). At
                                  # 18.23 sf it is the smallest room on the list, so the
                                  # clear-face oversizing this whole band exists to absorb
                                  # already ate most of it before the move.
                                  ("RM-S-VANITY", 18.23, 1.30),
                                  ("RM-S-BATH1", 80.73),
                                  ("RM-S-PLANT", 146.40), ("RM-S-STUDY2", 146.42)):
        limit = source * (ceiling[0] if ceiling else 1.25)
        assert source <= area_sf[tag] <= limit, (tag, area_sf[tag])
