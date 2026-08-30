"""``engineering.toml``, the fingerprint, and the two gates.

The seal is the whole point of the register, and a seal that cannot go stale is a
decoration. These tests are the round trip the design turns on: seal an item, perturb one
input, and confirm the stamp stops describing the model.
"""

from __future__ import annotations

import pytest

from typehaus.engineering import (
    EngineeringContext,
    EngineeringRecord,
    EngineeringResults,
    Freshness,
    LimitState,
    Quantity,
    Status,
    fingerprint,
    load_register,
    no_calc,
)
from typehaus.engineering.register import REGISTER_FILENAME


def _record(**overrides) -> EngineeringRecord:  # type: ignore[no-untyped-def]
    base = dict(
        item_id="retaining_wall/W-SG-E2", kind="retaining_wall", key="W-SG-E2",
        basis_version="1", basis="IRC R404.4", status=Status.OK,
        inputs=(Quantity("retained_height", 10.3698, "ft", 0.01),
                Quantity("footing_width", 7.0, "ft", 0.01)),
        limit_states=(LimitState("sliding", 1.5, 1.62, "", "IRC R404.4",
                                 is_safety_factor=True),),
        element_tags=("W-SG-E2",),
    )
    base.update(overrides)
    return EngineeringRecord(**base)  # type: ignore[arg-type]


def _write(tmp_path, body: str):  # type: ignore[no-untyped-def]
    (tmp_path / REGISTER_FILENAME).write_text(body)
    return load_register(tmp_path)


_SIGNOFF = '''
[[signoff]]
id        = "SG-LATERAL-01"
scope     = "Sunken-garden lateral system"
covers    = ["retaining_wall/W-SG-E2"]
engineer  = "Jane Doe, PE"
license   = "MN 12345"
sealed_on = "2026-09-14"
document  = "notes/sg_lateral_2026-09-14.pdf"

  [signoff.fingerprint]
  "retaining_wall/W-SG-E2" = "{}"
'''


# --- the file ---------------------------------------------------------------------------

def test_an_absent_file_is_an_empty_register_not_an_error(tmp_path) -> None:
    """A house that has not been to an engineer behaves exactly as it did before this
    existed — the same contract ``cli/price_file.py`` keeps for an absent prices.toml."""
    register = load_register(tmp_path)
    assert register.signoffs == ()
    assert register.covering("retaining_wall/W-SG-E2") is None
    assert register.freshness(_record())[0] is Freshness.UNSEALED


@pytest.mark.parametrize(("body", "needle"), [
    ('[[signoff]]\nid = "A"\n', "missing required key"),
    ('[[signoff]]\nid="A"\nscope="s"\ncovers="x"\nengineer="e"\nlicense="l"\n'
     'sealed_on="2026-01-01"\n', "must be a list of item ids"),
    ('[[signoff]]\nid="A"\nscope="s"\ncovers=["k/x"]\nengineer="e"\nlicense="l"\n'
     'sealed_on="not-a-date"\n', "must be an ISO date"),
])
def test_a_malformed_file_raises_naming_the_key(tmp_path, body, needle) -> None:
    """Never a silent default: a seal register that quietly ignores half of what it was
    given is worse than no register, because it looks like protection."""
    (tmp_path / REGISTER_FILENAME).write_text(body)
    with pytest.raises(ValueError) as exc:
        load_register(tmp_path)
    assert needle in str(exc.value)


def test_one_item_may_carry_only_one_seal(tmp_path) -> None:
    """Two stamps over one wall is a question for a person, not a tie-break rule."""
    body = ('[[signoff]]\nid="A"\nscope="s"\ncovers=["k/x"]\nengineer="e"\nlicense="l"\n'
            'sealed_on="2026-01-01"\n'
            '[[signoff]]\nid="B"\nscope="s"\ncovers=["k/x"]\nengineer="e"\nlicense="l"\n'
            'sealed_on="2026-01-02"\n')
    (tmp_path / REGISTER_FILENAME).write_text(body)
    with pytest.raises(ValueError, match="one item, one seal"):
        load_register(tmp_path)


def test_a_fingerprint_for_an_uncovered_item_is_refused(tmp_path) -> None:
    """It reads as protection and provides none — nothing would ever consult it."""
    body = ('[[signoff]]\nid="A"\nscope="s"\ncovers=["k/x"]\nengineer="e"\nlicense="l"\n'
            'sealed_on="2026-01-01"\n[signoff.fingerprint]\n"k/other" = "deadbeef"\n')
    (tmp_path / REGISTER_FILENAME).write_text(body)
    with pytest.raises(ValueError, match="which `covers` does not list"):
        load_register(tmp_path)


# --- the fingerprint --------------------------------------------------------------------

