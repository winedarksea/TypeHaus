"""``Room.exposed_services`` — the ceiling a house says is open on purpose.

Boxing a run out with a ``Soffit`` was the only authored answer to
``mep.run_in_finished_volume`` until this landed, which made a soffit the engine's idea of a
ceiling rather than the owner's: three of catlin's existed for no other reason, and all
three were retired on 2026-09-13 once their rooms could say it in words.

What these tests pin is the difference between this and a suppression, because that
difference is the whole point and nothing about the code's shape defends it:

* the declaration is a REASON, refused at load time if it is a flag wearing a string;
* the check PASSES with that reason quoted, so the report carries the decision;
* and it retires exactly one question. A run in a declared room is measured again against
  the headroom line, because ``code.R305_ceiling_height`` measures the STRUCTURE overhead
  and has never seen a pipe.
"""

from __future__ import annotations

import dataclasses

import pytest
from pydantic import ValidationError

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.findings import Result
from typehaus.model import Occupancy, ft, pt
from typehaus.model.spatial import Room

CID = "mep.run_in_finished_volume"
_ROOM = "RM-B-PLAY-N"
_REASON = "owner accepts exposed services in the basement: this ceiling is left open"


def _findings(model):
    return [f for f in run_from_model(model, [], tier=Tier.ADVISORY).findings
            if f.check_id == CID]


def _declare(model, room_tag: str, reason: str = _REASON):
    return dataclasses.replace(
        model,
        rooms=tuple(dataclasses.replace(r, exposed_services=reason)
                    if r.tag == room_tag else r for r in model.rooms))


def _run_across(model, room_tag: str, *, below_ceiling_in: float | None = None,
                above_floor_in: float | None = None):
    """Lay ``PR-B-MAIN-DRAIN`` flat across ``room_tag``'s ceiling polygon at one elevation.

    Built from the room's own resolved planes rather than from typed coordinates, so the
    two elevations these tests care about — under the ceiling, and under the head — stay
    true whatever the house does to that storey next.
    """
    ceiling = next(c for c in model.ceilings if c.room_ref == room_tag)
    storey = next(s for s in model.plan.storeys if s.tag == ceiling.storey)
    xs = [p[0] for p in ceiling.outline]
    ys = [p[1] for p in ceiling.outline]
    y = (min(ys) + max(ys)) / 2
    if below_ceiling_in is not None:
        z = ceiling.z0_m - below_ceiling_in * 0.0254
    else:
        z = storey.elevation.meters + float(above_floor_in) * 0.0254
    original = next(r for r in model.pipe_runs if r.tag == "PR-B-MAIN-DRAIN")
    moved = dataclasses.replace(
        original, path=((min(xs), y), (max(xs), y)), z_m=(z, z))
    return dataclasses.replace(
        model,
        pipe_runs=tuple(moved if r.tag == original.tag else r for r in model.pipe_runs))


# --- the declaration itself ---------------------------------------------------------------

def test_a_flag_is_refused_at_load_time() -> None:
    """A boolean here would be a suppression wearing a schema. The validator's bar is low
    and deliberately not zero — a few words in a row — and what it catches is every
    spelling a boolean would take."""
    for flag in ("", "  ", "true", "yes", "exposed", "x"):
        with pytest.raises(ValidationError):
            Room(uid="TSTROOM001", tag="RM-T", seed=pt(ft(1), ft(1)),
                 occupancy=Occupancy.LIVING, exposed_services=flag)


def test_a_sentence_is_kept_verbatim() -> None:
    """Stripped, and otherwise untouched: the check quotes it into the report, so anything
    this field normalised would be the reviewer reading the engine's words, not the
    owner's."""
    room = Room(uid="TSTROOM002", tag="RM-T", seed=pt(ft(1), ft(1)),
                occupancy=Occupancy.LIVING, exposed_services=f"  {_REASON}  ")
    assert room.exposed_services == _REASON


def test_the_default_changes_nothing(catlin_model_ro) -> None:
    """Undeclared is the ordinary case and must stay exactly as it was: every room on this
    house that says nothing is graded against its finished ceiling as before."""
    undeclared = [r.tag for r in catlin_model_ro.rooms if r.exposed_services is None]
    assert len(undeclared) > 30
    assert not [f for f in _findings(catlin_model_ro) if f.result is Result.FAIL]


# --- what it does to the finding ------------------------------------------------------------

