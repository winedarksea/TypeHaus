"""An interior partition's framing stops 3/4" under the structure over it — and only that.

Two things are pinned here and the second is the one that keeps getting re-collapsed:

1. **Where the framing tops out.** In the attic, the rafter SOFFIT less the gap, raked — not
   the roof deck plane, which put a double top plate through the full depth of a TJI 230.
   Everywhere else, the joist or SIP soffit less the gap.
2. **That ``z1_m`` never moves DOWN with it.** The body — the layer prisms, the gypsum bill,
   the stair-enclosure extent, the wet wall a riser climbs — belongs to ``platform.py``.
   Cutting it at the joist soffit as well opens a 12-5/8" slot in ``ST-S2A``'s enclosure
   (``code.R312_1_1_stair_open_side``) and leaves ``PR-B-CW-HYD-RISER`` and the two suite
   risers outside their own wet wall (``mep.wet_wall_occupancy`` x3). Four new FAILs on a
   house the gate holds at its two deliberate ones.

And the two gates that decide WHICH walls: a wall something bears on is not a partition
however little the author wrote on it (``bearing_refs``, swept generically because a
``Stair`` and a ``FloorOpening`` carry the field too), and a room inside a room is not one
either (``runs_full_storey_height``).
"""

from __future__ import annotations

import pytest

from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG
from typehaus.resolve.partition import (
    DEFLECTION_GAP_M,
    bearing_ref_tags,
    is_interior_partition,
    runs_full_storey_height,
    takes_a_deflection_gap,
)
from typehaus.resolve.roof_geometry import roof_underside_at
from typehaus.takeoff.partition_fasteners import partition_deflection_screw_rows

_IN = 0.0254

#: Every attic partition — the seven ``ToRoof`` walls the rake used to run to the deck.
_ATTIC = ("W-A-BA-E", "W-A-BATH-S", "W-A-GC-S", "W-A-HALL-S", "W-A-SN", "W-A-STU-N",
          "W-A-STU-W")

#: Walls that pass :func:`is_interior_partition` and must NOT move: a room inside a room
#: (the sauna hot room), the tub-deck curbs, the three fireplace wythe piers, a screen skirt.
#: Three of them sit inside ``platform._MAX_BAND_M``, so that guard does not save them.
#: (``W-M-FIRE-STUB`` became ``-STUB-S``/``-M``/``-N`` on 2026-09-19 — three 12" piers with
#: the joist pockets as gaps between them. Same wythe, same z band, three tags.)
_NOT_FULL_HEIGHT = ("W-B-SA-N", "W-B-SA-N2", "W-B-SA-W", "W-M-TUBDK-S", "W-M-TUBDK-W",
                    "W-M-FIRE-STUB-S", "W-M-FIRE-STUB-M", "W-M-FIRE-STUB-N",
                    "W-BW-SCREEN-SKIRT")


def test_the_gap_is_three_quarters_of_an_inch() -> None:
    """The SDPW sleeve, and the number the whole rule turns on."""
    assert round(DEFLECTION_GAP_M / _IN, 9) == 0.75


def test_every_attic_partition_rakes_to_the_rafter_soffit(catlin_model_ro) -> None:
    """Both endpoint elevations, against ``roof_underside_at`` read at the same points."""
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-HOUSE")
    for tag in _ATTIC:
        wall = catlin_model_ro.wall(tag)
        assert wall is not None, tag
        assert wall.plate_top_z_m is None, f"{tag} rakes; it has no flat plate"
        for point, top in zip(wall.axis, (wall.top_z0_m, wall.top_z1_m), strict=True):
            expected = roof_underside_at(catlin_model_ro, roof, point) - DEFLECTION_GAP_M
            assert top == pytest.approx(expected, abs=1e-9), tag


def test_the_attic_plate_is_a_foot_below_the_deck_it_used_to_reach(catlin_model_ro) -> None:
    """The size of the bug, stated: an 11-7/8" rafter plus the gap."""
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-HOUSE")
    from typehaus.resolve.roof_geometry import roof_height_at

    wall = catlin_model_ro.wall("W-A-STU-N")
    deck = roof_height_at(roof, wall.axis[0])
    assert (deck - wall.top_z0_m) / _IN == pytest.approx(11.875 + 0.75, abs=1e-6)


