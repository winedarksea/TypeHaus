"""MEP plumbing — sleeves, drain runs, checks (→ Permit-ready plan set Phase 2)."""

from __future__ import annotations

import copy
import dataclasses

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier


def test_expected_drain_point_is_the_authored_outlet_when_there_is_one(catlin_model):
    """A fixture whose waste does not drop under its own footprint authors
    ``drain_position``, and that override — not the fixture's footprint center — is what the
    sleeve must sit under. The kitchen sink's drain leaves at the wall behind the cabinet.

    (This used to read SP-M-WC1, BATH1's wall-hung carrier. That sleeve went with the
    2026-08-21 deck overhaul: the main floor over BATH1 is I-joists now and a joist bay is
    bored on the day, not cast before a pour. SP-M-KITCH is in the surviving concrete band
    and makes the identical point.)"""
    sleeve = next(s for s in catlin_model.sleeves if s.tag == "SP-M-KITCH")
    fixture = catlin_model.plan.by_tag("FX-M-KITCH-SINK")
    assert fixture.drain_position is not None
    assert sleeve.expected_center == fixture.drain_position.xy_m
    assert sleeve.expected_center != fixture.position.xy_m


def test_floor_wc_drains_under_its_own_bowl(catlin_model):
    """A floor-mounted WC puts the closet flange under the bowl, so the convention needs no
    override and the sleeve sits on the fixture's own position. RM-B-BATH's WC is the one
    left on a slab since the 2026-08-21 deck overhaul took the main floor's cast sleeves
    away (it used to be SP-M-WC2 in BATH2)."""
    sleeve = next(s for s in catlin_model.sleeves if s.tag == "SP-B-BATH-WC")
    fixture = catlin_model.plan.by_tag("FX-B-BATH-WC")
    assert fixture.drain_position is None
    assert sleeve.expected_center == fixture.position.xy_m
    assert sleeve.offset_m == pytest.approx(0.0, abs=1e-9)


def test_catlin_sleeve_expectation_sources_agree(catlin_model):
    """On this house the three expectation sources are not in conflict, and that is the
    point: SP-M-KITCH's authored outlet, the vertex of the run serving it, and the
    sleeve's own position are one point. Precedence only ever decides a disagreement, so if
    this test starts needing it, something drifted."""
    from typehaus.resolve.mep import _pipe_expected_point

    sleeve = next(el for el in catlin_model.plan.all_elements()
                  if el.element_kind == "SleevePenetration" and el.tag == "SP-M-KITCH")
    fixture = catlin_model.plan.by_tag("FX-M-KITCH-SINK")
    assert _pipe_expected_point(catlin_model, sleeve) == fixture.drain_position.xy_m


def test_authored_drain_position_outranks_the_routed_run():
    """The precedence in `_expected_sleeve_point`, pinned on a deliberate disagreement:
    authored `drain_position` beats a routed vertex, which beats the fixture convention.

    Order matters in the direction that surfaces defects. If a routed run could override the
    override, a stale `drain_position` would be silently ignored instead of failing
    `mep.sleeve_alignment` — which is exactly how SP-M-WC2's old position hid. So re-routing
    a run away from an authored flange must move the *expectation* nowhere; the sleeve stays
    where the human put it and the check reports the gap.
    """
    from types import SimpleNamespace

    from typehaus.model.enums import Service
    from typehaus.model.mep import SleevePenetration
    from typehaus.model.spatial import Fixture
    from typehaus.quantities import inch, m, pt
    from typehaus.resolve.mep import _expected_sleeve_point
    from typehaus.resolve.model import ResolvedPipeRun

    flange = pt(m(1.0), m(1.0))          # what the plan says
    routed = (m(4.0).meters, m(4.0).meters)  # where the run actually goes — 3m away
    sleeve = SleevePenetration(
        uid="TESTSLV001", tag="SP-T", host_ref="SL-T", position=flange,
        pipe_diameter=inch(3), sleeve_diameter=inch(4), serves_fixture="FX-T")
    assert sleeve.purpose == Service.DRAIN
    run = ResolvedPipeRun(
        uid="TESTRUN001", tag="PR-T", storey="main", system="drain",
        path=(routed, (routed[0], routed[1] + 1.0)), diameter_m=inch(3).meters,
        z_start_m=0.0, z_end_m=0.0, length_m=1.0, serves=("FX-T",))

    fixture = Fixture(uid="TESTFIX001", tag="FX-T", type_ref="FX-TOILET-STD",
                      position=pt(m(1.2), m(1.2)), drain_position=flange)
    held = {"fixture": fixture}
    model = SimpleNamespace(plan=SimpleNamespace(by_tag=lambda tag: held["fixture"]),
                            pipe_runs=[run])

    # The routed vertex is inside the snap radius of nothing here — it is 3m off — but the
    # authored point answers regardless of how near or far the run is.
    with_override = _expected_sleeve_point(model, sleeve)
    assert with_override == flange.xy_m

    # Drop the override and the run's own vertex becomes the expectation.
    held["fixture"] = fixture.model_copy(update={"drain_position": None})
    near = pt(m(1.05), m(1.0))  # a vertex within the 0.3m snap of the sleeve center
    model.pipe_runs = [ResolvedPipeRun(
        uid="TESTRUN002", tag="PR-T2", storey="main", system="drain",
        path=(near.xy_m, routed), diameter_m=inch(3).meters,
        z_start_m=0.0, z_end_m=0.0, length_m=1.0, serves=("FX-T",))]
    assert _expected_sleeve_point(model, sleeve) == near.xy_m


