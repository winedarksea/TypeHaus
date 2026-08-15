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
    """IRC P2902 — cross-connection control, one finding per connection that needs it.

    Hose connections are the ones this house actually has: a hydrant is a hose thread at
    the end of a potable line, which is the textbook cross-connection (P2902.3.1 answers it
    with an atmospheric vacuum breaker). The check grades each hydrant against the vacuum
    breaker on *its own* feed rather than against a house-wide count, because a house with
    three hydrants and one breaker protects one hydrant.
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
    breakers = _of_kind(ctx, PipeAccessoryKind.VACUUM_BREAKER)
    out: list[Finding] = []
    for hydrant in hydrants:
        feeds = {run.tag for run in ctx.model.pipe_runs if hydrant.tag in run.serves}
        mine = [b for b in breakers
                if hydrant.tag in b.serves or (b.pipe_ref in feeds and not b.serves)]
        if not mine:
            out.append(_fail(
                cid, f"hose connection {hydrant.tag} has no vacuum breaker — P2902.3.1 "
                     "requires backflow protection at every hose thread on a potable line",
                (hydrant.tag,)))
        else:
            out.append(_pass(
                cid, f"{hydrant.tag} is protected by {mine[0].tag}"
                     f"{' (' + mine[0].model + ')' if mine[0].model else ''}",
                (hydrant.tag, mine[0].tag)))
    for device in _of_kind(ctx, PipeAccessoryKind.BACKFLOW_PREVENTER):
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
