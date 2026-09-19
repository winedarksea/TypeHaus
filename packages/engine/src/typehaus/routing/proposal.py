"""A proposal is text a person pastes. **There is no ``--write``, and there never will be.**

Two reasons, and the second is fatal on its own. **There used to be a third and it was
false:** "``_content_hash`` hashes every ``plan/**/*.py``, so a machine edit stales every
pinned engineering seal." It does not. A seal is pinned against
``engineering/fingerprint.fingerprint(record)`` — scheme, kind, key, ``basis_version``, the
record's rounded inputs and its ratio — and ``content_hash`` is not one of them;
``fingerprint``'s own docstring says hashing the model was rejected for exactly this reason.
``_content_hash`` reaches printed prose (``takeoff/handoff.py``, ``calc_package.py``,
``calc_pdf.py``) and the UI's optimistic-concurrency revision (``source/coordinator.py``),
and nothing else. What actually stales a seal is **moving geometry or elevations** — which a
route proposal would do, so the concern was real and only the mechanism was wrong.

1. The prose in a plan file **is the design record.** ``houses/catlin/plan/mep_drainage.py``
   opens with thirty lines saying why the kitchen drain goes where it does; a write-back
   would preserve those lines while making them false, which is worse than deleting them.
2. **Accepting a route is a judgement.** ``haus engineering --fingerprint`` already prints
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
from typing import TYPE_CHECKING

from typehaus.quantities import M_PER_IN, Length, Point2D, ft, inch

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel

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
    #: Rectangular duct section. Both zero for anything round, and a duct that carries both
    #: a diameter and a width would be an element ``integrity.duct_run_section`` refuses —
    #: so exactly one of the two is ever printed.
    width_m: float = 0.0
    depth_m: float = 0.0
    #: Where the winning legs actually rode, filled from ``Route.corridor_tags``. A duct
    #: claiming ``routing=JOIST_BAY`` and a ``floor_ref`` it never entered is the one kind
    #: of proposal that passes a plan reader and fails ``mep.duct_bay_occupancy``.
    routing: str | None = None
    floor_ref: str | None = None
    soffit_ref: str | None = None
    #: Extra constructor keywords to echo verbatim — a raceway's ``from_ref``/``to_ref``.
    echo: dict[str, str] = field(default_factory=dict)
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
            terms=dict(self.terms), notes=list(self.notes), width_m=self.width_m,
            depth_m=self.depth_m, routing=self.routing, floor_ref=self.floor_ref,
            soffit_ref=self.soffit_ref, echo=dict(self.echo))

    def developed_ft(self) -> float:
        total = 0.0
        for a, b in zip(self.points, self.points[1:], strict=False):
            total += (sum((b[i] - a[i]) ** 2 for i in range(3))) ** 0.5
        return total / 0.3048

    def source(self, *, storey_datum_m: float = 0.0) -> str:
        """The constructor a person pastes, in dialect source.

        ``storey_datum_m`` subtracts the storey the run will be **filed on**, because
        ``PipeRun.elevations`` and ``DuctRun.elevations`` are storey-relative while a route
        is solved in project coordinates. Getting that wrong is silent — memory's "pipe
        elevations are storey-relative" — so it is a required decision at the call site
        rather than a default that happens to be right for ``main``.

        **A raceway ignores it.** ``ConduitRun``'s elevations are project-frame absolute
        (``model/mep.py``), so subtracting a datum from them would move the run by a storey
        and nothing would say so.

        No ``uid=``. ``haus fmt`` mints one, and a hand-written uid is the one thing this
        repo's own rules forbid outright.
        """
        if self.kind == "conduit":
            return self._conduit_source()
        from typehaus.source.serialize import value_source

        path = tuple(Point2D(length_source(x), length_source(y))
                     for x, y, _z in self.points)
        elevations = tuple(length_source(z - storey_datum_m)
                           for _x, _y, z in self.points)
        lines = [
            f'{_CONSTRUCTOR[self.kind]}(tag="{self.tag}", '
            f"system={_system_source(self.kind, self.system)},",
            *_wrapped("path", path),
        ]
        if self.width_m or self.depth_m:
            lines.append(f"        width={value_source(length_source(self.width_m))}, "
                         f"depth={value_source(length_source(self.depth_m))},")
        else:
            lines.append(
                f"        diameter={value_source(length_source(self.diameter_m))},")
        lines.extend(_wrapped("elevations", elevations))
        if self.routing:
            lines.append(f"        routing=DuctRouting.{self.routing.upper()},")
        for name, value in (("floor_ref", self.floor_ref),
                            ("soffit_ref", self.soffit_ref),
                            *sorted(self.echo.items())):
            if value:
                lines.append(f'        {name}="{value}",')
        if self.serves:
            lines.append(f"        serves={value_source(self.serves)},")
        lines[-1] = lines[-1].rstrip(",") + "),"
        return "\n".join(lines)

    def _conduit_source(self) -> str:
        """ONE ``ConduitRun``, with a z at every vertex.

        **This used to split the route into one element per flat plane**, because a raceway
        was a plan polyline plus two end elevations and "it rises at its last vertex" was
        the only profile the model could express. A route with two changes of height was
        therefore not one element, and ``trades/conduit.legalize`` cut it into several.

        ``ConduitRun.elevations`` retired that. A raceway now states a height at every
        vertex, exactly as ``PipeRun`` and ``DuctRun`` do, so a route with five changes of
        elevation is one run with five elevations — which is what it is on site, and what
        makes ``mep.run_interference`` able to grade it at all rather than reporting it as
        a schematic coverage gap.

        **Project-frame absolute, and no datum subtraction.** The duct and pipe emitter
        above subtracts the storey datum because those two author storey-relative
        elevations; a ``ConduitRun``'s are absolute, because a trunk crosses storeys and a
        panel-to-attic riser has no one storey to be relative to. Subtracting here was the
        one thing that would have made a pasted proposal silently wrong.
        """
        from typehaus.source.serialize import value_source

        path = tuple(Point2D(length_source(x), length_source(y))
                     for x, y, _z in self.points)
        elevations = tuple(length_source(z) for _x, _y, z in self.points)
        lines = [f'ConduitRun(tag="{self.tag}",', *_wrapped("path", path),
                 f"        trade_size={value_source(length_source(self.diameter_m))},",
                 *_wrapped("elevations", elevations),
                 f"        service={_system_source('conduit', self.system)},"]
        for name, value in sorted(self.echo.items()):
            lines.append(f'        {name}="{value}",')
        lines[-1] = lines[-1].rstrip(",") + "),"
        return "\n".join(lines)

    def as_dict(self, *, storey_datum_m: float = 0.0) -> dict:
        """Contract 2 of the roadmap: the network proposal, as JSON-able data.

        Both the **structured** geometry and the **source** a person pastes, because the two
        readers are different: an agent wants points and diameters it can reason about, and a
        person wants the constructor. Emitting only one of them makes the other reader
        re-derive it, and a re-derivation is a place for the two to drift.
        """
        return {
            "tag": self.tag, "kind": self.kind, "system": self.system,
            "points_m": [list(p) for p in self.points],
            "diameter_m": self.diameter_m,
            "width_m": self.width_m, "depth_m": self.depth_m,
            "serves": list(self.serves),
            "routing": self.routing, "floor_ref": self.floor_ref,
            "soffit_ref": self.soffit_ref,
            "developed_ft": round(self.developed_ft(), 4),
            "bends": self.bends,
            "cost_in_equivalent": round(self.cost, 4),
            "terms_in": {k: round(v, 4) for k, v in sorted(self.terms.items())},
            "notes": list(self.notes),
            # Contract 2 names the parts as well as the line: an agent choosing between two
            # alternatives needs to know one of them needs a fitting nobody stocks.
            "fittings": [
                {"vertex": record.index, "angle_deg": round(record.angle_deg, 2),
                 "order_key": record.order_key,
                 "catalog": record.spec.tag if record.spec is not None else None,
                 "gap": record.gap}
                for record in self.fittings()],
            "source": self.source(storey_datum_m=storey_datum_m),
        }

    def fittings(self) -> list:
        """Every fitting this lane's corners would take, as shared records.

        The same derivation that will bill the run once it is pasted
        (:mod:`typehaus.resolve.mep_fittings`), run on the proposal's own snapped polyline —
        so "this route needs three 1/4 bends and one turn nobody makes a part for" is
        answerable *before* the paste rather than at the next take-off. A route that costs
        two bends less and takes a fitting that does not exist is not the cheaper route.
        """
        from typehaus.resolve.mep_fittings import FAMILY_DUCT, FAMILY_PIPE, polyline_fittings

        if len(self.points) < 3:
            return []
        family = FAMILY_DUCT if self.kind == "duct" else FAMILY_PIPE
        rectangular = self.width_m > 0.0 or self.depth_m > 0.0
        size = max(self.width_m, self.depth_m) if rectangular else self.diameter_m
        if size <= 0.0:
            return []
        return polyline_fittings(self.tag, family, self.system, self.points, size,
                                 rectangular=rectangular)

    def fitting_lines(self) -> list[str]:
        """What ``--explain`` and the proposal banner print about the parts.

        Silent when every corner names a catalogued pattern: a route that takes four 1/4
        bends takes four 1/4 bends, and saying so on every proposal trains the reader to
        skip the block that matters.
        """
        records = [record for record in self.fittings() if record.spec is None]
        return [f"FITTING at vertex {record.index} ({record.angle_deg:.1f}°): {record.gap}"
                for record in records]

    def explain(self) -> list[str]:
        """The cost breakdown, biggest term first, in one unit."""
        out = [f"{self.tag}: {self.developed_ft():.2f} ft developed, {self.bends} bend(s), "
               f'{self.cost:.0f}" equivalent']
        for key, value in sorted(self.terms.items(), key=lambda kv: -abs(kv[1])):
            out.append(f'    {key:16s} {value:+9.1f}"')
        out.extend(f"    NOTE {line}" for line in self.notes)
        out.extend(f"    {line}" for line in self.fitting_lines())
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
        elif proposal.fitting_lines():
            # Printed even without ``--explain``: a corner no catalogued pattern makes is
            # not a cost breakdown, it is something the person pasting has to decide about.
            lines.extend(f"# {line}" for line in proposal.fitting_lines())
        lines.append(proposal.source(storey_datum_m=storey_datum_m))
        lines.append("")
    return "\n".join(lines)


# --- what a proposal may CLAIM about where it is concealed ---------------------------
#
# Read back out of the corridors the winning legs actually rode, never asserted. These sat
# in ``cli/cmd_route`` and are routing knowledge: what a ``<floor>:bay@<station>`` tag means
# is this package's own spelling, and a second reader of it in the CLI is a second place for
# it to drift.
def concealment(model: ResolvedModel, corridor_tags: tuple[str, ...]
                 ) -> tuple[str | None, str | None, str | None]:
    """``(routing, floor_ref, soffit_ref)`` from the lanes the winning legs actually rode.

    A bay corridor is tagged ``<floor>:bay@<station>`` and a soffit corridor is the
    soffit's own tag, so the claim a proposal makes about where it is concealed is read
    back out of the search rather than asserted. A route that rode neither says
    ``EXPOSED``, which is what it is; claiming ``JOIST_BAY`` with no bay under it is the
    one proposal that reads well and fails ``mep.duct_bay_occupancy``.
    """
    soffits = {s.tag for s in model.soffits}
    bay = next((t for t in corridor_tags if ":bay@" in t), None)
    if bay is not None:
        return ("joist_bay", bay.split(":", 1)[0], None)
    soffit = next((t for t in corridor_tags if t in soffits), None)
    if soffit is not None:
        return ("soffit", None, soffit)
    return ("exposed", None, None)


def bay_note(model: ResolvedModel, corridor_tags: tuple[str, ...],
              radius_m: float) -> str | None:
    """``duct.bay_occupancy_note`` for the channel the route rode, if it is a tight one."""
    from typehaus.routing.corridors import floor_corridors, soffit_corridors
    from typehaus.routing.trades import duct as duct_trade

    by_tag = {c.tag: c for c in (*floor_corridors(model), *soffit_corridors(model))}
    for tag in corridor_tags:
        corridor = by_tag.get(tag)
        if corridor is None:
            continue
        note = duct_trade.bay_occupancy_note(corridor, radius_m)
        if note:
            return note
    return None
