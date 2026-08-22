"""Doors and windows by type — the schedule the BOM never had.

A-601 draws the opening schedule off ``model.openings``, so the data has been resolved and
presented all along; it simply never reached ``bill_of_materials``. Doors and windows are
usually the second-largest line on a residential order after framing, and an estimate that
silently omits them reads as complete while being wrong by a lot.

Grouped by type ref, because that is the unit an order is placed in: eight WT-2736s are one
line on a window quote whatever walls they land in. An opening with no ``type_ref`` — a bare
rough void — is reported as its own UNKNOWN row rather than dropped, for the same reason the
finishes section reports an unfinished room.
"""

from __future__ import annotations

from typehaus.model.types import DoorType, WindowType
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel


def _size(width_in: float, height_in: float) -> str:
    """``27" x 36"``, trimming a trailing ``.0`` so a whole-inch unit reads as one."""
    return " x ".join(f"{value:g}\"" for value in (width_in, height_in))


def _product_description(kind: str, type_ref: str,
                         product: DoorType | WindowType | None,
                         qualifier: str | None,
                         width_in: float, height_in: float, arched: bool) -> str:
    """What this row IS, in words a supplier could quote from.

    This field is the row's human description everywhere downstream —
    ``cli/prices._DESCRIPTION_FIELDS`` reads ``product`` — so it lands in the estimate, the
    CSV and the task export. It used to be ``getattr(product, "name", None) or "UNKNOWN"``,
    and neither :class:`~typehaus.model.types.WindowType` nor
    :class:`~typehaus.model.types.DoorType` HAS a ``name`` field — only ``FurnitureType``
    does. So the fallback fired on every row, and every opening line in the estimate read
    UNKNOWN whether or not the type resolved. The bug was invisible because it looked
    exactly like the thing it was supposed to report.

    Nothing here invents a product name: the type tag IS the name a house orders by, and
    the operation and size are read off the resolved type. An opening with no type still
    says so, in its own words rather than in the same word a resolved one used.
    """
    size = _size(width_in, height_in)
    head = " arched" if arched else ""
    # ``kind`` is the resolver's own vocabulary and one of its values is already two words:
    # "rough_opening" would otherwise print as "rough_opening rough opening".
    noun = kind.replace("_", " ")
    if product is None:
        if type_ref:
            # A type_ref naming a type the library does not carry. Worth reading as its own
            # sentence: it is a dangling reference, not a deliberately bare rough opening.
            return f"{type_ref} — unresolved {noun} type, {size}{head}"
        return f"{noun}, {size}{head} (no type)"
    return f"{type_ref} — {qualifier} {noun}, {size}{head}"


def opening_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per opening type: count, nominal size, and the tags it covers."""
    door_types = {item.tag: item for item in model.plan.library.door_types}
    window_types = {item.tag: item for item in model.plan.library.window_types}

    groups: dict[tuple[str, str, float, float], dict[str, object]] = {}
    for opening in model.openings:
        key = (opening.kind, opening.type_ref or "", round(opening.width_m / M_PER_IN, 2),
               round(opening.height_m / M_PER_IN, 2))
        entry = groups.setdefault(key, {"count": 0, "tags": [], "arched": False})
        entry["count"] += 1
        entry["tags"].append(opening.tag)
        # An arched head is a different product, not a trim decision, so it stays visible
        # on the row rather than being averaged away into a rectangular opening's count.
        entry["arched"] = bool(entry["arched"]) or opening.arch_rise_m > 1e-9

    rows = []
    for (kind, type_ref, width_in, height_in), entry in sorted(groups.items()):
        product = door_types.get(type_ref) or window_types.get(type_ref)
        # The operation is what is actually ordered: a 36x60 casement and a 36x60 picture
        # unit are the same hole and different products, and for a door the leaf makeup
        # (glazed vs solid) moves the price as much as the operation does. Both ride in the
        # qualifier rather than the key because the type ref already separates the rows.
        operation = getattr(getattr(product, "operation", None), "value", None)
        qualifier = operation
        if product is not None and kind == "door":
            qualifier = f"{operation} · {'glazed' if product.glazed else 'solid'}"
        rows.append({
            "kind": kind,
            "type": type_ref or None,
            "product": _product_description(kind, type_ref, product, qualifier,
                                           width_in, height_in, bool(entry["arched"])),
            "known": product is not None,
            "operation": operation,
            "qualifier": qualifier,
            "width_in": width_in,
            "height_in": height_in,
            "arched": entry["arched"],
            "count": int(entry["count"]),
            "tags": sorted(entry["tags"]),
        })
    return rows
