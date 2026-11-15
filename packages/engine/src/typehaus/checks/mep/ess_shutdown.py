"""``electrical.ess_emergency_shutdown`` — 706.15(B) and 480.7(A)/(B) for a dwelling's battery.

706.15(B): a dwelling's ESS has an emergency shutdown that stops export to premises wiring,
started from a readily accessible outdoor device that shows off or on. Read here from the
inverter type's ``rsd_shutdown_scope`` (what the maker's manual says opening its RSD loop
stops) and the outdoor ``rsd_initiator`` device. 480.7(A) wants a dc disconnect only over
60 V (``battery_nominal_voltage_v``); 480.7(B)'s outdoor EMERGENCY DISCONNECT is graded as
met by that initiator and its derived label, the AHJ's reading of (B) staying open.
706.15(D)(1): a separate, field-serviced battery has a disconnect for every ungrounded
conductor within sight of it: met by the pack's own breaker where its type states
``battery_disconnect_all_ungrounded``, else by a ``DISCONNECT`` device on the battery's circuit
in sight (a plan line with no wall across, as ``electrical.hvac_disconnect`` reads it), else
UNKNOWN. Not graded: readily accessible, the off/on indication (a product fact).
See ``docs/code-notes/nec-2026-paraphrase-480-706.md``.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.nec import NEC, cite
from typehaus.resolve.room_lookup import room_owning

CID = "electrical.ess_emergency_shutdown"
_DC_DISCONNECT_OVER_V = 60.0  # 480.7(A)


@check(Tier.ADVISORY, CID)
def ess_emergency_shutdown(ctx: CheckContext) -> list[Finding]:
    eq_types = {t.tag: t for t in ctx.plan.library.equipment_types}
    equipment = [e for e in ctx.plan.all_elements() if e.element_kind == "Equipment"]
    batteries = sorted((e for e in equipment
                        if getattr(eq_types.get(e.type_ref or ""), "storage_kwh", None)),
                       key=lambda e: e.tag)
    if not batteries:
        return [not_applicable(CID, "no battery (storage_kwh) is placed, so there is no ESS",
                               code=cite(NEC.ESS_EMERGENCY_SHUTDOWN))]
    buildings = ctx.plan.project.buildings
    if buildings and not any(b.kind == "dwelling" for b in buildings):
        return [not_applicable(CID, "no building is a dwelling; 706.15(B)'s outdoor shutdown "
                                    "and 480.7(B) are dwelling rules",
                               code=cite(NEC.ESS_EMERGENCY_SHUTDOWN))]
    dev_types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    outdoor = [o.tag for o in sorted(ctx.model.canvas_objects, key=lambda o: o.tag)
               if getattr(dev_types.get(o.type_ref or ""), "rsd_initiator", False)
               and room_owning(ctx.model, o.storey, o.position) is None]
    inverters = [e for e in equipment
                 if getattr(eq_types.get(e.type_ref or ""), "inverter_kw_continuous", None)]
    out = [_shutdown(inverters, eq_types, outdoor)]
    for battery in batteries:
        out.extend(_battery(ctx, battery, eq_types, inverters, outdoor))
        out.append(_battery_disconnect(ctx, battery, eq_types))
    return out


def _battery_disconnect(ctx, battery, eq_types) -> Finding:
    """706.15(D)(1): the pack's own breaker, or an authored disconnect within sight."""
    from shapely.geometry import Point, Polygon

    from typehaus.checks.mep.electrical_spa_geometry import _separated, _walls
    from typehaus.model.enums import DeviceKind

    code = cite(NEC.ESS_BATTERY_DISCONNECT)
    if getattr(eq_types.get(battery.type_ref or ""), "battery_disconnect_all_ungrounded", None):
        return passed(CID, f"{battery.tag}: its own breaker opens every ungrounded conductor "
                           "(the maker's manual), on the battery, so within sight",
                      (battery.tag,), code)
    objects = {o.tag: o for o in ctx.model.canvas_objects}
    body = objects.get(battery.tag)
    seen = [d.tag for d in ctx.plan.all_elements()
            if d.element_kind == "ElectricalDevice" and d.kind is DeviceKind.DISCONNECT
            and battery.circuit and d.circuit == battery.circuit and body is not None
            and d.tag in objects and objects[d.tag].storey == body.storey
            and not _separated(Polygon(body.footprint), Point(objects[d.tag].position),
                               _walls(ctx, body.storey))]
    if seen:
        return passed(CID, f"{battery.tag}: {', '.join(sorted(seen))} on its circuit is in "
                           "sight of it", (battery.tag, *sorted(seen)), code)
    return unknown(CID, f"{battery.tag}: the type does not state that its breaker opens every "
                        "ungrounded conductor, and no disconnect on its circuit is in sight",
                   (battery.tag,), code,
                   "author battery_disconnect_all_ungrounded from the manual, or a disconnect")


