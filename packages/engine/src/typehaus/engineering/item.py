"""What an engineering calculation produces — the record, not a Finding.

A :class:`Finding` has nowhere to hold numbers. It carries a severity, a verdict and a
sentence, and that is the right shape for a rule that reads a table. It is the wrong shape
for the thing an engineer actually hands over, which is a demand, a capacity, a ratio, the
limit state that governed, and the clause each of those came from. Losing those to a string
is how a calculation stops being checkable — a reviewer cannot disagree with prose.

So the suite's output is an :class:`EngineeringRecord`, and a check turns one into a Finding
at the boundary (``checks/_authoring.engineered``). The record is what ``haus engineering``
prints term by term, and what the fingerprint is taken over.

This module is a leaf: it imports nothing from ``typehaus`` at all. The whole
``engineering`` package deliberately imports ``model``/``resolve``/``quantities``/``wind``
and **never** ``checks``, which is what lets ``CheckContext`` hold the results without a
cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Status(Enum):
    """What the suite was able to say about one item.

    ``NO_CALC`` is the state that makes adopting this framework safe. An item nobody has
    written a calculation for reports it, the check that delegates to the item reports
    UNKNOWN exactly as it did before the framework existed, and the permit gate stays shut
    in exactly the same way. What changes is that the outstanding work now has a *name*.
    """

    OK = "ok"                    # every limit state computed, and every ratio <= 1
    OVER = "over"                # computed, and something is over its capacity
    INCOMPLETE = "incomplete"    # the calc exists but an input it needs is missing
    NO_CALC = "no_calc"          # no calculation is registered for this kind


@dataclass(frozen=True)
class Quantity:
    """One number the calculation consumed or produced, with its unit *and its quantum*.

    ``quantum`` is the rounding step used when this value enters a fingerprint, and it is
    declared here rather than applied somewhere central so that the tolerance is reviewable
    beside the number it governs. Geometry re-derived through a solver carries float noise —
    a 7'-0" wall that comes back as ``2.1336000000000003`` metres is the same wall — and a
    seal that goes stale on the sixteenth decimal place is a seal nobody will trust.

    A quantum of ``None`` means the value is exact as written (a count, a class name).
    """

    name: str
    value: float
    unit: str
    quantum: float | None = None

    def rounded(self) -> float:
        """The value as the fingerprint sees it."""
        if self.quantum is None or self.quantum <= 0:
            return float(self.value)
        return round(float(self.value) / self.quantum) * self.quantum

    def __str__(self) -> str:
        return f"{self.name} = {self.value:,.4g} {self.unit}".rstrip()


@dataclass(frozen=True)
class LimitState:
    """One demand-vs-capacity comparison, with the clause it came from.

    ``ratio`` is demand over capacity, so >1 is over. A limit state expressed as a factor of
    safety (sliding, overturning) is converted to that convention at the point it is built,
    so that a reader comparing two rows of the same table is comparing like with like —
    ``required / achieved`` for a safety factor, ``demand / capacity`` for a strength.
    """

    name: str
    demand: float
    capacity: float
    unit: str
    citation: str
    #: Set where the number is a factor of safety rather than a force or a stress, so the
    #: CLI can letter it as "FS 1.62 >= 1.5" instead of a bare ratio nobody can place.
    is_safety_factor: bool = False

    @property
    def ratio(self) -> float:
        if self.capacity == 0:
            return float("inf")
        return self.demand / self.capacity

    @property
    def ok(self) -> bool:
        return self.ratio <= 1.0


@dataclass(frozen=True)
class EngineeringRecord:
    """The result of computing one item — ``<kind>/<element-tag>``.

    Identity is per *element*, never per group. One stamp covering three walls is the
    register's business (``register.py``); keeping the record per-element is what makes the
    fingerprint per-element too, so moving one wall stales that wall and leaves the other
    two alone.
    """

    item_id: str
    kind: str
    key: str
    #: Bumped by the calc module's author whenever the arithmetic changes. It rides in the
    #: fingerprint so a seal goes stale when *the calculation* changes, not only when the
    #: model does — a seal is against a computation, and silently swapping the computation
    #: under a valid-looking stamp is the failure this exists to prevent.
    basis_version: str = "0"
    #: The standard the calculation follows, printed on S-105 and in every finding.
    basis: str = ""
    summary: str = ""
    status: Status = Status.NO_CALC
    inputs: tuple[Quantity, ...] = ()
    limit_states: tuple[LimitState, ...] = ()
    #: Named inputs the calculation needed and did not get. Non-empty implies INCOMPLETE,
    #: and each name is printed so the reader learns *what to author*, not merely that
    #: something is absent.
    missing: tuple[str, ...] = ()
    #: Free-text notes from the calc — assumptions a reviewer is entitled to disagree with.
    notes: tuple[str, ...] = field(default_factory=tuple)
    #: Element tags this record covers, for the finding it becomes. Usually just ``key``.
    element_tags: tuple[str, ...] = ()

    @property
    def governing(self) -> LimitState | None:
        """The worst limit state — the one an engineer would name if asked what controls."""
        if not self.limit_states:
            return None
        return max(self.limit_states, key=lambda state: state.ratio)

    @property
    def ratio(self) -> float | None:
        governing = self.governing
        return None if governing is None else governing.ratio

    def describe(self) -> str:
        """The one-line "why" a finding appends after its own message."""
        governing = self.governing
        if governing is None:
            return self.summary or "no limit state computed"
        return (f"d/c = {governing.ratio:.2f}, governed by {governing.name} "
                f"({governing.citation})")


def item_id(kind: str, key: str) -> str:
    """``<kind>/<element-tag>`` — the one spelling of an item's identity."""
    return f"{kind}/{key}"


def no_calc(kind: str, key: str, *, reason: str = "") -> EngineeringRecord:
    """The record for an item this build computes nothing for.

    Deliberately a *record* rather than an absence. ``rafter/RF-GARAGE`` is the case that
    makes the difference load-bearing: a trussed roof's fabricator design governs, this
    engine will never compute it, and the item must still exist so the seal has something
    to cover and the CLI has a row to print.
    """
    return EngineeringRecord(
        item_id=item_id(kind, key), kind=kind, key=key, status=Status.NO_CALC,
        summary=reason or "no calculation is registered for this kind — an engineer's "
                          "design governs",
        element_tags=(key,),
    )
