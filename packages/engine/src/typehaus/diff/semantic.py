"""Semantic model of an IFC file — the vocabulary two *unrelated* IFCs can be compared in.

``haus diff`` reconciles an architect's edit of *our own* export: same authoring tool, same
GlobalIds, same conventions. Comparing against a foreign IFC (the archived catlin-house
builder's export, → 30 WP3.7 migration equivalence) shares none of that. Identity is gone,
naming is gone, and the two files model the same house with different conventions — most
importantly the reference draws every *layer* of a wall as its own ``IfcWall`` where TypeHaus
emits one wall carrying an ``IfcMaterialLayerSet``.

So both sides are lifted into one neutral vocabulary before anything is compared:

* **spatial hierarchy** — buildings and storeys, normalized to storey keys and elevations;
* **entities** — one record per occurrence: category, storey, world-coordinate centroid and
  bounding box, material-layer names, aggregated framing-member count;
* **runs** — face-adjacent same-category entities merged into the thing a builder would call
  one element (a wall line with all its layers; a wall split at grid nodes on one side and
  drawn as one run on the other), so layer-per-element and layerset-per-element conventions
  become comparable.

Geometry comes from ifcopenshell's shape iterator in world coordinates, which returns metres
regardless of the file's length unit — the reference is authored in millimetres.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

# IFC class → neutral category. Classes absent here are still censused under their raw class
# name; the map exists to give the categories we *compare* a stable, tool-neutral name.
CATEGORY_BY_IFC_CLASS: Mapping[str, str] = {
    "IfcWall": "wall",
    "IfcWallStandardCase": "wall",
    "IfcSlab": "slab",
    "IfcRoof": "roof",
    "IfcFooting": "footing",
    "IfcColumn": "column",
    "IfcBeam": "beam",
    "IfcMember": "member",
    "IfcDoor": "door",
    "IfcWindow": "window",
    "IfcStair": "stair",
    "IfcStairFlight": "stair",
    "IfcRailing": "railing",
    "IfcCovering": "covering",
    "IfcOpeningElement": "opening",
    "IfcBuildingElementProxy": "proxy",
}

# Categories worth a per-entity geometric comparison. Everything else is compared as a census
# count — matching 2000 individual studs between two framing solvers is noise, their count
# and their host element's geometry is the signal.
COMPARED_CATEGORIES: tuple[str, ...] = ("wall", "slab", "roof", "footing", "door", "window")

# Two entities belong to the same run when they are face-adjacent: their boxes touch (or
# overlap) within this gap on one axis while overlapping on the other two. Sized just over a
# millimetre-authored file's rounding, well under any real construction gap.
RUN_ADJACENCY_TOLERANCE_M = 0.02
# ...and they must overlap by at least this fraction of the *larger* extent on two axes, which
# is what separates a stacked layer or a collinear continuation from a corner or a tee.
RUN_OVERLAP_FRACTION = 0.5

_STOREY_SUFFIXES = (" floor", " level", " storey", " story")


@dataclass(frozen=True)
class SemanticStorey:
    """One storey of either model, keyed so the two naming conventions line up."""

    name: str
    key: str
    elevation_m: float | None   # None => the file never stated one (never guessed)
    building: str


@dataclass(frozen=True)
class SemanticEntity:
    """One comparable occurrence, or one merged run of them."""

    guid: str
    name: str
    category: str
    storey_key: str
    centroid_m: tuple[float, float, float]
    size_m: tuple[float, float, float]
    layer_names: tuple[str, ...] = ()      # from an IfcMaterialLayerSet, when the file has one
    layer_bands: int = 1                   # distinct across-thickness bands merged into a run
    framing_member_count: int = 0          # aggregated IfcMember/IfcBeam descendants
    opening_count: int = 0                 # IfcRelVoidsElement openings cut into it
    merged_from: tuple[str, ...] = ()      # names of the occurrences merged into this run

    @property
    def layer_count(self) -> int:
        """Layers however the file states them: a layer set, or merged adjacent bands."""
        return max(len(self.layer_names), self.layer_bands)

    @property
    def plan_length_m(self) -> float:
        return max(self.size_m[0], self.size_m[1])

    @property
    def plan_thickness_m(self) -> float:
        return min(self.size_m[0], self.size_m[1])

    def as_dict(self) -> dict:
        return {
            "name": self.name, "category": self.category, "storey": self.storey_key,
            "centroid_m": [round(v, 4) for v in self.centroid_m],
            "size_m": [round(v, 4) for v in self.size_m],
            "layer_count": self.layer_count, "layer_names": list(self.layer_names),
            "framing_member_count": self.framing_member_count,
            "opening_count": self.opening_count,
            "merged_from": list(self.merged_from),
        }



class AmbiguousStoreyDatum(ValueError):
    """Several buildings state the same storey key and no datum says which one governs."""


def pick_datum_storey(key: str, candidates: list[SemanticStorey],
                      datum_buildings: tuple[str, ...] | None) -> SemanticStorey:
    """Choose the storey that owns ``key``'s datum among same-keyed candidates.

    Storey keys are shared vocabulary ("main", "basement"), not identity: a file may state
    one key on several buildings, at different elevations. ``datum_buildings`` names which
    buildings govern, in priority order; with one candidate the question doesn't arise.
    Anything else is ambiguous, and picking silently would make the comparison depend on
    file order.
    """
    if len(candidates) == 1:
        return candidates[0]
    for building in datum_buildings or ():
        owned = [item for item in candidates if item.building == building]
        if len(owned) == 1:
            return owned[0]
        if owned:
            raise AmbiguousStoreyDatum(
                f"building {building!r} states storey key {key!r} "
                f"{len(owned)} times: {[item.name for item in owned]}"
            )
    raise AmbiguousStoreyDatum(
        f"storey key {key!r} is stated by "
        f"{sorted({item.building for item in candidates})}; pass datum_buildings to say "
        "which building owns the datum"
    )


@dataclass
class SemanticModel:
    """One IFC file lifted into the neutral vocabulary."""

    label: str
    schema: str
    storeys: tuple[SemanticStorey, ...] = ()
    entities: tuple[SemanticEntity, ...] = ()
    class_census: Mapping[str, int] = field(default_factory=dict)   # raw IFC class → count
    buildings: tuple[str, ...] = ()

    def in_category(self, category: str) -> list[SemanticEntity]:
        return [item for item in self.entities if item.category == category]

    def storey(self, key: str,
               datum_buildings: tuple[str, ...] | None = None) -> SemanticStorey | None:
        """The authoritative storey for ``key`` — the same rule the equivalence report uses.

        This was first-wins while the report was last-wins, so the two could disagree about
        which of several same-keyed storeys a comparison meant.
        """
        matches = [item for item in self.storeys if item.key == key]
        if not matches:
            return None
        return pick_datum_storey(key, matches, datum_buildings)

    def category_census(self) -> dict[tuple[str, str], int]:
        """(storey key, category) → count, over the compared categories' runs."""
        census: dict[tuple[str, str], int] = {}
        for item in self.entities:
            key = (item.storey_key, item.category)
            census[key] = census.get(key, 0) + 1
        return census

    def framing_member_total(self) -> int:
        return sum(item.framing_member_count for item in self.entities)


