"""mep.ventilation_distribution — ERV register coverage (advisory, tri-state)."""

from __future__ import annotations

from types import SimpleNamespace


from typehaus.checks.mep.hvac import ventilation_distribution
from typehaus.findings import Result
from typehaus.model.enums import DuctSystem
from typehaus.model.mep import Register
from typehaus.quantities import ft, pt
from typehaus.resolve.model import ResolvedRoom


CID = "mep.ventilation_distribution"


def _run(model):
    ctx = SimpleNamespace(model=model)
    return ventilation_distribution(ctx)


# --- synthetic tri-state fixtures ---------------------------------------------------

def _room(tag, occupancy, conditioned=True,
          ring=((0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0))):
    return ResolvedRoom(uid=tag, tag=tag, storey="main", occupancy=occupancy,
                        conditioned=conditioned, clear_face=list(ring),
                        area_m2=16.0, floor_finish=None)


def _fake_model(rooms, registers):
    plan = SimpleNamespace(
        storeys=[SimpleNamespace(tag="main")],
        storey_elements=lambda tag: registers if tag == "main" else [],
    )
    return SimpleNamespace(rooms=rooms, plan=plan)


def _register(tag, kind, position, room=None):
    return Register(uid=f"T{abs(hash(tag)) % 10**9:09d}", tag=tag,
                    kind=kind, position=position, room=room)


def test_no_rooms_is_unknown():
    findings = _run(_fake_model([], []))
    assert [f.result for f in findings] == [Result.UNKNOWN]


def test_unmatched_register_is_unknown_and_bare_bedroom_fails():
    rooms = [_room("RM-X-BED", "bedroom")]
    regs = [_register("REG-X-FAR", DuctSystem.SUPPLY, pt(ft(50), ft(50)))]
    findings = _run(_fake_model(rooms, regs))
    results = {f.result for f in findings}
    assert Result.UNKNOWN in results  # the stranded register
    fails = [f for f in findings if f.result == Result.FAIL]
    assert any("RM-X-BED" in f.message for f in fails)
    assert all(f.severity.value == "warn" for f in fails)  # ADVISORY, never an error


def test_point_in_polygon_matches_a_register_without_room():
    rooms = [_room("RM-X-BED", "bedroom")]
    # (2 m, 2 m) is inside the 4 m clear-face square; no room= authored.
    regs = [_register("REG-X-SUP", DuctSystem.SUPPLY, pt(ft(6, 6.74), ft(6, 6.74)))]
    findings = _run(_fake_model(rooms, regs))
    assert all(f.result == Result.PASS for f in findings)


def test_bathroom_without_stale_terminal_fails_and_exhaust_satisfies_it():
    rooms = [_room("RM-X-BATH", "bathroom")]
    findings = _run(_fake_model(rooms, []))
    assert any(f.result == Result.FAIL and "RM-X-BATH" in f.message for f in findings)
    regs = [_register("REG-X-EXH", DuctSystem.EXHAUST, pt(ft(1), ft(1)),
                      room="RM-X-BATH")]
    findings = _run(_fake_model(rooms, regs))
    assert all(f.result == Result.PASS for f in findings)


def test_unconditioned_room_needs_no_supply():
    rooms = [_room("RM-X-PORCH", "living", conditioned=False)]
    findings = _run(_fake_model(rooms, []))
    # No supply requirement, and the count-sanity line passes at 0-for-0.
    assert all(f.result == Result.PASS for f in findings)


# --- catlin coverage ----------------------------------------------------------------

# The 2026-07-29 ERV reduction (plans/TODO.md: "We don't need the 30 some ERV inlets and
# outlets in the house") left exactly two rooms unserved — RM-S-PLANT ("awaiting its own
# mini-HRV") and RM-S-STUDY2 ("takes air from the hall it opens onto") — and this test
# pinned that pair for six weeks. Both were drawn on 2026-08-16: REG-S-HP-PLANT and
# REG-S-HP-STUDY2, ceiling boots off DU-S-HP-SOUTH, System 1's FS-ATTIC joist-bay branch
# (houses/catlin/plan/mep_registers.py, mep_hvac.py). The set is empty now and stays named
# rather than the assertion being loosened to "mostly pass", so ANY room falling out of
# coverage fails this test.
_EXPECTED_UNSERVED: set[str] = set()


def test_catlin_distribution_has_no_unserved_rooms(catlin_model):
    findings = _run(catlin_model)
    assert findings
    unexpected = [f for f in findings if f.result != Result.PASS
                  and not _EXPECTED_UNSERVED.intersection(f.element_tags)]
    assert not unexpected, [f.message for f in unexpected]
    # And nothing is exempt that the model does not actually flag — a stale entry in
    # _EXPECTED_UNSERVED is as much a bug as a missing terminal.
    flagged = {t for f in findings if f.result != Result.PASS for t in f.element_tags}
    assert flagged == _EXPECTED_UNSERVED, flagged


def test_catlin_covers_every_required_room(catlin_model):
    findings = _run(catlin_model)
    tags = {t for f in findings for t in f.element_tags}
    # RM-A-EAST is storage, not living space, so it no longer calls for a ventilation path.
    for required in ("RM-M-BED", "RM-M-LIVING", "RM-M-STUDY", "RM-S-SUITE",
                     "RM-B-GYM", "RM-M-BATH1", "RM-M-BATH2",
                     "RM-M-LAUNDRY", "RM-S-BATH1", "RM-B-SAUNA"):
        assert required in tags, required


def test_catlin_count_sanity_reads_the_model(catlin_model):
    findings = _run(catlin_model)
    summary = [f for f in findings if not f.element_tags]
    assert len(summary) == 1
    supply = sum(1 for s in catlin_model.plan.storeys
                 for e in catlin_model.plan.storey_elements(s.tag)
                 if e.element_kind == "Register" and e.kind.value == "supply")
    assert f"{supply} supply" in summary[0].message


def test_catlin_has_the_ensuite_exhaust_run(catlin_model):
    exhausts = [d for d in catlin_model.ducts if d.system == "exhaust"]
    assert exhausts, "the ensuite shower's EXHAUST run should resolve"
    assert all(d.conflicts == () and d.depth_ok for d in exhausts)