def _scope(inverter, eq_types) -> tuple[str, ...] | None:
    return getattr(eq_types.get(inverter.type_ref or ""), "rsd_shutdown_scope", None)


def _shutdown(inverters, eq_types, outdoor) -> Finding:
    code = cite(NEC.ESS_EMERGENCY_SHUTDOWN)
    tags = tuple(sorted(e.tag for e in inverters)) + tuple(outdoor)
    if not inverters:
        return unknown(CID, "a battery is placed but no inverter, so what stops its export is "
                            "not modelled", tags, code)
    unstated = [e.tag for e in inverters if _scope(e, eq_types) is None]
    if unstated:
        return unknown(CID, f"{', '.join(unstated)}: what opening the RSD loop stops is not "
                            "authored (rsd_shutdown_scope), so the ESS shutdown is unknown",
                       tags, code, "author rsd_shutdown_scope from the inverter's manual")
    short = [e.tag for e in inverters if not {"ac_output", "ess"} <= set(_scope(e, eq_types))]
    if short:
        return failed(CID, f"{', '.join(short)}: its RSD loop does not stop both the ac output "
                           "and the ESS, so no device performs 706.15(B)'s shutdown", tags,
                      code, fix="an ESS emergency stop the maker supports, wired outdoors")
    if not outdoor:
        return failed(CID, "no rsd_initiator device stands outdoors to start the ESS "
                           "shutdown", tags, code, fix="put the initiator on an exterior face")
    return passed(CID, f"{', '.join(outdoor)} (outdoors) opens the RSD loop, which stops "
                       f"{', '.join(sorted(e.tag for e in inverters))}'s ac output and its ESS",
                  tags, code)


def _battery(ctx, battery, eq_types, inverters, outdoor) -> list[Finding]:
    volts = getattr(eq_types.get(battery.type_ref or ""), "battery_nominal_voltage_v", None)
    tags = (battery.tag,)
    if volts is None:
        return [unknown(CID, f"{battery.tag}: no battery_nominal_voltage_v, so 480.7(A)'s 60 V "
                             "test is unknown", tags, cite(NEC.BATTERY_DISCONNECT))]
    if volts > _DC_DISCONNECT_OVER_V:
        out = [unknown(CID, f"{battery.tag} is {volts:g} V dc, over 60 V: a dc disconnect "
                            "within sight is required and none is modelled", tags,
                       cite(NEC.BATTERY_DISCONNECT))]
    else:
        out = [not_applicable(CID, f"{battery.tag} is {volts:g} V dc nominal, not over 60 V, so "
                                   "480.7(A) asks for no dc disconnect", tags,
                              cite(NEC.BATTERY_DISCONNECT))]
    code = cite(NEC.BATTERY_EMERGENCY_DISCONNECT)
    remote = [e.tag for e in inverters if "ess" in (_scope(e, eq_types) or ())]
    labelled = {lb.host_ref for lb in ctx.model.electrical_labels
                if lb.section == NEC.BATTERY_EMERGENCY_DISCONNECT}
    hosts = [t for t in outdoor if t in labelled]
    if remote and hosts:
        out.append(passed(CID, f"{battery.tag}: {', '.join(hosts)} is an outdoor remote control "
                               f"that opens the ESS through {', '.join(remote)}, labelled "
                               "EMERGENCY DISCONNECT (derived, E-605); whether the AHJ applies "
                               "480.7(B) below 60 V stays open", tags + tuple(hosts), code))
    else:
        out.append(unknown(CID, f"{battery.tag}: no outdoor device is shown to disconnect the "
                                "battery, should the AHJ apply 480.7(B) below 60 V", tags, code))
    return out
