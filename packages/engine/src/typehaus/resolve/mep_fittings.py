"""Every fitting a run takes, derived once — the reading the take-off, the checks, the IFC
emitter and the router's proposal all share.

A run's geometry states where it turns and where another run joins it. What gets *installed*
at each of those points is a part, and until this module existed the answer was derived
three times over and agreed nowhere: ``takeoff/plumbing.fitting_takeoff`` counted elbows off
``sweep_turns`` and snapped them to three angles, ``emit/ifc/mep.py`` emitted no fitting at
all, and the router's proposal printed a polyline whose corners nobody had priced.

**Two questions, deliberately kept apart.** A vertex asks *what does this cost to buy* and
*what part is it*, and they are not the same question:

* :attr:`FittingRecord.order_key` is the take-off's answer — the row a turn is billed on. It
  is the key the take-off has always used and ``houses/*/prices.toml`` is keyed on, and it
  is unchanged here on purpose: a made bend is billed as two elbows whether or not a catalog
  row exists for the angle.
* :attr:`FittingRecord.spec` is the catalog's answer — the ASTM/ASME pattern that makes this
  turn, or ``None`` with :attr:`FittingRecord.gap` saying why not.

They disagree on catlin today and the disagreement is the point: ``elbow-22.5-1in`` is a
priced row for a part ASME B16.22 does not make. Merging the two would have buried that.

**A bendable service is not a fitting service.** Copper and PEX turn by being bent, to a
radius the *product* bounds; DWV and rigid duct turn by being fitted. A turn off a stock
angle therefore means something different in each, so :attr:`FittingRecord.bendable` carries
which one it is and the grading reads it.

Stdlib only, like the rest of ``resolve/``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typehaus.hardware.fittings import (
    KIND_ELBOW,
    KIND_TEE,
    KIND_WYE,
    SERVICE_DRAIN,
    SERVICE_DUCT,
    SERVICE_SUPPLY,
    SERVICE_VENT,
    FittingSpec,
    catalogued_angles,
    catalogued_sizes,
    fitting_catalog,
    fitting_for,
)
from typehaus.quantities import M_PER_IN
from typehaus.resolve.sweep import clean_path, sweep_turns

if TYPE_CHECKING:
    from typehaus.resolve.model import ResolvedModel

#: A run's ``system`` as the model spells it, mapped to the service the catalog is keyed on.
#: ``water_hot`` and ``water_cold`` are one service to a fitting supplier and two to a price
#: list, which is exactly why the mapping is explicit rather than a prefix test.
SERVICE_BY_SYSTEM: dict[str, str] = {
    "drain": SERVICE_DRAIN,
    "vent": SERVICE_VENT,
    "water_hot": SERVICE_SUPPLY,
    "water_cold": SERVICE_SUPPLY,
}

#: Services whose turns are made by bending the product rather than by a fitting. A turn off
#: a stock angle in one of these is a *bend*, graded against a product's minimum radius —
#: which no source in this repo publishes, so it is a coverage gap and not a defect.
BENDABLE_SERVICES: frozenset[str] = frozenset({SERVICE_SUPPLY})

#: The smallest size ASTM D3311 makes a DWV pattern in, inches. A gravity line thinner than
#: this is not plumbed in DWV at all — a 3/4" condensate or T&P discharge runs in tube and
#: turns on a tube fitting — so grading one against the DWV catalog reports the absence of a
#: part nobody would have ordered. Catlin carried six such findings on that mistake.
MIN_DWV_SIZE_IN = 1.25

#: How much a *pitched* line widens a pressure fitting's snap by. A gravity run in tube still
#: falls, and the elbow at the bottom of a 2 in/ft leg measures 80.5 degrees rather than 90 —
#: the same allowance the DWV rows carry in their own ``snap_deg``.
PITCHED_SNAP_BONUS_DEG = 5.0

#: Below this a vertex is not a fitting at all: it is where a run changes grade, which is the
#: pipe flexing or two lengths glued straight. Half the smallest stock DWV bend, and the same
#: number ``fitting_takeoff`` has always used.
MIN_FITTING_TURN_DEG = 10.0

#: Which take-off bills a record. Two families rather than one because they are two BOM
#: sections priced by two trades, and a shared reading that lost track of which would make
#: the plumber's sheet carry the tinner's elbows.
FAMILY_PIPE = "pipe"
FAMILY_DUCT = "duct"


@dataclass(frozen=True)
class FittingRecord:
    """One fitting: where it is, what it turns, what it is billed as, and what part it is."""

    run_tag: str
    #: ``pipe`` or ``duct`` — which take-off bills this row, and which emitter draws it.
    family: str
    #: ``elbow``, ``wye`` or ``tee``.
    kind: str
    #: The catalog service (:data:`SERVICE_BY_SYSTEM`), or the run's own system where the
    #: model uses a system the catalog has never been keyed on.
    service: str
    #: The run's system exactly as the model spells it — what the price row is qualified by.
    system: str
    #: Vertex index on the run's cleaned path, for an elbow. ``None`` for a branch fitting,
    #: which belongs to the junction rather than to a vertex of either run.
    index: int | None
    point: tuple[float, float, float]
    angle_deg: float
    plan_angle_deg: float
    nominal_in: float
    branch_in: float | None
    #: The child run that arrives at a branch fitting. ``None`` for an elbow. A parent takes
    #: one of these per child, so it is what tells two branches on one main apart — a bare
    #: "this main's branch fitting" collided on catlin's building drain.
    branch_tag: str | None
    #: The take-off row this turn is billed on — unchanged from what the take-off has always
    #: produced, and what ``prices.toml`` is keyed on.
    order_key: str
    #: The catalogued pattern, or ``None``.
    spec: FittingSpec | None
    #: Why :attr:`spec` is ``None``, in the words a report prints. ``None`` when there is a
    #: spec.
    gap: str | None
    #: Whether this service turns by bending the product rather than by a fitting.
    bendable: bool

    @property
    def tag_for_report(self) -> str:
        """How a finding or a proposal names this fitting."""
        if self.index is not None:
            return f"{self.run_tag} at vertex {self.index}"
        return f"{self.run_tag} where {self.branch_tag} joins it"


#: Stock DWV/supply elbow angles the *order key* snaps to. This is the take-off's own list
#: and is deliberately NOT the catalog's: it decides a price row, and the catalog decides a
#: part. See this module's docstring.
_ORDER_STOCK_DEG = (90.0, 45.0, 22.5)
_ORDER_SNAP_DEG = 10.0
#: A made bend's angle is rounded to this before it becomes a row: 71.4 and 71.6 degrees are
#: one bend made twice, and 71 and 57 are not.
_ORDER_ROUND_DEG = 5.0


def size_text(diameter_m: float) -> str:
    """A diameter as it is *ordered*: ``4in``, ``1.5in``, ``0.75in``."""
    return f"{round(diameter_m / M_PER_IN, 2):g}in"


def order_key(angle_deg: float, diameter_m: float) -> str:
    """The row a turn is billed on: a stock elbow, or a made bend at its own angle.

    Moved here unchanged from ``takeoff/plumbing``, so the one derivation has one home. The
    bend carries its angle because a row that does not is unbuildable: catlin's ``bend-2in``
    was three turns of 71, 57 and 63 degrees, and the plumber making them off that line has
    been told the size and nothing else.
    """
    for stock in _ORDER_STOCK_DEG:
        if abs(angle_deg - stock) <= _ORDER_SNAP_DEG:
            return f"elbow-{stock:g}-{size_text(diameter_m)}"
    rounded = round(angle_deg / _ORDER_ROUND_DEG) * _ORDER_ROUND_DEG
    return f"bend-{rounded:g}-{size_text(diameter_m)}"


def _nominal_in(diameter_m: float) -> float:
    """Nominal size in inches, rounded the way a catalog key is — never a float compare."""
    return round(diameter_m / M_PER_IN, 3)


def _match(service: str, kind: str, angle_deg: float, nominal_in: float,
           branch_in: float | None, bendable: bool,
           snap_bonus_deg: float = 0.0) -> tuple[FittingSpec | None, str | None]:
    """The catalogued pattern for a turn, or ``None`` and the reason in report prose.

    Three distinct absences, and the prose says which, because they ask for three different
    things from whoever reads it: read a submittal, widen the catalog, or look at the run.
    """
    spec = fitting_for(service, kind, angle_deg, nominal_in, branch_in=branch_in,
                       snap_bonus_deg=snap_bonus_deg)
    if spec is not None:
        return spec, None
    sizes = catalogued_sizes(service, kind)
    if not sizes:
        return None, (f"no {service} {kind} is catalogued at any size — this service's "
                      f"fittings have never been read into library/fittings.py")
    if not any(abs(size - nominal_in) < 1e-6 for size in sizes):
        listed = ", ".join(f"{size:g}\"" for size in sizes)
        return None, (f"no {service} {kind} is catalogued at {nominal_in:g}\" — the "
                      f"catalogued sizes are {listed}")
    if branch_in is not None:
        branches = sorted({item.branch_in for item in fitting_catalog()
                           if item.service == service and item.kind == kind
                           and abs(item.nominal_in - nominal_in) < 1e-6
                           and item.branch_in is not None})
        if branches and not any(abs(b - branch_in) < 1e-6 for b in branches):
            listed = ", ".join(f"{b:g}\"" for b in branches)
            return None, (f"no {nominal_in:g}\" {service} {kind} is catalogued with a "
                          f"{branch_in:g}\" branch — the catalogued branches are {listed}")
    angles = catalogued_angles(service, kind)
    listed = ", ".join(f"{a:g}" for a in angles)
    if bendable:
        return None, (f"a {angle_deg:.1f} degree turn in {nominal_in:g}\" {service} is a "
                      f"BENT TUBE, not a fitting (B16.22 makes {listed} degrees), and no "
                      f"product minimum bend radius is on record to grade it against")
    return None, (f"no stock {service} {kind} turns {angle_deg:.1f} degrees at "
                  f"{nominal_in:g}\" — the catalogued patterns are {listed} degrees")


#: What a rectangular duct's turn is, and why it carries no catalog row: a rectangular elbow
#: is fabricated to the duct's own two dimensions and its throat radius, so there is no
#: catalog of patterns to match it against — only a shop drawing.
RECTANGULAR_DUCT_GAP = ("a rectangular duct elbow is fabricated to the duct, not ordered "
                        "from a pattern catalog — its throat radius comes off a shop "
                        "drawing and nothing here can stand in for one")


def polyline_fittings(tag: str, family: str, system: str,
                      points: Sequence[tuple[float, float, float]], size_m: float,
                      *, rectangular: bool = False) -> list[FittingRecord]:
    """The elbows a bare 3D polyline takes — for a run that is not in the model yet.

    The router proposes geometry before anybody has pasted it, and "what parts does this
    lane need" is a question about the lane, not about the house. So the reading is split:
    this walks a polyline, and :func:`fitting_records` is what feeds it the runs a resolved
    model holds. A proposal graded by a different derivation from the one that will bill it
    once pasted is the drift this module exists to stop.
    """
    from typehaus.resolve.model import SolidSweep

    service, bonus = ((SERVICE_DUCT, 0.0) if family == FAMILY_DUCT
                      else _pipe_service(system, _nominal_in(size_m)))
    bendable = service in BENDABLE_SERVICES
    nominal = _nominal_in(size_m)
    sweep = SolidSweep(path=clean_path(list(points)), profile=((size_m / 2.0, 0.0),))
    out: list[FittingRecord] = []
    for turn in sweep_turns(sweep):
        if turn.angle_deg < MIN_FITTING_TURN_DEG:
            continue  # a grade change, not a fitting
        if rectangular:
            spec, gap = None, RECTANGULAR_DUCT_GAP
        else:
            spec, gap = _match(service, KIND_ELBOW, turn.angle_deg, nominal, None,
                               bendable, bonus)
        out.append(FittingRecord(
            run_tag=tag, family=family, kind=KIND_ELBOW, service=service, system=system,
            index=turn.index, point=tuple(turn.point), angle_deg=turn.angle_deg,
            plan_angle_deg=turn.plan_angle_deg, nominal_in=nominal, branch_in=None,
            order_key=order_key(turn.angle_deg, size_m), spec=spec, gap=gap,
            bendable=bendable, branch_tag=None))
    return out


def _turn_records(run: Any, family: str, *, size_m: float,
                  rectangular: bool = False) -> list[FittingRecord]:
    z = getattr(run, "z_m", None)
    if z is None or len(z) != len(run.path):
        return []
    return polyline_fittings(
        run.tag, family, run.system,
        [(x, y, zz) for (x, y), zz in zip(run.path, z, strict=True)], size_m,
        rectangular=rectangular)


def _pipe_service(system: str, nominal_in: float) -> tuple[str, float]:
    """The catalog service a pipe run's turns are graded against, and its snap allowance.

    A gravity system below :data:`MIN_DWV_SIZE_IN` is **tube**, not DWV, however the model
    spells its ``system``: 3/4" is not a size D3311 patterns are made in, and a 3/4"
    condensate line is copper or CPVC turning on a tube fitting. It keeps a pitched line's
    snap allowance, because it is still a line that falls.
    """
    service = SERVICE_BY_SYSTEM.get(system, system)
    if service in (SERVICE_DRAIN, SERVICE_VENT) and nominal_in < MIN_DWV_SIZE_IN:
        return SERVICE_SUPPLY, PITCHED_SNAP_BONUS_DEG
    return service, 0.0


def fitting_records(model: ResolvedModel) -> list[FittingRecord]:
    """Every fitting on every pipe and duct run, in a stable order.

    Elbows come off the run's own 3D polyline — a vertical drop meeting a horizontal branch
    is the 90 degrees it actually is — and wyes off ``drain_tie_ins``' geometric parent
    inference, the same rollup ``mep.pipe_sizing`` uses, which yields *both* diameters so the
    branch is sized correctly rather than at the larger of the two.

    **Supply tees are not derived.** There is no equivalent parent inference for a
    pressurised system — a water branch has no invert to arrive above, so nothing
    distinguishes a tee from two runs crossing — and a guess recorded as a fitting is worse
    than an absence.
    """
    from typehaus.resolve.mep_queries import drain_tie_ins

    out: list[FittingRecord] = []
    for run in model.pipe_runs:
        out.extend(_turn_records(run, FAMILY_PIPE, size_m=run.diameter_m))
    for duct in model.ducts:
        rectangular = duct.diameter_m is None
        # The same size the duct take-off has always keyed its rows on: the diameter where
        # there is one, the larger plan dimension where there is not.
        size = duct.diameter_m if not rectangular else max(duct.width_m, duct.depth_m)
        out.extend(_turn_records(duct, FAMILY_DUCT, size_m=size,
                                 rectangular=rectangular))

    by_tag = {run.tag: run for run in model.pipe_runs}
    for child_tag, parent_tag in sorted(drain_tie_ins(model.pipe_runs).items()):
        child, parent = by_tag.get(child_tag), by_tag.get(parent_tag)
        if child is None or parent is None:
            continue
        run_in, branch_in = _nominal_in(parent.diameter_m), _nominal_in(child.diameter_m)
        service, bonus = _pipe_service(parent.system, run_in)
        # A tube-sized gravity branch is a tee, not a wye: B16.22 makes no wye, and a
        # condensate line tees into its neighbour.
        kind = KIND_WYE if service != SERVICE_SUPPLY else KIND_TEE
        spec, gap = _match(service, kind, 45.0 if kind == KIND_WYE else 90.0,
                           run_in, branch_in, False, bonus)
        point = _tie_point(child)
        out.append(FittingRecord(
            run_tag=parent_tag, family=FAMILY_PIPE, kind=kind, service=service,
            system=parent.system,
            index=None, point=point, angle_deg=45.0, plan_angle_deg=45.0,
            nominal_in=run_in, branch_in=branch_in,
            order_key=(f"wye-{size_text(parent.diameter_m)[:-2]}x"
                       f"{size_text(child.diameter_m)}"),
            spec=spec, gap=gap, bendable=False, branch_tag=child_tag))
    return out


def _tie_point(child: Any) -> tuple[float, float, float]:
    """Where a branch meets its parent: the child's last placed point.

    A tie-in has no vertex of its own in either polyline — the child simply ends on the
    parent — so the junction is located at the end the child arrives with, which is the point
    a finding needs to send somebody to.
    """
    if child.z_m is None or not child.path:
        return (0.0, 0.0, 0.0)
    (x, y), z = child.path[-1], child.z_m[-1]
    return (x, y, z)


def family_records(records: list[FittingRecord], family: str) -> list[FittingRecord]:
    """Just one take-off's records — ``FAMILY_PIPE`` or ``FAMILY_DUCT``."""
    return [record for record in records if record.family == family]


