"""Lighting checks — controls, location listings, and 24V run supplies.

Advisory, like the rest of the electrical family: none of these blocks a build. They
answer the three questions a lighting plan is reviewed for that the panel schedule cannot
— can you turn it off, is it listed for where it hangs, and is the driver big enough.

Kept out of ``checks/mep/electrical.py`` so that file stays about power distribution; the
two share nothing but the ``ElectricalDevice`` element kind.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import LuminaireForm, Occupancy

# The sizing factor a 24V LED supply is picked by: continuous load at 125%, the same
# NEC 210.19(A)(1) basis a continuous branch-circuit load uses. A driver run at its
# nameplate cooks; the margin is what buys its rated life.
PSU_SIZING_FACTOR = 1.25

_M_TO_FT = 3.280839895013123


def _pass(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.PASS)


def _warn_fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message=msg, element_tags=tags,
                   result=Result.FAIL)


def _unknown(cid: str, reason: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.WARN, check_id=cid, message="UNKNOWN — " + reason,
                   element_tags=tags, result=Result.UNKNOWN)


def _luminaire_types(ctx: CheckContext) -> dict[str, object]:
    """Library entries that carry a ``LuminaireForm`` — i.e. the ``LuminaireType`` subset."""
    return {product.tag: product for product in ctx.plan.library.electrical_device_types
            if getattr(product, "form", None) is not None}


def _lit_elements(ctx: CheckContext) -> list[tuple[object, str]]:
    """Every authored luminaire and light run, paired with the storey it sits on."""
    out: list[tuple[object, str]] = []
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            kind = element.element_kind
            if kind == "LightRun":
                out.append((element, storey.tag))
            elif (kind == "ElectricalDevice"
                  and getattr(element.kind, "value", None) == "light"):
                out.append((element, storey.tag))
    return out


@check(Tier.ADVISORY, "electrical.lighting_controls")
def lighting_controls(ctx: CheckContext) -> list[Finding]:
    """Every luminaire names a switch that exists, or carries one on the fixture.

    ``controlled_by`` is authored on the *load*, so this is the one place the switch legs
    are reconciled: a named tag that resolves to nothing is a fixture nobody can turn off,
    and a tag that resolves to something which is not a switch is a wiring error drawn as
    a fact. A fixture whose type sets ``integral_switch`` names none by design and is
    exempt — there is no wall device to point at.

    The cross-circuit case is reported separately and is not the same defect: a switch fed
    from a different branch than the fixture it controls puts two circuits in one box,
    which NEC 210.7 permits only with a means to disconnect both simultaneously. Worth
    seeing on a drawing; not worth calling a failure.
    """
    cid = "electrical.lighting_controls"
    lit = _lit_elements(ctx)
    if not lit:
        return [_unknown(cid, "no luminaires modeled")]

    types = _luminaire_types(ctx)
    switches = {element.tag: element for storey in ctx.plan.storeys
                for element in ctx.plan.storey_elements(storey.tag)
                if element.element_kind == "ElectricalDevice"
                and getattr(element.kind, "value", None) == "switch"}

    out: list[Finding] = []
    controlled = 0
    for element, _storey in lit:
        product = types.get(getattr(element, "type_ref", "") or "")
        names = tuple(getattr(element, "controlled_by", ()) or ())
        if not names:
            if product is not None and getattr(product, "integral_switch", False):
                continue  # switched at the fixture; nothing to reconcile
            out.append(_warn_fail(
                cid, "luminaire " + element.tag + " names no switch and its type carries "
                     "no integral switch", (element.tag,)))
            continue
        missing = [name for name in names if name not in switches]
        if missing:
            out.append(_warn_fail(
                cid, "luminaire " + element.tag + " is controlled by "
                     + ", ".join(sorted(missing)) + ", which is not a switch in this plan",
                (element.tag,)))
            continue
        controlled += 1
        circuit = getattr(element, "circuit", None)
        if circuit is None:
            continue  # a 24V run has no branch circuit of its own; its PSU does
        crossed = sorted({name for name in names
                          if switches[name].circuit not in (None, circuit)})
        if crossed:
            out.append(_warn_fail(
                cid, "luminaire " + element.tag + " on " + circuit + " is switched by "
                     + ", ".join(crossed) + " on another circuit — NEC 210.7 wants a "
                     "simultaneous disconnect where two circuits share a box",
                (element.tag,) + tuple(crossed)))
    if not out:
        out.append(_pass(cid, str(controlled) + " luminaires resolve every switch they name"))
    return out


@check(Tier.ADVISORY, "electrical.wet_location")
def wet_location(ctx: CheckContext) -> list[Finding]:
    """A luminaire in a bathroom or outdoors has to be listed for the wet it will meet.

    Two populations, one rule. A fixture in a ``BATHROOM`` room is in a damp location at
    minimum (NEC 410.10(D) puts anything in the tub/shower zone in a wet one, and this
    model does not carry that zone, so damp is the floor and wet is what the bath cans are
    specified as anyway). A luminaire that stands inside no room at all is outside the
    modeled envelope — the porch fan is the case — and unlisted there it fails outright.

    "Exterior" is decided geometrically, not by a blank ``room`` field: an unlabeled
    fixture sitting squarely in a bedroom is a missing label, and calling it outdoors
    would turn a data gap into a code finding about the wrong thing.
    """
    cid = "electrical.wet_location"
    types = _luminaire_types(ctx)
    if not types:
        return [_unknown(cid, "no luminaire types in the library")]

    bathrooms = {room.tag for storey in ctx.plan.storeys
                 for room in ctx.plan.storey_elements(storey.tag)
                 if room.element_kind == "Room" and room.occupancy is Occupancy.BATHROOM}

    out: list[Finding] = []
    checked = 0
    for element, storey_tag in _lit_elements(ctx):
        product = types.get(getattr(element, "type_ref", "") or "")
        if product is None:
            continue
        room = getattr(element, "room", None)
        if room in bathrooms:
            where = "bathroom " + str(room)
        elif room is None and _stands_outside_every_room(ctx, element, storey_tag):
            where = "no modeled room (exterior)"
        else:
            continue
        checked += 1
        if product.damp_rated or product.wet_rated:
            continue
        out.append(_warn_fail(
            cid, "luminaire " + element.tag + " in " + where + " uses " + product.tag
                 + ", which is neither damp nor wet rated", (element.tag,)))
    if not checked:
        return [_unknown(cid, "no bathroom or exterior luminaires modeled")]
    if not out:
        out.append(_pass(cid, str(checked) + " bathroom/exterior luminaires are damp or "
                              "wet rated"))
    return out


def _stands_outside_every_room(ctx: CheckContext, element: object, storey_tag: str) -> bool:
    """Whether the element's plan point falls in no room's clear face on its storey.

    A ``LightRun`` has a path rather than a point; its first vertex answers the same
    question, since a run that starts outdoors is an exterior run.
    """
    from shapely.geometry import Point, Polygon

    position = getattr(element, "position", None)
    if position is not None:
        point = Point(position.xy_m)
    else:
        path = getattr(element, "path", ())
        if not path:
            return False
        point = Point(path[0].xy_m)
    rings = [room.clear_face for room in ctx.model.rooms
             if room.storey == storey_tag and len(room.clear_face) >= 3]
    return not any(Polygon(ring).buffer(0).contains(point) for ring in rings)


@check(Tier.ADVISORY, "electrical.light_run_psu")
def light_run_psu(ctx: CheckContext) -> list[Finding]:
    """Every low-voltage run names a supply that exists and is big enough to drive it.

    A 24V run carries no branch circuit — its PSU does — so an unresolvable ``psu_ref`` is
    not a naming slip, it is a fixture with no source. Where several runs share one supply
    their loads are summed before it is sized, because that is what the supply sees.
    """
    cid = "electrical.light_run_psu"
    runs = ctx.model.light_runs
    if not runs:
        return [_unknown(cid, "no light runs modeled")]

    types = {product.tag: product for product in ctx.plan.library.electrical_device_types}
    devices = {element.tag: element for storey in ctx.plan.storeys
               for element in ctx.plan.storey_elements(storey.tag)
               if element.element_kind == "ElectricalDevice"}

    out: list[Finding] = []
    demand_by_psu: dict[str, float] = {}
    for run in runs:
        product = types.get(run.type_ref)
        line_voltage = getattr(product, "voltage", 120) if product is not None else 120
        if run.psu_ref is None:
            if line_voltage != 120:
                out.append(_warn_fail(
                    cid, "light run " + run.tag + " is " + str(line_voltage)
                         + "V and names no supply", (run.tag,)))
            continue
        if run.psu_ref not in devices:
            out.append(_warn_fail(
                cid, "light run " + run.tag + " names supply " + run.psu_ref
                     + ", which is not a device in this plan", (run.tag,)))
            continue
        watts_per_ft = getattr(product, "watts_per_ft", None) or 0.0
        demand_by_psu[run.psu_ref] = (demand_by_psu.get(run.psu_ref, 0.0)
                                      + watts_per_ft * run.length_m * _M_TO_FT)

    for psu_tag in sorted(demand_by_psu):
        required = demand_by_psu[psu_tag] * PSU_SIZING_FACTOR
        rating = getattr(types.get(devices[psu_tag].type_ref or ""), "load_va", None)
        if rating is None:
            out.append(_unknown(cid, "supply " + psu_tag + " states no rating, so the "
                                     + "{:.0f}".format(required) + " W it has to carry "
                                     "cannot be checked", (psu_tag,)))
            continue
        if rating + 1e-6 < required:
            out.append(_warn_fail(
                cid, "supply " + psu_tag + " is rated " + "{:.0f}".format(rating)
                     + " W but drives " + "{:.0f}".format(demand_by_psu[psu_tag])
                     + " W of tape, which needs " + "{:.0f}".format(required)
                     + " W at the 125% continuous factor", (psu_tag,)))
    if not out:
        out.append(_pass(cid, str(len(runs)) + " light runs resolve to a supply sized for "
                              "125% of the tape they drive"))
    return out


# Forms with no point instance — a STRIP is a ``LightRun``, never a placed device. Exported
# so a caller that wants "the placeable luminaire forms" does not re-derive the exclusion.
NON_PLACEABLE_FORMS = frozenset({LuminaireForm.STRIP})
