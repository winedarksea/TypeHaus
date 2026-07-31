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

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"
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
    # East bedroom / hall partition and the two cross walls.
    ("N-S-B2", "x", 21, 11, 21.894),
    ("N-S-B2", "y", 18, 0, 17.991),
    ("N-S-B3", "y", 27, 0, 26.947),
    ("N-S-E2", "y", 18, 0, 17.991),
    ("N-S-E3", "y", 27, 0, 26.947),
    # West block: walk-in / suite / suite bath.
    ("N-S-D2", "x", 9, 7.5, 9.616),
    ("N-S-D2", "y", 12, 5, 12.391),
    ("N-S-D3", "y", 15, 11, 15.909),
    ("N-S-D4", "y", 22, 4, 22.306),
    ("N-S-W2", "y", 22, 4, 22.306),
    # Vanity alcove.
    ("N-S-V1", "x", 5, 10.5, 5.873),
    ("N-S-V2", "y", 26, 4, 26.374),
    # North-centre closet. (The hall-bath chase is checked separately: the source gives it
    # as a void, not as centrelines.)
    ("N-S-C3D", "y", 30, 10, 30.853),
    ("N-S-B4", "y", 30, 10, 30.853),
)

ATTIC_LINES = (
    ("N-A-C1", "y", 5, 7, 5.611),      # Den north wall
    ("N-A-D1", "y", 5, 7, 5.611),
    # The band wall lands 2 3/4" south of its source line, because its south face is set on
    # FO-A-STAIR's north edge — which is the relationship the source itself draws, with a
    # 6 3/4" wall where ours is 4 1/2".
    ("N-A-C2", "y", 9, 0, 9.228, 3.0),
    ("N-A-E1", "y", 9, 0, 9.228, 3.0),
    ("N-A-V1", "x", 22, 4, 22.31),     # stair vestibule east screen
    ("N-A-V2", "x", 22, 4, 22.31),
    ("N-A-V3", "x", 21, 2, 21.14),     # its north screen, stopping at the well
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
    for tag, y_ft in (("D-S-BED1", 15 + 2 / 12), ("D-S-BED2", 24 + 1 / 12),
                      ("D-S-BED3", 28 + 11 / 12)):
        x, y = centres[tag]
        assert x == pytest.approx(ft(21, 11).meters, abs=TOL_M), tag
        assert y == pytest.approx(ft(y_ft).meters, abs=TOL_M), tag

    # East wall: the source's four 2'-8" openings at y 3'-10", 13'-9", 22'-9", 31'-8",
    # each snapped to the nearest stud line on its own host.
    for tag, source_y in (("WIN-S-BED1", 13.75), ("WIN-S-BED2", 22.75),
                          ("WIN-S-BED3", 31 + 8 / 12)):
        x, y = centres[tag]
        assert x == pytest.approx(ft(36).meters, abs=ft(1).meters), tag
        assert abs(y - ft(source_y).meters) <= ft(0, 8).meters, tag

    # WIN-S-STUDY3 is the one east opening that leaves its source station on purpose
    # (2026-07-30 facade pass). The source draws it at y 3'-10", which put the row at
    # 10'-4"/9'-0"/9'-0"; at y 5'-4" the four windows run one exact 9'-0" rhythm, and
    # the facade's own regularity outranks a survey position the way the 16" module
    # already does. Asserted against the rhythm, not the survey.
    x, y = centres["WIN-S-STUDY3"]
    assert x == pytest.approx(ft(36).meters, abs=ft(1).meters)
    assert y == pytest.approx(ft(5, 4).meters, abs=TOL_M)
    for near, far in (("WIN-S-STUDY3", "WIN-S-BED1"), ("WIN-S-BED1", "WIN-S-BED2"),
                      ("WIN-S-BED2", "WIN-S-BED3")):
        assert centres[far][1] - centres[near][1] == pytest.approx(ft(9).meters,
                                                                  abs=TOL_M), far

    # One balcony door, east of the centre line, inside the source's 18'-8"..23'-11" run.
    assert "D-S-DECK-W" not in centres
    x, _y = centres["D-S-DECK-E"]
    assert ft(18, 8).meters < x < ft(23, 11).meters


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
    area_sf = {room.tag: room.area_m2 / 0.09290304 for room in model.rooms}
    for tag, source in (("RM-S-BED1", 114.2), ("RM-S-BED2", 114.2), ("RM-S-BED3", 114.2),
                        ("RM-S-SUITEBATH", 46.01), ("RM-S-CLOSET", 22.05),
                        ("RM-S-VANITY", 18.23), ("RM-S-BATH1", 80.73),
                        ("RM-S-PLANT", 146.40), ("RM-S-STUDY2", 146.42)):
        assert source <= area_sf[tag] <= source * 1.25, (tag, area_sf[tag])
