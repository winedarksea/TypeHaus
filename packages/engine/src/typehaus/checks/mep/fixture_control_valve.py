"""UPC 606.5 / 606.6: a control valve immediately ahead of each supply that needs one.

Oracle: ``houses/catlin/notes/supply_isolation_basis.md`` §3. Each supply connection (one
per fixture per system) is walked upstream (``resolve/supply_valves``):

- an appliance, or a slip-joint fixture supply (lavatory, sinks), needs a valve before any
  tee — or, on a parallel run, a valved outlet of a readily accessible manifold;
- any other fixture (WC, shower, tub) needs one only when its run is parallel: the walk
  reaches the outlet of a home-run manifold (every outlet feeds one fixture, no tee
  downstream) without meeting a tee. A branch manifold whose outlets tee is a trunk;
- the valve found must be ``accessible`` (606.6).

A port is the valve of the one connection its run feeds, which is its label; a port whose run
tees to a second fixture is never reached, because the tee is met first.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import EquipmentKind, Occupancy
from typehaus.resolve.plumbing_tables import FIXTURE_CLASS_BY_SYMBOL
from typehaus.resolve.room_lookup import room_owning
from typehaus.resolve.supply_valves import connections, isolation_of, supply_tree

CID = "mep.fixture_control_valve"
_CODE = "MN Plumbing Code (ch. 4714) 606.5"
_SLIP_JOINT = {"lavatory", "bar sink", "kitchen sink", "laundry sink"}
_APPLIANCE = {"clothes washer", "dishwasher"}


def _kind(element, fixture_types) -> str:
    """``appliance`` / ``slip_joint`` / ``other`` for 606.5's two named classes."""
    if element is None:
        return "other"
    if element.element_kind in {"Appliance", "Equipment"}:
        return "appliance"
    fixture_type = fixture_types.get(getattr(element, "type_ref", None) or "")
    label = FIXTURE_CLASS_BY_SYMBOL.get(getattr(fixture_type, "plan_symbol", None) or "")
    if label in _APPLIANCE:
        return "appliance"
    return "slip_joint" if label in _SLIP_JOINT else "other"


def _home_run_manifolds(tree, equipment) -> set[str]:
    """Water manifolds no outlet run of which tees: a parallel system, not a branch header.
    A water heater's outlet is a source, never a manifold."""
    sourced: dict[str, bool] = {}
    for run, port in tree.source_port.items():
        tag = port.split(".", 1)[0]
        if getattr(equipment.get(tag), "kind", None) is not EquipmentKind.WATER_MANIFOLD:
            continue
        sourced[tag] = sourced.get(tag, True) and not tree.children.get(run)
    return {tag for tag, single in sourced.items() if single}


def _usable_port(ctx, port: str, equipment, home_run: set[str]) -> str | None:
    """None when the outlet can stand as the control valve, else why it cannot."""
    tag = port.split(".", 1)[0]
    element = equipment.get(tag)
    if getattr(element, "kind", None) is not EquipmentKind.WATER_MANIFOLD:
        return f"{tag} is a source, not a manifold"
    if tag not in home_run:
        return f"{tag} is a branch header (an outlet run tees), not a parallel system"
    types = {t.tag: t for t in ctx.plan.library.equipment_types}
    machine = types.get(getattr(element, "type_ref", None) or "")
    if machine is None or not machine.valved_outlets:
        return f"{tag}'s outlets carry no valves"
    obj = next((o for o in ctx.model.canvas_objects if o.tag == tag), None)
    room = None if obj is None or not obj.footprint else room_owning(
        ctx.model, obj.storey, (sum(p[0] for p in obj.footprint) / len(obj.footprint),
                                sum(p[1] for p in obj.footprint) / len(obj.footprint)))
    if room is None or room.occupancy == Occupancy.UNCONDITIONED.value:
        return f"{tag} is not readily accessible (no conditioned room owns it)"
    return None


@check(Tier.CODE, CID)
def fixture_control_valve(ctx: CheckContext) -> list[Finding]:
    tree = supply_tree(ctx.model)
    elements = {e.tag: e for e in ctx.plan.all_elements()}
    fixture_types = {t.tag: t for t in ctx.plan.library.fixture_types}
    if not tree.runs:
        named = sorted(t for t, e in elements.items() if e.element_kind == "Fixture"
                       and _kind(e, fixture_types) != "other")
        if named:  # N/A is earned only by the absence of what 606.5 names
            return [unknown(CID, f"{len(named)} lav/sink/appliance fixtures but no water "
                                 "supply runs to read their valves from", tuple(named),
                            code=_CODE)]
        return [not_applicable(CID, "no lav, sink or appliance fixture and no supply runs",
                               code=_CODE)]
    equipment = {t: e for t, e in elements.items() if e.element_kind == "Equipment"}
    accessories = {a.tag: a for a in ctx.model.pipe_accessories}
    home_run = _home_run_manifolds(tree, equipment)
    picked: dict[tuple[str, str], tuple[str, str]] = {}
    for run_tag, target in connections(ctx.model, tree):
        key = (target, tree.runs[run_tag].system)
        # A riser overrun past its last tee also ends; the run naming the fixture alone wins.
        if key not in picked or len(tree.runs[run_tag].serves or ()) == 1:
            picked[key] = (run_tag, target)
    out: list[Finding] = []
    for (target, system), (run_tag, _) in sorted(picked.items()):
        kind = _kind(elements.get(target), fixture_types)
        found = isolation_of(tree, run_tag, target)
        side = system.replace("water_", "")
        what = f"{target} ({side}, {run_tag})"
        if found.valve:
            valve = accessories[found.valve]
            if kind == "other":
                continue  # a stop 606.5 does not ask for: the owner's (WC flood stops)
            if not valve.accessible:
                out.append(failed(CID, f"{what}: {valve.tag} is not accessible (606.6)",
                                  (target, valve.tag), code="MN Plumbing Code (ch. 4714) 606.6",
                                  fix="make the valve reachable, or mark it accessible"))
            else:
                out.append(passed(CID, f"{what}: {valve.tag} immediately ahead",
                                  (target, valve.tag), code=_CODE))
        elif found.port and (kind != "other" or found.port.split(".", 1)[0] in home_run):
            why = _usable_port(ctx, found.port, equipment, home_run)
            if why is None:
                out.append(passed(CID, f"{what}: parallel run, valved outlet {found.port} "
                                       "on a readily accessible manifold", (target,), code=_CODE))
            else:
                out.append(failed(CID, f"{what}: parallel run from {found.port}, {why}, and "
                                       "no valve ahead of the fixture", (target, run_tag),
                                  code=_CODE, fix="a stop at the fixture, or a valved manifold"))
        elif kind != "other":
            reason = (f"tees to {found.blocked_by} first" if found.blocked_by
                      else "meets no valve before its source")
            out.append(failed(CID, f"{what}: a {kind.replace('_', '-')} supply with no valve "
                                   f"immediately ahead; the walk upstream {reason}",
                              (target, run_tag), code=_CODE,
                              fix="add a SHUTOFF on the fixture's own supply"))
    if not out:
        out.append(passed(CID, "no supply connection here is one 606.5 names", code=_CODE))
    return out