def normalize_storey_key(name: str, aliases: Mapping[str, str] | None = None) -> str:
    """"Main Floor" → "main", "Attic Floor" → "attic"; explicit aliases win.

    Aliases are how a *specific* pair of models declares equivalences its naming cannot
    express — the reference's "Sunken Garden Floor" is part of TypeHaus' basement storey.
    """
    raw = (name or "").strip()
    if aliases and raw in aliases:
        return aliases[raw]
    key = raw.lower()
    for suffix in _STOREY_SUFFIXES:
        if key.endswith(suffix):
            key = key[: -len(suffix)]
    key = re.sub(r"\s+", "-", key.strip())
    return aliases.get(key, key) if aliases else key


def semantic_model_from_ifc(path: Path, label: str,
                            storey_aliases: Mapping[str, str] | None = None,
                            drop_storeys: Iterable[str] = ()) -> SemanticModel:
    """Read an IFC file into the neutral vocabulary. Requires ifcopenshell.

    ``drop_storeys`` names normalized storey keys to leave out entirely — the honest way to
    exclude something the other side deliberately does not model (the reference's explicit
    "placeholder" breezeway), rather than letting it read as a deletion.
    """
    try:
        import ifcopenshell
    except ImportError as exc:  # pragma: no cover - exercised only in slim installs
        raise RuntimeError("semantic IFC comparison requires ifcopenshell") from exc

    file = ifcopenshell.open(str(path))
    dropped = set(drop_storeys)
    storeys, storey_of_product = _spatial_structure(file, storey_aliases, dropped)
    class_census: dict[str, int] = {}
    for product in file.by_type("IfcProduct"):
        name = product.is_a()
        class_census[name] = class_census.get(name, 0) + 1

    children = _aggregation_children(file)
    entities: list[SemanticEntity] = []
    for product in file.by_type("IfcElement"):
        category = CATEGORY_BY_IFC_CLASS.get(product.is_a())
        if category not in COMPARED_CATEGORIES:
            continue
        storey_key = storey_of_product.get(product.id())
        if storey_key is None or storey_key in dropped:
            continue
        bounds = _product_bounds(product, children)
        if bounds is None:
            continue
        low, high = bounds
        entities.append(SemanticEntity(
            guid=product.GlobalId,
            name=product.Name or product.GlobalId,
            category=category,
            storey_key=storey_key,
            centroid_m=tuple((low[i] + high[i]) / 2 for i in range(3)),  # type: ignore[arg-type]
            size_m=tuple(high[i] - low[i] for i in range(3)),            # type: ignore[arg-type]
            layer_names=_layer_names(product),
            framing_member_count=_framing_member_count(product, children),
            opening_count=len(getattr(product, "HasOpenings", ()) or ()),
        ))

    return SemanticModel(
        label=label,
        schema=file.schema,
        storeys=storeys,
        entities=tuple(merge_runs(entities)),
        class_census=class_census,
        buildings=tuple(sorted(b.Name or b.GlobalId for b in file.by_type("IfcBuilding"))),
    )


