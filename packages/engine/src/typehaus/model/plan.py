"""PlanModel — the validated whole-building authored model (→ 02 §Pipeline)."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from pydantic import Field

from typehaus.model.assembly import Assembly, ConstructionRule
from typehaus.model.base import Element, HausModel
from typehaus.model.electrical import Circuit, LoadManagement
from typehaus.model.landscape import PlantType
from typehaus.model.materials import Material
from typehaus.model.product import Product
from typehaus.model.project import Building, Project, Storey
from typehaus.model.types import (
    ApplianceType,
    DoorType,
    DuctProductType,
    ElectricalDeviceType,
    EquipmentType,
    FixtureType,
    FurnitureType,
    RailingType,
    RegisterType,
    WindowType,
)
from typehaus.model.views import Transition


class Library(HausModel):
    """Shared definitions the plan references by tag (assemblies, materials, types)."""

    materials: tuple[Material, ...] = ()
    assemblies: tuple[Assembly, ...] = ()
    # The chosen-product catalog. Identity only — never a price (#28); a material or a
    # ``*Type`` names one by tag through its ``product_ref``.
    products: tuple[Product, ...] = ()
    door_types: tuple[DoorType, ...] = ()
    window_types: tuple[WindowType, ...] = ()
    furniture_types: tuple[FurnitureType, ...] = ()
    railing_types: tuple[RailingType, ...] = ()
    fixture_types: tuple[FixtureType, ...] = ()
    appliance_types: tuple[ApplianceType, ...] = ()
    equipment_types: tuple[EquipmentType, ...] = ()
    register_types: tuple[RegisterType, ...] = ()
    # The duct itself as a product, keyed by the (material, nominal diameter) pair a
    # ``DuctRun`` states and ``prices.toml``'s ``[ducts]`` already qualifies on. Nothing
    # in the takeoff needs it; the static budget does.
    duct_product_types: tuple[DuctProductType, ...] = ()
    electrical_device_types: tuple[ElectricalDeviceType, ...] = ()
    circuits: tuple[Circuit, ...] = ()
    load_managements: tuple[LoadManagement, ...] = ()
    transitions: tuple[Transition, ...] = ()
    construction_rules: tuple[ConstructionRule, ...] = ()
    # Illustrative planting (``model/landscape.py``); counted, never priced.
    plant_types: tuple[PlantType, ...] = ()

    def assembly(self, tag: str) -> Assembly | None:
        return next((a for a in self.assemblies if a.tag == tag), None)

    def material(self, tag: str) -> Material | None:
        return next((m for m in self.materials if m.tag == tag), None)

    def product(self, tag: str) -> Product | None:
        return next((p for p in self.products if p.tag == tag), None)

    def resolve_assembly(self, tag: str) -> Assembly | None:
        """Resolve a variant against its base — unchanged layers track the base (#35)."""
        asm = self.assembly(tag)
        if asm is None or asm.variant_of is None:
            return asm
        base = self.resolve_assembly(asm.variant_of)
        if base is None:
            return asm
        layers = list(base.layers)
        for sub in asm.substitute:
            layers = _apply_substitution(layers, sub)
        update = {
            "tag": asm.tag,
            "layers": tuple(layers),
            "variant_of": asm.variant_of,
            "stc": asm.stc if asm.stc is not None else base.stc,
            "interfaces": asm.interfaces or base.interfaces,
        }
        # A variant's own scalar fields are its own. Copying the base and overriding only
        # the layer stack silently dropped them: a variant that states its purchasing
        # ``source``, its own room-side ``default_lining``, a different ``junction_policy``
        # or ``role`` resolved with the base's. Each falls back to the base when unset, so
        # a variant that says nothing still tracks its base exactly as before.
        for field in ("label", "source"):
            value = getattr(asm, field)
            if value is not None:
                update[field] = value
        if asm.default_lining:
            update["default_lining"] = asm.default_lining
        defaults = type(asm).model_fields
        for field in ("junction_policy", "role"):
            value = getattr(asm, field)
            if value != defaults[field].default:
                update[field] = value
        return base.model_copy(update=update)


def _apply_substitution(layers: list, sub: object) -> list:
    from typehaus.model.assembly import Substitution

    assert isinstance(sub, Substitution)
    names = [layer.name for layer in layers]
    span = sub.span
    if span.mode == "outside_of":
        i = names.index(span.anchor)
        return layers[: i + 1] + list(sub.replacement)
    if span.mode == "inside_of":
        i = names.index(span.anchor)
        return list(sub.replacement) + layers[i:]
    a, b = names.index(span.anchor), names.index(span.anchor_b)  # type: ignore[arg-type]
    lo, hi = sorted((a, b))
    return layers[:lo] + list(sub.replacement) + layers[hi + 1 :]


# The building every storey belongs to when a house authors no ``Project.buildings``. Not a
# real structure — the name a one-structure model reads so ``building_of`` is total.
IMPLICIT_BUILDING = "building"


class PlanModel(HausModel):
    """The validated authored model, before resolve. Whole-building (→ 02 §Pipeline)."""

    project: Project
    library: Library = Library()
    # Per-storey element lists, keyed by storey tag. Storey defs live in `storeys`.
    storeys: tuple[Storey, ...] = ()
    elements: dict[str, tuple[Element, ...]] = Field(default_factory=dict)
    # Set by the loader, never serialized into authored plan source.  Sidecar asset paths
    # (for example imported house-local furniture) resolve relative to this directory.
    source_root: str | None = None

    def storey(self, tag: str) -> Storey | None:
        return next((s for s in self.storeys if s.tag == tag), None)

    # --- the building axis (a storey is a datum; the container is the building) ----------
    #
    # ``building`` is a pure function of storey, so none of this needs a new field on a
    # ``Resolved*`` class, a re-keying of ``elements``, or a per-element override. Everything
    # downstream asks the plan.

    def buildings(self) -> tuple[Building, ...]:
        """The authored structures, or the one implicit building every storey belongs to.

        The fallback is what keeps the axis inert for a house that authors nothing: one
        building, every storey in it, so ``building_of`` is total and every building-scoped
        consumer reduces to the whole-model behaviour it had before.
        """
        if self.project.buildings:
            return self.project.buildings
        return (Building(tag=IMPLICIT_BUILDING, name=self.project.building.name),)

    def building_of(self, storey_tag: str) -> str:
        """The building tag owning ``storey_tag``. Total: unknown or unclaimed reads first."""
        storey = self.storey(storey_tag)
        if storey is not None and storey.building:
            return storey.building
        return self.buildings()[0].tag

    def building(self, tag: str) -> Building | None:
        return next((b for b in self.buildings() if b.tag == tag), None)

    def storeys_of(self, building: str) -> tuple[Storey, ...]:
        """Every storey of one building, in authored order."""
        return tuple(s for s in self.storeys if self.building_of(s.tag) == building)

    def building_order(self, building: str) -> int:
        """Index of a building in sheet order; unknown sorts last, never first."""
        tags = [b.tag for b in self.buildings()]
        return tags.index(building) if building in tags else len(tags)

    def cells(self) -> tuple[tuple[Building, Storey], ...]:
        """Every (building, storey) pair, buildings in sheet order then authored storey order.

        The "cell" is the unit that a sheet, an ``IfcBuildingStorey`` and a space summary are
        really about — never the storey alone, which two buildings may share an elevation on.
        """
        by_building = {b.tag: b for b in self.buildings()}
        return tuple(
            (by_building[tag], storey)
            for tag in by_building
            for storey in self.storeys_of(tag)
        )

    # --- the datum axis (a LEVEL is one cut plane through every structure on it) ---------
    def levels(self) -> tuple[tuple[Storey, tuple[Storey, ...]], ...]:
        """Storeys grouped by shared elevation, bottom-up: ``(primary, every storey there)``.

        A **cell** is what one structure occupies; a **level** is what one horizontal cut
        crosses, and a drawing is the second. Five of catlin's structures hold a storey at
        ``0'-0"`` — the house's main floor, the garage deck, the porch, the north entry and
        the yard pads — and a reader asking for the main floor plan wants all five, because
        the porch is a thing you step onto from the main floor. Iterating storeys instead
        gave nine plumbing plans and a main floor plan with no porch on it.

        ``primary`` is the tag the level is NAMED and addressed by, and it is the dwelling's
        storey wherever one stands on the level, so catlin's fourteen storeys read as
        ``basement, main, second, attic``. Grouping is by ``Storey.level`` where a storey
        authors one and by its datum otherwise — see :meth:`_level_key`.
        """
        groups: dict[str, list[Storey]] = {}
        for storey in self.storeys:
            groups.setdefault(self._level_key(storey), []).append(storey)
        levels = []
        for key in groups:
            here = sorted(groups[key], key=lambda s: (
                self.building_of(s.tag) not in self._dwelling_tags(),
                self.building_order(self.building_of(s.tag)),
                s.elevation.meters, s.tag))
            levels.append((here[0], tuple(groups[key])))
        # By the primary's datum, so the list still reads bottom-up.
        return tuple(sorted(levels, key=lambda item: item[0].elevation.meters))

    def _level_key(self, storey: Storey) -> str:
        """What groups this storey with others: its authored ``level``, else its datum.

        An authored level wins outright — a storey naming one is making a claim about which
        floor it is drawn with, and that claim may cross datums (the garage's ``-1'-0"`` stem
        top is the same floor as the house's ``0'-0"`` deck). Unauthored, the datum is the
        honest default and rounds to 0.1 mm: two storeys reading one constant are bit-equal,
        but a float that has been through JSON should not split a floor on the last ulp.
        """
        if storey.level:
            joined = self.storey(storey.level)
            # One hop only. ``level`` names the storey to be drawn with, so the target's own
            # key is the answer — and a target that itself names one would make the grouping
            # depend on chain order, so it is not followed.
            if joined is not None and not joined.level:
                return f"datum:{round(joined.elevation.meters * 1e4)}"
            return f"level:{storey.level}"
        return f"datum:{round(storey.elevation.meters * 1e4)}"

    def _dwelling_tags(self) -> frozenset[str]:
        return frozenset(b.tag for b in self.buildings() if b.kind == "dwelling")

    def level_of(self, storey_tag: str) -> tuple[str, ...]:
        """Every storey sharing ``storey_tag``'s datum, itself included.

        The display filter: what a plan drawn at this level shows. A tag naming no storey
        answers with itself, so a caller holding a stale tag draws one storey rather than
        silently drawing the whole house.
        """
        storey = self.storey(storey_tag)
        if storey is None:
            return (storey_tag,)
        key = self._level_key(storey)
        return tuple(s.tag for s in self.storeys if self._level_key(s) == key)

    def storey_elements(self, storey_tag: str) -> tuple[Element, ...]:
        return self.elements.get(storey_tag, ())

    def all_elements(self) -> Iterator[Element]:
        for group in self.elements.values():
            yield from group

    def elements_of_kind(self, kind: str) -> Iterator[Element]:
        for el in self.all_elements():
            if el.element_kind == kind:
                yield el

    def by_tag(self, tag: str) -> Element | None:
        return self._tag_index().get(tag)

    def _tag_index(self) -> dict[str, Element]:
        """Tag -> element, built once per plan instance.

        This was a linear scan over ``all_elements()``. On the reference house ``resolve``
        called it ~4,000 times, which walked 1.18 M elements and cost ~13% of resolve's
        self-time — the single hottest entry in the profile. First tag wins, matching the
        old ``next(...)`` semantics on duplicates.

        The cache is keyed on the identity of the ``elements`` mapping it was built from,
        not merely stored on the instance: ``with_elements`` goes through ``model_copy``,
        which shallow-copies ``__dict__``, so an instance-only cache rides along onto the
        copy and answers for elements that copy no longer has. Comparing identity makes any
        copy, reconstruction or deserialization miss and rebuild.
        """
        cached = self.__dict__.get("_tag_index_cache")
        if cached is not None and cached[0] is self.elements:
            return cached[1]
        index: dict[str, Element] = {}
        for el in self.all_elements():
            if el.tag not in index:
                index[el.tag] = el
        object.__setattr__(self, "_tag_index_cache", (self.elements, index))
        return index

    def with_elements(self, storey_tag: str, items: Iterable[Element]) -> PlanModel:
        merged = dict(self.elements)
        merged[storey_tag] = tuple(items)
        return self.model_copy(update={"elements": merged})
