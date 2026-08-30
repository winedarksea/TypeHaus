"""``mep.run_over_void`` — a run may not span a floor opening with nothing under it.

The check is a buildability rule with no code section behind it, which is why it is ADVISORY.
What it is *not* is optional: a ``Result.FAIL`` at any severity breaks the 0-FAIL gate, and it
found two live defects on catlin the moment it was written (``CD-M-DATA-KITCH`` at 7.27 ft
and ``CD-M-DATA-PORCH`` at 15.52 ft across the stairwell) plus a third nobody had looked for
(``CD-A-PV-EAST``, whose last foot and whole riser stood in ``FO-A-HALL``).

These tests pin the three things that make it right rather than merely loud: the inward buffer,
the elevation band that decides which floor a run is *in*, and the wall exemption.
"""

from __future__ import annotations

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.mep.routing import MIN_SPAN_FT, ON_DECK_FT, VOID_BUFFER_M
from typehaus.checks.registry import Tier, registered
from typehaus.findings import Result

_M_TO_FT = 3.280839895013123


@pytest.fixture(scope="module")
def findings(catlin_model):
    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    return [f for f in report.findings if f.check_id == "mep.run_over_void"]


def test_the_check_is_actually_registered():
    """**The trap.** A module missing from ``checks/mep/__init__.py``'s import list registers
    nothing, emits nothing, and every other test in this file still passes — because a check
    that never runs produces no findings, which is indistinguishable from a check that found
    none. Assert the id is in the registry, not just that the findings list is empty."""
    assert "mep.run_over_void" in {cid for cid, _ in registered(Tier.ADVISORY)}


def test_catlin_has_no_run_spanning_a_void(findings):
    """The 0-FAIL gate. ``CheckReport.counts()`` counts a FAIL regardless of severity, so this
    ADVISORY check holds catlin to the same standard a code check would."""
    fails = [f for f in findings if f.result is Result.FAIL]
    assert not fails, [f.message for f in fails]
    assert [f.result for f in findings] == [Result.PASS]


def test_it_catches_a_run_drawn_across_the_stairwell(catlin_model):
    """The defect it exists for, reproduced by putting a run back where one used to be.

    ``CD-M-DATA-KITCH`` ran east at y=34'-6" and +9'-2" from the chase to x=19'-0". At that
    height it is inside FS-S-WEST, whose opening is x 10'-3 3/8"..17'-8 5/8", so 7'-5 1/4" of
    that leg was over a two-storey shaft; buffered inward 1" it measures **7.27 ft**.

    Note which floor it is measured against. ``FS-M-STAIR``, directly underneath, has an
    opening 2 5/8" narrower, and the same leg read against that one measures 7.05 — which is
    what every by-eye estimate of this defect reported, because storey membership says main
    and the physics says second."""
    import dataclasses

    from typehaus.model import ft

    original = next(run for run in catlin_model.conduits if run.tag == "CD-M-DATA-KITCH")
    # Metre tuples, the shape the RESOLVED path carries — ``pt()`` makes a Point2D, which is
    # the authoring vocabulary and not what a resolved run holds.
    old_path = ((ft(2).meters, ft(34, 6).meters), (ft(19).meters, ft(34, 6).meters),
                (ft(19).meters, ft(29).meters))
    regressed = dataclasses.replace(original, path=old_path)
    model = dataclasses.replace(
        catlin_model,
        conduits=tuple(regressed if run.tag == original.tag else run
                       for run in catlin_model.conduits))
    findings = [f for f in run_from_model(model, [], tier=Tier.ADVISORY).findings
                if f.check_id == "mep.run_over_void"]
    fails = [f for f in findings if f.result is Result.FAIL]
    assert len(fails) == 1, [f.message for f in fails]
    assert "CD-M-DATA-KITCH" in fails[0].element_tags
    assert "7.27 ft" in fails[0].message
    assert "FS-S-WEST" in fails[0].message


def test_the_void_is_buffered_inward_so_a_trimmer_line_is_not_a_span(catlin_model):
    """A run laid *along* the opening's own edge shares its coordinate. Unbuffered, that reads
    as unsupported — when the trimmer that makes the edge is exactly what it straps to.

    Laid exactly on ``FS-S-WEST``'s east trimmer and run the full depth of the opening, a
    raceway that would otherwise report nine feet of unsupported span reports nothing."""
    import dataclasses

    original = next(run for run in catlin_model.conduits if run.tag == "CD-M-DATA-PORCH")
    floor = next(f for f in catlin_model.floors if f.tag == "FS-S-WEST")
    void = floor.deck_voids[0]
    east = max(point[0] for point in void)
    on_the_trimmer = dataclasses.replace(
        original, path=((east, max(point[1] for point in void)),
                        (east, min(point[1] for point in void))))
    model = dataclasses.replace(
        catlin_model,
        conduits=tuple(on_the_trimmer if run.tag == original.tag else run
                       for run in catlin_model.conduits))
    fails = [f for f in run_from_model(model, [], tier=Tier.ADVISORY).findings
             if f.check_id == "mep.run_over_void" and f.result is Result.FAIL]
    assert not fails, [f.message for f in fails]
    assert pytest.approx(0.0254) == VOID_BUFFER_M


