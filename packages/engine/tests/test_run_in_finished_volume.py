"""``mep.run_in_finished_volume`` — a run hanging in a room somebody lives in.

``run_route_efficiency`` used to say the model had no per-room ceiling plane and so could
not ask this. It has had one since the ceiling work; this is the check that asks. Catlin's
basement service corridor was real, and all eleven findings were closed on 2026-09-09 by
reroutes, walls and one soffit. Two of those soffits were retired again on 2026-09-13 for
``Room.exposed_services`` declarations on ``RM-B-GYM`` and ``RM-B-STAIR``. The house passes.

What these tests pin is the machinery, because that is what had to survive the fix and is
what would rot now that nothing exercises it in anger: the band's lower edge, the
three-dimensional clip, the grace rule, and the sloped attic ceilings. Each of the
three defect tests below puts a real, fixed defect back on a mutable model rather than
leaning on the reference house still being wrong.
"""

from __future__ import annotations

import dataclasses

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier, registered
from typehaus.findings import Result
from typehaus.model.enums import EXPOSED_SERVICE_OCCUPANCIES, Occupancy


@pytest.fixture(scope="module")
def findings(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY,
                            only="mep.run_in_finished_volume")
    return [f for f in report.findings if f.check_id == "mep.run_in_finished_volume"]


def test_the_check_is_actually_registered() -> None:
    """**The trap.** ``routing_ceiling.py`` has to be named in ``checks/mep/__init__.py``.
    A module nothing imports registers nothing and emits nothing, which is
    indistinguishable from finding nothing."""
    assert "mep.run_in_finished_volume" in {cid for cid, _ in registered(Tier.ADVISORY)}


def test_the_attic_is_graded_against_the_roof_underside(findings, catlin_model) -> None:
    """``Room.ceiling=FollowRoof`` rooms are graded against the roof's underside less the
    lining, not skipped: nothing is reported as ungraded for want of a flat plane.

    Two regressions are put back on a mutable model. A vent crossing the bath at 3'-5" (the
    run ``PR-A-STUBATH-VENT`` was until 2026-10-29) hangs in the room's air. The same pipe
    on the floor of the west eave, under a rake lower than R304.3's 5'-0", is not graded but
    is NAMED: with no knee wall that eave is still finished room. The studio declares its
    eave services exposed (owner, 2026-10-29), so its PASS names the run; without the
    declaration it is an UNKNOWN."""
    from typehaus.model import ft, inch

    assert not [f for f in findings if f.result is Result.UNKNOWN
                and "FollowRoof" in f.message], [f.message for f in findings]

    original = next(r for r in catlin_model.pipe_runs if r.tag == "PR-A-STUBATH-VENT")

    def _with(path, z):
        moved = dataclasses.replace(original, path=path, z_m=z)
        return dataclasses.replace(
            catlin_model, pipe_runs=tuple(moved if r.tag == original.tag else r
                                          for r in catlin_model.pipe_runs))

    across = tuple((inch(x).meters, ft(19, 0).meters) for x in (180, 150, 120))
    z = (ft(23, 5).meters,) * 3
    fails = _fails_for(_with(across, z), "PR-A-STUBATH-VENT")
    assert [f.element_tags[1] for f in fails] == ["RM-A-STUBATH"], [f.message for f in fails]
    assert float(fails[0].message.split("hangs ")[1].split('"')[0]) > 40

    eave = tuple((inch(x).meters, ft(19, 0).meters) for x in (30, 24, 18))
    low = (ft(20, 1).meters,) * 3
    in_eave = _with(eave, low)
    assert not _fails_for(in_eave, "PR-A-STUBATH-VENT")

    def _report(model):
        return run_from_model(model, [], tier=Tier.ADVISORY,
                              only="mep.run_in_finished_volume").findings

    declared = [f for f in _report(in_eave) if f.result is Result.PASS
                and f.message.startswith("RM-A-STUDIO: services are deliberately exposed")]
    assert declared and "PR-A-STUBATH-VENT" in declared[0].message.split("in its eave")[1]
    undeclared = dataclasses.replace(in_eave, rooms=[
        dataclasses.replace(r, exposed_services=None) if r.tag == "RM-A-STUDIO" else r
        for r in in_eave.rooms])
    named = [f for f in _report(undeclared)
             if f.result is Result.UNKNOWN and "eave" in f.message]
    assert named and "PR-A-STUBATH-VENT in RM-A-STUDIO" in named[0].message