def _spatial_structure(file, aliases: Mapping[str, str] | None, dropped: set
                       ) -> tuple[tuple[SemanticStorey, ...], dict[int, str]]:
    """Storeys (with their building) + every element's storey, through aggregation."""
    import ifcopenshell.util.placement
    import ifcopenshell.util.unit

    scale = ifcopenshell.util.unit.calculate_unit_scale(file)
    building_of_storey: dict[int, str] = {}
    for relation in file.by_type("IfcRelAggregates"):
        parent = relation.RelatingObject
        if parent.is_a("IfcBuilding"):
            for child in relation.RelatedObjects:
                building_of_storey[child.id()] = parent.Name or parent.GlobalId

    storeys: list[SemanticStorey] = []
    key_by_storey_id: dict[int, str] = {}
    for storey in file.by_type("IfcBuildingStorey"):
        key = normalize_storey_key(storey.Name or "", aliases)
        if key in dropped:
            continue
        key_by_storey_id[storey.id()] = key
        # The placement is authoritative: it is what every element in the storey is measured
        # from, whereas the ``Elevation`` attribute is a label a foreign exporter may write in
        # the wrong unit (the reference does exactly that). Fall back to it only when the
        # storey has no placement at all.
        elevation = None
        if storey.ObjectPlacement is not None:
            matrix = ifcopenshell.util.placement.get_local_placement(storey.ObjectPlacement)
            elevation = float(matrix[2][3]) * scale
        elif storey.Elevation is not None:
            elevation = float(storey.Elevation) * scale
        storeys.append(SemanticStorey(name=storey.Name or "", key=key, elevation_m=elevation,
                                      building=building_of_storey.get(storey.id(), "")))

    storey_of_product: dict[int, str] = {}
    for relation in file.by_type("IfcRelContainedInSpatialStructure"):
        key = key_by_storey_id.get(relation.RelatingStructure.id())
        if key is None:
            continue
        for element in relation.RelatedElements:
            storey_of_product[element.id()] = key
    # An element aggregated under another (a layer wall inside a wall assembly) inherits its
    # parent's storey — the reference only spatially contains the assembly.
    for _ in range(4):  # aggregation nests a few levels deep at most
        for relation in file.by_type("IfcRelAggregates"):
            key = storey_of_product.get(relation.RelatingObject.id())
            if key is None:
                continue
            for child in relation.RelatedObjects:
                storey_of_product.setdefault(child.id(), key)
    return tuple(storeys), storey_of_product


def _aggregation_children(file) -> dict[int, list]:
    children: dict[int, list] = {}
    for relation in file.by_type("IfcRelAggregates"):
        children.setdefault(relation.RelatingObject.id(), []).extend(relation.RelatedObjects)
    return children


def _framing_member_count(product, children: Mapping[int, list]) -> int:
    """Members/beams aggregated under this element, at any depth."""
    total = 0
    for child in children.get(product.id(), ()):
        if CATEGORY_BY_IFC_CLASS.get(child.is_a()) in ("member", "beam"):
            total += 1
        total += _framing_member_count(child, children)
    return total


def _layer_names(product) -> tuple[str, ...]:
    for relation in getattr(product, "HasAssociations", ()) or ():
        if not relation.is_a("IfcRelAssociatesMaterial"):
            continue
        material = relation.RelatingMaterial
        layer_set = getattr(material, "ForLayerSet", None) or material
        layers = getattr(layer_set, "MaterialLayers", None)
        if layers:
            return tuple((layer.Name or getattr(layer.Material, "Name", "") or "layer")
                         for layer in layers)
    return ()


