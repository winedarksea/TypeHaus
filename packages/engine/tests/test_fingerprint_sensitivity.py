"""Every material input a calculation CONSUMES must move its fingerprint.

** THE DEFECT THIS EXISTS TO PREVENT A SECOND TIME. ** ``retaining_wall``'s ``inputs``
tuple was geometry and soil only, so editing ``W-SG-E2``'s mix from 5,000 psi to 4,000 moved
four capacities, left ``Status.OK`` standing and left the fingerprint hash unchanged. A
pinned seal survived a change to the very concrete it was a statement about — and the
governing limit state there is *sliding*, which no material term touches, so the record's
two-decimal ratio could not move either. Nothing in the suite would have found it: the
existing per-kind tests pin the numbers a calc PRODUCES, and this is about what it READS.

** WHY THIS IS A HARNESS AND NOT A TEST OF ONE KIND. ** The question — "is every value this
calculation consumed inside the digest a seal is pinned against?" — is the same question for
every registered kind, and asking it once per kind by hand is how the next kind repeats the
defect. So the model is perturbed at the SHARED readings every kind goes through
(``resolve/concrete.fc_psi``, ``resolve/concrete.cover_for``, ``model/rebar.BARS``), the
whole suite is re-run, and the contract is asserted over every record at once:

    **a record whose limit states moved must have a fingerprint that moved.**

That is the property, stated in the direction that matters. The converse is fine and is not
asserted: a fingerprint may move where no capacity does, which is exactly what happens to a
record whose inputs carry a term no limit state happens to be governed by — and pinning a
seal against MORE than governs it is the conservative direction.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch

import pytest
from _helpers import CATLIN

from typehaus.engineering.fingerprint import fingerprint, pinnable


def _suite(plan):
    """A fresh, unmemoised result map — the perturbation must not read a cached record."""
    from typehaus.checks.run import build_context

    ctx, _ = build_context(plan, CATLIN)
    return dict(ctx.engineering)


def _patched_everywhere(name: str, replacement):
    """Patch one ``resolve.concrete`` function at its source AND at every re-export.

    A module that did ``from typehaus.resolve.concrete import fc_psi`` holds its own
    reference, so patching only the source would leave that reader on the real function and
    the harness would silently prove nothing. The engineering package is walked rather than
    listed for the same reason the harness is generic at all.
    """
    import importlib
    import pkgutil

    import typehaus.engineering as pkg
    import typehaus.resolve.concrete as source

    targets = [(source, name)]
    for info in pkgutil.iter_modules(pkg.__path__):
        module = importlib.import_module(f"{pkg.__name__}.{info.name}")
        if getattr(module, name, None) is getattr(source, name):
            targets.append((module, name))
    return [patch.object(module, attr, replacement) for module, attr in targets]


@contextmanager
def _weaker_concrete():
    """Every specified f'c down 20%. Flexure, shear and axial capacity all read it."""
    import typehaus.resolve.concrete as source

    real = source.fc_psi

    def weaker(spec):
        value = real(spec)
        return None if value is None else value * 0.8

    patches = _patched_everywhere("fc_psi", weaker)
    for entry in patches:
        entry.start()
    try:
        yield
    finally:
        for entry in reversed(patches):
            entry.stop()


@contextmanager
def _deeper_cover():
    """Every specified cover +1/2". Cover comes off ``d`` directly, so it spends capacity."""
    import typehaus.resolve.concrete as source

    real = source.cover_for

    def deeper(plan, element):
        value, basis = real(plan, element)
        return (None if value is None else value + 0.5), basis

    patches = _patched_everywhere("cover_for", deeper)
    for entry in patches:
        entry.start()
    try:
        yield
    finally:
        for entry in reversed(patches):
            entry.stop()


_PERTURBATIONS = {
    "fc": _weaker_concrete,
    "cover": _deeper_cover,
}


def _one_size_smaller(plan):
    """A COPY of the plan with every authored bar one ASTM size down.

    A model edit, not a patched constant — and that distinction is the whole reason this is
    built this way. Shrinking ``model/rebar.BARS`` would move capacities too, but ``BARS``
    is a published table, the same class of thing as an ACI coefficient: a change there is a
    ``BASIS_VERSION`` bump, not a stale seal. A ``#5`` written down as a ``#4`` in a plan
    file is the model moving underneath a stamp, which is exactly what a fingerprint is for.

    Generic over the model rather than over the kinds: any element field holding a
    ``ReinforcementSpec`` is rewritten, so a kind added tomorrow that reads authored steel
    is covered the day it lands.
    """
    from typehaus.model.rebar import BARS, ReinforcementSpec

    smallest = min(BARS)

    def shrink(spec):
        bars = tuple(b.model_copy(update={"bar": max(b.bar - 1, smallest)})
                     for b in spec.bars)
        return spec.model_copy(update={"bars": bars})

    touched = 0
    out = plan
    for storey_tag, group in plan.elements.items():
        rebuilt = []
        for element in group:
            updates = {name: shrink(value)
                       for name, value in vars(element).items()
                       if isinstance(value, ReinforcementSpec)}
            if updates:
                touched += 1
                element = element.model_copy(update=updates)
            rebuilt.append(element)
        out = out.with_elements(storey_tag, rebuilt)
    assert touched, "no element in this house authors a ReinforcementSpec"
    return out


@pytest.fixture(scope="module")
def baseline(catlin_plan):
    return _suite(catlin_plan)


@pytest.mark.parametrize("name", sorted(_PERTURBATIONS))
def test_a_capacity_that_moves_moves_its_fingerprint(name, catlin_plan, baseline) -> None:
    with _PERTURBATIONS[name]():
        after = _suite(catlin_plan)
    _assert_digests_moved(name, baseline, after)


def test_a_smaller_authored_bar_moves_its_fingerprint(catlin_plan, baseline) -> None:
    """The reinforcement axis, perturbed in the MODEL — see :func:`_one_size_smaller`."""
    _assert_digests_moved("bar size", baseline, _suite(_one_size_smaller(catlin_plan)))


def _assert_digests_moved(name: str, baseline, after) -> None:

    moved_capacity: list[str] = []
    same_digest: list[str] = []
    for item_id, before in baseline.items():
        now = after.get(item_id)
        if now is None or not pinnable(before) or not pinnable(now):
            continue
        capacities_before = tuple((s.name, s.capacity) for s in before.limit_states)
        capacities_now = tuple((s.name, s.capacity) for s in now.limit_states)
        if capacities_before == capacities_now:
            continue
        moved_capacity.append(item_id)
        if fingerprint(before) == fingerprint(now):
            same_digest.append(item_id)

    assert moved_capacity, (
        f"perturbing {name} moved no capacity anywhere in the house — the harness is not "
        f"exercising anything and would pass whatever the inputs tuples said")
    assert not same_digest, (
        f"perturbing {name} moved these records' capacities and NOT their fingerprints, so "
        f"a seal pinned over them would still read FRESH: {sorted(same_digest)}")
