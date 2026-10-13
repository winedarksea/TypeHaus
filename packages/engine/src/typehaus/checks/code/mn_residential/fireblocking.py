"""R302.11 fireblocking at a multi-storey floor chase.

Covered only for stacked CHASE ``FloorOpening``s: a chase over a chase on the storey
directly above or below is a shaft, and every hole in it (the topmost included, which opens
into the roof space) must be closed in the deck plane. The sheet's penetrations are derived
from the runs on every resolve (``resolve/opening_fireblock.py``), so this grades them.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import _fail, _na, _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import LayerFunction

_CID, _CODE = "code.fireblock_chase", "R302.11"


def _stacked(ctx: CheckContext) -> list[tuple[str, str]]:
    """``(floor tag, opening tag)`` for each CHASE that overlaps one a storey above/below."""
    from shapely.geometry import Polygon

    chases = [(floor.storey, floor.tag, tag, Polygon(ring))
              for floor in ctx.model.floors for tag, ring in floor.chases]
    neighbours: dict[str, set[str]] = {}
    for storey in {c[0] for c in chases}:
        building = ctx.plan.building_of(storey)
        order = [s.tag for s in sorted(ctx.plan.storeys_of(building),
                                       key=lambda s: s.elevation.meters)]
        i = order.index(storey)
        neighbours[storey] = set(order[max(i - 1, 0):i]) | set(order[i + 1:i + 2])
    out = []
    for storey, floor_tag, tag, rect in chases:
        if any(other[0] in neighbours[storey] and rect.intersection(other[3]).area > 1e-6
               for other in chases):
            out.append((floor_tag, tag))
    return out


@check(Tier.CODE, _CID)
def fireblock_chase(ctx: CheckContext) -> list[Finding]:
    """R302.11 — a chase stacked through two or more decks is fireblocked at each one."""
    stacked = _stacked(ctx)
    if not stacked:
        return [_na(_CID, "no CHASE opening stacks over another, so no multi-storey shaft",
                    (), _CODE)]
    min_web = ctx.preferences.mep.fireblock_min_web_in * 0.0254
    blocks = {b.opening_tag: b for b in ctx.model.fireblocks}
    out: list[Finding] = []
    for floor_tag, tag in sorted(stacked, key=lambda s: s[1]):
        opening = ctx.plan.by_tag(tag)
        block = blocks.get(tag)
        if not opening.fireblock or block is None:
            deck = ctx.plan.by_tag(floor_tag)
            sheet = getattr(getattr(deck, "subfloor", None), "material_ref", "plywood-subfloor")
            out.append(_fail(_CID, f"{tag} is a floor chase in a multi-storey shaft with no "
                             "fireblock; add `fireblock=(Layer(name=\"fireblock\", "
                             f"material_ref=\"{sheet}\", thickness=inch(0.75), "
                             "function=LayerFunction.SHEATHING),), "
                             "fireblock_sealant=\"firestop-sealant\"`", (tag,), _CODE))
            continue
        runs = ", ".join(t for t, _ in block.penetrations) or "none"
        wool = any(layer.function is LayerFunction.INSULATION
                   for layer in opening.fireblock[1:])
        if block.min_web_m is not None and block.min_web_m < min_web and not wool:
            a, b = block.min_web_between
            out.append(_fail(_CID, f"{tag}: the fireblock sheet between {a} and {b} is "
                             f"{block.min_web_m / 0.0254:.2f}\" (< "
                             f"{min_web / 0.0254:.2f}\"), a sliver; pack the crossing with "
                             "a mineral-wool layer under the sheet", (tag, a), _CODE))
            continue
        if block.penetrations and not opening.fireblock_sealant:
            out.append(_fail(_CID, f"{tag}: the fireblock is penetrated by {runs} and names "
                             "no fireblock_sealant for the annular spaces (R302.11 item 4)",
                             (tag,), _CODE))
            continue
        out.append(_pass(_CID, f"{tag} is fireblocked in the deck plane "
                         f"({opening.fireblock[0].material_ref}); penetrations sealed: "
                         f"{runs}", _CODE))
    return out