def test_a_run_below_the_joists_is_not_this_checks_business(catlin_model, findings):
    """The elevation band, from the other side. Catlin's basement ceiling carries four runs at
    -1'-6" to -1'-7 3/8" whose plan lines cross the stairwell — but ``FS-M-STAIR``'s joists
    stop at -0'-11 7/8", so they hang *below* the floor, in the room.

    Whether they foul the stair's headroom is a real question and a different one; this check
    has no per-room ceiling plane and must not pretend to answer it. A storey-based match, or a
    band dialled deep enough to reach them, calls all four void-spanners."""
    below = {"CD-B-KITCHEN", "CD-B-DATA-MEDIA", "DU-B-ERV-R-PLAY", "DU-B-ERV-R-BATH"}
    named = {tag for f in findings for tag in f.element_tags}
    assert not (below & named)
    # ...and they really do cross the opening in plan, so the exemption is the band, not luck.
    stair = next(floor for floor in catlin_model.floors if floor.tag == "FS-M-STAIR")
    joist_bottom = min(member.z0_m for member in stair.members if member.z0_m is not None)
    for duct in catlin_model.ducts:
        if duct.tag in below:
            assert max(duct.z_m) < joist_bottom, duct.tag


def test_a_run_lying_on_the_deck_is_graded(catlin_model):
    """The band's other edge. ``CD-A-DATA-NE`` rides 6" *above* the attic deck, which is above
    ``deck_z1_m`` — a band that stopped at the decking would miss every raceway strapped to a
    floor it lies on, which is most of them in an attic."""
    attic = next(floor for floor in catlin_model.floors
                 if floor.tag == "FS-ATTIC" and floor.deck_voids)
    run = next(r for r in catlin_model.conduits if r.tag == "CD-A-DATA-NE")
    assert run.z_start_m > attic.deck_z1_m
    assert run.z_start_m < attic.deck_z1_m + ON_DECK_FT / _M_TO_FT


def test_a_wall_over_the_void_is_the_exemption(catlin_model):
    """``CD-A-PV-EAST`` finishes at y=35'-10", 4" into W-A-N2B's stud cavity, and the cavity is
    directly over ``FS-ATTIC``'s void's northern edge. It passes because a wall is framing to
    strap to — which is the whole rule: the check asks for support, not for deck."""
    wall = next(w for w in catlin_model.walls if w.tag == "W-A-N2B")
    stud = next(layer for layer in wall.layers if layer.name == "stud")
    ys = [point[1] for point in stud.polygon]
    run = next(r for r in catlin_model.conduits if r.tag == "CD-A-PV-EAST")
    assert min(ys) <= run.path[-1][1] <= max(ys)


def test_a_clipped_corner_is_below_the_reporting_floor():
    """``MIN_SPAN_FT`` exists so a route that nicks a void corner by an inch — an artifact of
    where a vertex landed — does not teach the reader to ignore the check."""
    assert 0 < MIN_SPAN_FT < 1.0


# --- mep.run_route_efficiency --------------------------------------------------------------

def test_the_ratio_advisory_is_registered_and_passes_catlin(catlin_model):
    """Report-only in spirit, FAIL in fact — and it passes because the threshold is set where
    catlin's own worst honest route sits, not above the worst thing in the house."""
    from typehaus.checks.registry import MepPreferences

    assert "mep.run_route_efficiency" in {cid for cid, _ in registered(Tier.ADVISORY)}
    report = run_from_model(catlin_model, [], tier=Tier.ADVISORY)
    mine = [f for f in report.findings if f.check_id == "mep.run_route_efficiency"]
    assert mine and not [f for f in mine if f.result is Result.FAIL]
    assert MepPreferences().max_run_developed_over_straight == 2.5


def test_a_trunk_is_excluded_because_it_is_not_a_route(catlin_model):
    """``PR-B-CW-TRUNK`` serves twenty-one fixtures and scores 2.69 — over the line, and
    correctly so. It is a distribution tree flattened into one polyline, and the distance
    between its first and last vertex is not a path it could have taken instead.

    The exclusion is a rule about what the geometry MEANS, not a suppression: state it as
    "three or more terminals" and it applies to any house, where a per-tag entry would only
    ever have applied to this one."""
    from typehaus.takeoff.runs import run_schedule

    trunk = next(r for r in catlin_model.pipe_runs if r.tag == "PR-B-CW-TRUNK")
    assert len(trunk.serves) >= 3
    row = next(r for r in run_schedule(catlin_model) if r["tag"] == "PR-B-CW-TRUNK")
    assert row["ratio"] > 2.5  # it WOULD fail, and is not graded
    findings = [f for f in run_from_model(catlin_model, [], tier=Tier.ADVISORY).findings
                if f.check_id == "mep.run_route_efficiency"]
    assert not any("PR-B-CW-TRUNK" in f.element_tags for f in findings)


def test_the_worst_graded_run_leaves_a_documented_margin(catlin_model):
    """If this shrinks to nothing, the threshold has stopped meaning anything and somebody
    should look at the run rather than at the number."""
    from typehaus.takeoff.runs import run_schedule

    terminals = {r.tag: len(r.serves) for r in catlin_model.pipe_runs}
    graded = [r for r in run_schedule(catlin_model)
              if r["ratio"] is not None and r["developed_ft"] >= 20
              and terminals.get(r["tag"], 0) < 3]
    worst = max(graded, key=lambda r: r["ratio"])
    assert worst["tag"] == "PR-M-CW-COLDSTORE-STUB"
    assert worst["ratio"] == pytest.approx(2.41, abs=0.03)
