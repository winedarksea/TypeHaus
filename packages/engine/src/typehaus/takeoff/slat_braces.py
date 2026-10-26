"""A slat band's hardware: a connector at each slat end, the plate screws, the post ties.

The lumber bills off the resolved members in ``takeoff/framing.py``, like every other stick.
This bills what the :class:`~typehaus.model.braces.SlatBrace` names: its slats come from the
resolved record, so a slat the layout dropped is a pair of connectors nobody buys, and a
screwed infill slat bills its toe screws instead.
"""

from __future__ import annotations

from collections import Counter

from typehaus.hardware.catalog import (
    ROLE_KNEE_BRACE,
    ROLE_KNEE_BRACE_EQUAL_WIDTH,
    hardware_by_model,
    structural_hardware_catalog,
)
from typehaus.model.braces import SlatBrace
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row


def _knee_brace_item(model: str, connectors_per_end: int):
    """The catalog record for ``model`` in its authored knee-brace connection type."""
    role = ROLE_KNEE_BRACE_EQUAL_WIDTH if connectors_per_end == 2 else ROLE_KNEE_BRACE
    return next((item for item in structural_hardware_catalog()
                 if item.model == model and item.role == role),
                hardware_by_model(model))


def _family_source(part: str) -> str | None:
    """The source of the family a part is a length rung of (SDWS22400DB of ``SDWS22___DB``).
    Only the source: the family's ROLE is another joint's (through-foam), not this one."""
    family = next((item for item in structural_hardware_catalog()
                   if part in (getattr(item, "part_number_by_length_in", None) or {}).values()),
                  None)
    return family.source if family is not None else None


def slat_brace_rows(model: ResolvedModel) -> list:
    """One row per part, scope and connection type over the model's slat bands."""
    slats = {brace.tag: sum(1 for m in brace.members if m.category == "brace"
                            and (m.connection or "").startswith("kneebrace:"))
             for brace in model.braces}
    infill = {brace.tag: sum(1 for m in brace.members if m.category == "brace"
                             and (m.connection or "").startswith("screwed:"))
              for brace in model.braces}
    counts: Counter = Counter()
    tags: dict[tuple[str, str, int], list[str]] = {}
    for storey in model.plan.storeys:
        for el in model.plan.storey_elements(storey.tag):
            if not isinstance(el, SlatBrace) or el.tag not in slats:
                continue
            for key, n in (((el.connector, "slat brace connector"),
                            2 * el.connectors_per_end * slats[el.tag]),
                           ((el.infill_fastener, "slat brace infill screw"),
                            2 * el.infill_fasteners_each_end * infill[el.tag]),
                           ((el.plate_fastener, "slat brace plate screw"),
                            2 * el.plate_fasteners),
                           ((el.centre_post_tie, "slat brace centre post tie"),
                            2 * el.centre_post_ties_each_end)):
                key = (*key, el.connectors_per_end if key[1] == "slat brace connector" else 1)
                if n:
                    counts[key] += n
                tags.setdefault(key, []).append(el.tag)
    rows = []
    for (part, scope, connectors_per_end), count in sorted(counts.items()):
        item = (_knee_brace_item(part, connectors_per_end) if scope == "slat brace connector"
                else hardware_by_model(part))
        rule = {"slat brace connector": f"{connectors_per_end} at each end of every braced slat",
                "slat brace infill screw": "the authored count at each end of a screwed slat",
                "slat brace plate screw": "the authored count through each of two plates",
                "slat brace centre post tie": "the authored count at each end of the post",
                }[scope]
        element_tags = sorted(tags[(part, scope, connectors_per_end)])
        row = hardware_row(item, scope=scope, count=count, part_number=part,
                           tags=element_tags,
                           basis=f"{rule} ({', '.join(element_tags)})")
        if item is None:
            row["source"] = _family_source(part)
        rows.append(row)
    return rows
