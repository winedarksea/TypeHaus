"""Drainage checks — does the water actually have somewhere to go?

Both of these exist because the model let drainage be asserted in prose. Two Catlin gutters
carried ``slope="1/16 in/ft to the east downspout"`` and sloped toward a leader nobody had
ever authored; the foundation schedule printed "DRAINING TO SUMP" because a sump *solid*
existed, while every drain tile on the project said it discharged to daylight. Neither was
catchable, because neither claim was made in a form anything could resolve.

ADVISORY rather than CODE: a gutter that names no leader may simply be undocumented at this
stage of the drawing set, which is a note to the author and not a permit blocker.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.mep import Sump
from typehaus.model.structure import Drywell, FootingBedding, FrenchDrain
from typehaus.model.trim import Downspout, Gutter


def _advisory_fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    # Advisory findings never carry ERROR severity — that is reserved for hard blockers, and
    # the permit integrity gate treats any ERROR as one regardless of check_id.
    return advisory(cid, msg, tags, Result.FAIL)


def _elements(ctx: CheckContext):
    for storey in ctx.model.plan.storeys:
        yield from ctx.model.plan.storey_elements(storey.tag)


def _gutter_hosts(ctx: CheckContext) -> dict[str, object]:
    """Everything a ``Downspout.gutter_ref`` may legitimately name.

    An authored :class:`Gutter`, or the *roof* that derives one along its eave: an
    ``EaveGutter`` is a spec inside ``Roof.eave_trim`` with no tag of its own, so a leader
    under a derived channel can only name the roof it hangs from.
    """
    hosts: dict[str, object] = {}
    for element in _elements(ctx):
        if isinstance(element, Gutter):
            hosts[element.tag] = element
        eave_trim = getattr(element, "eave_trim", None)
        if eave_trim is not None and getattr(eave_trim, "gutter", None) is not None:
            hosts[element.tag] = element
    return hosts


def _gutter_runs(ctx: CheckContext):
    """``(tag, run)`` for every gutter in the plan, authored or derived.

    A derived ``EaveGutter`` has no tag of its own — it is a spec inside ``Roof.eave_trim``
    — so it reports under the roof that carries it, which is also what a leader must name.
    """
    for element in _elements(ctx):
        if isinstance(element, Gutter):
            yield element.tag, element
        eave_trim = getattr(element, "eave_trim", None)
        eave_gutter = getattr(eave_trim, "gutter", None) if eave_trim is not None else None
        if eave_gutter is not None:
            yield element.tag, eave_gutter


@check(Tier.ADVISORY, "drainage.downspout_ref")
def downspout_ref(ctx: CheckContext) -> list[Finding]:
    """Every gutter falls to a leader that exists, and every leader hangs off a real gutter."""
    cid = "drainage.downspout_ref"
    out: list[Finding] = []
    leaders = {element.tag: element for element in _elements(ctx)
               if isinstance(element, Downspout)}
    hosts = _gutter_hosts(ctx)

    for tag, run in _gutter_runs(ctx):
        ref = run.downspout_ref
        if ref is None:
            # The prose was the only claim, so the prose is what it is held to: a note that
            # names a downspout while the field naming one is empty is exactly the gutter
            # that sloped to a leader nobody had authored.
            if "downspout" in (run.slope or "").lower():
                out.append(_advisory_fail(
                    cid, f"gutter {tag} slopes to a downspout in its note ({run.slope!r}) "
                         f"but names none in downspout_ref", (tag,)))
            continue
        if ref not in leaders:
            out.append(_advisory_fail(
                cid, f"gutter {tag} falls to downspout {ref!r}, which no element declares",
                (tag,)))

    for leader in leaders.values():
        if leader.gutter_ref is not None and leader.gutter_ref not in hosts:
            out.append(_advisory_fail(
                cid, f"downspout {leader.tag} drains gutter {leader.gutter_ref!r}, which is "
                     f"neither an authored Gutter nor a roof with an eave gutter",
                (leader.tag,)))

    if not out:
        out.append(_pass(cid, f"every gutter and leader resolves ({len(leaders)} leaders)"))
    return out


@check(Tier.ADVISORY, "drainage.discharge_consistency")
def discharge_consistency(ctx: CheckContext) -> list[Finding]:
    """Where drainage says it discharges to, that thing exists.

    ``discharge`` is free text on purpose — "daylight" is a real answer and names nothing —
    so this resolves only the claims that name a element kind the model can hold: a sump, a
    drywell, a french drain. A pump's circuit must likewise be a circuit on the panel.
    """
    cid = "drainage.discharge_consistency"
    out: list[Finding] = []
    sumps = {element.tag: element for element in _elements(ctx) if isinstance(element, Sump)}
    receivers = dict(sumps)
    for element in _elements(ctx):
        if isinstance(element, (Drywell, FrenchDrain)):
            receivers[element.tag] = element
    circuits = {circuit.tag for circuit in ctx.model.plan.library.circuits}

    def _check_discharge(owner_tag: str, discharge: str | None) -> None:
        if not discharge:
            return
        text = discharge.strip()
        if text.lower() == "daylight":
            return
        if text.lower() == "sump":
            if not sumps:
                out.append(_advisory_fail(
                    cid, f"{owner_tag} discharges to a sump, but the plan has none",
                    (owner_tag,)))
            return
        # Anything else that looks like a tag has to resolve; free-text prose does not.
        if text.upper() == text and "-" in text and text not in receivers:
            out.append(_advisory_fail(
                cid, f"{owner_tag} discharges to {text!r}, which no element declares",
                (owner_tag,)))

    for element in _elements(ctx):
        if isinstance(element, FootingBedding) and element.drain_tile_spec is not None:
            _check_discharge(element.tag, element.drain_tile_spec.discharge)
        elif isinstance(element, FrenchDrain):
            _check_discharge(element.tag, element.discharge_ref)
            if element.tile is not None:
                _check_discharge(element.tag, element.tile.discharge)
        elif isinstance(element, Sump) and element.pump is not None:
            _check_discharge(element.tag, element.pump.discharge)
            circuit_ref = element.pump.circuit_ref
            if circuit_ref is not None and circuit_ref not in circuits:
                out.append(_advisory_fail(
                    cid, f"sump pump at {element.tag} is on circuit {circuit_ref!r}, which "
                         f"the panel schedule does not carry", (element.tag,)))
        elif isinstance(element, Drywell):
            for inlet in element.inlet_refs:
                if ctx.model.plan.by_tag(inlet) is None:
                    out.append(_advisory_fail(
                        cid, f"drywell {element.tag} is fed by {inlet!r}, which no element "
                             f"declares", (element.tag,)))

    if not out:
        out.append(_pass(cid, "every authored discharge resolves"))
    return out
