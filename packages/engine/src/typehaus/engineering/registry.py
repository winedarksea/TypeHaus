"""The suite's registry and its lazily-memoising result map.

Deliberately *not* a ``Tier.ENGINEERING`` inside ``checks/registry.py``, for two reasons
that pull the same way. ``run_checks`` is a flat loop with no ordering, so a prescriptive
check that needed an engineering result first would force two registry passes and an
implicit dependency between tiers. And the output is not a :class:`Finding` at all: it is a
calculation record with numbers in it, which ``Finding`` cannot hold.

The map is lazy. ``haus check --tier code`` must not pay to design a retaining wall, and
nothing here runs until a check asks for an item by id.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field

from typehaus.engineering.item import EngineeringRecord, Status, item_id, no_calc
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedModel


@dataclass(frozen=True)
class EngineeringContext:
    """What every calculation is allowed to read.

    The plan, the resolved model, and the house's preferences — the same three a check
    gets, minus the jurisdiction profile. A calculation is against a *standard*, not against
    a local amendment: ACI 318 does not change when the city does, and a calc that read the
    profile would be a prescriptive check wearing engineering clothes.
    """

    plan: PlanModel
    model: ResolvedModel
    preferences: object = None
    #: The site's declared soil group (IRC Table R405.1 symbol). A *site fact*, passed in as
    #: a bare string rather than by handing the calc the jurisdiction profile it happens to
    #: be stored on. The distinction is load-bearing: a calculation is against a standard,
    #: and one that could read the profile would be a prescriptive check wearing engineering
    #: clothes — ACI 318 and IBC 1806.2 do not change when the city does. ``None`` is never
    #: defaulted around; a calc that needs it reports INCOMPLETE naming it.
    soil_class: str | None = None


#: ``kind`` -> the function that enumerates and computes every item of that kind.
_CALCS: dict[str, Callable[[EngineeringContext], list[EngineeringRecord]]] = {}
#: ``kind`` -> the function that enumerates the *keys* of that kind without computing them.
#: A kind may register only this, which is how ``rafter/RF-GARAGE`` exists as an item with
#: no calculation behind it: the item has to be nameable before anyone can seal it.
_KEYS: dict[str, Callable[[EngineeringContext], list[str]]] = {}


def calc(kind: str) -> Callable[
        [Callable[[EngineeringContext], list[EngineeringRecord]]],
        Callable[[EngineeringContext], list[EngineeringRecord]]]:
    """Register the calculation for one limit-state family."""

    def deco(fn):  # type: ignore[no-untyped-def]
        _CALCS[kind] = fn
        return fn

    return deco


def keys(kind: str) -> Callable[
        [Callable[[EngineeringContext], list[str]]],
        Callable[[EngineeringContext], list[str]]]:
    """Register the *enumeration* for one kind, separately from its arithmetic.

    Split from :func:`calc` on purpose. An item that this engine will never compute — a
    trussed roof, where the fabricator's sealed design governs — still has to appear in the
    register, in ``haus engineering``, and on the permit line, or the outstanding work is
    invisible again. Registering keys without a calc is how it does.
    """

    def deco(fn):  # type: ignore[no-untyped-def]
        _KEYS[kind] = fn
        return fn

    return deco


def registered_kinds() -> tuple[str, ...]:
    return tuple(sorted(set(_CALCS) | set(_KEYS)))


@dataclass
class EngineeringResults(Mapping[str, EngineeringRecord]):
    """Every engineering item this house has, computed on first ask and then remembered.

    A ``Mapping`` so a check can write ``ctx.engineering[item]`` and ``item in
    ctx.engineering`` without learning a second vocabulary. Asking for an item of a kind
    nobody registered a calculation for yields a ``NO_CALC`` record rather than a
    ``KeyError`` — the whole point is that "an engineer owns this" is a state, not an error.
    """

    context: EngineeringContext
    _records: dict[str, EngineeringRecord] = field(default_factory=dict)
    _done: set[str] = field(default_factory=set)

    def _run(self, kind: str) -> None:
        if kind in self._done:
            return
        self._done.add(kind)
        for key in _KEYS.get(kind, lambda _ctx: [])(self.context):
            self._records.setdefault(item_id(kind, key), no_calc(kind, key))
        for record in _CALCS.get(kind, lambda _ctx: [])(self.context):
            self._records[record.item_id] = record

    def _resolve_all(self) -> None:
        for kind in registered_kinds():
            self._run(kind)

    def __getitem__(self, key: str) -> EngineeringRecord:
        kind = key.split("/", 1)[0]
        self._run(kind)
        record = self._records.get(key)
        if record is not None:
            return record
        element = key.split("/", 1)[1] if "/" in key else key
        return no_calc(kind, element)

    def __contains__(self, key: object) -> bool:
        """Whether a *computed or enumerated* item exists under this id.

        ``__getitem__`` never raises, so this is the question a caller actually has:
        "did the suite produce anything for this?", not "will the lookup work?".
        """
        if not isinstance(key, str):
            return False
        self._run(key.split("/", 1)[0])
        return key in self._records

    def __iter__(self) -> Iterator[str]:
        self._resolve_all()
        return iter(sorted(self._records))

    def __len__(self) -> int:
        self._resolve_all()
        return len(self._records)

    @property
    def unresolved(self) -> tuple[EngineeringRecord, ...]:
        """Items with no local calculation, or one that could not finish."""
        self._resolve_all()
        return tuple(record for _id, record in sorted(self._records.items())
                     if record.status in (Status.NO_CALC, Status.INCOMPLETE))


class _NoEngineering(Mapping[str, EngineeringRecord]):
    """An empty result map that answers every lookup with NO_CALC instead of raising.

    The default for :class:`CheckContext.engineering`, and the fallback ``engineered()``
    uses for a hand-built context. A plain ``{}`` would be the obvious default and is the
    wrong one: a check delegating an item would then raise ``KeyError`` in every unit test
    that constructs its own context, which is a test-harness failure masquerading as a
    check bug. "Nobody registered a calculation for this" is a real state with a real
    record, and it is the honest answer for a context that carries no suite at all.
    """

    def __getitem__(self, key: str) -> EngineeringRecord:
        kind, _, element = key.partition("/")
        return no_calc(kind, element or key)

    def __contains__(self, key: object) -> bool:
        return False

    def __iter__(self) -> Iterator[str]:
        return iter(())

    def __len__(self) -> int:
        return 0


#: One shared instance — it is stateless.
NO_ENGINEERING = _NoEngineering()


def records_of(ctx: object) -> Mapping[str, EngineeringRecord]:
    """The engineering results on a context, tolerating one that carries none.

    Test fixtures build ``CheckContext``-shaped objects by hand (a ``SimpleNamespace`` with
    four attributes), and demanding they all learn about the engineering suite to exercise
    an unrelated rule would be the framework taxing every caller for a feature they do not
    use. A context with no results, or with a plain dict, reads as NO_CALC.
    """
    results = getattr(ctx, "engineering", None)
    if isinstance(results, EngineeringResults):
        return results
    if results is None or not isinstance(results, Mapping) or not results:
        return NO_ENGINEERING
    return results