def _product_bounds(product, children: Mapping[int, list]):
    """World-coordinate (low, high) corners, or None when nothing has geometry.

    A container without its own representation (the reference's stud walls, which exist only
    to aggregate members) borrows the extent of what it aggregates, so it still lands on the
    wall line it belongs to instead of vanishing from the comparison.
    """
    from typehaus.diff.ifc_adapter import product_world_bounds

    own = product_world_bounds(product)
    if own is not None:
        return own
    boxes = [box for box in (_product_bounds(child, children)
                             for child in children.get(product.id(), ())) if box is not None]
    if not boxes:
        return None
    low = tuple(min(box[0][i] for box in boxes) for i in range(3))
    high = tuple(max(box[1][i] for box in boxes) for i in range(3))
    return low, high


def _interval_overlap(a_low: float, a_high: float, b_low: float, b_high: float) -> float:
    return min(a_high, b_high) - max(a_low, b_low)


def _face_adjacent(a: SemanticEntity, b: SemanticEntity) -> bool:
    """True when two entities are the same construction seen as separate occurrences."""
    overlapping_axes = 0
    for axis in range(3):
        a_low = a.centroid_m[axis] - a.size_m[axis] / 2
        a_high = a.centroid_m[axis] + a.size_m[axis] / 2
        b_low = b.centroid_m[axis] - b.size_m[axis] / 2
        b_high = b.centroid_m[axis] + b.size_m[axis] / 2
        overlap = _interval_overlap(a_low, a_high, b_low, b_high)
        if overlap < -RUN_ADJACENCY_TOLERANCE_M:
            return False  # a real gap on this axis: separate constructions
        largest = max(a.size_m[axis], b.size_m[axis])
        if largest <= 0 or overlap >= RUN_OVERLAP_FRACTION * largest:
            overlapping_axes += 1
    # Layers stack (or segments continue) across exactly one axis and share the other two;
    # a corner or a tee shares only one, which is what keeps them apart.
    return overlapping_axes >= 2


def merge_runs(entities: Sequence[SemanticEntity]) -> list[SemanticEntity]:
    """Merge face-adjacent same-category entities of one storey into construction runs."""
    merged: list[SemanticEntity] = []
    for category in sorted({item.category for item in entities}):
        for storey in sorted({item.storey_key for item in entities
                              if item.category == category}):
            group = [item for item in entities
                     if item.category == category and item.storey_key == storey]
            merged.extend(_merge_group(group))
    return merged


def _merge_group(group: list[SemanticEntity]) -> list[SemanticEntity]:
    parent = list(range(len(group)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            if find(i) != find(j) and _face_adjacent(group[i], group[j]):
                parent[find(j)] = find(i)

    clusters: dict[int, list[SemanticEntity]] = {}
    for index, item in enumerate(group):
        clusters.setdefault(find(index), []).append(item)
    return [_fuse(members) for members in clusters.values()]


def _fuse(members: list[SemanticEntity]) -> SemanticEntity:
    if len(members) == 1:
        return members[0]
    lows = [tuple(item.centroid_m[axis] - item.size_m[axis] / 2 for axis in range(3))
            for item in members]
    highs = [tuple(item.centroid_m[axis] + item.size_m[axis] / 2 for axis in range(3))
             for item in members]
    low = tuple(min(point[axis] for point in lows) for axis in range(3))
    high = tuple(max(point[axis] for point in highs) for axis in range(3))
    size = tuple(high[axis] - low[axis] for axis in range(3))
    # The run's thickness axis is its smallest plan dimension; distinct bands across it are
    # the file's layers when it states them one element at a time.
    thickness_axis = 0 if size[0] <= size[1] else 1
    bands = {round(item.centroid_m[thickness_axis], 3) for item in members}
    lead = max(members, key=lambda item: item.size_m[0] * item.size_m[1] * item.size_m[2])
    return SemanticEntity(
        guid=lead.guid,
        name=lead.name,
        category=lead.category,
        storey_key=lead.storey_key,
        centroid_m=tuple((low[axis] + high[axis]) / 2 for axis in range(3)),  # type: ignore[arg-type]
        size_m=size,  # type: ignore[arg-type]
        layer_names=max((item.layer_names for item in members), key=len),
        layer_bands=len(bands),
        framing_member_count=sum(item.framing_member_count for item in members),
        opening_count=sum(item.opening_count for item in members),
        merged_from=tuple(sorted(item.name for item in members)),
    )