def test_lav_expected_drain_point_projects_onto_wet_wall(catlin_model):
    """A hot-water fixture with no authored override drains back to its wet wall, so the
    expectation is its footprint centre *projected onto that wall's axis*.

    Built from the real house's own library rather than read off a sleeve: catlin has no
    unoverridden lavatory left over concrete since the 2026-08-21 deck overhaul framed the
    main floor (it was SP-M-LAV1 in BATH1), and RM-B-BATH's lav authors a
    ``drain_position``, which by decision 4 short-circuits the projection this measures."""
    from typehaus.model.spatial import Fixture
    from typehaus.quantities import ft, pt
    from typehaus.resolve.mep import _expected_drain_point

    lav = catlin_model.plan.by_tag("FX-B-BATH-LAV")
    wall = catlin_model.wall("W-B-BA-N")  # runs in x, so the projection fixes y
    stand_off = Fixture(uid="FXTESTLAV1", tag="FX-T-LAV", type_ref=lav.type_ref,
                        room=lav.room, position=pt(ft(15), ft(19)),
                        wall_ref="W-B-BA-N")
    class _Plan:
        library = catlin_model.plan.library

        def by_tag(self, tag):
            return stand_off if tag == stand_off.tag else catlin_model.plan.by_tag(tag)

    model = copy.copy(catlin_model)
    model.plan = _Plan()

    point = _expected_drain_point(model, stand_off.tag)
    assert point is not None
    assert point[0] == pytest.approx(ft(15).meters, abs=1e-6)
    assert point[1] == pytest.approx(wall.axis[0][1], abs=1e-6)


def test_drain_position_override_wins():
    from typehaus.model.spatial import Fixture
    from typehaus.quantities import ft, pt
    from typehaus.resolve.mep import _expected_drain_point

    fixture = Fixture(uid="FX1", tag="FX-OVR", type_ref="FX-LAV", room="RM-1",
                      position=pt(ft(3), ft(3)), wall_ref="W-1",
                      drain_position=pt(ft(99), ft(99)))

    class _Library:
        fixture_types = ()

    class _Plan:
        library = _Library()

        def by_tag(self, tag):
            return fixture if tag == fixture.tag else None

    class _Model:
        plan = _Plan()

    point = _expected_drain_point(_Model(), fixture.tag)
    assert point == (ft(99).meters, ft(99).meters)


def test_sleeve_alignment_fails_at_one_inch_offset(catlin_model):
    model = copy.copy(catlin_model)
    model.sleeves = [
        dataclasses.replace(s, center=(s.center[0] + 0.0254, s.center[1]),
                            offset_m=0.0254)
        if s.tag == "SP-M-KITCH" else s
        for s in catlin_model.sleeves
    ]
    report = run_from_model(model, [], tier=Tier.CODE)
    fails = [f for f in report.findings
             if f.check_id == "mep.sleeve_alignment" and "SP-M-KITCH" in f.element_tags
             and f.result.value == "fail"]
    assert fails, [f.message for f in report.findings if f.check_id == "mep.sleeve_alignment"]


