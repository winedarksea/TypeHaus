"""A proposal is text a person pastes. **There is no ``--write``, and there never will be.**

Three reasons, and the third is fatal on its own:

1. ``source/loader._content_hash`` hashes every ``plan/**/*.py``, so a machine edit stales
   every pinned engineering seal in the house. A router that silently invalidates a PE's
   stamp is not a convenience.
2. The prose in a plan file **is the design record.** ``houses/catlin/plan/mep_drainage.py``
   opens with thirty lines saying why the kitchen drain goes where it does; a write-back
   would preserve those lines while making them false, which is worse than deleting them.
3. **Accepting a route is a judgement.** ``haus engineering --fingerprint`` already prints
   a value for a person to paste for exactly this reason, and this is the same shape of
   act: the engine computes, the person commits.

The literal is built through :func:`~typehaus.source.serialize.value_source`, which already
handles ``Point2D`` and ``Length`` and is therefore **dialect-legal by construction** — a
1-tuple gets its trailing comma, nothing emits a ``frozenset``, and no operator appears in
a value. Coordinates are snapped to 1/16" **before** the feasibility re-check, so what is
printed is what was verified rather than what was found and then rounded.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from typehaus.quantities import M_PER_IN, Length, Point2D, ft, inch

#: The grid every printed coordinate lands on. A sixteenth is what this house authors to
#: and what a tape measures; printing a route to a millimetre would be claiming a precision
#: the framing does not have.
SNAP_IN = 1.0 / 16.0


def snap(metres: float) -> float:
    """One coordinate onto the 1/16" grid."""
    return round(metres / M_PER_IN * (1.0 / SNAP_IN)) * SNAP_IN * M_PER_IN


