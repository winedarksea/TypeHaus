"""Every printable thing in a resolved model, as one true solid with its policy row.

The IR's elements, the placeables (drawn through the glTF emitter's own code by
``solids3d.recorder``) and the countertop slabs. A floor is printed as its whole package,
filled from its own joists' underside to its deck: the joists are framing and never print,
and a 3/4" deck alone is a tenth of a millimetre at 1:128.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from typehaus.print3d.policy import PrintSettings, Treatment, placeable_kind, treatment
from typehaus.resolve.model import ResolvedModel
from typehaus.solids3d.convert import element_manifold, to_manifold, union
from typehaus.solids3d.recorder import Primitive, placeable_primitives


@dataclass
class PrintItem:
    uid: str
    tag: str
    kind: str
    treatment: Treatment
    solid: object  # manifold3d.Manifold
    storey: str | None = None
    #: A wall's axis, the frame it thickens in.
    axis: tuple[tuple[float, float], tuple[float, float]] | None = None
    #: A placeable's primitives, whose explicit dimensions grade a furniture piece.
    primitives: list[Primitive] = field(default_factory=list)


@dataclass
class Collection:
    items: list[PrintItem]
    dropped: Counter  # kind -> count, by policy


def collect(model: ResolvedModel, settings: PrintSettings) -> Collection:
    index = _records(model)
    dropped: Counter = Counter()
    items: list[PrintItem] = []
    ir_uids = set()
    for element in sorted(model.geometry.elements, key=lambda item: item.uid):
        ir_uids.add(element.uid)
        record = index.get(element.uid)
        kind = _site_kind(model, element.kind, record)
        rule = treatment(kind, settings)
        if rule is Treatment.DROP:
            dropped[kind] += 1
            continue
        solid = (_floor_package(model, element) if element.kind == "floor"
                 else element_manifold(element))
        if solid.is_empty():
            continue
        items.append(PrintItem(element.uid, getattr(record, "tag", element.uid), kind, rule,
                               solid, getattr(record, "storey", None),
                               getattr(record, "axis", None) if element.kind == "wall" else None))
    items += _placeables(model, settings, ir_uids, dropped)
    from typehaus.resolve.geometry_countertops import countertop_prisms

    rule = treatment("countertop", settings)
    for top in sorted(model.countertops, key=lambda item: item.uid):
        solid = union(to_manifold(prism) for prism in countertop_prisms(model, top))
        if rule is not Treatment.DROP and not solid.is_empty():
            items.append(PrintItem(top.uid, top.tag, "countertop", rule, solid,
                                   getattr(top, "storey", None)))
    return Collection(items, dropped)


def _placeables(model, settings, ir_uids, dropped) -> list[PrintItem]:
    from typehaus.emit.gltf.canvas_objects import CanvasDrawContext
    from typehaus.resolve.placeable_fixity import fixity_types, is_fixed

    context = CanvasDrawContext.of(model)
    fixity = fixity_types(model.plan)
    out = []
    for item in sorted(model.canvas_objects, key=lambda co: co.uid):
        if item.domain == "opening" or item.uid in ir_uids:
            continue
        kind = placeable_kind(item, context.types.get(item.type_ref), is_fixed(item, fixity))
        rule = treatment(kind, settings)
        if rule is Treatment.DROP or (rule is Treatment.LOOSE and not settings.furniture):
            dropped[kind] += 1
            continue
        primitives = placeable_primitives(item, context)
        solid = union(to_manifold(primitive.solid) for primitive in primitives)
        if not solid.is_empty():
            out.append(PrintItem(item.uid, item.tag, kind, rule, solid, item.storey,
                                 primitives=primitives))
    return out


def _floor_package(model: ResolvedModel, element):
    """The deck's plan, solid from the underside of its own joists to the deck's top."""
    deck = element_manifold(element)
    framing = model.geometry.by_uid(f"{element.uid}::framing")
    low, high = deck.bounding_box()[2], deck.bounding_box()[5]
    if framing is not None:
        low = min(low, element_manifold(framing).bounding_box()[2])
    return deck.project().extrude(high - low).translate((0.0, 0.0, low))


def _site_kind(model: ResolvedModel, kind: str, record) -> str:
    """A pour slab no room owns is site flatwork (a walk, a drive, a pad in the yard)."""
    from typehaus.resolve.room_lookup import room_owning
    from typehaus.resolve.solid_categories import is_pour_slab

    category = getattr(record, "category", None)
    if kind != "slab" or category is None or not is_pour_slab(category):
        return kind
    xs = [x for x, _ in record.outline]
    ys = [y for _, y in record.outline]
    centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    return kind if room_owning(model, record.storey, centre) is not None else "site"


def _records(model: ResolvedModel) -> dict[str, object]:
    """uid -> the resolved record behind an IR element (its tag, storey, axis, category)."""
    index: dict[str, object] = {}
    for name in ("walls", "floors", "ceilings", "roofs", "stairs", "soffits", "solids",
                 "openings", "countertops"):
        for record in getattr(model, name, ()):
            index.setdefault(record.uid, record)
    return index