def test_the_work_list_is_clear(findings) -> None:
    """**The work list is empty, and this test is the record of what emptied it.**

    Every one of the eleven is named because a silent regression here is a run back in
    somebody's living room, and because the three answers the check's own hint gives are
    each represented.

    REROUTED OUT OF THE ROOM: ``PR-M-COND-HEADS`` into ``RM-B-SAUNA``'s service void (that
    ceiling is 14" lower than the storey's), ``PR-B-COND``'s trunk, and ``PR-B-HW-KITCH``,
    which steps north and up 1 3/16" to cross ``RM-B-STAIR`` and back down in the gym where
    the ceiling is lower. ``CD-B-KITCHEN`` and ``CD-B-DATA-MEDIA`` came up 2" to -1'-4",
    where they sit 1 9/16" under ``SL-M-DECK``'s board — which is what
    ``plan/electrical.py``'s own prose had claimed all along while the authored elevation
    said otherwise.

    TAKEN INTO A WALL: ``PR-B-CW-BATH2`` into ``W-M-HS1``, ``PR-B-CW-SUITE`` and
    ``PR-B-HW-SUITE`` into ``W-S-SN3`` (via ``FS-S-WEST``'s truss webs), and
    ``PR-B-ERV-COND``'s crossing into the bath inside ``W-B-STR2``'s cavity (2026-10-17;
    across the bath floor it failed this check) on its way to ``FX-B-BATH-LAV``.

    DECLARED OPEN: ``DU-B-ERV-R-GYM`` and ``PR-B-COND``'s gym leg. A 3" duct under a
    ceiling can never make the 3" this check allows — its own radius spends half of it — so
    for eleven days the answer was ``SF-B-GYM``, a bulkhead. ``RM-B-GYM.exposed_services``
    replaced it on 2026-09-13: the run is still measured, against the 6'-8" headroom line,
    and it is the sentence rather than 107 SF of board that carries the room.

    SPLIT: ``CD-B-GARAGE`` wanted the basement ceiling indoors and -4'-0" of burial in the
    house/garage gap, and a ``ConduitRun`` changes elevation only at its LAST vertex. It is
    two runs now — one feeder, both naming ``ED-B-PANEL`` and ``ED-G-EV-1450`` — handing
    over at a vertical drop inside ``W-B-N2``, at the station its sleeve always punched.
    """
    fails = [f for f in findings if f.result is Result.FAIL]
    assert not fails, [f.message for f in fails]
    assert any(f.result is Result.PASS for f in findings), [f.message for f in findings]


def test_a_riser_is_reported_as_feet_of_height(catlin_model) -> None:
    """A riser's plan piece is a point, so there is no length to report and a crossing test
    alone cannot see it at all.

    ``PR-B-CW-SUITE`` used to stop 30" above the suite bath's floor, 51" from the nearest
    fixture it names and in open air. It now jogs through ``FS-S-WEST`` and rises inside
    ``W-S-SN3``, so the defect is put back here: the exposure is the riser's HEIGHT, and the
    depth is clamped to the room, which is what makes "107.5 below a 107.5-inch room" mean
    "it occupies the whole of it"."""
    from typehaus.model import ft, inch

    assert not _fails_for(catlin_model, "PR-B-CW-SUITE")
    original = next(r for r in catlin_model.pipe_runs if r.tag == "PR-B-CW-SUITE")
    head = (ft(13, 7.2).meters, ft(16, 10.8).meters)
    regressed = dataclasses.replace(
        original,
        path=((ft(8).meters, ft(16).meters), head, head),
        z_m=(inch(-14.8).meters, inch(-14.8).meters, ft(12, 6).meters))
    model = dataclasses.replace(
        catlin_model,
        pipe_runs=tuple(regressed if r.tag == original.tag else r
                        for r in catlin_model.pipe_runs))
    fails = _fails_for(model, "PR-B-CW-SUITE")
    riser = next(f for f in fails if f.element_tags[1] == "RM-S-SUITEBATH")
    assert "107.5\" below RM-S-SUITEBATH" in riser.message
    exposure = float(riser.message.split(" for ")[1].split(" ft")[0])
    assert exposure == pytest.approx(2.5, abs=0.1)