def test_a_seal_survives_float_noise_but_not_a_real_change() -> None:
    """The reason each Quantity declares its own quantum.

    A 7'-0" wall re-derived through metres and a solver comes back as 2.1336000000000003 m;
    a seal that goes stale on the sixteenth decimal place is a seal nobody will trust. A
    seal that survives the wall actually moving is worse.
    """
    sealed = fingerprint(_record())
    noise = _record(inputs=(Quantity("retained_height", 10.369800000000001, "ft", 0.01),
                            Quantity("footing_width", 6.999999999999999, "ft", 0.01)))
    assert fingerprint(noise) == sealed

    moved = _record(inputs=(Quantity("retained_height", 10.87, "ft", 0.01),
                            Quantity("footing_width", 7.0, "ft", 0.01)))
    assert fingerprint(moved) != sealed


def test_a_seal_goes_stale_when_the_calculation_changes_too() -> None:
    """``basis_version`` is why. A fingerprint over the inputs alone answers "did the model
    change" and is silent on "did the arithmetic change", which would let an edit to the
    calc slip under a stamp that is still, on paper, valid."""
    assert fingerprint(_record(basis_version="2")) != fingerprint(_record())


def test_the_governing_ratio_is_a_tripwire_for_a_forgotten_basis_bump() -> None:
    changed = _record(limit_states=(LimitState("sliding", 1.5, 1.10, "", "IRC R404.4",
                                               is_safety_factor=True),))
    assert fingerprint(changed) != fingerprint(_record())


def test_reordering_the_calcs_own_bookkeeping_does_not_stale_a_seal() -> None:
    reordered = _record(inputs=tuple(reversed(_record().inputs)))
    assert fingerprint(reordered) == fingerprint(_record())


# --- the states -------------------------------------------------------------------------

def test_the_four_seal_states(tmp_path) -> None:
    record = _record()
    current = fingerprint(record)

    fresh = _write(tmp_path, _SIGNOFF.format(current))
    assert fresh.freshness(record)[0] is Freshness.FRESH

    # Perturb one input: the stamp no longer describes what is drawn.
    moved = _record(inputs=(Quantity("retained_height", 11.5, "ft", 0.01),
                            Quantity("footing_width", 7.0, "ft", 0.01)))
    assert fresh.freshness(moved)[0] is Freshness.STALE

    unpinned = _write(tmp_path, _SIGNOFF.split("  [signoff.fingerprint]")[0])
    assert unpinned.freshness(record)[0] is Freshness.UNPINNED

    assert fresh.freshness(_record(item_id="rafter/RF-HOUSE", kind="rafter",
                                   key="RF-HOUSE"))[0] is Freshness.UNSEALED


def test_an_item_with_no_calculation_can_be_stamped_but_never_pinned(tmp_path) -> None:
    """The trussed-roof case, and the reason the two gates are separate.

    ``rafter/RF-GARAGE`` is designed by its fabricator; this engine computes nothing for it,
    so there are no inputs to hash and no way to notice if the roof changes underneath the
    stamp. Recording the seal is right; letting it satisfy the final gate is not.
    """
    body = ('[[signoff]]\nid="TRUSS-01"\nscope="garage roof trusses"\n'
            'covers=["rafter/RF-GARAGE"]\nengineer="e"\nlicense="l"\n'
            'sealed_on="2026-01-01"\n')
    register = _write(tmp_path, body)
    state, signoff = register.freshness(no_calc("rafter", "RF-GARAGE"))
    assert signoff is not None and signoff.id == "TRUSS-01"
    assert state is Freshness.UNPINNED
    assert state is not Freshness.FRESH


# --- the gates --------------------------------------------------------------------------

def test_draft_passes_on_the_local_calc_and_sealed_does_not(catlin_plan, tmp_path) -> None:
    """The requirement the whole two-gate split exists for: draft approval is what permits a
    permit-ready printoff, and it must not wait on a professional signature."""
    from typehaus.checks import evaluate_permit_checklist, run

    report = run(catlin_plan, None, profile="mn-2024")
    checklist = evaluate_permit_checklist(report, "mn-2024")
    engineered = checklist.engineered
    assert engineered, "catlin has engineered requirements; the fixture is wrong if not"
    # Nothing is sealed in the repo, so the final gate is shut and every engineered line
    # says why.
    assert not checklist.sealed
    assert set(checklist.unsealed) == set(engineered)
    assert all(item.seal is Freshness.UNSEALED for item in engineered)


def test_a_context_with_no_suite_reads_as_no_calc_rather_than_raising() -> None:
    """Test fixtures build CheckContext-shaped objects by hand. A plain ``{}`` default would
    turn every one of them into a KeyError the moment a check delegated an item — a
    harness failure masquerading as a check bug."""
    from types import SimpleNamespace

    from typehaus.engineering.registry import records_of

    assert records_of(SimpleNamespace())["retaining_wall/X"].status is Status.NO_CALC
    assert records_of(SimpleNamespace(engineering={}))["k/X"].status is Status.NO_CALC


def test_the_results_map_is_lazy(catlin_plan) -> None:
    """``haus check --tier code`` must not pay to design a retaining wall."""
    from typehaus.resolve import resolve

    model, _ = resolve(catlin_plan)
    results = EngineeringResults(EngineeringContext(plan=catlin_plan, model=model,
                                                    soil_class="GM"))
    assert results._records == {}  # constructing it computed nothing
    results["retaining_wall/W-SG-E2"]
    assert results._records  # and asking computed only that kind