def test_a_storey_line_partition_moves_its_plate_and_not_its_body(catlin_model_ro) -> None:
    """**The two-tops contract, as a test, so nobody re-collapses it.**

    ``W-M-HS3`` is lifted through the main floor's joist band to the second-storey datum.
    Its plate stops 3/4" under the 11-7/8" I-joist soffit; its body still runs the full
    storey line, because that is what closes the band and what the stair enclosure and the
    wet walls are measured against.
    """
    wall = catlin_model_ro.wall("W-M-HS3")
    assert wall.plate_top_z_m / _IN == pytest.approx(107.375, abs=1e-6)
    assert wall.z1_m / _IN == pytest.approx(120.0, abs=1e-6)


def test_the_body_never_sinks_below_the_plate_on_any_partition(catlin_model_ro) -> None:
    """The whole of the "shape A" guard, swept rather than spot-checked."""
    refs = bearing_ref_tags(catlin_model_ro.plan)
    for wall in catlin_model_ro.walls:
        if not takes_a_deflection_gap(catlin_model_ro, wall, refs):
            continue
        top = wall.plate_top_z_m if wall.plate_top_z_m is not None else wall.z1_m
        assert top <= wall.z1_m + 1e-9, wall.tag


def test_the_one_wall_whose_framing_goes_down_to_a_sip_soffit(catlin_model_ro) -> None:
    """``W-B-CE`` stands under ``SL-M-DECK``, whose soffit is 1-9/16" below the joists'.

    The ``min`` across the decks covering a wall, and the reason it is a ``min``: a
    ``ResolvedWall`` carries one flat framing top, so the low reading is the only one that
    never runs into structure. (``W-B-CW`` also sees ``SL-M-TUBDK`` 20" UP, where a ``max``
    would put a basement plate 19-1/4" above its own ceiling.)
    """
    wall = catlin_model_ro.wall("W-B-CE")
    assert wall.plate_top_z_m / _IN == pytest.approx(-14.1875, abs=1e-6)
    assert wall.z1_m / _IN == pytest.approx(-13.4375, abs=1e-6)


def test_a_partition_whose_plate_rises_takes_its_body_with_it(catlin_model_ro) -> None:
    """``W-B-CW`` authors 8'-0" in a 8'-0 1/16" storey and reaches nothing. It does now.

    The plate rises 13/16" to meet the joist soffit less the gap, and the body follows,
    because drywall runs to the top plate. Rising is the safe direction: it closes a gap,
    and cannot open one in a stair enclosure or a wet wall.
    """
    wall = catlin_model_ro.wall("W-B-CW")
    assert wall.plate_top_z_m / _IN == pytest.approx(-12.625, abs=1e-6)
    assert wall.z1_m == pytest.approx(wall.plate_top_z_m, abs=1e-9)


@pytest.mark.parametrize("tag", _NOT_FULL_HEIGHT)
def test_a_room_inside_a_room_is_left_alone(catlin_model_ro, tag: str) -> None:
    refs = bearing_ref_tags(catlin_model_ro.plan)
    wall = catlin_model_ro.wall(tag)
    assert wall is not None, tag
    assert is_interior_partition(catlin_model_ro, wall, refs), \
        f"{tag} is what the full-height gate exists to catch, not what another gate catches"
    assert not runs_full_storey_height(catlin_model_ro, wall), tag
    assert wall.plate_top_z_m is None or wall.plate_top_z_m == pytest.approx(wall.z1_m)


@pytest.mark.parametrize("tag", ("W-S-SS2", "W-S-SN3"))
def test_a_wall_something_bears_on_is_not_a_partition(catlin_model_ro, tag: str) -> None:
    """``ST-S2A.bearing_refs`` holds the first and a ``FloorOpening``'s holds the second.

    Neither is a ``Wall``/``Roof``/``FloorSystem``, which is why the sweep is generic. Lower
    these two and the stair enclosure and the deck hole's header both lose their support.
    """
    refs = bearing_ref_tags(catlin_model_ro.plan)
    assert tag in refs
    wall = catlin_model_ro.wall(tag)
    assert not takes_a_deflection_gap(catlin_model_ro, wall, refs)
    assert wall.z1_m / _IN == pytest.approx(240.0, abs=1e-6)


def test_the_gate_answers_the_same_before_and_after_the_pass(catlin_model_ro) -> None:
    """62 partitions, including the four new study return/rear segments.

    Not a tautology: the pass MOVES the plate it selects on, so a full-height tolerance
    measured only upward would drop ``W-B-CE`` — whose plate lands 1-11/16" below its
    storey line — the moment it had been treated as a partition. The fastener take-off asks
    this question of the resolved model, so it has to be a fixed point.
    """
    refs = bearing_ref_tags(catlin_model_ro.plan)
    tags = [w.tag for w in catlin_model_ro.walls
            if takes_a_deflection_gap(catlin_model_ro, w, refs)]
    assert len(tags) == 62
    assert "W-B-CE" in tags


