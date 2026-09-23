"""Does a ventilator that feeds an air handler's ducts run only with that blower turning?

An ERV that injects into an air handler's return hands its fresh air to the AH's own
distribution. With the AH blower off the air still enters, but it leaves through the nearest
low-resistance path (catlin: the return grille into one study) instead of reaching the rooms
the whole-house rate was counted for. So the delivered ventilation depends on a CONTROL
SEQUENCE: the ventilator's interlock contacts call the air handler's fan (IRC M1505.4's
"associated ducts and controls"; N1103.6 / MN 1322 R403.5 for the rate those controls make
real). Ventilator manuals wire it as a furnace/air-handler interlock for exactly this case.

The sequence is authored, never inferred: ``Equipment.blower_interlock_ref`` names the other
unit, on either machine. The COUPLING is derived — a walk over the duct graph from the
ventilator through runs, plenums and mixing boxes until it reaches an air handler — because
"these ducts connect" is geometry the model already holds.

Coupled and interlocked: PASS. Coupled with no interlock: UNKNOWN — the code does not
prescribe a relay, but without one the counted rate is not shown to reach the rooms. A ref
naming nothing: FAIL. No ventilator, or one reaching no air handler: N/A, earned by the walk.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import EquipmentKind

CID = "mep.erv_blower_interlock"
CODE = "IRC M1505.4 / N1103.6 (MN 1322 R403.5); ventilator installation manual"

#: Machines whose blower carries a distribution a ventilator can ride.
AIR_HANDLERS = frozenset({EquipmentKind.AIR_HANDLER, EquipmentKind.DUCTED_AIR_HANDLER,
                          EquipmentKind.FURNACE})
#: Boxes air passes THROUGH: a walk continues across them rather than stopping.
_PASSIVE = frozenset({EquipmentKind.DUCT_MANIFOLD, EquipmentKind.MIXING_BOX})


@dataclass(frozen=True)
class Coupling:
    """One ventilator and the air handlers its ducts reach."""

    erv: str
    air_handlers: tuple[str, ...]
    interlocked: tuple[str, ...]  # the subset an authored interlock covers

    @property
    def missing(self) -> tuple[str, ...]:
        return tuple(t for t in self.air_handlers if t not in self.interlocked)


def _equipment(ctx: CheckContext) -> dict[str, object]:
    return {el.tag: el for el in ctx.plan.all_elements() if el.element_kind == "Equipment"}


def _graph(ctx: CheckContext) -> dict[tuple[str, str], set[tuple[str, str]]]:
    """Undirected adjacency over ``("d", duct)`` and ``("e", canvas object)`` nodes: every
    duct end joined to the machine it lands in and to the run it tees into — the same two
    joint tests ``mep.duct_connectivity`` grades."""
    from typehaus.checks.mep.duct_connectivity import _meets_another_duct, equipment_at_end

    adj: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    for duct in ctx.model.ducts:
        if len(duct.path) < 2:
            continue
        node = ("d", duct.tag)
        for index in (0, -1):
            z = duct.z_m[index] if duct.z_m and len(duct.z_m) == len(duct.path) else None
            for other in (("e", equipment_at_end(ctx, z, duct.path[index])),
                          ("d", _meets_another_duct(ctx, duct, z, duct.path[index]))):
                if other[1] is not None:
                    adj[node].add(other)
                    adj[other].add(node)
    return adj


def _reached_air_handlers(adj, kinds: dict[str, EquipmentKind], start: str) -> set[str]:
    seen = {("e", start)}
    queue = deque([("e", start)])
    found: set[str] = set()
    while queue:
        for nxt in adj.get(queue.popleft(), ()):
            if nxt in seen:
                continue
            seen.add(nxt)
            kind = kinds.get(nxt[1]) if nxt[0] == "e" else None
            if kind in AIR_HANDLERS:
                found.add(nxt[1])  # arrived; its own ducts are its distribution, not ours
            elif nxt[0] == "d" or kind in _PASSIVE:
                queue.append(nxt)
    return found


def couplings(ctx: CheckContext, adj=None) -> list[Coupling]:
    """Every ventilator in the plan with the air handlers its duct network reaches."""
    units = _equipment(ctx)
    kinds = {tag: el.kind for tag, el in units.items()}
    ervs = sorted(tag for tag, kind in kinds.items() if kind is EquipmentKind.ERV)
    if not ervs:
        return []
    adj = _graph(ctx) if adj is None else adj
    out = []
    for erv in ervs:
        reached = tuple(sorted(_reached_air_handlers(adj, kinds, erv)))
        own = units[erv].blower_interlock_ref
        covered = tuple(ah for ah in reached
                        if own == ah or units[ah].blower_interlock_ref == erv)
        out.append(Coupling(erv, reached, covered))
    return out


def uninterlocked(ctx: CheckContext) -> list[Coupling]:
    """The couplings some reached air handler's blower is not interlocked with."""
    return [c for c in couplings(ctx) if c.missing]


def blower_dependent_ducts(ctx: CheckContext) -> dict[str, str]:
    """``{duct tag: ERV tag}`` for an un-interlocked air handler's own runs — the ducts
    whose fresh air arrives only when a blower nobody has tied to the ventilator turns.
    The walk from the AH stops at every machine, so it stays on the AH's side of the mix."""
    adj = _graph(ctx)
    out: dict[str, str] = {}
    for c in couplings(ctx, adj):
        for ah in c.missing:
            seen, queue = {("e", ah)}, deque([("e", ah)])
            while queue:
                for nxt in adj.get(queue.popleft(), ()):
                    if nxt[0] == "d" and nxt not in seen:
                        seen.add(nxt)
                        out.setdefault(nxt[1], c.erv)
                        queue.append(nxt)
    return out


@check(Tier.CODE, CID)
def erv_blower_interlock(ctx: CheckContext) -> list[Finding]:
    """A ventilator ducted into an air handler's distribution names that blower's interlock."""
    units = _equipment(ctx)
    out: list[Finding] = []
    for tag, unit in sorted(units.items()):
        ref = getattr(unit, "blower_interlock_ref", None)
        if ref is not None and ref not in units:
            out.append(failed(CID, f"{tag}.blower_interlock_ref={ref!r} names no Equipment",
                              (tag,), CODE))
    found = couplings(ctx)
    if not found:
        return out or [not_applicable(CID, "this plan holds no ERV/HRV, so no ventilator "
                                           "rides an air handler's blower", (), CODE)]
    for c in found:
        if not c.air_handlers:
            out.append(not_applicable(CID, f"{c.erv}'s duct network reaches no air handler; "
                                           "its own fan distributes its air", (c.erv,), CODE))
        elif c.missing:
            out.append(unknown(
                CID, f"{c.erv} ducts into {', '.join(c.missing)}'s distribution but no "
                "blower interlock is recorded; with that blower off its fresh air does not "
                "reach the rooms it was counted for", (c.erv, *c.missing), CODE,
                fix=f"wire the ventilator's interlock to the air handler's fan call and "
                    f"author blower_interlock_ref={c.missing[0]!r} on {c.erv}"))
        else:
            out.append(passed(CID, f"{c.erv} runs only with {', '.join(c.air_handlers)}'s "
                                   "blower (blower_interlock_ref)", (c.erv,), CODE))
    return out