def takeoff_rows(records: list[FittingRecord]) -> list[dict[str, object]]:
    """The fitting take-off's rows, rolled up by system and order key.

    Identical in shape and in key to what ``fitting_takeoff`` has always emitted — so
    ``prices.toml`` still joins — with two columns added: the catalogued part this row's
    turns are, and the coverage gap where there is none. A row whose turns disagree (some
    matched, some not) reports ``None`` for the part and names the first gap, which is the
    conservative reading: a row is only a part when every turn on it is that part.
    """
    counts: dict[tuple[str, str], dict[str, object]] = {}
    for record in records:
        entry = counts.setdefault((record.system, record.order_key), {
            "count": 0, "tags": set(), "specs": set(), "gaps": [], "ungraded": 0})
        entry["count"] = int(entry["count"]) + 1
        tags, specs, gaps = entry["tags"], entry["specs"], entry["gaps"]
        assert isinstance(tags, set) and isinstance(specs, set) and isinstance(gaps, list)
        tags.add(record.run_tag)
        specs.add(record.spec.tag if record.spec is not None else None)
        if record.gap is not None:
            entry["ungraded"] = int(entry["ungraded"]) + 1
            if record.gap not in gaps:
                gaps.append(record.gap)

    rows: list[dict[str, object]] = []
    for (system, key), entry in sorted(counts.items()):
        specs = entry["specs"]
        assert isinstance(specs, set)
        gaps = entry["gaps"]
        assert isinstance(gaps, list)
        part = next(iter(specs)) if len(specs) == 1 else None
        tags = entry["tags"]
        assert isinstance(tags, set)
        rows.append({"system": system, "fitting": key, "count": int(entry["count"]),
                     "tags": sorted(tags), "catalog": part,
                     "gap": gaps[0] if gaps else None,
                     "ungraded": int(entry["ungraded"])})
    return rows
