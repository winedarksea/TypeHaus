"""IMC 2018 307.2.3 — auxiliary and secondary condensate drain systems.

Minnesota strikes the IRC's mechanical chapters and adopts the IMC (Minn. R. 1346.0050); the
IRC twin is M1411.3. Where overflow from the equipment pan, or a stopped condensate line,
would damage building components, each cooling coil or condensing appliance takes one of:

1. an auxiliary pan under the coil with its own drain to a conspicuous point;
2. an overflow line from the equipment's own pan, above the primary connection, to a
   conspicuous point;
3. an auxiliary pan with no drain, carrying a UL 508 water-level switch that shuts the
   equipment off before the pan overflows;
4. a UL 508 water-level switch in the primary pan or drain line that shuts it off.

``Equipment.secondary_drain_pan`` / ``overflow_drain_ref`` / ``float_switch_ref`` spell all
four. What is not graded: the conspicuousness of a termination, and the pan's size and depth
(307.2.3.2) — the model carries neither.
"""

from __future__ import annotations

from typehaus.checks._authoring import by_result
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import DuctSystem, EquipmentKind
from typehaus.model.placeables import MountKind
from typehaus.resolve.solid_categories import is_pour_slab

CID = "mep.condensate_overflow"
CODE = "MN Mechanical Code (Minn. R. 1346.0050, IMC 2018) 307.2.3"

#: Kinds carrying a cooling coil or a condensing burner. A wall-mount INDOOR_HEAD is left
#: out on purpose: its pan is integral to an exposed case in the room it serves, so overflow
#: shows at the case — enforcement there is the AHJ's call, not one this rule makes.
GRADED_KINDS = frozenset({EquipmentKind.AIR_HANDLER, EquipmentKind.DUCTED_AIR_HANDLER,
                          EquipmentKind.FURNACE})

#: A unit's base may sit this far below the deck top it stands on (mesh and finish noise).
_SEAT_TOLERANCE_M = 0.01


@check(Tier.CODE, CID)
def condensate_overflow(ctx: CheckContext) -> list[Finding]:
    """IMC 307.2.3 — every coil whose overflow would do damage has one of the four guards."""
    units = sorted((e for e in ctx.plan.all_elements()
                    if e.element_kind == "Equipment" and e.kind in GRADED_KINDS),
                   key=lambda e: e.tag)
    if not units:
        # A return duct implies a central unit the plan has not modeled — a gap, not absence.
        if any(d.system is DuctSystem.RETURN for d in ctx.plan.all_elements()
               if d.element_kind == "DuctRun"):
            return [by_result(CID, Result.UNKNOWN, "return ducts are modeled but no air "
                              "handler or furnace is", (), CODE)]
        return [by_result(CID, Result.NOT_APPLICABLE, "no air handler or furnace is modeled "
                          "and no return duct implies one", (), CODE)]
    equipment = {e.tag: e for e in ctx.plan.all_elements() if e.element_kind == "Equipment"}
    runs = {r.tag for r in ctx.model.pipe_runs}
    return [_grade(ctx, unit, equipment, runs) for unit in units]


def _grade(ctx: CheckContext, unit, equipment: dict, runs: set[str]) -> Finding:
    tag = unit.tag
    drain, switch = unit.overflow_drain_ref, unit.float_switch_ref
    if drain is not None and drain not in runs:
        return by_result(CID, Result.FAIL, f"{tag} names overflow_drain_ref {drain}, which "
                         "resolves to no pipe run", (tag, drain), CODE)
    if drain is not None and drain == unit.pan_drain_ref:
        return by_result(CID, Result.FAIL, f"{tag}'s overflow drain {drain} is its primary "
                         "condensate line; 307.2.3 asks for a separate one", (tag, drain), CODE,
                         "run the overflow as its own PipeRun, or author a float switch")
    if switch is not None:
        if switch not in equipment:
            return by_result(CID, Result.FAIL, f"{tag} names float_switch_ref {switch}, "
                             "which resolves to no equipment", (tag, switch), CODE)
        if switch not in (tag, unit.outdoor_ref):
            return by_result(CID, Result.FAIL, f"{tag}'s float switch shuts off {switch}, "
                             "which is neither this unit nor its outdoor unit, so a full pan "
                             "keeps making water", (tag, switch), CODE,
                             "name the unit itself or its outdoor_ref")

    pan = unit.secondary_drain_pan
    if drain is not None:
        where = "its auxiliary pan" if pan else "its own pan's overflow connection"
        return by_result(CID, Result.PASS, f"{tag}: {where} drains separately through "
                         f"{drain} (307.2.3 item {1 if pan else 2}; the termination's "
                         "conspicuousness is not graded)", (tag,), CODE)
    if switch is not None:
        where = "its auxiliary pan" if pan else "its primary pan or drain line"
        return by_result(CID, Result.PASS, f"{tag}: a water-level switch in {where} shuts "
                         f"off {switch} (307.2.3 item {3 if pan else 4})", (tag,), CODE)

    slab = _bare_slab_on_grade_under(ctx, unit)
    if slab is not None:
        return by_result(CID, Result.NOT_APPLICABLE, f"{tag} stands on {slab}, a bare "
                         "concrete slab with no floor beneath it — overflow there damages "
                         "no building component", (tag,), CODE)
    if pan:
        return by_result(CID, Result.FAIL, f"{tag} has an auxiliary pan with neither a drain "
                         "nor a water-level switch; 307.2.3 item 3 needs the switch",
                         (tag,), CODE, "author overflow_drain_ref or float_switch_ref")
    return by_result(CID, Result.UNKNOWN, f"{tag} names no auxiliary pan, overflow drain or "
                     "float switch, and nothing shows its overflow would be harmless",
                     (tag,), CODE, "author secondary_drain_pan with overflow_drain_ref, or "
                     "float_switch_ref")


def _bare_slab_on_grade_under(ctx: CheckContext, unit) -> str | None:
    """The tag of the bare pour slab a floor-standing unit sits on, when nothing is below it.

    Positive evidence only: floor-mounted, the surface under its base is a pour slab with no
    covering (a coating's 0" counts as bare), and no lower surface stands at the point.
    """
    from typehaus.resolve.walking_surface import surfaces_at

    if unit.mount.kind is not MountKind.FLOOR:
        return None
    placed = next((o for o in ctx.model.canvas_objects if o.uid == unit.uid), None)
    if placed is None:
        return None
    base = placed.body_z0_m if placed.body_z0_m is not None else placed.z_m
    surfaces = surfaces_at(ctx.model, placed.position)
    seated = [s for s in surfaces if s.deck_top_m <= base + _SEAT_TOLERANCE_M]
    if not seated:
        return None
    under = max(seated, key=lambda s: s.deck_top_m)
    if any(s.deck_top_m < under.deck_top_m - _SEAT_TOLERANCE_M for s in surfaces):
        return None  # something stands below this floor
    solid = next((s for s in ctx.model.solids if s.tag == under.deck_tag), None)
    if solid is None or not is_pour_slab(solid.category) or under.finish_in != 0.0:
        return None
    return under.deck_tag
