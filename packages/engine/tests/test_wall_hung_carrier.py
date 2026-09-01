"""A wall-hung WC's carrier: the bay it needs, the framing around it, and where it drains.

Three things had to become true at once for ``FX-TOILET-WH`` to be modelled honestly, and
each is a separate failure mode if it drifts:

* the framing solver parts its module studs around the frame (and around nothing else),
* the frame is *framed* — flanking studs and blocking, real sticks in the BOM,
* the drain point is derived from the type and the host wall rather than restated by hand
  on the instance.

``houses/catlin``'s ``FX-M-BATH1-WC`` is the one instance in the repo, so it is the oracle
throughout. ``W-M-HS1`` is ``INT_2X6_STAGGERED_PLUMBING`` — a *halved* 8" module — which is
what makes the keepout worth testing: an unparted layout puts two studs through the frame.
"""

from __future__ import annotations

import pytest

from typehaus.resolve.framing.carriers import (
    CARRIER_FRAME_HEIGHT_M,
    backing_wall,
    carrier_bands,
    carrier_bays,
    carrier_keepouts,
)

IN = 0.0254
CARRIER_WALL = "W-M-HS1"
CARRIER_FIXTURE = "FX-M-BATH1-WC"


@pytest.fixture()
def bay(catlin_plan, catlin_model_ro):
    bays = carrier_bays(catlin_plan, catlin_model_ro)
    assert len(bays) == 1, [b.fixture_tag for b in bays]
    return bays[0]


def test_the_carrier_is_located_on_the_wall_it_stands_in_not_its_wet_wall(catlin_plan, bay):
    """``wall_ref`` says ``W-M-BAE``, and following it would frame a bay in the wrong wall.

    This is the whole reason ``backing_wall`` resolves the host geometrically. The fixture's
    own ``wall_ref`` is its WET wall — where the vent takeoff and the supply riser are — and
    at catlin the two walls are perpendicular to each other.
    """
    fixture = catlin_plan.by_tag(CARRIER_FIXTURE)
    assert fixture.wall_ref == "W-M-BAE"
    assert bay.wall_tag == CARRIER_WALL
    # 19 3/4" of clear bay, centred on the bowl at x = 26.41".
    assert bay.center_m / IN == pytest.approx(26.409, abs=0.01)
    assert bay.half_m * 2 / IN == pytest.approx(19.75, abs=1e-6)


def test_a_floor_mounted_fixture_claims_no_bay(catlin_plan, catlin_model_ro):
    """Three gates, and ``FX-M-BATH2-WC`` fails one of them on the very same wall.

    It backs ``W-M-HS1`` too, and it drains, and nothing about its footprint says it has no
    frame — only its type's silence on ``carrier_bay_width`` does. That silence is the gate.
    """
    types = {item.tag: item for item in catlin_plan.library.fixture_types}
    floor_mount = catlin_plan.by_tag("FX-M-BATH2-WC")
    fixture_type = types[floor_mount.type_ref]
    assert fixture_type.carrier_bay_width is None
    host = backing_wall(catlin_plan, catlin_model_ro, floor_mount, fixture_type)
    assert host is not None and host[0].tag == CARRIER_WALL  # it does back the same wall
    assert all(b.fixture_tag != floor_mount.tag
               for b in carrier_bays(catlin_plan, catlin_model_ro))


def test_the_keepout_is_wider_than_the_bay_by_a_stud_each_side(catlin_plan, catlin_model_ro):
    """The module has to clear the flanking studs, not just the frame between them."""
    (band,) = carrier_bands(catlin_plan, catlin_model_ro)[CARRIER_WALL]
    (keepout,) = carrier_keepouts(catlin_plan, catlin_model_ro)[CARRIER_WALL]
    assert keepout[0] == pytest.approx(band[0])
    assert (keepout[1] - band[1]) / IN == pytest.approx(1.5)


def test_module_studs_part_around_the_bay_and_only_around_it(catlin_model_ro, bay):
    """No module stud inside the bay, and the neighbouring rhythm untouched.

    "And only around it" is the half that would fail silently: a keepout that swallowed the
    whole wall would also pass "no stud in the bay", and nobody would notice until the
    drywall had nothing to land on.
    """
    wall = catlin_model_ro.wall(CARRIER_WALL)
    stations = sorted((member.p0[0] - wall.axis[0][0]) / IN
                      for member in wall.members
                      if member.category == "stud"
                      and not member.child_key.startswith("carrier-"))
    low, high = bay.low_m / IN, bay.high_m / IN
    inside = [s for s in stations if low + 1e-6 < s < high - 1e-6]
    assert not inside, f"module studs at {inside} run through the carrier frame"
    # Beyond the bay the 8" staggered rhythm is exactly as it was.
    assert [s for s in stations if s > high] == pytest.approx([40.0, 48.0, 56.0, 64.0, 72.0])


