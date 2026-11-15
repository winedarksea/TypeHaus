"""Article 411 listing facts of the low-voltage lighting supplies, as grouped rows.

Reported under ``electrical.light_run_psu`` (``lighting.py``), over every supply a light run
or a supply-fed luminaire names. One row per rule, each naming the types that decide it:

* **411.2** the supply states its listing (``supply_listing``): the supply part of a system
  of listed parts. The luminaires' and fittings' listing is not modelled, so a PASS speaks
  for the supplies only.
* **411.6(A)** concealed secondary wiring is a Chapter 3 method or from a listed Class 2
  source: ``class_2`` True passes; False needs a Chapter 3 method the model does not hold
  (UNKNOWN); unset is UNKNOWN.
* **411.7(B)** the secondary is isolated from the branch circuit (``isolating_secondary``):
  True passes, False fails (advisory), unset is UNKNOWN.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory, passed, unknown
from typehaus.findings import Finding, Result
from typehaus.model.nec import NEC, cite


def supply_tags(ctx) -> list[str]:
    """Every device a light run or a luminaire names as its supply."""
    named = {run.psu_ref for run in ctx.model.light_runs if run.psu_ref}
    named |= {e.psu_ref for e in ctx.plan.all_elements()
              if e.element_kind == "ElectricalDevice" and getattr(e, "psu_ref", None)}
    return sorted(named)


def _by_type(supplies: dict[str, str | None], types: dict, field: str) -> dict:
    """Fact value -> {type tag: [supply tags]}."""
    out: dict = {}
    for tag, type_ref in sorted(supplies.items()):
        value = getattr(types.get(type_ref or ""), field, None)
        out.setdefault(value, {}).setdefault(type_ref or "(untyped)", []).append(tag)
    return out


def _names(groups: dict) -> str:
    return "; ".join(f"{t} ({', '.join(tags)})" for t, tags in sorted(groups.items()))


def listing_rows(cid: str, ctx, devices: dict, types: dict) -> list[Finding]:
    supplies = {t: devices[t].type_ref for t in supply_tags(ctx) if t in devices}
    if not supplies:
        return []
    tags = tuple(sorted(supplies))
    out: list[Finding] = []
    listing = _by_type(supplies, types, "supply_listing")
    code = cite(NEC.LOW_VOLTAGE_LIGHTING_LISTING)
    if None in listing:
        out.append(unknown(cid, f"411.2: no listing is stated for {_names(listing[None])}",
                           tags, code=code, fix="author supply_listing from the datasheet"))
    else:
        stated = "; ".join(f"{_names(g)}: {value}" for value, g in sorted(listing.items()))
        out.append(passed(cid, f"411.2: every supply states its listing ({stated}); the "
                               "luminaires' and fittings' listing is not modelled", tags,
                          code=code))
    class_2 = _by_type(supplies, types, "class_2")
    code = cite(NEC.LOW_VOLTAGE_LIGHTING_CONCEALED)
    gaps = []
    if False in class_2:
        gaps.append(f"{_names(class_2[False])} are not Class 2, so their concealed secondary "
                    "needs a Chapter 3 wiring method the model does not hold")
    if None in class_2:
        gaps.append(f"{_names(class_2[None])} state no Class 2 listing")
    if gaps:
        out.append(unknown(cid, "411.6(A): " + "; ".join(gaps), tags, code=code))
    else:
        out.append(passed(cid, "411.6(A): every supply is a listed Class 2 source", tags,
                          code=code))
    isolated = _by_type(supplies, types, "isolating_secondary")
    code = cite(NEC.LOW_VOLTAGE_LIGHTING_ISOLATION)
    if False in isolated:
        out.append(advisory(cid, f"411.7(B): {_names(isolated[False])} do not isolate the "
                                 "secondary from the branch circuit", tags, Result.FAIL,
                            code=code))
    elif None in isolated:
        out.append(unknown(cid, f"411.7(B): {_names(isolated[None])} state no isolated output",
                           tags, code=code, fix="author isolating_secondary from the datasheet"))
    else:
        out.append(passed(cid, "411.7(B): every supply isolates its secondary", tags, code=code))
    return out
