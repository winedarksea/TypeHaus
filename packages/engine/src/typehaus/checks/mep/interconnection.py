"""``code.NEC_705_12_interconnection`` — NEC 705.12(B) busbar paths, per panel carrying a source.

Every path the printed (B) offers that the model can decide is tried, and the finding names
each one and whether it holds; the panel passes on any one:

- **(B)(1)** 125% of the sources' 705.28(A) current plus the busbar's OCPD within the bus.
- **(B)(2)** the same sum within 120% of the bus, with the source at the end opposite the
  primary feed and the (b) warning beside it. The end is derived: the panel type states where
  the feed enters (``main_feed_end``) and slots map to rows (odd left, even right, a 2-pole
  takes ``slot`` and ``slot + 2``); the source is at the end when no other breaker reaches a
  row past its farthest one. The (b) label is reported (``resolve/electrical_labels`` derives
  it), never a condition: a label is owed, not authored.
- **(B)(3)** every OCPD on the panel but the main summed within the bus, the main no larger
  than the bus (its label is not derived, so a pass says it is owed).
- **(B)(4)** a center-fed dwelling panel: either end, by the (2) arithmetic and label.

Not tried: (A) feeders, (B)(5) feed-through, (B)(6) engineering supervision. One documented
limit: the model has no feeder element, so a subpanel without its own ``service_amps`` takes
the service size as its main term (conservative for a subpanel). See
``docs/code-notes/nec-2026-paraphrase-690-705-710.md``.
"""

from __future__ import annotations

from typehaus.checks.mep.power_sources import source_term
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, by_result, not_applicable
from typehaus.model.nec import NEC, cite

_CID = "code.NEC_705_12_interconnection"
_BUS_ALLOWANCE = 1.2  # (B)(2)(a), (B)(4)


def _rows(circuit) -> tuple[int, int]:
    """First and last bus row a breaker occupies (slots 1-2 are row 1)."""
    first = (circuit.slot + 1) // 2
    return first, first + max(circuit.poles, 1) - 1


def _at_far_end(sources, others, feed_end: str) -> bool:
    """No other breaker reaches a row past the sources' farthest one, measured from the feed.
    "center" accepts either end (705.12(B)(4))."""
    if feed_end == "center":
        return _at_far_end(sources, others, "top") or _at_far_end(sources, others, "bottom")
    if feed_end == "top":
        return max(_rows(c)[1] for c in sources) >= max((_rows(c)[1] for c in others), default=0)
    return min(_rows(c)[0] for c in sources) <= min((_rows(c)[0] for c in others),
                                                    default=10**6)


def _placement(group, panel_circuits, feed_end) -> bool | None:
    if feed_end is None or any(c.slot is None for c in panel_circuits):
        return None
    others = [c for c in panel_circuits if not c.source]
    return _at_far_end(group, others, feed_end)


_Path = tuple[str, bool | None, str]  # (section, holds, why)


