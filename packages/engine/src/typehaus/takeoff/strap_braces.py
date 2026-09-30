"""Strap braces as hardware: the strap by product and length, and the nails that fix it.

A :class:`~typehaus.model.braces.StrapBrace` is steel cut off a coil, so it bills here and
never in the lumber take-off (``takeoff/framing.py`` skips ``STRAP_CATEGORY``). Counts come
from the authored elements; lengths from the resolved member, the same piece the viewer draws.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from typehaus.hardware.catalog import hardware_by_model
from typehaus.hardware.config import WallTieRules
from typehaus.model.braces import StrapBrace
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row

_M_TO_FT = 3.280839895013123


def strap_brace_rows(model: ResolvedModel, rules: WallTieRules) -> list:
    """One row per strap product (count, total LF) and one per (product, fastener) nail set.

    A product the catalog sells by the coil (CS16) counts COILS, as ``coil_strap_rows`` does,
    so the price join stays per coil; the strap count and LF ride in the basis.
    """
    lengths = {brace.tag: sum(m.length_m for m in brace.members)
               for brace in model.braces if brace.kind == "strap"}
    straps: dict[str, list] = defaultdict(list)
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, StrapBrace) and element.tag in lengths:
                straps[element.product].append((storey.tag, element))

    rows = []
    for product, group in sorted(straps.items()):
        by_storey = Counter(storey for storey, _ in group)
        total_ft = sum(lengths[el.tag] for _, el in group) * _M_TO_FT
        tags = [el.tag for _, el in group]
        item = hardware_by_model(product)
        coils = (math.ceil(total_ft / rules.coil_strap_coil_length_ft)
                 if item is not None and item.unit == "coil" else None)
        cut = f" from {rules.coil_strap_coil_length_ft:g} ft coils" if coils else ""
        rows.append(hardware_row(
            item, scope="strap brace", count=coils or len(group), coils=coils,
            part_number=product, length_ft=total_ft, tags=tags,
            by_storey=None if coils else dict(sorted(by_storey.items())),
            basis=(f"{len(group)} modeled strap brace(s), {total_ft:.1f} LF cut to "
                   f"length{cut} ({', '.join(sorted(tags))})")))
        nails: Counter = Counter()
        for _, el in group:
            nails[el.fastener] += 2 * el.fasteners_each_end
        for fastener, count in sorted(nails.items()):
            if not count:
                continue
            row = hardware_row(
                None, scope=f"strap brace fastener ({product})", count=count,
                part_number=fastener or None, size=fastener or None,
                basis=f"per-end nail count x 2 ends over {len(group)} {product} strap(s)")
            # The nail the strap's own row is measured through: its source is the strap's.
            row["source"] = (f"{item.source} — the nails its published row is measured "
                             f"through" if item is not None else None)
            rows.append(row)
    return rows
