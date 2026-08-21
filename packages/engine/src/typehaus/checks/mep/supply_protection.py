"""Supply-side protection: the shutoff, the backflow devices, the arrestors.

Everything here was previously unanswerable. ``mep.hydrant_freeze_depth`` said so in its
own output — it emitted an UNKNOWN reading "the model has no valve or backflow-preventer
element, so neither can be evaluated here" — and the rest was prose in ``plans/TODO.md``:
a backflow preventer on the basement fixtures, arrestors at the washer, a main shutoff that
is accessible. ``PipeAccessory`` is the element that makes all three real questions, and
these are the three checks that ask them.

CODE tier, all three. None of them is a preference: P2903.9.1 requires the main shutoff and
requires it accessible, P2902 requires backflow protection at every hose connection, and
P2903.5 requires arrestors where quick-closing valves are installed.

Each check no-ops on a plan with no supply runs. A house with no water is not a house
missing a shutoff — it is a house whose plumbing has not been drawn yet, and reporting three
FAILs against it would train the reader to ignore them.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail, passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import PipeAccessoryKind, PipeSystem, Service

_SUPPLY_SYSTEMS = (PipeSystem.WATER_COLD.value, PipeSystem.WATER_HOT.value)


def _has_supply(ctx: CheckContext) -> bool:
    return any(run.system in _SUPPLY_SYSTEMS for run in ctx.model.pipe_runs)


def _of_kind(ctx: CheckContext, kind: PipeAccessoryKind) -> list:
    return [a for a in ctx.model.pipe_accessories if a.kind == kind.value]


# The two device families P2902 counts as protection. A shutoff is not one of them: closing
# a valve is an operation, and a cross-connection is judged on what holds with nobody there.
_GUARD_KINDS = frozenset({PipeAccessoryKind.VACUUM_BREAKER.value,
                          PipeAccessoryKind.BACKFLOW_PREVENTER.value})


def _named(device) -> str:
    """``TAG (model)`` where a model number was authored — what an inspector looks for."""
    return f"{device.tag} ({device.model})" if device.model else device.tag


@check(Tier.CODE, "mep.main_shutoff")
def main_shutoff(ctx: CheckContext) -> list[Finding]:
    """IRC P2903.9.1 — one main shutoff valve, and it has to be reachable.

    Two failures, not one, because they fail differently on site. A missing valve is caught
    at rough-in; a valve behind the water heater passes rough-in and is discovered the night
    something bursts. ``accessible`` is authored rather than derived: whether you can get a
    hand on a valve is a judgement about the room around it, and geometry alone would only
    be guessing.

    More than one MAIN_SHUTOFF is also a failure. "The" main shutoff is singular by
    definition — two of them means nobody knows which one the label on the panel refers to,
    and it is nearly always a copy-paste rather than a real second service.
    """
    cid = "mep.main_shutoff"
    if not _has_supply(ctx):
        return []
    mains = _of_kind(ctx, PipeAccessoryKind.MAIN_SHUTOFF)
    if not mains:
        return [_fail(cid, "the water service has no main shutoff — P2903.9.1 requires one "
                           "valve controlling the whole supply")]
    if len(mains) > 1:
        return [_fail(cid, "the supply declares "
                           f"{len(mains)} main shutoffs ({', '.join(a.tag for a in mains)}); "
                           "P2903.9.1's main shutoff is singular",
                      tuple(a.tag for a in mains))]
    main = mains[0]
    if not main.accessible:
        return [_fail(cid, f"main shutoff {main.tag} does not declare `accessible=True` — "
                           "P2903.9.1 requires the valve be reachable without removing a "
                           "panel or standing on something",
                      (main.tag,))]
    where = f" in {main.room}" if main.room else ""
    return [_pass(cid, f"main shutoff {main.tag} is on {main.pipe_ref}{where} and is "
                       "declared accessible", (main.tag,))]


@check(Tier.CODE, "mep.backflow_prevention")
def backflow_prevention(ctx: CheckContext) -> list[Finding]:
    """IRC P2902 — cross-connection control, graded per connection rather than per device.

    The unit is the *branch*, not the fitting. What a cross-connection asks is what stands
    between the potable trunk and the opening, and every guard on the feed is part of that
    answer whether it screws onto the hose thread or sits on the branch in a mechanical
    room. So an outlet and its run are read as one thing: each hydrant gets one finding
    naming everything protecting it, and adding a device to the branch changes what that
    finding says. The earlier shape asked only "is there a vacuum breaker on my feed" and
    then rubber-stamped each backflow preventer with a PASS restating what it was authored
    to serve — two loops that never met, so a device could be added, scheduled and billed
    without moving the grade of the fixture it was bought for.

    This is what makes the garage yard hydrant legible. Its second opening — the weep at
    the buried shutoff, which empties the barrel into stone every time the handle closes —
    is one the code never names, so ``PA-G-HYD-BFP`` sits on the branch rather than at the
    thread. Nothing here knows what a weep is, and nothing here needs to: the check stopped
    discarding the rest of the branch, and the hydrant that carries a second device now
    reads differently from the two that do not.

    Still per hydrant, not per house — three hydrants and one breaker protects one hydrant.

    A hydrant whose *type* declares ``integral_vacuum_breaker`` (a Woodford Model 19 wall
    hydrant, unlike the garage's bare-thread yard hydrant) needs no accessory of its own:
    the device is built into the faucet body, already inside the fixture's own price, and
    authoring a second ``PipeAccessory(VACUUM_BREAKER)`` for it would both misstate the
    installation and double-bill a part that was never separately bought.

    Devices that guard no hydrant are graded on whether they are attached to anything real.
    ``pipe_ref`` is already the resolver's business (an accessory with no host run is an
    integrity error before a check ever runs), but ``serves`` is nobody's: a tag that names
    no element in the model is a device the schedule carries, the estimate prices and the
    plumber installs across a connection that does not exist.
    """
    cid = "mep.backflow_prevention"
    if not _has_supply(ctx):
        return []
    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    hydrants = [
        element for storey in ctx.plan.storeys
        for element in ctx.plan.storey_elements(storey.tag)
        if element.element_kind == "Fixture"
        and types.get(element.type_ref) is not None
        and types[element.type_ref].plan_symbol == "hydrant"
        and Service.WATER_COLD in types[element.type_ref].needs
    ]
    guards = [a for a in ctx.model.pipe_accessories if a.kind in _GUARD_KINDS]
    out: list[Finding] = []
    counted: set[str] = set()
    for hydrant in hydrants:
        feeds = {run.tag for run in ctx.model.pipe_runs if hydrant.tag in run.serves}
        mine = [g for g in guards
                if hydrant.tag in g.serves or (g.pipe_ref in feeds and not g.serves)]
        counted.update(g.tag for g in mine)
        threads = [g for g in mine if g.kind == PipeAccessoryKind.VACUUM_BREAKER.value]
        hydrant_type = types.get(hydrant.type_ref)
        integral = bool(hydrant_type and hydrant_type.integral_vacuum_breaker)
        if not threads and not integral:
            out.append(_fail(
                cid, f"hose connection {hydrant.tag} has no vacuum breaker — P2902.3.1 "
                     "requires backflow protection at every hose thread on a potable line",
                (hydrant.tag,)))
            continue
        branch = [g for g in mine if g.kind == PipeAccessoryKind.BACKFLOW_PREVENTER.value]
        if threads:
            message = f"{hydrant.tag}'s hose thread is protected by {_named(threads[0])}"
        else:
            message = (f"{hydrant.tag}'s hose thread is protected by its own integral "
                       f"vacuum breaker ({hydrant_type.name}) — no separate accessory to "
                       "schedule or bill")
        if branch:
            message += (f", and its branch ({', '.join(sorted(feeds)) or 'its feed'}) "
                        f"carries {' and '.join(_named(g) for g in branch)}")
        out.append(_pass(cid, message, (hydrant.tag, *(g.tag for g in mine))))
    known = {element.tag for storey in ctx.plan.storeys
             for element in ctx.plan.storey_elements(storey.tag)}
    for device in _of_kind(ctx, PipeAccessoryKind.BACKFLOW_PREVENTER):
        if device.tag in counted:
            continue
        missing = [tag for tag in device.serves if tag not in known]
        if missing:
            out.append(_fail(
                cid, f"backflow preventer {device.tag} declares protection for "
                     f"{', '.join(missing)}, which the model does not contain — the device "
                     "would be scheduled and installed across a connection that is not there",
                (device.tag,)))
            continue
        served = ", ".join(device.serves) if device.serves else device.pipe_ref or "—"
        out.append(_pass(cid, f"backflow preventer {device.tag} protects {served}",
                         (device.tag,)))
    return out


@check(Tier.CODE, "mep.water_hammer_arrestor")
def water_hammer_arrestor(ctx: CheckContext) -> list[Finding]:
    """IRC P2903.5 — an arrestor on each supply feeding a quick-closing valve.

    *Each* supply: a washer slams both its hot and its cold solenoid shut, and an arrestor
    on the cold alone leaves the hot line to hammer. So the check pairs every quick-closing
    product with the systems that actually serve it and demands an arrestor per system,
    rather than counting devices against appliances.

    ``quick_closing`` is a field on the product type (``ApplianceType``), not a guess from
    its name — see the note there.
    """
    cid = "mep.water_hammer_arrestor"
    if not _has_supply(ctx):
        return []
    types = {t.tag: t for t in ctx.plan.library.appliance_types}
    arrestors = _of_kind(ctx, PipeAccessoryKind.WATER_HAMMER_ARRESTOR)
    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            product = types.get(getattr(element, "type_ref", None) or "")
            if product is None or not getattr(product, "quick_closing", False):
                continue
            for system in _SUPPLY_SYSTEMS:
                feeds = {run.tag for run in ctx.model.pipe_runs
                         if run.system == system and element.tag in run.serves}
                if not feeds:
                    continue  # this product takes no water of this temperature
                mine = [a for a in arrestors
                        if a.system == system
                        and (element.tag in a.serves or a.pipe_ref in feeds)]
                label = "cold" if system == PipeSystem.WATER_COLD.value else "hot"
                if not mine:
                    out.append(_fail(
                        cid, f"{element.tag} has a quick-closing valve on its {label} "
                             f"supply ({', '.join(sorted(feeds))}) and no water-hammer "
                             "arrestor on it — P2903.5",
                        (element.tag,)))
                else:
                    out.append(_pass(
                        cid, f"{element.tag}'s {label} supply is arrested by "
                             f"{mine[0].tag}", (element.tag, mine[0].tag)))
    return out
