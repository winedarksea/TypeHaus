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

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum

#: Below this a value is float noise from a solver, not a quantity.
_ZERO = 1e-9


def num(value: float, sig: int = 4) -> str:
    """``value`` to at least ``sig`` significant figures, comma-grouped, never an exponent.

    Here, in the leaf, so a calc module can format the numbers in its own working the same
    way the sheets format everything else (``takeoff/calc_numfmt`` re-exports it).
    """
    if not math.isfinite(value):
        return str(value)
    if abs(value) < _ZERO:
        return "0"
    decimals = min(12, max(0, sig - 1 - math.floor(math.log10(abs(value)))))
    text = f"{value:,.{decimals}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


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


class Scope(Enum):
    """How much of the QUESTION one record answers — orthogonal to :class:`Status`.

    ** ``Status.OK`` MEANS "EVERY LIMIT STATE THE MODULE ENUMERATED IS UNDER 1", AND THE
    BUNDLE'S README CALLED IT "computed ... with nothing missing". ** Those are different
    claims, and every calc sheet's own §9 contradicts the second on every page: "only the
    limit states listed in §4 are graded; a failure mode this engine does not enumerate is
    not evaluated here and is not implied to pass." A reviewer reading OK beside a
    completeness claim is being told something the sheet underneath them denies.

    ``Status`` cannot carry it. It has fifteen consumer sites plus a documented IFC Pset
    contract, three of which are exhaustive label maps that ``KeyError`` on a new member —
    and more importantly the two facts are genuinely independent: a record can be arithmetic-
    complete and scope-incomplete (every enumerated state passes, and the module enumerates
    four of the seven a design needs), or scope-complete and over (it grades the whole
    question and the answer is no). ``Freshness`` is the precedent: a fourth axis, carried
    beside the status rather than folded into it, and read by renderers only.

    Nothing gates on this. It is what the sheets and the README SAY, and the point is that
    what they say becomes true.
    """

    #: The module enumerates every limit state this design needs. Rare and worth earning.
    COMPLETE = "complete"
    #: The module grades a real subset and the sheet's §9 says which. The ordinary case, and
    #: the honest default: a screening tool is a screening tool.
    SCREENING = "screening"
    #: Somebody else designs this; the engine holds a name and a deliverable, not numbers.
    EXTERNAL = "external"


@dataclass(frozen=True)
class Oracle:
    """The independent hand-worked check behind a calculation — a citation, not an input.

    The root ``CLAUDE.md`` rule ("a calc that only agrees with itself is not verified") is
    satisfied today only in a Python module docstring, which is exactly where a reviewer
    holding the CLI output cannot see it. This is that reference made data, so the calc
    package can print "who checked this independently" beside every result.

    Deliberately **not** hashed by ``fingerprint.py``. A seal is a statement about the
    numbers a calculation consumed; staling one because somebody renamed a note or added a
    section reference would make the stamp mean less, not more.
    """

    #: File name under ``houses/<name>/notes/`` — the note, not a path, so the reference
    #: survives a house being copied or renamed.
    note: str
    #: Optional section within the note (``"§4"``), where only part of it oracles this calc.
    section: str = ""
    #: The test module that reproduces the note's arithmetic, when one exists.
    test: str = ""

    def __str__(self) -> str:
        return f"{self.note} {self.section}".rstrip()


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
    #: Plain words for the symbol ("retained height"). Not hashed. Empty falls back to the
    #: kind's :func:`declare_sheet` labels, then the package's own dictionary.
    label: str = ""

    def rounded(self) -> float:
        """The value as the fingerprint sees it."""
        if self.quantum is None or self.quantum <= 0:
            return float(self.value)
        return round(float(self.value) / self.quantum) * self.quantum

    def __str__(self) -> str:
        return f"{self.name} = {num(self.value)} {self.unit}".rstrip()