def test_sleeve_rejected_when_inside_floor_opening():
    from typehaus.model.mep import SleevePenetration
    from typehaus.quantities import ft, inch, pt
    from typehaus.resolve.model import ResolvedModel, ResolvedSolid
    from typehaus.resolve.mep import resolve_mep

    class _FakeOpening:
        outline = (pt(ft(0), ft(0)), pt(ft(2), ft(0)), pt(ft(2), ft(2)), pt(ft(0), ft(2)))

    class _FakeSlab:
        tag = "SL-TEST"
        openings = ("FO-TEST",)

    sleeve = SleevePenetration(uid="X", tag="SP-BAD", host_ref="SL-TEST",
                               position=pt(ft(1), ft(1)), pipe_diameter=inch(3),
                               sleeve_diameter=inch(4))

    class _FakePlan:
        storeys: list = []

        def storey_elements(self, tag):
            return [sleeve]

        def by_tag(self, tag):
            return {"SL-TEST": _FakeSlab(), "FO-TEST": _FakeOpening()}.get(tag)

    class _FakeStorey:
        tag = "main"

    _FakePlan.storeys = [_FakeStorey()]
    model = ResolvedModel(plan=_FakePlan())
    model.solids.append(ResolvedSolid(
        uid="S1", tag="SL-TEST", storey="main", category="slab",
        outline=[(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)], z0_m=-0.2, z1_m=0.0,
    ))
    findings = resolve_mep(model)
    assert any(f.check_id == "integrity.sleeve_in_opening" for f in findings)


def test_drain_slope_pass_for_catlin_main_run(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == "mep.drain_slope"]
    assert matched and all(f.result.value == "pass" for f in matched)


def test_drain_slope_unknown_without_inverts():
    from typehaus.model.enums import PipeSystem
    from typehaus.model.mep import PipeRun
    from typehaus.quantities import ft, inch, pt
    from typehaus.resolve.model import ResolvedModel
    from typehaus.resolve.mep import resolve_mep

    run = PipeRun(uid="X", tag="PR-TEST", system=PipeSystem.DRAIN,
                 path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))), diameter=inch(3))

    class _FakePlan:
        storeys: list = []

        def storey_elements(self, tag):
            return [run]

        def by_tag(self, tag):
            return None

    class _FakeStorey:
        tag = "basement"
        elevation = ft(-9)

    _FakePlan.storeys = [_FakeStorey()]
    model = ResolvedModel(plan=_FakePlan())
    resolve_mep(model)
    assert model.pipe_runs[0].z_start_m is None
    assert model.pipe_runs[0].z_end_m is None


def _vent_termination_context(authored_termination):
    """A one-roof, one-vent context for the termination check.

    Gable, ridge along y, eave 3 m, ridge 5 m over a 10x10 footprint: the riser at x=2 m
    sits 40% of the way up the rake, so the roof plane there is 3.8 m and the derived
    termination 12" above it.
    """
    from typehaus.checks.registry import CheckContext, JurisdictionProfile, Preferences
    from typehaus.model.enums import PipeSystem
    from typehaus.model.mep import VentRun
    from typehaus.quantities import inch, m, pt
    from typehaus.resolve.model import ResolvedModel, ResolvedRoof

    vent = VentRun(uid="V1", tag="VR-TEST", systems=(PipeSystem.VENT,), diameter=inch(3),
                   chase_position=pt(m(2), m(2)), start_elevation=m(0), exit_elevation=m(3),
                   exit_offset=pt(m(0), m(1)),
                   roof_termination_elevation=authored_termination)

    class _FakePlan:
        storeys: list = []

        def storey_elements(self, tag):
            return [vent]

        def by_tag(self, tag):
            return vent if tag == vent.tag else None

    class _FakeStorey:
        tag = "attic"

    _FakePlan.storeys = [_FakeStorey()]
    plan = _FakePlan()
    model = ResolvedModel(plan=plan)
    model.roofs.append(ResolvedRoof(
        uid="R1", tag="RF-TEST", storey="attic", form="gable",
        footprint=[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)],
        eave_z_m=3.0, ridge_z_m=5.0, ridge_direction="y", assembly="A",
        surface_area_m2=100.0,
    ))
    return CheckContext(plan=plan, model=model, preferences=Preferences(),
                        profile=JurisdictionProfile(name="t", edition="t", effective_date="t",
                                                     irc_base="t", coverage_statement="t"))


