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

from typehaus.model.enums import DoorOperation, LayerFunction
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
    CSV and the task export. Neither :class:`~typehaus.model.types.WindowType` nor
    :class:`~typehaus.model.types.DoorType` has a ``name`` field (only ``FurnitureType``
    does), so this cannot fall back to ``getattr(product, "name", None)``.

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


# A door leaf that hangs on butt hinges and takes a lockset. The two exclusions are not
# "doors we happen not to like": an OVERHEAD sectional has no lockset and no hinges (its
# operator is its own scope), and a POCKET door's hardware is the track, jamb kit and edge
# pull that ship with the pocket frame — both are billed elsewhere, and billing a passage
# set against either is a double-count.
_NO_DOOR_HARDWARE = (DoorOperation.OVERHEAD, DoorOperation.POCKET)


def _host_structure(model: ResolvedModel, host_wall: str | None) -> str:
    """The coarse material a host wall's STRUCTURE layer is made of, or ``""``.

    This is the axis "does this opening land in a concrete wall" — the question a window
    buck, a blockout or a lintel is bought by, and one nothing in the BOM could answer.
    The STRUCTURE layer's ``material_ref`` is the same discriminator
    ``takeoff/wall_structure.py`` groups its pours by, so the two tables name a wall's
    material the same way.
    """
    if not host_wall:
        return ""
    wall = model.wall(host_wall)
    if wall is None:
        return ""
    for layer in wall.layers:
        if layer.function == LayerFunction.STRUCTURE.value:
            return layer.material_ref or ""
    return ""


def opening_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per opening type: count, nominal size, and the tags it covers.

    ``takes_hardware`` is the predicate a lockset-and-hinges scope is bought by. It does not
    enter the group key — the type ref already separates the rows and the operation is a
    property of the type, so every opening in a group agrees on it.

    ``host_assembly`` and ``host_structure`` **do** enter the key, because they are
    properties of the *hole*, not of the product: the same DT-EXT-SWING36 in a framed wall
    and in a 12" pour is one order of doors and two different openings to make. They must be
    single-valued strings rather than a tuple of the hosts, because a price driver compares
    one literal — a tuple field is unfilterable, so a row carrying ``("W-A", "W-B")`` could
    never be selected by either.
    """
    door_types = {item.tag: item for item in model.plan.library.door_types}
    window_types = {item.tag: item for item in model.plan.library.window_types}

    groups: dict[tuple[str, str, float, float, str, str], dict[str, object]] = {}
    for opening in model.openings:
        host_assembly = ""
        wall = model.wall(opening.host_wall) if opening.host_wall else None
        if wall is not None:
            host_assembly = wall.assembly or ""
        key = (opening.kind, opening.type_ref or "", round(opening.width_m / M_PER_IN, 2),
               round(opening.height_m / M_PER_IN, 2), host_assembly,
               _host_structure(model, opening.host_wall))
        entry = groups.setdefault(key, {"count": 0, "tags": [], "arched": False})
        entry["count"] += 1
        entry["tags"].append(opening.tag)
        # An arched head is a different product, not a trim decision, so it stays visible
        # on the row rather than being averaged away into a rectangular opening's count.
        entry["arched"] = bool(entry["arched"]) or opening.arch_rise_m > 1e-9

    rows = []
    for ((kind, type_ref, width_in, height_in, host_assembly, host_structure),
         entry) in sorted(groups.items()):
        product = door_types.get(type_ref) or window_types.get(type_ref)
        # The operation is what is actually ordered: a 36x60 casement and a 36x60 picture
        # unit are the same hole and different products, and for a door the leaf makeup
        # (glazed vs solid) moves the price as much as the operation does. Both ride in the
        # qualifier rather than the key because the type ref already separates the rows.
        raw_operation = getattr(product, "operation", None)
        operation = getattr(raw_operation, "value", None)
        qualifier = operation
        if product is not None and kind == "door":
            qualifier = f"{operation} · {'glazed' if product.glazed else 'solid'}"
        rows.append({
            "kind": kind,
            "type": type_ref or None,
            "takes_hardware": kind == "door" and raw_operation not in _NO_DOOR_HARDWARE,
            "host_assembly": host_assembly or None,
            "host_structure": host_structure or None,
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