@dataclass(frozen=True)
class Step:
    """One line of a limit state's working: ``symbol = equation = numbers = value unit``.

    The sheet prints these in order, so a reviewer checks each number with a calculator and
    never opens the code (review E-02). The last steps must arrive at the state's demand and
    its capacity; a test holds every converted kind to that. Not hashed.
    """

    symbol: str
    #: Plain words: "largest bending moment over the snow patterns".
    meaning: str
    value: float
    unit: str = ""
    #: In symbols, ASCII/Latin-1 only (the PDF font): ``"w L^2 / 8"``. Empty for a value
    #: read straight off a table row.
    equation: str = ""
    #: The equation with numbers in, formatted with :func:`num`: ``"1,246 x 4.979^2 / 8"``.
    numbers: str = ""
    #: The clause, table row or method: ``"NDS 2018 Supplement Table 5A, 24F-V4 DF"``.
    source: str = ""

    def text(self) -> str:
        parts = [f"`{self.symbol}`"]
        parts += [p for p in (self.equation, self.numbers) if p]
        line = " = ".join(parts) + f" = **{num(self.value)}{' ' + self.unit if self.unit else ''}**"
        return line + (f" — {self.meaning}" if self.meaning else "") + (
            f" ({self.source})" if self.source else "")


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
    #: Set where the row is a prescriptive DETAILING rule — a bar count, a tie pitch, a
    #: minimum steel area — rather than a demand the structure has to carry.
    #:
    #: These rows are bounded above by 1.0 *when the design is compliant*, and they reach
    #: exactly 1.000 when it sits on the code minimum, which is the ordinary and desirable
    #: case. That makes them useless as a governing state: a blind ``max`` by ratio hands
    #: "bar count" the win over a real axial ratio of 0.04, and the sheet then tells a
    #: reviewer that a 12" column with 96% of its capacity spare is "controlled by bar
    #: count". No engineer would say that. They are still graded, still printed, and still
    #: fail the item when they go over — they are only excluded from ``governing``.
    is_detailing: bool = False
    #: The named load combination this demand came from, as a reviewer would cite it:
    #: ``"ASCE 7-22 2.4.1(6b) D + 0.75L + 0.75(0.6W)"``. Every sealed residential package
    #: sampled identifies the governing combination BY NUMBER at each member, because
    #: "the wind case" is not checkable and a numbered combination is — a reviewer can
    #: reproduce the factors from the standard without asking what was assumed.
    #:
    #: Empty is the honest default and is what almost every state carries today: this
    #: engine's kinds mostly compute one demand from one case, and writing a combination
    #: number beside a demand that was never combined would be a claim about the arithmetic
    #: that the arithmetic does not support. Populating it is per-kind work, and a kind that
    #: sets it is asserting the demand really is that combination.
    combination: str = ""
    #: The **machine-readable half** of ``combination``: the standard's own case letters
    #: (D, L, S, W, H, E) against their factors, e.g. ``(("W", 0.6),)`` for
    #: ``"ASCE 7-16 §2.4.1(7) 0.6W"``.
    #:
    #: ``combination`` is a citation written for a person and is not parseable in general:
    #: ``analytical/loads`` read the letters back out of the prose, which meant a clause
    #: number in front of the factors ("§2.4.1(7)") was indistinguishable from the factors,
    #: and the one combination catlin actually declares typed as unparseable and was
    #: **dropped in silence**. The analysis export then carried unit load cases and no
    #: combination at all, and nothing said so.
    #:
    #: Letters, not this engine's own case enum, because ``engineering`` is a leaf that
    #: ``analytical`` reads and not the other way round — and because the letter is what the
    #: standard prints, so a reviewer checks it against the clause without a mapping.
    combination_factors: tuple[tuple[str, float], ...] = ()
    #: The arithmetic behind ``demand`` and ``capacity``, in order — see :class:`Step`.
    working: tuple[Step, ...] = ()

    @property
    def ratio(self) -> float:
        if self.capacity == 0:
            return float("inf")
        return self.demand / self.capacity

    @property
    def ok(self) -> bool:
        return self.ratio <= 1.0


@dataclass(frozen=True)
class NotCovered:
    """One limit state or question this calculation does not grade, and who closes it.

    Review E-01: a stamp must say what it does not cover. Printed in the family sheet's
    last section and in the summary's owner table. Not hashed.
    """

    what: str
    why: str
    #: Who closes it, by role: "the sealing engineer", "the owner (stated basis)",
    #: "the truss fabricator", "the contractor at excavation".
    owner: str
    #: The deliverable or event that closes it.
    closes_by: str = ""


class BasisKind(Enum):
    """How a stated basis entered the design."""

    OWNER_BASIS = "owner's stated basis"
    OWNER_ACCEPTED = "owner-accepted"
    OWNER_READING = "owner's reading of a published row"
    SPECIFIED = "specified, not yet confirmed"


