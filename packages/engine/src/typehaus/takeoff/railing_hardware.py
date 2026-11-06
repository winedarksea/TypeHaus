"""Guard and handrail mounting hardware, counted off the parts the resolver drew (S-602).

Not BOM rows: a railing bills by its run in ``railings.py`` and the kit carries these. This
is the connection list a framing inspector grades: bases, brackets, their fasteners and the
backing behind them. Every count is a drawn solid; fasteners per part follow the hole
patterns ``resolve/railings`` drills.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.model.structure import Railing
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.railings.parts import railing_type

#: ``surface_assembly``: a 2 x 2 hole pattern in every cast base.
_HOLES_PER_BASE = 4
#: ``fascia_assembly``: four mounting holes per bracket (2 x 2 straight, 1 x 2 per corner
#: leaf), and two post screws each side of the pocket.
_HOLES_PER_BRACKET = 4
_POST_SCREWS_PER_BRACKET = 4

UNTYPED = "(untyped)"


def inch_text(value_in: float) -> str:
    """5/16", 6", 1 1/2" — to the 1/16" when it lands on one, else three figures."""
    sixteenths = value_in * 16
    if abs(sixteenths - round(sixteenths)) > 0.01:
        return f'{value_in:.3g}"'
    sign = "-" if sixteenths < 0 else ""
    whole, fraction = divmod(abs(round(sixteenths)), 16)
    if not fraction:
        return f'{sign}{whole}"'
    from math import gcd

    common = gcd(fraction, 16)
    text = f"{fraction // common}/{16 // common}"
    return f'{sign}{whole} {text}"' if whole else f'{sign}{text}"'


def _size(diameter, length) -> str:
    return f"{inch_text(diameter.inches)} x {inch_text(length.inches)}"


def _part(railing: Railing, solid) -> tuple[str, int]:
    """``("FASCIA-BRACKET", 3)`` off ``RL-SG-BALCONY-FASCIA-BRACKET3``."""
    suffix = solid.tag[len(railing.tag) + 1:]
    word = suffix.rstrip("0123456789")
    return word, int(suffix[len(word):] or 0)


def railing_hardware_rows(model: ResolvedModel) -> list[dict[str, object]]:
    """``{type, part, product, size, count, railings}`` per railing type and part."""
    solids = defaultdict(list)
    for solid in model.solids:
        if solid.category == "railing" and solid.host_ref:
            solids[solid.host_ref].append(solid)
    rows: dict[tuple[str, str, str, str], dict[str, object]] = {}

    def add(railing: Railing, part: str, product: str, size: str, count: int) -> None:
        key = (railing.type_ref or UNTYPED, part, product, size)
        row = rows.setdefault(key, {"type": key[0], "part": part, "product": product,
                                    "size": size, "count": 0, "railings": set()})
        row["count"] += count
        row["railings"].add(railing.tag)

    for railing in model.plan.elements_of_kind("Railing"):
        product = railing_type(model.plan.library, railing)
        surface = product.surface_mount if product is not None else None
        fascia = product.fascia_mount if product is not None else None
        parts = solids.get(railing.tag, ())
        words = {_part(railing, solid)[0] for solid in parts}
        if "POST" in words and not words & {"BASE", "FASCIA-BRACKET"}:
            # Posts drawn with no mount: say so rather than list nothing.
            add(railing, "post mount, NOT MODELLED", "—", "—",
                sum(1 for solid in parts if _part(railing, solid)[0] == "POST"))
        for solid in parts:
            word, index = _part(railing, solid)
            if word == "BASE" and surface is not None:
                add(railing, "surface post base", solid.product or surface.product,
                    f"{inch_text(surface.base_width.inches)} sq", 1)
            elif word == "ANCHORS" and surface is not None:
                wood = railing.surface_post_mounts[index - 1].substrate == "wood"
                add(railing, "base screw, wood" if wood else "base anchor, concrete", "—",
                    _size(surface.wood_screw_diameter, surface.wood_screw_length) if wood
                    else _size(surface.concrete_anchor_diameter,
                               surface.concrete_anchor_length), _HOLES_PER_BASE)
            elif word == "BACKING":
                block = railing.surface_post_mounts[index - 1].backing_size
                add(railing, f"post backing block, {solid.material or '—'}", "—",
                    " x ".join(inch_text(v.inches) for v in block) if block else "—", 1)
            elif word == "FASCIA-BRACKET" and fascia is not None:
                add(railing, "fascia post bracket", solid.product or "—",
                    f"{inch_text(product.post_width.inches)} post"
                    if product.post_width else "—", 1)
                add(railing, "bracket screw" if fascia.fastener == "wood_screw"
                    else "bracket bolt", fascia.fastener_product,
                    _size(fascia.bolt_diameter, fascia.bolt_length), _HOLES_PER_BRACKET)
                add(railing, "post screw, self-drilling", "—",
                    _size(fascia.post_screw_diameter, fascia.post_screw_length),
                    _POST_SCREWS_PER_BRACKET)
            elif word == "FASCIA-INSERT":
                add(railing, "post-bottom insert", "—", "—", 1)
            elif word == "FASCIA-FOOTBLOCK" and fascia is not None:
                add(railing, "foot block", solid.product or fascia.foot_block_product, "—", 1)
                add(railing, "foot block screw, into fascia", "—",
                    _size(fascia.post_screw_diameter, fascia.foot_block_fascia_screw_length), 1)
                add(railing, "post screw, self-drilling", "—",
                    _size(fascia.post_screw_diameter, fascia.post_screw_length), 1)
            elif word == "BRACKET":
                add(railing, "rail bracket", "—", "—", 1)
            elif word == "RETURN":
                add(railing, "rail return to wall", "—", "—", 1)
            elif word == "ENDPLATE":
                add(railing, "wall end plate", "—", "—", 1)
            elif word == "COLBRK":
                add(railing, "rail bracket on column", "—", "—", 1)
    return [{**row, "railings": sorted(row["railings"])}
            for _key, row in sorted(rows.items())]