def test_the_bay_is_framed_rather_than_merely_empty(catlin_model_ro, bay):
    """Studs on the bay's edges, a course at its base and head, cripples over the head."""
    wall = catlin_model_ro.wall(CARRIER_WALL)
    carrier = {member.child_key: member for member in wall.members
               if member.child_key.startswith("carrier-")}
    assert set(carrier) == {"carrier-0-stud-0", "carrier-0-stud-1",
                            "carrier-0-block-0", "carrier-0-head-1",
                            "carrier-0-cripple-000", "carrier-0-cripple-001"}
    x0 = wall.axis[0][0]
    studs = sorted((carrier[k].p0[0] - x0) / IN for k in ("carrier-0-stud-0", "carrier-0-stud-1"))
    # Stud centres sit half a stud outboard of the clear bay, so their inner faces ARE it.
    assert studs == pytest.approx([bay.low_m / IN - 0.75, bay.high_m / IN + 0.75])
    for key in ("carrier-0-stud-0", "carrier-0-stud-1"):
        assert carrier[key].category == "stud"
        assert carrier[key].profile == "2x6"  # full plate depth, not a staggered half-bay
    base, head = carrier["carrier-0-block-0"], carrier["carrier-0-head-1"]
    # Both courses are "blocking", not "header": a header registers against a real opening
    # (test_opening_framing_registers_with_the_opening_it_frames), and nothing passes
    # through a carrier bay.
    assert (base.category, head.category) == ("blocking", "blocking")
    assert base.length_m / IN == pytest.approx(19.75)
    assert (head.z0_m - base.z0_m) == pytest.approx(CARRIER_FRAME_HEIGHT_M)


def test_cripples_put_the_module_back_above_the_head_course(catlin_model_ro):
    """``W-S-SN1`` stacks on this wall, so the three displaced studs have to reappear.

    Not a new rhythm: the cripples stand on the wall's OWN 8" staggered module, at exactly
    the stations the keepout removed. They restore the load path, not the metric —
    ``_stud_grid.orphan_studs`` counts category "stud", and a cripple is not one, by the
    same design that excludes a window's cripples.
    """
    wall = catlin_model_ro.wall(CARRIER_WALL)
    x0 = wall.axis[0][0]
    head = next(m for m in wall.members if m.child_key == "carrier-0-head-1")
    cripples = [m for m in wall.members if m.category == "cripple"
                and m.child_key.startswith("carrier-")]
    # 24" and 32", not 16": the 16" module lands 0.22" from the jamb stud at 15.78", and a
    # cripple there would interpenetrate it. The jamb IS the full-height member on that line.
    assert sorted((m.p0[0] - x0) / IN for m in cripples) == pytest.approx([24.0, 32.0])
    assert all(m.z0_m == pytest.approx(head.z1_m) for m in cripples)
    # They run to the wall's own framing top, like the module studs they replace.
    module_top = max(m.z1_m for m in wall.members if m.category == "stud")
    assert all(m.z1_m == pytest.approx(module_top) for m in cripples)


def test_the_drain_point_is_derived_from_the_type_and_the_host_wall(catlin_plan,
                                                                   catlin_model_ro):
    """No ``drain_position`` on the instance, and the derived point is not the type nominal.

    The type states 11.9" behind the bowl centre, which is a PRODUCT set-back measured off
    the frame's face — it cannot know the finish thickness in front of it. Projected onto
    the host wall's axis, the drop lands centred in the 5 1/2" cavity, 1.135" further back,
    which is where the deleted override used to say it was.
    """
    from typehaus.resolve.mep_sleeves import _expected_drain_point

    fixture = catlin_plan.by_tag(CARRIER_FIXTURE)
    assert fixture.drain_position is None, "the override is derived now; do not re-author it"

    point = _expected_drain_point(catlin_model_ro, CARRIER_FIXTURE)
    wall = catlin_model_ro.wall(CARRIER_WALL)
    assert point[0] / IN == pytest.approx(26.409, abs=0.01)
    assert point[1] == pytest.approx(wall.axis[0][1])          # on the wall's own axis
    assert point[1] != pytest.approx(fixture.position.xy_m[1])  # NOT under the footprint
    nominal = fixture.position.xy_m[1] - 11.9 * IN             # the type's raw set-back
    assert abs(point[1] - nominal) / IN == pytest.approx(1.135, abs=0.01)


def test_a_floor_drained_wc_still_drops_under_its_own_footprint(catlin_model_ro):
    """The WALL branch must not have swallowed the "no WATER_HOT" heuristic it precedes."""
    from typehaus.resolve.mep_sleeves import _expected_drain_point

    for tag in ("FX-M-BATH2-WC", "FX-B-BATH-WC", "FX-A-STUBATH-WC"):
        fixture = catlin_model_ro.plan.by_tag(tag)
        if fixture.drain_position is not None:
            continue
        assert _expected_drain_point(catlin_model_ro, tag) == fixture.position.xy_m


def test_the_carrier_checks_report_the_bath2_crowding_without_failing(catlin_model_ro):
    """A 5 1/2" wall is what makes the overlap a rough-in note rather than a defect.

    ``FX-M-BATH2-WC`` backs the south face of the same wall and its body overlaps the bay by
    16.3". In this cavity a Duofix 2x4-class frame leaves ~2" behind it for a 1/2" supply to
    cross; in a 3 1/2" one there would be nothing to cross through, and the same geometry
    would be a FAIL. Both checks are ADVISORY, so neither may fail catlin today.
    """
    from typehaus.checks.advisory.carriers import carrier_bay_conflict, carrier_bay_depth
    from typehaus.checks.registry import CheckContext, Preferences

    ctx = CheckContext(plan=catlin_model_ro.plan, model=catlin_model_ro,
                       preferences=Preferences(), profile=None)  # neither check reads a profile
    findings = [*carrier_bay_depth(ctx), *carrier_bay_conflict(ctx)]
    assert {f.check_id for f in findings} == {"advisory.carrier_bay_depth",
                                              "advisory.carrier_bay_conflict"}
    assert all(f.result.value == "pass" for f in findings), [f.message for f in findings]
    conflict = next(f for f in findings if f.check_id == "advisory.carrier_bay_conflict")
    assert "FX-M-BATH2-WC" in conflict.message and "BEHIND the frame" in conflict.message