def test_vent_termination_height_flags_an_authored_elevation_above_the_roof():
    from typehaus.checks.mep.plumbing import vent_termination_height
    from typehaus.quantities import m

    findings = vent_termination_height(_vent_termination_context(m(5.5)))
    assert [f.result.value for f in findings] == ["fail"]
    assert "1.4" in findings[0].message or "too high" in findings[0].message
    # Advisory findings never block the permit gate (see plumbing_common._advisory_fail).
    assert findings[0].severity.value == "warn"


def test_vent_termination_height_passes_an_authored_elevation_that_matches():
    from typehaus.checks.mep.plumbing import vent_termination_height
    from typehaus.quantities import inch, m

    matching = m(3.8 + inch(12).meters)
    findings = vent_termination_height(_vent_termination_context(matching))
    assert [f.result.value for f in findings] == ["pass"]


def test_vent_termination_height_passes_when_the_elevation_is_left_derived():
    from typehaus.checks.mep.plumbing import vent_termination_height

    findings = vent_termination_height(_vent_termination_context(None))
    assert [f.result.value for f in findings] == ["pass"]


def test_catlin_vent_termination_height_passes(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    matched = [f for f in report.findings if f.check_id == "mep.vent_termination_height"]
    assert matched and all(f.result.value == "pass" for f in matched)


def test_catlin_sleeve_alignment_is_clean(catlin_model):
    """The whole check, not just the offsets: ``mep.sleeve_alignment`` also fails a drain
    fixture standing over a structural slab with nothing serving it, which is how the
    basement utility sink surfaced."""
    report = run_from_model(catlin_model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == "mep.sleeve_alignment"]
    assert matched
    assert all(f.result.value == "pass" for f in matched), \
        [f.message for f in matched if f.result.value != "pass"]


def test_basement_slab_fixtures_drain_through_their_own_slab_stub_ups(catlin_model):
    """A fixture on a slab-on-grade has no wall drain stack — its trap arm runs under the
    slab — so the penetration is authored where the trap actually drops, not projected onto
    a wall centerline the way a wall-drained lavatory is.

    Written against FX-1, the mechanical room's utility sink, which was the only such fixture
    in the house until 2026-07-30. It is gone now: the stair-foot bathroom and the sauna's
    shower end took the basement from one slab fixture to four, and each of them owns a stub.
    """
    slab_fixtures = ("FX-B-BATH-WC", "FX-B-BATH-LAV", "FX-B-SAUNA-SH", "FX-B-SAUNA-FD")
    for tag in slab_fixtures:
        sleeve = next(s for s in catlin_model.sleeves if s.serves_fixture == tag)
        fixture = catlin_model.plan.by_tag(tag)
        assert sleeve.host_slab == "SL-B-FLOOR", tag
        # The convention only needs an authored `drain_position` where the trap is not under
        # the fixture: a closet flange, a shower pan's outlet and a floor drain's body all are.
        expected = (fixture.drain_position or fixture.position).xy_m
        assert sleeve.expected_center == expected, tag
        assert sleeve.offset_m == pytest.approx(0.0, abs=1e-9), tag


def test_catlin_wet_wall_depth_has_no_findings(catlin_model):
    """``advisory.wet_wall_depth`` reports only problems, so silence is the pass. It fires
    on a drain fixture with no ``wall_ref`` at all, which is what FX-1 used to be.

    Note what this does *not* assert: that 5 1/2" is a code minimum. It is not — the number is
    ``preferences.toml``'s own planning allowance and the check is ADVISORY tier, in no item of
    the mn-2024 permit profile. This test holds the house to its own preference, nothing more.
    """
    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    matched = [f for f in report.findings if f.check_id == "advisory.wet_wall_depth"]
    assert not matched, [f.message for f in matched]


def test_bath1_fixtures_sit_inside_the_room_and_clear_of_each_other(catlin_model):
    """RM-M-BATH1 is packed wall-to-wall, so both footprints have to be inside the room's
    clear face and disjoint from each other. The lavatory used to protrude through W-M-BAE
    into the hall, which is what D-M-BATH1's swing was colliding with."""
    from shapely.geometry import Polygon

    room = Polygon(next(r for r in catlin_model.rooms if r.tag == "RM-M-BATH1").clear_face)
    footprints = {obj.tag: Polygon(obj.footprint) for obj in catlin_model.canvas_objects
                  if obj.room == "RM-M-BATH1"}
    assert {"FX-M-BATH1-WC", "FX-M-BATH1-LAV"} <= set(footprints)
    for tag, footprint in footprints.items():
        assert room.covers(footprint), f"{tag} escapes RM-M-BATH1"
    overlap = footprints["FX-M-BATH1-WC"].intersection(footprints["FX-M-BATH1-LAV"])
    assert overlap.area <= 1e-9, f"{overlap.area * 10.7639:.2f} ft2 of fixture overlap"


def test_laundry_goods_fit_the_alcove_and_clear_each_other(catlin_model):
    """RM-M-LAUNDRY is 62 3/4" x 56 3/4" of clear floor holding 28" of stacked washer/dryer
    plus a 24" utility tub, so there is no slack to lose. Both bodies have to stay inside the
    room and off each other, and the fold-down rack has to hang over the tub without the two
    ever meeting — it clears vertically (48" mount over a 43" fixture), not in plan."""
    from shapely.geometry import Polygon

    room = Polygon(next(r for r in catlin_model.rooms if r.tag == "RM-M-LAUNDRY").clear_face)
    objects = {obj.tag: obj for obj in catlin_model.canvas_objects
               if obj.room == "RM-M-LAUNDRY"}
    assert {"FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK", "FURN-M-LAUNDRY-RACK"} <= set(objects)
    for tag, obj in objects.items():
        mount = obj.mount
        if mount is not None and mount.recessed_into_host_surface and mount.kind.value == "wall":
            continue  # ED-M-LAUNDRY-RC1/DR1 are boxes let *into* the partition — their body
            # belongs behind the finish plane, which is the whole point of the recessed flag,
            # and the machine sits flat against the wall because of it.
        # By area, not `covers`: every one of these backs sits *on* the south finish face by
        # design, so boundary-touching is the intended result and float noise at 1e-15 would
        # make a containment predicate report it as an escape.
        assert Polygon(obj.footprint).difference(room).area <= 1e-9, \
            f"{tag} escapes RM-M-LAUNDRY"
    overlap = Polygon(objects["FX-M-LAUNDRY"].footprint).intersection(
        Polygon(objects["FX-M-LAUNDRY-SINK"].footprint))
    assert overlap.area <= 1e-9, f"{overlap.area * 10.7639:.2f} ft2 of laundry overlap"
    # The rack is the one pair that *does* overlap in plan, and must, since it hangs over the
    # tub. It is a shelf rather than a collision only because it starts above the tub's box.
    tub_height = next(t.height.meters for t in catlin_model.plan.library.fixture_types
                      if t.tag == "FX-LAUNDRY-SINK-24")
    assert objects["FURN-M-LAUNDRY-RACK"].z_m >= objects["FX-M-LAUNDRY-SINK"].z_m + tub_height


def test_laundry_tub_drain_clears_the_centre_cross_wall(catlin_model):
    """FX-M-LAUNDRY-SINK's body straddles y=18', where W-B-CW2's 12" of cast concrete runs
    from the basement up to the deck. Its waste therefore drops at the front of the basin,
    not under its centre — drop it at the fixture's own position and it lands on the wall."""
    fixture = next(f for f in catlin_model.plan.all_elements()
                   if getattr(f, "tag", None) == "FX-M-LAUNDRY-SINK")
    assert fixture.drain_position is not None, "the override is the whole point"
    _, drain_y = fixture.drain_position.xy_m
    wall_north_face = next(w for w in catlin_model.walls if w.tag == "W-B-CW2")
    assert wall_north_face.axis[0][1] == pytest.approx(18 * 0.3048)
    # 12" wall on the y=18' axis -> north face at 18'-6". The drop must clear it and still
    # land inside the tub, whose north edge is at 19'-1 1/8".
    assert 18.5 * 0.3048 < drain_y < (19 + 1.125 / 12) * 0.3048


def test_catlin_door_swings_are_clear_of_fixtures(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.INTEGRITY)
    matched = [f for f in report.findings if f.check_id == "integrity.door_swing_conflict"]
    assert not matched, [f.message for f in matched]


# Every fixture in the house vents, and this test exists to keep it that way.
#
# It used to carry an UNVENTED_FIXTURES dict of eight declared exceptions. They surfaced
# together when the library dedupe retagged catlin's house-local fixture types onto the
# shared ones: the house-local FX-LAV / FX-SHOWER / FX-TUB / FX-TUBSHOWER omitted
# Service.VENT from `needs` while the shared FX-LAV-24 / FX-SHOWER-36 / FX-TUB-60 /
# FX-TUBSHOWER-60 state it — correctly, because a fixture that drains is vented. So the
# house's vent design (water closets only) had been authored against a claim its own fixture
# types quietly did not make: those eight were never *passing*, they were never checked.
#
# The plumbing pass closed all eight. Seven got real vent runs on 2026-07-29 (the main-bath-2
# fixtures tie into PR-M-WC-VENT rather than needing W-M-BA2E to continue past its ceiling).
# FX-1 was last, on 2026-07-30: it could not be vented while it had no drain, and it could
# not drain until the building main went under the slab — see PR-B-UTIL-VENT, the basement's
# only vent branch. A ninth fixture, FX-M-BATH1-LAV, joined the check that same day when
# FX-LAV-COMPACT was given the Service.VENT it had always been missing.
def test_catlin_fixtures_all_reach_a_vent_chase(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    matched = [f for f in report.findings if f.check_id == "mep.vent_reachability"]
    assert matched
    unvented = [(f.message) for f in matched if f.result.value != "pass"]
    assert not unvented, unvented
    # The two whose wet wall stops at its own ceiling must say so, not silently pass.
    # (FX-S-BATH1-WC used to be the third: since the ensuite de-overlap pass it backs
    # onto the exterior W-S-W1, which continues up, so it vents in-wall.)
    offset_vented = [f for f in matched if "chase" in f.message]
    assert {"FX-M-BATH1-WC", "FX-M-BATH2-WC"} <= {
        tag for f in offset_vented for tag in f.element_tags
    }


def test_authored_vent_branches_carry_their_fixtures_into_the_ir(catlin_model):
    """``PipeRun.serves`` is what links a vent branch to the fixture it vents; dropping it
    in the resolver would make every offset vent invisible to the check."""
    runs = {run.tag: run for run in catlin_model.pipe_runs if run.system == "vent"}
    assert "FX-M-BATH1-WC" in runs["PR-M-WC-VENT"].serves
    assert "FX-M-BATH2-WC" in runs["PR-M-WC-VENT"].serves
    # The hall-bath branch vents the whole group, not just the water closet: the plumbing
    # pass added the lavatories and the tub-shower whose trap arms tie into the same leg.
    assert runs["PR-S-BATH1-VENT"].serves == (
        "FX-S-BATH1-WC", "FX-S-BATH1-LAV", "FX-S-BATH1-SH",
        "FX-S-VANITY-LAV1", "FX-S-VANITY-LAV2")


def _vent_path_model(run_path, wall_axis, chase_xy, systems=None):
    """One fixture, one wet wall, one riser chase, one authored vent run."""
    from typehaus.model.enums import PipeSystem
    from typehaus.model.mep import VentRun
    from typehaus.quantities import inch, m, pt
    from typehaus.resolve.model import ResolvedModel, ResolvedPipeRun, ResolvedWall

    vent = VentRun(uid="V1", tag="VR-TEST",
                   systems=systems if systems is not None else (PipeSystem.VENT,),
                   diameter=inch(3), chase_position=pt(m(chase_xy[0]), m(chase_xy[1])),
                   start_elevation=m(0), exit_elevation=m(3), exit_offset=pt(m(0), m(1)))

    class _FakePlan:
        def all_elements(self):
            return [vent]

    model = ResolvedModel(plan=_FakePlan())
    model.pipe_runs.append(ResolvedPipeRun(
        uid="P1", tag="PR-TEST", storey="main", system="vent", path=list(run_path),
        diameter_m=inch(2).meters, z_start_m=None, z_end_m=None, length_m=1.0,
        serves=("FX-TEST-WC",),
    ))
    wall = ResolvedWall(uid="W1", tag="W-TEST", storey="main", assembly="A", axis=wall_axis,
                        layers=(), z0_m=0.0, z1_m=2.7)
    return model, wall


def test_vent_path_accepts_a_run_from_the_wet_wall_to_the_chase():
    from typehaus.checks.mep.vent_path import evaluate_vent_path

    model, wall = _vent_path_model(
        run_path=[(0.0, 0.0), (0.0, 4.0), (2.0, 4.0)],
        wall_axis=((0.0, -1.0), (0.0, 1.0)), chase_xy=(2.0, 4.0),
    )
    path = evaluate_vent_path(model, "FX-TEST-WC", wall)
    assert path.is_connected and path.chase_tag == "VR-TEST"


def test_vent_path_rejects_a_run_that_never_reaches_a_chase():
    from typehaus.checks.mep.vent_path import evaluate_vent_path

    model, wall = _vent_path_model(
        run_path=[(0.0, 0.0), (0.0, 4.0)],
        wall_axis=((0.0, -1.0), (0.0, 1.0)), chase_xy=(9.0, 9.0),
    )
    path = evaluate_vent_path(model, "FX-TEST-WC", wall)
    assert not path.is_connected and path.chase_tag is None


def test_vent_path_rejects_a_run_that_never_touches_the_wet_wall():
    from typehaus.checks.mep.vent_path import evaluate_vent_path

    model, wall = _vent_path_model(
        run_path=[(5.0, 0.0), (5.0, 4.0), (2.0, 4.0)],
        wall_axis=((0.0, -1.0), (0.0, 1.0)), chase_xy=(2.0, 4.0),
    )
    path = evaluate_vent_path(model, "FX-TEST-WC", wall)
    assert not path.is_connected and not path.touches_wet_wall


def test_vent_path_rejects_a_radon_only_riser():
    """A passive soil-gas stack is not a plumbing vent; tying a trap arm into one would
    push sewer gas at the radon fan, so only a riser carrying VENT counts."""
    from typehaus.checks.mep.vent_path import evaluate_vent_path
    from typehaus.model.enums import PipeSystem

    model, wall = _vent_path_model(
        run_path=[(0.0, 0.0), (0.0, 4.0), (2.0, 4.0)],
        wall_axis=((0.0, -1.0), (0.0, 1.0)), chase_xy=(2.0, 4.0),
        systems=(PipeSystem.RADON,),
    )
    assert evaluate_vent_path(model, "FX-TEST-WC", wall).chase_tag is None


def test_vent_reachability_fails_a_water_closet_with_no_vent_path(catlin_model):
    """Deleting the authored branch has to bring the failure back — the check must not be
    passing these fixtures on the wet wall alone."""
    import copy

    model = copy.copy(catlin_model)
    model.pipe_runs = [run for run in catlin_model.pipe_runs if run.tag != "PR-M-WC-VENT"]
    report = run_from_model(model, [], tier=Tier.ADVISORY)
    failed = {tag for f in report.findings if f.check_id == "mep.vent_reachability"
              and f.result.value == "fail" for tag in f.element_tags}
    assert {"FX-M-BATH1-WC", "FX-M-BATH2-WC"} <= failed


def test_missing_sleeve_over_slab_fails():
    from typehaus.checks.mep.plumbing import _missing_sleeve_findings
    from typehaus.checks.registry import CheckContext, JurisdictionProfile, Preferences
    from typehaus.model.enums import Service
    from typehaus.model.types import FixtureType
    from typehaus.quantities import ft, pt
    from typehaus.resolve.model import ResolvedModel, ResolvedSolid

    class _FakeFixture:
        element_kind = "Fixture"
        tag = "FX-TEST-WC"
        type_ref = "FX-TOILET"
        position = pt(ft(1), ft(1))

    class _Library:
        fixture_types = (FixtureType(tag="FX-TOILET", name="WC", footprint=(ft(2), ft(2)),
                                      height=ft(2), needs=frozenset({Service.DRAIN})),)

    class _FakePlan:
        library = _Library()
        storeys: list = []

        def storey_elements(self, tag):
            return [_FakeFixture()]

    class _FakeStorey:
        tag = "main"

    _FakePlan.storeys = [_FakeStorey()]
    model = ResolvedModel(plan=_FakePlan())
    model.solids.append(ResolvedSolid(
        uid="S1", tag="SL-TEST", storey="main", category="slab",
        outline=[(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)], z0_m=-0.2, z1_m=0.0,
    ))
    ctx = CheckContext(plan=_FakePlan(), model=model, preferences=Preferences(),
                       profile=JurisdictionProfile(name="t", edition="t", effective_date="t",
                                                    irc_base="t", coverage_statement="t"))
    findings = _missing_sleeve_findings(ctx)
    assert findings and findings[0].result.value == "fail"