def _paths(ctx, panel_ref, product, group, main_amps, source_amps) -> list[_Path]:
    """(section, holds, why) for each path the model can weigh."""
    bus = float(product.bus_amps)
    total = round(main_amps + source_amps, 2)
    on_panel = [c for c in ctx.plan.library.circuits if c.panel_ref == panel_ref]
    feed_end = getattr(product, "main_feed_end", None)
    labelled = any(lb.section == NEC.INTERCONNECTION_LABEL and lb.host_ref == panel_ref
                   for lb in ctx.model.electrical_labels)
    rows = -(-int(product.spaces) // 2) if getattr(product, "spaces", None) else None
    at_end = _placement(group, on_panel, feed_end)
    where = ", ".join(f"{c.tag} rows {_rows(c)[0]}-{_rows(c)[1]}" for c in group if c.slot)
    where += f" of {rows}" if rows else ""
    out = [(NEC.INTERCONNECTION_100PCT, total <= bus + 1e-9,
            f"{total:g}A {'within' if total <= bus + 1e-9 else 'over'} the {bus:g}A bus")]
    allowance = bus * _BUS_ALLOWANCE
    fits = total <= allowance + 1e-9
    section = NEC.INTERCONNECTION_CENTER_FED if feed_end == "center" else \
        NEC.INTERCONNECTION_120PCT
    if at_end is None:
        place = (f"placement unknown ({where}): the panel type states no main_feed_end"
                 if feed_end is None else f"placement unknown ({where}): a slot is unauthored")
    else:
        place = (f"source at the end opposite the {feed_end} feed ({where})" if at_end
                 else f"source not at the end opposite the {feed_end} feed: a breaker sits "
                      f"past it ({where})")
    label = "the (b) label is derived (E-605)" if labelled else "the (b) label is owed"
    holds = (fits and at_end) if at_end is not None else (False if not fits else None)
    arithmetic = f"{total:g}A {'within' if fits else 'over'} {_BUS_ALLOWANCE:g} x {bus:g}A"
    spare = f", {allowance - total:g}A spare" if fits else ""
    out.append((section, holds, f"{arithmetic} = {allowance:g}A{spare}; {place}; {label}"))
    loads = round(sum(float(c.breaker_amps) for c in on_panel), 2)
    sum_ok = loads <= bus + 1e-9 and main_amps <= bus + 1e-9
    out.append((NEC.INTERCONNECTION_SUM, sum_ok,
                f"OCPDs other than the main sum to {loads:g}A against the {bus:g}A bus"
                + ("; its label is owed, not derived" if sum_ok else "")))
    return out


@check(Tier.CODE, _CID)
def interconnection_busbar(ctx: CheckContext) -> list[Finding]:
    """NEC 705.12(B) per panel carrying a ``source=True`` circuit: which paths hold."""
    code = cite(NEC.INTERCONNECTION)
    sources = [c for c in ctx.plan.library.circuits if c.source]
    if not sources:
        return [not_applicable(_CID, "no circuit in the schedule is a power source, so this "
                                     "house has no interconnected PV or generator for "
                                     f"{NEC.INTERCONNECTION} to size", (), code)]
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    panels = {e.tag: e for e in ctx.plan.all_elements()
              if e.element_kind == "ElectricalDevice" and e.kind.value == "panel"}
    from typehaus.takeoff.electrical import service_load_summary
    service_amps = service_load_summary(ctx.model)["service_amps"]
    by_panel: dict[str, list] = {}
    for circuit in sources:
        by_panel.setdefault(circuit.panel_ref, []).append(circuit)
    out: list[Finding] = []
    for panel_ref, group in sorted(by_panel.items()):
        product = types.get(getattr(panels.get(panel_ref), "type_ref", None) or "")
        main_amps = float(getattr(product, "service_amps", None) or service_amps or 0.0) or None
        terms = [source_term(ctx, c) for c in group]
        source_amps = round(sum(amps for amps, _ in terms), 2)
        tags = tuple([panel_ref] + sorted(c.tag for c in group))
        names = ", ".join(sorted(c.tag for c in group))
        if getattr(product, "bus_amps", None) is None or main_amps is None:
            missing = "bus_amps" if main_amps else "a main rating (service_amps)"
            out.append(by_result(_CID, Result.UNKNOWN,
                                 f"panel {panel_ref} carries {source_amps}A of source "
                                 f"breakers ({names}) but states no {missing}", tags, code,
                                 "declare bus_amps and service_amps on the panel's type"))
            continue
        head = (f"panel {panel_ref}: {main_amps:g}A main + {source_amps:g}A source "
                f"({'; '.join(how for _, how in terms)})")
        paths = _paths(ctx, panel_ref, product, group, main_amps, source_amps)
        detail = "; ".join(f"{sec} {'holds' if ok else 'unknown' if ok is None else 'fails'}: "
                           f"{why}" for sec, ok, why in paths)
        met = [sec for sec, ok, _ in paths if ok]
        if met:
            out.append(by_result(_CID, Result.PASS,
                                 f"{head} — met by {', '.join(met)}. {detail}", tags, code))
        elif any(ok is None for _, ok, _ in paths):
            out.append(by_result(_CID, Result.UNKNOWN, f"{head} — no path shown. {detail}",
                                 tags, code, "state the panel type's main_feed_end and slots"))
        else:
            out.append(by_result(_CID, Result.FAIL, f"{head} — no path holds. {detail}", tags,
                                 code, "move the source breaker to the bus end opposite the "
                                       "feed, reduce the source, or connect supply side"))
    return out