def test_it_leads_with_depth_not_length(catlin_model) -> None:
    """Ranking by crossing length puts the long shallow runs on top; ranking by intrusion
    puts the real defects there. ``PR-B-KITCH-DRAIN`` was 14.5 ft into the theater and
    ``CD-B-GARAGE`` only 6 ft into the stair, but the stair one was 36" deep against the
    theater's 6.7". The message says the depth first.

    ``CD-B-GARAGE``'s pre-split form is put back to say so — flat at -4'-0" the whole way
    across the house, which is five feet off the basement slab.

    **``RM-B-STAIR``'s declaration is taken back off for this one test**, and that is the
    point of it rather than a workaround. The room says its services are deliberately
    exposed as of 2026-09-13 (``SF-B-HALL``'s retirement), so on the live house this
    conduit would be graded against the 6'-8" headroom line — a real finding, in the other
    branch, reading 19.3". The branch under test here is the CEILING comparison and its
    depth-first ranking, and a fixture that quietly stopped exercising it would still have
    passed on the headroom wording.
    """
    from typehaus.model import ft

    catlin_model = dataclasses.replace(
        catlin_model,
        rooms=tuple(dataclasses.replace(r, exposed_services=None)
                    if r.tag == "RM-B-STAIR" else r for r in catlin_model.rooms))
    assert not _fails_for(catlin_model, "CD-B-GARAGE")
    original = next(r for r in catlin_model.conduits if r.tag == "CD-B-GARAGE")
    regressed = dataclasses.replace(
        original,
        # The cross leg is at 25'-9", under the hall's ceiling south of the well: y=35'-0"
        # was the 4" deck strip FO-M-STAIR left at the wall, open well since 2026-09-23.
        path=((ft(2).meters, ft(29).meters), (ft(2).meters, ft(25, 9).meters),
              (ft(16).meters, ft(25, 9).meters), (ft(16).meters, ft(41, 9.375).meters)),
        z_start_m=ft(-4).meters, z_end_m=ft(5, 10).meters)
    model = dataclasses.replace(
        catlin_model,
        conduits=tuple(regressed if r.tag == original.tag else r
                       for r in catlin_model.conduits))
    fails = _fails_for(model, "CD-B-GARAGE")
    assert [f.element_tags[1] for f in fails] == ["RM-B-STAIR"]
    for finding in fails:
        head = finding.message.split(" below ")[0]
        assert head.endswith('"'), finding.message
        assert "hangs" in head
    intrusion = float(fails[0].message.split("hangs ")[1].split('"')[0])
    assert intrusion == pytest.approx(36.1, abs=0.2), fails[0].message


def test_a_service_room_ceiling_is_not_a_finished_one() -> None:
    """A mechanical room's ceiling is a service plane and pipe hangs there by design. The
    set is a fact about the vocabulary, in ``model/enums.py`` beside
    ``SLEEPING_OCCUPANCIES`` — and it deliberately excludes the two it is tempting to add:
    a hallway is a room people look up in, and a stairwell is the one place a bulkhead
    lands at head height."""
    assert Occupancy.MECHANICAL in EXPOSED_SERVICE_OCCUPANCIES
    assert Occupancy.HALLWAY not in EXPOSED_SERVICE_OCCUPANCIES
    assert Occupancy.STAIR not in EXPOSED_SERVICE_OCCUPANCIES
    assert Occupancy.BATHROOM not in EXPOSED_SERVICE_OCCUPANCIES


def _fails_for(model, tag):
    return [f for f in run_from_model(model, [], tier=Tier.ADVISORY,
                                      only="mep.run_in_finished_volume").findings
            if f.check_id == "mep.run_in_finished_volume"
            and f.result is Result.FAIL and f.element_tags[0] == tag]


def test_the_clip_is_three_dimensional_not_a_whole_segment_band(catlin_model) -> None:
    """The defect this was written for, put back: ``PR-A-STUBATH-DRAIN``'s original
    three-point form dived from the attic bay straight to the second-storey stack head in
    one diagonal.

    Only the part of that segment actually inside the suite bath's air counts: it starts
    where the pipe's crown passes under the ceiling, not where the plan line crosses the
    room's edge — the same lesson ``crossing_band`` already records for rough openings. And
    the depth is clamped to the room, because the pipe's bottom ends up under the storey
    datum and "116 inches below the ceiling" of a 107-inch room is not a usable number."""
    from typehaus.model import ft

    original = next(r for r in catlin_model.pipe_runs if r.tag == "PR-A-STUBATH-DRAIN")
    regressed = dataclasses.replace(
        original,
        path=((ft(11, 0.875).meters, ft(19, 4).meters),
              (ft(9, 7.5).meters, ft(19, 4).meters),
              (ft(13).meters, ft(16, 10.8).meters)),
        z_m=(ft(19, 4).meters, ft(19, 3.5).meters, ft(9, 9).meters))
    model = dataclasses.replace(
        catlin_model,
        pipe_runs=tuple(regressed if r.tag == original.tag else r
                        for r in catlin_model.pipe_runs))
    fails = _fails_for(model, "PR-A-STUBATH-DRAIN")
    assert [f.element_tags[1] for f in fails] == ["RM-S-SUITEBATH"]
    # The segment is 4.16 ft of plan; only the part actually inside the room's air counts,
    # and it starts where the pipe's crown passes under the ceiling rather than where the
    # plan line enters the polygon.
    exposure = float(fails[0].message.split(" for ")[1].split(" ft")[0])
    assert 3.0 < exposure < 4.16, fails[0].message
    intrusion = float(fails[0].message.split("hangs ")[1].split('"')[0])
    assert intrusion == pytest.approx(107.5, abs=0.1), fails[0].message


