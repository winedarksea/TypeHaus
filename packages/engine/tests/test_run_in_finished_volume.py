"""``mep.run_in_finished_volume`` — a run hanging in a room somebody lives in.

``run_route_efficiency`` used to say the model had no per-room ceiling plane and so could
not ask this. It has had one since the ceiling work; this is the check that asks. Catlin's
basement service corridor was real, and all eleven findings were closed on 2026-09-09 by
reroutes, walls and one soffit. The house passes.

What these tests pin is the machinery, because that is what had to survive the fix and is
what would rot now that nothing exercises it in anger: the band's lower edge, the
three-dimensional clip, the grace rule, and the honest UNKNOWN over the attic. Each of the
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
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY)
    return [f for f in report.findings if f.check_id == "mep.run_in_finished_volume"]


def test_the_check_is_actually_registered() -> None:
    """**The trap.** ``routing_ceiling.py`` has to be named in ``checks/mep/__init__.py``.
    A module nothing imports registers nothing and emits nothing, which is
    indistinguishable from finding nothing."""
    assert "mep.run_in_finished_volume" in {cid for cid, _ in registered(Tier.ADVISORY)}


def test_the_attic_is_reported_unknown_rather_than_passed(findings) -> None:
    """Every ``RM-A-*`` room resolves ``ResolvedCeiling.z0_m = None`` (``FollowRoof``), so
    there is no plane to compare a run against. A check that stayed silent about them would
    be claiming coverage it does not have — the tri-state contract's whole point."""
    unknowns = [f for f in findings if f.result is Result.UNKNOWN
                and "FollowRoof" in f.message]
    assert len(unknowns) == 1, [f.message for f in findings]
    assert set(unknowns[0].element_tags) >= {"RM-A-STUBATH", "RM-A-STUDIO", "RM-A-STUDY"}


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
    ``PR-B-ERV-COND``'s fall into ``W-B-SA-N``'s cavity, which is the only way that line
    can reach its receptor at all — the ERV pan is at 4'-6" and the sauna's ceiling is at
    6'-10 13/16", so it can never travel over it the way ``PR-B-COND`` does.

    BOXED OUT: ``DU-B-ERV-R-GYM`` and ``PR-B-COND``'s gym leg, under ``SF-B-GYM``. A 3"
    duct under a ceiling can never make the 3" this check allows — its own radius spends
    half of it — so a box is the only answer there, and this is the one finding whose fix
    could not have been anything else.

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
    across the house, which is five feet off the basement slab."""
    from typehaus.model import ft

    assert not _fails_for(catlin_model, "CD-B-GARAGE")
    original = next(r for r in catlin_model.conduits if r.tag == "CD-B-GARAGE")
    regressed = dataclasses.replace(
        original,
        path=((ft(2).meters, ft(29).meters), (ft(2).meters, ft(35).meters),
              (ft(16).meters, ft(35).meters), (ft(16).meters, ft(41, 9.375).meters)),
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
    return [f for f in run_from_model(model, [], tier=Tier.ADVISORY).findings
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
