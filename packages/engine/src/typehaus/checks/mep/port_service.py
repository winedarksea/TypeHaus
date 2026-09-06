"""Does anything actually arrive at the ports a machine declares?

``mep.duct_connectivity`` grades duct *ends*: every run must land on something. That is one
half of the question and it is structurally blind to the other half — a machine that no run
was ever drawn to. Nothing lands on nothing, so nothing is reported. ``EQ-B-ERV`` stood in
the basement for a fortnight with four declared air ports and no duct to either manifold,
and every check in this engine passed: the runs that existed all landed correctly, and the
runs that did not exist could not be missed by a rule that iterates over runs.

This is the companion, iterating over *machines*. An :class:`~typehaus.model.types.
EquipmentType` states its ports — an ERV has four, a manifold one, a mixing box two — and a
port is a claim that something connects there. The claim is checkable: a duct of the right
system has to reach the case.

**Graded at the service level, not positionally.** A :class:`~typehaus.model.placeables.
ServicePort` carries a local ``position``, and matching a duct end against it would look
like the stronger rule. It is not: the Catlin ERV authors all four of its ports at the same
local ``(0, 0, 21.6")`` — "ports are all on top and all 6" round" — because the datasheet
gives a face, not four coordinates. A positional match against four coincident points is
vacuous, and a positional *tolerance* wide enough to be fair to that authoring is wider than
the case. So the port's station is *reported* (through ``rotate_into_plan``, the same
transform the plan symbols and the drain-drop resolver use) and the *verdict* is taken at
the service level: this machine declares supply air, and a SUPPLY run must reach it.

Two arrival strengths, in that order, and the order matters:

* a run whose **end** lands in the case. This is the ordinary connection and it is the one
  that carries information about direction: the four runs at EQ-B-ERV-MAN-EXH all end there
  and all of them are return/exhaust, which is how the check can tell that the exhaust
  manifold is carrying the *supply* manifold's type.
* failing that, a run **passing through** it — ``mep_soffit.connected``'s own principle,
  "a run *through* a machine is as plumbed as a run *into* one". This is what an exterior
  hood needs: the duct does not stop at the hood, it goes past it and out, and its end is
  graded as an outdoor termination by ``mep.duct_connectivity`` rather than as a landing.
  Ends are preferred over pass-throughs because a pass-through says nothing about which
  machine the run belongs to: two adjacent manifolds have radials crossing each other's
  footprint, and reading those as arrivals would credit each with the other's air.

The third verdict is the interesting one. When something arrives but *nothing of the
declared service* does, the answer is UNKNOWN, not FAIL: it is nearly always a **reversible
casting stated once**. EQ-T-ERV-HOOD-6 is "the same casting with the damper reversed" and
declares OUTDOOR_AIR, so the discharge hood built from it is reached by an EXHAUST run;
EQ-T-ERV-MANIFOLD-6 declares a SUPPLY_AIR trunk and is placed as an extract manifold too.
Nothing is wrong with the building in either case — what is missing is a model that can say
"this type is directional and this placement reverses it", and reporting a FAIL would be
reporting the catalog's shape rather than the house's.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.mep.duct_connectivity import JOINT_TOLERANCE_M, case_height
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import AIR_SERVICE_DUCT_SYSTEM
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_sleeves import rotate_into_plan
from typehaus.resolve.mep_soffit import segment_meets_box

CHECK_ID = "mep.equipment_port_service"


def _case_box(footprint) -> tuple[tuple[float, float], tuple[float, float]]:
    """The plan bounds of a resolved footprint, widened by the joint tolerance."""
    xs = [point[0] for point in footprint]
    ys = [point[1] for point in footprint]
    return ((min(xs) - JOINT_TOLERANCE_M, max(xs) + JOINT_TOLERANCE_M),
            (min(ys) - JOINT_TOLERANCE_M, max(ys) + JOINT_TOLERANCE_M))


def _reaches_vertically(z: float | None, base_m: float, height_m: float | None) -> bool:
    """Whether an elevation is inside the case. Unknown height falls back to the plan test.

    Same band as ``mep.duct_connectivity._meets_equipment``: ``z_m`` is the object's *base*
    — a ceiling-hung ERV at a 6'-0" mount resolves to the bottom of its case — so the band
    runs upward from it.
    """
    if z is None or height_m is None:
        return True
    return base_m - JOINT_TOLERANCE_M <= z <= base_m + height_m + JOINT_TOLERANCE_M


def _arrivals(ctx: CheckContext, obj, height_m: float | None
              ) -> tuple[dict[str, str], dict[str, str]]:
    """``(ends, pass_throughs)``: duct system value -> the tag of a run arriving that way."""
    box = _case_box(obj.footprint)
    ends: dict[str, str] = {}
    through: dict[str, str] = {}
    for duct in ctx.model.ducts:
        if len(duct.path) < 2:
            continue
        system = duct.system.value if hasattr(duct.system, "value") else str(duct.system)
        landed = False
        for index, point in ((0, duct.path[0]), (len(duct.path) - 1, duct.path[-1])):
            if not segment_meets_box(point, point, box):
                continue
            z = duct.z_m[index] if len(duct.z_m) > index else None
            if _reaches_vertically(z, obj.z_m, height_m):
                ends.setdefault(system, duct.tag)
                landed = True
                break
        if landed:
            continue
        for index in range(len(duct.path) - 1):
            if not segment_meets_box(duct.path[index], duct.path[index + 1], box):
                continue
            if len(duct.z_m) <= index + 1:
                through.setdefault(system, duct.tag)
                break
            low = min(duct.z_m[index], duct.z_m[index + 1])
            high = max(duct.z_m[index], duct.z_m[index + 1])
            if (height_m is None
                    or (low <= obj.z_m + height_m + JOINT_TOLERANCE_M
                        and high >= obj.z_m - JOINT_TOLERANCE_M)):
                through.setdefault(system, duct.tag)
                break
    return ends, through


def _port_stations(element, ports) -> str:
    """Where the declared ports land in plan, for the message. Never the verdict.

    They are placed with the same ``rotate_into_plan`` the plan symbols and the drain-drop
    resolver use, so what is printed is where the model actually thinks the collar is —
    which is exactly how a reader discovers that four of them are the same point.
    """
    seen: list[str] = []
    for port in ports:
        local = (port.position[0].meters, port.position[1].meters)
        x, y = rotate_into_plan(element, local)
        station = f"({x / M_PER_IN / 12:.2f}', {y / M_PER_IN / 12:.2f}')"
        if station not in seen:
            seen.append(station)
    return ", ".join(seen)


@check(Tier.INTEGRITY, CHECK_ID)
def equipment_port_service(ctx: CheckContext) -> list[Finding]:
    """Every air port a machine declares is reached by a duct of that port's system."""
    types = {entry.tag: entry for entry in ctx.plan.library.equipment_types}
    objects = {obj.tag: obj for obj in ctx.model.canvas_objects}
    out: list[Finding] = []
    for element in ctx.plan.all_elements():
        if element.element_kind != "Equipment":
            continue
        machine_type = types.get(getattr(element, "type_ref", None) or "")
        obj = objects.get(element.tag)
        if machine_type is None or obj is None or not obj.footprint:
            continue
        ports = [port for port in machine_type.ports
                 if port.service in AIR_SERVICE_DUCT_SYSTEM]
        if not ports:
            continue
        wanted = {AIR_SERVICE_DUCT_SYSTEM[port.service].value for port in ports}
        height_m = case_height(ctx, obj.type_ref)
        ends, through = _arrivals(ctx, obj, height_m)
        arrived = ends or through
        how = "ends in" if ends else "passes through"
        stations = _port_stations(element, ports)
        names = ", ".join(sorted(wanted))
        if not arrived:
            out.append(failed(
                CHECK_ID,
                f"{element.tag} declares {len(ports)} air port(s) — {names} — at {stations}, "
                "and no duct run of any system reaches its case: nothing was ever drawn to "
                "this machine, which no rule that iterates over duct ends can notice",
                (element.tag,)))
            continue
        matched = sorted(wanted & set(arrived))
        if matched:
            served = ", ".join(f"{system} via {arrived[system]}" for system in matched)
            missing = sorted(wanted - set(arrived))
            note = ("" if not missing else
                    f"; no run arrives for {', '.join(missing)}, which "
                    f"{machine_type.tag} also declares")
            out.append(passed(
                CHECK_ID,
                f"{element.tag}'s declared air service is served: {served} "
                f"({how} the case){note}", (element.tag,)))
            continue
        out.append(unknown(
            CHECK_ID,
            f"{element.tag} declares {names} (per {machine_type.tag}) but the run(s) that "
            f"reach its case carry "
            f"{', '.join(f'{system} ({tag})' for system, tag in sorted(arrived.items()))}: "
            "the type is a reversible casting stated in one direction and placed in the "
            "other, and this model has no way to say so — the ports are a product fact, the "
            "placement is a house fact, and nothing reconciles them",
            (element.tag,)))
    if not out:
        return [not_applicable(
            CHECK_ID,
            "no placed Equipment names an EquipmentType declaring a supply, return, "
            "exhaust or outdoor-air ServicePort, so there is no port to serve", ())]
    return out