def test_a_drop_that_ends_at_a_thing_in_the_room_is_the_connection_to_it(
        catlin_model) -> None:
    """The grace rule. ``PR-M-DRYER-COND`` ends over ``FX-M-LAUNDRY-SINK``: its last leg is
    the connection, not a transit. Move that terminal vertex out of reach of everything in
    the room and the same geometry becomes a finding — so it is the terminal test deciding
    it, not a threshold."""
    assert not _fails_for(catlin_model, "PR-M-DRYER-COND")

    original = next(r for r in catlin_model.pipe_runs if r.tag == "PR-M-DRYER-COND")
    # Only index 0 or len(path)-2 can ever qualify, so re-labelling the run's own last leg
    # as an interior one is enough: repeat the final vertex and the connection becomes
    # transit through the room with no terminal at its end.
    moved = dataclasses.replace(
        original,
        path=(*original.path[:-1], (original.path[-1][0] + 3.0, original.path[-1][1])),
        z_m=(*original.z_m[:-1], original.z_m[-1]))
    model = dataclasses.replace(
        catlin_model,
        pipe_runs=tuple(moved if r.tag == original.tag else r
                        for r in catlin_model.pipe_runs))
    assert _fails_for(model, "PR-M-DRYER-COND")


def test_a_trap_under_its_own_basin_is_the_fixture_not_transit(catlin_model) -> None:
    """``PR-A-BAR-DRAIN`` leaves the open-frame SUNNERSTA in three legs (stub, trap-arm,
    drop through the floor), all inside the sink's footprint, so all are the fixture's own
    connection. Move the drop 10" south of the basin, or start it 17" over the basin's
    283.1" top, and the same legs are transit."""
    from typehaus.model import inch

    assert not _fails_for(catlin_model, "PR-A-BAR-DRAIN")
    original = next(r for r in catlin_model.pipe_runs if r.tag == "PR-A-BAR-DRAIN")

    def _with(**fields):
        moved = dataclasses.replace(original, **fields)
        return dataclasses.replace(
            catlin_model, pipe_runs=tuple(moved if r.tag == original.tag else r
                                          for r in catlin_model.pipe_runs))

    south = inch(177.74).meters  # 10" past the footprint's south edge at 187.74"
    path = (original.path[0], (original.path[1][0], south), (original.path[2][0], south),
            *original.path[3:])
    assert _fails_for(_with(path=path), "PR-A-BAR-DRAIN")
    over = (inch(300.0).meters,) * 2 + tuple(original.z_m[2:])
    assert _fails_for(_with(z_m=over), "PR-A-BAR-DRAIN")


def test_the_bands_lower_edge_is_the_storey_datum(catlin_model) -> None:
    """``ResolvedCeiling`` carries no floor plane, and without a lower edge a basement main
    is graded against every room stacked above it — 435 rows on this house against 66.

    ``PR-B-MAIN-DRAIN`` hangs in the basement and is clear of every finished ceiling there.
    Nothing about its plan geometry changes when its elevations do, so a finding that
    appears once it is raised into the main floor's air is the band's floor talking."""
    original = next(r for r in catlin_model.pipe_runs if r.tag == "PR-B-MAIN-DRAIN")
    assert not _fails_for(catlin_model, "PR-B-MAIN-DRAIN")

    lifted = dataclasses.replace(
        original, z_m=tuple(z + 60 * 0.0254 for z in original.z_m))
    model = dataclasses.replace(
        catlin_model,
        pipe_runs=tuple(lifted if r.tag == original.tag else r
                        for r in catlin_model.pipe_runs))
    fails = _fails_for(model, "PR-B-MAIN-DRAIN")
    assert fails and all(tag.startswith("RM-M-") for tag in
                         (f.element_tags[1] for f in fails)), [f.message for f in fails]