def length_source(metres: float) -> Length:
    """A ``Length`` whose authored unit is the one this house writes.

    ``ft(f, i)`` above zero, ``inch(x)`` below it — and the second half is not a style
    choice. ``ft(f, i)`` is ``f * 12 + i``, so a negative elevation cannot be written that
    way at all: ``ft(-7, 10)`` now raises and ``ft(-0, 8)`` is caught by
    ``dialect.mixed_sign_ft``. A basement invert is a negative number, and printing one as
    a feet-inches pair is how a proposal becomes an un-loadable file.
    """
    total_in = round(metres / M_PER_IN * (1.0 / SNAP_IN)) * SNAP_IN
    if total_in < 12:
        # Under a foot — a diameter, a jog, a negative invert — reads as inches and only
        # as inches. Below zero it is not a style question at all: see above.
        return inch(total_in)
    feet = int(total_in // 12)
    rem = round(total_in - feet * 12, 6)
    return ft(feet, rem) if rem else ft(feet)


@dataclass
class RouteProposal:
    """One proposed run: its polyline, its elevations, and where its cost went.

    ``terms`` is the cost breakdown in inches of equivalent travel — the whole content of
    ``--explain``, and the reason this class carries it rather than only the answer. A
    router that cannot say why it chose a line is one nobody will take a line from.
    """

    tag: str
    kind: str  # "pipe" | "duct" | "conduit"
    points: list[tuple[float, float, float]]
    diameter_m: float
    serves: tuple[str, ...] = ()
    system: str = "drain"
    cost: float = 0.0
    bends: int = 0
    terms: dict[str, float] = field(default_factory=dict)
    #: Free-form lines the caller wants printed with the proposal — a legalisation notice,
    #: a head-budget shortfall, a firestop somebody has to detail. Never silent.
    notes: list[str] = field(default_factory=list)

    def snapped(self) -> RouteProposal:
        """The same proposal on the 1/16" grid, with collinear vertices already collapsed.

        Snapping can make two vertices coincide; a repeated plan point carrying two
        elevations is a legal vertical leg and is kept, and a point repeated at the same
        elevation is dropped because two points at one place are one point.
        """
        points: list[tuple[float, float, float]] = []
        for x, y, z in self.points:
            candidate = (snap(x), snap(y), snap(z))
            if points and points[-1] == candidate:
                continue
            points.append(candidate)
        return RouteProposal(
            tag=self.tag, kind=self.kind, points=points, diameter_m=self.diameter_m,
            serves=self.serves, system=self.system, cost=self.cost, bends=self.bends,
            terms=dict(self.terms), notes=list(self.notes))

    def developed_ft(self) -> float:
        total = 0.0
        for a, b in zip(self.points, self.points[1:], strict=False):
            total += (sum((b[i] - a[i]) ** 2 for i in range(3))) ** 0.5
        return total / 0.3048

    def source(self, *, storey_datum_m: float = 0.0) -> str:
        """The constructor a person pastes, in dialect source.

        ``storey_datum_m`` subtracts the storey the run will be **filed on**, because
        ``PipeRun.elevations`` are storey-relative while a route is solved in project
        coordinates. Getting that wrong is silent — memory's "pipe elevations are
        storey-relative" — so it is a required decision at the call site rather than a
        default that happens to be right for ``main``.

        No ``uid=``. ``haus fmt`` mints one, and a hand-written uid is the one thing this
        repo's own rules forbid outright.
        """
        from typehaus.source.serialize import value_source

        path = tuple(Point2D(length_source(x), length_source(y))
                     for x, y, _z in self.points)
        elevations = tuple(length_source(z - storey_datum_m)
                           for _x, _y, z in self.points)
        lines = [
            f'{_CONSTRUCTOR[self.kind]}(tag="{self.tag}", '
            f"system={_system_source(self.kind, self.system)},",
            *_wrapped("path", path),
            f"        diameter={value_source(length_source(self.diameter_m))},",
            *_wrapped("elevations", elevations),
        ]
        if self.serves:
            lines.append(f"        serves={value_source(self.serves)}),")
        else:
            lines[-1] = lines[-1].rstrip(",") + "),"
        return "\n".join(lines)

    def explain(self) -> list[str]:
        """The cost breakdown, biggest term first, in one unit."""
        out = [f"{self.tag}: {self.developed_ft():.2f} ft developed, {self.bends} bend(s), "
               f'{self.cost:.0f}" equivalent']
        for key, value in sorted(self.terms.items(), key=lambda kv: -abs(kv[1])):
            out.append(f'    {key:16s} {value:+9.1f}"')
        out.extend(f"    NOTE {line}" for line in self.notes)
        return out


_CONSTRUCTOR = {"pipe": "PipeRun", "duct": "DuctRun", "conduit": "ConduitRun"}

#: The repo's line length. A proposal that has to be reflowed before it will pass `ruff` is
#: a proposal somebody edits before pasting, and an edited paste is where a typo enters.
_WIDTH = 96


def _wrapped(name: str, values: Iterable[object]) -> list[str]:
    """``name=(a, b, c)`` over as many 8-space-indented lines as it takes.

    A 1-tuple keeps its trailing comma — ``value_source`` puts it there and this must not
    strip it. The editable dialect needs it and ``build --inspect`` is what says so.
    """
    from typehaus.source.serialize import value_source

    items = [value_source(v) for v in values]
    if len(items) == 1:
        items[0] += ","
    lines, current = [], f"        {name}=("
    for index, item in enumerate(items):
        piece = item + ("," if index < len(items) - 1 or len(items) == 1 else "")
        if len(current) + len(piece) + 1 > _WIDTH and current.strip() != f"{name}=(":
            lines.append(current.rstrip())
            current = " " * (9 + len(name))
        current += piece + (" " if index < len(items) - 1 else "")
    lines.append(current.rstrip() + "),")
    return lines


def _system_source(kind: str, system: str) -> str:
    enum = {"pipe": "PipeSystem", "duct": "DuctSystem", "conduit": "Service"}[kind]
    return f"{enum}.{system.upper()}"


def render(proposals: Sequence[RouteProposal], *, storey_datum_m: float = 0.0,
           explain: bool = False) -> str:
    """The whole printout: a banner nobody can mistake for a file, then the constructors.

    The banner is not decoration. A block of dialect source in a terminal looks exactly
    like a file, and the one thing a reader must not conclude is that it has been written
    anywhere.
    """
    lines = [
        "# --- PROPOSED, NOT WRITTEN " + "-" * 50,
        "# Nothing on disk changed. Paste what you accept into the house's own "
        "`# haus: editable`",
        "# file, then run `haus fmt` to mint uids. Coordinates are on the 1/16\" grid and "
        "the",
        "# feasibility above was checked AFTER snapping, so this is what was verified.",
        "",
    ]
    for proposal in proposals:
        if explain:
            lines.extend(f"# {line}" for line in proposal.explain())
        lines.append(proposal.source(storey_datum_m=storey_datum_m))
        lines.append("")
    return "\n".join(lines)