# --- the SDPW schedule -----------------------------------------------------------------


@pytest.fixture(scope="module")
def sdpw_rows(catlin_model_ro):
    return partition_deflection_screw_rows(catlin_model_ro, CONFIG.partition_deflection)


def test_the_part_is_chosen_by_the_top_plate_and_not_by_length(sdpw_rows) -> None:
    """Every row is the SDPW19600, and the deciding fact is not that 6" reaches.

    4.50" is required (3/4" gap + a 3" double top plate + 3/4" published minimum
    penetration) and the 5" SDPW14500 reaches it comfortably — but Simpson publish that
    screw's allowables and spacing for a single 2x or a built-up plate to 2-1/4", and the
    SDPW19600's for the double 2x this house frames on all eleven interior assemblies.
    """
    billed = [row for row in sdpw_rows if row["count"]]
    assert billed
    assert {row["part_number"] for row in billed} == {"SDPW19600"}
    assert all(row["size"] == "6 in" for row in billed)
    assert all("double 2x top plate" in row["basis"] for row in billed)


def test_the_three_count_rules_are_three_rows(sdpw_rows) -> None:
    """Perpendicular crossings, a pitch under a parallel member, blocked bays between them.

    Splitting the parallel case in two is not optional: coding only the blocking branch
    would call for blocking in the bays that already have a joist in them.
    """
    counts = {row["scope"]: row["count"] for row in sdpw_rows}
    # 2026-09-23: FS-S-WEST's 26'-8" truss moved to 26'-10", off W-M-STOS2 (2 -> 3 blocked).
    assert counts == {
        "partition top plate, perpendicular framing above": 101,
        "partition top plate, under a parallel member": 10,
        "partition top plate, blocking between parallel members": 77,
    }


def test_the_attic_bills_ten_crossings_and_only_because_the_plates_came_down(
        sdpw_rows) -> None:
    """Before Part 1 the attic gap read -11 7/8" and every one of these was a refusal."""
    row = next(r for r in sdpw_rows
               if r["scope"] == "partition top plate, perpendicular framing above")
    assert row["by_storey"]["attic"] == 10


def test_a_partition_under_a_sip_soffit_is_refused_and_says_so(sdpw_rows) -> None:
    """A screw into a SIP is a different part on a different rule. Never silently billed.

    The refusal rides on the basis of the rows that WERE billed rather than on a zero-count
    row of its own: such a row reaches the per-trade RFQ and the S-series hardware schedule
    as an order line for nothing.
    """
    assert all(row["count"] for row in sdpw_rows), "no row here may be an empty order line"
    for row in sdpw_rows:
        for tag in ("W-B-CE", "W-B-BA-E", "W-B-WELL"):
            assert tag in row["basis"], f"{row['scope']} does not name {tag}"


def test_the_blocking_row_says_where_the_blocking_IS_framed(sdpw_rows) -> None:
    """It said "billed nowhere" until 2026-09-19, and that stopped being true.

    ``resolve/floor_blocking.py`` now lays a block between the joists over a partition
    standing in a bay, at the same framing module this count uses. Over a ROOF it still
    does not, and the basis has to keep saying so — this row covers both.
    """
    row = next(r for r in sdpw_rows
               if r["scope"] == "partition top plate, blocking between parallel members")
    assert "floor_blocking" in row["basis"]
    assert "over a ROOF it is not carried" in row["basis"]


def test_the_screw_releases_vertically_and_the_catalog_says_so() -> None:
    """``uplift_lb`` must stay ``None``: this joint deliberately does not hold anything down."""
    from typehaus.hardware.catalog import (
        ROLE_PARTITION_DEFLECTION_SCREW,
        structural_hardware_catalog,
    )

    records = [item for item in structural_hardware_catalog()
               if item.role == ROLE_PARTITION_DEFLECTION_SCREW]
    assert len(records) == 2
    for item in records:
        assert item.allowable is not None, item.tag
        assert item.allowable.uplift_lb is None, item.tag
        assert item.allowable.lateral_f1_lb and item.allowable.lateral_f2_lb
        assert "ER-192" in item.allowable.citation