def test_it_turns_a_fail_into_a_pass_that_quotes_the_reason(catlin_model) -> None:
    """The mechanism, both halves in one test.

    A run laid 10" under ``RM-B-PLAY-N``'s ceiling is a FAIL — that is the check working.
    Declaring the room's ceiling open turns it into a PASS **naming the run and quoting the
    sentence**, which is the only thing separating this from a suppression: a suppressed
    check folds to UNKNOWN and says nothing a reviewer can weigh.
    """
    exposed_run = _run_across(catlin_model, _ROOM, below_ceiling_in=10.0)
    fails = [f for f in _findings(exposed_run)
             if f.result is Result.FAIL and f.element_tags[1] == _ROOM]
    assert fails, "the regression did not reproduce — no run hangs in the room"

    declared = _findings(_declare(exposed_run, _ROOM))
    assert not [f for f in declared if f.result is Result.FAIL], \
        [f.message for f in declared]
    passes = [f for f in declared if f.result is Result.PASS and _ROOM in f.element_tags]
    assert len(passes) == 1, [f.message for f in declared]
    assert _REASON in passes[0].message
    assert "PR-B-MAIN-DRAIN" in passes[0].message
    assert "PR-B-MAIN-DRAIN" in passes[0].element_tags


def test_exposed_is_not_ungraded(catlin_model) -> None:
    """**The one that matters.** The same declared room, with the run dropped to 5'-0" off
    the floor: still a FAIL, and a differently-worded one, because a pipe somebody walks
    into is not the question the declaration answered.

    Nothing else in the engine catches this. ``code.R305_ceiling_height`` derives the
    underside of the STRUCTURE over a room — deck, slab or soffit — and a run is none of
    those, so without this branch declaring a room exposed would quietly retire a real
    hazard along with the cosmetic one.
    """
    low = _declare(_run_across(catlin_model, _ROOM, above_floor_in=60.0), _ROOM)
    fails = [f for f in _findings(low) if f.result is Result.FAIL]
    assert len(fails) == 1, [f.message for f in _findings(low)]
    assert "headroom line" in fails[0].message
    assert "6'-8\"" in fails[0].message
    assert fails[0].element_tags == ("PR-B-MAIN-DRAIN", _ROOM)
    # And the room gets no PASS while it holds a headroom finding: one room, one verdict.
    assert not [f for f in _findings(low)
                if f.result is Result.PASS and _ROOM in f.element_tags]


def test_a_declaration_that_grades_nothing_says_so(catlin_model) -> None:
    """A mechanical room is already exempt by occupancy, so a declaration on one reads
    nothing and must not be reported as though it had. UNKNOWN, naming the room — the
    tri-state contract's own rule, and the way an author finds out the sentence they wrote
    is decorative."""
    declared = _findings(_declare(catlin_model, "RM-B-FURNACE"))
    unknowns = [f for f in declared
                if f.result is Result.UNKNOWN and "RM-B-FURNACE" in f.element_tags]
    assert len(unknowns) == 1, [f.message for f in declared]
    assert "grades nothing" in unknowns[0].message
    assert _REASON in unknowns[0].message


# --- the reference house --------------------------------------------------------------------

def test_catlin_declares_its_two_rooms(catlin_model_ro) -> None:
    """The demonstration, pinned. Both rooms pass with their own sentence quoted, and the
    gym's names the run it is carrying — ``PR-B-COND``, which hangs in its open ceiling
    since ``SF-B-GYM`` was retired on 2026-09-13.

    **It named two until D3 (2026-09-19) and now it names one, and the room's own sentence
    moved with it.** ``DU-B-ERV-R-GYM`` used to cross the gym's width at y=10'-6 5/8"; it
    comes down the stair hall's x=17'-0" lane now and enters on its terminal leg, so what
    hangs in the gym's air is the condensate line alone. That is the half of this check
    worth pinning: the PASS quotes the room back to itself, so a design that stops putting a
    duct in a room has to stop saying it does.

    ``RM-S-SUITE`` names ``DU-S-HP-SUITE``. It named nothing until 2026-09-13, when
    ``SF-S-SUITE`` was retired — and the empty case's own sentence is what said so, which
    is the whole reason it exists instead of "0 run(s)".
    """
    passes = {f.element_tags[0]: f.message for f in _findings(catlin_model_ro)
              if f.result is Result.PASS and f.element_tags}
    assert "exposed services in the basement" in passes["RM-B-GYM"]
    assert "PR-B-COND" in passes["RM-B-GYM"]
    assert "DU-B-ERV-R-GYM" not in passes["RM-B-GYM"]
    assert "the condensate line crossing it" in passes["RM-B-GYM"]
    # Where it went. The hall carries three ERV branches and the sauna vent since D3.
    assert "DU-B-ERV-R-GYM" in passes["RM-B-STAIR"]
    assert "DU-B-ERV-R-PLAY" in passes["RM-B-STAIR"]
    assert "exposed duct in the primary suite" in passes["RM-S-SUITE"]
    assert "DU-S-HP-SUITE" in passes["RM-S-SUITE"]
    assert "nothing currently hangs in its open air" not in passes["RM-S-SUITE"]
