"""HVAC duct/joist-bay resolver + checks (→ Permit-ready plan set Phase 3)."""

from __future__ import annotations

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier


@pytest.fixture(scope="module")
def second_floor(catlin_model):
    """The east half — I-joist — for the generic joist-bay tests below. Its x-span is
    18'-36' (5.4864m-10.9728m), so the synthetic duct paths here sit inside that range
    rather than the pre-split fixture's 1m-5m."""
    return next(f for f in catlin_model.floors if f.tag == "FS-S-EAST")


@pytest.fixture(scope="module")
def west_floor(catlin_model):
    """The west half — open-web floor truss — for the open-web legality tests. Its
    x-span is 0'-18' (0m-5.4864m)."""
    return next(f for f in catlin_model.floors if f.tag == "FS-S-WEST")


def test_parallel_in_bay_trunk_ducts_pass(catlin_model):
    for duct in catlin_model.ducts:
        assert duct.conflicts == (), (duct.tag, duct.conflicts)
        assert duct.depth_ok


def test_duct_centered_on_a_joist_line_fails(second_floor):
    from typehaus.model.enums import DuctRouting
    from typehaus.resolve.mep import duct_bay_occupancy

    conflicts, _, _ = duct_bay_occupancy(
        [(6.0, 0.4064), (9.0, 0.4064)],  # centered exactly on the joist line at y=16"
        width_m=0.3048, depth_m=0.2032, routing=DuctRouting.JOIST_BAY,
        floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts


def test_sixteen_inch_wide_duct_fails_clear_bay_width(second_floor):
    from typehaus.model.enums import DuctRouting
    from typehaus.resolve.mep import duct_bay_occupancy

    conflicts, _, _ = duct_bay_occupancy(
        [(6.0, 6.2992), (9.0, 6.2992)], width_m=0.4064, depth_m=0.2032,
        routing=DuctRouting.JOIST_BAY, floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts


def test_perpendicular_run_requires_soffit_or_chase(second_floor):
    from typehaus.model.enums import DuctRouting
    from typehaus.resolve.mep import duct_bay_occupancy

    conflicts, _, _ = duct_bay_occupancy(
        [(6.0, 0.0), (6.0, 3.0)], width_m=0.3048, depth_m=0.2032,
        routing=DuctRouting.JOIST_BAY, floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts
    conflicts_soffit, _, _ = duct_bay_occupancy(
        [(6.0, 0.0), (6.0, 3.0)], width_m=0.3048, depth_m=0.2032,
        routing=DuctRouting.SOFFIT, floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts_soffit == []


def test_perpendicular_run_through_open_web_is_legal_within_the_chord_opening(west_floor):
    """A truss's 8 7/8" clear chord-to-chord opening (11.875" depth, two 1.5" chords) lets
    a shallow-enough perpendicular run cross without a soffit or chase; a run too deep for
    the opening still conflicts, and names the real reason."""
    from typehaus.model.enums import DuctRouting
    from typehaus.resolve.mep import duct_bay_occupancy

    conflicts, crossings, _ = duct_bay_occupancy(
        [(1.0, 0.0), (1.0, 3.0)], width_m=0.3048, depth_m=0.1524,  # 6" deep, fits the web
        routing=DuctRouting.JOIST_BAY, floor=west_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts == []
    assert crossings

    conflicts_deep, _, _ = duct_bay_occupancy(
        [(1.0, 0.0), (1.0, 3.0)], width_m=0.3048, depth_m=0.254,  # 10" deep, too deep
        routing=DuctRouting.JOIST_BAY, floor=west_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert conflicts_deep
    assert any("opening" in message for message in conflicts_deep)


def test_bearing_crossing_reported_with_fire_blocking_note(catlin_model):
    """A duct crossing a bearing line is legal, not a defect — the resolver lays identical
    perpendicular positions on both sides of the line. What the builder still owes is the
    R302.11 draftstop, so the crossing rides along as a *note on a PASS* rather than as a
    failure that would have to be waived on every through-duct in the house."""
    report = run_from_model(catlin_model, [], tier=Tier.STRUCTURAL, only="mep.duct_joist_bay")
    matched = [f for f in report.findings if f.check_id == "mep.duct_joist_bay"]
    assert matched
    assert all(f.result.value == "pass" for f in matched)
    assert all(f.severity.value == "warn" for f in matched)  # never a permit-gate blocker
    noted = [f for f in matched if "crosses bearing wall" in f.message]
    assert noted
    assert all("R302.11" in f.message and "fire blocking" in f.message for f in noted)


def test_depth_exceeding_joist_depth_fails(second_floor):
    from typehaus.model.enums import DuctRouting
    from typehaus.resolve.mep import duct_bay_occupancy

    _, _, depth_ok = duct_bay_occupancy(
        [(6.0, 6.2992), (9.0, 6.2992)], width_m=0.3048, depth_m=0.4,  # ~15.75" > 11.875"
        routing=DuctRouting.JOIST_BAY, floor=second_floor, bearing_walls=[], spacing_m=0.4064,
    )
    assert not depth_ok


# --- mep.duct_connectivity ------------------------------------------------------------
#
# The rule is "no duct ends in mid-air", and every one of these guards a way the first
# drafts of it got a wrong answer confidently. Two runs sharing a plan point on different
# floors is the recurring one, and it is silent in both directions: it hid four real
# orphans behind coincidences, and it would have reported a legitimate tee as one.


def _connectivity(model):
    report = run_from_model(model, [], tier=Tier.INTEGRITY, only="mep.duct_connectivity")
    return [f for f in report.findings if f.check_id == "mep.duct_connectivity"]


def test_no_duct_in_catlin_ends_on_nothing(catlin_model):
    findings = _connectivity(catlin_model)
    assert findings
    orphans = [f.message for f in findings if f.result.value == "fail"]
    assert not orphans, orphans


def test_a_branch_tees_into_the_side_of_a_trunk(catlin_model):
    """Against a *segment*, not a vertex. DU-S-HP-SUITE leaves DU-S-HP-SUP 118" from either
    end of the trunk's only leg, which is where a take-off normally lands."""
    landed = [f.message for f in _connectivity(catlin_model)
              if "DU-S-HP-SUITE start" in f.message]
    assert landed == ["duct DU-S-HP-SUITE start lands on DU-S-HP-SUP"]


def test_the_trunk_hands_off_collinearly_at_its_south_cap(catlin_model):
    """** THIS TEST ASSERTED A CAPPED END UNTIL 2026-09-04, AND THE REVERSAL IS THE POINT. **

    DU-S-HP-SUP used to run NORTH out of a machine at the south end of the chase and simply
    stop past its last bedroom boot — a cap earned from the take-offs on its final leg.
    With EQ-S-HP1-AH moved to SF-S-HP1 over RM-S-NCLOSET the trunk runs SOUTH, and its end
    is no longer a cap at all: DU-S-HP-SOUTH-RISE picks it up COLLINEARLY at x=19'-6",
    y=9'-10", 18x8 reducing to 10x6, and stands up into the FS-ATTIC bay.

    That reducer replaced an east dogleg with two elbows whose only purpose was to get round
    the old machine. So the assertion is the handoff, and the check earning it from geometry
    rather than from a `duct_ref` is what makes it worth pinning.
    """
    ends = [f for f in _connectivity(catlin_model) if "DU-S-HP-SUP end" in f.message]
    assert len(ends) == 1
    assert ends[0].result.value == "pass"
    assert ends[0].message == "duct DU-S-HP-SUP end lands on DU-S-HP-SOUTH-RISE"
    # And the handoff is collinear: same x, and the riser starts where the trunk stops.
    trunk = next(d for d in catlin_model.ducts if d.tag == "DU-S-HP-SUP")
    riser = next(d for d in catlin_model.ducts if d.tag == "DU-S-HP-SOUTH-RISE")
    assert trunk.path[-1] == pytest.approx(riser.path[0])
    assert {p[0] for p in trunk.path} == {p[0] for p in riser.path}


def test_a_machine_67_inches_above_the_end_is_not_a_joint(catlin_model):
    """The elevation band on the equipment probe. Drop DU-ERV-OA's last vertex to the floor
    and it is no longer in EQ-B-ERV's case, however squarely it still sits in its footprint —
    which is exactly how both ERV chase risers passed a plan-only test while ending 67" under
    the gable hood they were credited to."""
    import dataclasses

    index, duct = next((i, d) for i, d in enumerate(catlin_model.ducts)
                       if d.tag == "DU-ERV-OA")
    catlin_model.ducts[index] = dataclasses.replace(
        duct, z_m=(*duct.z_m[:-1], duct.z_m[-1] - 2.0))  # 6'-7" lower: below the case
    orphans = [f.message for f in _connectivity(catlin_model) if f.result.value == "fail"]
    assert any("DU-ERV-OA end" in message for message in orphans), orphans


@pytest.mark.parametrize("n", (1, 2, 3))
def test_each_bedroom_grille_is_fed_by_a_drawn_branch(catlin_plan, catlin_model, n):
    """REG-S-HP-BED1/2/3 named the trunk until 2026-09-23 and nothing reached them: the check
    tests run ENDS and `register_duct_ref` only that the tag exists. Each is now the boot at
    the end of its own branch: a side collar straight off DU-S-HP-SUP's east face."""
    from typehaus.checks.mep.duct_connectivity import BOOT_REACH_M

    register = next(e for e in catlin_plan.all_elements() if e.tag == f"REG-S-HP-BED{n}")
    assert register.duct_ref == f"DU-S-HP-BED{n}"
    leg = next(d for d in catlin_model.ducts if d.tag == f"DU-S-HP-BED{n}")
    at = next(o.position for o in catlin_model.canvas_objects if o.tag == register.tag)
    end = leg.path[-1]
    assert ((at[0] - end[0]) ** 2 + (at[1] - end[1]) ** 2) ** 0.5 <= BOOT_REACH_M
    findings = {f.message for f in _connectivity(catlin_model) if f.result.value == "pass"}
    assert f"duct DU-S-HP-BED{n} start lands on DU-S-HP-SUP" in findings
    assert len(leg.path) == 2
    assert leg.z_m[0] == pytest.approx(leg.z_m[1])
    assert leg.path[0][1] == pytest.approx(leg.path[1][1])
    assert at[1] == pytest.approx(end[1])
    assert register.location.attachment.wall_ref == f"W-S-BW{n}"


def test_bed3_straight_branch_clears_framing_and_keeps_return_grille_in_plenum(
    catlin_model_ro,
):
    """The soffit check clips at its end, so explicitly measure this tight corner too."""
    from shapely.geometry import Polygon, box

    from typehaus.quantities import inch
    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.resolve.mep_bore_geometry import member_plan_shape
    from typehaus.resolve.mep_soffit import HANGER_GAP_M

    model = catlin_model_ro
    assert not any(d.tag == "DU-S-HP-BED3-RISE" for d in model.ducts)
    branch = next(d for d in model.ducts if d.tag == "DU-S-HP-BED3")
    half_diameter = branch.diameter_m / 2
    branch_body = box(branch.path[0][0], branch.path[0][1] - half_diameter,
                      branch.path[1][0], branch.path[1][1] + half_diameter)
    plenum = next(o for o in model.canvas_objects if o.tag == "EQ-S-ERV-MIX")
    assert branch_body.distance(Polygon(plenum.footprint)) >= HANGER_GAP_M - 1e-9
    structural_shapes = []
    for wall in model.walls:
        if wall.tag not in ("W-S-BD2", "W-S-BW3"):
            continue
        for member in wall.members:
            if member.category == "strapping":
                continue  # The collar's local resilient-channel cut is a field detail.
            if (member.z0_m >= branch.z_m[0] + half_diameter
                    or member.z1_m <= branch.z_m[0] - half_diameter):
                continue
            shape = member_plan_shape(member, cross_section(member.profile))
            if shape is not None:
                structural_shapes.append(shape)
    assert structural_shapes
    assert min(branch_body.distance(shape) for shape in structural_shapes) >= inch(.5).meters - 1e-9
    return_grille = next(o for o in model.canvas_objects if o.tag == "REG-S-HP-RET")
    assert Polygon(plenum.footprint).buffer(1e-9).covers(Polygon(return_grille.footprint))


def test_study_sidewall_boot_connects_and_clears_soffit_framing(catlin_plan, catlin_model_ro):
    from shapely.geometry import LineString, Point, Polygon, box

    from typehaus.quantities import inch
    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.resolve.mep_bore_geometry import member_plan_shape

    model = catlin_model_ro
    register = next(e for e in catlin_plan.all_elements() if e.tag == "REG-S-HP-STUDY2")
    grille = next(o for o in model.canvas_objects if o.tag == register.tag)
    branch = next(d for d in model.ducts if d.tag == register.duct_ref)
    riser = next(d for d in model.ducts if d.tag == "DU-S-HP-SOUTH-RISE")
    bay = next(d for d in model.ducts if d.tag == "DU-S-HP-SOUTH")
    soffit = next(s for s in model.soffits if s.tag == "SF-S-DUCT")
    room = next(r for r in model.rooms if r.tag == register.room)
    assert register.mount.kind.value == "wall"
    assert register.design_cfm == 75
    assert branch.design_cfm == 75
    assert bay.design_cfm == 175
    assert riser.design_cfm == branch.design_cfm + bay.design_cfm
    assert branch.diameter_m == pytest.approx(inch(6).meters)
    assert branch.path[-1] == pytest.approx(grille.position)
    assert branch.z_m[0] == pytest.approx(riser.z_m[0])
    assert branch.z_m[0] == pytest.approx(grille.z_m + inch(3).meters)
    assert LineString(riser.path[:2]).distance(Point(branch.path[0])) < 1e-9
    assert bay.path[0] == pytest.approx(riser.path[-1])
    attic_boot = next(o for o in model.canvas_objects if o.tag == "REG-A-HP-STUDY")
    assert LineString(bay.path).distance(Point(attic_boot.position)) < 1e-9
    assert Polygon(room.clear_face).covers(Polygon(grille.footprint))
    assert bay.length_m == pytest.approx(inch(90).meters)
    assert not bay.conflicts

    half_diameter = branch.diameter_m / 2
    boot_body = box(branch.path[0][0], branch.path[0][1] - half_diameter,
                    branch.path[-1][0], branch.path[-1][1] + half_diameter)
    for member in soffit.members:
        if (member.z0_m >= branch.z_m[0] + half_diameter
                or member.z1_m <= branch.z_m[0] - half_diameter):
            continue
        shape = member_plan_shape(member, cross_section(member.profile))
        assert shape is not None
        assert not boot_body.intersects(shape), member.child_key
        assert not Polygon(grille.footprint).intersects(shape), member.child_key
    findings = _connectivity(model)
    assert not [f.message for f in findings if f.result.value == "fail"]
    assert any(f.message == "duct DU-S-HP-STUDY2 start lands on DU-S-HP-SOUTH-RISE"
               for f in findings)
