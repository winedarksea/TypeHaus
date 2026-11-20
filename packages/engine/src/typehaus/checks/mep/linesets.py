"""Refrigerant linesets against the outdoor unit's published table, and their ends (#139).

``mep.lineset_limits``: per set, length against ``max_per_port`` / ``min_per_port`` and the
rise against ``max_rise_od_above`` / ``below``; per outdoor unit, the sum against
``max_total``; and a kit long enough to buy. The table is the manufacturer's, a prescriptive
read: Minnesota adopts the IMC for mechanical (Minn. R. 1346.0050), whose 304.1 binds it.
An unread figure is UNKNOWN, never a default.

``mep.lineset_reach``: each end lands on its port pair within the standard's tolerance, and
every head paired by ``outdoor_ref`` has a set. An end within tolerance of a schematic port
station is UNKNOWN, since the station itself is unread.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.resolve.linesets import lineset_standard

_LIMITS = "mep.lineset_limits"
_REACH = "mep.lineset_reach"
_CODE = "MN Mechanical Code (Minn. R. 1346.0050, IMC 2018) 304.1 (manufacturer's instructions)"
_FT = 0.3048


def _ft(value_m: float) -> str:
    return f"{value_m / _FT:.1f} ft"


def _limits_of(ctx: CheckContext, outdoor_tag: str | None):
    equipment = next((el for el in ctx.plan.all_elements() if el.tag == outdoor_tag), None)
    types = {t.tag: t for t in ctx.plan.library.equipment_types}
    product = types.get(getattr(equipment, "type_ref", None) or "")
    return getattr(product, "refrigerant_limits", None)


@check(Tier.CODE, _LIMITS)
def lineset_limits(ctx: CheckContext) -> list[Finding]:
    linesets = getattr(ctx.model, "linesets", [])
    if not linesets:
        return [not_applicable(_LIMITS, "no refrigerant PipeRun in the model", (), _CODE)]
    standard = lineset_standard(ctx.plan)
    out: list[Finding] = []
    by_unit: dict[str, list] = {}
    for item in linesets:
        tags = tuple(t for t in (item.tag, item.head_tag, item.outdoor_tag) if t)
        limits = _limits_of(ctx, item.outdoor_tag)
        if limits is None:
            out.append(unknown(_LIMITS, f"{item.tag}: {item.outdoor_tag or 'no outdoor unit'} "
                                        "publishes no refrigerant_limits", tags, _CODE))
            continue
        by_unit.setdefault(item.outdoor_tag, []).append(item)
        cite = f" ({limits.source})"
        graded, unread = [], []
        for label, limit, value, worse in (
                ("length", limits.max_per_port, item.developed_m, lambda v, lim: v > lim),
                ("minimum length", limits.min_per_port, item.developed_m,
                 lambda v, lim: v < lim),
                ("rise, unit above", limits.max_rise_od_above,
                 max(item.rise_m or 0.0, 0.0), lambda v, lim: v > lim),
                ("rise, unit below", limits.max_rise_od_below,
                 max(-(item.rise_m or 0.0), 0.0), lambda v, lim: v > lim)):
            if limit is None or (label.startswith("rise") and item.rise_m is None):
                unread.append(label)
            elif worse(value, limit.meters):
                out.append(failed(_LIMITS, f"{item.tag}: {label} {_ft(value)} against the "
                                           f"published {_ft(limit.meters)}{cite}", tags, _CODE))
            else:
                graded.append(f"{label} {_ft(value)} of {_ft(limit.meters)}")
        if item.kit_m is None and standard is None:
            out.append(unknown(_LIMITS, f"{item.tag}: no LinesetStandard names stock kits",
                               tags, _CODE))
        elif item.kit_m is None:
            out.append(failed(_LIMITS, f"{item.tag}: ordered {_ft(item.ordered_m)} is longer "
                                       "than the LinesetStandard's longest stock kit",
                              tags, _CODE))
        if graded:
            out.append(passed(_LIMITS, f"{item.tag}: " + "; ".join(graded), tags, _CODE))
        if unread:
            out.append(unknown(_LIMITS, f"{item.tag}: {', '.join(unread)} not read from the "
                                        f"table{cite}", tags, _CODE))
    for unit, items in sorted(by_unit.items()):
        limits = _limits_of(ctx, unit)
        total = sum(i.developed_m for i in items)
        tags = (unit, *(i.tag for i in items))
        if limits.max_total is None:
            out.append(unknown(_LIMITS, f"{unit}: total line length not read ({limits.source})",
                               tags, _CODE))
        elif total > limits.max_total.meters:
            out.append(failed(_LIMITS, f"{unit}: {_ft(total)} of line over {len(items)} set(s) "
                                       f"against the published {_ft(limits.max_total.meters)}",
                              tags, _CODE))
        else:
            out.append(passed(_LIMITS, f"{unit}: {_ft(total)} of line over {len(items)} set(s), "
                                       f"of {_ft(limits.max_total.meters)}", tags, _CODE))
    return out


@check(Tier.CODE, _REACH)
def lineset_reach(ctx: CheckContext) -> list[Finding]:
    heads = [el for el in ctx.plan.all_elements()
             if el.element_kind == "Equipment" and getattr(el, "outdoor_ref", None)]
    linesets = getattr(ctx.model, "linesets", [])
    if not heads and not linesets:
        return [not_applicable(_REACH, "no indoor unit is paired with an outdoor unit",
                               (), _CODE)]
    standard = lineset_standard(ctx.plan)
    tolerance = standard.port_tolerance.meters if standard else None
    out: list[Finding] = []
    served = {item.head_tag for item in linesets}
    for head in heads:
        if head.tag not in served:
            out.append(failed(_REACH, f"{head.tag}: paired with {head.outdoor_ref} and no "
                                      "refrigerant PipeRun serves it", (head.tag,), _CODE))
    for item in linesets:
        tags = tuple(t for t in (item.tag, item.head_tag, item.outdoor_tag) if t)
        if tolerance is None:
            out.append(unknown(_REACH, f"{item.tag}: no LinesetStandard states a port "
                                       "tolerance", tags, _CODE))
            continue
        missing = [name for name, offset in (("head", item.head_offset_m),
                                             ("outdoor unit", item.outdoor_offset_m))
                   if offset is None]
        if missing:
            out.append(failed(_REACH, f"{item.tag}: no liquid/vapor port pair declared on its "
                                      f"{' or '.join(missing)}"
                                      f"{' port ' + item.port if item.port else ''}",
                              tags, _CODE))
            continue
        far = [f"{name} end {offset / 0.0254:.1f}\" off its ports"
               for name, offset in (("head", item.head_offset_m),
                                    ("outdoor", item.outdoor_offset_m))
               if offset > tolerance]
        if far:
            out.append(failed(_REACH, f"{item.tag}: " + "; ".join(far), tags, _CODE))
        elif not item.ports_exact:
            out.append(unknown(_REACH, f"{item.tag}: ends within {tolerance / 0.0254:.0f}\" of "
                                       "port stations that are schematic; confirm them on the "
                                       "delivered units", tags, _CODE))
        else:
            out.append(passed(_REACH, f"{item.tag}: both ends on their ports", tags, _CODE))
    return out
