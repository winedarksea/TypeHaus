"""The hardware a ``SuspensionAnchor`` names: one of each part per framed anchor.

The joist line itself bills as framing (it is a ``"joist"`` member); this is only the
saddle and swivel below it. An anchor that framed nothing buys nothing.
"""

from __future__ import annotations

from typehaus.hardware.catalog import structural_hardware_catalog
from typehaus.model.suspension import suspension_anchors
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row


def suspension_anchor_rows(model: ResolvedModel) -> list[dict]:
    framed = {r.tag for r in model.suspension_anchors if r.reason is None}
    catalog = {item.tag: item for item in structural_hardware_catalog()}
    uses: dict[str, list[str]] = {}
    for anchor in suspension_anchors(model.plan):
        if anchor.tag in framed:
            for tag in anchor.hardware:
                uses.setdefault(tag, []).append(anchor.tag)
    return [hardware_row(catalog.get(tag), scope="suspension anchor", count=len(tags),
                         basis=f"one per hang point: {', '.join(sorted(tags))}",
                         tags=sorted(tags))
            for tag, tags in sorted(uses.items())]