@dataclass(frozen=True)
class StatedBasis:
    """A design input that rests on a decision rather than on a code row or a measurement.

    One home for the owner's bases and acceptances (deck snow, the curtains, a catalog
    reading, an accepted ratio, specified soil), printed in the same table on every sheet
    that rests on it. Not hashed: changing the wording stales no seal.
    """

    kind: BasisKind
    subject: str
    statement: str
    #: What it leaves out, or what would bring it back to the owner.
    reopens_if: str = ""
    #: Where it is recorded: "owner decision 5", a catalog page and table revision.
    reference: str = ""


@dataclass(frozen=True)
class Figure:
    """A free-body sketch, drawn as monospace ASCII from the record's own numbers.

    ASCII so the markdown and the PDF print the same deterministic thing with no image
    pipeline; lines at most :data:`FIGURE_WIDTH` characters. ``engineering/sketch.py``
    draws the common shapes.
    """

    title: str
    lines: tuple[str, ...]
    caption: str = ""


FIGURE_WIDTH = 72


@dataclass(frozen=True)
class SheetSpec:
    """What a kind declares for its calculation sheet, beside the records it computes."""

    not_covered: tuple[NotCovered, ...] = ()
    bases: tuple[StatedBasis, ...] = ()
    #: Plain words per input name, for the symbol table.
    labels: Mapping[str, str] = field(default_factory=dict)
    #: ``record -> Figure``; called on each worked member. Must be deterministic.
    figure: Callable[[EngineeringRecord], Figure | None] | None = None


_SHEETS: dict[str, SheetSpec] = {}


def declare_sheet(kind: str, **spec: object) -> None:
    """Declare a kind's not-covered table, stated bases, labels and figure (see SheetSpec)."""
    _SHEETS[kind] = SheetSpec(**spec)  # type: ignore[arg-type]


def sheet_spec(kind: str) -> SheetSpec:
    return _SHEETS.get(kind, SheetSpec())


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
    #: The standard the calculation follows, printed on S-603 and in every finding.
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
    #: The hand-worked note(s) that independently reproduce this arithmetic. Prose, so it
    #: stays out of the fingerprint — see :class:`Oracle`.
    oracle: tuple[Oracle, ...] = ()
    #: How much of the QUESTION this record answers — see :class:`Scope`. Orthogonal to
    #: :attr:`status`, and deliberately defaulted to ``SCREENING`` rather than left None: a
    #: module that has not thought about it is screening, and saying so is the honest
    #: reading. **Not hashed by the fingerprint**, for the same reason ``oracle`` is not: a
    #: seal is a statement about numbers, and re-classifying a module's coverage should not
    #: stale a stamp over arithmetic that did not move.
    scope: Scope = Scope.SCREENING
    #: Member-specific exclusions and stated bases, on top of the kind's own
    #: (:func:`declare_sheet`). Not hashed.
    not_covered: tuple[NotCovered, ...] = ()
    bases: tuple[StatedBasis, ...] = ()

    def value(self, name: str) -> float | None:
        """An input's value by name, or ``None`` — what a figure reads."""
        return next((q.value for q in self.inputs if q.name == name), None)

    @property
    def governing(self) -> LimitState | None:
        """The worst CAPACITY limit state — what an engineer would name as controlling.

        Detailing rows are excluded (see :attr:`LimitState.is_detailing`): they sit at
        1.000 whenever the design meets the code minimum exactly, so including them means
        the answer to "what controls this column?" is always "bar count". Where an item has
        no capacity state at all — a pier whose axial demand could not be derived — this is
        ``None`` rather than the worst detailing row, because the honest answer there is
        that the section is ungraded, not that it is at 100%.
        """
        graded = [state for state in self.limit_states if not state.is_detailing]
        if not graded:
            return None
        return max(graded, key=lambda state: state.ratio)

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


def no_calc(kind: str, key: str, *, reason: str = "",
            oracle: tuple[Oracle, ...] = (), basis: str = "") -> EngineeringRecord:
    """The record for an item this build computes nothing for.

    Deliberately a *record* rather than an absence. ``rafter/RF-GARAGE`` is the case that
    makes the difference load-bearing: a trussed roof's fabricator design governs, this
    engine will never compute it, and the item must still exist so the seal has something
    to cover and the CLI has a row to print.
    """
    return EngineeringRecord(
        item_id=item_id(kind, key), kind=kind, key=key, status=Status.NO_CALC, basis=basis,
        summary=reason or "no calculation is registered for this kind — an engineer's "
                          "design governs",
        element_tags=(key,), oracle=oracle, scope=Scope.EXTERNAL,
    )
